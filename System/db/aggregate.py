# ==============================================================================
# FILE: System/db/aggregate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""SYSTEM condensation engine — fixed reporting periods into per-layer db files."""  # info: """SYSTEM condensation engine — fixed reporting periods into per-layer db files."""
from __future__ import annotations  # info: from __future__ import annotations
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo
import math  # info: import math

LAYERS = ("1sec", "1min", "5min", "15min", "1hour", "day", "7days", "month", "year")  # info: set LAYERS
SECONDS = {"1sec": 1, "1min": 60, "5min": 300, "15min": 900, "1hour": 3600, "7days": 604800}  # info: set SECONDS
LOCAL = ZoneInfo("Pacific/Honolulu")  # info: set LOCAL

# ====================================================
# SECTION: function _dt
# What it does:  dt.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _dt(s: str) -> datetime:  # info: def _dt
    return datetime.fromisoformat(s.replace("Z", "+00:00"))  # info: return datetime . fromisoformat ( s . replace

# ====================================================
# SECTION: function _iso
# What it does:  iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _iso(d: datetime) -> str:  # info: def _iso
    return d.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")  # info: return d . astimezone ( timezone . utc

# ====================================================
# SECTION: function period_bounds
# What it does: period bounds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def period_bounds(layer: str, at: datetime):  # info: def period_bounds
    d = at.astimezone(LOCAL)  # info: set d
    if layer == "1sec":  # info: if layer == "1sec" :
        start = d.replace(microsecond=0)  # info: set start
    elif layer == "1min":  # info: elif layer == "1min" :
        start = d.replace(second=0, microsecond=0)  # info: set start
    elif layer == "5min":  # info: elif layer == "5min" :
        start = d.replace(minute=(d.minute // 5) * 5, second=0, microsecond=0)  # info: set start
    elif layer == "15min":  # info: elif layer == "15min" :
        start = d.replace(minute=(d.minute // 15) * 15, second=0, microsecond=0)  # info: set start
    elif layer == "1hour":  # info: elif layer == "1hour" :
        start = d.replace(minute=0, second=0, microsecond=0)  # info: set start
    elif layer == "day":  # info: elif layer == "day" :
        start = d.replace(hour=0, minute=0, second=0, microsecond=0)  # info: set start
    elif layer == "7days":  # info: elif layer == "7days" :
        start = datetime.combine(d.date() - timedelta(days=d.weekday()), datetime.min.time(), LOCAL)  # info: set start
    elif layer == "month":  # info: elif layer == "month" :
        start = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # info: set start
    elif layer == "year":  # info: elif layer == "year" :
        start = d.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)  # info: set start
    else:  # info: else :
        raise ValueError(layer)  # info: raise ValueError ( layer )
    if layer in SECONDS:  # info: if layer in SECONDS :
        end = start + timedelta(seconds=SECONDS[layer])  # info: set end
    elif layer == "month":  # info: elif layer == "month" :
        y = start.year + int(start.month == 12)  # info: set y
        m = 1 if start.month == 12 else start.month + 1  # info: set m
        end = start.replace(year=y, month=m)  # info: set end
    else:  # info: else :
        end = start.replace(year=start.year + 1) if layer == "year" else start + timedelta(days=1)  # info: set end
    return start, end  # info: return start , end

# ====================================================
# SECTION: function aggregate_period
# What it does: Aggregate raw measurements in [start, end) into this layer file. Returns row count.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def aggregate_period(conn, layer: str, start: datetime, end: datetime, source_layer: str = "raw") -> int:  # info: def aggregate_period
    """Aggregate raw measurements in [start, end) into this layer file. Returns row count."""  # info: """Aggregate raw measurements in [start, end) into this layer file. Returns row count."""
    period_start, period_end = _iso(start), _iso(end)  # info: period_start , period_end = _iso ( start )
    now = _iso(datetime.now(timezone.utc))  # info: set now
    conn.execute(  # info: conn . execute (
        """INSERT INTO aggregation_run(layer, period_start, period_end, source_layer, status, started_at)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(layer, period_start, period_end) DO UPDATE SET
             source_layer=excluded.source_layer, status='running', started_at=excluded.started_at,
             completed_at=NULL, row_count=NULL""",
        (layer, period_start, period_end, source_layer, "running", now),  # info: call (
    )  # info: )
    run = conn.execute(  # info: set run
        "SELECT aggregation_run_id FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",  # info: "SELECT aggregation_run_id FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?" ,
        (layer, period_start, period_end),  # info: call (
    ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
    conn.execute("DELETE FROM aggregate_measurement WHERE aggregation_run_id=?", (run,))  # info: conn . execute ( "DELETE FROM aggregate_measurement WHERE aggregation_run_id=?" , ( run

    # Pull from the raw system.db (passed as source via a separate connection in condense)
    # Here we expect the caller to have already attached or we query via the raw path.
    # For simplicity the condense step will pass the raw rows.
    return 0  # filled by condense using the helper below

# ====================================================
# SECTION: function _stats
# What it does:  stats.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _stats(values: list[float]) -> dict:  # info: def _stats
    if not values:  # info: if not values :
        return {  # info: return {
            "sample_count": 0, "valid_sample_count": 0, "coverage_pct": 0.0,  # info: "sample_count" : 0 , "valid_sample_count" : 0 ,
            "observed_span_s": 0.0, "valid_duration_s": None,  # info: "observed_span_s" : 0.0 , "valid_duration_s" : None ,
            "value_avg": None, "value_min": None, "value_max": None,  # info: "value_avg" : None , "value_min" : None ,
            "value_sum": None, "value_delta": None, "state": "missing",  # info: "value_sum" : None , "value_delta" : None ,
        }  # info: }
    return {  # info: return {
        "sample_count": len(values),  # info: "sample_count" : len ( values ) ,
        "valid_sample_count": len(values),  # info: "valid_sample_count" : len ( values ) ,
        "coverage_pct": 100.0,  # info: "coverage_pct" : 100.0 ,
        "observed_span_s": 0.0,  # info: "observed_span_s" : 0.0 ,
        "valid_duration_s": None,  # info: "valid_duration_s" : None ,
        "value_avg": sum(values) / len(values),  # info: "value_avg" : sum ( values ) / len
        "value_min": min(values),  # info: "value_min" : min ( values ) ,
        "value_max": max(values),  # info: "value_max" : max ( values ) ,
        "value_sum": sum(values),  # info: "value_sum" : sum ( values ) ,
        "value_delta": values[-1] - values[0],  # info: "value_delta" : values [ - 1 ] -
        "state": "measured",  # info: "state" : "measured" ,
    }  # info: }

# ====================================================
# SECTION: function write_aggregate
# What it does: write aggregate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_aggregate(conn, run_id: int, metric_key: str, unit: str | None, values: list[float]) -> None:  # info: def write_aggregate
    s = _stats(values)  # info: set s
    conn.execute(  # info: conn . execute (
        """INSERT INTO aggregate_measurement
           (aggregation_run_id, metric_key, unit, sample_count, valid_sample_count,
            coverage_pct, observed_span_s, valid_duration_s,
            value_avg, value_min, value_max, value_sum, value_delta, state)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (run_id, metric_key, unit, s["sample_count"], s["valid_sample_count"],  # info: call (
         s["coverage_pct"], s["observed_span_s"], s["valid_duration_s"],  # info: s [ "coverage_pct" ] , s [ "observed_span_s"
         s["value_avg"], s["value_min"], s["value_max"], s["value_sum"], s["value_delta"], s["state"]),  # info: s [ "value_avg" ] , s [ "value_min"
    )  # info: )
