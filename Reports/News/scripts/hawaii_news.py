# ==============================================================================
# FILE: Reports/News/scripts/hawaii_news.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Hawaii state news/events collector (G3 port of G0 old/operations/news/hawaii/news.py, 2026-09-29).

Official hawaii.gov namespace only (the shared collector rejects other domains). Writes the SQLite DB to
Database Reports/News/hawaii/hawaii_news.db (git-ignored) and a small summary Reports/News/hawaii/hawaii-news-last.json.
G0 ran it daily at 10:00 HST (cronologicals/on-time/10:00). G3: on demand; the job is PROPOSED (see Reports/News/README.md).
"""
import argparse, contextlib, io, json, os, sqlite3, sys  # info: import argparse , contextlib , io , json
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
from _collector import run  # noqa: E402
STATE_SLUG = 'hawaii'  # info: set STATE_SLUG
DB_ROOT = Path(os.environ.get('RR_DATABASE_ROOT', '/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database'))  # info: set DB_ROOT
OUT = DB_ROOT / 'Reports' / 'News' / STATE_SLUG  # info: set OUT
DB = OUT / (STATE_SLUG + '_news.db')  # info: set DB
PORTAL_URL = 'https://www.hawaii.gov/'  # info: set PORTAL_URL
# Seed feeds (2026-09-29 14:2x HST): each answered 200 with >= 1 RSS item from the desk. G0 portal discovery alone found
# 0 posts (25 x HTTP 404). Not seeded: health.hawaii.gov/feed/, dlnr.hawaii.gov/blog/feed/, honolulu.gov/feed/ (200, 0 items);
# dcr.hawaii.gov/feed/, hawaiicounty.gov RSSFeed.aspx (403); kauai.gov RSSFeed.aspx (404).
# ====================================================
# SECTION: SEED_FEEDS
# What it does: Set SEED_FEEDS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
SEED_FEEDS = (  # info: set SEED_FEEDS
    'https://governor.hawaii.gov/feed/',  # info: 'https://governor.hawaii.gov/feed/' ,
    'https://ltgov.hawaii.gov/feed/',  # info: 'https://ltgov.hawaii.gov/feed/' ,
    'https://health.hawaii.gov/news/feed/',  # info: 'https://health.hawaii.gov/news/feed/' ,
    'https://dlnr.hawaii.gov/feed/',  # info: 'https://dlnr.hawaii.gov/feed/' ,
    'https://hidot.hawaii.gov/feed/',  # info: 'https://hidot.hawaii.gov/feed/' ,
    'https://dod.hawaii.gov/hiema/feed/',  # info: 'https://dod.hawaii.gov/hiema/feed/' ,
    'https://dod.hawaii.gov/feed/',  # info: 'https://dod.hawaii.gov/feed/' ,
    'https://ag.hawaii.gov/feed/',  # info: 'https://ag.hawaii.gov/feed/' ,
    'https://labor.hawaii.gov/feed/',  # info: 'https://labor.hawaii.gov/feed/' ,
    'https://cca.hawaii.gov/feed/',  # info: 'https://cca.hawaii.gov/feed/' ,
    'https://humanservices.hawaii.gov/feed/',  # info: 'https://humanservices.hawaii.gov/feed/' ,
    'https://energy.hawaii.gov/feed/',  # info: 'https://energy.hawaii.gov/feed/' ,
    'https://dbedt.hawaii.gov/feed/',  # info: 'https://dbedt.hawaii.gov/feed/' ,
    'https://dab.hawaii.gov/feed/',  # hdoa.hawaii.gov/feed/ redirects here
    'https://tax.hawaii.gov/feed/',  # info: 'https://tax.hawaii.gov/feed/' ,
    'https://www.mauicounty.gov/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml',  # County of Maui (not hawaii.gov)
)  # info: )
CHECKPOINT = '2026-03-31T00:00:00Z'  # info: set CHECKPOINT


# ====================================================
# SECTION: function summary
# What it does: summary.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def summary() -> dict:  # info: def summary
    c = sqlite3.connect(DB)  # info: set c
    try:  # info: try :
        posts = c.execute('SELECT COUNT(*) FROM posts').fetchone()[0]  # info: set posts
        events = c.execute('SELECT COUNT(*) FROM events').fetchone()[0]  # info: set events
        latest = [dict(zip(('title', 'url', 'published_at', 'source_id'), r)) for r in c.execute(  # info: set latest
            'SELECT title,url,published_at,source_id FROM posts ORDER BY COALESCE(published_at,collected_at) DESC LIMIT 10')]  # info: 'SELECT title,url,published_at,source_id FROM posts ORDER BY COALESCE(published_at,collected_at) DESC LIMIT 10
        health = dict(c.execute('SELECT status,COUNT(*) FROM source_health GROUP BY status').fetchall())  # info: set health
        last_run = (c.execute("SELECT value FROM collector_state WHERE key='last_run'").fetchone() or [None])[0]  # info: set last_run
    finally:  # info: finally :
        c.close()  # info: c . close ( )
    return {'state': STATE_SLUG, 'portal': PORTAL_URL, 'posts': posts, 'events': events, 'health': health,  # info: return { 'state' : STATE_SLUG , 'portal' :
            'last_run_utc': last_run, 'latest': latest}  # info: 'last_run_utc' : last_run , 'latest' : latest }


# ====================================================
# SECTION: block if
# What it does: __name__ == '__main__'
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
if __name__ == '__main__':  # info: if __name__ == '__main__' :
    ap = argparse.ArgumentParser(); ap.add_argument('--backfill', action='store_true'); ap.add_argument('--checkpoint', default=CHECKPOINT)  # info: set ap
    a = ap.parse_args()  # info: set a
    buf = io.StringIO()  # info: set buf
    with contextlib.redirect_stdout(buf):  # info: with contextlib . redirect_stdout ( buf ) :
        run(STATE_SLUG, PORTAL_URL, DB, a.backfill, a.checkpoint, seed_feeds=SEED_FEEDS)  # info: call run
    s = summary(); s['run'] = buf.getvalue().strip(); s['at'] = datetime.now().astimezone().isoformat(timespec='seconds')  # info: set s
    tmp = OUT / 'hawaii-news-last.json.tmp'  # info: set tmp
    tmp.write_text(json.dumps(s, indent=2, ensure_ascii=False) + '\n', encoding='utf-8'); os.replace(tmp, OUT / 'hawaii-news-last.json')  # info: tmp . write_text ( json . dumps (
    print(json.dumps({k: s[k] for k in ('posts', 'events', 'health', 'run')}, ensure_ascii=False))  # info: call print
