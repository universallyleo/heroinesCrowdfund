#!/usr/bin/env python3
"""Apply a validated scrape stage and optionally commit it from GitHub Actions."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from agency_config import (REGISTRY_PATH, fingerprint, resolve_agency, validate_records,
                           validate_metadata, normalize_progress)
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def apply_staged_files(report, output_dir, agency_id, repo_root, backup_stamp, run_id, attempt):
    agency = resolve_agency(agency_id, repo_root)
    if report.get("schemaVersion") != 1 or report.get("agencyId") != agency_id or report.get("outcome") not in ("success", "partial") or report.get("fatalError"):
        raise ValueError("Stage is failed or belongs to another agency")
    if report.get("scraperId") != agency["scraper"]["id"] or report.get("registrySha256") != fingerprint(repo_root / REGISTRY_PATH):
        raise ValueError("Stage registry/scraper has changed")
    if agency['scraper']['id'] == 'campfire_madsink':
        from campfire_madsink import MEMBERS_PATH
        if report.get('parserConfigSha256') != fingerprint(MEMBERS_PATH):
            raise ValueError('Stage membership mapping has changed')
    sources = agency['scraper']['discoverySources']
    if set(report.get('sources', {})) != {s['id'] for s in sources} or any(
        report['sources'][s['id']].get('listingUrl') != s['listingUrl'] for s in sources
    ):
        raise ValueError('Stage discovery source identity mismatch')
    names = {"databasePath": "database", "metadataPath": "metadata", "progressPath": "progress"}
    originals, candidates, changes = {}, {}, {}
    for key, name in names.items():
        path = repo_root / agency[key]
        if report.get("sourceFiles", {}).get(key) != {"path": agency[key], "sha256": fingerprint(path)}:
            raise ValueError(f"Stale or mismatched source: {key}")
        originals[path] = path.read_bytes()
        candidate = output_dir / f"candidate_{name}.json"
        candidates[path] = candidate.read_bytes()
        changed = json.loads(originals[path]) != json.loads(candidates[path])
        if type(report.get(f"{name}Changed")) is not bool or report[f"{name}Changed"] != changed:
            raise ValueError(f"Inconsistent {name}Changed flag")
        changes[path] = changed
    database_path = repo_root / agency['databasePath']
    metadata_path = repo_root / agency['metadataPath']
    progress_path = repo_root / agency['progressPath']
    validate_records(json.loads(candidates[database_path]))
    metadata = json.loads(candidates[metadata_path])
    validate_metadata(metadata, agency)
    progress = json.loads(candidates[progress_path])
    if normalize_progress(progress, agency) != progress:
        raise ValueError("Candidate progress is not normalized for the selected registry")
    if report['databaseChanged'] and (metadata['updatedAt'] is None or metadata['updatedAt'] != report.get('generatedAt')):
        raise ValueError("Changed records require matching content-update metadata")
    for token in (backup_stamp, run_id, attempt):
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', token):
            raise ValueError('Invalid backup identity')
    backup_path = metadata_backup = None
    created_backups, temporary_files, replaced = [], [], []
    try:
        if report['databaseChanged']:
            backup_root = repo_root / agency['backupRoot']
            backup_root.mkdir(parents=True, exist_ok=True)
            stem = f'backup_at_{backup_stamp}_run{run_id}_attempt{attempt}'
            backup_path = backup_root / (stem + '.json')
            metadata_backup = backup_root / (stem + '.metadata.json')
            for path, original in ((backup_path, originals[database_path]), (metadata_backup, originals[metadata_path])):
                with path.open('xb') as file:
                    created_backups.append(path)
                    file.write(original)
        for path, changed in changes.items():
            if changed:
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.update-', delete=False) as file:
                    temporary = Path(file.name); temporary_files.append(temporary)
                    file.write(candidates[path])
                os.replace(temporary, path)
                replaced.append(path)
    except Exception:
        for path in reversed(replaced):
            path.write_bytes(originals[path])
        for path in created_backups:
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in temporary_files:
            path.unlink(missing_ok=True)
    changed_paths = [str(path) for path, changed in changes.items() if changed] + [str(path) for path in created_backups]
    return {'backup': str(backup_path) if backup_path else None,
            'metadata_backup': str(metadata_backup) if metadata_backup else None, 'changed_paths': changed_paths}


def _run_git(repo_root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=check,
        text=True,
        capture_output=True,
    )


def commit_and_push(
    repo_root: Path,
    database_path: Path,
    progress_path: Path,
    backup_path: str | None,
    commit_message: str,
    extra_paths: list[str] | None = None,
) -> str | None:
    paths = [str(database_path), str(progress_path), *(extra_paths or [])]
    if backup_path:
        paths.append(backup_path)
    if _run_git(repo_root, "branch", "--show-current").stdout.strip() != "main":
        raise ValueError("Publication requires the main branch")
    if _run_git(repo_root, "diff", "--cached", "--name-only").stdout.strip():
        raise ValueError("Publication checkout already has staged changes")
    allowed = {str((repo_root / path).resolve()) for path in paths}
    dirty = _run_git(repo_root, "status", "--porcelain", "--untracked-files=all", "-z").stdout.split('\0')
    if any(str((repo_root / entry[3:]).resolve()) not in allowed for entry in dirty if entry):
        raise ValueError("Publication checkout has unrelated changes")
    _run_git(repo_root, "add", "--", *paths)

    staged_diff = _run_git(repo_root, "diff", "--cached", "--quiet", check=False)
    if staged_diff.returncode == 0:
        return None
    _run_git(repo_root, "config", "user.name", "github-actions[bot]")
    _run_git(repo_root, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    _run_git(repo_root, "commit", "-m", commit_message)
    _run_git(repo_root, "push", "origin", "HEAD:main")
    return _run_git(repo_root, "rev-parse", "HEAD").stdout.strip()


def _write_github_output(path: Path | None, values: dict[str, str | None]) -> None:
    if path is None:
        return
    with path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value or ''}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--agency", default="heroines")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--publish", action="store_true", help="Commit/push to main from a clean production checkout")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "local"))
    parser.add_argument("--attempt", default=os.environ.get("GITHUB_RUN_ATTEMPT", "local"))
    parser.add_argument("--backup-stamp", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    args = parser.parse_args()
    args.repo_root = args.repo_root.resolve()
    if args.publish:
        if _run_git(args.repo_root, "branch", "--show-current").stdout.strip() != "main" or _run_git(args.repo_root, "status", "--porcelain").stdout.strip():
            raise ValueError("Publishing requires a clean main checkout before application")
    report = json.loads((args.output_dir / "run_report.json").read_text(encoding="utf-8"))
    result = apply_staged_files(report, args.output_dir, args.agency, args.repo_root,
                               args.backup_stamp, args.run_id, args.attempt)
    commit_sha = None
    if args.publish and result['changed_paths']:
        agency = resolve_agency(args.agency, args.repo_root)
        commit_sha = commit_and_push(args.repo_root, Path(agency['databasePath']), Path(agency['progressPath']),
                                    result['backup'], f"data: update {args.agency} crowdfunding snapshot/progress",
                                    extra_paths=result['changed_paths'])
    outputs = {"database_changed": str(report['databaseChanged']).lower(),
               "metadata_changed": str(report['metadataChanged']).lower(),
               "progress_changed": str(report['progressChanged']).lower(),
               "public_data_changed": str(report['databaseChanged'] or report['metadataChanged']).lower(),
               "commit_sha": commit_sha}
    _write_github_output(args.github_output, outputs)
    print(json.dumps({**result, **outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
