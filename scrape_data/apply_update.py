#!/usr/bin/env python3
"""Apply a validated scrape stage and optionally commit it from GitHub Actions."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def apply_staged_files(
    report: dict[str, object],
    output_dir: Path,
    database_path: Path,
    progress_path: Path,
    backup_root: Path,
    backup_stamp: str,
    run_id: str,
    attempt: str,
) -> dict[str, str | None]:
    database_changed = bool(report.get("databaseChanged"))
    progress_changed = bool(report.get("progressChanged"))
    backup_path: Path | None = None

    if database_changed:
        candidate_database = output_dir / "candidate_database.json"
        if not candidate_database.exists():
            raise RuntimeError(f"missing staged database: {candidate_database}")
        if not database_path.exists():
            raise RuntimeError(f"missing source database: {database_path}")
        backup_root.mkdir(parents=True, exist_ok=True)
        backup_path = backup_root / (
            f"backup_at_{backup_stamp}_run{run_id}_attempt{attempt}.json"
        )
        shutil.copy2(database_path, backup_path)
        shutil.copy2(candidate_database, database_path)

    if progress_changed:
        candidate_progress = output_dir / "candidate_progress.json"
        if not candidate_progress.exists():
            raise RuntimeError(f"missing staged progress: {candidate_progress}")
        shutil.copy2(candidate_progress, progress_path)

    return {"backup": str(backup_path) if backup_path else None}


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
) -> str | None:
    paths = [str(database_path), str(progress_path)]
    if backup_path:
        paths.append(backup_path)
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
    parser.add_argument("--database", type=Path, default=Path("src/lib/data/heroinesCF.json"))
    parser.add_argument("--progress", type=Path, default=Path("scrape_data/scrape_progress.json"))
    parser.add_argument("--backup-root", type=Path, default=Path("src/lib/data/old"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "local"))
    parser.add_argument("--attempt", default=os.environ.get("GITHUB_RUN_ATTEMPT", "local"))
    parser.add_argument(
        "--backup-stamp",
        default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    )
    args = parser.parse_args()

    report = json.loads((args.output_dir / "run_report.json").read_text(encoding="utf-8"))
    result = apply_staged_files(
        report,
        args.output_dir,
        args.database,
        args.progress,
        args.backup_root,
        args.backup_stamp,
        args.run_id,
        args.attempt,
    )

    commit_sha = None
    if report.get("databaseChanged") or report.get("progressChanged"):
        commit_message = (
            "data: update scraped crowdfunding records"
            if report.get("databaseChanged")
            else "data: update scraper progress"
        )
        commit_sha = commit_and_push(
            args.repo_root,
            args.database,
            args.progress,
            result["backup"],
            commit_message,
        )

    outputs = {
        "database_changed": "true" if report.get("databaseChanged") else "false",
        "progress_changed": "true" if report.get("progressChanged") else "false",
        "commit_sha": commit_sha,
    }
    _write_github_output(args.github_output, outputs)
    print(json.dumps({**result, **outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
