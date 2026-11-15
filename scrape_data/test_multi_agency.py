import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agency_config import read_json
from scraper import run_pipeline, parse_project_page
from test_agency_config import setup_repo, write
from test_scraper import NEW_LISTING_PAGE, PROJECT_PAGE

class MultiAgencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.registry = setup_repo(self.root)
        self.a = self.registry['agencies'][0]; self.output = self.root / 'stage'

    def run_stage(self, pages):
        return run_pipeline(agency_id='a', repo_root=self.root, output_dir=self.output,
                            fetch_text=pages.__getitem__, generated_at='2026-11-15T12:00:00Z')

    def test_two_sources_deduplicate_and_do_not_touch_other_agency(self):
        self.a['scraper']['discoverySources'].append({'id':'second','listingUrl':'https://camp-fire.jp/profile/second/projects/post'})
        write(self.root / 'src/lib/data/agencies.json', self.registry)
        pages = {s['listingUrl']:NEW_LISTING_PAGE for s in self.a['scraper']['discoverySources']}
        pages['https://camp-fire.jp/projects/300/view'] = PROJECT_PAGE
        calls = []
        def fetch(url): calls.append(url); return pages[url]
        other = [(self.root / self.registry['agencies'][1][key]).read_bytes() for key in ('databasePath','metadataPath','progressPath')]
        report = run_pipeline(agency_id='a', repo_root=self.root, output_dir=self.output, fetch_text=fetch)
        self.assertEqual(report['outcome'], 'success')
        self.assertEqual(calls.count('https://camp-fire.jp/projects/300/view'), 1)
        progress = read_json(self.output / 'candidate_progress.json')
        self.assertEqual(progress['pending']['299']['sourceIds'], ['a','second'])
        self.assertEqual(progress['sources']['second']['checkpointUrl'], 'https://camp-fire.jp/projects/300/view')
        self.assertEqual(other, [(self.root / self.registry['agencies'][1][key]).read_bytes() for key in ('databasePath','metadataPath','progressPath')])

    def test_all_listings_fail_but_pending_success_can_publish(self):
        progress = read_json(self.root / self.a['progressPath'])
        progress['pending']['198'] = {'url':'https://camp-fire.jp/projects/198/view','title':'pending','description':'','status':'failed','sourceIds':['a']}
        write(self.root / self.a['progressPath'], progress)
        report = self.run_stage({'https://camp-fire.jp/projects/198/view':PROJECT_PAGE})
        self.assertEqual(report['outcome'], 'partial'); self.assertTrue(report['databaseChanged'])
        self.assertEqual(read_json(self.output / 'candidate_progress.json')['sources'], progress['sources'])
        self.assertEqual(read_json(self.output / 'candidate_progress.json')['pending'], {})

    def test_total_failure_stages_no_candidates_and_noop_retains_freshness(self):
        report = self.run_stage({})
        self.assertEqual(report['outcome'], 'failed')
        self.assertFalse((self.output / 'candidate_database.json').exists())
        record = parse_project_page(PROJECT_PAGE, 'https://camp-fire.jp/projects/300/view')
        write(self.root / self.a['databasePath'], [record])
        report = self.run_stage({self.a['scraper']['discoverySources'][0]['listingUrl']:NEW_LISTING_PAGE})
        self.assertFalse(report['databaseChanged']); self.assertFalse(report['metadataChanged'])
        self.assertIsNone(read_json(self.output / 'candidate_metadata.json')['updatedAt'])

    def test_failed_source_keeps_checkpoint_and_discards_partial_discovery(self):
        self.a['scraper']['discoverySources'].append({'id':'second','listingUrl':'https://camp-fire.jp/profile/second/projects/post'})
        write(self.root / 'src/lib/data/agencies.json', self.registry)
        broken = NEW_LISTING_PAGE + '<a href="?page=2">次のページ</a>'
        report = self.run_stage({self.a['scraper']['discoverySources'][0]['listingUrl']:broken,
                               self.a['scraper']['discoverySources'][1]['listingUrl']:NEW_LISTING_PAGE,
                               'https://camp-fire.jp/projects/300/view':PROJECT_PAGE})
        self.assertEqual(report['outcome'],'partial')
        progress = read_json(self.output / 'candidate_progress.json')
        self.assertIsNone(progress['sources']['a']['checkpointUrl'])
        self.assertEqual(progress['pending']['299']['sourceIds'],['second'])

if __name__ == '__main__': unittest.main()
