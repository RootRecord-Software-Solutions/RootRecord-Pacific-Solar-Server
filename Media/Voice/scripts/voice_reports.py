# ==============================================================================
# FILE: Media/Voice/scripts/voice_reports.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""G3 voice reports (template-first ports of G1 desks). Stdlib only; run with system python3.

  python3 voice_reports.py <report> [--no-voice]
  reports: hourly_chime · nws_weather · energy_report · remaining_tasks · morning_report · midday_report · late_report
           · earthquake_report · hurricane_desk · kilauea_report · solar_desk · security_desk · bandwidth_desk
           · official_weather · boot_brief · current_report

Each run writes Database Media/Audio/Voice/Reports/<report>_current.md (old copy -> Reports/Archive/
<report>_YYYYMMDDTHHMM.md) and a stitched WAV Media/Audio/Voice/<report>_current.wav via voice-render.sh
(single-flight lock, nice 10, phrase-clip cache, non-resident). If the lock is busy the WAV is skipped
(rc 75 recorded) and the text still lands. A Telegram voice note posts only when RR_VOICE_DELIVER=1. RR_TELEGRAM_DEST=council selects the original council chat. After a finished WAV, radio_push.py sends that one _current file to the Mainland library over SSH unless RR_RADIO_PUSH=0. Speakers stay off. The Mainland host does not fetch.
Only G3 data that exists is read: Database Energy/{soc,watts}/*-last.json (EcoFlow BLE), Database
Weather/Hawai'i (NWS alerts + SFP state forecast, Pacific weather poller), Library Work-Order checkboxes,
/proc, and Database Geology/Earthquakes/{hawaii,global}-last.json (Pacific Geology/scripts/geology_collect.py,
job geology_collect gated RR_GEOLOGY=1). earthquake_report = G1 earthquake-hourly spoken script (Carly), job gated
RR_VOICE_QUAKE=1 (2026-09-29, migration-geology). G1 council_quake (Telegram per-quake posts) stays NOT ported.
hurricane_desk = G1 weather/hurricane-desk Hawaiʻi block (Carly), fed from Database Weather/Hawai'i/hurricanes/
tracking/*/track.json (Pacific weather poller, NHC CurrentStorms, Hawaiʻi-relevant storms only) + NWS HI alerts; job gated
RR_VOICE_HURRICANE=1. G1 global JTWC/RAMMB board, OBS and radio push stay NOT ported.
kilauea_report = G1 hourly Kīlauea desk line (persona._kilauea_line) + the cached HVO-notice lead-in, from Database
Geology/Volcanoes/{kilauea,mauna-loa}-last.json; job gated RR_VOICE_KILAUEA=1. G1 rr-kilauea Grok draft / Discord post NOT ported.
solar_desk / security_desk / bandwidth_desk = G1 hourly-clip-reports desks (Bruce solar; Carly security + bandwidth) from
Database Energy/{soc,watts,sun} and Pacific System/scripts/host_desks.py (net samples in Database System/network/).
Gates PROPOSED (RR_VOICE_SOLAR / RR_VOICE_SECURITY / RR_VOICE_BANDWIDTH) - not registered in jobs.py (sign-off).
official_weather = G1 official-weather-media spoken statement (Ava): HLS (Pacific Weather/scripts/official_statement.py ->
Database Weather/Hawai'i/official/) or HWO / AFD (weather poller text products). boot_brief = G1 boot-prelims Boot Report
(file-only, no Grok) as a template brief (Ava). Both PROPOSED (RR_VOICE_OFFICIAL / RR_VOICE_BOOT), not in jobs.py.
Roll-ups append an LLM summary via run-infer.sh only when RR_VOICE_ROLLUP_LLM=1 (off by default). The off state is not written into the report.
Scheduling: jobs.py, one env gate per report (read at poller start). Added 2026-09-29 (g3-voice-reports2).
current_report runs at :00 and :30 and summarizes the same measured desks. Headings use the scheduled slot, not the finish time.
Morning, midday, and late stay at 09:00, 12:00, and 21:00.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import sys  # info: import sys
import tempfile  # info: import tempfile
import time  # info: import time
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
from speakable import spoken_clock  # noqa: E402
from speakers import retire_current  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
LIB = Path(os.environ.get("RR_LIBRARY_ROOT", "/home/rootrecord/RootRecord-Ecosystem/5 - RootRecord-Library"))  # info: set LIB
PACIFIC = HERE.parents[2]  # info: set PACIFIC
REPORTS = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))  # info: set REPORTS
WX = DB / "Weather" / "Hawai'i"  # info: set WX
ALERTS = WX / "hfo" / "api.weather.gov" / "alerts" / "active" / "area=HI" / "area=HI_current.json"  # info: set ALERTS
SFP = WX / "reports" / "0 Level Processing" / "sfp_state_forecast_current.md"  # info: set SFP
ZFP = WX / "hfo" / "api.weather.gov" / "products" / "types" / "ZFP" / "locations" / "HFO" / "HFO_current.txt"  # info: set ZFP
ENERGY = DB / "Energy"  # info: set ENERGY
QUAKES = DB / "Geology" / "Earthquakes"  # info: set QUAKES
QUAKE_STATE = REPORTS / "earthquake_report_seen.json"  # G1 earthquake-hourly.json seen_ids (new since last report)
QUAKE_STALE_MIN = 20  # info: set QUAKE_STALE_MIN
VOLCANOES = DB / "Geology" / "Volcanoes"  # info: set VOLCANOES
HVO_STALE_MIN = 30  # info: set HVO_STALE_MIN
_MAX_HI, _MAX_GLOBAL = 6, 8  # G1 spoken caps
HURRICANES = WX / "hurricanes" / "tracking"  # <Storm>_<first-seen>/track.json (Pacific Weather/hurricanes/scripts/sources.py)
HUR_ACTIVE_H = 6  # a track polled within this many hours counts as on the board
HAWAII_THREAT_NM = 800  # G1 hurricane_desk
HAWAII_POS = {"Honolulu": (21.3069, -157.8583), "Hilo": (19.7297, -155.0900), "Līhuʻe": (21.9811, -159.3711),  # info: set HAWAII_POS
              "Kona": (19.6390, -155.9969)}  # G1 hurricane_desk HAWAII_POS
TROPICAL_EVENTS = ("hurricane", "tropical storm", "tropical depression", "typhoon", "cyclone", "storm surge")  # info: set TROPICAL_EVENTS
COMPASS = ("north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest")  # info: set COMPASS
STORM_CLASS = {"HU": "Hurricane", "TS": "Tropical Storm", "TD": "Tropical Depression", "STS": "Subtropical Storm",  # info: set STORM_CLASS
               "SS": "Subtropical Storm", "SD": "Subtropical Depression", "PTC": "Post-tropical Cyclone",  # info: "SS" : "Subtropical Storm" , "SD" : "Subtropical Depression" ,
               "PC": "Post-tropical Cyclone", "TY": "Typhoon", "STY": "Super Typhoon"}  # NHC classification codes
DEVICES = (("delta2", "Delta 2"), ("river2pro", "River 2 Pro"))  # info: set DEVICES
STALE_MIN = 30  # info: set STALE_MIN
DELTA_GEN_W = 550  # info: Delta 2 AC in above this is the generator
RIVER_GEN_W = 300  # info: River 2 Pro AC in above this is the generator
# ====================================================
# SECTION: KIND
# What it does: Set KIND.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
KIND = {"hourly_chime": "chime", "nws_weather": "nws", "energy_report": "energy", "remaining_tasks": "remaining",  # info: set KIND
        "morning_report": "morning", "midday_report": "midday", "late_report": "late", "earthquake_report": "earthquake",  # info: "morning_report" : "morning" , "midday_report" : "midday" ,
        "hurricane_desk": "hurricane", "kilauea_report": "kilauea",  # info: "hurricane_desk" : "hurricane" , "kilauea_report" : "kilauea" ,
        "solar_desk": "solar", "security_desk": "security", "bandwidth_desk": "bandwidth",  # info: "solar_desk" : "solar" , "security_desk" : "security" ,
        "official_weather": "official", "boot_brief": "boot", "current_report": "current"}  # info: "official_weather" : "official" , "boot_brief" : "boot" , "current_report" : "current"
DEV_NOTE = "Automated Reports are in active development and is expected to change"  # info: set DEV_NOTE
ROLLUP_AT = {"morning": (9, 0), "midday": (12, 0), "late": (21, 0)}  # info: set ROLLUP_AT }


# ====================================================
# SECTION: function now
# What it does: now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> datetime:  # info: def now
    return datetime.now().astimezone().replace(microsecond=0)  # info: return datetime . now ( ) . astimezone


# ====================================================
# SECTION: function on_the_dot
# What it does: Scheduled clock with seconds cleared. Half hours snap to :00 or :30. A named hour and minute stay put.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def on_the_dot(t: datetime, hour: int | None = None, minute: int | None = None) -> datetime:  # info: def on_the_dot
    if hour is None:  # info: if hour is None :
        hour = t.hour  # info: set hour
        minute = 0 if t.minute < 30 else 30  # info: set minute
    return t.replace(hour=hour, minute=0 if minute is None else minute, second=0, microsecond=0)  # info: return t . replace (


# ====================================================
# SECTION: function clock
# What it does: clock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clock(t: datetime) -> str:  # info: def clock
    return spoken_clock(t.hour, t.minute)  # info: return spoken_clock ( t . hour , t


# ====================================================
# SECTION: function jload
# What it does: jload.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def jload(p: Path):  # info: def jload
    try:  # info: try :
        return json.loads(p.read_text(encoding="utf-8"))  # info: return json . loads ( p . read_text
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return None  # info: return None


# ------------------------------------------------------------------ data readers (existing G3 sources only)
# ====================================================
# SECTION: function energy_facts
# What it does: energy facts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def energy_facts(t: datetime) -> list[dict]:  # info: def energy_facts
    out = []  # info: set out
    for key, name in DEVICES:  # info: for key , name in DEVICES :
        soc, watts = jload(ENERGY / "soc" / f"{key}-last.json"), jload(ENERGY / "watts" / f"{key}-last.json") or {}  # info: soc , watts = jload ( ENERGY /
        if not soc or "soc" not in soc:  # info: if not soc or "soc" not in soc
            out.append({"name": name, "ok": False})  # info: out . append ( { "name" : name
            continue  # info: continue
        try:  # info: try :
            age = int((t - datetime.fromisoformat(soc["at"])).total_seconds() // 60)  # info: set age
        except (KeyError, ValueError):  # info: except ( KeyError , ValueError ) :
            age = None  # info: set age
        out.append({"name": name, "ok": True, "soc": round(float(soc["soc"])), "at": soc.get("at"), "age_min": age,  # info: out . append ( { "name" : name
                    "solar_w": watts.get("solar_input_power"), "ac_out_w": watts.get("ac_output_power"),  # info: "solar_w" : watts . get ( "solar_input_power" )
                    "usbc_out_w": watts.get("usbc_output_power"), "ac_in_w": watts.get("ac_input_power"),  # info: "usbc_out_w" : watts . get ( "usbc_output_power" )
                    "charge": watts.get("charge_source")})  # info: "charge" : watts . get ( "charge_source" )
    mark_supply(out)  # info: label generator or a Delta-to-River transfer
    return out  # info: return out


# ====================================================
# SECTION: function _watts
# What it does: Float watts, or None when the field is missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _watts(v):  # info: def _watts
    try:  # info: try :
        return float(v)  # info: return float ( v )
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return None  # info: return None


# ====================================================
# SECTION: function watts_match
# What it does: True when Delta AC out and River AC in are the same transfer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def watts_match(a, b) -> bool:  # info: def watts_match
    if a is None or b is None:  # info: if a is None or b is None :
        return False  # info: return False
    if a < 20 or b < 20:  # info: if a < 20 or b < 20 :
        return False  # info: return False
    return abs(a - b) <= max(40.0, 0.12 * max(a, b))  # info: return abs ( a - b ) <= max ( 40.0 , 0.12 * max ( a , b ) )


# ====================================================
# SECTION: function mark_supply
# What it does: Delta AC in over 550 W, or River AC in over 300 W, is generator. A matching Delta output is a transfer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mark_supply(facts: list[dict]) -> None:  # info: def mark_supply
    by = {f.get("name"): f for f in facts if f.get("ok")}  # info: set by
    delta, river = by.get("Delta 2"), by.get("River 2 Pro")  # info: delta , river = by . get (
    d_out = _watts(delta.get("ac_out_w")) if delta else None  # info: set d_out
    r_in = _watts(river.get("ac_in_w")) if river else None  # info: set r_in
    transfer = watts_match(d_out, r_in)  # info: set transfer
    if delta:  # info: if delta :
        d_in = _watts(delta.get("ac_in_w"))  # info: set d_in
        delta["supply"] = "generator" if d_in is not None and d_in > DELTA_GEN_W else None  # info: delta [ "supply" ] = "generator" if d_in
        delta["feeding"] = "transfer" if transfer else None  # info: delta [ "feeding" ] = "transfer" if transfer else None
    if river:  # info: if river :
        if transfer:  # info: if transfer :
            river["supply"] = "transfer"  # info: river [ "supply" ] = "transfer"
        else:  # info: else :
            river["supply"] = "generator" if r_in is not None and r_in > RIVER_GEN_W else None  # info: river [ "supply" ] = "generator" if r_in


# ====================================================
# SECTION: function supply_clause
# What it does: Spoken generator or transfer clause. Empty when neither applies.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def supply_clause(f: dict) -> str:  # info: def supply_clause
    if f.get("supply") == "generator":  # info: if f . get ( "supply" ) == "generator" :
        return f", on generator, AC in {spoken_watts(f.get('ac_in_w'))}"  # info: return f" , on generator, AC in { spoken_watts
    if f.get("supply") == "transfer":  # info: if f . get ( "supply" ) == "transfer" :
        return ", transfer from the Delta 2"  # info: return ", transfer from the Delta 2"
    if f.get("feeding") == "transfer":  # info: if f . get ( "feeding" ) == "transfer" :
        return ", transfer to the River 2 Pro"  # info: return ", transfer to the River 2 Pro"
    return ""  # info: return ""


# ====================================================
# SECTION: function range_clause
# What it does: Out-of-range line when a pack reading is stale. Does not call it old.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def range_clause(f: dict) -> str | None:  # info: def range_clause
    age = f.get("age_min")  # info: set age
    if not f.get("ok") or age is None or age <= STALE_MIN:  # info: if not f . get ( "ok" ) or age is None or age <= STALE_MIN :
        return None  # info: return None
    return f"{f['name']} is out of range."  # info: return f" { f [ 'name' ] } is out of range. "


# ====================================================
# SECTION: function alerts
# What it does: alerts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def alerts() -> tuple[list[dict], str | None]:  # info: def alerts
    d = jload(ALERTS)  # info: set d
    if not isinstance(d, dict):  # info: if not isinstance ( d , dict )
        return [], None  # info: return [ ] , None
    rows = []  # info: set rows
    for f in d.get("features") or []:  # info: for f in d . get ( "features"
        p = f.get("properties") or {}  # info: set p
        rows.append({"event": p.get("event") or "Alert", "area": (p.get("areaDesc") or "").replace(";", ","),  # info: rows . append ( { "event" : p
                     "expires": p.get("expires") or p.get("ends")})  # info: "expires" : p . get ( "expires" )
    return rows, d.get("updated")  # info: return rows , d . get ( "updated"


# ====================================================
# SECTION: function _flat
# What it does: Collapse a forecast paragraph to one line. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _flat(text: str) -> str:  # info: def _flat
    return " ".join((text or "").split())  # info: return " " . join ( ( text or "" ) . split ( ) )


# ====================================================
# SECTION: function _shore
# What it does: Keep the shore temperature when a zone also lists an elevation. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _shore(phrase: str) -> str:  # info: def _shore
    raw = (phrase or "").strip(" ,")  # info: set raw
    cut = re.split(r" near the shore| near \d| at \d{3,}| to around \d+", raw, maxsplit=1)[0].strip(" ,")  # info: set cut
    if cut and cut != raw:  # info: if cut and cut != raw
        return cut + " at the shore"  # info: return cut + " at the shore"
    return cut  # info: return cut


# ====================================================
# SECTION: function sfp_read
# What it does: Issued stamp and island groups from the HFO state forecast. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sfp_read() -> tuple[str | None, list[dict]]:  # info: def sfp_read
    """Issued stamp and island groups [{name, periods:[(label, body)]}] from the HFO state forecast. Does not send."""  # info: """Issued stamp and island groups from the HFO state forecast. Does not send."""
    try:  # info: try :
        txt = SFP.read_text(encoding="utf-8")  # info: set txt
    except OSError:  # info: except OSError :
        return None, []  # info: return None , [ ]
    issued = re.search(r"^\d{3,4} [AP]M HST .+ \d{4}$", txt, re.M)  # info: set issued
    fence = re.search(r"```text\n(.+?)\n```", txt, re.S)  # info: set fence
    body = fence.group(1) if fence else txt  # info: set body
    period = re.compile(r"^\.([A-Z][A-Z ]+)\.\.\.(.+?)(?=^\.[A-Z]|^HIZ|```|\Z)", re.M | re.S)  # info: set period
    parts = re.split(r"(?m)^([A-Za-z][A-Za-z ,'ʻ.-]*[A-Za-z])-\s*$", body)  # info: set parts
    groups = []  # info: set groups
    i = 1  # info: set i
    while i + 1 < len(parts):  # info: while i + 1 < len ( parts )
        name = parts[i].replace("-", ", ")  # info: set name
        periods = [(m.group(1).title(), _flat(m.group(2))) for m in period.finditer(parts[i + 1])]  # info: set periods
        if periods:  # info: if periods :
            groups.append({"name": name, "periods": periods})  # info: groups . append ( { "name" : name , "periods" : periods } )
        i += 2  # info: set i
    if not groups:  # info: if not groups :
        periods = [(m.group(1).title(), _flat(m.group(2))) for m in period.finditer(body)]  # info: set periods
        if periods:  # info: if periods :
            groups.append({"name": "State", "periods": periods})  # info: groups . append ( { "name" : "State" , "periods" : periods } )
    return (issued.group(0) if issued else None), groups  # info: return issued line , groups


# ====================================================
# SECTION: function sfp_today
# What it does: First forecast period of the NWS HFO State Forecast (SFP) for Kauai–Oahu–Maui–Molokai–Lanai.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sfp_today() -> tuple[str | None, str | None]:  # info: def sfp_today
    """First forecast period of the NWS HFO State Forecast (SFP) for Kauai–Oahu–Maui–Molokai–Lanai."""  # info: """First forecast period of the NWS HFO State Forecast (SFP) for Kauai–Oahu–Maui–Molokai–Lanai."""
    issued, groups = sfp_read()  # info: issued , groups = sfp_read ( )
    if not groups or not groups[0]["periods"]:  # info: if not groups or not groups [ 0 ] [ "periods" ]
        return None, issued  # info: return None , issued
    label, body = groups[0]["periods"][0]  # info: label , body = groups [ 0 ] [ "periods" ] [ 0 ]
    return f"{label}: {body}", issued  # info: return first period , issued


# ====================================================
# SECTION: function zfp_temps
# What it does: Today high and tonight low for Honolulu, Lihue, Kahului, Hilo, and Kailua-Kona. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def zfp_temps() -> list[dict]:  # info: def zfp_temps
    """Today high and tonight low from the HFO zone forecast. Shore number when a zone also lists elevation. Does not send."""  # info: """Today high and tonight low from the HFO zone forecast. Does not send."""
    places = (("Honolulu Metro", "Honolulu"), ("Kauai East", "Lihue"), ("Maui Central Valley North", "Kahului"),  # info: set places
              ("Big Island East", "Hilo"), ("Kona", "Kailua-Kona"))  # info: ( "Big Island East" , "Hilo" ) , ( "Kona" , "Kailua-Kona" )
    try:  # info: try :
        txt = ZFP.read_text(encoding="utf-8")  # info: set txt
    except OSError:  # info: except OSError :
        return []  # info: return [ ]
    found = {}  # info: set found
    for block in re.split(r"(?m)^HIZ\d+", txt):  # info: for block in re . split
        name_m = re.search(r"(?m)^([A-Za-z][A-Za-z ]+)-\s*$", block)  # info: set name_m
        if not name_m:  # info: if not name_m :
            continue  # info: continue
        key = name_m.group(1).strip()  # info: set key
        if key in found or key not in {zone for zone, _ in places}:  # info: if key in found or key not in zones
            continue  # info: continue
        row = {"place": dict(places)[key], "high": None, "low": None}  # info: set row
        for label, word, field in (("TODAY", "Highs", "high"), ("TONIGHT", "Lows", "low")):  # info: for label , word , field
            hit = re.search(rf"(?ms)^\.{label}\.\.\.(.+?)(?=^\.[A-Z]|\Z)", block)  # info: set hit
            if not hit:  # info: if not hit :
                continue  # info: continue
            deg = re.search(rf"\b{word}\s+(.+?)(?:\.|$)", _flat(hit.group(1)))  # info: set deg
            if deg:  # info: if deg :
                row[field] = _shore(deg.group(1))  # info: row [ field ] = _shore
        if row["high"] or row["low"]:  # info: if row [ "high" ] or row [ "low" ]
            found[key] = row  # info: found [ key ] = row
    return [found[zone] for zone, _ in places if zone in found]  # info: return rows in place order


# ====================================================
# SECTION: function open_tasks
# What it does: open tasks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def open_tasks() -> tuple[int, list[tuple[int, str]]]:  # info: def open_tasks
    wo = LIB / "Documentation" / "06-development" / "Work-Orders"  # info: set wo
    per = []  # info: set per
    for f in sorted(wo.glob("*.md")):  # info: for f in sorted ( wo . glob
        try:  # info: try :
            n = len(re.findall(r"^\s*- \[ \]", f.read_text(encoding="utf-8"), re.M))  # info: set n
        except OSError:  # info: except OSError :
            continue  # info: continue
        if n:  # info: if n :
            code = re.search(r"(WO-[A-Z0-9-]+?)(?:-\d{4}-\d{2}-\d{2})?(?:\.md|-Action)", f.name)  # info: set code
            per.append((n, code.group(1) if code else f.stem))  # info: per . append ( ( n , code
    per.sort(key=lambda x: (-x[0], x[1]))  # info: per . sort ( key = lambda x
    return sum(n for n, _ in per), per  # info: return sum ( n for n , _


# ====================================================
# SECTION: function host
# What it does: host.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host() -> dict:  # info: def host
    def snap():  # info: def snap
        v = [int(x) for x in open("/proc/stat").readline().split()[1:]]  # info: set v
        return sum(v), v[3] + (v[4] if len(v) > 4 else 0)  # info: return sum ( v ) , v [
    t1, i1 = snap(); time.sleep(0.5); t2, i2 = snap()  # info: t1 , i1 = snap ( ) ;
    m = {ln.split(":")[0]: int(ln.split()[1]) for ln in open("/proc/meminfo")}  # info: set m
    return {"cpu": round(100 * (1 - (i2 - i1) / max(1, t2 - t1))), "mem": round(100 * (1 - m["MemAvailable"] / m["MemTotal"]))}  # info: return { "cpu" : round ( 100 *


# ====================================================
# SECTION: function quake_facts
# What it does: Database Geology/Earthquakes last files (written by Pacific Geology/scripts/geology_collect.py).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def quake_facts(t: datetime) -> dict:  # info: def quake_facts
    """Database Geology/Earthquakes last files (written by Pacific Geology/scripts/geology_collect.py)."""  # info: """Database Geology/Earthquakes last files (written by Pacific Geology/scripts/geology_collect.py)."""
    out = {}  # info: set out
    for key in ("hawaii", "global"):  # info: for key in ( "hawaii" , "global" )
        d = jload(QUAKES / f"{key}-last.json")  # info: set d
        if not isinstance(d, dict) or not isinstance(d.get("events"), list):  # info: if not isinstance ( d , dict )
            out[key] = None  # info: out [ key ] = None
            continue  # info: continue
        try:  # info: try :
            age = int((t - datetime.fromisoformat(d["at"])).total_seconds() // 60)  # info: set age
        except (KeyError, TypeError, ValueError):  # info: except ( KeyError , TypeError , ValueError )
            age = None  # info: set age
        out[key] = dict(d, age_min=age)  # info: out [ key ] = dict ( d
    return out  # info: return out


# ====================================================
# SECTION: function _m25
# What it does:  m25.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _m25(events: list[dict]) -> list[dict]:  # info: def _m25
    out = []  # info: set out
    for e in events:  # info: for e in events :
        try:  # info: try :
            if float(e.get("mag") or 0) >= 2.5:  # info: if float ( e . get ( "mag"
                out.append(e)  # info: out . append ( e )
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            continue  # info: continue
    return out  # info: return out


# ------------------------------------------------------------------ builders: (markdown, spoken sentences)
# ====================================================
# SECTION: function b_hourly_chime
# What it does: Prebuilt :00 and :30 chime. Ava, Bruce, and Carly leapfrog by the hour. No live render.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_hourly_chime(t: datetime):  # info: def b_hourly_chime
    from hourly_chimes import chime_sentence, persona_for  # info: from hourly_chimes import chime_sentence , persona_for
    hour, minute = t.hour, t.minute  # info: hour , minute = t . hour , t . minute
    line = chime_sentence(hour, minute)  # info: set line
    who = persona_for(hour)  # info: set who
    md = [f"# Hourly chime — {t.isoformat()}", "", f"- Voice: {who}", "", line, ""]  # info: set md
    return "\n".join(md), [line]  # info: return "\n" . join ( md ) , [ line ]


# ====================================================
# SECTION: function _temp_clause
# What it does: High and low words from one forecast period. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _temp_clause(body: str) -> str:  # info: def _temp_clause
    bits = []  # info: set bits
    for word, say in (("Highs", "highs"), ("Lows", "lows")):  # info: for word , say
        hit = re.search(rf"\b{word}\s+(.+?)(?:\.|$)", body or "")  # info: set hit
        if hit:  # info: if hit :
            bits.append(f"{say} {_shore(hit.group(1))}")  # info: bits . append
    if bits:  # info: if bits :
        return ", ".join(bits)  # info: return ", " . join ( bits )
    return re.split(r"(?<=\.)\s", body or "")[0].strip().rstrip(".")  # info: return first sentence


# ====================================================
# SECTION: function b_nws_weather
# What it does: Alerts, today's state forecast, shore temperatures, and the later outlook. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_nws_weather(t: datetime):  # info: def b_nws_weather
    rows, upd = alerts()  # info: rows , upd = alerts ( )
    issued, groups = sfp_read()  # info: issued , groups = sfp_read ( )
    places = zfp_temps()  # info: set places
    today = None  # info: set today
    if groups and groups[0]["periods"]:  # info: if groups and groups [ 0 ] [ "periods" ]
        label, body = groups[0]["periods"][0]  # info: label , body = first period
        today = f"{label}: {body}"  # info: set today
    sp = ["NWS Hawaii Report."]  # info: set sp
    md = [f"# NWS Hawaii — {t.isoformat()}", "", f"- Alerts source: `api.weather.gov/alerts/active?area=HI` (updated {upd or 'n/a'})",
          f"- Forecast source: NWS HFO State Forecast (SFP), issued {issued or 'n/a'}",
          "- Temperatures: NWS HFO Zone Forecast (ZFP), today high and tonight low", "", "## Active alerts", ""]
    if rows:  # info: if rows :
        sp.append(f"{len(rows)} active alert{'s' if len(rows) != 1 else ''} for Hawaii.")  # info: sp . append ( f" { len (
        for r in rows[:3]:  # info: for r in rows [ : 3 ]
            sp.append(f"{r['event']} for {r['area']}.")  # info: sp . append ( f" { r [
        md += [f"- **{r['event']}** — {r['area']} (expires {r['expires']})" for r in rows]  # info: set md
    else:  # info: else :
        sp.append("No active HI alerts from the API sample.")  # info: sp . append ( "No active HI alerts from the API sample." )
        md.append("- none")  # info: md . append ( "- none" )
    md += ["", "## State forecast (first period)", "", today or "_not on file_", ""]
    if today:  # info: if today :
        sp.append(f"State forecast for {today.split(':', 1)[0].lower()}.")  # info: sp . append ( f" State forecast for { today
        sp.append(today.split(":", 1)[1].strip().rstrip(".") + ".")  # info: sp . append ( today . split (
    md += ["## Temperatures", "", "Shore number when the zone also lists an elevation.", ""]  # info: md += temperatures heading
    if places:  # info: if places :
        spoken_places = []  # info: set spoken_places
        for p in places:  # info: for p in places
            bits = []  # info: set bits
            if p["high"]:  # info: if p [ "high" ]
                bits.append(f"high {p['high']}")  # info: bits . append
            if p["low"]:  # info: if p [ "low" ]
                bits.append(f"low {p['low']}")  # info: bits . append
            md.append(f"- **{p['place']}** — " + ", ".join(bits))  # info: md . append
            spoken_places.append(f"{p['place']} " + ", ".join(bits))  # info: spoken_places . append
        sp.append("Temperatures. " + ". ".join(spoken_places) + ".")  # info: sp . append
    else:  # info: else :
        md.append("- _not on file_")  # info: md . append ( "- _not on file_" )
        sp.append("Temperatures are not on file.")  # info: sp . append
    md += ["## Outlook", ""]  # info: md += outlook heading
    wrote = False  # info: set wrote
    outlook_bits = []  # info: set outlook_bits
    for g in groups:  # info: for g in groups
        later = g["periods"][1:]  # info: set later
        if not later:  # info: if not later
            continue  # info: continue
        if wrote:  # info: if wrote
            md.append("")  # info: md . append ( "" )
        wrote = True  # info: set wrote
        md += [f"**{g['name']}**", ""]  # info: md += group heading
        for label, body in later:  # info: for label , body in later
            md.append(f"- {label}: {body}")  # info: md . append
        if not outlook_bits:  # info: if not outlook_bits
            for label, body in later[:2]:  # info: for label , body in later [ : 2 ]
                outlook_bits.append(f"{label}, {_temp_clause(body)}")  # info: outlook_bits . append
    if wrote:  # info: if wrote
        sp.append("Outlook. " + ". ".join(outlook_bits) + ".")  # info: sp . append
    else:  # info: else
        md.append("- _not on file_")  # info: md . append ( "- _not on file_" )
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function newest_ch1
# What it does: Newest ch1 camera still and its age in minutes. Does not describe the picture.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def newest_ch1(t: datetime) -> dict | None:  # info: def newest_ch1
    frames = DB / "Media" / "Images"  # info: set frames
    files = [p for p in frames.glob("ch1-*.jpg") if p.is_file()] if frames.is_dir() else []  # info: set files
    if not files:  # info: if not files :
        return None  # info: return None
    latest = max(files, key=lambda p: p.stat().st_mtime)  # info: set latest
    age = max(0, int((t.timestamp() - latest.stat().st_mtime) // 60))  # info: set age
    return {"path": str(latest), "age_min": age}  # info: return { "path" : str ( latest ) , "age_min" : age }


# ====================================================
# SECTION: function camera_observation
# What it does: This hour's channel-1 weather and panel-tilt sentence. Looks only when the hour has no reading.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def camera_observation(t: datetime) -> str:  # info: def camera_observation
    cam = PACIFIC / "Security" / "Cameras"  # info: set cam
    if str(cam) not in sys.path:  # info: if str ( cam ) not in sys . path :
        sys.path.insert(0, str(cam))  # info: sys . path . insert ( 0 , str ( cam ) )
    try:  # info: try :
        import panel_look  # info: import panel_look
        row = panel_look.observe(t)  # info: set row
    except Exception:  # info: except Exception :
        return ""  # info: return ""
    return str((row or {}).get("sentence") or "")  # info: return str ( ( row or { } ) . get ( "sentence" ) or "" )


# ====================================================
# SECTION: function last_camera_look
# What it does: Last stored channel-1 sentence and its age. Does not call the vision model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def last_camera_look(t: datetime) -> dict:  # info: def last_camera_look
    """Last stored channel-1 sentence and its age. Does not call the vision model."""  # info: """Last stored channel-1 sentence and its age. Does not call the vision model."""
    cam = PACIFIC / "Security" / "Cameras"  # info: set cam
    if str(cam) not in sys.path:  # info: if str ( cam ) not in sys . path :
        sys.path.insert(0, str(cam))  # info: sys . path . insert ( 0 , str ( cam ) )
    try:  # info: try :
        import panel_look  # info: import panel_look
        row = panel_look.load_cache() or {}  # info: set row
    except Exception:  # info: except Exception :
        return {}  # info: return { }
    if not isinstance(row, dict):  # info: if not isinstance ( row , dict ) :
        return {}  # info: return { }
    age = None  # info: set age
    try:  # info: try :
        when = datetime.fromisoformat(str(row.get("at") or ""))  # info: set when
        if when.tzinfo is None and t.tzinfo is not None:  # info: if when . tzinfo is None and t . tzinfo is not None :
            when = when.replace(tzinfo=t.tzinfo)  # info: set when
        age = max(0, int((t - when).total_seconds() // 60))  # info: set age
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        age = None  # info: set age
    return {"sentence": str(row.get("sentence") or ""), "age_min": age,  # info: return { "sentence" : str ( row . get ( "sentence" ) or "" ) , "age_min" : age ,
            "hour": str(row.get("hour") or ""), "at": row.get("at")}  # info: "hour" : str ( row . get ( "hour" ) or "" ) , "at" : row . get ( "at" ) }


# ====================================================
# SECTION: function board_status
# What it does: Read report_board.py status. Morning 09:00, midday 12:00, late 21:00.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def board_status() -> dict | None:  # info: def board_status
    script = PACIFIC / "Reports" / "scripts" / "report_board.py"  # info: set script
    if not script.is_file():  # info: if not script . is_file ( ) :
        return None  # info: return None
    try:  # info: try :
        proc = subprocess.run([sys.executable, str(script), "status"], capture_output=True, text=True, timeout=30)  # info: set proc
    except (OSError, subprocess.TimeoutExpired):  # info: except ( OSError , subprocess . TimeoutExpired ) :
        return None  # info: return None
    if proc.returncode != 0:  # info: if proc . returncode != 0 :
        return None  # info: return None
    try:  # info: try :
        data = json.loads(proc.stdout)  # info: set data
    except ValueError:  # info: except ValueError :
        return None  # info: return None
    return data if isinstance(data, dict) and data.get("ok") else None  # info: return data if isinstance ( data , dict ) and data . get ( "ok" ) else None


# ====================================================
# SECTION: function speak_board
# What it does: Spoken remaining tasks from report-board slots. Does not play audio.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speak_board(t: datetime, payload: dict | None):  # info: def speak_board
    labels = {"morning": "Morning report", "midday": "Midday report", "late": "Late report"}  # info: set labels
    closed = {"done", "missed", "skipped_optional"}  # info: set closed
    rows = []  # info: set rows
    for key, row in ((payload or {}).get("slots") or {}).items():  # info: for key , row in ( ( payload or { } ) . get ( "slots" ) or { } ) . items ( ) :
        if not isinstance(row, dict):  # info: if not isinstance ( row , dict ) :
            continue  # info: continue
        try:  # info: try :
            when = datetime.fromisoformat(str(row.get("scheduled_at")))  # info: set when
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            continue  # info: continue
        if when.tzinfo is None and t.tzinfo is not None:  # info: if when . tzinfo is None and t . tzinfo is not None :
            when = when.replace(tzinfo=t.tzinfo)  # info: set when
        rows.append((when, str(key), str(row.get("status") or "unknown")))  # info: rows . append ( ( when , str ( key ) , str ( row . get ( "status" ) or "unknown" ) ) )
    rows.sort()  # info: rows . sort ( )
    hour = [row for row in rows if t < row[0] <= t + timedelta(hours=1) and row[2] not in closed]  # info: set hour
    stamp = on_the_dot(t, t.hour, 0)  # info: set stamp
    sp = [f"Remaining tasks at {clock(stamp)} Hawaiian Standard Time.".replace("..", "."), DEV_NOTE + "."]  # info: set sp
    if payload is None:  # info: if payload is None :
        sp.append("The report board is not on file.")  # info: sp . append ( "The report board is not on file." )
    else:  # info: else :
        sp.append(f"{len(hour)} item{'s' if len(hour) != 1 else ''} in the next hour.")  # info: sp . append ( f" { len ( hour ) } item { 's' if len ( hour ) != 1 else '' } in the next hour. " )
        for when, key, _status in hour:  # info: for when , key , _status in hour :
            sp.append(f"{clock(when)} {labels.get(key, key)}.")  # info: sp . append ( f" { clock ( when ) } { labels . get ( key , key ) } . " )
        if not hour:  # info: if not hour :
            later = [row for row in rows if row[0] > t and row[2] not in closed]  # info: set later
            if later:  # info: if later :
                sp.append(f"Next is {clock(later[0][0])} {labels.get(later[0][1], later[0][1])}.")  # info: sp . append ( f" Next is { clock ( later [ 0 ] [ 0 ] ) } { labels . get ( later [ 0 ] [ 1 ] , later [ 0 ] [ 1 ] ) } . " )
            else:  # info: else :
                sp.append("No later report slots are open.")  # info: sp . append ( "No later report slots are open." )
    md = [f"# Remaining tasks — {stamp.isoformat()}", "", DEV_NOTE, "", "Source: report_board.py status (morning 09:00, midday 12:00, late 21:00).", ""]  # info: set md
    md += [f"- {labels.get(key, key)} {when.isoformat()} {status}" for when, key, status in rows]  # info: set md
    md += ["", "## Spoken", "", " ".join(sp), ""]  # info: set md
    return "\n".join(md), sp  # info: return "\n" . join ( md ) , sp


# ====================================================
# SECTION: function b_energy_report
# What it does: Pack watts, the newest ch1 still, and one hourly camera observation.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_energy_report(t: datetime):  # info: def b_energy_report
    facts = energy_facts(t)  # info: set facts
    sp = ["Energy desk report."]  # info: set sp
    md = [f"# Energy desk — {t.isoformat()}", "", "| Device | SOC | Solar in | AC out | USB-C out | Reading at | Age |", "|---|---|---|---|---|---|---|"]
    if not any(f["ok"] for f in facts):  # info: if not any ( f [ "ok" ]
        sp.append("EcoFlow is offline.")  # info: sp . append ( "EcoFlow is offline." )
    for f in facts:  # info: for f in facts :
        if not f["ok"]:  # info: if not f [ "ok" ] :
            md.append(f"| {f['name']} | no reading | | | | | |")  # info: md . append ( f" | { f
            continue  # info: continue
        md.append(f"| {f['name']} | {f['soc']}% | {f['solar_w']} W | {f['ac_out_w']} W | {f['usbc_out_w']} W | {f['at']} | {f['age_min']} min |")  # info: md . append ( f" | { f
        s = f"{f['name']} battery {f['soc']}%"  # info: set s
        if f["solar_w"] is not None:  # info: if f [ "solar_w" ] is not None
            s += f", solar input {spoken_watts(f['solar_w'])}"  # info: set s
        out = sum(x for x in (f["ac_out_w"], f["usbc_out_w"]) if isinstance(x, (int, float)))  # info: set out
        if f["ac_out_w"] is not None or f["usbc_out_w"] is not None:  # info: if f [ "ac_out_w" ] is not None
            s += f", output {spoken_watts(out)}"  # info: set s
        sp.append(s + supply_clause(f) + ".")  # info: sp . append ( s + supply_clause ( f ) + "." )
        note = range_clause(f)  # info: set note
        if note:  # info: if note :
            sp.append(note)  # info: sp . append ( note )
    still = newest_ch1(t)  # info: set still
    if still:  # info: if still :
        name = Path(still["path"]).name  # info: set name
        if still["age_min"] > 0:  # info: if still [ "age_min" ] > 0 :
            md.append(f"- Solar panel still age: {still['age_min']} min (`{name}`)")  # info: md . append ( f" - Solar panel still age: { still
            sp.append(f"Solar panel still is {still['age_min']} minutes old.")  # info: sp . append ( f" Solar panel still is { still
        else:  # info: else :
            md.append(f"- Solar panel still: current (`{name}`)")  # info: md . append ( f" - Solar panel still: current ( ` { name } ` ) " )
    else:  # info: else :
        md.append("- Solar panel still: not on file")  # info: md . append ( "- Solar panel still: not on file" )
        sp.append("No solar panel still on file.")  # info: sp . append ( "No solar panel still on file." )
    look = camera_observation(t)  # info: set look
    if look:  # info: if look :
        md.append(f"- {look}")  # info: md . append ( f" - { look } " )
        sp.append(look)  # info: sp . append ( look )
    md += ["", "_Source: Database Energy/soc + Energy/watts (*-last.json, EcoFlow BLE), the newest ch1 camera still, and one hourly Gemma look at that still._", ""]  # info: set md
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


_KM_ABOUT = re.compile(r"^(\d+(?:\.\d+)?)\s+km\b")  # info: set _KM_ABOUT


# ====================================================
# SECTION: function _about_km
# What it does: Insert "about" before a leading USGS kilometer distance so the magnitude and the distance do not run together.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _about_km(place) -> str:  # info: def _about_km
    """Insert "about" before a leading USGS kilometer distance so the magnitude and the distance do not run together."""  # info: """Insert "about" before a leading USGS kilometer distance so the magnitude and the distance do not run together.""
    return _KM_ABOUT.sub(r"about \1 km", str(place or "").strip(), count=1)  # info: return _KM_ABOUT . sub


# ====================================================
# SECTION: function b_earthquake_report
# What it does: G1 earthquake-hourly build_spoken + report lines, fed from Database Geology/ instead of a live USGS call. Places with a kilometer distance say "about" first.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_earthquake_report(t: datetime):  # info: def b_earthquake_report
    """G1 earthquake-hourly build_spoken + report lines, fed from Database Geology/ instead of a live USGS call. Places with a kilometer distance say "about" first."""  # info: """G1 earthquake-hourly build_spoken + report lines, fed from Database Geology/ instead of a live USGS call. Places with a kilometer distance say "about" first.""
    q = quake_facts(t)  # info: set q
    hi, gl = q.get("hawaii"), q.get("global")  # info: hi , gl = q . get (
    md = [f"# Earthquake report — {t.isoformat()}", ""]
    if not hi and not gl:  # info: if not hi and not gl :
        md += ["_No USGS data on file (Database Geology/Earthquakes/*-last.json missing). Run geology_collect.py._", ""]  # info: set md
        return "\n".join(md), ["Earthquake data is not on file."]  # info: return "\n" . join ( md ) ,
    prev = jload(QUAKE_STATE) or {}  # info: set prev
    seen = set(prev.get("seen_ids") or [])  # info: set seen
    hi_ev, gl_ev = list((hi or {}).get("events") or []), list((gl or {}).get("events") or [])  # info: hi_ev , gl_ev = list ( ( hi
    fresh_hi = [e for e in hi_ev if e.get("id") and e["id"] not in seen]  # info: set fresh_hi
    fresh_gl = [e for e in gl_ev if e.get("id") and e["id"] not in seen]  # info: set fresh_gl
    sp = [f"Earthquake report at {clock(t)}.".replace("..", ".")]  # info: set sp
    if hi is None:  # info: if hi is None :
        sp.append("Local earthquake data is not on file.")  # info: sp . append ( "Local earthquake data is not on file." )
    elif fresh_hi:  # info: elif fresh_hi :
        sp.append(f"{len(fresh_hi)} new local earthquake{'s' if len(fresh_hi) != 1 else ''}.")  # info: sp . append ( f" { len (
        sp += [f"Magnitude {e.get('mag')}, {_about_km(e.get('place'))}." for e in fresh_hi[:_MAX_HI]]  # info: set sp
    else:  # info: else :
        sp.append("No new local earthquakes since the last report.")  # info: sp . append ( "No new local earthquakes since the last report." )
    if hi is not None:  # info: if hi is not None :
        sp.append(f"Local last twenty four hours: {len(_m25(hi_ev))} magnitude 2.5 or greater.")  # info: sp . append ( f" Local last twenty four hours: { len
    if gl is None:  # info: if gl is None :
        sp.append("Global earthquake data is not on file.")  # info: sp . append ( "Global earthquake data is not on file." )
    elif fresh_gl:  # info: elif fresh_gl :
        sp.append(f"{len(fresh_gl)} new global earthquake{'s' if len(fresh_gl) != 1 else ''}.")  # info: sp . append ( f" { len (
        sp += [f"Magnitude {e.get('mag')}, {_about_km(e.get('place'))}." for e in fresh_gl[:_MAX_GLOBAL]]  # info: set sp
    else:  # info: else :
        sp.append("No new global earthquakes since the last report.")  # info: sp . append ( "No new global earthquakes since the last report." )
    if gl is not None:  # info: if gl is not None :
        sp.append(f"Global last twenty four hours: {len(_m25(gl_ev))} magnitude 2.5 or greater.")  # info: sp . append ( f" Global last twenty four hours: { len
    for label, d in (("Hawaii", hi), ("global", gl)):  # info: for label , d in ( ( "Hawaii"
        if d and d.get("age_min") is not None and d["age_min"] > QUAKE_STALE_MIN:  # info: if d and d . get ( "age_min"
            sp.append(f"The {'local' if label == 'Hawaii' else label} U.S. Geological Survey data is {d['age_min']} minutes old.")  # info: sp . append ( f" The { 'local' if label == 'Hawaii' else label } U.S. Geological Survey data is { d [ 'age_min' ] } minutes old. " )
    for label, d, fresh in (("Hawaii", hi, fresh_hi), ("Global", gl, fresh_gl)):  # info: for label , d , fresh in (
        md += [f"## {label} Changes Since Last Report"]
        md += [f"- M{e.get('mag')} {_about_km(e.get('place'))} ({e.get('time_hst')})" for e in fresh[:12]] or ["- No new earthquakes."]  # info: set md
        if len(fresh) > 12:  # info: if len ( fresh ) > 12 :
            md.append(f"- ...and {len(fresh) - 12} more new earthquakes.")  # info: md . append ( f" - ...and { len
        ev = list((d or {}).get("events") or [])  # info: set ev
        big = max((float(e["mag"]) for e in _m25(ev)), default=None)  # info: set big
        md += ["", f"## {label} 24-Hour M2.5+ Summary",
               f"- {len(_m25(ev))} earthquakes" + (f"; largest M{big:g}." if big is not None else "."),  # info: f" - { len ( _m25 ( ev
               f"- Source: `{(d or {}).get('source', 'n/a')}` (collected {(d or {}).get('at', 'n/a')})", ""]  # info: f" - Source: ` { ( d or { }
    if not os.environ.get("RR_VOICE_QUAKE_DRY"):  # info: if not os . environ . get (
        ids = [e["id"] for e in hi_ev + gl_ev if e.get("id")]  # info: set ids
        state = {"seen_ids": (list(seen) + [i for i in ids if i not in seen])[-400:], "updated_at": t.isoformat()}  # info: set state
        QUAKE_STATE.parent.mkdir(parents=True, exist_ok=True)  # info: QUAKE_STATE . parent . mkdir ( parents =
        tmp = QUAKE_STATE.with_suffix(".tmp")  # info: set tmp
        tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
        os.replace(tmp, QUAKE_STATE)  # info: os . replace ( tmp , QUAKE_STATE )
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function _gc_nm
# What it does:  gc nm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _gc_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:  # info: def _gc_nm
    import math  # info: import math
    p1, p2 = math.radians(lat1), math.radians(lat2)  # info: p1 , p2 = math . radians (
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2  # info: set a
    return 2 * 3440.065 * math.asin(min(1.0, math.sqrt(a)))  # info: return 2 * 3440.065 * math . asin


# ====================================================
# SECTION: function _bearing
# What it does:  bearing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:  # info: def _bearing
    import math  # G1 hurricane_desk._bearing
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)  # info: p1 , p2 , dl = math .
    y = math.sin(dl) * math.cos(p2)  # info: set y
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)  # info: set x
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0  # info: return ( math . degrees ( math .


# ====================================================
# SECTION: function _compass
# What it does:  compass.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _compass(deg: float) -> str:  # info: def _compass
    return COMPASS[int((deg + 22.5) // 45) % 8]  # info: return COMPASS [ int ( ( deg +


# ====================================================
# SECTION: function _nearest_island
# What it does:  nearest island.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _nearest_island(lat: float, lon: float) -> tuple[str, float]:  # info: def _nearest_island
    return min(((k, _gc_nm(v[0], v[1], lat, lon)) for k, v in HAWAII_POS.items()), key=lambda kv: kv[1])  # info: return min ( ( ( k , _gc_nm


# ====================================================
# SECTION: function hurricane_facts
# What it does: Storms from the G3 weather poller's track.json files (latest position, movement from the last two distinct fixes).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hurricane_facts(t: datetime) -> list[dict]:  # info: def hurricane_facts
    """Storms from the G3 weather poller's track.json files (latest position, movement from the last two distinct fixes)."""  # info: """Storms from the G3 weather poller's track.json files (latest position, movement from the last two distinct 
    out = []  # info: set out
    for tr in sorted(HURRICANES.glob("*/track.json")) if HURRICANES.is_dir() else []:  # info: for tr in sorted ( HURRICANES . glob
        d = jload(tr) or {}  # info: set d
        pos = [p for p in d.get("positions") or [] if p.get("lat") is not None and p.get("lon") is not None]  # info: set pos
        if not pos:  # info: if not pos :
            continue  # info: continue
        last = pos[-1]  # info: set last
        try:  # info: try :
            lat, lon = float(last["lat"]), float(last["lon"])  # info: lat , lon = float ( last [
            age_h = (t - datetime.fromisoformat(last["polled_at_hst"])).total_seconds() / 3600  # info: set age_h
        except (KeyError, TypeError, ValueError):  # info: except ( KeyError , TypeError , ValueError )
            continue  # info: continue
        fixes = []  # first poll time of each distinct position
        for p in pos:  # info: for p in pos :
            key = (float(p["lat"]), float(p["lon"]))  # info: set key
            if not fixes or fixes[-1][0] != key:  # info: if not fixes or fixes [ - 1
                fixes.append((key, p.get("polled_at_hst")))  # info: fixes . append ( ( key , p
        island, nm = _nearest_island(lat, lon)  # info: island , nm = _nearest_island ( lat ,
        move_c = move_kt = approach = None  # info: set move_c
        if len(fixes) >= 2:  # info: if len ( fixes ) >= 2 :
            (a, ta), (b, tb) = fixes[-2], fixes[-1]  # info: call (
            move_c = _compass(_bearing(a[0], a[1], b[0], b[1]))  # info: set move_c
            try:  # info: try :
                hrs = (datetime.fromisoformat(tb) - datetime.fromisoformat(ta)).total_seconds() / 3600  # info: set hrs
                move_kt = round(_gc_nm(a[0], a[1], b[0], b[1]) / hrs) if hrs > 0.5 else None  # info: set move_kt
            except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
                move_kt = None  # info: set move_kt
            prev_nm = _nearest_island(a[0], a[1])[1]  # info: set prev_nm
            approach = "toward" if nm < prev_nm - 5 else "away" if nm > prev_nm + 5 else "steady"  # info: set approach
        try:  # info: try :
            kt = int(round(float(last.get("intensity")))) if last.get("intensity") not in (None, "") else None  # info: set kt
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            kt = None  # info: set kt
        code = str(last.get("classification") or "").upper()  # info: set code
        out.append({"name": str(d.get("storm_name") or tr.parent.name.split("_")[0]).replace("_", " "),  # info: out . append ( { "name" : str
                    "label": STORM_CLASS.get(code, "Tropical system"), "code": code, "lat": lat, "lon": lon,  # info: "label" : STORM_CLASS . get ( code ,
                    "knots": kt, "island": island, "nm": int(round(nm)),  # info: "knots" : kt , "island" : island ,
                    "bearing": _compass(_bearing(HAWAII_POS[island][0], HAWAII_POS[island][1], lat, lon)),  # info: "bearing" : _compass ( _bearing ( HAWAII_POS [
                    "movement_compass": move_c, "movement_kt": move_kt, "approach": approach, "fixes": len(fixes),  # info: "movement_compass" : move_c , "movement_kt" : move_kt ,
                    "polled_at": last.get("polled_at_hst"), "age_h": round(age_h, 1), "active": age_h <= HUR_ACTIVE_H,  # info: "polled_at" : last . get ( "polled_at_hst" )
                    "path": str(tr.relative_to(DB))})  # info: "path" : str ( tr . relative_to (
    return sorted(out, key=lambda s: s["nm"])  # info: return sorted ( out , key = lambda


# ====================================================
# SECTION: function b_hurricane_desk
# What it does: G1 hurricane_desk.hawaii_block + build spoken text, from G3 track.json + NWS HI alerts (never invents storms).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_hurricane_desk(t: datetime):  # info: def b_hurricane_desk
    """G1 hurricane_desk.hawaii_block + build spoken text, from G3 track.json + NWS HI alerts (never invents storms)."""  # info: """G1 hurricane_desk.hawaii_block + build spoken text, from G3 track.json + NWS HI alerts (never invents storm
    storms = hurricane_facts(t)  # info: set storms
    active = [s for s in storms if s["active"]]  # info: set active
    rows, updated = alerts()  # info: rows , updated = alerts ( )
    trop = [r for r in rows if any(k in str(r["event"]).lower() for k in TROPICAL_EVENTS)]  # info: set trop
    sp = ["Hurricane global desk, Pacific Root Server."]  # info: set sp
    if trop:  # info: if trop :
        watch = " NWS Honolulu: " + "; ".join(f"{r['event']} for {r['area'] or 'Hawaii'}" for r in trop) + "."  # info: set watch
    elif updated is None:  # info: elif updated is None :
        watch = " NWS Hawaii alert data is not on file."  # info: set watch
    else:  # info: else :
        watch = " No tropical watches or warnings for Hawaii in the last NWS pull."  # info: set watch
    if not active:  # info: if not active :
        sp.append("Nearest Hurricane from a Hawaiian island. No tropical system with a mapped position is on the board."  # info: sp . append ( "Nearest Hurricane from a Hawaiian island. No tropical system with a mapped position is on the b
                  + watch)  # info: + watch )
    else:  # info: else :
        n = active[0]  # info: set n
        local = bool(trop) or n["nm"] < HAWAII_THREAT_NM  # info: set local
        title = "Nearest Hurricane from a Hawaiian island" if local else "Pacific basin cyclone, not a Hawaii threat"  # info: set title
        ns, ew = ("north" if n["lat"] >= 0 else "south"), ("east" if n["lon"] >= 0 else "west")  # info: ns , ew = ( "north" if n
        move = ""  # info: set move
        if n["movement_kt"] == 0:  # info: if n [ "movement_kt" ] == 0 :
            move = " Nearly stationary."  # info: set move
        elif n["movement_compass"]:  # info: elif n [ "movement_compass" ] :
            vs = {"toward": "toward Hawaii", "away": "away from Hawaii",  # info: set vs
                  "steady": "holding roughly steady relative to Hawaii"}.get(n["approach"] or "", "")  # info: "steady" : "holding roughly steady relative to Hawaii" } . get ( n
            kt_s = f" at about {n['movement_kt']} knots" if n["movement_kt"] else ""  # info: set kt_s
            move = f" Moving {n['movement_compass']}{kt_s}" + (f", {vs}." if vs else ".")  # info: set move
        wind = f" Maximum sustained winds {n['knots']} knots." if n["knots"] else ""  # info: set wind
        hint = ""  # info: set hint
        if not local:  # info: if not local :
            hint = " Do not treat this as a Hawaii local storm."  # info: set hint
            if n["bearing"] == "west":  # info: if n [ "bearing" ] == "west" :
                hint = " West of Kauai is toward Asia and Japan, not toward the islands." + hint  # info: set hint
        sp.append(f"{title}. {n['label']} {n['name']} is about {n['nm']} nautical miles from {n['island']}."  # info: sp . append ( f" { title }
                  f" Center {abs(n['lat']):.1f} {ns}, {abs(n['lon']):.1f} {ew}. It bears {n['bearing']} of {n['island']}."  # info: f" Center { abs ( n [ 'lat'
                  f"{hint}{move}{wind}{watch}")  # info: f" { hint } { move } {
        if len(active) > 1:  # info: if len ( active ) > 1 :
            others = "; ".join(f"{s['label']} {s['name']}, about {s['nm']} nautical miles from {s['island']}" for s in active[1:4])  # info: set others
            sp.append(f"{len(active)} tropical systems are on the Hawaii tracking board. Also tracked: {others}.")  # info: sp . append ( f" { len (
    sp.append("Stay with NWS Honolulu for watches and warnings.")  # info: sp . append ( "Stay with NWS Honolulu for watches and warnings." )
    md = [f"# Hurricane desk — {t.isoformat()}", "", " ".join(sp), "", "## Tracked systems (G3 weather poller)", ""]
    md += ["| Storm | Class | Knots | Position | Nearest island | nm | Bearing | Movement | Last poll (HST) | On board |",  # info: set md
           "|---|---|---|---|---|---|---|---|---|---|"]  # info: "|---|---|---|---|---|---|---|---|---|---|" ]
    md += [f"| {s['name']} | {s['label']} ({s['code'] or '?'}) | {s['knots'] if s['knots'] is not None else 'n/a'} | "  # info: set md
           f"{s['lat']:.1f}, {s['lon']:.1f} | {s['island']} | {s['nm']} | {s['bearing']} | "  # info: f" { s [ 'lat' ] : .1f
           f"{(s['movement_compass'] or 'n/a')} {('~' + str(s['movement_kt']) + ' kt') if s['movement_kt'] else ''} {s['approach'] or ''} | "  # info: call f"
           f"{s['polled_at']} ({s['age_h']} h ago) | {'yes' if s['active'] else 'stale'} |" for s in storms] or ["| none on file | | | | | | | | | |"]  # info: f" { s [ 'polled_at' ] } (
    md += ["", f"NWS HI alerts (updated {updated or 'n/a'}): " + (", ".join(r["event"] for r in rows) or "none") +  # info: set md
           f"; tropical: {len(trop)}.", "",  # info: f" ; tropical: { len ( trop ) }
           "_Sources: Database `Weather/Hawai'i/hurricanes/tracking/*/track.json` (NHC CurrentStorms, Hawaiʻi-relevant "  # info: "_Sources: Database `Weather/Hawai'i/hurricanes/tracking/*/track.json` (NHC CurrentStorms, Hawaiʻi-relevant "
           "storms only: 800 nm or CPHC) and the NWS HI alerts file. Movement is estimated from the last two distinct "  # info: "storms only: 800 nm or CPHC) and the NWS HI alerts file. Movement is estimated from the last two distinct "
           "tracked fixes. G1's global JTWC/RAMMB board is not collected in G3, so there is no global count._", ""]  # info: "tracked fixes. G1's global JTWC/RAMMB board is not collected in G3, so there is no global count._" , "" ]
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function _first_sentences
# What it does:  first sentences.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _first_sentences(text: str, n: int = 2, cap: int = 420) -> str:  # info: def _first_sentences
    parts = re.split(r"(?<=[.!?])\s+", " ".join((text or "").split()))  # info: set parts
    return " ".join(parts[:n])[:cap].strip()  # info: return " " . join ( parts [ :


# ====================================================
# SECTION: function b_kilauea_report
# What it does: G1 hourly Kīlauea desk (persona._kilauea_line wording) + HVO notice excerpt, from Database Geology/Volcanoes/.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_kilauea_report(t: datetime):  # info: def b_kilauea_report
    """G1 hourly Kīlauea desk (persona._kilauea_line wording) + HVO notice excerpt, from Database Geology/Volcanoes/."""  # info: """G1 hourly Kīlauea desk (persona._kilauea_line wording) + HVO notice excerpt, from Database Geology/Volcanoe
    k, ml = jload(VOLCANOES / "kilauea-last.json"), jload(VOLCANOES / "mauna-loa-last.json")  # info: k , ml = jload ( VOLCANOES /
    hi = jload(QUAKES / "hawaii-last.json") or {}  # info: set hi
    md = [f"# Kilauea report — {t.isoformat()}", ""]
    if not isinstance(k, dict) or not k.get("alert_level"):  # info: if not isinstance ( k , dict )
        md += ["_No HVO data on file (Database Geology/Volcanoes/kilauea-last.json missing). Run geology_collect.py._", ""]  # info: set md
        return "\n".join(md), ["Kilauea: DOWN."]  # info: return "\n" . join ( md ) ,
    level = str(k.get("alert_level") or "unknown").strip().lower()  # info: set level
    erupting = k.get("erupting")  # info: set erupting
    if erupting:  # info: if erupting :
        state = "is erupting"  # info: set state
    elif level in {"advisory", "watch", "warning", "normal"} and erupting is False:  # info: elif level in { "advisory" , "watch" ,
        state = "is not erupting"  # info: set state
    else:  # info: else :
        state = "eruption state unknown"  # info: set state
    color = str(k.get("color_code") or "").lower()  # info: set color
    sp = [f"Kilauea report at {clock(t)}.".replace("..", "."),  # info: set sp
          f"Alert level {level}" + (f", aviation color code {color}." if color else "."),  # info: f" Alert level { level } " + (
          f"The volcano {state}."]  # info: f" The volcano { state } . " ]
    note = k.get("latest_activity_notice") if erupting and k.get("latest_activity_notice") else k.get("latest_notice")  # info: set note
    note = note if isinstance(note, dict) else {}  # info: set note
    excerpt = _first_sentences(note.get("synopsis") or "")  # info: set excerpt
    if excerpt:  # info: if excerpt :
        sp += ["Here is the latest observatory notice.", excerpt]  # info: set sp
    else:  # info: else :
        sp.append("No HVO headline in this sample.")  # info: sp . append ( "No HVO headline in this sample." )
    if hi.get("kilauea_150km_count") is not None:  # info: if hi . get ( "kilauea_150km_count" ) is
        n = int(hi["kilauea_150km_count"])  # info: set n
        sp.append(f"U.S. Geological Survey: {n} earthquake{'s' if n != 1 else ''} magnitude 1 or greater within 150 kilometers in the last "  # info: sp . append ( f" U.S. Geological Survey: { n } earthquake
                  f"{hi.get('window_h', 24)} hours.")  # info: f" { hi . get ( 'window_h' ,
    if isinstance(ml, dict) and ml.get("alert_level"):  # info: if isinstance ( ml , dict ) and
        sp.append(f"Mauna Loa alert level: {str(ml['alert_level']).lower()}.")  # info: sp . append ( f" Mauna Loa alert level: { str
    try:  # info: try :
        age = int((t - datetime.fromisoformat(k["at"])).total_seconds() // 60)  # info: set age
    except (KeyError, TypeError, ValueError):  # info: except ( KeyError , TypeError , ValueError )
        age = None  # info: set age
    if age is not None and age > HVO_STALE_MIN:  # info: if age is not None and age >
        sp.append(f"That HVO status is {age} minutes old.")  # info: sp . append ( f" That HVO status is { age
    md += [f"- **Kīlauea:** {k.get('alert_level')} / {k.get('color_code')} — erupting `{erupting}` — {k.get('headline')}",  # info: set md
           f"- **Latest notice used:** {note.get('type', 'n/a')} ({note.get('sent_utc', 'n/a')} UTC) {note.get('url', '')}",  # info: f" - **Latest notice used:** { note . get ( 'type'
           f"- **Mauna Loa:** {(ml or {}).get('alert_level', 'n/a')} / {(ml or {}).get('color_code', 'n/a')}",  # info: f" - **Mauna Loa:** { ( ml or { }
           f"- **Quakes ≤150 km of Kīlauea (M≥1, {hi.get('window_h', 24)} h):** {hi.get('kilauea_150km_count', 'n/a')}",  # info: f" - **Quakes ≤150 km of Kīlauea (M≥1, { hi . get ( 'window_h'
           f"- **Collected:** {k.get('at')} (USGS HANS)", "", "## Spoken", "", " ".join(sp), ""]
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function _host_desks
# What it does:  host desks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _host_desks():  # info: def _host_desks
    sys.path.insert(0, str(PACIFIC / "System" / "scripts"))  # info: sys . path . insert ( 0 ,
    import host_desks  # noqa: E402  (Pacific System/scripts/host_desks.py, G1 host_metrics port)
    return host_desks  # info: return host_desks


# ====================================================
# SECTION: function spoken_watts
# What it does: Spoken power: whole watts; 0 (or 0.0 from the cloud read) -> "zero watts" (2026-09-29 text fix).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def spoken_watts(v) -> str:  # info: def spoken_watts
    """Spoken power: whole watts; 0 (or 0.0 from the cloud read) -> "zero watts" (2026-09-29 text fix)."""  # info: """Spoken power: whole watts; 0 (or 0.0 from the cloud read) -> "zero watts" (2026-09-29 text fix)."""
    w = int(round(float(v)))  # info: set w
    return "zero watts" if w == 0 else ("one watt" if w == 1 else f"{w} watts")  # info: return "zero watts" if w == 0 else (


# ====================================================
# SECTION: function spoken_hhmm
# What it does: "06:11" -> "six eleven a.m." (sun times spoken as words; 2026-09-29 text fix). Non-HH:MM passes through.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def spoken_hhmm(hhmm) -> str:  # info: def spoken_hhmm
    """"06:11" -> "six eleven a.m." (sun times spoken as words; 2026-09-29 text fix). Non-HH:MM passes through."""  # info: """"06:11" -> "six eleven a.m." (sun times spoken as words; 2026-09-29 text fix). Non-HH:MM passes through."""
    try:  # info: try :
        h, m = (int(x) for x in str(hhmm).split(":")[:2])  # info: h , m = ( int ( x
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return str(hhmm)  # info: return str ( hhmm )
    return spoken_clock(h, m)  # info: return spoken_clock ( h , m )


# ====================================================
# SECTION: function b_solar_desk
# What it does: Hourly packs, sun times, the newest channel-1 still, and the last stored camera look.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_solar_desk(t: datetime):  # info: def b_solar_desk
    """Hourly packs, sun times, the newest channel-1 still, and the last stored camera look."""  # info: """Hourly packs, sun times, the newest channel-1 still, and the last stored camera look."""
    facts = energy_facts(t)  # info: set facts
    sun = jload(ENERGY / "sun" / "sun-times-last.json") or {}  # info: set sun
    sp = [f"Solar desk at {clock(t)} Hawaiian Standard Time.".replace("..", ".")]  # info: set sp
    lines, spoken_lines = [], []  # info: lines , spoken_lines = [ ] , [
    for f in facts:  # info: for f in facts :
        if not f["ok"]:  # info: if not f [ "ok" ] :
            lines.append(f"{f['name']}: offline")  # info: lines . append ( f" { f [
            spoken_lines.append(f"{f['name']}: offline")  # info: spoken_lines . append ( f" { f [
            continue  # info: continue
        bits, sbits = [f"state of charge {f['soc']}%"], [f"state of charge {f['soc']}%"]  # info: bits , sbits = [ f" state of charge {
        power = [(k, f.get(k)) for k in ("solar_w", "ac_out_w", "usbc_out_w") if f.get(k) is not None]  # info: set power
        labels = {"solar_w": "solar input", "ac_out_w": "AC out", "usbc_out_w": "USB-C out"}  # info: set labels
        for k, v in power:  # info: for k , v in power :
            bits.append(f"{labels[k]} {v} W")  # info: bits . append ( f" { labels [ k ] } { v } W " )
        clause = supply_clause(f).lstrip(", ")  # info: set clause
        nonzero = [(k, v) for k, v in power if int(round(float(v))) != 0]  # info: set nonzero
        if clause:  # info: if clause :
            bits.append(clause)  # info: bits . append ( clause )
            sbits.append(clause)  # info: sbits . append ( clause )
        if nonzero:  # info: if nonzero :
            sbits += [f"{labels[k]} {spoken_watts(v)}" for k, v in nonzero]  # info: set sbits
        elif not clause:  # info: elif not clause :
            sbits.append("idle")  # no solar in, no AC out, no USB-C out, not on generator or transfer
        lines.append(f"{f['name']}: " + ", ".join(bits))  # info: lines . append ( f" { f [
        spoken_lines.append(f"{f['name']}: " + ", ".join(sbits))  # info: spoken_lines . append ( f" { f [
    if not any(f["ok"] for f in facts):  # info: if not any ( f [ "ok" ]
        sp.append("EcoFlow is offline.")  # info: sp . append ( "EcoFlow is offline." )
    else:  # info: else :
        sp += [x + "." for x in spoken_lines]  # info: set sp
        for f in facts:  # info: for f in facts :
            note = range_clause(f)  # info: set note
            if note:  # info: if note :
                sp.append(note)  # info: sp . append ( note )
    if sun.get("date") == t.date().isoformat() and sun.get("sunset"):  # info: if sun . get ( "date" ) ==
        if t.strftime("%H:%M") < sun["sunset"]:  # info: if t . strftime ( "%H:%M" ) <
            sp.append(f"Sunrise was {spoken_hhmm(sun['sunrise'])}, sunset is {spoken_hhmm(sun['sunset'])}.".replace("..", "."))  # info: sp . append ( f" Sunrise was { spoken_hhmm
        elif sun.get("next_sunrise"):  # info: elif sun . get ( "next_sunrise" ) :
            sp.append(f"Sunset was {spoken_hhmm(sun['sunset'])}; next sunrise {spoken_hhmm(sun['next_sunrise'])}.".replace("..", "."))  # info: sp . append ( f" Sunset was { spoken_hhmm
        else:  # info: else :
            sp.append(f"Sunset was {spoken_hhmm(sun['sunset'])}.".replace("..", "."))  # info: sp . append ( f" Sunset was { spoken_hhmm
    elif sun.get("date"):  # info: elif sun . get ( "date" ) :
        sp.append("Sun times on file are not for today.")  # info: sp . append ( "Sun times on file are not for today." )
    extra = []  # info: set extra
    still = newest_ch1(t)  # info: set still
    if still:  # info: if still :
        name = Path(still["path"]).name  # info: set name
        if still["age_min"] > 0:  # info: if still [ "age_min" ] > 0 :
            extra.append(f"- Solar panel still age: {still['age_min']} min (`{name}`)")  # info: extra . append ( f" - Solar panel still age:
            unit = "minute" if still["age_min"] == 1 else "minutes"  # info: set unit
            sp.append(f"Solar panel still is {still['age_min']} {unit} old.")  # info: sp . append ( f" Solar panel still is { still
        else:  # info: else :
            extra.append(f"- Solar panel still: current (`{name}`)")  # info: extra . append ( f" - Solar panel still: current ( ` { name } ` ) " )
    else:  # info: else :
        extra.append("- Solar panel still: not on file")  # info: extra . append ( "- Solar panel still: not on file" )
        sp.append("No solar panel still on file.")  # info: sp . append ( "No solar panel still on file." )
    look = last_camera_look(t)  # info: set look
    if look.get("sentence"):  # info: if look . get ( "sentence" ) :
        extra.append(f"- {look['sentence']}")  # info: extra . append ( f" - { look [ 'sentence' ] } " )
        sp.append(look["sentence"])  # info: sp . append ( look [ "sentence" ] )
        if look.get("hour") != t.strftime("%Y-%m-%dT%H") and look.get("age_min") is not None:  # info: if look . get ( "hour" ) != t . strftime
            extra.append(f"- Camera look age: {look['age_min']} min ({look.get('at')})")  # info: extra . append ( f" - Camera look age: { look
            unit = "minute" if look["age_min"] == 1 else "minutes"  # info: set unit
            sp.append(f"That camera look is {look['age_min']} {unit} old.")  # info: sp . append ( f" That camera look is { look
    else:  # info: else :
        extra.append("- Camera look: not on file")  # info: extra . append ( "- Camera look: not on file" )
        sp.append("No solar panel camera look on file.")  # info: sp . append ( "No solar panel camera look on file." )
    md = [f"# Solar desk — {t.isoformat()}", ""] + [f"- {x}" for x in lines] + [
        f"- Sun: {sun.get('sunrise', 'n/a')} / {sun.get('sunset', 'n/a')} ({sun.get('date', 'n/a')}, Open-Meteo)",  # info: f" - Sun: { sun . get ( 'sunrise'
    ] + extra + ["", "## Spoken", "", " ".join(sp), "",  # info: ] + extra + [ "" , "## Spoken" , "" , " " . join ( sp ) , "" ,
        "_Source: Database Energy/soc + Energy/watts (EcoFlow BLE), Energy/sun/sun-times-last.json, the newest ch1 still, and Energy/vision/ch1-look-last.json._", ""]  # info: "_Source: Database Energy/soc + Energy/watts (EcoFlow BLE), Energy/sun/sun-times-last.json, the newest ch1 still, and Energy/vision/ch1-look-last.json._" , "" ]
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function b_security_desk
# What it does: G1 host_metrics.security_spoken, unchanged wording, from host_desks.security_snapshot() (counts only).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_security_desk(t: datetime):  # info: def b_security_desk
    """G1 host_metrics.security_spoken, unchanged wording, from host_desks.security_snapshot() (counts only)."""  # info: """G1 host_metrics.security_spoken, unchanged wording, from host_desks.security_snapshot() (counts only)."""
    row = _host_desks().security_snapshot()  # info: set row
    bits = [f"Security desk at {clock(t)}.".replace("..", ".")]  # info: set bits
    ufw = row.get("ufw_boot")  # info: set ufw
    if ufw is True:  # info: if ufw is True :
        bits.append("The firewall is set to start on boot.")  # info: bits . append ( "The firewall is set to start on boot." )
    elif ufw is False:  # info: elif ufw is False :
        bits.append("The firewall is not set to start on boot.")  # info: bits . append ( "The firewall is not set to start on boot." )
    ssh = row.get("ssh_active")  # info: set ssh
    if ssh is True:  # info: if ssh is True :
        bits.append("OpenSSH service is active.")  # info: bits . append ( "OpenSSH service is active." )
    elif ssh is False:  # info: elif ssh is False :
        bits.append("OpenSSH service is not active.")  # info: bits . append ( "OpenSSH service is not active." )
    if row.get("listen_tcp") is not None:  # info: if row . get ( "listen_tcp" ) is
        bits.append(f"{row['listen_tcp']} TCP listeners.")  # info: bits . append ( f" { row [
    if row.get("established") is not None:  # info: if row . get ( "established" ) is
        bits.append(f"{row['established']} established connections.")  # info: bits . append ( f" { row [
    if row.get("failed_1h") is not None:  # info: if row . get ( "failed_1h" ) is
        bits.append(f"Failed sign-ins: {row['failed_1h']} in the last hour, {row['failed_24h']} in the last twenty four hours.")  # info: bits . append ( f" Failed sign-ins: { row
    else:  # info: else :
        bits.append("The sign-in log is not readable.")  # info: bits . append ( "The sign-in log is not readable." )
    if row.get("fail2ban"):  # info: if row . get ( "fail2ban" ) :
        bits.append("Fail2ban is running.")  # info: bits . append ( "Fail2ban is running." )
    md = [f"# Security desk — {t.isoformat()}", "",
          f"- Firewall starts on boot: {row.get('ufw_boot')}",  # info: f" - Firewall starts on boot: { row . get ( 'ufw_boot' ) } " ,
          f"- SSH active: {row.get('ssh_active')}",  # info: f" - SSH active: { row . get ( 'ssh_active' ) } " ,
          f"- TCP listeners: {row.get('listen_tcp')}",  # info: f" - TCP listeners: { row . get ( 'listen_tcp' ) } " ,
          f"- Established connections: {row.get('established')}",  # info: f" - Established connections: { row . get ( 'established' ) } " ,
          f"- Failed sign-ins, last hour: {row.get('failed_1h')}",  # info: f" - Failed sign-ins, last hour: { row . get ( 'failed_1h' ) } " ,
          f"- Failed sign-ins, last 24 hours: {row.get('failed_24h')}",  # info: f" - Failed sign-ins, last 24 hours: { row . get ( 'failed_24h' ) } " ,
          "", "## Spoken", "", " ".join(bits), "",
          "_Source: Pacific System/scripts/host_desks.py (ufw.conf, systemctl is-active, /proc/net/tcp, auth.log counts only)._", ""]  # info: "_Source: Pacific System/scripts/host_desks.py (ufw.conf, systemctl is-active, /proc/net/tcp, auth.log counts 
    return "\n".join(md), bits  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function b_bandwidth_desk
# What it does: G1 host_metrics.bandwidth_spoken (records one sample, then last hour / 24 h deltas).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_bandwidth_desk(t: datetime):  # info: def b_bandwidth_desk
    """G1 host_metrics.bandwidth_spoken (records one sample, then last hour / 24 h deltas)."""  # info: """G1 host_metrics.bandwidth_spoken (records one sample, then last hour / 24 h deltas)."""
    hd = _host_desks()  # info: set hd
    net = hd.net_counters()  # info: set net
    if net and not os.environ.get("RR_VOICE_BANDWIDTH_DRY"):  # info: if net and not os . environ .
        hd.append_net_sample(net)  # info: hd . append_net_sample ( net )
    hour, day = hd.net_usage_window(3600, now=net), hd.net_usage_window(86400, now=net)  # info: hour , day = hd . net_usage_window (
    md = [f"# Bandwidth desk — {t.isoformat()}", "", f"- iface: {(net or {}).get('iface')} ({(net or {}).get('link')})",
          f"- last hour: {hour}", f"- last 24 h: {day}", ""]  # info: f" - last hour: { hour } " , f"
    if hour is None and day is None:  # info: if hour is None and day is None
        md += ["_Not enough samples yet (needs samples covering 45 min; run `host_desks.py net-sample` every 5 min)._", ""]  # info: set md
        return "\n".join(md), ["Bandwidth data is not on file yet."]  # info: return "\n" . join ( md ) ,
    sb = hd.spoken_bytes  # info: set sb
    bits = [f"Bandwidth desk at {clock(t)}.".replace("..", "."), f"This host is on {(net or {}).get('link') or 'network'}."]  # info: set bits
    bits.append(f"Last hour: {sb(hour['rx'])} down, {sb(hour['tx'])} up, {sb(hour['total'])} total." if hour else "Last hour is not on file yet.")  # info: bits . append ( f" Last hour: { sb
    bits.append(f"Last twenty four hours: {sb(day['rx'])} down, {sb(day['tx'])} up, {sb(day['total'])} total." if day  # info: bits . append ( f" Last twenty four hours: { sb
                else "Last twenty four hours is not on file yet.")  # info: else "Last twenty four hours is not on file yet." )
    md += ["## Spoken", "", " ".join(bits), ""]
    return "\n".join(md), bits  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function _say_code
# What it does: WO-ECO -> 'E C O', WO-RPT-001 -> 'R P T 1' (short acronyms spelled out for Kokoro).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _say_code(code: str) -> str:  # info: def _say_code
    """WO-ECO -> 'E C O', WO-RPT-001 -> 'R P T 1' (short acronyms spelled out for Kokoro)."""  # info: """WO-ECO -> 'E C O', WO-RPT-001 -> 'R P T 1' (short acronyms spelled out for Kokoro)."""
    parts = []  # info: set parts
    for p in code.removeprefix("WO-").split("-"):  # info: for p in code . removeprefix ( "WO-"
        parts.append(" ".join(p) if p.isalpha() and len(p) <= 4 else str(int(p)) if p.isdigit() else p.title())  # info: parts . append ( " " . join (
    return " ".join(parts)  # info: return " " . join ( parts )


# ====================================================
# SECTION: function b_remaining_tasks
# What it does: b remaining tasks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_remaining_tasks(t: datetime):  # info: def b_remaining_tasks
    payload = board_status()  # info: set payload
    return speak_board(t, payload)  # info: return speak_board ( t , payload )


# ====================================================
# SECTION: function _rollup
# What it does:  rollup.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _rollup(t: datetime, slot: str):  # info: def _rollup
    title = {"morning": "Morning report.", "midday": "Midday report.", "late": "Late report."}[slot]  # info: set title
    when = on_the_dot(t, *ROLLUP_AT[slot])  # info: set when
    facts, (rows, _), (today, _), h, (tasks, per) = energy_facts(t), alerts(), sfp_today(), host(), open_tasks()  # info: call facts
    sp = [title, f"It's {clock(when)} Hawaiian Standard Time.".replace("..", "."), DEV_NOTE + "."]  # info: set sp
    lines = []  # info: set lines
    ok = [f for f in facts if f["ok"]]  # info: set ok
    if ok:  # info: if ok :
        s = "Batteries: " + ", ".join(f"{f['name']} {f['soc']}%" for f in ok)  # info: set s
        solar = sum(f["solar_w"] or 0 for f in ok)  # info: set solar
        # spoken form says "at": "Delta 2 36%" would hit the G1 clock rule ("two thirty six a.m.")
        sp.append("Battery levels: " + ", ".join(f"{f['name']} at {f['soc']}%" for f in ok) + f". Solar input {spoken_watts(solar)}.")  # info: sp . append ( "Battery levels: " + ", " .
        lines.append(s + f"; solar input {solar} W")  # info: lines . append ( s + f" ; solar input
    else:  # info: else :
        sp.append("EcoFlow is offline.")  # info: sp . append ( "EcoFlow is offline." )
        lines.append("EcoFlow: no reading")  # info: lines . append ( "EcoFlow: no reading" )
    if rows:  # info: if rows :
        sp.append(f"{len(rows)} active weather alert{'s' if len(rows) != 1 else ''}, including {rows[0]['event']}.")  # info: sp . append ( f" { len (
    else:  # info: else :
        sp.append("No active HI alerts from the API sample.")  # info: sp . append ( "No active HI alerts from the API sample." )
    lines.append(f"NWS alerts active: {len(rows)}" + (f" ({', '.join(r['event'] for r in rows)})" if rows else ""))  # info: lines . append ( f" NWS alerts active: { len
    if today:  # info: if today :
        first = re.split(r"(?<=\.)\s", today.split(":", 1)[1].strip())[0]  # info: set first
        sp.append(f"Forecast for {today.split(':', 1)[0].lower()}: {first}")  # info: sp . append ( f" Forecast for { today
        lines.append(f"Forecast {today}")  # info: lines . append ( f" Forecast { today
    sp.append(f"Host CPU {h['cpu']}%, memory {h['mem']}% used.")  # info: sp . append ( f" Host CPU { h
    lines.append(f"Host CPU {h['cpu']}%, memory {h['mem']}% used")  # info: lines . append ( f" Host CPU { h
    sp.append(f"{tasks} open work order items.")  # info: sp . append ( f" { tasks }
    lines.append(f"Open work-order items: {tasks}")  # info: lines . append ( f" Open work-order items: { tasks
    summary = llm_summary(lines) if os.environ.get("RR_VOICE_ROLLUP_LLM", "0") == "1" else None  # info: set summary
    if summary:  # info: if summary :
        sp.append(summary)  # info: sp . append ( summary )
    sp.append("End of report.")  # info: sp . append ( "End of report." )
    md = [f"# {title[:-1]} — {when.isoformat()}", "", DEV_NOTE, "", "## Measured", ""] + [f"- {x}" for x in lines]
    if summary:  # info: if summary
        md += ["", "## LLM summary", "", summary, ""]  # info: md += the summary only
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function llm_summary
# What it does: Optional, gated: 1–2 sentence summary via run-infer.sh (FLM on demand, single-flight). Metadata-only logging.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def llm_summary(lines: list[str]) -> str | None:  # info: def llm_summary
    """Optional, gated: 1–2 sentence summary via run-infer.sh (FLM on demand, single-flight). Metadata-only logging."""  # info: """Optional, gated: 1–2 sentence summary via run-infer.sh (FLM on demand, single-flight). Metadata-only loggin
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:  # info: with tempfile . NamedTemporaryFile ( "w" , suffix
        f.write("\n".join(lines) + "\n")  # info: f . write ( "\n" . join (
    try:  # info: try :
        env = dict(os.environ, DESK_LIVE_FILE=f.name, RR_CALLER="voice_rollup")  # info: set env
        p = subprocess.run(["bash", str(PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"), "ava",  # info: set p
                            "Summarize the measured desk lines in one or two short spoken sentences. Use only those numbers."],  # info: "Summarize the measured desk lines in one or two short spoken sentences. Use only those numbers." ] ,
                           capture_output=True, text=True, timeout=180, env=env)  # info: set capture_output
        out = " ".join(ln for ln in (p.stdout or "").splitlines() if not ln.startswith("[ok]")).strip()  # info: set out
        return out[:400] if p.returncode == 0 and out and out != "No live desk data attached." else None  # info: return out [ : 400 ] if p
    except (OSError, subprocess.TimeoutExpired):  # info: except ( OSError , subprocess . TimeoutExpired )
        return None  # info: return None
    finally:  # info: finally :
        os.unlink(f.name)  # info: os . unlink ( f . name )


OFFICIAL = WX / "official"  # Pacific Weather/scripts/official_statement.py (HLS)
HFO_TEXT = WX / "hfo" / "api.weather.gov" / "products" / "types"  # weather poller: <TYPE>/locations/HFO/HFO_current.txt
OFFICIAL_MAX_H = 24  # a statement older than this is not read as current (G1 read the newest product regardless)
_WMO_HEAD = re.compile(r"^\s*0{3}\s+[A-Z]{4}\d{2}\s+[A-Z]{4}\s+\d{6}\s+[A-Z]{6}\s+")  # info: set _WMO_HEAD
_UGC = re.compile(r"\b(?:[A-Z]{2}[ZC][0-9>\-]{3,}-)+\d{6}-\s*")  # info: set _UGC


# ====================================================
# SECTION: function _speech_product
# What it does: Flattened NWS product -> speakable: drop the WMO / AWIPS header and UGC zone strings, ** markers, dashes runs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _speech_product(text: str) -> str:  # info: def _speech_product
    """Flattened NWS product -> speakable: drop the WMO / AWIPS header and UGC zone strings, ** markers, dashes runs."""  # info: """Flattened NWS product -> speakable: drop the WMO / AWIPS header and UGC zone strings, ** markers, dashes ru
    t = _UGC.sub("", _WMO_HEAD.sub("", " ".join((text or "").split())))  # info: set t
    t = re.sub(r"\*\*|-{3,}|\s\*\s", " ", t)  # info: set t
    return " ".join(t.split())  # info: return " " . join ( t . split


# ====================================================
# SECTION: function official_products
# What it does: [{type, text, issued, age_h}] newest-first candidates: HLS (official/), HWO, AFD (poller).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def official_products(t: datetime) -> list[dict]:  # info: def official_products
    """[{type, text, issued, age_h}] newest-first candidates: HLS (official/), HWO, AFD (poller)."""  # info: """[{type, text, issued, age_h}] newest-first candidates: HLS (official/), HWO, AFD (poller)."""
    out = []  # info: set out
    st = jload(OFFICIAL / "official-last.json") or {}  # info: set st
    hls = OFFICIAL / "HLS_current.txt"  # info: set hls
    issued = ((st.get("hls") or {}).get("issued")) if isinstance(st, dict) else None  # info: set issued
    if hls.is_file():  # info: if hls . is_file ( ) :
        try:  # info: try :
            age = (t - datetime.fromisoformat(str(issued).replace("Z", "+00:00"))).total_seconds() / 3600 if issued else None  # info: set age
        except ValueError:  # info: except ValueError :
            age = None  # info: set age
        out.append({"type": "HLS", "text": hls.read_text(encoding="utf-8", errors="replace"), "issued": issued,  # info: out . append ( { "type" : "HLS"
                    "age_h": round(age, 1) if age is not None else None})  # info: "age_h" : round ( age , 1 )
    for typ in ("HWO", "AFD"):  # info: for typ in ( "HWO" , "AFD" )
        f = HFO_TEXT / typ / "locations" / "HFO" / "HFO_current.txt"  # info: set f
        if f.is_file():  # info: if f . is_file ( ) :
            age = (t.timestamp() - f.stat().st_mtime) / 3600  # poller rewrites on change; mtime ~ last fetch
            out.append({"type": typ, "text": f.read_text(encoding="utf-8", errors="replace"),  # info: out . append ( { "type" : typ
                        "issued": datetime.fromtimestamp(f.stat().st_mtime).astimezone().isoformat(timespec="minutes"),  # info: "issued" : datetime . fromtimestamp ( f .
                        "age_h": round(age, 1)})  # info: "age_h" : round ( age , 1 )
    return out  # info: return out


# ====================================================
# SECTION: function b_official_weather
# What it does: G1 official_weather_media._official_statement spoken text: HLS, else HWO, else AFD; 4500-char cap (G1).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_official_weather(t: datetime):  # info: def b_official_weather
    """G1 official_weather_media._official_statement spoken text: HLS, else HWO, else AFD; 4500-char cap (G1)."""  # info: """G1 official_weather_media._official_statement spoken text: HLS, else HWO, else AFD; 4500-char cap (G1)."""
    prods = official_products(t)  # info: set prods
    fresh = [p for p in prods if p["age_h"] is not None and p["age_h"] <= OFFICIAL_MAX_H and _speech_product(p["text"])]  # info: set fresh
    md = [f"# Official weather statement — {t.isoformat()}", "", "| Product | Issued / fetched | Age h | Used |",
          "| --- | --- | --- | --- |"]  # info: "| --- | --- | --- | --- |" ]
    pick = fresh[0] if fresh else None  # info: set pick
    for p in prods:  # info: for p in prods :
        md.append(f"| {p['type']} | {p['issued'] or 'n/a'} | {p['age_h'] if p['age_h'] is not None else 'n/a'} | "  # info: md . append ( f" | { p
                  f"{'yes' if p is pick else ''} |")  # info: f" { 'yes' if p is pick else
    if pick is None:  # info: if pick is None :
        spoken = "Honolulu National Weather Service has no local hurricane statement in effect."  # G1 fallback wording
    else:  # info: else :
        spoken = _speech_product(pick["text"])  # info: set spoken
        if len(spoken) > 4500:  # info: if len ( spoken ) > 4500 :
            spoken = spoken[:4500].rsplit(" ", 1)[0] + "."  # info: set spoken
    sp = [f"Official NWS Honolulu statement. {spoken}"]  # info: set sp
    md += ["", "## Spoken", "", sp[0], "",
           "_Sources: Database `Weather/Hawai'i/official/HLS_current.txt` (official_statement.py) + "  # info: "_Sources: Database `Weather/Hawai'i/official/HLS_current.txt` (official_statement.py) + "
           "`Weather/Hawai'i/hfo/api.weather.gov/products/types/{HWO,AFD}/locations/HFO/HFO_current.txt` (weather poller)._", ""]  # info: "`Weather/Hawai'i/hfo/api.weather.gov/products/types/{HWO,AFD}/locations/HFO/HFO_current.txt` (weather poller)
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function _uptime
# What it does:  uptime.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _uptime() -> tuple[str, int]:  # info: def _uptime
    up = float(open("/proc/uptime").read().split()[0])  # info: set up
    boot = datetime.fromtimestamp(time.time() - up).astimezone()  # info: set boot
    return boot.isoformat(timespec="minutes"), int(up // 60)  # info: return boot . isoformat ( timespec = "minutes"


# ====================================================
# SECTION: function b_boot_brief
# What it does: G1 boot-prelims Boot Report (morning before noon HST, midday after), file-only, template wording, no Grok.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_boot_brief(t: datetime):  # info: def b_boot_brief
    """G1 boot-prelims Boot Report (morning before noon HST, midday after), file-only, template wording, no Grok."""  # info: """G1 boot-prelims Boot Report (morning before noon HST, midday after), file-only, template wording, no Grok."
    kind = "morning" if t.hour < 12 else "midday"  # G1 desk_report_kind
    boot_at, up_min = _uptime()  # info: boot_at , up_min = _uptime ( )
    facts, (rows, _), h = energy_facts(t), alerts(), host()  # info: call facts
    k = jload(VOLCANOES / "kilauea-last.json") or {}  # info: set k
    storms = [x for x in hurricane_facts(t) if x.get("active")]  # info: set storms
    b = datetime.fromisoformat(boot_at)  # info: set b
    sp = [f"Boot report, {kind} edition.", f"It's {clock(t)} Hawaiian Standard Time.".replace("..", "."),  # info: set sp
          (f"The Pacific desk came up at {spoken_clock(b.hour, b.minute)}, {up_min} minutes ago." if up_min < 120 else  # info: call (
           f"The Pacific desk came up at {spoken_clock(b.hour, b.minute)}, about {round(up_min / 60)} hours ago.")  # info: f" The Pacific desk came up at { spoken_clock ( b . hour
          if up_min < 1440 else f"The Pacific desk has been up {up_min // 1440} days."]  # info: if up_min < 1440 else f" The Pacific desk has been up {
    lines = [f"Kind: {kind}", f"Boot: {boot_at} (up {up_min} min)", f"Host CPU {h['cpu']}%, memory {h['mem']}% used"]  # info: set lines
    ok = [f for f in facts if f["ok"]]  # info: set ok
    if ok:  # info: if ok :
        sp.append("Battery levels: " + ", ".join(f"{f['name']} at {f['soc']}%" for f in ok) + ".")  # info: sp . append ( "Battery levels: " + ", " .
        lines.append("Batteries: " + ", ".join(f"{f['name']} {f['soc']}%" for f in ok))  # info: lines . append ( "Batteries: " + ", " .
    else:  # info: else :
        sp.append("EcoFlow is offline."); lines.append("Batteries: offline")  # info: sp . append ( "EcoFlow is offline." ) ; lines
    ev = sorted({r["event"] for r in rows})  # info: set ev
    sp.append(f"{len(rows)} active weather alert{'s' if len(rows) != 1 else ''}" + (f", including {', '.join(ev[:3])}." if ev else "."))  # info: sp . append ( f" { len (
    lines.append(f"NWS alerts: {len(rows)}" + (f" ({', '.join(ev)})" if ev else ""))  # info: lines . append ( f" NWS alerts: { len
    if k.get("alert_level"):  # info: if k . get ( "alert_level" ) :
        sp.append(f"Kilauea alert level {str(k['alert_level']).lower()}" + (", erupting." if k.get("erupting") else "."))  # info: sp . append ( f" Kilauea alert level { str
        lines.append(f"Kilauea: {k['alert_level']} / {k.get('color_code')} erupting={k.get('erupting')}")  # info: lines . append ( f" Kilauea: { k
    if storms:  # info: if storms :
        s0 = storms[0]  # info: set s0
        sp.append(f"{s0['label']} {s0['name']} is about {s0['nm']} nautical miles from {s0['island']}.")  # info: sp . append ( f" { s0 [
        lines.append(f"Nearest storm: {s0['label']} {s0['name']} {s0['nm']} nm from {s0['island']}")  # info: lines . append ( f" Nearest storm: { s0
    sp.append(f"CPU {h['cpu']}%, memory {h['mem']}% used. End of boot report.")  # info: sp . append ( f" CPU { h
    md = [f"# Boot brief ({kind}) — {t.isoformat()}", ""] + [f"- {x}" for x in lines] + [
        "", "## Spoken", "", " ".join(sp), "",
        "_Sources: /proc/uptime, Database Energy + Weather alerts + Geology/Volcanoes + hurricane track.json. "  # info: "_Sources: /proc/uptime, Database Energy + Weather alerts + Geology/Volcanoes + hurricane track.json. "
        "G1 prelims order (NOAA -> NWS -> Kilauea) = the proposed ON_BOOT job runs geology_collect first._", ""]  # info: "G1 prelims order (NOAA -> NWS -> Kilauea) = the proposed ON_BOOT job runs geology_collect first._" , "" ]
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function b_current_report
# What it does: Full current summary of every measured desk, stamped on the half hour.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_current_report(t: datetime):  # info: def b_current_report
    """Full current summary of every measured desk. The heading is the :00 or :30 slot, not the finish time."""  # info: docstring
    stamp = on_the_dot(t)  # info: set stamp
    facts = energy_facts(t)  # info: set facts
    sun = jload(ENERGY / "sun" / "sun-times-last.json") or {}  # info: set sun
    moon = jload(ENERGY / "moon" / "moon-last.json") or {}  # info: set moon
    rows, upd = alerts()  # info: rows , upd = alerts ( )
    issued, groups = sfp_read()  # info: issued , groups = sfp_read ( )
    places = zfp_temps()  # info: set places
    quakes = quake_facts(t)  # info: set quakes
    kilauea = jload(VOLCANOES / "kilauea-last.json") or {}  # info: set kilauea
    mauna = jload(VOLCANOES / "mauna-loa-last.json") or {}  # info: set mauna
    storms = [s for s in hurricane_facts(t) if s.get("active")]  # info: set storms
    import system_perf  # info: import system_perf
    perf = system_perf.sample()  # info: set perf
    desks = _host_desks()  # info: set desks
    sec = desks.security_snapshot()  # info: set sec
    net = desks.net_counters()  # info: set net
    bw_hour, bw_day = desks.net_usage_window(3600, now=net), desks.net_usage_window(86400, now=net)  # info: bw_hour , bw_day = desks . net_usage_window
    still, look = newest_ch1(t), last_camera_look(t)  # info: still , look = newest_ch1 ( t ) , last_camera_look ( t )
    tasks, _per = open_tasks()  # info: tasks , _per = open_tasks ( )
    board = board_status()  # info: set board
    fresh = [p for p in official_products(t) if p.get("age_h") is not None and p["age_h"] <= OFFICIAL_MAX_H]  # info: set fresh
    md = [f"# Current report — {stamp.isoformat()}", "", DEV_NOTE, ""]  # info: set md
    sp = [f"Current report at {clock(stamp)} Hawaiian Standard Time.".replace("..", "."), DEV_NOTE + "."]  # info: set sp
    md += ["## Energy", ""]  # info: md += energy heading
    ok = [f for f in facts if f.get("ok")]  # info: set ok
    if ok:  # info: if ok :
        solar = sum(f.get("solar_w") or 0 for f in ok)  # info: set solar
        sp.append("Battery levels: " + ", ".join(f"{f['name']} at {f['soc']}%" for f in ok) + f". Solar input {spoken_watts(solar)}.")  # info: sp . append battery line
    else:  # info: else :
        sp.append("EcoFlow is offline.")  # info: sp . append ( "EcoFlow is offline." )
    for f in facts:  # info: for f in facts :
        if not f.get("ok"):  # info: if not f . get ( "ok" ) :
            md.append(f"- {f['name']}: no reading")  # info: md . append ( f" - { f [ 'name' ] } : no reading " )
            continue  # info: continue
        bits = [f"SOC {f['soc']}%", f"solar {f.get('solar_w')} W", f"AC out {f.get('ac_out_w')} W", f"USB-C out {f.get('usbc_out_w')} W"]  # info: set bits
        age = f"age {f.get('age_min')} min" if f.get("age_min") is not None else "age n/a"  # info: set age
        md.append(f"- {f['name']}: " + ", ".join(bits) + supply_clause(f) + f", {age}")  # info: md . append energy line
        note = range_clause(f)  # info: set note
        if note:  # info: if note :
            sp.append(note)  # info: sp . append ( note )
    md += ["", "## Sun and moon", ""]  # info: md += sun heading
    md.append(f"- Sun: {sun.get('sunrise', 'n/a')} / {sun.get('sunset', 'n/a')} ({sun.get('date', 'n/a')})")  # info: md . append sun line
    md.append(f"- Moon: {moon.get('phase_name', 'n/a')}, {moon.get('illumination', 'n/a')}% lit, rise {moon.get('moonrise', 'n/a')}, set {moon.get('moonset', 'n/a')}")  # info: md . append moon line
    if sun.get("date") == stamp.date().isoformat() and sun.get("sunrise") and sun.get("sunset"):  # info: if sun . get ( "date" ) == stamp . date
        sp.append(f"Sunrise {spoken_hhmm(sun['sunrise'])}, sunset {spoken_hhmm(sun['sunset'])}.".replace("..", "."))  # info: sp . append sun sentence
    else:  # info: else :
        sp.append("Sun times for today are not on file.")  # info: sp . append ( "Sun times for today are not on file." )
    if moon.get("phase_name"):  # info: if moon . get ( "phase_name" ) :
        sp.append(f"Moon is {moon['phase_name']}, {moon.get('illumination', 'n/a')} percent lit.")  # info: sp . append moon sentence
    else:  # info: else :
        sp.append("Moon phase is not on file.")  # info: sp . append ( "Moon phase is not on file." )
    md += ["", "## Weather", ""]  # info: md += weather heading
    if rows:  # info: if rows :
        md += [f"- {r['event']} — {r['area']}" for r in rows]  # info: md += alert lines
        sp.append(f"{len(rows)} active weather alert{'s' if len(rows) != 1 else ''}, including {rows[0]['event']}.")  # info: sp . append alert sentence
    else:  # info: else :
        md.append("- No active Hawaii alerts")  # info: md . append ( "- No active Hawaii alerts" )
        sp.append("No active Hawaii alerts.")  # info: sp . append ( "No active Hawaii alerts." )
    today = None  # info: set today
    if groups and groups[0]["periods"]:  # info: if groups and groups [ 0 ] [ "periods" ] :
        label, body = groups[0]["periods"][0]  # info: label , body = groups [ 0 ] [ "periods" ] [ 0 ]
        today = f"{label}: {body}"  # info: set today
    md.append(f"- State forecast ({issued or 'n/a'}): {today or 'not on file'}")  # info: md . append forecast line
    if today:  # info: if today :
        sp.append(f"Forecast for {today.split(':', 1)[0].lower()}: {re.split(r'(?<=[.]) ', today.split(':', 1)[1].strip())[0]}")  # info: sp . append forecast sentence
    if places:  # info: if places :
        for p in places:  # info: for p in places :
            bits = []  # info: set bits
            if p.get("high"):  # info: if p . get ( "high" ) :
                bits.append(f"high {p['high']}")  # info: bits . append ( f" high { p [ 'high' ] } " )
            if p.get("low"):  # info: if p . get ( "low" ) :
                bits.append(f"low {p['low']}")  # info: bits . append ( f" low { p [ 'low' ] } " )
            md.append(f"- {p['place']}: " + ", ".join(bits))  # info: md . append place line
        sp.append("Temperatures. " + ". ".join(f"{p['place']} high {p['high'] or 'n/a'}, low {p['low'] or 'n/a'}" for p in places) + ".")  # info: sp . append temperature sentence
    md.append(f"- Alerts updated: {upd or 'n/a'}")  # info: md . append ( f" - Alerts updated: { upd or 'n/a' } " )
    md += ["", "## Geology", ""]  # info: md += geology heading
    for label, key in (("Hawaii", "hawaii"), ("Global", "global")):  # info: for label , key in
        pack = quakes.get(key)  # info: set pack
        if not pack:  # info: if not pack :
            md.append(f"- {label} earthquakes: not on file")  # info: md . append ( f" - { label } earthquakes: not on file " )
            continue  # info: continue
        ev = list(pack.get("events") or [])  # info: set ev
        bigs = []  # info: set bigs
        for e in _m25(ev):  # info: for e in _m25 ( ev ) :
            try:  # info: try :
                bigs.append(float(e.get("mag")))  # info: bigs . append ( float ( e . get ( "mag" ) ) )
            except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
                continue  # info: continue
        big = max(bigs) if bigs else None  # info: set big
        largest = f", largest M{big:g}" if big is not None else ""  # info: set largest
        md.append(f"- {label}: {len(_m25(ev))} magnitude 2.5 or greater in 24 h{largest}, sample age {pack.get('age_min')} min")  # info: md . append quake line
    hi_pack = quakes.get("hawaii") or {}  # info: set hi_pack
    if hi_pack:  # info: if hi_pack :
        sp.append(f"Local earthquakes, last twenty four hours: {len(_m25(list(hi_pack.get('events') or [])))} magnitude 2.5 or greater.")  # info: sp . append quake sentence
    else:  # info: else :
        sp.append("Local earthquake data is not on file.")  # info: sp . append ( "Local earthquake data is not on file." )
    if isinstance(kilauea, dict) and kilauea.get("alert_level"):  # info: if isinstance ( kilauea , dict ) and kilauea . get ( "alert_level" ) :
        md.append(f"- Kilauea: {kilauea.get('alert_level')} / {kilauea.get('color_code')}, erupting {kilauea.get('erupting')}")  # info: md . append kilauea line
        sp.append(f"Kilauea alert level {str(kilauea.get('alert_level')).lower()}" + (", erupting." if kilauea.get("erupting") else "."))  # info: sp . append kilauea sentence
    else:  # info: else :
        md.append("- Kilauea: not on file")  # info: md . append ( "- Kilauea: not on file" )
        sp.append("Kilauea status is not on file.")  # info: sp . append ( "Kilauea status is not on file." )
    if isinstance(mauna, dict) and mauna.get("alert_level"):  # info: if isinstance ( mauna , dict ) and mauna . get ( "alert_level" ) :
        md.append(f"- Mauna Loa: {mauna.get('alert_level')} / {mauna.get('color_code')}")  # info: md . append mauna line
        sp.append(f"Mauna Loa alert level {str(mauna.get('alert_level')).lower()}.")  # info: sp . append mauna sentence
    md += ["", "## Hurricanes", ""]  # info: md += hurricane heading
    if storms:  # info: if storms :
        s0 = storms[0]  # info: set s0
        md.append(f"- {s0['label']} {s0['name']}: {s0['nm']} nm from {s0['island']}, bearing {s0['bearing']}")  # info: md . append storm line
        sp.append(f"{s0['label']} {s0['name']} is about {s0['nm']} nautical miles from {s0['island']}.")  # info: sp . append storm sentence
        for s in storms[1:4]:  # info: for s in storms [ 1 : 4 ] :
            md.append(f"- {s['label']} {s['name']}: {s['nm']} nm from {s['island']}")  # info: md . append other storm
    else:  # info: else :
        md.append("- No tropical system on the board")  # info: md . append ( "- No tropical system on the board" )
        sp.append("No tropical system with a mapped position is on the board.")  # info: sp . append ( "No tropical system with a mapped position is on the board." )
    md += ["", "## Host", ""]  # info: md += host heading
    up_h, up_m = perf["uptime_s"] // 3600, (perf["uptime_s"] % 3600) // 60  # info: up_h , up_m = perf [ "uptime_s" ] // 3600 , ( perf [ "uptime_s" ] % 3600 ) // 60
    md.append(f"- CPU {perf['cpu_pct']}%, load {' / '.join(perf['load'])}")  # info: md . append cpu line
    md.append(f"- Memory {perf['mem_pct']}% used ({perf['mem_used_gb']} / {perf['mem_total_gb']} GB)")  # info: md . append memory line
    md.append(f"- Disk {perf['disk_pct']}% used ({perf['disk_used_gb']} / {perf['disk_total_gb']} GB)")  # info: md . append disk line
    md.append(f"- Uptime {up_h}h {up_m}m")  # info: md . append uptime line
    host_say = f"Host CPU {round(perf['cpu_pct'])}%, memory {round(perf['mem_pct'])}% used, disk {round(perf['disk_pct'])}% used."  # info: set host_say
    if perf.get("temp_c") is not None:  # info: if perf . get ( "temp_c" ) is not None :
        md.append(f"- Temperature {perf['temp_c']} C")  # info: md . append temp line
        host_say = host_say[:-1] + f", temperature {perf['temp_c']} degrees Celsius."  # info: set host_say
    sp.append(host_say)  # info: sp . append ( host_say )
    md += ["", "## Security", ""]  # info: md += security heading
    md.append(f"- Firewall starts on boot: {sec.get('ufw_boot')}")  # info: md . append firewall line
    md.append(f"- SSH active: {sec.get('ssh_active')}")  # info: md . append ssh line
    md.append(f"- TCP listeners: {sec.get('listen_tcp')}")  # info: md . append listeners line
    md.append(f"- Established connections: {sec.get('established')}")  # info: md . append connections line
    md.append(f"- Failed sign-ins, last hour / 24 h: {sec.get('failed_1h')} / {sec.get('failed_24h')}")  # info: md . append failed sign-ins
    if sec.get("failed_1h") is not None:  # info: if sec . get ( "failed_1h" ) is not None :
        sp.append(f"Security. Failed sign-ins {sec.get('failed_1h')} in the last hour, {sec.get('failed_24h')} in the last twenty four hours.")  # info: sp . append security sentence
    else:  # info: else :
        sp.append("The sign-in log is not readable.")  # info: sp . append ( "The sign-in log is not readable." )
    md += ["", "## Bandwidth", ""]  # info: md += bandwidth heading
    if bw_hour or bw_day:  # info: if bw_hour or bw_day :
        if bw_hour:  # info: if bw_hour :
            md.append(f"- Last hour: {bw_hour['rx']} bytes down, {bw_hour['tx']} bytes up")  # info: md . append hour bytes
            sp.append(f"Last hour bandwidth: {desks.spoken_bytes(bw_hour['rx'])} down, {desks.spoken_bytes(bw_hour['tx'])} up.")  # info: sp . append hour bandwidth
        if bw_day:  # info: if bw_day :
            md.append(f"- Last 24 h: {bw_day['rx']} bytes down, {bw_day['tx']} bytes up")  # info: md . append day bytes
    else:  # info: else :
        md.append("- Not enough samples yet")  # info: md . append ( "- Not enough samples yet" )
        sp.append("Bandwidth data is not on file yet.")  # info: sp . append ( "Bandwidth data is not on file yet." )
    md += ["", "## Camera", ""]  # info: md += camera heading
    if still:  # info: if still :
        md.append(f"- Solar panel still age: {still['age_min']} min")  # info: md . append still age
        sp.append(f"Solar panel still is {still['age_min']} minutes old." if still["age_min"] else "Solar panel still is current.")  # info: sp . append still sentence
    else:  # info: else :
        md.append("- Solar panel still: not on file")  # info: md . append ( "- Solar panel still: not on file" )
        sp.append("No solar panel still on file.")  # info: sp . append ( "No solar panel still on file." )
    if look.get("sentence"):  # info: if look . get ( "sentence" ) :
        md.append(f"- {look['sentence']}")  # info: md . append ( f" - { look [ 'sentence' ] } " )
        sp.append(look["sentence"])  # info: sp . append ( look [ "sentence" ] )
    md += ["", "## Report board", ""]  # info: md += board heading
    labels = {"morning": "Morning report", "midday": "Midday report", "late": "Late report"}  # info: set labels
    slot_rows = []  # info: set slot_rows
    for key, row in ((board or {}).get("slots") or {}).items():  # info: for key , row in board slots
        if isinstance(row, dict):  # info: if isinstance ( row , dict ) :
            slot_rows.append((str(row.get("scheduled_at") or ""), labels.get(key, key), str(row.get("status") or "unknown")))  # info: slot_rows . append
    slot_rows.sort()  # info: slot_rows . sort ( )
    if slot_rows:  # info: if slot_rows :
        md += [f"- {name} {at} {status}" for at, name, status in slot_rows]  # info: md += slot lines
        sp.append("Report board: " + ", ".join(f"{name} {status}" for _at, name, status in slot_rows) + ".")  # info: sp . append board sentence
    else:  # info: else :
        md.append("- Report board is not on file")  # info: md . append ( "- Report board is not on file" )
        sp.append("The report board is not on file.")  # info: sp . append ( "The report board is not on file." )
    md += ["", "## Official weather", ""]  # info: md += official heading
    if fresh:  # info: if fresh :
        pick = fresh[0]  # info: set pick
        md.append(f"- {pick['type']}, age {pick['age_h']} h")  # info: md . append official line
        sp.append(f"Official weather product {pick['type']} is on file.")  # info: sp . append official sentence
    else:  # info: else :
        md.append("- No fresh Honolulu statement")  # info: md . append ( "- No fresh Honolulu statement" )
        sp.append("No fresh Honolulu weather statement is on file.")  # info: sp . append ( "No fresh Honolulu weather statement is on file." )
    md += ["", "## Work orders", "", f"- Open items: {tasks}", ""]  # info: md += work orders
    sp.append(f"{tasks} open work order items. End of current report.")  # info: sp . append ( f" { tasks } open work order items. End of current report. " )
    md += ["## Spoken", "", " ".join(sp), ""]  # info: md += spoken
    return "\n".join(md), sp  # info: return "\n" . join ( md ) , sp


# ====================================================
# SECTION: BUILD
# What it does: Set BUILD.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
BUILD = {"hourly_chime": b_hourly_chime, "nws_weather": b_nws_weather, "energy_report": b_energy_report,  # info: set BUILD
         "remaining_tasks": b_remaining_tasks, "morning_report": lambda t: _rollup(t, "morning"),  # info: "remaining_tasks" : b_remaining_tasks , "morning_report" : lambda t
         "midday_report": lambda t: _rollup(t, "midday"), "late_report": lambda t: _rollup(t, "late"),  # info: "midday_report" : lambda t : _rollup ( t
         "earthquake_report": b_earthquake_report, "hurricane_desk": b_hurricane_desk,  # info: "earthquake_report" : b_earthquake_report , "hurricane_desk" : b_hurricane_desk ,
         "kilauea_report": b_kilauea_report, "solar_desk": b_solar_desk, "security_desk": b_security_desk,  # info: "kilauea_report" : b_kilauea_report , "solar_desk" : b_solar_desk ,
         "bandwidth_desk": b_bandwidth_desk, "official_weather": b_official_weather, "boot_brief": b_boot_brief,  # info: "bandwidth_desk" : b_bandwidth_desk , "official_weather" : b_official_weather ,
         "current_report": b_current_report}  # info: "current_report" : b_current_report


# ====================================================
# SECTION: function write_md
# What it does: write md.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_md(report: str, md: str) -> Path:  # info: def write_md
    path = REPORTS / f"{report}_current.md"  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    if path.is_file():  # info: if path . is_file ( ) :
        retire_current(path)  # info: call retire_current
    tmp = path.with_suffix(".md.tmp")  # info: set tmp
    tmp.write_text(md.rstrip() + "\n\n_Template report; measured values only._\n", encoding="utf-8")  # info: tmp . write_text ( md . rstrip (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )
    return path  # info: return path


# ====================================================
# SECTION: function voice
# What it does: voice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def voice(report: str, spoken: list[str]) -> dict:  # info: def voice
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:  # info: with tempfile . NamedTemporaryFile ( "w" , suffix
        f.write(" ".join(spoken))  # info: f . write ( " " . join (
    cmd = ["bash", str(HERE / "voice-render.sh"), "stitch", "--report", report, "--kind", KIND[report], "--text-file", f.name]  # info: set cmd
    if report == "hourly_chime":  # info: if report == "hourly_chime" :
        cmd.append("--no-gate")  # G1 chimes bypassed the live-facts gate (spelled-out times carry no digits)
    try:  # info: try :
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # info: set p
        last = (p.stdout.strip().splitlines() or ["{}"])[-1]  # info: set last
        try:  # info: try :
            res = json.loads(last)  # info: set res
        except ValueError:  # info: except ValueError :
            res = {}  # info: set res
        res["rc"] = p.returncode  # info: res [ "rc" ] = p . returncode
        if p.returncode == 75:  # info: if p . returncode == 75 :
            res["detail"] = "busy (single-flight) — WAV skipped"  # info: res [ "detail" ] = "busy (single-flight) — WAV skipped"
        return res  # info: return res
    finally:  # info: finally :
        os.unlink(f.name)  # info: os . unlink ( f . name )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if len(sys.argv) < 2 or sys.argv[1] not in BUILD:  # info: if len ( sys . argv ) <
        print(json.dumps({"ok": False, "detail": f"usage: voice_reports.py {'|'.join(BUILD)} [--no-voice]"}))  # info: call print
        return 2  # info: return 2
    report, t = sys.argv[1], now()  # info: report , t = sys . argv [
    if report == "hourly_chime" and t.minute not in (0, 30):  # info: if report == "hourly_chime" and t . minute not in ( 0 , 30 ) :
        print(json.dumps({"ok": True, "report": report, "skipped": True, "detail": "prebuilt chimes play at :00 and :30"}))  # info: call print
        return 0  # info: return 0
    md, spoken = BUILD[report](t)  # info: md , spoken = BUILD [ report ]
    res = {"ok": True, "report": report, "md": str(write_md(report, md)), "sentences": len(spoken)}  # info: set res
    if "--no-voice" not in sys.argv and report == "hourly_chime":  # info: if "--no-voice" not in sys . argv and report == "hourly_chime" :
        from hourly_chimes import persona_for, wav_path  # info: from hourly_chimes import persona_for , wav_path
        path = wav_path(t.hour, t.minute)  # info: set path
        who = persona_for(t.hour)  # info: set who
        if not path.is_file():  # info: if not path . is_file ( ) :
            res["voice"] = {"ok": False, "detail": "prebuilt chime missing", "wav": str(path)}  # info: res [ "voice" ] = { "ok" : False
        else:  # info: else :
            res["voice"] = {"ok": True, "mode": "prebuilt", "wav": str(path), "agent": who}  # info: res [ "voice" ] = { "ok" : True , "mode" : "prebuilt"
            import voice_deliver  # info: import voice_deliver
            res["deliver"] = voice_deliver.deliver(report, path, " ".join(spoken), KIND[report], report_text=md, who=who, remember_as=t.strftime("%Y-%m-%dT%H:%M"))  # info: res [ "deliver" ] = voice_deliver . deliver
    elif "--no-voice" not in sys.argv and report == "energy_report":  # info: elif "--no-voice" not in sys . argv and report == "energy_report" :
        res["voice"] = {"ok": True, "skipped": True, "detail": "blended into the hourly solar desk; this run refreshes the camera look"}  # info: res [ "voice" ] = { "ok" : True , "skipped" : True , "detail" : "blended into the hourly solar desk; this run refreshes the camera look" }
    elif "--no-voice" not in sys.argv:  # info: elif "--no-voice" not in sys . argv :
        res["voice"] = voice(report, spoken)  # info: res [ "voice" ] = voice ( report
        wav = (res.get("voice") or {}).get("wav")  # info: set wav
        if wav:  # info: if wav
            import voice_deliver  # info: import voice_deliver
            photo = newest_ch1(t) if report == "solar_desk" else None  # info: set photo
            look = str(last_camera_look(t).get("sentence") or "") if report == "solar_desk" else ""  # info: set look
            age_line = f"Solar panel still is {photo['age_min']} minutes old." if photo and photo["age_min"] > 0 else ""  # info: set age_line
            caption = " ".join(part for part in (look, age_line) if part)  # info: set caption
            res["deliver"] = voice_deliver.deliver(report, wav, " ".join(spoken), KIND[report], report_text=md, photo=(photo or {}).get("path"), photo_caption=caption)  # info: res [ "deliver" ] = voice_deliver . deliver
        voice_res = res.get("voice") or {}  # info: set voice_res
        if os.environ.get("RR_RADIO_PUSH", "1") == "1" and voice_res.get("ok") and not voice_res.get("skipped") and voice_res.get("rc") == 0 and voice_res.get("wav"):  # info: if os . environ . get ( "RR_RADIO_PUSH" , "1" ) == "1" and voice_res . get ( "ok" ) and not voice_res . get ( "skipped" ) and voice_res . get ( "rc" ) == 0 and voice_res . get ( "wav" )
            import radio_push  # info: import radio_push
            res["radio"] = radio_push.push_report(report)  # info: res [ "radio" ] = radio_push . push_report ( report )
    print(json.dumps(res, ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
