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
"""Build live-data page JSON from files this system already writes.

  python3 live_data_pages.py

Power reads Energy watts and soc last files. Weather reads the Hawaiʻi state
report header. Kīlauea reads Geology Volcanoes/kilauea-last.json.
Missing numbers are omitted. Chat, packs, day board, Minecraft, and context
are not built here.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE
OUT = DATABASE / "Website" / "pages"  # info: set OUT
ENERGY = DATABASE / "Energy"  # info: set ENERGY
WEATHER_REPORT = DATABASE / "Weather" / "Hawai'i" / "reports" / "0 Level Processing" / "Hawaii_State_Weather_Report_current.md"  # info: set WEATHER_REPORT
KILAUEA = DATABASE / "Geology" / "Volcanoes" / "kilauea-last.json"  # info: set KILAUEA
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
# ====================================================
# SECTION: POWER_FIELDS
# What it does: Set POWER_FIELDS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
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
# What it does:  now line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now_line() -> str:  # info: def _now_line
    now = datetime.now(HST)  # info: set now
    return now.strftime("%A, %B ") + str(now.day) + now.strftime(", %Y · %H:%M Hawaiian Standard Time")  # info: return now . strftime ( "%A, %B " ) +


# ====================================================
# SECTION: function _read_json
# What it does:  read json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_json(path: Path) -> dict[str, Any]:  # info: def _read_json
    if not path.is_file():  # info: if not path . is_file ( ) :
        return {}  # info: return { }
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {}  # info: return { }
    return data if isinstance(data, dict) else {}  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function _pick
# What it does:  pick.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pick(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:  # info: def _pick
    out: dict[str, Any] = {}  # info: set out
    for key in fields:  # info: for key in fields :
        if key in row and row[key] is not None:  # info: if key in row and row [ key
            out[key] = row[key]  # info: out [ key ] = row [ key
    return out  # info: return out


# ====================================================
# SECTION: function build_power
# What it does: build power.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_power() -> dict[str, Any]:  # info: def build_power
    devices: dict[str, Any] = {}  # info: set devices
    for name in ("delta2", "river2pro"):  # info: for name in ( "delta2" , "river2pro" )
        watts = _pick(_read_json(ENERGY / "watts" / f"{name}-last.json"), POWER_FIELDS)  # info: set watts
        soc = _pick(_read_json(ENERGY / "soc" / f"{name}-last.json"), ("soc", "at", "source"))  # info: set soc
        device: dict[str, Any] = {}  # info: set device
        if watts:  # info: if watts :
            device["watts"] = watts  # info: device [ "watts" ] = watts
        if soc:  # info: if soc :
            device["soc"] = soc  # info: device [ "soc" ] = soc
        if device:  # info: if device :
            devices[name] = device  # info: devices [ name ] = device
    page: dict[str, Any] = {  # info: set page
        "resource": "power",  # info: "resource" : "power" ,
        "title": "Power / solar",  # info: "title" : "Power / solar" ,
        "as_of": _now_line(),  # info: "as_of" : _now_line ( ) ,
    }  # info: }
    if devices:  # info: if devices :
        page["devices"] = devices  # info: page [ "devices" ] = devices
    return page  # info: return page


# ====================================================
# SECTION: function build_weather
# What it does: build weather.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_weather() -> dict[str, Any]:  # info: def build_weather
    page: dict[str, Any] = {  # info: set page
        "resource": "weather",  # info: "resource" : "weather" ,
        "title": "Weather",  # info: "title" : "Weather" ,
        "as_of": _now_line(),  # info: "as_of" : _now_line ( ) ,
    }  # info: }
    if not WEATHER_REPORT.is_file():  # info: if not WEATHER_REPORT . is_file ( ) :
        return page  # info: return page
    text = WEATHER_REPORT.read_text(encoding="utf-8", errors="replace")  # info: set text
    generated = re.search(r"^\- \*\*Generated:\*\* (.+)$", text, re.M)  # info: set generated
    sections = re.search(r"^\- \*\*Current report sections:\*\* (\d+)$", text, re.M)  # info: set sections
    report: dict[str, Any] = {"file": WEATHER_REPORT.name}  # info: set report
    if generated:  # info: if generated :
        report["generated"] = generated.group(1).strip()  # info: report [ "generated" ] = generated . group
    if sections:  # info: if sections :
        report["sections"] = int(sections.group(1))  # info: report [ "sections" ] = int ( sections
    page["report"] = report  # info: page [ "report" ] = report
    return page  # info: return page


# ====================================================
# SECTION: function build_kilauea
# What it does: build kilauea.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_kilauea() -> dict[str, Any]:  # info: def build_kilauea
    raw = _read_json(KILAUEA)  # info: set raw
    page: dict[str, Any] = {  # info: set page
        "resource": "kilauea",  # info: "resource" : "kilauea" ,
        "title": "Kīlauea",  # info: "title" : "Kīlauea" ,
        "as_of": _now_line(),  # info: "as_of" : _now_line ( ) ,
    }  # info: }
    if not raw:  # info: if not raw :
        return page  # info: return page
    kept = _pick(raw, ("at", "alert_level", "color_code", "headline", "erupting", "status_sent_utc"))  # info: set kept
    if kept:  # info: if kept :
        page["status"] = kept  # info: page [ "status" ] = kept
    return page  # info: return page


# ====================================================
# SECTION: function build_all
# What it does: build all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_all() -> dict[str, Any]:  # info: def build_all
    return {  # info: return {
        "power": build_power(),  # info: "power" : build_power ( ) ,
        "weather": build_weather(),  # info: "weather" : build_weather ( ) ,
        "kilauea": build_kilauea(),  # info: "kilauea" : build_kilauea ( ) ,
    }  # info: }


# ====================================================
# SECTION: function write_all
# What it does: write all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_all() -> list[Path]:  # info: def write_all
    OUT.mkdir(parents=True, exist_ok=True)  # info: OUT . mkdir ( parents = True ,
    written: list[Path] = []  # info: set written
    for name, page in build_all().items():  # info: for name , page in build_all ( )
        path = OUT / f"{name}.json"  # info: set path
        tmp = path.with_suffix(".json.tmp")  # info: set tmp
        tmp.write_text(json.dumps(page, indent=2), encoding="utf-8")  # info: tmp . write_text ( json . dumps (
        tmp.replace(path)  # info: tmp . replace ( path )
        written.append(path)  # info: written . append ( path )
    return written  # info: return written


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    paths = write_all()  # info: set paths
    print(f"live-data {len(paths)} pages")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
