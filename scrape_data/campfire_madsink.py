"""MAD’S iNK title/year details; HTML financial extraction remains shared.

Membership is a reviewed mapping, not an assumption inferred from an idol's name.
Unknown members and ambiguous event years remain pending for manual review.
"""
import copy
import json
import re
from pathlib import Path

MEMBERS_PATH = Path(__file__).with_name('madsink_members.json')

def refresh_groups(records):
    """Apply a reviewed membership revision to historical rows, without re-fetching pages."""
    from scraper import ParseError
    members = json.loads(MEMBERS_PATH.read_text(encoding='utf-8'))['members']
    result = copy.deepcopy(records)
    for record in result:
        member = record['subject']['member']
        if member not in members:
            raise ParseError(f'Unreviewed MAD’S iNK member/group mapping: {member}')
        record['subject']['group'] = '/'.join(members[member])
    return result

def parse_details(title, soup, description):
    # Import lazily so this adapter can also be imported independently in tests.
    from scraper import ParseError
    normalized = re.sub(r'[【】〖〗]', '', title).strip()
    match = re.fullmatch(r'(.+?)\s*(生誕祭|LAST LIVE)\s*(?:20\d{2})?\s*(?:応援)?プロジェクト\s*(?:20\d{2})?', normalized)
    if not match:
        raise ParseError(f'Unrecognized MAD’S iNK title: {title}')
    member, event_type = match.groups()
    member = member.strip()
    members = json.loads(MEMBERS_PATH.read_text(encoding='utf-8'))['members']
    if member not in members:
        raise ParseError(f'Unreviewed MAD’S iNK member/group mapping: {member}')
    years = {int(y) for y in re.findall(r'(?<!\d)(20\d{2})(?!\d)', title)}
    story = ' '.join(el.get_text(' ', strip=True) for el in soup.select('.fr-view'))
    years.update(int(y) for y in re.findall(r'生誕イベント\s*[:：]\s*(20\d{2})年', story))
    years.update(int(y) for y in re.findall(r'(?<!\d)(20\d{2})年', description))
    if len(years) != 1:
        raise ParseError(f'Ambiguous MAD’S iNK event year: {sorted(years)}: {title}')
    return {'group': '/'.join(members[member]), 'member': member,
            'type': '生誕・卒業公演' if event_type == 'LAST LIVE' else event_type}, years.pop()
