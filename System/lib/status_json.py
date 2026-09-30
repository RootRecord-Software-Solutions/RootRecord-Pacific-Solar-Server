# ==============================================================================
# FILE: System/lib/status_json.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Write one clean transmission JSON: current values + latest closed 5min averages."""  # info: """Write one clean transmission JSON: current values + latest closed 5min averages."""
from __future__ import annotations  # info: from __future__ import annotations
import json  # info: import json
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

import paths  # info: import paths
from db.store import connect, connect_layer  # info: from db . store import connect , connect_layer

LOCAL = ZoneInfo("Pacific/Honolulu")  # info: set LOCAL
STATUS_PATH = paths.SYSTEM_DATA / "status" / "system-status.json"  # info: set STATUS_PATH

# ====================================================
# SECTION: function _iso_now
# What it does:  iso now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _iso_now():  # info: def _iso_now
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")  # info: return datetime . now ( timezone . utc

# ====================================================
# SECTION: function _latest_raw
# What it does:  latest raw.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _latest_raw(conn) -> dict:  # info: def _latest_raw
    row = conn.execute(  # info: set row
        "SELECT observation_id, observed_at, host FROM observation ORDER BY observed_at DESC LIMIT 1"  # info: "SELECT observation_id, observed_at, host FROM observation ORDER BY observed_at DESC LIMIT 1"
    ).fetchone()  # info: ) . fetchone ( )
    if not row:  # info: if not row :
        return {}  # info: return { }
    obs_id, at, host = row[0], row[1], row[2]  # info: obs_id , at , host = row [
    metrics = {}  # info: set metrics
    for r in conn.execute(  # info: for r in conn . execute (
        "SELECT metric_key, value_num, unit, state FROM measurement WHERE observation_id=?",  # info: "SELECT metric_key, value_num, unit, state FROM measurement WHERE observation_id=?" ,
        (obs_id,),  # info: call (
    ):  # info: ) :
        metrics[r["metric_key"]] = {  # info: metrics [ r [ "metric_key" ] ] =
            "value": r["value_num"],  # info: "value" : r [ "value_num" ] ,
            "unit": r["unit"],  # info: "unit" : r [ "unit" ] ,
            "state": r["state"],  # info: "state" : r [ "state" ] ,
        }  # info: }
    return {"observed_at": at, "host": host, "metrics": metrics}  # info: return { "observed_at" : at , "host" :

# ====================================================
# SECTION: function _latest_5min
# What it does:  latest 5min.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _latest_5min(layer_conn) -> dict:  # info: def _latest_5min
    run = layer_conn.execute(  # info: set run
        """SELECT aggregation_run_id, period_start, period_end, completed_at
           FROM aggregation_run
           WHERE layer='5min' AND status='complete'
           ORDER BY period_end DESC LIMIT 1"""
    ).fetchone()  # info: ) . fetchone ( )
    if not run:  # info: if not run :
        return {}  # info: return { }
    metrics = {}  # info: set metrics
    for r in layer_conn.execute(  # info: for r in layer_conn . execute (
        """SELECT metric_key, value_avg, value_min, value_max, sample_count, unit, state
           FROM aggregate_measurement WHERE aggregation_run_id=?""",
        (run[0],),  # info: call (
    ):  # info: ) :
        metrics[r["metric_key"]] = {  # info: metrics [ r [ "metric_key" ] ] =
            "avg": r["value_avg"],  # info: "avg" : r [ "value_avg" ] ,
            "min": r["value_min"],  # info: "min" : r [ "value_min" ] ,
            "max": r["value_max"],  # info: "max" : r [ "value_max" ] ,
            "samples": r["sample_count"],  # info: "samples" : r [ "sample_count" ] ,
            "unit": r["unit"],  # info: "unit" : r [ "unit" ] ,
            "state": r["state"],  # info: "state" : r [ "state" ] ,
        }  # info: }
    return {  # info: return {
        "period_start": run[1],  # info: "period_start" : run [ 1 ] ,
        "period_end": run[2],  # info: "period_end" : run [ 2 ] ,
        "completed_at": run[3],  # info: "completed_at" : run [ 3 ] ,
        "metrics": metrics,  # info: "metrics" : metrics ,
    }  # info: }

# ====================================================
# SECTION: function write_status_json
# What it does: write status json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_status_json() -> Path:  # info: def write_status_json
    paths.ensure_dirs()  # info: paths . ensure_dirs ( )
    (paths.SYSTEM_DATA / "status").mkdir(parents=True, exist_ok=True)  # info: call (
    raw = connect()  # info: set raw
    try:  # info: try :
        current = _latest_raw(raw)  # info: set current
    finally:  # info: finally :
        raw.close()  # info: raw . close ( )

    five = {}  # info: set five
    try:  # info: try :
        lc = connect_layer("5min")  # info: set lc
        try:  # info: try :
            five = _latest_5min(lc)  # info: set five
        finally:  # info: finally :
            lc.close()  # info: lc . close ( )
    except Exception:  # info: except Exception :
        five = {}  # info: set five

    payload = {  # info: set payload
        "skill": "system-stats",  # info: "skill" : "system-stats" ,
        "generated_at": _iso_now(),  # info: "generated_at" : _iso_now ( ) ,
        "host": current.get("host") or "host",  # info: "host" : current . get ( "host" )
        "current": current,  # info: "current" : current ,
        "five_min": five,  # info: "five_min" : five ,
    }  # info: }
    tmp = STATUS_PATH.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(STATUS_PATH)  # info: tmp . replace ( STATUS_PATH )
    return STATUS_PATH  # info: return STATUS_PATH
