#!/usr/bin/env python3
"""Build the global news index from state databases already on disk (WO-MIG-12).

Does not collect. Does not invent stories. Empty and missing states stay visible
in collection_health. locations stays empty until the country location pollers land.
Writes Database Reports/News/global/global-news-last.json. The job stays off
until RR_GLOBAL_NEWS=1 is registered in jobs.py.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORTALS_PATH = HERE.parent / 'config' / 'state_portals.json'
DB_ROOT = Path(os.environ.get('RR_DATABASE_ROOT', '/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database'))
NEWS_ROOT = DB_ROOT / 'Reports' / 'News'
OUT = NEWS_ROOT / 'global' / 'global-news-last.json'
LOG = DB_ROOT / 'Logs' / 'Reports' / 'News' / 'build-global-news-last.json'

DISPLAY = {
    'new-york': 'New York', 'new-jersey': 'New Jersey',
    'north-carolina': 'North Carolina', 'south-carolina': 'South Carolina',
    'north-dakota': 'North Dakota', 'south-dakota': 'South Dakota',
    'west-virginia': 'West Virginia', 'new-mexico': 'New Mexico',
    'rhode-island': 'Rhode Island', 'new-hampshire': 'New Hampshire',
}
STATE_CODES = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO',
    'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA',
    'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
    'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
    'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',
    'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY',
}
REGION = {
    'AL': 'south', 'AK': 'north-america', 'AZ': 'southwest', 'AR': 'south', 'CA': 'west', 'CO': 'west',
    'CT': 'northeast', 'DE': 'northeast', 'FL': 'south', 'GA': 'south', 'HI': 'pacific', 'ID': 'west',
    'IL': 'midwest', 'IN': 'midwest', 'IA': 'midwest', 'KS': 'midwest', 'KY': 'south', 'LA': 'south',
    'ME': 'northeast', 'MD': 'northeast', 'MA': 'northeast', 'MI': 'midwest', 'MN': 'midwest', 'MS': 'south',
    'MO': 'midwest', 'MT': 'west', 'NE': 'midwest', 'NV': 'west', 'NH': 'northeast', 'NJ': 'northeast',
    'NM': 'southwest', 'NY': 'northeast', 'NC': 'south', 'ND': 'midwest', 'OH': 'midwest', 'OK': 'south',
    'OR': 'west', 'PA': 'northeast', 'RI': 'northeast', 'SC': 'south', 'SD': 'midwest', 'TN': 'south',
    'TX': 'south', 'UT': 'west', 'VT': 'northeast', 'VA': 'south', 'WA': 'west', 'WV': 'south',
    'WI': 'midwest', 'WY': 'west',
}
WEIGHTS = {
    'emergency': 100, 'hazards': 100, 'health': 85, 'government': 80, 'science': 70,
    'environment': 70, 'infrastructure': 65, 'utilities': 65, 'education': 55,
    'business': 50, 'community': 45, 'culture': 45, 'events': 35,
}


def score(category) -> int:
    c = (category or 'general').lower()
    for key, weight in WEIGHTS.items():
        if key in c:
            return weight
    return 40


def parse_ts(value) -> int:
    if not value:
        return 0
    text = str(value)
    for fmt, n in (('%Y-%m-%dT%H:%M:%S', 19), ('%Y-%m-%d', 10)):
        try:
            return int(time.mktime(time.strptime(text[:n], fmt)))
        except Exception:
            continue
    return 0


def display_name(slug: str) -> str:
    return DISPLAY.get(slug, slug.replace('-', ' ').title())


def db_health(path: Path) -> dict:
    result = {'database': str(path), 'posts': 0, 'events': 0, 'sources': 0, 'source_health': {}}
    try:
        con = sqlite3.connect(path)
        result['posts'] = con.execute('select count(*) from posts').fetchone()[0]
        result['events'] = con.execute('select count(*) from events').fetchone()[0]
        result['sources'] = con.execute('select count(*) from sources').fetchone()[0]
        try:
            for status, count in con.execute('select status,count(*) from source_health group by status'):
                result['source_health'][status] = count
        except sqlite3.Error:
            pass
        con.close()
    except sqlite3.Error as exc:
        result['error'] = str(exc)
    return result


def read_db(path: Path, slug: str):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    posts, events = [], []
    st = display_name(slug)
    code = STATE_CODES.get(st)
    region = REGION.get(code, 'north-america')
    try:
        for r in con.execute('select p.*, s.publisher from posts p left join sources s on p.source_id=s.source_id'):
            posts.append({
                'title': r['title'], 'summary': r['summary'], 'link': r['url'],
                'published_label': r['published_at'], 'published_ts': parse_ts(r['published_at']),
                'category': r['category'] or 'general',
                'category_label': (r['category'] or 'General').replace('-', ' ').title(),
                'source_id': r['source_id'], 'source': r['publisher'] or r['source_id'] or 'Source',
                'country_code': 'US', 'region': region,
                'state_code': code, 'state_name': st, 'location': None,
                'importance': score(r['category']),
            })
        for r in con.execute('select e.*, s.publisher from events e left join sources s on e.source_id=s.source_id'):
            events.append({
                'title': r['title'], 'description': r['description'], 'link': r['url'],
                'start_label': r['start_at'], 'start_ts': parse_ts(r['start_at']),
                'location': r['location'], 'type': r['category'] or 'Event',
                'source': r['publisher'] or r['source_id'] or 'Source',
                'state_code': code, 'state_name': st, 'country_code': 'US', 'region': region,
            })
    finally:
        con.close()
    return posts, events


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def main() -> int:
    portals = json.loads(PORTALS_PATH.read_text(encoding='utf-8'))
    items, ev, health = [], [], []
    for slug in sorted(portals):
        db = NEWS_ROOT / slug / f'{slug}_news.db'
        if not db.is_file():
            health.append({'state': slug, 'database': None, 'posts': 0, 'events': 0, 'sources': 0, 'status': 'missing_database'})
            continue
        h = db_health(db)
        h.update({'state': slug, 'status': 'ok' if h['posts'] or h['events'] else 'empty'})
        health.append(h)
        if h.get('error'):
            continue
        p, e = read_db(db, slug)
        items.extend(p)
        ev.extend(e)
    uniq = {x['link']: x for x in items if x.get('link')}
    items = sorted(uniq.values(), key=lambda x: (x['importance'], x['published_ts']), reverse=True)
    ev = sorted(
        {(x['title'], x.get('start_label'), x.get('link')): x for x in ev}.values(),
        key=lambda x: x.get('start_ts', 0),
    )
    payload = {
        'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'items': items[:5000],
        'events': ev[:1000],
        'collection_health': health,
        'locations': [],
    }
    write_json(OUT, payload)
    write_json(LOG, {
        'at': payload['generated_at'],
        'posts': len(items),
        'events': len(ev),
        'states': len(health),
        'out': str(OUT),
    })
    print(f'global news index: {len(items)} posts, {len(ev)} events, {len(health)} states -> {OUT}')
    for h in health:
        print(f"  {h.get('state')}: {h.get('status')} posts={h.get('posts', 0)} events={h.get('events', 0)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
