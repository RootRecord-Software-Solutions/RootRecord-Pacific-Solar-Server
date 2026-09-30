#!/usr/bin/env python3
"""Run the state news collectors that are stale (WO-MIG-12).

Hawaiʻi goes through hawaii_news.py. Every other slug goes through state_news.py.
An empty database is a bounded --backfill. A database checked within the freshness
window is skipped. Default 2 workers. Paths follow RR_DATABASE_ROOT.
The job stays off until RR_STATE_NEWS=1 is registered in jobs.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORTALS_PATH = HERE.parent / 'config' / 'state_portals.json'
DB_ROOT = Path(os.environ.get('RR_DATABASE_ROOT', '/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database'))
DEFAULT_MAX_AGE_MINUTES = 55
DEFAULT_WORKERS = 2
TIMEOUT_SECONDS = 120


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)
    except Exception:
        return None


def db_for(slug: str) -> Path:
    return DB_ROOT / 'Reports' / 'News' / slug / f'{slug}_news.db'


def db_state(db: Path):
    if not db.is_file():
        return False, None
    try:
        con = sqlite3.connect(str(db), timeout=10)
        try:
            posts = con.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
            events = con.execute('SELECT COUNT(*) FROM events').fetchone()[0]
            times = []
            for table, column in (
                ('source_health', 'last_checked_at'),
                ('posts', 'collected_at'),
                ('events', 'collected_at'),
            ):
                try:
                    row = con.execute(f'SELECT MAX({column}) FROM {table}').fetchone()
                    if row and row[0]:
                        dt = parse_time(row[0])
                        if dt:
                            times.append(dt)
                except sqlite3.Error:
                    pass
            latest = max(times) if times else None
            return bool(posts or events), latest
        finally:
            con.close()
    except Exception:
        return False, None


def collector_running(slug: str) -> bool:
    script = 'hawaii_news.py' if slug == 'hawaii' else 'state_news.py'
    needle = f'{script} --state {slug}' if slug != 'hawaii' else script
    try:
        result = subprocess.run(
            ['pgrep', '-f', needle],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False


def run_state(slug: str, max_age_minutes: int, force: bool) -> dict:
    db = db_for(slug)
    has_content, latest = db_state(db)
    now = datetime.now(timezone.utc)
    recent = bool(latest and (now - latest).total_seconds() < max_age_minutes * 60)
    if not force and has_content and recent:
        return {'state': slug, 'status': 'skipped', 'reason': 'fresh', 'last_checked': latest.isoformat()}
    if collector_running(slug):
        return {'state': slug, 'status': 'skipped', 'reason': 'already-running'}
    backfill = not has_content
    if slug == 'hawaii':
        command = [sys.executable, str(HERE / 'hawaii_news.py')]
    else:
        command = [sys.executable, str(HERE / 'state_news.py'), '--state', slug]
    if backfill:
        command.append('--backfill')
    started = now.isoformat()
    try:
        result = subprocess.run(
            command,
            cwd=str(HERE),
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            env=os.environ.copy(),
        )
        return {
            'state': slug,
            'status': 'ok' if result.returncode == 0 else 'failed',
            'mode': 'backfill' if backfill else 'incremental',
            'returncode': result.returncode,
            'stdout': (result.stdout or '').strip()[-2000:],
            'stderr': (result.stderr or '').strip()[-2000:],
            'started': started,
        }
    except subprocess.TimeoutExpired:
        return {'state': slug, 'status': 'timeout', 'mode': 'backfill' if backfill else 'incremental', 'started': started}
    except Exception as exc:
        return {'state': slug, 'status': 'error', 'error': repr(exc), 'started': started}


def write_log(payload: dict) -> None:
    log_dir = DB_ROOT / 'Logs' / 'Reports' / 'News'
    log_dir.mkdir(parents=True, exist_ok=True)
    tmp = log_dir / 'build-state-news-last.json.tmp'
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    os.replace(tmp, log_dir / 'build-state-news-last.json')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-age-minutes', type=int, default=DEFAULT_MAX_AGE_MINUTES)
    ap.add_argument('--workers', type=int, default=DEFAULT_WORKERS)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    portals = json.loads(PORTALS_PATH.read_text(encoding='utf-8'))
    states = sorted(portals)
    if not states:
        print(f'ERROR: no portals in {PORTALS_PATH}')
        return 1
    print(f'Collectors: {len(states)}  freshness: {args.max_age_minutes} min  workers: {args.workers}')
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(run_state, slug, args.max_age_minutes, args.force): slug for slug in states}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status = result['status']
            slug = result['state']
            if status == 'ok':
                print(f'[{slug}] OK · {result["mode"]}')
            elif status == 'skipped':
                print(f'[{slug}] SKIP · {result["reason"]}')
            elif status == 'timeout':
                print(f'[{slug}] TIMEOUT')
            else:
                print(f'[{slug}] FAILED · returncode={result.get("returncode")}')
                if result.get('stderr'):
                    print(f'  {result["stderr"]}')
    results.sort(key=lambda r: r['state'])
    failed = [r for r in results if r['status'] in {'failed', 'timeout', 'error'}]
    payload = {
        'at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'states': len(results),
        'collected': sum(1 for r in results if r['status'] == 'ok'),
        'skipped': sum(1 for r in results if r['status'] == 'skipped'),
        'failed': len(failed),
        'results': results,
    }
    write_log(payload)
    print(f"checked={payload['states']} collected={payload['collected']} skipped={payload['skipped']} failed={payload['failed']}")
    return 0 if not failed else 1


if __name__ == '__main__':
    raise SystemExit(main())
