# ==============================================================================
# FILE: Energy/db/condense.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Runtime condensation of newly closed telemetry periods — one db file per layer."""  # info: """Runtime condensation of newly closed telemetry periods — one db file per layer."""
from __future__ import annotations  # info: from __future__ import annotations
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from Energy.db.store import connect, connect_layer, initialize_schema, DEFAULT_DB_PATH, LAYERS_DIR  # info: from Energy . db . store import connect
from Energy.db.aggregate import aggregate_period, consolidate_period, period_bounds, LAYERS, BUCKET_SOURCE, _iso  # info: from Energy . db . aggregate import aggregate_period
from Energy.db.report_json import write_period_report  # info: from Energy . db . report_json import write_period_report


# ====================================================
# SECTION: function ensure_layers
# What it does: Create every EcoFlow layer database if it is missing. Raw samples land in layers/1sec.db on first persist (same file as the 1sec layer).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_layers(db_path=None, layers_dir=None):  # info: def ensure_layers
    from Energy.db.store import initialize_layer_schema, layer_db_path  # info: local import keeps layer-only create off the raw path
    import sqlite3  # info: import sqlite3
    layers_dir = Path(layers_dir) if layers_dir else LAYERS_DIR  # info: set layers_dir
    for layer in LAYERS:  # info: for layer in LAYERS :
        path = layer_db_path(layer, layers_dir)  # info: set path
        path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
        conn = sqlite3.connect(str(path))  # info: open the layer file only — no ATTACH of the raw db
        try:  # info: try
            initialize_layer_schema(conn)  # info: call initialize_layer_schema
        finally:  # info: finally
            conn.close()  # info: conn . close


MINUTE_LAYERS = ("1sec", "1min", "5min", "15min")  # info: set MINUTE_LAYERS
HOUR_LAYERS = ("1hour", "day", "7days", "month", "year")  # info: set HOUR_LAYERS


# ====================================================
# SECTION: function consolidate_minutes
# What it does: Roll closed second samples into the minute, 5-minute, and 15-minute buckets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def consolidate_minutes(db_path=None, layers_dir=None):  # info: def consolidate_minutes
    return condense_closed_periods(db_path, layers_dir, layers=MINUTE_LAYERS)  # info: return condense_closed_periods


# ====================================================
# SECTION: function condense_hours
# What it does: Roll closed minute buckets into the hour, day, week, month, and year buckets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def condense_hours(db_path=None, layers_dir=None):  # info: def condense_hours
    total = condense_closed_periods(db_path, layers_dir, layers=HOUR_LAYERS)  # info: set total
    write_period_report(db_path, layers_dir)  # info: refresh periods.json for the AI reports
    return total  # info: return total


# ====================================================
# SECTION: function condense_closed_periods
# What it does: Create missing layer files, then condense the requested closed buckets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def condense_closed_periods(db_path=None, layers_dir=None, layers=None):  # info: def condense_closed_periods
    raw_path = Path(db_path) if db_path else DEFAULT_DB_PATH  # info: set raw_path
    layers_dir = Path(layers_dir) if layers_dir else LAYERS_DIR  # info: set layers_dir
    ensure_layers(raw_path, layers_dir)  # info: call ensure_layers
    raw_conn = connect(raw_path)  # info: set raw_conn
    initialize_schema(raw_conn)  # info: call initialize_schema
    total = 0  # info: set total
    try:  # info: try :
        row = raw_conn.execute("SELECT MIN(observed_at), MAX(observed_at) FROM observation").fetchone()  # info: set row
        if not row or not row[0] or not row[1]:  # info: if not row or not row [ 0
            return 0  # info: return 0
        earliest = datetime.fromisoformat(row[0].replace("Z", "+00:00"))  # info: set earliest
        latest = datetime.fromisoformat(row[1].replace("Z", "+00:00"))  # info: set latest

        chosen = tuple(layers) if layers else LAYERS  # info: set chosen
        for layer in chosen:  # info: for layer in chosen :
            source = BUCKET_SOURCE.get(layer)  # info: set source
            layer_conn = connect_layer(layer, raw_path, layers_dir)  # info: set layer_conn
            child_conn = connect_layer(source, raw_path, layers_dir) if source else None  # info: set child_conn
            try:  # info: try :
                start, _ = period_bounds(layer, earliest)  # info: start , _ = period_bounds ( layer ,
                while True:  # info: while True :
                    _, end = period_bounds(layer, start)  # info: _ , end = period_bounds ( layer ,
                    if end > latest:  # info: if end > latest :
                        break  # info: break
                    key = (_iso(start), _iso(end))  # info: set key
                    done = layer_conn.execute(  # info: set done
                        "SELECT status FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",  # info: "SELECT status FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?" ,
                        (layer, *key)).fetchone()  # info: call (
                    if not done or done[0] != "complete":  # info: if not done or done [ 0 ]
                        if source:  # info: if source
                            total += consolidate_period(layer_conn, child_conn, layer, start, end, source)  # info: roll the finer bucket
                        else:  # info: else
                            total += aggregate_period(layer_conn, layer, start, end, "raw")  # info: set total
                    start = end  # info: set start
            finally:  # info: finally :
                layer_conn.close()  # info: layer_conn . close ( )
                if child_conn is not None:  # info: if child_conn is not None
                    child_conn.close()  # info: child_conn . close ( )
        return total  # info: return total
    finally:  # info: finally :
        raw_conn.close()  # info: raw_conn . close ( )
