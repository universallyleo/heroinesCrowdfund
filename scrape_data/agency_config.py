"""Shared registry, ownership, and snapshot validation for offline data updates."""
import copy
import hashlib
import json
import math
import re
from datetime import date, datetime
from pathlib import Path

REGISTRY_PATH = Path('src/lib/data/agencies.json')
PATH_KEYS = ('databasePath', 'metadataPath', 'progressPath')
SCRAPERS = {'campfire', 'campfire_madsink'}
PROJECT_URL = re.compile(r'https://camp-fire\.jp/projects/[0-9]+/view')

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def resolve_agency(agency_id, repo_root=Path('.')):
    root = repo_root.resolve()
    registry = read_json(root / REGISTRY_PATH)
    if registry.get('schemaVersion') != 1 or not isinstance(registry.get('agencies'), list):
        raise ValueError('Unsupported agency registry')
    ids, owned, backups = set(), set(), set()
    selected = None
    for agency in registry['agencies']:
        id = agency.get('id', '')
        if not re.fullmatch(r'[a-z][a-z0-9_]*', id) or id in ids:
            raise ValueError(f'Invalid/duplicate agency ID: {id}')
        ids.add(id)
        if not agency.get('label') or not agency.get('sources'):
            raise ValueError(f'Missing label/sources: {id}')
        for source in agency['sources']:
            if not source.get('label') or not str(source.get('url', '')).startswith('https://'):
                raise ValueError(f'Invalid attribution source: {id}')
        scraper = agency.get('scraper', {})
        if scraper.get('id') not in SCRAPERS or not scraper.get('discoverySources'):
            raise ValueError(f'Unknown scraper or missing discovery: {id}')
        sources = set()
        for source in scraper['discoverySources']:
            sid = source.get('id', '')
            if not re.fullmatch(r'[a-z][a-z0-9_]*', sid) or sid in sources or not re.fullmatch(
                r'https://camp-fire\.jp/profile/[^/?#]+/projects/post', source.get('listingUrl', '')):
                raise ValueError(f'Invalid discovery source: {id}')
            sources.add(sid)
        for key in (*PATH_KEYS, 'backupRoot'):
            raw = agency.get(key, '')
            path = (root / raw).resolve()
            if not raw or Path(raw).is_absolute() or not path.is_relative_to(root) or path == root or '..' in Path(raw).parts:
                raise ValueError(f'Unsafe {key}: {raw}')
            if key == 'backupRoot':
                if not path.is_relative_to(root / 'src/lib/data/old') or path == root / 'src/lib/data/old' or path in backups:
                    raise ValueError(f'Invalid/colliding backup root: {raw}')
                backups.add(path)
            else:
                expected = root / ('scrape_data' if key == 'progressPath' else 'src/lib/data')
                if not path.is_relative_to(expected) or path.suffix != '.json' or path in owned or path == root / REGISTRY_PATH:
                    raise ValueError(f'Invalid/colliding {key}: {raw}')
                owned.add(path)
                if not path.is_file():
                    raise ValueError(f'Missing configured file: {raw}')
        if id == agency_id:
            selected = agency
    if any(p.is_relative_to(b) for p in owned for b in backups) or any(a != b and a.is_relative_to(b) for a in backups for b in backups):
        raise ValueError('Overlapping owned and backup paths')
    if registry.get('defaultAgencyId') not in ids or selected is None:
        raise ValueError(f'Unknown/default agency ID: {agency_id}')
    return selected

def validate_metadata(value, agency):
    if value.get('schemaVersion') != 1 or value.get('agencyId') != agency['id'] or 'updatedAt' not in value:
        raise ValueError('Invalid metadata ownership/schema')
    if value['updatedAt'] is not None:
        timestamp = datetime.fromisoformat(value['updatedAt'].replace('Z', '+00:00'))
        if timestamp.tzinfo is None:
            raise ValueError('Metadata timestamp must include timezone')

def normalize_progress(value, agency):
    value = copy.deepcopy(value)
    configured = agency['scraper']['discoverySources']
    if 'schemaVersion' not in value:
        if agency['id'] != 'heroines' or [s['id'] for s in configured] != ['heroines'] or 'checkpointUrl' not in value:
            raise ValueError('Legacy progress only belongs to heroines')
        value = {'schemaVersion': 1, 'agencyId': 'heroines', 'sources': {'heroines': {
            'listingUrl': configured[0]['listingUrl'], 'checkpointUrl': value['checkpointUrl']}},
            'pending': {id: {**entry, 'sourceIds': ['heroines']} for id, entry in value['pending'].items()}}
    if value.get('schemaVersion') != 1 or value.get('agencyId') != agency['id'] or not isinstance(value.get('sources'), dict) or not isinstance(value.get('pending'), dict):
        raise ValueError('Invalid progress ownership/schema')
    for source in configured:
        previous = value['sources'].get(source['id'])
        if previous is None or previous.get('listingUrl') != source['listingUrl']:
            value['sources'][source['id']] = {'listingUrl': source['listingUrl'], 'checkpointUrl': None}
        checkpoint = value['sources'][source['id']].get('checkpointUrl')
        if checkpoint is not None and not PROJECT_URL.fullmatch(checkpoint):
            raise ValueError('Invalid checkpoint URL')
    for id, entry in value['pending'].items():
        if not id.isdigit() or entry.get('url') != f'https://camp-fire.jp/projects/{id}/view' or entry.get('status') not in ('unfinished', 'failed'):
            raise ValueError('Invalid pending project')
        if not isinstance(entry.get('sourceIds'), list) or not entry['sourceIds'] or any(s not in value['sources'] for s in entry['sourceIds']):
            raise ValueError('Invalid pending source IDs')
    return value

def validate_records(records):
    if not isinstance(records, list):
        raise ValueError('Database must be an array')
    seen = set()
    for record in records:
        url = record.get('url', '')
        if not PROJECT_URL.fullmatch(url) or url in seen:
            raise ValueError(f'Invalid/duplicate project URL: {url}')
        seen.add(url)
        if not record.get('title') or record.get('per') != '終了':
            raise ValueError(f'Invalid title/status: {url}')
        if any(not isinstance(record.get('subject', {}).get(k), str) or not record['subject'][k].strip() for k in ('group', 'member', 'type')):
            raise ValueError(f'Invalid subject: {url}')
        for key in ('total', 'rest'):
            number = record.get(key)
            if type(number) not in (int, float) or not math.isfinite(number) or number < 0 or int(number) != number:
                raise ValueError(f'Invalid {key}: {url}')
        if type(record.get('eventYear')) is not int or not 2000 <= record['eventYear'] <= 2100:
            raise ValueError(f'Invalid event year: {url}')
        if date.fromisoformat(record['start']) > date.fromisoformat(record['end']):
            raise ValueError(f'Invalid date range: {url}')
        if not isinstance(record.get('pricePatrons'), list) or not record['pricePatrons']:
            raise ValueError(f'Missing rewards: {url}')
        for reward in record['pricePatrons']:
            if any(type(reward.get(k)) is not int or reward[k] < 0 for k in ('price', 'patrons')):
                raise ValueError(f'Invalid rewards: {url}')
