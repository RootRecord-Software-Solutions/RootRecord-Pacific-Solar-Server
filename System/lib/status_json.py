"""Write one clean transmission JSON: current values + latest closed 5min averages."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import paths
from db.store import connect, connect_layer

LOCAL = ZoneInfo("Pacific/Honolulu")
STATUS_PATH = paths.SYSTEM_DATA / "status" / "system-status.json"

def _iso_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def _latest_raw(conn) -> dict:
    row = conn.execute(
        "SELECT observation_id, observed_at, host FROM observation ORDER BY observed_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return {}
    obs_id, at, host = row[0], row[1], row[2]
    metrics = {}
    for r in conn.execute(
        "SELECT metric_key, value_num, unit, state FROM measurement WHERE observation_id=?",
        (obs_id,),
    ):
        metrics[r["metric_key"]] = {
            "value": r["value_num"],
            "unit": r["unit"],
            "state": r["state"],
        }
    return {"observed_at": at, "host": host, "metrics": metrics}

def _latest_5min(layer_conn) -> dict:
    run = layer_conn.execute(
        """SELECT aggregation_run_id, period_start, period_end, completed_at
           FROM aggregation_run
           WHERE layer='5min' AND status='complete'
           ORDER BY period_end DESC LIMIT 1"""
    ).fetchone()
    if not run:
        return {}
    metrics = {}
    for r in layer_conn.execute(
        """SELECT metric_key, value_avg, value_min, value_max, sample_count, unit, state
           FROM aggregate_measurement WHERE aggregation_run_id=?""",
        (run[0],),
    ):
        metrics[r["metric_key"]] = {
            "avg": r["value_avg"],
            "min": r["value_min"],
            "max": r["value_max"],
            "samples": r["sample_count"],
            "unit": r["unit"],
            "state": r["state"],
        }
    return {
        "period_start": run[1],
        "period_end": run[2],
        "completed_at": run[3],
        "metrics": metrics,
    }

def write_status_json() -> Path:
    paths.ensure_dirs()
    (paths.SYSTEM_DATA / "status").mkdir(parents=True, exist_ok=True)
    raw = connect()
    try:
        current = _latest_raw(raw)
    finally:
        raw.close()

    five = {}
    try:
        lc = connect_layer("5min")
        try:
            five = _latest_5min(lc)
        finally:
            lc.close()
    except Exception:
        five = {}

    payload = {
        "skill": "system-stats",
        "generated_at": _iso_now(),
        "host": current.get("host") or "host",
        "current": current,
        "five_min": five,
    }
    tmp = STATUS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATUS_PATH)
    return STATUS_PATH
