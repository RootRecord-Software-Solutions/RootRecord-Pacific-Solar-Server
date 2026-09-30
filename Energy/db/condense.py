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
from Energy.db.aggregate import aggregate_period, period_bounds, LAYERS, _iso  # info: from Energy . db . aggregate import aggregate_period


# ====================================================
# SECTION: function condense_closed_periods
# What it does: condense closed periods.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def condense_closed_periods(db_path=None, layers_dir=None):  # info: def condense_closed_periods
    raw_path = Path(db_path) if db_path else DEFAULT_DB_PATH  # info: set raw_path
    layers_dir = Path(layers_dir) if layers_dir else LAYERS_DIR  # info: set layers_dir
    raw_conn = connect(raw_path)  # info: set raw_conn
    initialize_schema(raw_conn)  # info: call initialize_schema
    total = 0  # info: set total
    try:  # info: try :
        row = raw_conn.execute("SELECT MIN(observed_at), MAX(observed_at) FROM observation").fetchone()  # info: set row
        if not row or not row[0] or not row[1]:  # info: if not row or not row [ 0
            return 0  # info: return 0
        earliest = datetime.fromisoformat(row[0].replace("Z", "+00:00"))  # info: set earliest
        latest = datetime.fromisoformat(row[1].replace("Z", "+00:00"))  # info: set latest

        for layer in LAYERS:  # info: for layer in LAYERS :
            layer_conn = connect_layer(layer, raw_path, layers_dir)  # info: set layer_conn
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
                        total += aggregate_period(layer_conn, layer, start, end, "raw")  # info: set total
                    start = end  # info: set start
            finally:  # info: finally :
                layer_conn.close()  # info: layer_conn . close ( )
        return total  # info: return total
    finally:  # info: finally :
        raw_conn.close()  # info: raw_conn . close ( )
