import unittest
import json
import tempfile
from pathlib import Path

import requests

from scraper import (
    HttpFetcher,
    ParseError,
    discover_listing,
    merge_records,
    parse_event_year,
    parse_listing_page,
    parse_project_page,
    parse_subject,
    run_pipeline,
)


LISTING_PAGE_1 = """
<section class="boxes1">
  <div class="box-in project-card-content" data_project_id="200">
    <a class="area" href="/projects/search?prefecture=tokyo">東京都</a>
    <div class="box-title"><a href="https://camp-fire.jp/projects/200/view" title="Open project"><h4>Open project</h4></a>
      <div class="sub"><p>2026年10月実施予定</p></div>
    </div>
    <div class="overview"><div class="per"><small>残り</small> 10日</div></div>
  </div>
  <div class="box-in project-card-content" data_project_id="199">
    <a class="area" href="/projects/search?prefecture=tokyo">東京都</a>
    <div class="box-title"><a href="/projects/199/view" title="Closed project"><h4>Closed project</h4></a>
      <div class="sub"><p>2026年9月実施予定</p></div>
    </div>
    <div class="overview"><div class="per"><small>残り</small> 終了</div></div>
  </div>
</section>
<a href="/profile/heroines/projects?page=2">次のページ &gt;</a>
"""


PROJECT_PAGE = """
<html>
  <head><meta name="description" content="2025年12月実施予定のイベント" /></head>
  <body>
    <div class="project-hero"><span class="title-name">パラレルサイダー＜リア＞＜笑茉＞合同生誕祭応援プロジェクト</span></div>
    <div class="overview">
      <p class="backer-amount">1,234 円</p>
      <p class="backer">12 人</p>
    </div>
    <div class="overview-bottom-pc">
      <div class="text-when-closed-wrap"><p>このプロジェクトは、2025/11/01 に募集を開始し、12 人の支援により 1,234 円を集め、2026/01/31 に募集を終了しました</p></div>
    </div>
    <section id="reward-pc-section"><div class="reward-container"><ul>
      <li class="item"><div class="summary"><div class="info-area"><div class="header"><p class="price">1,000 円</p></div><div class="patrons-ship"><p class="patrons">支援者：2人</p></div></div></div></li>
      <li class="item"><div class="summary"><div class="info-area"><div class="header"><p class="price">1,000 円</p></div><div class="patrons-ship"><p class="patrons">支援者：3人</p></div></div></div></li>
      <li class="item"><div class="summary"><div class="info-area"><div class="header"><p class="price">3,000 円</p></div><div class="patrons-ship"><p class="patrons">支援者：1人</p></div></div></div></li>
    </ul></div></section>
  </body>
</html>
"""


class ScraperParsingTests(unittest.TestCase):
    def test_parse_subject_supports_bracket_variants_and_joint_members(self):
        self.assertEqual(
            parse_subject("iLiFE!／＜向日えな＞生誕祭応援プロジェクト"),
            {"group": "iLiFE!", "member": "向日えな", "type": "生誕祭"},
        )
        self.assertEqual(
            parse_subject("パラレルサイダー＜リア＞＜笑茉＞合同生誕祭応援プロジェクト"),
            {"group": "パラレルサイダー", "member": "リア, 笑茉", "type": "合同生誕祭"},
        )
        self.assertEqual(
            parse_subject("TENRIN〖霞あげは〗生誕祭応援プロジェクト"),
            {"group": "TENRIN", "member": "霞あげは", "type": "生誕祭"},
        )
        with self.assertRaises(ParseError):
            parse_subject("Unrecognized title")

    def test_parse_event_year_requires_one_year(self):
        self.assertEqual(parse_event_year("2025年12月実施予定"), 2025)
        with self.assertRaises(ParseError):
            parse_event_year("年内実施予定")
        with self.assertRaises(ParseError):
            parse_event_year("2025年と2026年の合同イベント")

    def test_parse_listing_page_extracts_cards_and_next_page(self):
        summaries, next_url = parse_listing_page(
            LISTING_PAGE_1, "https://camp-fire.jp/profile/heroines/projects"
        )

        self.assertEqual([summary.project_id for summary in summaries], ["200", "199"])
        self.assertEqual(summaries[0].status, "残り 10日")
        self.assertEqual(summaries[1].status, "残り 終了")
        self.assertEqual(next_url, "https://camp-fire.jp/profile/heroines/projects?page=2")

    def test_parse_project_page_aggregates_rewards_and_uses_description_year(self):
        record = parse_project_page(
            PROJECT_PAGE,
            "https://camp-fire.jp/projects/199/view",
            listing_description="2026年9月実施予定",
        )

        self.assertEqual(record["total"], 1234)
        self.assertEqual(record["rest"], 12)
        self.assertEqual(record["start"], "2025-11-01")
        self.assertEqual(record["end"], "2026-01-31")
        self.assertEqual(record["eventYear"], 2025)
        self.assertEqual(record["pricePatrons"], [{"price": 1000, "patrons": 5}, {"price": 3000, "patrons": 1}])
        self.assertEqual(record["per"], "終了")

    def test_parse_project_page_rejects_invalid_calendar_dates(self):
        invalid_page = PROJECT_PAGE.replace("2026/01/31", "2026/99/99")
        with self.assertRaises(ParseError):
            parse_project_page(
                invalid_page,
                "https://camp-fire.jp/projects/199/view",
                listing_description="2026年9月実施予定",
            )

    def test_discover_listing_stops_after_checkpoint_page(self):
        page_2 = LISTING_PAGE_1.replace(
            '<a href="/profile/heroines/projects?page=2">次のページ &gt;</a>', ""
        ).replace("data_project_id=\"200\"", "data_project_id=\"198\"")
        pages = {
            "https://camp-fire.jp/profile/heroines/projects": LISTING_PAGE_1,
            "https://camp-fire.jp/profile/heroines/projects?page=2": page_2,
        }
        fetched = []

        def fetch(url):
            fetched.append(url)
            return pages[url]

        result = discover_listing(
            fetch,
            checkpoint_url="https://camp-fire.jp/projects/199/view",
            listing_url="https://camp-fire.jp/profile/heroines/projects",
        )

        self.assertTrue(result.checkpoint_found)
        self.assertEqual(result.pages_scanned, 1)
        self.assertEqual([summary.project_id for summary in result.summaries], ["200", "199"])
        self.assertEqual(fetched, ["https://camp-fire.jp/profile/heroines/projects"])

    def test_discover_listing_reports_missing_checkpoint_after_last_page(self):
        page_2 = LISTING_PAGE_1.replace(
            '<a href="/profile/heroines/projects?page=2">次のページ &gt;</a>', ""
        )
        pages = {
            "https://camp-fire.jp/profile/heroines/projects": LISTING_PAGE_1,
            "https://camp-fire.jp/profile/heroines/projects?page=2": page_2,
        }

        result = discover_listing(
            pages.__getitem__,
            checkpoint_url="https://camp-fire.jp/projects/999/view",
            listing_url="https://camp-fire.jp/profile/heroines/projects",
        )

        self.assertFalse(result.checkpoint_found)
        self.assertEqual(result.pages_scanned, 2)

    def test_http_fetcher_retries_request_failures(self):
        class Response:
            text = "ok"
            encoding = "utf-8"

            def raise_for_status(self):
                return None

        class Session:
            def __init__(self):
                self.headers = {}
                self.calls = 0

            def get(self, url, timeout):
                self.calls += 1
                if self.calls < 3:
                    raise requests.Timeout("temporary")
                return Response()

        session = Session()
        fetcher = HttpFetcher(attempts=3, delay=0, session=session)
        self.assertEqual(fetcher("https://example.test"), "ok")
        self.assertEqual(session.calls, 3)

    def test_merge_records_prepends_new_records_in_descending_project_id_order(self):
        existing = [{"url": "https://camp-fire.jp/projects/100/view", "title": "existing"}]
        new_records = [
            {"url": "https://camp-fire.jp/projects/102/view", "title": "newer"},
            {"url": "https://camp-fire.jp/projects/101/view", "title": "older"},
            {"url": "https://camp-fire.jp/projects/100/view", "title": "duplicate"},
        ]

        merged = merge_records(existing, new_records)

        self.assertEqual([record["title"] for record in merged], ["newer", "older", "existing"])

    def test_run_pipeline_publishes_successes_and_retains_open_and_failed_projects(self):
        listing = LISTING_PAGE_1.replace(
            "</section>",
            """
  <div class="box-in project-card-content" data_project_id="198">
    <div class="box-title"><a href="/projects/198/view" title="Failed project"><h4>Failed project</h4></a>
      <div class="sub"><p>2025年8月実施予定</p></div>
    </div>
    <div class="overview"><div class="per"><small>残り</small> 終了</div></div>
  </div>
</section>""",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "database.json"
            progress = root / "progress.json"
            output = root / "output"
            database.write_text(
                json.dumps([{"url": "https://camp-fire.jp/projects/100/view", "title": "existing"}]),
                encoding="utf-8",
            )
            progress.write_text(
                json.dumps(
                    {
                        "checkpointUrl": "https://camp-fire.jp/projects/199/view",
                        "pending": {},
                    }
                ),
                encoding="utf-8",
            )
            pages = {
                "https://camp-fire.jp/profile/heroines/projects": listing,
                "https://camp-fire.jp/projects/199/view": PROJECT_PAGE,
                "https://camp-fire.jp/projects/198/view": "<html></html>",
            }

            report = run_pipeline(database, progress, output, fetch_text=pages.__getitem__)

            self.assertEqual(report["newProjectIds"], ["199"])
            self.assertEqual(report["unfinishedProjectIds"], ["200"])
            self.assertEqual(report["failedProjectIds"], ["198"])
            candidate_database = json.loads(
                (output / "candidate_database.json").read_text(encoding="utf-8")
            )
            self.assertEqual(candidate_database[0]["url"], "https://camp-fire.jp/projects/199/view")

    def test_run_pipeline_retries_pending_project_even_when_listing_does_not_reach_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "database.json"
            progress = root / "progress.json"
            output = root / "output"
            database.write_text(
                json.dumps(
                    [
                        {"url": "https://camp-fire.jp/projects/199/view", "title": "checkpoint"},
                    ]
                ),
                encoding="utf-8",
            )
            progress.write_text(
                json.dumps(
                    {
                        "checkpointUrl": "https://camp-fire.jp/projects/199/view",
                        "pending": {
                            "198": {
                                "url": "https://camp-fire.jp/projects/198/view",
                                "title": "Pending project",
                                "description": "2025年8月実施予定",
                                "status": "unfinished",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            pages = {
                "https://camp-fire.jp/profile/heroines/projects": LISTING_PAGE_1,
                "https://camp-fire.jp/projects/198/view": PROJECT_PAGE,
            }

            report = run_pipeline(database, progress, output, fetch_text=pages.__getitem__)

            self.assertEqual(report["newProjectIds"], ["198"])
            self.assertEqual(report["failedProjectIds"], [])
            candidate_progress = json.loads(
                (output / "candidate_progress.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("198", candidate_progress["pending"])


if __name__ == "__main__":
    unittest.main()
