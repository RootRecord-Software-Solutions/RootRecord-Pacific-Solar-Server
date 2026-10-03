# ==============================================================================
# FILE: System/db/condense.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Runtime condensation of newly closed SYSTEM periods — one db file per layer."""  # info: """Runtime condensation of newly closed SYSTEM periods — one db file per layer."""
from __future__ import annotations  # info: from __future__ import annotations
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from db.store import connect, connect_layer, initialize_schema  # info: from db . store import connect , connect_layer
from db.aggregate import period_bounds, write_aggregate, _iso, LAYERS  # info: from db . aggregate import period_bounds , write_aggregate
import paths  # info: import paths

MINUTE_LAYERS = ("1sec", "1min", "5min", "15min")  # info: set MINUTE_LAYERS
HOUR_LAYERS = ("1hour", "day", "7days", "month", "year")  # info: set HOUR_LAYERS


# ====================================================
# SECTION: function ensure_layers
# What it does: Create every System layer database if it is missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_layers(db_path: Path | None = None, layers_dir: Path | None = None) -> None:  # info: def ensure_layers
    raw_path = Path(db_path) if db_path else paths.SYSTEM_DB  # info: set raw_path
    layers_dir = Path(layers_dir) if layers_dir else paths.LAYERS_DIR  # info: set layers_dir
    raw = connect(raw_path)  # info: set raw
    initialize_schema(raw)  # info: call initialize_schema
    raw.close()  # info: raw . close ( )
    for layer in LAYERS:  # info: for layer in LAYERS
        layer_conn = connect_layer(layer, layers_dir)  # info: set layer_conn
        layer_conn.close()  # info: layer_conn . close ( )


# ====================================================
# SECTION: function consolidate_minutes
# What it does: Roll closed second samples into the minute, 5-minute, and 15-minute buckets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def consolidate_minutes(db_path: Path | None = None, layers_dir: Path | None = None) -> int:  # info: def consolidate_minutes
    return condense_closed_periods(db_path, layers_dir, layers=MINUTE_LAYERS)  # info: return condense_closed_periods


# ====================================================
# SECTION: function condense_hours
# What it does: Roll closed minute buckets into the hour, day, week, month, and year buckets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def condense_hours(db_path: Path | None = None, layers_dir: Path | None = None) -> int:  # info: def condense_hours
    return condense_closed_periods(db_path, layers_dir, layers=HOUR_LAYERS)  # info: return condense_closed_periods


# ====================================================
# SECTION: function condense_closed_periods
# What it does: Create missing layer files, then condense the requested closed buckets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def condense_closed_periods(db_path: Path | None = None, layers_dir: Path | None = None, layers=None) -> int:  # info: def condense_closed_periods
    raw_path = Path(db_path) if db_path else paths.SYSTEM_DB  # info: set raw_path
    layers_dir = Path(layers_dir) if layers_dir else paths.LAYERS_DIR  # info: set layers_dir
    ensure_layers(raw_path, layers_dir)  # info: call ensure_layers
    raw = connect(raw_path)  # info: set raw
    initialize_schema(raw)  # info: call initialize_schema
    total = 0  # info: set total
    try:  # info: try :
        row = raw.execute("SELECT MIN(observed_at), MAX(observed_at) FROM observation").fetchone()  # info: set row
        if not row or not row[0] or not row[1]:  # info: if not row or not row [ 0
            return 0  # info: return 0
        earliest = datetime.fromisoformat(row[0].replace("Z", "+00:00"))  # info: set earliest
        latest = datetime.fromisoformat(row[1].replace("Z", "+00:00"))  # info: set latest

        chosen = tuple(layers) if layers else LAYERS  # info: set chosen
        for layer in chosen:  # info: for layer in chosen :
            layer_conn = connect_layer(layer, layers_dir)  # info: set layer_conn
            try:  # info: try :
                start, _ = period_bounds(layer, earliest)  # info: start , _ = period_bounds ( layer ,
                while True:  # info: while True :
                    _, end = period_bounds(layer, start)  # info: _ , end = period_bounds ( layer ,
                    if end > latest:  # info: if end > latest :
                        break  # info: break
                    key = (_iso(start), _iso(end))  # info: set key
                    done = layer_conn.execute(  # info: set done
                        "SELECT status FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",  # info: "SELECT status FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?" ,
                        (layer, *key),  # info: call (
                    ).fetchone()  # info: ) . fetchone ( )
                    if not done or done[0] != "complete":  # info: if not done or done [ 0 ]
                        total += _aggregate_one(raw, layer_conn, layer, start, end)  # info: set total
                    start = end  # info: set start
            finally:  # info: finally :
                layer_conn.close()  # info: layer_conn . close ( )
        return total  # info: return total
    finally:  # info: finally :
        raw.close()  # info: raw . close ( )


# ====================================================
# SECTION: function _aggregate_one
# What it does: Aggregate one closed period from raw measurements into one layer file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _aggregate_one(raw, layer_conn, layer, start, end) -> int:  # info: def _aggregate_one
    period_start, period_end = _iso(start), _iso(end)  # info: period_start , period_end = _iso ( start )
    now = _iso(datetime.now(timezone.utc))  # info: set now
    layer_conn.execute(  # info: layer_conn . execute (
        """INSERT INTO aggregation_run(layer, period_start, period_end, source_layer, status, started_at)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(layer, period_start, period_end) DO UPDATE SET
             status='running', started_at=excluded.started_at, completed_at=NULL, row_count=NULL""",
        (layer, period_start, period_end, "raw", "running", now),  # info: call (
    )  # info: )
    run = layer_conn.execute(  # info: set run
        "SELECT aggregation_run_id FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",  # info: "SELECT aggregation_run_id FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?" ,
        (layer, period_start, period_end),  # info: call (
    ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
    layer_conn.execute("DELETE FROM aggregate_measurement WHERE aggregation_run_id=?", (run,))  # info: layer_conn . execute ( "DELETE FROM aggregate_measurement WHERE aggregation_run_id=?" , ( run

    rows = raw.execute(  # info: set rows
        """SELECT m.metric_key, m.value_num, m.unit, o.observed_at
           FROM measurement m JOIN observation o ON o.observation_id = m.observation_id
           WHERE o.observed_at >= ? AND o.observed_at < ?
             AND m.state = 'measured' AND m.value_num IS NOT NULL
           ORDER BY m.metric_key, o.observed_at""",
        (period_start, period_end),  # info: call (
    ).fetchall()  # info: ) . fetchall ( )

    from collections import defaultdict  # info: from collections import defaultdict
    buckets: dict[str, list] = defaultdict(list)  # info: set buckets
    units: dict[str, str | None] = {}  # info: set units
    for r in rows:  # info: for r in rows :
        buckets[r["metric_key"]].append(float(r["value_num"]))  # info: buckets [ r [ "metric_key" ] ] .
        units[r["metric_key"]] = r["unit"]  # info: units [ r [ "metric_key" ] ] =

    count = 0  # info: set count
    for metric, values in buckets.items():  # info: for metric , values in buckets . items
        write_aggregate(layer_conn, run, metric, units.get(metric), values)  # info: call write_aggregate
        count += 1  # info: set count

    watermark = raw.execute(  # info: set watermark
        "SELECT MAX(observed_at) FROM observation WHERE observed_at >= ? AND observed_at < ?",  # info: "SELECT MAX(observed_at) FROM observation WHERE observed_at >= ? AND observed_at < ?" ,
        (period_start, period_end),  # info: call (
    ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
    layer_conn.execute(  # info: layer_conn . execute (
        "UPDATE aggregation_run SET status='complete', completed_at=?, source_watermark=?, row_count=? WHERE aggregation_run_id=?",  # info: "UPDATE aggregation_run SET status='complete', completed_at=?, source_watermark=?, row_count=? WHERE aggregati
        (now, watermark, count, run),  # info: call (
    )  # info: )
    layer_conn.commit()  # info: layer_conn . commit ( )
    return count  # info: return count
