# ==============================================================================
# FILE: Website/scripts/live_data_pages.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Build the ML2 /api/operations bundle from domain Database files.

  python3 live_data_pages.py

Reads Energy soc/watts, Weather Hawaiʻi report + Weather/moon, and Geology
Kīlauea. Writes only the operations bundle (Database/Website/operations.json and
the globe rebroadcast status-current.json). Does not write Website/pages/*.json —
the public site uses ML2; domain dirs are the data authority.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE
OPS_FILE = DATABASE / "Website" / "operations.json"  # info: single Website artifact for ML2 seed
STATUS_FILE = Path(  # info: set STATUS_FILE
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/"
    "Communications/network/local-data-globe/rebroadcast/status-current.json"
)  # info: end STATUS_FILE
ENERGY = DATABASE / "Energy"  # info: set ENERGY
WEATHER_REPORT = DATABASE / "Weather" / "Hawai'i" / "reports" / "0 Level Processing" / "Hawaii_State_Weather_Report_current.md"  # info: set WEATHER_REPORT
MOON = DATABASE / "Weather" / "moon" / "moon_current.json"  # info: moon under Weather
MOON_LEGACY = DATABASE / "Energy" / "moon" / "moon-last.json"  # info: drain old path
KILAUEA = DATABASE / "Geology" / "Volcanoes" / "Hawaii" / "kilauea-last.json"  # info: Hawaiʻi volcano bank
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
POWER_FIELDS = (  # info: set POWER_FIELDS
    "solar_input_power",  # info: "solar_input_power" ,
    "ac_output_power",  # info: "ac_output_power" ,
    "ac_input_power",  # info: "ac_input_power" ,
    "usbc_output_power",  # info: "usbc_output_power" ,
    "at",  # info: "at" ,
    "source",  # info: "source" ,
    "charge_source",  # info: "charge_source" ,
)  # info: )


# ====================================================
# SECTION: function _now_line
# What it does: Operator-facing as_of line in Hawaiʻi time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now_line() -> str:  # info: def _now_line
    now = datetime.now(HST)  # info: set now
    return now.strftime("%A, %B ") + str(now.day) + now.strftime(", %Y · %H:%M Hawaiian Standard Time")  # info: return now . strftime


# ====================================================
# SECTION: function _read_json
# What it does: Read one JSON object file, or {}.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_json(path: Path) -> dict[str, Any]:  # info: def _read_json
    if not path.is_file():  # info: if not path . is_file ( )
        return {}  # info: return { }
    try:  # info: try
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {}  # info: return { }
    return data if isinstance(data, dict) else {}  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function _pick
# What it does: Keep only named keys that are present and not None.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pick(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:  # info: def _pick
    out: dict[str, Any] = {}  # info: set out
    for key in fields:  # info: for key in fields
        if key in row and row[key] is not None:  # info: if key in row and row [ key
            out[key] = row[key]  # info: out [ key ] = row [ key
    return out  # info: return out


# ====================================================
# SECTION: function build_power
# What it does: Power block from Energy/soc and Energy/watts last files.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_power() -> dict[str, Any]:  # info: def build_power
    devices: dict[str, Any] = {}  # info: set devices
    for name in ("delta2", "river2pro"):  # info: for name in ( "delta2" , "river2pro" )
        watts = _pick(_read_json(ENERGY / "watts" / f"{name}-last.json"), POWER_FIELDS)  # info: set watts
        soc = _pick(_read_json(ENERGY / "soc" / f"{name}-last.json"), ("soc", "at", "source"))  # info: set soc
        device: dict[str, Any] = {}  # info: set device
        if watts:  # info: if watts
            device["watts"] = watts  # info: device [ "watts" ] = watts
        if soc:  # info: if soc
            device["soc"] = soc  # info: device [ "soc" ] = soc
        if device:  # info: if device
            devices[name] = device  # info: devices [ name ] = device
    page: dict[str, Any] = {  # info: set page
        "resource": "power",  # info: "resource" : "power" ,
        "title": "Power / solar",  # info: "title" : "Power / solar" ,
        "as_of": _now_line(),  # info: "as_of" : _now_line ( ) ,
        "source_paths": [  # info: domain authority, not Website/pages
            "Energy/soc/*-last.json",  # info: soc path
            "Energy/watts/*-last.json",  # info: watts path
        ],  # info: end source_paths
    }  # info: }
    if devices:  # info: if devices
        page["devices"] = devices  # info: page [ "devices" ] = devices
    return page  # info: return page


# ====================================================
# SECTION: function build_weather
# What it does: Weather block from the Hawaiʻi report header plus Weather/moon.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_weather() -> dict[str, Any]:  # info: def build_weather
    page: dict[str, Any] = {  # info: set page
        "resource": "weather",  # info: "resource" : "weather" ,
        "title": "Weather",  # info: "title" : "Weather" ,
        "as_of": _now_line(),  # info: "as_of" : _now_line ( ) ,
        "source_paths": [  # info: domain authority
            "Weather/Hawai'i/reports/0 Level Processing/Hawaii_State_Weather_Report_current.md",  # info: report
            "Weather/moon/moon_current.json",  # info: moon
        ],  # info: end source_paths
    }  # info: }
    if WEATHER_REPORT.is_file():  # info: if WEATHER_REPORT . is_file ( )
        text = WEATHER_REPORT.read_text(encoding="utf-8", errors="replace")  # info: set text
        generated = re.search(r"^\- \*\*Generated:\*\* (.+)$", text, re.M)  # info: set generated
        sections = re.search(r"^\- \*\*Current report sections:\*\* (\d+)$", text, re.M)  # info: set sections
        report: dict[str, Any] = {"file": WEATHER_REPORT.name}  # info: set report
        if generated:  # info: if generated
            report["generated"] = generated.group(1).strip()  # info: report [ "generated" ]
        if sections:  # info: if sections
            report["sections"] = int(sections.group(1))  # info: report [ "sections" ]
        page["report"] = report  # info: page [ "report" ] = report
    moon_raw = _read_json(MOON) or _read_json(MOON_LEGACY)  # info: Weather first, legacy Energy fallback
    moon = _pick(  # info: set moon
        moon_raw,  # info: moon_raw
        ("phase", "phase_name", "illumination", "next_phase", "next_phase_date", "fetched_at", "date"),  # info: fields
    )  # info: end _pick
    if moon:  # info: if moon
        page["moon"] = moon  # info: moon nested under weather — no separate Website page
    return page  # info: return page


# ====================================================
# SECTION: function build_kilauea
# What it does: Kīlauea block from Geology/Volcanoes/Hawaii/kilauea-last.json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_kilauea() -> dict[str, Any]:  # info: def build_kilauea
    raw = _read_json(KILAUEA)  # info: set raw
    page: dict[str, Any] = {  # info: set page
        "resource": "kilauea",  # info: "resource" : "kilauea" ,
        "title": "Kīlauea",  # info: "title" : "Kīlauea" ,
        "as_of": _now_line(),  # info: "as_of" : _now_line ( ) ,
        "source_paths": ["Geology/Volcanoes/Hawaii/kilauea-last.json"],  # info: domain authority
    }  # info: }
    if not raw:  # info: if not raw
        return page  # info: return page
    kept = _pick(raw, ("at", "alert_level", "color_code", "headline", "erupting", "status_sent_utc"))  # info: set kept
    if kept:  # info: if kept
        page["status"] = kept  # info: page [ "status" ] = kept
    return page  # info: return page


# ====================================================
# SECTION: function build_bundle
# What it does: One operations document for ML2 /api/operations from domain files only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_bundle() -> dict[str, Any]:  # info: def build_bundle
    weather = build_weather()  # info: set weather
    report = weather.get("report")  # info: set report
    weather_out = dict(weather)  # info: set weather_out
    if isinstance(report, dict):  # info: if isinstance ( report , dict )
        weather_out["report"] = {k: v for k, v in report.items() if k != "file"}  # info: strip local filename
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "kind": "last-known",  # info: "kind" : "last-known" ,
        "as_of": _now_line(),  # info: "as_of" : _now_line ( ) ,
        "power": build_power(),  # info: from Energy/
        "weather": weather_out,  # info: from Weather/ (includes moon)
        "kilauea": build_kilauea(),  # info: from Geology/
    }  # info: }


# ====================================================
# SECTION: function _atomic_write
# What it does: Atomically replace one JSON file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _atomic_write(path: Path, obj: dict[str, Any]) -> Path:  # info: def _atomic_write
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    tmp.replace(path)  # info: tmp . replace ( path )
    return path  # info: return path


# ====================================================
# SECTION: function write_all
# What it does: Write operations.json + status-current.json only. Removes Website/pages if present.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_all() -> list[Path]:  # info: def write_all
    bundle = build_bundle()  # info: set bundle
    written = [  # info: set written
        _atomic_write(OPS_FILE, bundle),  # info: ML2 seed / desk mirror
        _atomic_write(STATUS_FILE, bundle),  # info: globe rebroadcast → ML2 cache
    ]  # info: end written
    pages = OPS_FILE.parent / "pages"  # info: set pages
    if pages.is_dir():  # info: retire redundant page copies
        for path in pages.glob("*.json"):  # info: for path in pages . glob
            try:  # info: try
                path.unlink()  # info: path . unlink ( )
            except OSError:  # info: except OSError
                pass  # info: pass
        try:  # info: try
            pages.rmdir()  # info: pages . rmdir ( )
        except OSError:  # info: except OSError
            pass  # info: pass
    return written  # info: return written


# ====================================================
# SECTION: function main
# What it does: Rebuild the ML2 operations bundle from domain Database files.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    paths = write_all()  # info: set paths
    print(f"live-data {len(paths)} files (domain sources → operations bundle)")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
