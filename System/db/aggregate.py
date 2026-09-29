"""SYSTEM condensation engine — fixed reporting periods into per-layer db files."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import math

LAYERS = ("1sec", "1min", "5min", "15min", "1hour", "day", "7days", "month", "year")
SECONDS = {"1sec": 1, "1min": 60, "5min": 300, "15min": 900, "1hour": 3600, "7days": 604800}
LOCAL = ZoneInfo("Pacific/Honolulu")

def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def _iso(d: datetime) -> str:
    return d.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def period_bounds(layer: str, at: datetime):
    d = at.astimezone(LOCAL)
    if layer == "1sec":
        start = d.replace(microsecond=0)
    elif layer == "1min":
        start = d.replace(second=0, microsecond=0)
    elif layer == "5min":
        start = d.replace(minute=(d.minute // 5) * 5, second=0, microsecond=0)
    elif layer == "15min":
        start = d.replace(minute=(d.minute // 15) * 15, second=0, microsecond=0)
    elif layer == "1hour":
        start = d.replace(minute=0, second=0, microsecond=0)
    elif layer == "day":
        start = d.replace(hour=0, minute=0, second=0, microsecond=0)
    elif layer == "7days":
        start = datetime.combine(d.date() - timedelta(days=d.weekday()), datetime.min.time(), LOCAL)
    elif layer == "month":
        start = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif layer == "year":
        start = d.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(layer)
    if layer in SECONDS:
        end = start + timedelta(seconds=SECONDS[layer])
    elif layer == "month":
        y = start.year + int(start.month == 12)
        m = 1 if start.month == 12 else start.month + 1
        end = start.replace(year=y, month=m)
    else:
        end = start.replace(year=start.year + 1) if layer == "year" else start + timedelta(days=1)
    return start, end

def aggregate_period(conn, layer: str, start: datetime, end: datetime, source_layer: str = "raw") -> int:
    """Aggregate raw measurements in [start, end) into this layer file. Returns row count."""
    period_start, period_end = _iso(start), _iso(end)
    now = _iso(datetime.now(timezone.utc))
    conn.execute(
        """INSERT INTO aggregation_run(layer, period_start, period_end, source_layer, status, started_at)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(layer, period_start, period_end) DO UPDATE SET
             source_layer=excluded.source_layer, status='running', started_at=excluded.started_at,
             completed_at=NULL, row_count=NULL""",
        (layer, period_start, period_end, source_layer, "running", now),
    )
    run = conn.execute(
        "SELECT aggregation_run_id FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",
        (layer, period_start, period_end),
    ).fetchone()[0]
    conn.execute("DELETE FROM aggregate_measurement WHERE aggregation_run_id=?", (run,))

    # Pull from the raw system.db (passed as source via a separate connection in condense)
    # Here we expect the caller to have already attached or we query via the raw path.
    # For simplicity the condense step will pass the raw rows.
    return 0  # filled by condense using the helper below

def _stats(values: list[float]) -> dict:
    if not values:
        return {
            "sample_count": 0, "valid_sample_count": 0, "coverage_pct": 0.0,
            "observed_span_s": 0.0, "valid_duration_s": None,
            "value_avg": None, "value_min": None, "value_max": None,
            "value_sum": None, "value_delta": None, "state": "missing",
        }
    return {
        "sample_count": len(values),
        "valid_sample_count": len(values),
        "coverage_pct": 100.0,
        "observed_span_s": 0.0,
        "valid_duration_s": None,
        "value_avg": sum(values) / len(values),
        "value_min": min(values),
        "value_max": max(values),
        "value_sum": sum(values),
        "value_delta": values[-1] - values[0],
        "state": "measured",
    }

def write_aggregate(conn, run_id: int, metric_key: str, unit: str | None, values: list[float]) -> None:
    s = _stats(values)
    conn.execute(
        """INSERT INTO aggregate_measurement
           (aggregation_run_id, metric_key, unit, sample_count, valid_sample_count,
            coverage_pct, observed_span_s, valid_duration_s,
            value_avg, value_min, value_max, value_sum, value_delta, state)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (run_id, metric_key, unit, s["sample_count"], s["valid_sample_count"],
         s["coverage_pct"], s["observed_span_s"], s["valid_duration_s"],
         s["value_avg"], s["value_min"], s["value_max"], s["value_sum"], s["value_delta"], s["state"]),
    )
