#!/usr/bin/env python3
"""One official-portal news collector for a US state other than Hawaiʻi (WO-MIG-12).

Portal URLs live in Reports/News/config/state_portals.json. Hawaiʻi stays on
hawaii_news.py so its 16 seed feeds are unchanged. Writes Database
Reports/News/<slug>/<slug>_news.db (git-ignored) and <slug>-news-last.json.
"""
import argparse, contextlib, io, json, os, sqlite3, sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _collector import run  # noqa: E402

PORTALS_PATH = HERE.parent / 'config' / 'state_portals.json'
DB_ROOT = Path(os.environ.get('RR_DATABASE_ROOT', '/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database'))
CHECKPOINT = '2026-03-31T00:00:00Z'


def load_portals() -> dict:
    data = json.loads(PORTALS_PATH.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not data:
        raise SystemExit(f'ERROR: portal list is empty: {PORTALS_PATH}')
    return data


def summary(slug: str, portal: str, db: Path) -> dict:
    c = sqlite3.connect(db)
    try:
        posts = c.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        events = c.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        latest = [dict(zip(('title', 'url', 'published_at', 'source_id'), r)) for r in c.execute(
            'SELECT title,url,published_at,source_id FROM posts ORDER BY COALESCE(published_at,collected_at) DESC LIMIT 10')]
        health = dict(c.execute('SELECT status,COUNT(*) FROM source_health GROUP BY status').fetchall())
        last_run = (c.execute("SELECT value FROM collector_state WHERE key='last_run'").fetchone() or [None])[0]
    finally:
        c.close()
    return {'state': slug, 'portal': portal, 'posts': posts, 'events': events, 'health': health,
            'last_run_utc': last_run, 'latest': latest}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', required=True)
    ap.add_argument('--backfill', action='store_true')
    ap.add_argument('--checkpoint', default=CHECKPOINT)
    a = ap.parse_args()
    slug = a.state.strip().lower()
    if slug == 'hawaii':
        print('hawaii is collected by hawaii_news.py (16 seed feeds). This script skips it.', file=sys.stderr)
        return 2
    portals = load_portals()
    if slug not in portals:
        print(f'ERROR: unknown state {slug!r}. Known: {", ".join(sorted(portals))}', file=sys.stderr)
        return 2
    portal = portals[slug]
    out = DB_ROOT / 'Reports' / 'News' / slug
    db = out / (slug + '_news.db')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(slug, portal, db, a.backfill, a.checkpoint)
    s = summary(slug, portal, db)
    s['run'] = buf.getvalue().strip()
    s['at'] = datetime.now().astimezone().isoformat(timespec='seconds')
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / f'{slug}-news-last.json.tmp'
    tmp.write_text(json.dumps(s, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    os.replace(tmp, out / f'{slug}-news-last.json')
    print(json.dumps({k: s[k] for k in ('posts', 'events', 'health', 'run')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
