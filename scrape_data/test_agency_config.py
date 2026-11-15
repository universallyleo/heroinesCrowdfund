import copy
import json
import tempfile
import unittest
from pathlib import Path

import agency_config as config

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def setup_repo(root, ids=('a', 'b')):
    agencies = []
    for id in ids:
        agency = {'id': id, 'label': id, 'sources': [{'label': id, 'url': f'https://camp-fire.jp/profile/{id}'}],
                  'databasePath': f'src/lib/data/agencies/{id}/projects.json',
                  'metadataPath': f'src/lib/data/agencies/{id}/metadata.json',
                  'progressPath': f'scrape_data/progress/{id}.json', 'backupRoot': f'src/lib/data/old/{id}',
                  'scraper': {'id': 'campfire', 'discoverySources': [{'id': id, 'listingUrl': f'https://camp-fire.jp/profile/{id}/projects/post'}]}}
        agencies.append(agency)
        write(root / agency['databasePath'], [])
        write(root / agency['metadataPath'], {'schemaVersion': 1, 'agencyId': id, 'updatedAt': None})
        write(root / agency['progressPath'], {'schemaVersion': 1, 'agencyId': id, 'sources': {
            id: {'listingUrl': agency['scraper']['discoverySources'][0]['listingUrl'], 'checkpointUrl': None}}, 'pending': {}})
    registry = {'schemaVersion': 1, 'defaultAgencyId': ids[0], 'agencies': agencies}
    write(root / 'src/lib/data/agencies.json', registry)
    return registry

class AgencyConfigTests(unittest.TestCase):
    def test_committed_registry_files_and_manual_workflow_choices_agree(self):
        import re
        root = Path(__file__).resolve().parents[1]
        registry = config.read_json(root / config.REGISTRY_PATH)
        for entry in registry['agencies']:
            agency = config.resolve_agency(entry['id'],root)
            config.validate_records(config.read_json(root / agency['databasePath']))
            config.validate_metadata(config.read_json(root / agency['metadataPath']),agency)
            progress = config.read_json(root / agency['progressPath'])
            self.assertEqual(config.normalize_progress(progress,agency),progress)
        workflow = (root / '.github/workflows/update-data.yml').read_text(encoding='utf-8')
        choice_block = workflow.split('      agency:',1)[1].split('      dry_run:',1)[0]
        self.assertEqual(set(re.findall(r'^          - (\w+)$',choice_block,re.M)),{a['id'] for a in registry['agencies']})

    def test_resolution_rejects_unknown_missing_and_colliding_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); registry = setup_repo(root)
            self.assertEqual(config.resolve_agency('a', root)['id'], 'a')
            with self.assertRaises(ValueError): config.resolve_agency('unknown', root)
            for key, value in [('databasePath', registry['agencies'][0]['databasePath']), ('backupRoot', 'src/lib/data'), ('progressPath', '../escape.json')]:
                changed = copy.deepcopy(registry); changed['agencies'][1][key] = value
                write(root / 'src/lib/data/agencies.json', changed)
                with self.assertRaises(ValueError): config.resolve_agency('a', root)
            changed = copy.deepcopy(registry); changed['agencies'][1]['scraper']['id'] = 'unknown'
            write(root / 'src/lib/data/agencies.json', changed)
            with self.assertRaises(ValueError): config.resolve_agency('a', root)
            write(root / 'src/lib/data/agencies.json', registry)
            (root / registry['agencies'][0]['databasePath']).unlink()
            with self.assertRaises(ValueError): config.resolve_agency('a', root)

    def test_metadata_and_progress_ownership_and_lossless_legacy_migration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); agency = setup_repo(root, ('heroines',))['agencies'][0]
            old = {'checkpointUrl': 'https://camp-fire.jp/projects/990003/view', 'pending': {'123': {'url':'https://camp-fire.jp/projects/123/view','status':'failed','error':'retry','description':'2026年','title':'x','lastAttemptAt':None}}}
            migrated = config.normalize_progress(old, agency)
            self.assertEqual(migrated['sources']['heroines']['checkpointUrl'], old['checkpointUrl'])
            self.assertEqual({k:v for k,v in migrated['pending']['123'].items() if k!='sourceIds'}, old['pending']['123'])
            with self.assertRaises(ValueError): config.validate_metadata({'schemaVersion':1,'agencyId':'b','updatedAt':None}, agency)
            migrated['agencyId'] = 'b'
            with self.assertRaises(ValueError): config.normalize_progress(migrated, agency)

if __name__ == '__main__': unittest.main()
