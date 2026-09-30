# ==============================================================================
# FILE: Geology/scripts/earthquakes_backfill.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import gzip  # info: import gzip
import json  # info: import json
import os  # info: import os
import sqlite3  # info: import sqlite3
import time  # info: import time
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import urlencode  # info: from urllib . parse import urlencode
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
DB_PATH = DB / "Geology" / "Earthquakes" / "quakes.db"  # info: set DB_PATH
UA = "RootRecord-Pacific-Geology-backfill/1.0 (+https://rootrecord.cloud)"  # info: set UA
TIMEOUT = min(10.0, float(os.environ.get("RR_GEOLOGY_TIMEOUT", "10")))  # info: set TIMEOUT
HAWAII_START = datetime(2010, 1, 1, tzinfo=timezone.utc)   # G0
GLOBAL_START = datetime(2020, 1, 1, tzinfo=timezone.utc)   # G0
MIN_GLOBAL_MAG = 2.5  # info: set MIN_GLOBAL_MAG
SLEEP_SEC = 1.0  # info: set SLEEP_SEC
MAX_PER_QUERY = 20000  # info: set MAX_PER_QUERY
HI_BOX = dict(minlatitude=18.5, maxlatitude=22.5, minlongitude=-161, maxlongitude=-154)  # G0 box (wider than G1)


# ====================================================
# SECTION: function _get
# What it does:  get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(url: str) -> bytes:  # info: def _get
    req = Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})  # info: set req
    with urlopen(req, timeout=TIMEOUT) as r:  # info: with urlopen ( req , timeout = TIMEOUT
        raw = r.read()  # info: set raw
    return gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw  # info: return gzip . decompress ( raw ) if


# ====================================================
# SECTION: function fetch
# What it does: fetch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch(params: dict) -> dict:  # info: def fetch
    return json.loads(_get("https://earthquake.usgs.gov/fdsnws/event/1/query?" + urlencode(params)).decode("utf-8"))  # info: return json . loads ( _get ( "https://earthquake.usgs.gov/fdsnws/event/1/query?"


# ====================================================
# SECTION: function count_events
# What it does: count events.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def count_events(params: dict) -> int:  # info: def count_events
    q = urlencode({k: v for k, v in params.items() if k != "format"})  # info: set q
    return int(_get(f"https://earthquake.usgs.gov/fdsnws/event/1/count?{q}").decode().strip())  # info: return int ( _get ( f" https://earthquake.usgs.gov/fdsnws/event/1/count? {


# ====================================================
# SECTION: function connect
# What it does: connect.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def connect(path: Path) -> sqlite3.Connection:  # info: def connect
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    con = sqlite3.connect(str(path))  # info: set con
    con.execute("PRAGMA journal_mode=WAL")  # info: con . execute ( "PRAGMA journal_mode=WAL" )
    con.execute("""CREATE TABLE IF NOT EXISTS quakes (
        id TEXT PRIMARY KEY, source TEXT NOT NULL, time_ms INTEGER, time_utc TEXT, updated_ms INTEGER, updated_utc TEXT,
        latitude REAL, longitude REAL, depth_km REAL, mag REAL, mag_type TEXT, place TEXT, type TEXT, status TEXT,
        tsunami INTEGER, sig INTEGER, url TEXT, detail TEXT, raw_json TEXT NOT NULL, first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_quakes_time ON quakes(time_ms DESC)")  # info: con . execute ( "CREATE INDEX IF NOT EXISTS idx_quakes_time ON quakes(time_ms DESC)" )
    con.execute("CREATE INDEX IF NOT EXISTS idx_quakes_source ON quakes(source)")  # info: con . execute ( "CREATE INDEX IF NOT EXISTS idx_quakes_source ON quakes(source)" )
    con.commit()  # info: con . commit ( )
    return con  # info: return con


# ====================================================
# SECTION: function ms_to_iso
# What it does: ms to iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ms_to_iso(ms):  # info: def ms_to_iso
    try:  # info: try :
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat() if ms is not None else None  # info: return datetime . fromtimestamp ( ms / 1000.0
    except (TypeError, ValueError, OSError):  # info: except ( TypeError , ValueError , OSError )
        return None  # info: return None


# ====================================================
# SECTION: UPSERT
# What it does: Set UPSERT.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
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


# ====================================================
# SECTION: function ingest
# What it does: ingest.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ingest(con: sqlite3.Connection, geo: dict, source: str, now: str) -> int:  # info: def ingest
    n = 0  # info: set n
    for feat in geo.get("features") or []:  # info: for feat in geo . get ( "features"
        props, coords = feat.get("properties") or {}, (feat.get("geometry") or {}).get("coordinates") or [None, None, None]  # info: props , coords = feat . get (
        eid = feat.get("id") or props.get("code")  # info: set eid
        if not eid:  # info: if not eid :
            continue  # info: continue
        con.execute(UPSERT, (  # info: con . execute ( UPSERT , (
            eid, source, props.get("time"), ms_to_iso(props.get("time")), props.get("updated"), ms_to_iso(props.get("updated")),  # info: eid , source , props . get (
            coords[1] if len(coords) > 1 else None, coords[0] if coords else None, coords[2] if len(coords) > 2 else None,  # info: coords [ 1 ] if len ( coords
            props.get("mag"), props.get("magType"), props.get("place"), props.get("type"), props.get("status"),  # info: props . get ( "mag" ) , props
            props.get("tsunami"), props.get("sig"), props.get("url"), props.get("detail"),  # info: props . get ( "tsunami" ) , props
            json.dumps(feat, separators=(",", ":")), now, now))  # info: json . dumps ( feat , separators =
        n += 1  # info: set n
    return n  # info: return n


# ====================================================
# SECTION: function chunks
# What it does: chunks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chunks(start: datetime, end: datetime, step: timedelta):  # info: def chunks
    cur = start  # info: set cur
    while cur < end:  # info: while cur < end :
        nxt = min(cur + step, end)  # info: set nxt
        yield cur, nxt  # info: yield cur , nxt
        cur = nxt  # info: set cur


# ====================================================
# SECTION: function backfill_window
# What it does: backfill window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def backfill_window(con, source, start, end, step, extra, now) -> int:  # info: def backfill_window
    total = 0  # info: set total
    for a, b in chunks(start, end, step):  # info: for a , b in chunks ( start
        params = {"format": "geojson", "orderby": "time", "starttime": a.strftime("%Y-%m-%dT%H:%M:%S"),  # info: set params
                  "endtime": b.strftime("%Y-%m-%dT%H:%M:%S"), **extra}  # info: "endtime" : b . strftime ( "%Y-%m-%dT%H:%M:%S" )
        try:  # info: try :
            n = count_events(params)  # info: set n
        except Exception as e:  # noqa: BLE001
            print(f"  count fail {a.date()}–{b.date()}: {e}")  # info: call print
            time.sleep(SLEEP_SEC)  # info: time . sleep ( SLEEP_SEC )
            continue  # info: continue
        if n == 0:  # info: if n == 0 :
            print(f"  {source} {a.date()} → {b.date()}: 0")  # info: call print
            time.sleep(SLEEP_SEC * 0.3)  # info: time . sleep ( SLEEP_SEC * 0.3 )
            continue  # info: continue
        if n >= MAX_PER_QUERY:  # info: if n >= MAX_PER_QUERY :
            if step <= timedelta(hours=6):  # info: if step <= timedelta ( hours = 6
                print(f"  SKIP too dense {a}–{b} count={n}")  # info: call print
                time.sleep(SLEEP_SEC)  # info: time . sleep ( SLEEP_SEC )
                continue  # info: continue
            print(f"  split {a.date()}–{b.date()} count={n}")  # info: call print
            total += backfill_window(con, source, a, b, step / 2, extra, now)  # info: set total
            continue  # info: continue
        try:  # info: try :
            got = ingest(con, fetch(params), source, now)  # info: set got
            con.commit()  # info: con . commit ( )
            total += got  # info: set total
            print(f"  {source} {a.date()} → {b.date()}: count={n} upserted={got}")  # info: call print
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL {a.date()}–{b.date()}: {e}")  # info: call print
            con.rollback()  # info: con . rollback ( )
        time.sleep(SLEEP_SEC)  # info: time . sleep ( SLEEP_SEC )
    return total  # info: return total


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--hawaii-start")  # info: ap . add_argument ( "--hawaii-start" )
    ap.add_argument("--global-start")  # info: ap . add_argument ( "--global-start" )
    ap.add_argument("--days", type=int, help="shortcut: both starts = now - N days")  # info: ap . add_argument ( "--days" , type =
    ap.add_argument("--min-global", type=float, default=MIN_GLOBAL_MAG)  # info: ap . add_argument ( "--min-global" , type =
    ap.add_argument("--skip-global", action="store_true")  # info: ap . add_argument ( "--skip-global" , action =
    ap.add_argument("--db", default=str(DB_PATH))  # info: ap . add_argument ( "--db" , default =
    a = ap.parse_args()  # info: set a
    end = datetime.now(timezone.utc)  # info: set end
    day = lambda s: datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)  # noqa: E731
    hi_start = end - timedelta(days=a.days) if a.days else day(a.hawaii_start) if a.hawaii_start else HAWAII_START  # info: set hi_start
    gl_start = end - timedelta(days=a.days) if a.days else day(a.global_start) if a.global_start else GLOBAL_START  # info: set gl_start
    now, con = end.isoformat(), connect(Path(a.db))  # info: now , con = end . isoformat (
    print("=== Hawaii M≥1 ===")  # info: call print
    hi_n = backfill_window(con, "hawaii", hi_start, end, timedelta(days=31), {"minmagnitude": 1, **HI_BOX}, now)  # info: set hi_n
    print(f"Hawaii upserted (this run): {hi_n}")  # info: call print
    g_n = 0  # info: set g_n
    if not a.skip_global:  # info: if not a . skip_global :
        print("=== Global M≥%.1f ===" % a.min_global)  # info: call print
        g_n = backfill_window(con, "global", gl_start, end, timedelta(days=7), {"minmagnitude": a.min_global}, now)  # info: set g_n
        print(f"Global upserted (this run): {g_n}")  # info: call print
    total = con.execute("SELECT COUNT(*) FROM quakes").fetchone()[0]  # info: set total
    by = list(con.execute("SELECT source, COUNT(*) FROM quakes GROUP BY source"))  # info: set by
    con.close()  # info: con . close ( )
    print(json.dumps({"ok": True, "db": a.db, "hawaii_upserted": hi_n, "global_upserted": g_n, "total": total, "by_source": by}))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
