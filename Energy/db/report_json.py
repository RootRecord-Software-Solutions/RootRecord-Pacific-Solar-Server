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
# SECTION: function _stats
# What it does: Average, minimum, maximum, and count of every sample in the window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _stats(points: list) -> tuple:  # info: def _stats
    vals = [float(value) for _, value in points if value is not None]  # info: set vals
    if not vals:  # info: if not vals
        return None, None, None, 0  # info: return None , None , None , 0
    return _num(sum(vals) / len(vals)), _num(min(vals)), _num(max(vals)), len(vals)  # info: return the full-window average


# ====================================================
# SECTION: function _wh
# What it does: Watt-hours between samples in one window. A gap over 60 seconds is left out.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _wh(points: list, start, end):  # info: def _wh
    rows = [{"value": float(value), "at": at, "state": "measured"} for at, value in points if value is not None]  # info: set rows
    if len(rows) < 2:  # info: if len ( rows ) < 2
        return None  # info: return None
    energy, _covered = _energy(rows, start, end)  # info: energy , _covered = _energy ( rows , start , end )
    return _num(energy)  # info: return _num ( energy )


# ====================================================
# SECTION: function _power
# What it does: Timed power samples for one device channel inside the window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _power(raw_conn, device_id: int, channel: str, start_iso: str, end_iso: str) -> list:  # info: def _power
    return raw_conn.execute(  # info: return raw_conn . execute
        "SELECT o.observed_at, em.value_num FROM electrical_measurement em "  # info: select the channel
        "JOIN observation o ON o.observation_id=em.observation_id "  # info: join the observation
        "WHERE o.device_id=? AND em.channel=? AND em.metric_key='power_w' "  # info: this device and channel
        "AND em.state IN ('measured','defaulted') AND em.value_num IS NOT NULL "  # info: measured watts only
        "AND o.observed_at>=? AND o.observed_at<? ORDER BY o.observed_at",  # info: inside the timeframe
        (device_id, channel, start_iso, end_iso),  # info: the window
    ).fetchall()  # info: fetchall


# ====================================================
# SECTION: function _pack
# What it does: Full-window averages and watt-hours produced and spent for one pack.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pack(raw_conn, device, start, end) -> dict | None:  # info: def _pack
    start_iso, end_iso = _iso(start), _iso(end)  # info: set start_iso , end_iso
    soc_rows = raw_conn.execute(  # info: set soc_rows
        "SELECT o.observed_at, bm.value_num FROM battery_measurement bm "  # info: select state of charge
        "JOIN observation o ON o.observation_id=bm.observation_id "  # info: join the observation
        "JOIN battery b ON b.battery_id=bm.battery_id "  # info: join the battery
        "WHERE b.device_id=? AND b.battery_role='primary' AND bm.metric_key='soc_percent' "  # info: primary pack only
        "AND bm.state IN ('measured','defaulted') AND bm.value_num IS NOT NULL "  # info: measured percent only
        "AND o.observed_at>=? AND o.observed_at<? ORDER BY o.observed_at",  # info: inside the timeframe
        (device["device_id"], start_iso, end_iso),  # info: the window
    ).fetchall()  # info: fetchall
    solar = _power(raw_conn, device["device_id"], "solar_input", start_iso, end_iso)  # info: set solar
    if not solar:  # info: if the pack reports sun on the XT60 port
        solar = _power(raw_conn, device["device_id"], "xt60_input", start_iso, end_iso)  # info: set solar
    ac_out = _power(raw_conn, device["device_id"], "ac_output", start_iso, end_iso)  # info: set ac_out
    ac_in = _power(raw_conn, device["device_id"], "ac_input", start_iso, end_iso)  # info: set ac_in
    usb1 = _power(raw_conn, device["device_id"], "usb_c_1", start_iso, end_iso)  # info: set usb1
    usb2 = _power(raw_conn, device["device_id"], "usb_c_2", start_iso, end_iso)  # info: set usb2
    spent_points = _power(raw_conn, device["device_id"], "output_total", start_iso, end_iso)  # info: set spent_points
    soc_avg, soc_min, soc_max, samples = _stats(soc_rows)  # info: soc_avg , soc_min , soc_max , samples = _stats ( soc_rows )
    solar_avg, _, _, _ = _stats(solar)  # info: solar_avg from the full window
    ac_out_avg, _, _, _ = _stats(ac_out)  # info: ac_out_avg from the full window
    ac_in_avg, _, _, _ = _stats(ac_in)  # info: ac_in_avg from the full window
    usb_avgs = [avg for avg, _, _, count in (_stats(usb1), _stats(usb2)) if count]  # info: set usb_avgs
    spent_avg, _, _, _ = _stats(spent_points)  # info: spent_avg from the full window
    pack = {  # info: set pack
        "alias": device["alias"] or device["model"],  # info: "alias"
        "model": device["model"],  # info: "model"
        "soc_avg": soc_avg,  # info: "soc_avg"
        "soc_min": soc_min,  # info: "soc_min"
        "soc_max": soc_max,  # info: "soc_max"
        "samples": samples,  # info: "samples"
        "solar_w_avg": solar_avg,  # info: "solar_w_avg"
        "ac_out_w_avg": ac_out_avg,  # info: "ac_out_w_avg"
        "ac_in_w_avg": ac_in_avg,  # info: "ac_in_w_avg"
        "usbc_w_avg": _num(sum(usb_avgs)) if usb_avgs else None,  # info: "usbc_w_avg"
        "output_w_avg": spent_avg,  # info: "output_w_avg"
        "produced_wh": _wh(solar, start, end),  # info: sun watt-hours
        "spent_wh": _wh(spent_points, start, end),  # info: output watt-hours
    }  # info: end pack
    if not any(pack[key] is not None for key in ("soc_avg", "solar_w_avg", "ac_out_w_avg", "output_w_avg", "produced_wh", "spent_wh")):  # info: if the pack has no measured figure
        return None  # info: return None
    return pack  # info: return pack


# ====================================================
# SECTION: function _window
# What it does: Average every sample in the current hour, day, week, month, or year, and total watt-hours.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _window(layer: str, raw_conn, now: datetime) -> dict:  # info: def _window
    start, end = period_bounds(layer, now)  # info: start , end = period_bounds ( layer , now )
    devices = raw_conn.execute("SELECT device_id, alias, model FROM device").fetchall()  # info: set devices
    packs = []  # info: set packs
    for device in devices:  # info: for device in devices
        pack = _pack(raw_conn, device, start, end)  # info: set pack
        if pack:  # info: if pack
            packs.append(pack)  # info: packs . append
    return {"layer": layer, "period_start": _iso(start), "period_end": _iso(end), "packs": packs}  # info: return the window


# ====================================================
# SECTION: function write_period_report
# What it does: Write Energy/layers/periods.json with full averages and watt-hours for every timeframe.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_period_report(db_path=None, layers_dir=None, dest: Path | None = None) -> Path:  # info: def write_period_report
    raw_path = Path(db_path) if db_path else DEFAULT_DB_PATH  # info: set raw_path
    layers_dir = Path(layers_dir) if layers_dir else LAYERS_DIR  # info: set layers_dir
    dest = Path(dest) if dest else Path(layers_dir) / "periods.json"  # info: set dest
    raw_conn = connect(raw_path)  # info: set raw_conn
    now = datetime.now(timezone.utc)  # info: set now
    try:  # info: try
        windows = {name: _window(layer, raw_conn, now) for name, layer in REPORT_WINDOWS}  # info: set windows
    finally:  # info: finally
        raw_conn.close()  # info: raw_conn . close
    payload = {  # info: set payload
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),  # info: "updated_at"
        "source": "raw samples in each timeframe",  # info: "source"
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
    for name in ("hour", "day", "week", "month", "year"):  # info: for name in every timeframe
        window = (doc.get("windows") or {}).get(name) or {}  # info: set window
        packs = window.get("packs") or []  # info: set packs
        if not packs:  # info: if not packs
            lines.append(f"{name}: no samples")  # info: lines . append empty window
            continue  # info: continue
        span = f"{window.get('period_start')} to {window.get('period_end')}"  # info: set span
        for pack in packs:  # info: for pack in packs
            bits = [f"{pack.get('alias')} {name} {span}"]  # info: set bits
            if pack.get("soc_avg") is not None:  # info: if soc is present
                bits.append(f"soc avg {pack['soc_avg']} min {pack.get('soc_min')} max {pack.get('soc_max')}")  # info: bits . append soc
            for key, label in (("solar_w_avg", "solar_w"), ("ac_out_w_avg", "ac_out_w"), ("ac_in_w_avg", "ac_in_w"), ("usbc_w_avg", "usbc_w"), ("output_w_avg", "output_w"), ("produced_wh", "produced_wh"), ("spent_wh", "spent_wh")):  # info: for key , label
                if pack.get(key) is not None:  # info: if this figure is present
                    bits.append(f"{label} {pack[key]}")  # info: bits . append the figure
            lines.append(", ".join(bits))  # info: lines . append
    return lines  # info: return lines
