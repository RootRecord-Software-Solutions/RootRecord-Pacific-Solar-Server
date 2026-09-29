"""Runtime condensation of newly closed telemetry periods — one db file per layer."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from Energy.db.store import connect, connect_layer, initialize_schema, DEFAULT_DB_PATH, LAYERS_DIR
from Energy.db.aggregate import aggregate_period, period_bounds, LAYERS, _iso


def condense_closed_periods(db_path=None, layers_dir=None):
    raw_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    layers_dir = Path(layers_dir) if layers_dir else LAYERS_DIR
    raw_conn = connect(raw_path)
    initialize_schema(raw_conn)
    total = 0
    try:
        row = raw_conn.execute("SELECT MIN(observed_at), MAX(observed_at) FROM observation").fetchone()
        if not row or not row[0] or not row[1]:
            return 0
        earliest = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
        latest = datetime.fromisoformat(row[1].replace("Z", "+00:00"))

        for layer in LAYERS:
            layer_conn = connect_layer(layer, raw_path, layers_dir)
            try:
                start, _ = period_bounds(layer, earliest)
                while True:
                    _, end = period_bounds(layer, start)
                    if end > latest:
                        break
                    key = (_iso(start), _iso(end))
                    done = layer_conn.execute(
                        "SELECT status FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",
                        (layer, *key)).fetchone()
                    if not done or done[0] != "complete":
                        total += aggregate_period(layer_conn, layer, start, end, "raw")
                    start = end
            finally:
                layer_conn.close()
        return total
    finally:
        raw_conn.close()
