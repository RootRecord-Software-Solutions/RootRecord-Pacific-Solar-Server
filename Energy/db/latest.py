# ==============================================================================
# FILE: Energy/db/latest.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Read latest measured values from the RootRecord SQLite data layer.

Never invents numbers. Missing stays missing (returns None).
"""
from __future__ import annotations  # info: from __future__ import annotations

from pathlib import Path  # info: from pathlib import Path
from typing import Any, Optional  # info: from typing import Any , Optional

from .store import DEFAULT_DB_PATH, connect  # info: from . store import DEFAULT_DB_PATH , connect


# ====================================================
# SECTION: function _db_exists
# What it does:  db exists.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _db_exists(db_path: Path | str = DEFAULT_DB_PATH) -> bool:  # info: def _db_exists
    p = Path(db_path)  # info: set p
    return p.is_file() and p.stat().st_size > 0  # info: return p . is_file ( ) and p


# ====================================================
# SECTION: function latest_for_alias
# What it does: Return latest observation summary for a device alias, or None if unavailable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def latest_for_alias(alias: str, db_path: Path | str = DEFAULT_DB_PATH) -> Optional[dict[str, Any]]:  # info: def latest_for_alias
    """Return latest observation summary for a device alias, or None if unavailable."""  # info: """Return latest observation summary for a device alias, or None if unavailable."""
    if not _db_exists(db_path):  # info: if not _db_exists ( db_path ) :
        return None  # info: return None
    conn = connect(db_path)  # info: set conn
    try:  # info: try :
        row = conn.execute(  # info: set row
            """
            SELECT d.device_id, d.serial_number, d.model, d.alias, o.observation_id, o.observed_at
            FROM device d
            JOIN observation o ON o.device_id = d.device_id
            WHERE d.alias = ?
            ORDER BY o.observed_at DESC
            LIMIT 1
            """,
            (alias,),  # info: call (
        ).fetchone()  # info: ) . fetchone ( )
        if not row:  # info: if not row :
            # fallback: match by serial prefix / model name heuristics
            row = conn.execute(  # info: set row
                """
                SELECT d.device_id, d.serial_number, d.model, d.alias, o.observation_id, o.observed_at
                FROM device d
                JOIN observation o ON o.device_id = d.device_id
                WHERE lower(COALESCE(d.alias,'')) = lower(?)
                   OR lower(COALESCE(d.model,'')) LIKE lower(?)
                ORDER BY o.observed_at DESC
                LIMIT 1
                """,
                (alias, f"%{alias}%"),  # info: call (
            ).fetchone()  # info: ) . fetchone ( )
        if not row:  # info: if not row :
            return None  # info: return None

        device_id, sn, model, dev_alias, obs_id, observed_at = row  # info: device_id , sn , model , dev_alias ,

        def measured(table: str, metric: str, extra_where: str = "", extra_args: tuple = ()) -> Any:  # info: def measured
            q = f"""  # info: set q
                SELECT value_num, value_text, value_bool, state
                FROM {table}  # info: { table } WHERE observation_id=? AND metric_key=?
                WHERE observation_id=? AND metric_key=? {extra_where}  # info: { extra_where } LIMIT 1
                LIMIT 1
            """  # info: """
            r = conn.execute(q, (obs_id, metric, *extra_args)).fetchone()  # info: set r
            if not r:  # info: if not r :
                return None  # info: return None
            state = r[3]  # info: set state
            if state in ("missing", "not_applicable"):  # info: if state in ( "missing" , "not_applicable" )
                return None  # info: return None
            if r[0] is not None:  # info: if r [ 0 ] is not None
                return r[0]  # info: return r [ 0 ]
            if r[1] is not None:  # info: if r [ 1 ] is not None
                return r[1]  # info: return r [ 1 ]
            if r[2] is not None:  # info: if r [ 2 ] is not None
                return bool(r[2])  # info: return bool ( r [ 2 ] )
            return None  # info: return None

        def electrical(channel: str, metric: str = "power_w") -> Any:  # info: def electrical
            r = conn.execute(  # info: set r
                """
                SELECT value_num, state FROM electrical_measurement
                WHERE observation_id=? AND channel=? AND metric_key=?
                LIMIT 1
                """,
                (obs_id, channel, metric),  # info: call (
            ).fetchone()  # info: ) . fetchone ( )
            if not r or r[1] in ("missing", "not_applicable"):  # info: if not r or r [ 1 ]
                return None  # info: return None
            return r[0]  # info: return r [ 0 ]

        # Primary battery SOC
        soc = None  # info: set soc
        bat = conn.execute(  # info: set bat
            """
            SELECT bm.value_num, bm.state
            FROM battery b
            JOIN battery_measurement bm ON bm.battery_id = b.battery_id
            WHERE b.device_id=? AND b.battery_role='primary'
              AND bm.observation_id=? AND bm.metric_key='soc_percent'
            LIMIT 1
            """,
            (device_id, obs_id),  # info: call (
        ).fetchone()  # info: ) . fetchone ( )
        if bat and bat[1] not in ("missing", "not_applicable"):  # info: if bat and bat [ 1 ] not
            soc = bat[0]  # info: set soc
        if soc is None:  # info: if soc is None :
            soc = measured("device_measurement", "battery_level")  # info: set soc

        # Expansion batteries (B3 etc.)
        expansions = []  # info: set expansions
        for er in conn.execute(  # info: for er in conn . execute (
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
            (obs_id, device_id),  # info: call (
        ):  # info: ) :
            slot, esn, esoc, estate = er  # info: slot , esn , esoc , estate =
            expansions.append({  # info: expansions . append ( {
                "slot": slot,  # info: "slot" : slot ,
                "sn": esn,  # info: "sn" : esn ,
                "soc": esoc if estate not in ("missing", "not_applicable", None) else None,  # info: "soc" : esoc if estate not in (
            })  # info: } )

        return {  # info: return {
            "alias": dev_alias or alias,  # info: "alias" : dev_alias or alias ,
            "sn": sn,  # info: "sn" : sn ,
            "model": model,  # info: "model" : model ,
            "observed_at": observed_at,  # info: "observed_at" : observed_at ,
            "soc": soc,  # info: "soc" : soc ,
            "ac_output_power": electrical("ac_output") or measured("device_measurement", "ac_output_power"),  # info: "ac_output_power" : electrical ( "ac_output" ) or measured
            "ac_input_power": electrical("ac_input"),  # info: "ac_input_power" : electrical ( "ac_input" ) ,
            "solar_input_power": electrical("solar_input") or electrical("xt60_input"),  # info: "solar_input_power" : electrical ( "solar_input" ) or electrical
            "usbc_output_power": electrical("usb_c_1"),  # info: "usbc_output_power" : electrical ( "usb_c_1" ) ,
            "input_power": electrical("input_total") or measured("device_measurement", "input_power"),  # info: "input_power" : electrical ( "input_total" ) or measured
            "output_power": electrical("output_total") or measured("device_measurement", "output_power"),  # info: "output_power" : electrical ( "output_total" ) or measured
            "expansions": expansions,  # info: "expansions" : expansions ,
            "source": "sqlite",  # info: "source" : "sqlite" ,
        }  # info: }
    finally:  # info: finally :
        conn.close()  # info: conn . close ( )


# ====================================================
# SECTION: function board_snapshot
# What it does: Compact board view for poller /energy display.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def board_snapshot(db_path: Path | str = DEFAULT_DB_PATH) -> dict[str, Any]:  # info: def board_snapshot
    """Compact board view for poller /energy display."""  # info: """Compact board view for poller /energy display."""
    delta = latest_for_alias("delta2", db_path)  # info: set delta
    river = latest_for_alias("river2pro", db_path)  # info: set river
    return {"delta2": delta, "river2pro": river, "db": str(db_path)}  # info: return { "delta2" : delta , "river2pro" :
