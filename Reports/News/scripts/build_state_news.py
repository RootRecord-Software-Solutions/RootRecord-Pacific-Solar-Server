# ==============================================================================
# FILE: Reports/News/scripts/build_state_news.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Run the state news collectors that are stale (WO-MIG-12).

Hawaiʻi goes through hawaii_news.py. Every other slug goes through state_news.py.
An empty database is a bounded --backfill. A database checked within the freshness
window is skipped. Default 2 workers. Paths follow RR_DATABASE_ROOT.
The job stays off until RR_STATE_NEWS=1 is registered in jobs.py.
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import os  # info: import os
import sqlite3  # info: import sqlite3
import subprocess  # info: import subprocess
import sys  # info: import sys
from concurrent.futures import ThreadPoolExecutor, as_completed  # info: from concurrent . futures import ThreadPoolExecutor , as_completed
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
PORTALS_PATH = HERE.parent / 'config' / 'state_portals.json'  # info: set PORTALS_PATH
DB_ROOT = Path(os.environ.get('RR_DATABASE_ROOT', '/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database'))  # info: set DB_ROOT
DEFAULT_MAX_AGE_MINUTES = 55  # info: set DEFAULT_MAX_AGE_MINUTES
DEFAULT_WORKERS = 2  # info: set DEFAULT_WORKERS
TIMEOUT_SECONDS = 120  # info: set TIMEOUT_SECONDS


# ====================================================
# SECTION: function parse_time
# What it does: parse time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_time(value):  # info: def parse_time
    if not value:  # info: if not value :
        return None  # info: return None
    try:  # info: try :
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)  # info: return datetime . fromisoformat ( str ( value
    except Exception:  # info: except Exception :
        return None  # info: return None


# ====================================================
# SECTION: function db_for
# What it does: db for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def db_for(slug: str) -> Path:  # info: def db_for
    return DB_ROOT / 'Reports' / 'News' / slug / f'{slug}_news.db'  # info: return DB_ROOT / 'Reports' / 'News' / slug


# ====================================================
# SECTION: function db_state
# What it does: db state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def db_state(db: Path):  # info: def db_state
    if not db.is_file():  # info: if not db . is_file ( ) :
        return False, None  # info: return False , None
    try:  # info: try :
        con = sqlite3.connect(str(db), timeout=10)  # info: set con
        try:  # info: try :
            posts = con.execute('SELECT COUNT(*) FROM posts').fetchone()[0]  # info: set posts
            events = con.execute('SELECT COUNT(*) FROM events').fetchone()[0]  # info: set events
            times = []  # info: set times
            for table, column in (  # info: for table , column in (
                ('source_health', 'last_checked_at'),  # info: call (
                ('posts', 'collected_at'),  # info: call (
                ('events', 'collected_at'),  # info: call (
            ):  # info: ) :
                try:  # info: try :
                    row = con.execute(f'SELECT MAX({column}) FROM {table}').fetchone()  # info: set row
                    if row and row[0]:  # info: if row and row [ 0 ] :
                        dt = parse_time(row[0])  # info: set dt
                        if dt:  # info: if dt :
                            times.append(dt)  # info: times . append ( dt )
                except sqlite3.Error:  # info: except sqlite3 . Error :
                    pass  # info: pass
            latest = max(times) if times else None  # info: set latest
            return bool(posts or events), latest  # info: return bool ( posts or events ) ,
        finally:  # info: finally :
            con.close()  # info: con . close ( )
    except Exception:  # info: except Exception :
        return False, None  # info: return False , None


# ====================================================
# SECTION: function collector_running
# What it does: collector running.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def collector_running(slug: str) -> bool:  # info: def collector_running
    script = 'hawaii_news.py' if slug == 'hawaii' else 'state_news.py'  # info: set script
    needle = f'{script} --state {slug}' if slug != 'hawaii' else script  # info: set needle
    try:  # info: try :
        result = subprocess.run(  # info: set result
            ['pgrep', '-f', needle],  # info: [ 'pgrep' , '-f' , needle ] ,
            stdout=subprocess.DEVNULL,  # info: set stdout
            stderr=subprocess.DEVNULL,  # info: set stderr
            timeout=3,  # info: set timeout
        )  # info: )
        return result.returncode == 0  # info: return result . returncode == 0
    except Exception:  # info: except Exception :
        return False  # info: return False


# ====================================================
# SECTION: function run_state
# What it does: run state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_state(slug: str, max_age_minutes: int, force: bool) -> dict:  # info: def run_state
    db = db_for(slug)  # info: set db
    has_content, latest = db_state(db)  # info: has_content , latest = db_state ( db )
    now = datetime.now(timezone.utc)  # info: set now
    recent = bool(latest and (now - latest).total_seconds() < max_age_minutes * 60)  # info: set recent
    if not force and has_content and recent:  # info: if not force and has_content and recent :
        return {'state': slug, 'status': 'skipped', 'reason': 'fresh', 'last_checked': latest.isoformat()}  # info: return { 'state' : slug , 'status' :
    if collector_running(slug):  # info: if collector_running ( slug ) :
        return {'state': slug, 'status': 'skipped', 'reason': 'already-running'}  # info: return { 'state' : slug , 'status' :
    backfill = not has_content  # info: set backfill
    if slug == 'hawaii':  # info: if slug == 'hawaii' :
        command = [sys.executable, str(HERE / 'hawaii_news.py')]  # info: set command
    else:  # info: else :
        command = [sys.executable, str(HERE / 'state_news.py'), '--state', slug]  # info: set command
    if backfill:  # info: if backfill :
        command.append('--backfill')  # info: command . append ( '--backfill' )
    started = now.isoformat()  # info: set started
    try:  # info: try :
        result = subprocess.run(  # info: set result
            command,  # info: command ,
            cwd=str(HERE),  # info: set cwd
            text=True,  # info: set text
            capture_output=True,  # info: set capture_output
            timeout=TIMEOUT_SECONDS,  # info: set timeout
            env=os.environ.copy(),  # info: set env
        )  # info: )
        return {  # info: return {
            'state': slug,  # info: 'state' : slug ,
            'status': 'ok' if result.returncode == 0 else 'failed',  # info: 'status' : 'ok' if result . returncode ==
            'mode': 'backfill' if backfill else 'incremental',  # info: 'mode' : 'backfill' if backfill else 'incremental' ,
            'returncode': result.returncode,  # info: 'returncode' : result . returncode ,
            'stdout': (result.stdout or '').strip()[-2000:],  # info: call 'stdout'
            'stderr': (result.stderr or '').strip()[-2000:],  # info: call 'stderr'
            'started': started,  # info: 'started' : started ,
        }  # info: }
    except subprocess.TimeoutExpired:  # info: except subprocess . TimeoutExpired :
        return {'state': slug, 'status': 'timeout', 'mode': 'backfill' if backfill else 'incremental', 'started': started}  # info: return { 'state' : slug , 'status' :
    except Exception as exc:  # info: except Exception as exc :
        return {'state': slug, 'status': 'error', 'error': repr(exc), 'started': started}  # info: return { 'state' : slug , 'status' :


# ====================================================
# SECTION: function write_log
# What it does: write log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_log(payload: dict) -> None:  # info: def write_log
    log_dir = DB_ROOT / 'Logs' / 'Reports' / 'News'  # info: set log_dir
    log_dir.mkdir(parents=True, exist_ok=True)  # info: log_dir . mkdir ( parents = True ,
    tmp = log_dir / 'build-state-news-last.json.tmp'  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, log_dir / 'build-state-news-last.json')  # info: os . replace ( tmp , log_dir /


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument('--max-age-minutes', type=int, default=DEFAULT_MAX_AGE_MINUTES)  # info: ap . add_argument ( '--max-age-minutes' , type =
    ap.add_argument('--workers', type=int, default=DEFAULT_WORKERS)  # info: ap . add_argument ( '--workers' , type =
    ap.add_argument('--force', action='store_true')  # info: ap . add_argument ( '--force' , action =
    args = ap.parse_args()  # info: set args
    portals = json.loads(PORTALS_PATH.read_text(encoding='utf-8'))  # info: set portals
    states = sorted(portals)  # info: set states
    if not states:  # info: if not states :
        print(f'ERROR: no portals in {PORTALS_PATH}')  # info: call print
        return 1  # info: return 1
    print(f'Collectors: {len(states)}  freshness: {args.max_age_minutes} min  workers: {args.workers}')  # info: call print
    results = []  # info: set results
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:  # info: with ThreadPoolExecutor ( max_workers = max ( 1
        futures = {pool.submit(run_state, slug, args.max_age_minutes, args.force): slug for slug in states}  # info: set futures
        for future in as_completed(futures):  # info: for future in as_completed ( futures ) :
            result = future.result()  # info: set result
            results.append(result)  # info: results . append ( result )
            status = result['status']  # info: set status
            slug = result['state']  # info: set slug
            if status == 'ok':  # info: if status == 'ok' :
                print(f'[{slug}] OK · {result["mode"]}')  # info: call print
            elif status == 'skipped':  # info: elif status == 'skipped' :
                print(f'[{slug}] SKIP · {result["reason"]}')  # info: call print
            elif status == 'timeout':  # info: elif status == 'timeout' :
                print(f'[{slug}] TIMEOUT')  # info: call print
            else:  # info: else :
                print(f'[{slug}] FAILED · returncode={result.get("returncode")}')  # info: call print
                if result.get('stderr'):  # info: if result . get ( 'stderr' ) :
                    print(f'  {result["stderr"]}')  # info: call print
    results.sort(key=lambda r: r['state'])  # info: results . sort ( key = lambda r
    failed = [r for r in results if r['status'] in {'failed', 'timeout', 'error'}]  # info: set failed
    payload = {  # info: set payload
        'at': datetime.now().astimezone().isoformat(timespec='seconds'),  # info: 'at' : datetime . now ( ) .
        'states': len(results),  # info: 'states' : len ( results ) ,
        'collected': sum(1 for r in results if r['status'] == 'ok'),  # info: 'collected' : sum ( 1 for r in
        'skipped': sum(1 for r in results if r['status'] == 'skipped'),  # info: 'skipped' : sum ( 1 for r in
        'failed': len(failed),  # info: 'failed' : len ( failed ) ,
        'results': results,  # info: 'results' : results ,
    }  # info: }
    write_log(payload)  # info: call write_log
    print(f"checked={payload['states']} collected={payload['collected']} skipped={payload['skipped']} failed={payload['failed']}")  # info: call print
    return 0 if not failed else 1  # info: return 0 if not failed else 1


if __name__ == '__main__':  # info: if __name__ == '__main__' :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
