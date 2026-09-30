#!/usr/bin/env python3
"""Hawaii state news/events collector (G3 port of G0 old/operations/news/hawaii/news.py, 2026-09-29).

Official hawaii.gov namespace only (the shared collector rejects other domains). Writes the SQLite DB to
Database Reports/News/hawaii/hawaii_news.db (git-ignored) and a small summary Reports/News/hawaii/hawaii-news-last.json.
G0 ran it daily at 10:00 HST (cronologicals/on-time/10:00). G3: on demand; the job is PROPOSED (see Reports/News/README.md).
"""
import argparse, contextlib, io, json, os, sqlite3, sys
from datetime import datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _collector import run  # noqa: E402
STATE_SLUG = 'hawaii'
DB_ROOT = Path(os.environ.get('RR_DATABASE_ROOT', '/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database'))
OUT = DB_ROOT / 'Reports' / 'News' / STATE_SLUG
DB = OUT / (STATE_SLUG + '_news.db')
PORTAL_URL = 'https://www.hawaii.gov/'
# Seed feeds (2026-09-29 14:2x HST): each answered 200 with >= 1 RSS item from the desk. G0 portal discovery alone found
# 0 posts (25 x HTTP 404). Not seeded: health.hawaii.gov/feed/, dlnr.hawaii.gov/blog/feed/, honolulu.gov/feed/ (200, 0 items);
# dcr.hawaii.gov/feed/, hawaiicounty.gov RSSFeed.aspx (403); kauai.gov RSSFeed.aspx (404).
SEED_FEEDS = (
    'https://governor.hawaii.gov/feed/',
    'https://ltgov.hawaii.gov/feed/',
    'https://health.hawaii.gov/news/feed/',
    'https://dlnr.hawaii.gov/feed/',
    'https://hidot.hawaii.gov/feed/',
    'https://dod.hawaii.gov/hiema/feed/',
    'https://dod.hawaii.gov/feed/',
    'https://ag.hawaii.gov/feed/',
    'https://labor.hawaii.gov/feed/',
    'https://cca.hawaii.gov/feed/',
    'https://humanservices.hawaii.gov/feed/',
    'https://energy.hawaii.gov/feed/',
    'https://dbedt.hawaii.gov/feed/',
    'https://dab.hawaii.gov/feed/',  # hdoa.hawaii.gov/feed/ redirects here
    'https://tax.hawaii.gov/feed/',
    'https://www.mauicounty.gov/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml',  # County of Maui (not hawaii.gov)
)
CHECKPOINT = '2026-03-31T00:00:00Z'


def summary() -> dict:
    c = sqlite3.connect(DB)
    try:
        posts = c.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        events = c.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        latest = [dict(zip(('title', 'url', 'published_at', 'source_id'), r)) for r in c.execute(
            'SELECT title,url,published_at,source_id FROM posts ORDER BY COALESCE(published_at,collected_at) DESC LIMIT 10')]
        health = dict(c.execute('SELECT status,COUNT(*) FROM source_health GROUP BY status').fetchall())
        last_run = (c.execute("SELECT value FROM collector_state WHERE key='last_run'").fetchone() or [None])[0]
    finally:
        c.close()
    return {'state': STATE_SLUG, 'portal': PORTAL_URL, 'posts': posts, 'events': events, 'health': health,
            'last_run_utc': last_run, 'latest': latest}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--backfill', action='store_true'); ap.add_argument('--checkpoint', default=CHECKPOINT)
    a = ap.parse_args()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(STATE_SLUG, PORTAL_URL, DB, a.backfill, a.checkpoint, seed_feeds=SEED_FEEDS)
    s = summary(); s['run'] = buf.getvalue().strip(); s['at'] = datetime.now().astimezone().isoformat(timespec='seconds')
    tmp = OUT / 'hawaii-news-last.json.tmp'
    tmp.write_text(json.dumps(s, indent=2, ensure_ascii=False) + '\n', encoding='utf-8'); os.replace(tmp, OUT / 'hawaii-news-last.json')
    print(json.dumps({k: s[k] for k in ('posts', 'events', 'health', 'run')}, ensure_ascii=False))
