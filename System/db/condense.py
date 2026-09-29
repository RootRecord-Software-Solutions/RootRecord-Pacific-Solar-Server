"""Runtime condensation of newly closed SYSTEM periods — one db file per layer."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from db.store import connect, connect_layer, initialize_schema
from db.aggregate import period_bounds, write_aggregate, _iso, LAYERS
import paths

def condense_closed_periods(db_path: Path | None = None, layers_dir: Path | None = None) -> int:
    raw_path = Path(db_path) if db_path else paths.SYSTEM_DB
    layers_dir = Path(layers_dir) if layers_dir else paths.LAYERS_DIR
    raw = connect(raw_path)
    initialize_schema(raw)
    total = 0
    try:
        row = raw.execute("SELECT MIN(observed_at), MAX(observed_at) FROM observation").fetchone()
        if not row or not row[0] or not row[1]:
            return 0
        earliest = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
        latest = datetime.fromisoformat(row[1].replace("Z", "+00:00"))

        for layer in LAYERS:
            layer_conn = connect_layer(layer, layers_dir)
            try:
                start, _ = period_bounds(layer, earliest)
                while True:
                    _, end = period_bounds(layer, start)
                    if end > latest:
                        break
                    key = (_iso(start), _iso(end))
                    done = layer_conn.execute(
                        "SELECT status FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",
                        (layer, *key),
                    ).fetchone()
                    if not done or done[0] != "complete":
                        total += _aggregate_one(raw, layer_conn, layer, start, end)
                    start = end
            finally:
                layer_conn.close()
        return total
    finally:
        raw.close()

def _aggregate_one(raw, layer_conn, layer, start, end) -> int:
    period_start, period_end = _iso(start), _iso(end)
    now = _iso(datetime.now(timezone.utc))
    layer_conn.execute(
        """INSERT INTO aggregation_run(layer, period_start, period_end, source_layer, status, started_at)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(layer, period_start, period_end) DO UPDATE SET
             status='running', started_at=excluded.started_at, completed_at=NULL, row_count=NULL""",
        (layer, period_start, period_end, "raw", "running", now),
    )
    run = layer_conn.execute(
        "SELECT aggregation_run_id FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",
        (layer, period_start, period_end),
    ).fetchone()[0]
    layer_conn.execute("DELETE FROM aggregate_measurement WHERE aggregation_run_id=?", (run,))

    # group measured values by metric
    rows = raw.execute(
        """SELECT m.metric_key, m.value_num, m.unit, o.observed_at
           FROM measurement m JOIN observation o ON o.observation_id = m.observation_id
           WHERE o.observed_at >= ? AND o.observed_at < ?
             AND m.state = 'measured' AND m.value_num IS NOT NULL
           ORDER BY m.metric_key, o.observed_at""",
        (period_start, period_end),
    ).fetchall()

    from collections import defaultdict
    buckets: dict[str, list] = defaultdict(list)
    units: dict[str, str | None] = {}
    for r in rows:
        buckets[r["metric_key"]].append(float(r["value_num"]))
        units[r["metric_key"]] = r["unit"]

    count = 0
    for metric, values in buckets.items():
        write_aggregate(layer_conn, run, metric, units.get(metric), values)
        count += 1

    watermark = raw.execute(
        "SELECT MAX(observed_at) FROM observation WHERE observed_at >= ? AND observed_at < ?",
        (period_start, period_end),
    ).fetchone()[0]
    layer_conn.execute(
        "UPDATE aggregation_run SET status='complete', completed_at=?, source_watermark=?, row_count=? WHERE aggregation_run_id=?",
        (now, watermark, count, run),
    )
    layer_conn.commit()
    return count
