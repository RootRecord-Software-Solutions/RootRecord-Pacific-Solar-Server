# ==============================================================================
# FILE: Reports/News/scripts/state_news.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""One official-portal news collector for a US state other than Hawaiʻi (WO-MIG-12).

Portal URLs live in Reports/News/config/state_portals.json. Hawaiʻi stays on
hawaii_news.py so its 16 seed feeds are unchanged. Writes Database
Reports/News/<slug>/<slug>_news.db (git-ignored) and <slug>-news-last.json.
"""
import argparse, contextlib, io, json, os, sqlite3, sys  # info: import argparse , contextlib , io , json
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
from _collector import run  # noqa: E402

PORTALS_PATH = HERE.parent / 'config' / 'state_portals.json'  # info: set PORTALS_PATH
DB_ROOT = Path(os.environ.get('RR_DATABASE_ROOT', '/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database'))  # info: set DB_ROOT
CHECKPOINT = '2026-03-31T00:00:00Z'  # info: set CHECKPOINT


# ====================================================
# SECTION: function load_portals
# What it does: load portals.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_portals() -> dict:  # info: def load_portals
    data = json.loads(PORTALS_PATH.read_text(encoding='utf-8'))  # info: set data
    if not isinstance(data, dict) or not data:  # info: if not isinstance ( data , dict )
        raise SystemExit(f'ERROR: portal list is empty: {PORTALS_PATH}')  # info: raise SystemExit ( f' ERROR: portal list is empty: { PORTALS_PATH }
    return data  # info: return data


# ====================================================
# SECTION: function summary
# What it does: summary.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def summary(slug: str, portal: str, db: Path) -> dict:  # info: def summary
    c = sqlite3.connect(db)  # info: set c
    try:  # info: try :
        posts = c.execute('SELECT COUNT(*) FROM posts').fetchone()[0]  # info: set posts
        events = c.execute('SELECT COUNT(*) FROM events').fetchone()[0]  # info: set events
        latest = [dict(zip(('title', 'url', 'published_at', 'source_id'), r)) for r in c.execute(  # info: set latest
            'SELECT title,url,published_at,source_id FROM posts ORDER BY COALESCE(published_at,collected_at) DESC LIMIT 10')]  # info: 'SELECT title,url,published_at,source_id FROM posts ORDER BY COALESCE(published_at,collected_at) DESC LIMIT 10
        health = dict(c.execute('SELECT status,COUNT(*) FROM source_health GROUP BY status').fetchall())  # info: set health
        last_run = (c.execute("SELECT value FROM collector_state WHERE key='last_run'").fetchone() or [None])[0]  # info: set last_run
    finally:  # info: finally :
        c.close()  # info: c . close ( )
    return {'state': slug, 'portal': portal, 'posts': posts, 'events': events, 'health': health,  # info: return { 'state' : slug , 'portal' :
            'last_run_utc': last_run, 'latest': latest}  # info: 'last_run_utc' : last_run , 'latest' : latest }


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument('--state', required=True)  # info: ap . add_argument ( '--state' , required =
    ap.add_argument('--backfill', action='store_true')  # info: ap . add_argument ( '--backfill' , action =
    ap.add_argument('--checkpoint', default=CHECKPOINT)  # info: ap . add_argument ( '--checkpoint' , default =
    a = ap.parse_args()  # info: set a
    slug = a.state.strip().lower()  # info: set slug
    if slug == 'hawaii':  # info: if slug == 'hawaii' :
        print('hawaii is collected by hawaii_news.py (16 seed feeds). This script skips it.', file=sys.stderr)  # info: call print
        return 2  # info: return 2
    portals = load_portals()  # info: set portals
    if slug not in portals:  # info: if slug not in portals :
        print(f'ERROR: unknown state {slug!r}. Known: {", ".join(sorted(portals))}', file=sys.stderr)  # info: call print
        return 2  # info: return 2
    portal = portals[slug]  # info: set portal
    out = DB_ROOT / 'Reports' / 'News' / slug  # info: set out
    db = out / (slug + '_news.db')  # info: set db
    buf = io.StringIO()  # info: set buf
    with contextlib.redirect_stdout(buf):  # info: with contextlib . redirect_stdout ( buf ) :
        run(slug, portal, db, a.backfill, a.checkpoint)  # info: call run
    s = summary(slug, portal, db)  # info: set s
    s['run'] = buf.getvalue().strip()  # info: s [ 'run' ] = buf . getvalue
    s['at'] = datetime.now().astimezone().isoformat(timespec='seconds')  # info: s [ 'at' ] = datetime . now
    out.mkdir(parents=True, exist_ok=True)  # info: out . mkdir ( parents = True ,
    tmp = out / f'{slug}-news-last.json.tmp'  # info: set tmp
    tmp.write_text(json.dumps(s, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, out / f'{slug}-news-last.json')  # info: os . replace ( tmp , out /
    print(json.dumps({k: s[k] for k in ('posts', 'events', 'health', 'run')}, ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == '__main__':  # info: if __name__ == '__main__' :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
