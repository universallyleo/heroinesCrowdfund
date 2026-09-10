#!/usr/bin/env python3
"""Discover and scrape finished CAMPFIRE projects for the heroines profile."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


LISTING_URL = "https://camp-fire.jp/profile/heroines/projects"
DEFAULT_CHECKPOINT_URL = "https://camp-fire.jp/projects/956928/view"
DEFAULT_DATABASE_PATH = Path("src/lib/data/heroinesCF.json")
DEFAULT_PROGRESS_PATH = Path("scrape_data/scrape_progress.json")
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_ATTEMPTS = 3
DEFAULT_REQUEST_DELAY_SECONDS = 1.0
USER_AGENT = (
    "Mozilla/5.0 (compatible; heroinesCrowdfund scraper; +https://github.com/"
    "universallyleo/heroinesCrowdfund)"
)


class ScrapeError(RuntimeError):
    """Base error for expected scraper failures."""


class ParseError(ScrapeError):
    """Raised when CAMPFIRE HTML does not contain valid project data."""


class DiscoveryError(ScrapeError):
    """Raised when the listing cannot be safely traversed."""


class ProjectNotFinished(ParseError):
    """Raised when a project page is still open during a pending retry."""


@dataclass(frozen=True)
class ProjectSummary:
    project_id: str
    url: str
    title: str
    description: str
    status: str


@dataclass(frozen=True)
class DiscoveryResult:
    summaries: list[ProjectSummary]
    pages_scanned: int
    checkpoint_found: bool


class HttpFetcher:
    """Small sequential HTTP client with spacing and retry behavior."""

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        attempts: int = DEFAULT_ATTEMPTS,
        delay: float = DEFAULT_REQUEST_DELAY_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.attempts = attempts
        self.delay = delay
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._last_request_at: float | None = None

    def __call__(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            self._wait_between_requests()
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = response.encoding or "utf-8"
                self._last_request_at = time.monotonic()
                return response.text
            except requests.RequestException as exc:
                last_error = exc
                self._last_request_at = time.monotonic()
                if attempt == self.attempts:
                    break

        raise ScrapeError(f"request failed after {self.attempts} attempts: {url}: {last_error}")

    def _wait_between_requests(self) -> None:
        if self._last_request_at is None or self.delay <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project_id_from_url(url: str) -> str:
    match = re.search(r"/projects/(\d+)(?:/view)?(?:[/?#]|$)", url)
    if not match:
        raise ParseError(f"cannot find project id in URL: {url}")
    return match.group(1)


def canonical_project_url(url: str) -> str:
    return f"https://camp-fire.jp/projects/{project_id_from_url(url)}/view"


def parse_number(text: str) -> int:
    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        raise ParseError(f"expected a number, got: {text!r}")
    return int(digits)


def parse_event_year(text: str) -> int:
    years = sorted({int(value) for value in re.findall(r"(?<!\d)(20\d{2})年", text)})
    if len(years) != 1:
        raise ParseError(f"expected exactly one event year, got {years or 'none'}")
    return years[0]


def _normalize_date(parts: tuple[str, str, str], url: str) -> str:
    try:
        return date(*(int(part) for part in parts)).isoformat()
    except ValueError as exc:
        raise ParseError(f"project page has an invalid date: {url}: {parts}") from exc


_BRACKET_RE = re.compile(
    r"【([^【】]+)】|＜([^＜＞]+)＞|〖([^〖〗]+)〗|<([^<>]+)>|\[([^\[\]]+)\]"
)


def parse_subject(title: str) -> dict[str, str]:
    suffix = "応援プロジェクト"
    if not title.strip().endswith(suffix):
        raise ParseError(f"title does not end with {suffix}: {title}")

    matches = list(_BRACKET_RE.finditer(title))
    if not matches:
        raise ParseError(f"title has no supported member brackets: {title}")

    group = re.sub(r"[／/]\s*$", "", title[: matches[0].start()].strip()).strip()
    if not group:
        raise ParseError(f"title has no group: {title}")

    members: list[str] = []
    for index, match in enumerate(matches):
        member = next((value for value in match.groups() if value is not None), "").strip()
        if not member:
            raise ParseError(f"title has an empty member: {title}")
        members.append(member)
        if index + 1 < len(matches):
            between = title[match.end() : matches[index + 1].start()]
            if re.sub(r"[\s/／,、・&]+", "", between):
                raise ParseError(f"title has ambiguous text between members: {title}")

    event_type = title[matches[-1].end() : -len(suffix)].strip()
    if not event_type:
        raise ParseError(f"title has no event type: {title}")

    return {"group": group, "member": ", ".join(members), "type": event_type}


def _first_text(soup: BeautifulSoup, selectors: Iterable[str]) -> str:
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(" ", strip=True)
            if text:
                return text
    return ""


def _first_attribute(soup: BeautifulSoup, selector: str, attribute: str) -> str:
    element = soup.select_one(selector)
    return element.get(attribute, "").strip() if element else ""


def parse_listing_page(html: str, page_url: str) -> tuple[list[ProjectSummary], str | None]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".project-card-content[data_project_id], .project-card-content")
    if not cards:
        raise DiscoveryError(f"listing page has no project cards: {page_url}")

    summaries: list[ProjectSummary] = []
    seen_ids: set[str] = set()
    for card in cards:
        link = next(
            (
                candidate
                for candidate in card.select("a[href]")
                if re.search(
                    r"/projects/\d+/view(?:[?#]|$)", urljoin(page_url, candidate["href"])
                )
            ),
            None,
        )
        if not link:
            raise DiscoveryError(f"project card has no project link: {page_url}")

        url = canonical_project_url(urljoin(page_url, link["href"]))
        project_id = card.get("data_project_id", "").strip() or project_id_from_url(url)
        if project_id in seen_ids:
            continue
        seen_ids.add(project_id)

        title = (
            link.get("title", "").strip()
            or _first_text(card, [".box-title h4", ".box-title"])
            or ""
        )
        description = _first_text(card, [".box-title .sub p", ".sub p"])
        status = _first_text(card, [".overview .per", ".per"])
        if not title or not status:
            raise DiscoveryError(f"project card is missing title or status: {url}")

        summaries.append(ProjectSummary(project_id, url, title, description, status))

    next_url: str | None = None
    for link in soup.select("a[href]"):
        link_text = link.get_text(" ", strip=True)
        if "次のページ" in link_text:
            next_url = urljoin(page_url, link["href"])
            break

    return summaries, next_url


def discover_listing(
    fetch_text: Callable[[str], str],
    checkpoint_url: str,
    listing_url: str = LISTING_URL,
    full_scan: bool = False,
) -> DiscoveryResult:
    checkpoint_id = project_id_from_url(checkpoint_url)
    current_url = listing_url
    visited_urls: set[str] = set()
    summaries: list[ProjectSummary] = []
    seen_ids: set[str] = set()
    pages_scanned = 0
    checkpoint_found = False

    while current_url:
        if current_url in visited_urls:
            raise DiscoveryError(f"listing pagination loop detected at {current_url}")
        visited_urls.add(current_url)
        html = fetch_text(current_url)
        page_summaries, next_url = parse_listing_page(html, current_url)
        pages_scanned += 1

        for summary in page_summaries:
            if summary.project_id not in seen_ids:
                summaries.append(summary)
                seen_ids.add(summary.project_id)
        if any(summary.project_id == checkpoint_id for summary in page_summaries):
            checkpoint_found = True
            if not full_scan:
                break

        current_url = next_url

    return DiscoveryResult(summaries, pages_scanned, checkpoint_found)


def parse_project_page(
    html: str,
    url: str,
    listing_description: str = "",
) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    title = _first_text(soup, ["div.project-hero span.title-name", ".project-hero .title-name"])
    if not title:
        raise ParseError(f"project page has no title: {url}")

    closed_text = _first_text(
        soup,
        [
            "div.overview-bottom-pc div.text-when-closed-wrap p",
            ".text-when-closed-wrap p",
            "div.overview .per",
        ],
    )
    if not re.search(r"募集(?:を)?終了|募集終了|終了", closed_text):
        raise ProjectNotFinished(f"project is not finished: {url}")

    dates = re.findall(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", closed_text)
    if len(dates) < 2:
        raise ParseError(f"project page has fewer than two dates: {url}")
    start = _normalize_date(dates[0], url)
    end = _normalize_date(dates[-1], url)

    total_text = _first_text(soup, ["div.overview p.backer-amount", ".backer-amount"])
    patrons_text = _first_text(soup, ["div.overview p.backer", ".backer"])
    if not total_text or not patrons_text:
        raise ParseError(f"project page has no funding summary: {url}")
    total = parse_number(total_text)
    patrons = parse_number(patrons_text)

    reward_items = soup.select("section#reward-pc-section div.reward-container ul li.item")
    if not reward_items:
        reward_items = soup.select("section#reward-pc-section li.item")
    if not reward_items:
        raise ParseError(f"project page has no rewards: {url}")

    reward_totals: dict[int, int] = {}
    for item in reward_items:
        price_text = _first_text(item, ["div.info-area div.header p.price", ".price"])
        patrons_for_reward_text = _first_text(
            item, ["div.info-area div.patrons-ship p.patrons", ".patrons"]
        )
        if not price_text or not patrons_for_reward_text:
            raise ParseError(f"reward is missing price or patrons: {url}")
        price = parse_number(price_text)
        reward_patrons = parse_number(patrons_for_reward_text)
        reward_totals[price] = reward_totals.get(price, 0) + reward_patrons

    meta_description = _first_attribute(soup, 'meta[name="description"]', "content")
    year_source = meta_description or listing_description
    event_year = parse_event_year(year_source)

    return {
        "url": canonical_project_url(url),
        "title": title,
        "total": total,
        "rest": patrons,
        "per": "終了",
        "pricePatrons": [
            {"price": price, "patrons": reward_totals[price]}
            for price in sorted(reward_totals)
        ],
        "subject": parse_subject(title),
        "start": start,
        "end": end,
        "eventYear": event_year,
    }


def merge_records(existing: list[dict[str, object]], new_records: list[dict[str, object]]) -> list[dict[str, object]]:
    existing_ids = {project_id_from_url(str(record["url"])) for record in existing}
    unique_new: dict[str, dict[str, object]] = {}
    for record in new_records:
        project_id = project_id_from_url(str(record["url"]))
        if project_id not in existing_ids:
            unique_new[project_id] = record
    ordered_new = [unique_new[project_id] for project_id in sorted(unique_new, key=int, reverse=True)]
    return ordered_new + existing


def load_progress(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"checkpointUrl": DEFAULT_CHECKPOINT_URL, "pending": {}}

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        checkpoint = canonical_project_url(str(value["checkpointUrl"]))
        pending = value.get("pending", {})
        if not isinstance(pending, dict):
            raise ValueError("pending must be an object")
        return {"checkpointUrl": checkpoint, "pending": pending}
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ScrapeError(f"invalid progress file: {path}: {exc}") from exc


def _pending_entry(summary: ProjectSummary, status: str, attempted_at: str | None = None, error: str | None = None) -> dict[str, object]:
    return {
        "url": summary.url,
        "title": summary.title,
        "description": summary.description,
        "status": status,
        "lastAttemptAt": attempted_at,
        "error": error,
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_pipeline(
    database_path: Path,
    progress_path: Path,
    output_dir: Path,
    full_scan: bool = False,
    fetch_text: Callable[[str], str] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or utc_now()
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = json.loads(database_path.read_text(encoding="utf-8"))
    progress = load_progress(progress_path)
    pending = copy.deepcopy(progress["pending"])
    fetch_text = fetch_text or HttpFetcher()

    try:
        discovery = discover_listing(
            fetch_text,
            str(progress["checkpointUrl"]),
            full_scan=full_scan,
        )
    except Exception as exc:
        report = {
            "generatedAt": generated_at,
            "fatalError": str(exc),
            "databaseChanged": False,
            "progressChanged": False,
        }
        _write_json(output_dir / "run_report.json", report)
        return report

    existing_ids = {project_id_from_url(str(record["url"])) for record in existing}
    candidates: dict[str, ProjectSummary] = {}
    prior_pending_ids = set(pending)
    for summary in discovery.summaries:
        if summary.project_id in existing_ids:
            pending.pop(summary.project_id, None)
        elif "終了" in summary.status:
            candidates[summary.project_id] = summary
        elif summary.project_id not in pending:
            pending[summary.project_id] = _pending_entry(summary, "unfinished")

    for project_id in prior_pending_ids:
        entry = pending[project_id]
        if project_id in existing_ids or project_id in candidates:
            continue
        try:
            candidates[project_id] = ProjectSummary(
                project_id=project_id,
                url=canonical_project_url(str(entry["url"])),
                title=str(entry.get("title", "")),
                description=str(entry.get("description", "")),
                status=str(entry.get("status", "unfinished")),
            )
        except (KeyError, TypeError, ParseError) as exc:
            entry["status"] = "failed"
            entry["error"] = str(exc)

    new_records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for project_id in sorted(candidates, key=int, reverse=True):
        summary = candidates[project_id]
        attempted_at = utc_now()
        try:
            record = parse_project_page(
                fetch_text(summary.url), summary.url, listing_description=summary.description
            )
            new_records.append(record)
            pending.pop(project_id, None)
        except ProjectNotFinished:
            pending[project_id] = _pending_entry(summary, "unfinished", attempted_at)
        except Exception as exc:
            error = str(exc)
            pending[project_id] = _pending_entry(summary, "failed", attempted_at, error)
            failures.append({"projectId": project_id, "url": summary.url, "error": error})

    merged = merge_records(existing, new_records)
    resulting_ids = existing_ids | {project_id_from_url(str(record["url"])) for record in new_records}
    new_checkpoint = str(progress["checkpointUrl"])
    for summary in discovery.summaries:
        if summary.project_id in resulting_ids:
            new_checkpoint = summary.url
            break

    candidate_progress = {
        "checkpointUrl": new_checkpoint,
        "pending": {key: pending[key] for key in sorted(pending, key=lambda value: int(value))},
    }
    progress_changed = candidate_progress != progress
    report = {
        "generatedAt": generated_at,
        "pagesScanned": discovery.pages_scanned,
        "checkpointFound": discovery.checkpoint_found,
        "checkpointUrl": new_checkpoint,
        "newProjectIds": [project_id_from_url(str(record["url"])) for record in new_records],
        "unfinishedProjectIds": sorted(
            key for key, value in pending.items() if value.get("status") == "unfinished"
        ),
        "failedProjectIds": sorted(
            key for key, value in pending.items() if value.get("status") == "failed"
        ),
        "failures": failures,
        "databaseChanged": bool(new_records),
        "progressChanged": progress_changed,
        "fullScan": full_scan,
    }
    _write_json(output_dir / "candidate_database.json", merged)
    _write_json(output_dir / "candidate_progress.json", candidate_progress)
    _write_json(output_dir / "run_report.json", report)
    return report


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE_PATH)
    parser.add_argument("--progress", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--full-scan", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    output_dir = args.output_dir or Path(tempfile.mkdtemp(prefix="heroines-scrape-"))
    report = run_pipeline(args.database, args.progress, output_dir, full_scan=args.full_scan)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report.get("fatalError") else 0


if __name__ == "__main__":
    sys.exit(main())
