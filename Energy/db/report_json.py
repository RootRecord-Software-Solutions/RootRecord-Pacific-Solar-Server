# ==============================================================================
# FILE: Energy/db/report_json.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""JSON snapshot of EcoFlow averages for the current hour, day, week, month, and year."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

from Energy.db.aggregate import _energy, _iso, period_bounds  # info: from Energy . db . aggregate import _energy
from Energy.db.store import DEFAULT_DB_PATH, LAYERS_DIR, connect  # info: from Energy . db . store import DEFAULT_DB_PATH


REPORT_WINDOWS = (("hour", "1hour"), ("day", "day"), ("week", "7days"), ("month", "month"), ("year", "year"))  # info: set REPORT_WINDOWS
REPORT_JSON = Path(os.environ.get("ROOTRECORD_ENERGY_PERIODS", str(LAYERS_DIR / "periods.json")))  # info: set REPORT_JSON


# ====================================================
# SECTION: function _num
# What it does: Round a measured number, or leave it empty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _num(value):  # info: def _num
    if value is None:  # info: if value is None
        return None  # info: return None
    return round(float(value), 2)  # info: return round ( float ( value ) , 2 )


# ====================================================
# SECTION: function _pick
# What it does: First measured metric row for a key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pick(rows: list, key: str):  # info: def _pick
    for row in rows:  # info: for row in rows
        if row["metric_key"] == key and int(row["valid_sample_count"] or 0) > 0:  # info: if this key was measured
            return row  # info: return row
    return None  # info: return None


# ====================================================
# SECTION: function _avg
# What it does: Average of one measured metric, or None.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _avg(rows: list, key: str):  # info: def _avg
    row = _pick(rows, key)  # info: set row
    return _num(row["value_avg"]) if row else None  # info: return the average or None


# ====================================================
# SECTION: function _pack
# What it does: One pack's measured hour, day, week, or month figures.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pack(alias: str, model: str, rows: list, primary_id) -> dict | None:  # info: def _pack
    device_rows = [row for row in rows if row["subject_type"] == "device"]  # info: set device_rows
    primary = [row for row in rows if row["subject_type"] == "battery" and row["subject_id"] == primary_id]  # info: set primary
    soc = _pick(primary, "soc_percent")  # info: set soc
    usbc = [v for v in (_avg(device_rows, "electrical:usb_c_1:power_w"), _avg(device_rows, "electrical:usb_c_2:power_w")) if v is not None]  # info: set usbc
    out_row = _pick(device_rows, "electrical:output_total:power_w") or _pick(device_rows, "output_power")  # info: set out_row
    pack = {  # info: set pack
        "alias": alias,  # info: "alias"
        "model": model,  # info: "model"
        "soc_avg": _num(soc["value_avg"]) if soc else None,  # info: "soc_avg"
        "soc_min": _num(soc["value_min"]) if soc else None,  # info: "soc_min"
        "soc_max": _num(soc["value_max"]) if soc else None,  # info: "soc_max"
        "samples": int(soc["valid_sample_count"]) if soc else 0,  # info: "samples"
        "solar_w_avg": _avg(device_rows, "electrical:solar_input:power_w"),  # info: "solar_w_avg"
        "ac_out_w_avg": _avg(device_rows, "electrical:ac_output:power_w"),  # info: "ac_out_w_avg"
        "ac_in_w_avg": _avg(device_rows, "electrical:ac_input:power_w"),  # info: "ac_in_w_avg"
        "usbc_w_avg": _num(sum(usbc)) if usbc else None,  # info: "usbc_w_avg"
        "output_w_avg": _avg(device_rows, "output_power"),  # info: "output_w_avg"
        "input_w_avg": _avg(device_rows, "input_power"),  # info: "input_w_avg"
        "energy_wh": _num(out_row["energy_wh"]) if out_row else None,  # info: "energy_wh"
    }  # info: end pack
    measured = [pack[key] for key in ("soc_avg", "solar_w_avg", "ac_out_w_avg", "ac_in_w_avg", "usbc_w_avg", "output_w_avg")]  # info: set measured
    if not any(value is not None for value in measured):  # info: if the pack has no measured figure
        return None  # info: return None
    return pack  # info: return pack


# ====================================================
# SECTION: function _window
# What it does: Latest closed period in one layer database, grouped by pack.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _window(layer: str, raw_conn, layers_dir: Path) -> dict:  # info: def _window
    path = layer_db_path(layer, layers_dir)  # info: set path
    empty = {"layer": layer, "period_start": None, "period_end": None, "packs": []}  # info: set empty
    if not path.is_file():  # info: if not path . is_file
        return empty  # info: return empty
    conn = connect(path)  # info: set conn
    try:  # info: try
        run = conn.execute(  # info: set run
            "SELECT aggregation_run_id, period_start, period_end FROM aggregation_run "  # info: select the latest complete run
            "WHERE layer=? AND status='complete' ORDER BY period_end DESC LIMIT 1",  # info: closed period only
            (layer,),  # info: layer
        ).fetchone()  # info: fetchone
        if not run:  # info: if not run
            return empty  # info: return empty
        rows = conn.execute(  # info: set rows
            "SELECT subject_type, subject_id, metric_key, value_avg, value_min, value_max, energy_wh, valid_sample_count "  # info: measured columns
            "FROM aggregate_measurement WHERE aggregation_run_id=?",  # info: this run only
            (run["aggregation_run_id"],),  # info: run id
        ).fetchall()  # info: fetchall
    finally:  # info: finally
        conn.close()  # info: conn . close
    devices = raw_conn.execute("SELECT device_id, alias, model FROM device").fetchall()  # info: set devices
    batteries = raw_conn.execute("SELECT battery_id, device_id, battery_role FROM battery").fetchall()  # info: set batteries
    packs = []  # info: set packs
    for device in devices:  # info: for device in devices
        owned = {row["battery_id"] for row in batteries if row["device_id"] == device["device_id"]}  # info: set owned
        primary = next((row["battery_id"] for row in batteries if row["device_id"] == device["device_id"] and row["battery_role"] == "primary"), None)  # info: set primary
        mine = [row for row in rows if (row["subject_type"] == "device" and row["subject_id"] == device["device_id"]) or (row["subject_type"] == "battery" and row["subject_id"] in owned)]  # info: set mine
        pack = _pack(device["alias"] or device["model"], device["model"], mine, primary)  # info: set pack
        if pack:  # info: if pack
            packs.append(pack)  # info: packs . append
    return {"layer": layer, "period_start": run["period_start"], "period_end": run["period_end"], "packs": packs}  # info: return the window


# ====================================================
# SECTION: function write_period_report
# What it does: Write Energy/layers/periods.json from the closed hour, day, week, and month databases.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_period_report(db_path=None, layers_dir=None, dest: Path | None = None) -> Path:  # info: def write_period_report
    raw_path = Path(db_path) if db_path else DEFAULT_DB_PATH  # info: set raw_path
    layers_dir = Path(layers_dir) if layers_dir else LAYERS_DIR  # info: set layers_dir
    dest = Path(dest) if dest else REPORT_JSON  # info: set dest
    raw_conn = connect(raw_path)  # info: set raw_conn
    try:  # info: try
        windows = {name: _window(layer, raw_conn, layers_dir) for name, layer in REPORT_WINDOWS}  # info: set windows
    finally:  # info: finally
        raw_conn.close()  # info: raw_conn . close
    payload = {  # info: set payload
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),  # info: "updated_at"
        "source": "Energy/layers",  # info: "source"
        "windows": windows,  # info: "windows"
    }  # info: end payload
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir
    tmp = dest.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, dest)  # info: os . replace
    return dest  # info: return dest


# ====================================================
# SECTION: function period_lines
# What it does: Short lines an AI report can quote from periods.json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def period_lines(doc: dict | None) -> list[str]:  # info: def period_lines
    if not isinstance(doc, dict):  # info: if not isinstance ( doc , dict )
        return []  # info: return [ ]
    lines = []  # info: set lines
    for name in ("hour", "day", "week", "month"):  # info: for name in the four windows
        window = (doc.get("windows") or {}).get(name) or {}  # info: set window
        packs = window.get("packs") or []  # info: set packs
        if not packs:  # info: if not packs
            lines.append(f"{name}: no closed period")  # info: lines . append empty window
            continue  # info: continue
        span = f"{window.get('period_start')} to {window.get('period_end')}"  # info: set span
        for pack in packs:  # info: for pack in packs
            bits = [f"{pack.get('alias')} {name} {span}"]  # info: set bits
            if pack.get("soc_avg") is not None:  # info: if soc is present
                bits.append(f"soc avg {pack['soc_avg']} min {pack.get('soc_min')} max {pack.get('soc_max')}")  # info: bits . append soc
            for key, label in (("solar_w_avg", "solar_w"), ("ac_out_w_avg", "ac_out_w"), ("ac_in_w_avg", "ac_in_w"), ("usbc_w_avg", "usbc_w"), ("energy_wh", "energy_wh")):  # info: for key , label
                if pack.get(key) is not None:  # info: if this figure is present
                    bits.append(f"{label} {pack[key]}")  # info: bits . append the figure
            lines.append(", ".join(bits))  # info: lines . append
    return lines  # info: return lines
