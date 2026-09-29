#!/usr/bin/env python3
"""USGS earthquake backfill into SQLite (G3 port of G0 `old` operations/backfillquakes.py). Stdlib only. ON DEMAND.

  python3 earthquakes_backfill.py [--hawaii-start YYYY-MM-DD] [--global-start YYYY-MM-DD] [--days N]
                                  [--min-global 2.5] [--skip-global] [--db PATH]

Hawaiʻi: M>=1.0, island box, monthly chunks.  Global: M>=min_global, weekly chunks.
Respects the USGS 20k/query cap by counting first (fdsnws/event/1/count) and halving dense windows.
Same `quakes` table + UPSERT as G0 (id, source, time, lat/lon/depth, mag, place, status, tsunami, sig, url, raw_json,
first_seen/last_seen). DB default: Database Geology/Earthquakes/quakes.db (git-ignored binary).
Changes from G0 (documented): DB path (was /home/ava-core/database/quakes.db); --days / start flags instead of editing
constants (G0 defaults kept: HI 2010-01-01, global 2020-01-01 — a full default run is thousands of requests, operator
decision only); 10 s timeout per request (G0: 60/120 s); polite 1 s sleep kept. NOT scheduled (no jobs.py entry).
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
DB_PATH = DB / "Geology" / "Earthquakes" / "quakes.db"
UA = "RootRecord-Pacific-Geology-backfill/1.0 (+https://rootrecord.cloud)"
TIMEOUT = min(10.0, float(os.environ.get("RR_GEOLOGY_TIMEOUT", "10")))
HAWAII_START = datetime(2010, 1, 1, tzinfo=timezone.utc)   # G0
GLOBAL_START = datetime(2020, 1, 1, tzinfo=timezone.utc)   # G0
MIN_GLOBAL_MAG = 2.5
SLEEP_SEC = 1.0
MAX_PER_QUERY = 20000
HI_BOX = dict(minlatitude=18.5, maxlatitude=22.5, minlongitude=-161, maxlongitude=-154)  # G0 box (wider than G1)


def _get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urlopen(req, timeout=TIMEOUT) as r:
        raw = r.read()
    return gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw


def fetch(params: dict) -> dict:
    return json.loads(_get("https://earthquake.usgs.gov/fdsnws/event/1/query?" + urlencode(params)).decode("utf-8"))


def count_events(params: dict) -> int:
    q = urlencode({k: v for k, v in params.items() if k != "format"})
    return int(_get(f"https://earthquake.usgs.gov/fdsnws/event/1/count?{q}").decode().strip())


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS quakes (
        id TEXT PRIMARY KEY, source TEXT NOT NULL, time_ms INTEGER, time_utc TEXT, updated_ms INTEGER, updated_utc TEXT,
        latitude REAL, longitude REAL, depth_km REAL, mag REAL, mag_type TEXT, place TEXT, type TEXT, status TEXT,
        tsunami INTEGER, sig INTEGER, url TEXT, detail TEXT, raw_json TEXT NOT NULL, first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_quakes_time ON quakes(time_ms DESC)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_quakes_source ON quakes(source)")
    con.commit()
    return con


def ms_to_iso(ms):
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat() if ms is not None else None
    except (TypeError, ValueError, OSError):
        return None


UPSERT = """
INSERT INTO quakes (id, source, time_ms, time_utc, updated_ms, updated_utc, latitude, longitude, depth_km, mag, mag_type,
    place, type, status, tsunami, sig, url, detail, raw_json, first_seen, last_seen)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
ON CONFLICT(id) DO UPDATE SET
    source=excluded.source, time_ms=excluded.time_ms, time_utc=excluded.time_utc, updated_ms=excluded.updated_ms,
    updated_utc=excluded.updated_utc, latitude=excluded.latitude, longitude=excluded.longitude,
    depth_km=excluded.depth_km, mag=excluded.mag, mag_type=excluded.mag_type, place=excluded.place, type=excluded.type,
    status=excluded.status, tsunami=excluded.tsunami, sig=excluded.sig, url=excluded.url, detail=excluded.detail,
    raw_json=excluded.raw_json, last_seen=excluded.last_seen
"""


def ingest(con: sqlite3.Connection, geo: dict, source: str, now: str) -> int:
    n = 0
    for feat in geo.get("features") or []:
        props, coords = feat.get("properties") or {}, (feat.get("geometry") or {}).get("coordinates") or [None, None, None]
        eid = feat.get("id") or props.get("code")
        if not eid:
            continue
        con.execute(UPSERT, (
            eid, source, props.get("time"), ms_to_iso(props.get("time")), props.get("updated"), ms_to_iso(props.get("updated")),
            coords[1] if len(coords) > 1 else None, coords[0] if coords else None, coords[2] if len(coords) > 2 else None,
            props.get("mag"), props.get("magType"), props.get("place"), props.get("type"), props.get("status"),
            props.get("tsunami"), props.get("sig"), props.get("url"), props.get("detail"),
            json.dumps(feat, separators=(",", ":")), now, now))
        n += 1
    return n


def chunks(start: datetime, end: datetime, step: timedelta):
    cur = start
    while cur < end:
        nxt = min(cur + step, end)
        yield cur, nxt
        cur = nxt


def backfill_window(con, source, start, end, step, extra, now) -> int:
    total = 0
    for a, b in chunks(start, end, step):
        params = {"format": "geojson", "orderby": "time", "starttime": a.strftime("%Y-%m-%dT%H:%M:%S"),
                  "endtime": b.strftime("%Y-%m-%dT%H:%M:%S"), **extra}
        try:
            n = count_events(params)
        except Exception as e:  # noqa: BLE001
            print(f"  count fail {a.date()}–{b.date()}: {e}")
            time.sleep(SLEEP_SEC)
            continue
        if n == 0:
            print(f"  {source} {a.date()} → {b.date()}: 0")
            time.sleep(SLEEP_SEC * 0.3)
            continue
        if n >= MAX_PER_QUERY:
            if step <= timedelta(hours=6):
                print(f"  SKIP too dense {a}–{b} count={n}")
                time.sleep(SLEEP_SEC)
                continue
            print(f"  split {a.date()}–{b.date()} count={n}")
            total += backfill_window(con, source, a, b, step / 2, extra, now)
            continue
        try:
            got = ingest(con, fetch(params), source, now)
            con.commit()
            total += got
            print(f"  {source} {a.date()} → {b.date()}: count={n} upserted={got}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL {a.date()}–{b.date()}: {e}")
            con.rollback()
        time.sleep(SLEEP_SEC)
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hawaii-start")
    ap.add_argument("--global-start")
    ap.add_argument("--days", type=int, help="shortcut: both starts = now - N days")
    ap.add_argument("--min-global", type=float, default=MIN_GLOBAL_MAG)
    ap.add_argument("--skip-global", action="store_true")
    ap.add_argument("--db", default=str(DB_PATH))
    a = ap.parse_args()
    end = datetime.now(timezone.utc)
    day = lambda s: datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)  # noqa: E731
    hi_start = end - timedelta(days=a.days) if a.days else day(a.hawaii_start) if a.hawaii_start else HAWAII_START
    gl_start = end - timedelta(days=a.days) if a.days else day(a.global_start) if a.global_start else GLOBAL_START
    now, con = end.isoformat(), connect(Path(a.db))
    print("=== Hawaii M≥1 ===")
    hi_n = backfill_window(con, "hawaii", hi_start, end, timedelta(days=31), {"minmagnitude": 1, **HI_BOX}, now)
    print(f"Hawaii upserted (this run): {hi_n}")
    g_n = 0
    if not a.skip_global:
        print("=== Global M≥%.1f ===" % a.min_global)
        g_n = backfill_window(con, "global", gl_start, end, timedelta(days=7), {"minmagnitude": a.min_global}, now)
        print(f"Global upserted (this run): {g_n}")
    total = con.execute("SELECT COUNT(*) FROM quakes").fetchone()[0]
    by = list(con.execute("SELECT source, COUNT(*) FROM quakes GROUP BY source"))
    con.close()
    print(json.dumps({"ok": True, "db": a.db, "hawaii_upserted": hi_n, "global_upserted": g_n, "total": total, "by_source": by}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
