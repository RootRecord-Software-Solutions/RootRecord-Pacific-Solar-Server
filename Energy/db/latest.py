"""Read latest measured values from the RootRecord SQLite data layer.

Never invents numbers. Missing stays missing (returns None).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .store import DEFAULT_DB_PATH, connect


def _db_exists(db_path: Path | str = DEFAULT_DB_PATH) -> bool:
    p = Path(db_path)
    return p.is_file() and p.stat().st_size > 0


def latest_for_alias(alias: str, db_path: Path | str = DEFAULT_DB_PATH) -> Optional[dict[str, Any]]:
    """Return latest observation summary for a device alias, or None if unavailable."""
    if not _db_exists(db_path):
        return None
    conn = connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT d.device_id, d.serial_number, d.model, d.alias, o.observation_id, o.observed_at
            FROM device d
            JOIN observation o ON o.device_id = d.device_id
            WHERE d.alias = ?
            ORDER BY o.observed_at DESC
            LIMIT 1
            """,
            (alias,),
        ).fetchone()
        if not row:
            # fallback: match by serial prefix / model name heuristics
            row = conn.execute(
                """
                SELECT d.device_id, d.serial_number, d.model, d.alias, o.observation_id, o.observed_at
                FROM device d
                JOIN observation o ON o.device_id = d.device_id
                WHERE lower(COALESCE(d.alias,'')) = lower(?)
                   OR lower(COALESCE(d.model,'')) LIKE lower(?)
                ORDER BY o.observed_at DESC
                LIMIT 1
                """,
                (alias, f"%{alias}%"),
            ).fetchone()
        if not row:
            return None

        device_id, sn, model, dev_alias, obs_id, observed_at = row

        def measured(table: str, metric: str, extra_where: str = "", extra_args: tuple = ()) -> Any:
            q = f"""
                SELECT value_num, value_text, value_bool, state
                FROM {table}
                WHERE observation_id=? AND metric_key=? {extra_where}
                LIMIT 1
            """
            r = conn.execute(q, (obs_id, metric, *extra_args)).fetchone()
            if not r:
                return None
            state = r[3]
            if state in ("missing", "not_applicable"):
                return None
            if r[0] is not None:
                return r[0]
            if r[1] is not None:
                return r[1]
            if r[2] is not None:
                return bool(r[2])
            return None

        def electrical(channel: str, metric: str = "power_w") -> Any:
            r = conn.execute(
                """
                SELECT value_num, state FROM electrical_measurement
                WHERE observation_id=? AND channel=? AND metric_key=?
                LIMIT 1
                """,
                (obs_id, channel, metric),
            ).fetchone()
            if not r or r[1] in ("missing", "not_applicable"):
                return None
            return r[0]

        # Primary battery SOC
        soc = None
        bat = conn.execute(
            """
            SELECT bm.value_num, bm.state
            FROM battery b
            JOIN battery_measurement bm ON bm.battery_id = b.battery_id
            WHERE b.device_id=? AND b.battery_role='primary'
              AND bm.observation_id=? AND bm.metric_key='soc_percent'
            LIMIT 1
            """,
            (device_id, obs_id),
        ).fetchone()
        if bat and bat[1] not in ("missing", "not_applicable"):
            soc = bat[0]
        if soc is None:
            soc = measured("device_measurement", "battery_level")

        # Expansion batteries (B3 etc.)
        expansions = []
        for er in conn.execute(
            """
            SELECT b.battery_slot, b.serial_number, bm.value_num, bm.state
            FROM battery b
            LEFT JOIN battery_measurement bm
              ON bm.battery_id = b.battery_id
             AND bm.observation_id = ?
             AND bm.metric_key = 'soc_percent'
            WHERE b.device_id=? AND b.battery_role='expansion'
            ORDER BY b.battery_slot
            """,
            (obs_id, device_id),
        ):
            slot, esn, esoc, estate = er
            expansions.append({
                "slot": slot,
                "sn": esn,
                "soc": esoc if estate not in ("missing", "not_applicable", None) else None,
            })

        return {
            "alias": dev_alias or alias,
            "sn": sn,
            "model": model,
            "observed_at": observed_at,
            "soc": soc,
            "ac_output_power": electrical("ac_output") or measured("device_measurement", "ac_output_power"),
            "ac_input_power": electrical("ac_input"),
            "solar_input_power": electrical("solar_input") or electrical("xt60_input"),
            "usbc_output_power": electrical("usb_c_1"),
            "input_power": electrical("input_total") or measured("device_measurement", "input_power"),
            "output_power": electrical("output_total") or measured("device_measurement", "output_power"),
            "expansions": expansions,
            "source": "sqlite",
        }
    finally:
        conn.close()


def board_snapshot(db_path: Path | str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Compact board view for poller /energy display."""
    delta = latest_for_alias("delta2", db_path)
    river = latest_for_alias("river2pro", db_path)
    return {"delta2": delta, "river2pro": river, "db": str(db_path)}
