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
  reports: hourly_chime · nws_weather · remaining_tasks · morning_report · midday_report · late_report
           · earthquake_report · hurricane_desk · kilauea_report · kilauea_image_check · solar_desk · security_desk · bandwidth_desk
           · boot_brief · current_report · custom_msg

Each run writes Database Media/Audio/Voice/Reports/<report>_current.md (old copy -> Reports/Archive/
<report>_YYYYMMDDTHHMM.md) and a stitched WAV Media/Audio/Voice/<report>_current.wav via voice-render.sh
(single-flight lock, nice 10, phrase-clip cache, non-resident). If the lock is busy the WAV is skipped
(rc 75 recorded) and the text still lands. A Telegram voice note posts only when RR_VOICE_DELIVER=1. RR_TELEGRAM_DEST=council selects the original council chat. After a finished WAV, radio_push.py sends that one _current file to the Mainland library over SSH unless RR_RADIO_PUSH=0. Speakers stay off. The Mainland host does not fetch.
Only G3 data that exists is read: Database Energy/{soc,watts}/*-last.json (EcoFlow BLE), Database
Weather/Hawai'i (NWS alerts + SFP state forecast, Pacific weather poller), Library Work-Order checkboxes,
/proc, and Database Geology/Earthquakes/{hawaii,global}-last.json (ML2 collectors/geology.py → Database,
job geology_collect gated RR_GEOLOGY=1). earthquake_report = G1 earthquake-hourly spoken script (Carly), job gated
RR_VOICE_QUAKE=1 (2026-09-29, migration-geology). G1 council_quake (Telegram per-quake posts) stays NOT ported.
hurricane_desk = G1 weather/hurricane-desk Hawaiʻi block (Carly), fed from Database Weather/Hawai'i/hurricanes/
tracking/*/track.json (Pacific weather poller, NHC CurrentStorms, Hawaiʻi-relevant storms only) + NWS HI alerts; job gated
RR_VOICE_HURRICANE=1. G1 global JTWC/RAMMB board, OBS and radio push stay NOT ported.
kilauea_report = G1 hourly Kīlauea desk line (persona._kilauea_line) + the cached HVO-notice lead-in, from Database
Geology/Volcanoes/Hawaii/{kilauea,mauna-loa}-last.json; job gated RR_VOICE_KILAUEA=1. G1 rr-kilauea Grok draft / Discord post NOT ported.
kilauea_image_check = Carly every-15m USGS HVO still look via Geology/scripts/kilauea_look.py (Gemma stack shared with
panel_look); speaks "Kilauea observation image was checked" plus measured fountaining/activity findings; job gated
RR_VOICE_KILAUEA_IMAGE=1. Report-side only — not in LOCAL_DATA_POLL_JOBS.
solar_desk = combined energy + solar product (Bruce): one merged battery (average charge, totaled watts), sun times, newest ch1 still, and this hour's
camera look (refreshes via panel_look.observe when the hour has no reading). The separate energy_report voice job
is retired; content lives here. security_desk / bandwidth_desk = G1 hourly desks (Carly) from host_desks.py;
bandwidth_desk also folds Mainland site analytics (Home proxy + Radio listeners) from
Database Logs/Website/analytics/daily (Website/scripts/analytics_pull.py / pull-from-api.sh).
Gates: RR_VOICE_SOLAR / RR_VOICE_SECURITY / RR_VOICE_BANDWIDTH (jobs.py).
boot_brief = G1 boot-prelims Boot Report (file-only, no Grok) as a template brief (Ava). PROPOSED (RR_VOICE_BOOT), not in jobs.py.
custom_msg = Bruce reads Database Media/Audio/Voice/custom_msg_current.txt every run (exact path).
Roll-ups append an LLM summary via run-infer.sh only when RR_VOICE_ROLLUP_LLM=1 (off by default). The off state is not written into the report.
Scheduling: jobs.py, one env gate per report (read at poller start). Added 2026-09-29 (g3-voice-reports2).
current_report summarizes the same measured desks. Spoken time and headings are the clock when the text is built.
Morning, midday, and late still run at 09:02, 12:02, and 21:02, and they say that clock.
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
REPORTS = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB / "Media" / "Audio" / "Voice" / "Reports")))  # info: set REPORTS
# Exact source for custom_msg — always this path, every run.
CUSTOM_MSG = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Audio/Voice/custom_msg_current.txt")  # info: set CUSTOM_MSG
WX = DB / "Weather" / "Hawai'i"  # info: set WX
ALERTS = WX / "hfo" / "api.weather.gov" / "alerts" / "active" / "area=HI" / "area=HI_current.json"  # info: set ALERTS
SFP = WX / "reports" / "0 Level Processing" / "sfp_state_forecast_current.md"  # info: set SFP
ZFP = WX / "hfo" / "api.weather.gov" / "products" / "types" / "ZFP" / "locations" / "HFO" / "HFO_current.txt"  # info: set ZFP
ENERGY = DB / "Energy"  # info: set ENERGY
QUAKES = DB / "Geology" / "Earthquakes"  # info: set QUAKES
QUAKE_STATE = REPORTS / "earthquake_report_seen.json"  # G1 earthquake-hourly.json seen_ids (new since last report)
QUAKE_STALE_MIN = 20  # info: set QUAKE_STALE_MIN
VOLCANOES = DB / "Geology" / "Volcanoes" / "Hawaii"  # info: Hawaiʻi volcano + cams bank
ANALYTICS_DAILY = DB / "Logs" / "Website" / "analytics" / "daily"  # info: set ANALYTICS_DAILY
HVO_STALE_MIN = 30  # info: set HVO_STALE_MIN
_MAX_HI, _MAX_GLOBAL = 6, 8  # G1 spoken caps
HURRICANES = WX / "hurricanes" / "tracking"  # <Storm>_<first-seen>/track.json (ML2 weather_hawaii → Database)
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
OFFLINE_SOC = 5  # info: set OFFLINE_SOC
DELTA_GEN_W = 550  # info: Delta 2 AC in above this is the generator
RIVER_GEN_W = 300  # info: River 2 Pro AC in above this is the generator


def ble_voice_on() -> bool:  # info: def ble_voice_on
    """EcoFlow BLE pack lines on air. Default off while the adapter is unreliable."""  # info: docstring
    return os.environ.get("RR_VOICE_BLE", "0") == "1"  # info: return RR_VOICE_BLE gate
# ====================================================
# SECTION: KIND
# What it does: Set KIND.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
KIND = {"hourly_chime": "chime", "nws_weather": "nws", "remaining_tasks": "remaining",  # info: set KIND
        "morning_report": "morning", "midday_report": "midday", "late_report": "late", "earthquake_report": "earthquake",  # info: "morning_report" : "morning" , "midday_report" : "midday" ,
        "hurricane_desk": "hurricane", "kilauea_report": "kilauea", "kilauea_image_check": "kilauea",  # info: kilauea kinds -> Carly
        "solar_desk": "solar", "security_desk": "security", "bandwidth_desk": "bandwidth",  # info: "solar_desk" : "solar" , "security_desk" : "security" ,
        "boot_brief": "boot", "current_report": "current", "custom_msg": "custom"}  # info: custom_msg -> Bruce
DEV_NOTE = "Automated Reports are in active development and is expected to change"  # info: set DEV_NOTE


# ====================================================
# SECTION: function now
# What it does: Hawaii clock when the report text is built.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> datetime:  # info: def now
    return datetime.now().astimezone().replace(microsecond=0)  # info: return datetime . now ( ) . astimezone


# ====================================================
# SECTION: function clock
# What it does: Spoken hour and minute of the generation clock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clock(t: datetime) -> str:  # info: def clock
    return spoken_clock(t.hour, t.minute)  # info: return spoken_clock ( t . hour , t


def generated_at(t: datetime) -> str:  # info: def generated_at
    return f"Report generated at {clock(t)}.".replace("..", ".")  # info: return f" Report generated at { clock ( t ) } . " . replace ( ".." , "." )


def say_change(sp: list, key: str, value, label: str, t: datetime) -> None:  # info: def say_change
    """Append percent change for yesterday, last week, and last month. Skip a period with no earlier reading."""  # info: docstring
    import compare_span  # info: import compare_span
    sp.extend(compare_span.sentences(key, value, label, t))  # info: sp . extend ( compare_span . sentences ( key , value , label , t ) )


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
    if not ble_voice_on():  # info: BLE off the air for now
        return []  # info: return empty — callers skip EcoFlow lines
    out = []  # info: set out
    for key, name in DEVICES:  # info: for key , name in DEVICES :
        soc, watts = jload(ENERGY / "soc" / f"{key}_current.json"), jload(ENERGY / "watts" / f"{key}_current.json") or {}  # info: soc , watts = jload ( ENERGY /
        if not soc or "soc" not in soc:  # info: if not soc or "soc" not in soc
            out.append({"name": name, "ok": False})  # info: out . append ( { "name" : name
            continue  # info: continue
        try:  # info: try :
            age = int((t - datetime.fromisoformat(soc["at"])).total_seconds() // 60)  # info: set age
        except (KeyError, ValueError):  # info: except ( KeyError , ValueError ) :
            age = None  # info: set age
        row = {"name": name, "key": key, "ok": True, "soc": round(float(soc["soc"])), "at": soc.get("at"), "age_min": age,  # info: set row
               "solar_w": watts.get("solar_input_power"), "ac_out_w": watts.get("ac_output_power"),  # info: "solar_w" : watts . get ( "solar_input_power" )
               "usbc_out_w": watts.get("usbc_output_power"), "ac_in_w": watts.get("ac_input_power"),  # info: "usbc_out_w" : watts . get ( "usbc_output_power" )
               "charge": watts.get("charge_source")}  # info: "charge" : watts . get ( "charge_source" )
        row["off"] = (  # info: row [ "off" ] =
            isinstance(age, int) and age > STALE_MIN and row["soc"] <= OFFLINE_SOC  # info: isinstance ( age , int ) and age > STALE_MIN and row [ "soc" ] <= OFFLINE_SOC
        )  # info: )
        out.append(row)  # info: out . append ( row )
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
    if f.get("off") or not f.get("ok") or age is None or age <= STALE_MIN:  # info: if f . get ( "off" ) or not f . get ( "ok" ) or age is None or age <= STALE_MIN :
        return None  # info: return None
    return f"{f['name']} is out of range."  # info: return f" { f [ 'name' ] } is out of range. "


# ====================================================
# SECTION: function off_sentence
# What it does: One line when a pack at 5 percent or less has stopped reporting. Does not list watts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def off_sentence(f: dict) -> str:  # info: def off_sentence
    return f"{f['name']} discharged and powered off. Last reading was {f['soc']} percent."  # info: return f" { f [ 'name' ] } discharged and powered off. Last reading was { f [ 'soc' ] } percent. "


# ====================================================
# SECTION: function reading_age_clause
# What it does: Comma clause when a pack sample is at least 10 minutes old.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def reading_age_clause(f: dict) -> str:  # info: def reading_age_clause
    """Comma clause when a pack sample is at least 10 minutes old."""  # info: """Comma clause when a pack sample is at least 10 minutes old."""
    age = f.get("age_min")  # info: set age
    if f.get("off") or not f.get("ok") or not isinstance(age, int) or age < 10:  # info: if f . get ( "off" ) or not f . get ( "ok" ) or not isinstance
        return ""  # info: return ""
    unit = "minute" if age == 1 else "minutes"  # info: set unit
    return f", reading is {age} {unit} old"  # info: return f" , reading is { age } { unit } old "


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
# SECTION: function _elev
# What it does: Keep the elevation temperature when a zone also lists the shore. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _elev(phrase: str) -> str:  # info: def _elev
    raw = (phrase or "").strip(" ,")  # info: set raw
    hit = re.search(  # info: set hit
        r"(?:to\s+)?((?:around\s+)?\d+(?:\s+to\s+\d+)?)\s+(?:at|above|near)\s+(\d{3,})\s*feet",  # info: elevation band pattern
        raw,  # info: raw ,
        re.I,  # info: re . I ,
    )  # info: )
    if hit:  # info: if hit :
        return f"{hit.group(1).strip()} at {hit.group(2)} feet"  # info: return elev reading
    return ""  # info: return ""


# ====================================================
# SECTION: function _zone_range
# What it does: Keep the shore-to-elevation temperature span when a zone lists both. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _zone_range(phrase: str) -> str:  # info: def _zone_range
    raw = (phrase or "").strip(" ,")  # info: set raw
    if re.search(r"near the shore|at \d{3,}\s*feet|above \d{3,}\s*feet|near \d{3,}\s*feet", raw, re.I):  # info: if zone lists shore or elev
        return raw  # info: return raw
    return _shore(raw)  # info: return _shore ( raw )


# ====================================================
# SECTION: function _band_temp
# What it does: Apply shore, elev, or full-zone band to a Highs/Lows phrase. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _band_temp(phrase: str, band: str) -> str:  # info: def _band_temp
    if not phrase:  # info: if not phrase :
        return ""  # info: return ""
    if band == "shore":  # info: if band == "shore" :
        return _shore(phrase)  # info: return _shore ( phrase )
    if band == "elev":  # info: if band == "elev" :
        return _elev(phrase) or _zone_range(phrase)  # info: return elev or full zone span
    return _zone_range(phrase)  # info: return _zone_range ( phrase )


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
# What it does: Today high and tonight low for Honolulu, Lihue, Kahului, Hilo, Mountain View, Volcano, and Kailua-Kona. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _forecast_labels(now: datetime | None = None) -> tuple[tuple[str, ...], tuple[str, ...]]:  # info: def _forecast_labels
    """High and low period names for this Hawaii day. NWS uses the weekday after midnight, and Today or Tonight earlier."""  # info: docstring
    clock = now or datetime.now().astimezone()  # info: set clock
    day = clock.strftime("%A").upper()  # info: set day
    highs = (day, "TODAY")  # info: set highs
    if clock.hour < 6:  # info: if clock . hour < 6
        lows = ("REST OF TONIGHT", "TONIGHT", f"{day} NIGHT")  # info: set lows
    else:  # info: else
        lows = (f"{day} NIGHT", "TONIGHT", "REST OF TONIGHT")  # info: set lows
    return highs, lows  # info: return highs , lows


def _period_body(block: str, labels: tuple[str, ...]) -> str:  # info: def _period_body
    for label in labels:  # info: for label in labels
        hit = re.search(rf"(?ms)^\.{re.escape(label)}\.\.\.(.+?)(?=^\.[A-Z]|\Z)", block)  # info: set hit
        if hit:  # info: if hit
            return hit.group(1)  # info: return hit . group ( 1 )
    return ""  # info: return ""


def zfp_temps() -> list[dict]:  # info: def zfp_temps
    """Today high and tonight low from the HFO zone forecast for report towns. Shore, elev, or full-zone band per place. Does not send."""  # info: docstring
    # (NWS zone name, spoken place, band). Big Island East covers Hilo + Mountain View + Volcano.
    places = (  # info: set places
        ("Honolulu Metro", "Honolulu", "shore"),  # info: Honolulu shore
        ("Kauai East", "Lihue", "shore"),  # info: Lihue shore
        ("Maui Central Valley North", "Kahului", "shore"),  # info: Kahului shore
        ("Big Island East", "Hilo", "shore"),  # info: Hilo shore
        ("Big Island East", "Mountain View", "range"),  # info: Mountain View upcountry span
        ("Big Island East", "Volcano", "elev"),  # info: Volcano ~4000 ft band
        ("Kona", "Kailua-Kona", "shore"),  # info: Kailua-Kona shore
    )  # info: )
    try:  # info: try :
        txt = ZFP.read_text(encoding="utf-8")  # info: set txt
    except OSError:  # info: except OSError :
        return []  # info: return [ ]
    high_labels, low_labels = _forecast_labels()  # info: high_labels , low_labels = _forecast_labels ( )
    zone_raw: dict[str, dict] = {}  # info: set zone_raw
    wanted = {zone for zone, _, _ in places}  # info: set wanted
    for block in re.split(r"(?m)^HIZ\d+", txt):  # info: for block in re . split
        name_m = re.search(r"(?m)^([A-Za-z][A-Za-z ]+)-\s*$", block)  # info: set name_m
        if not name_m:  # info: if not name_m :
            continue  # info: continue
        key = name_m.group(1).strip()  # info: set key
        if key in zone_raw or key not in wanted:  # info: if key in zone_raw or key not in wanted
            continue  # info: continue
        raw = {"high": None, "low": None}  # info: set raw
        for labels, word, field in ((high_labels, "Highs", "high"), (low_labels, "Lows", "low")):  # info: for labels , word , field
            body = _period_body(block, labels)  # info: set body
            deg = re.search(rf"\b{word}\s+(.+?)(?:\.|$)", _flat(body)) if body else None  # info: set deg
            if deg:  # info: if deg :
                raw[field] = deg.group(1)  # info: raw [ field ] = deg . group ( 1 )
        if raw["high"] or raw["low"]:  # info: if raw [ "high" ] or raw [ "low" ]
            zone_raw[key] = raw  # info: zone_raw [ key ] = raw
    out: list[dict] = []  # info: set out
    for zone, place, band in places:  # info: for zone , place , band in places
        raw = zone_raw.get(zone)  # info: set raw
        if not raw:  # info: if not raw :
            continue  # info: continue
        row = {"place": place, "high": None, "low": None}  # info: set row
        for field in ("high", "low"):  # info: for field in ( "high" , "low" )
            if raw.get(field):  # info: if raw . get ( field ) :
                valued = _band_temp(raw[field], band)  # info: set valued
                if valued:  # info: if valued :
                    row[field] = valued  # info: row [ field ] = valued
        if row["high"] or row["low"]:  # info: if row [ "high" ] or row [ "low" ]
            out.append(row)  # info: out . append ( row )
    return out  # info: return out


# ====================================================
# SECTION: function open_tasks
# What it does: open tasks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def open_tasks() -> tuple[int, list[tuple[int, str]]]:  # info: def open_tasks
    wo = LIB / "Documentation" / "06-Development" / "Work-Orders"  # info: set wo
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
# What it does: Database Geology/Earthquakes last files (written by ML2 geology collector).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def quake_facts(t: datetime) -> dict:  # info: def quake_facts
    """Database Geology/Earthquakes last files (written by ML2 geology collector)."""  # info: ML2 geology → Database
    out = {}  # info: set out
    for key in ("hawaii", "global"):  # info: for key in ( "hawaii" , "global" )
        d = jload(QUAKES / f"{key}_current.json")  # info: set d
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
def quake_change_sentence(label: str, change: dict) -> str | None:  # info: def quake_change_sentence
    parts = []  # info: set parts
    for key, words in (("24h", "previous day"), ("7d", "previous week")):  # info: for key , words
        pct = change.get(f"m25_{key}_pct")  # info: set pct
        if pct == "new":  # info: if pct == new
            parts.append(f"new compared with the {words}")  # info: parts . append new
        elif isinstance(pct, int) and pct > 0:  # info: elif rise
            parts.append(f"up {pct} percent from the {words}")  # info: parts . append rise
        elif isinstance(pct, int) and pct < 0:  # info: elif drop
            parts.append(f"down {abs(pct)} percent from the {words}")  # info: parts . append drop
        elif pct == 0:  # info: elif unchanged
            parts.append(f"unchanged from the {words}")  # info: parts . append unchanged
    if not parts:  # info: if not parts
        return None  # info: return None
    return f"{label} magnitude 2.5 count is " + ", and ".join(parts) + "."  # info: return sentence


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
    sp = ["NWS Hawaii Report.", generated_at(t)]  # info: set sp
    md = [f"# NWS Hawaii — {t.isoformat()}", "", f"- Alerts source: `api.weather.gov/alerts/active?area=HI` (updated {upd or 'n/a'})",
          f"- Forecast source: NWS HFO State Forecast (SFP), issued {issued or 'n/a'}",
          "- Temperatures: NWS HFO Zone Forecast (ZFP), today high and tonight low", "", "## Active alerts", ""]
    if rows:  # info: if rows :
        sp.append(f"{len(rows)} active alert{'s' if len(rows) != 1 else ''} for Hawaii.")  # info: sp . append ( f" { len (
        say_change(sp, "nws.alerts", len(rows), "Active alerts", t)  # info: say_change alerts
        for r in rows[:3]:  # info: for r in rows [ : 3 ]
            sp.append(f"{r['event']} for {r['area']}.")  # info: sp . append ( f" { r [
        md += [f"- **{r['event']}** — {r['area']} (expires {r['expires']})" for r in rows]  # info: set md
    else:  # info: else :
        sp.append("No active HI alerts from the API sample.")  # info: sp . append ( "No active HI alerts from the API sample." )
        say_change(sp, "nws.alerts", 0, "Active alerts", t)  # info: say_change alerts
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
        for p in places:  # info: for p in places
            if p.get("high"):  # info: if p . get ( "high" )
                say_change(sp, f"nws.{p['place']}.high", p["high"], f"{p['place']} high", t)  # info: say_change high
            if p.get("low"):  # info: if p . get ( "low" )
                say_change(sp, f"nws.{p['place']}.low", p["low"], f"{p['place']} low", t)  # info: say_change low
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
    count, per = open_tasks()  # info: set count , per
    sp = ["Remaining tasks.", generated_at(t), DEV_NOTE + "."]  # info: set sp
    sp.append(f"{count} open work order item{'s' if count != 1 else ''}.")  # info: sp . append open work
    say_change(sp, "tasks.open", count, "Open work orders", t)  # info: say_change open work
    for n, code in per[:4]:  # info: for n , code in per
        sp.append(f"{code}, {n} open.")  # info: sp . append one order
    md = [f"# Remaining tasks — {t.isoformat()}", "", DEV_NOTE, "", "Source: open work orders.", ""]  # info: set md
    md += [f"- {code}: {n} open" for n, code in per] or ["- No open work order items."]  # info: set md
    md += ["", "## Spoken", "", " ".join(sp), ""]  # info: set md
    return "\n".join(md), sp  # info: return "\n" . join ( md ) , sp


# ====================================================
# SECTION: function b_energy_report
# What it does: Retired. Energy content folded into b_solar_desk (packs + camera look refresh). Kept as an alias for one release.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_energy_report(t: datetime):  # info: def b_energy_report (retired alias)
    """Retired energy desk. Forwards to the combined solar desk."""  # info: docstring
    return b_solar_desk(t)  # info: return b_solar_desk ( t )


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
    sp = ["Earthquake report.", generated_at(t)]  # info: set sp
    if hi is None:  # info: if hi is None :
        sp.append("Local earthquake data is not on file.")  # info: sp . append ( "Local earthquake data is not on file." )
    elif fresh_hi:  # info: elif fresh_hi :
        sp.append(f"{len(fresh_hi)} new local earthquake{'s' if len(fresh_hi) != 1 else ''}.")  # info: sp . append ( f" { len (
        sp += [f"Magnitude {e.get('mag')}, {_about_km(e.get('place'))}." for e in fresh_hi[:_MAX_HI]]  # info: set sp
    else:  # info: else :
        sp.append("No new local earthquakes since the last report.")  # info: sp . append ( "No new local earthquakes since the last report." )
    if hi is not None:  # info: if hi is not None :
        sp.append(f"Local last twenty four hours: {len(_m25(hi_ev))} magnitude 2.5 or greater.")  # info: sp . append ( f" Local last twenty four hours: { len
        local_change = quake_change_sentence("Local", hi.get("change") if isinstance(hi.get("change"), dict) else {})  # info: set local_change
        if local_change:  # info: if local_change
            sp.append(local_change)  # info: sp . append local change
        say_change(sp, "quake.hawaii.m25", len(_m25(hi_ev)), "Local magnitude 2.5 count", t)  # info: say_change local quakes
    if gl is None:  # info: if gl is None :
        sp.append("Global earthquake data is not on file.")  # info: sp . append ( "Global earthquake data is not on file." )
    elif fresh_gl:  # info: elif fresh_gl :
        sp.append(f"{len(fresh_gl)} new global earthquake{'s' if len(fresh_gl) != 1 else ''}.")  # info: sp . append ( f" { len (
        sp += [f"Magnitude {e.get('mag')}, {_about_km(e.get('place'))}." for e in fresh_gl[:_MAX_GLOBAL]]  # info: set sp
    else:  # info: else :
        sp.append("No new global earthquakes since the last report.")  # info: sp . append ( "No new global earthquakes since the last report." )
    if gl is not None:  # info: if gl is not None :
        sp.append(f"Global last twenty four hours: {len(_m25(gl_ev))} magnitude 2.5 or greater.")  # info: sp . append ( f" Global last twenty four hours: { len
        world_change = quake_change_sentence("Global", gl.get("change") if isinstance(gl.get("change"), dict) else {})  # info: set world_change
        if world_change:  # info: if world_change
            sp.append(world_change)  # info: sp . append world change
        say_change(sp, "quake.global.m25", len(_m25(gl_ev)), "Global magnitude 2.5 count", t)  # info: say_change global quakes
    for label, d in (("Hawaii", hi), ("global", gl)):  # info: for label , d in ( ( "Hawaii"
        if d and d.get("age_min") is not None and d["age_min"] > QUAKE_STALE_MIN:  # info: if d and d . get ( "age_min"
            sp.append(f"The {'local' if label == 'Hawaii' else label} United States Geological Survey data is {d['age_min']} minutes old.")  # info: sp . append ( f" The { 'local' if label == 'Hawaii' else label } United States Geological Survey data is { d [ 'age_min' ] } minutes old. " )
    for label, d, fresh in (("Hawaii", hi, fresh_hi), ("Global", gl, fresh_gl)):  # info: for label , d , fresh in (
        md += [f"## {label} Changes Since Last Report"]
        md += [f"- M{e.get('mag')} {_about_km(e.get('place'))} ({e.get('time_hst')})" for e in fresh[:12]] or ["- No new earthquakes."]  # info: set md
        if len(fresh) > 12:  # info: if len ( fresh ) > 12 :
            md.append(f"- ...and {len(fresh) - 12} more new earthquakes.")  # info: md . append ( f" - ...and { len
        ev = list((d or {}).get("events") or [])  # info: set ev
        big = max((float(e["mag"]) for e in _m25(ev)), default=None)  # info: set big
        change = (d or {}).get("change") if isinstance((d or {}).get("change"), dict) else {}  # info: set change
        md += ["", f"## {label} 24-Hour M2.5+ Summary",
               f"- {len(_m25(ev))} earthquakes" + (f"; largest M{big:g}." if big is not None else "."),  # info: f" - { len ( _m25 ( ev
               f"- 24h change: {change.get('m25_24h_pct', 'n/a')} percent. 7d change: {change.get('m25_7d_pct', 'n/a')} percent.",  # info: change line
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
# What it does: Spoken hurricane desk in sentences. Coordinates stay in the table, not on the air.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_hurricane_desk(t: datetime):  # info: def b_hurricane_desk
    """G1 hurricane_desk.hawaii_block + build spoken text, from G3 track.json + NWS HI alerts (never invents storms)."""  # info: """G1 hurricane_desk.hawaii_block + build spoken text, from G3 track.json + NWS HI alerts (never invents storm
    storms = hurricane_facts(t)  # info: set storms
    active = [s for s in storms if s["active"]]  # info: set active
    rows, updated = alerts()  # info: rows , updated = alerts ( )
    trop = [r for r in rows if any(k in str(r["event"]).lower() for k in TROPICAL_EVENTS)]  # info: set trop
    sp = ["Hurricane desk.", generated_at(t)]  # info: set sp
    if trop:  # info: if trop
        named = ", and ".join(f"{r['event']} for {r['area'] or 'Hawaii'}" for r in trop)  # info: set named
        watch = f"NWS Honolulu has {named}."  # info: set watch
    elif updated is None:  # info: elif updated is None
        watch = "The Hawaii alert file is not on the desk."  # info: set watch
    else:  # info: else
        watch = "Honolulu has no tropical watch or warning."  # info: set watch
    if not active:  # info: if not active
        sp.append("No tropical system has a current position near the islands.")  # info: sp . append quiet
        sp.append(watch)  # info: sp . append watch
    else:  # info: else
        n = active[0]  # info: set n
        local = bool(trop) or n["nm"] < HAWAII_THREAT_NM  # info: set local
        sp.append(f"{n['label']} {n['name']} is about {n['nm']} nautical miles from {n['island']}.")  # info: sp . append where
        if not local:  # info: if not local
            if n["bearing"] == "west":  # info: if west of the islands
                sp.append("It is west of the islands, toward Asia, not toward Hawaii.")  # info: sp . append west
            else:  # info: else
                sp.append("It is not a threat to Hawaii.")  # info: sp . append not local
        if n["movement_kt"] == 0:  # info: if stationary
            sp.append("It is nearly stationary.")  # info: sp . append stationary
        elif n["movement_compass"]:  # info: elif it is moving
            vs = {"toward": "toward Hawaii", "away": "away from Hawaii", "steady": "holding steady relative to Hawaii"}.get(n["approach"] or "", "")  # info: set vs
            speed = f" at about {n['movement_kt']} knots" if n["movement_kt"] else ""  # info: set speed
            moving = f"It is moving {n['movement_compass']}{speed}"  # info: set moving
            sp.append(moving + (f", {vs}." if vs else "."))  # info: sp . append moving
        if n["knots"]:  # info: if winds
            sp.append(f"Winds are about {n['knots']} knots.")  # info: sp . append winds
        sp.append(watch)  # info: sp . append watch
        say_change(sp, f"hurricane.{n['name']}.nm", n["nm"], f"{n['name']} distance", t)  # info: say_change distance
        if n.get("knots"):  # info: if n . get ( "knots" )
            say_change(sp, f"hurricane.{n['name']}.knots", n["knots"], f"{n['name']} winds", t)  # info: say_change winds
        if len(active) > 1:  # info: if more storms
            others = ". ".join(f"{s['label']} {s['name']} is about {s['nm']} nautical miles from {s['island']}" for s in active[1:4])  # info: set others
            sp.append(f"{len(active)} systems are on the board. {others}.")  # info: sp . append others
    sp.append("Watches and warnings stay with NWS Honolulu.")  # info: sp . append closer
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
# SECTION: function kilauea_photo_summary
# What it does: Report whether a banked Kīlauea photo was viewed and summarize look conditions.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def kilauea_photo_summary() -> str:  # info: def kilauea_photo_summary
    """Return a short photo-viewed and conditions line from current/last bank data."""  # info: docstring
    cams_dir = VOLCANOES / "Cams"  # info: set cams directory
    current_look = {}  # info: set current look
    look_paths = [cams_dir / "kilauea-look_current.json", cams_dir / "kilauea-look-current.json"]  # info: set preferred look paths
    look_paths += sorted(cams_dir.glob("*_current.json"))  # info: add other current look paths
    for look_path in look_paths:  # info: for current look path
        data = jload(look_path) or {}  # info: load current look
        if any(key in data for key in ("image", "activity", "visible", "sentence", "fountaining")):  # info: if look-shaped data
            current_look = data  # info: set current look data
            break  # info: stop current look scan
    look = current_look or jload(cams_dir / "kilauea-look_current.json") or {}  # info: choose current or last look
    cams_current = jload(cams_dir / "cams_current.json") or {}  # info: load current cams metadata
    viewed = None  # info: set viewed unknown
    if isinstance(cams_current.get("photo_viewed"), bool):  # info: if bank photo flag
        viewed = cams_current["photo_viewed"]  # info: use bank photo flag
    elif isinstance(cams_current.get("cams"), list):  # info: if bank cam rows
        viewed = any(isinstance(cam, dict) and (cam.get("viewed") or cam.get("ok")) for cam in cams_current["cams"])  # info: infer bank photo flag
    if viewed is None:  # info: if no bank photo flag
        viewed = bool(look.get("image"))  # info: infer viewed from look image
    activity = str(look.get("activity") or "").strip().lower()  # info: set activity
    visible = str(look.get("visible") or "").strip()  # info: set visible
    if bool(look.get("fountaining")) or activity == "fountaining":  # info: if fountaining
        conditions = "lava fountaining"  # info: set fountaining conditions
    elif activity:  # info: if activity
        conditions = activity  # info: set activity conditions
    else:  # info: if no activity
        conditions = ""  # info: set empty conditions
    # Drop invented night/day clock phrases (Gemma has said "dark night sky" on daylight stills).
    vis_low = visible.lower()  # info: set vis_low
    if visible and not any(tok in vis_low for tok in ("night", "daytime", "sunrise", "sunset", "dawn", "dusk")):  # info: if visible is factual
        conditions = f"{conditions}; {visible}" if conditions else visible  # info: append visible detail
    if not viewed:  # info: if photo not viewed
        return "Photo viewed: no. Conditions: no still available."  # info: return no-photo line
    if not conditions:  # info: if conditions missing
        conditions = "not recorded"  # info: set unknown conditions
    return f"Photo viewed: yes. Conditions: {conditions}."  # info: return photo line


# ====================================================
# SECTION: function b_kilauea_report
# What it does: G1 hourly Kīlauea desk (persona._kilauea_line wording) + HVO notice excerpt, from Database Geology/Volcanoes/Hawaii/.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_kilauea_report(t: datetime):  # info: def b_kilauea_report
    """G1 hourly Kīlauea desk (persona._kilauea_line wording) + HVO notice excerpt, from Database Geology/Volcanoes/Hawaii/."""  # info: Hawaiʻi volcano bank
    k, ml = jload(VOLCANOES / "kilauea_current.json"), jload(VOLCANOES / "mauna-loa_current.json")  # info: k , ml = jload ( VOLCANOES /
    hi = jload(QUAKES / "hawaii_current.json") or {}  # info: set hi
    photo_line = kilauea_photo_summary()  # info: set photo line
    # Hour batch already aired kilauea_image_check — keep photo in md, do not speak it again.
    speak_photo = os.environ.get("RR_HOUR_BATCH", "0") != "1"  # info: speak_photo false when image check is the prior desk
    md = [f"# Kilauea report — {t.isoformat()}", ""]
    if not isinstance(k, dict) or not k.get("alert_level"):  # info: if not isinstance ( k , dict )
        spoken_down = ["Kilauea: DOWN."] + ([photo_line] if speak_photo else [])  # info: set spoken_down
        md += ["_No HVO data on file (Database Geology/Volcanoes/Hawaii/kilauea_current.json missing). Run geology_collect.py._", f"- **Photo:** {photo_line}", "", "## Spoken", "", " ".join(spoken_down), ""]  # info: set md
        return "\n".join(md), spoken_down  # info: return down
    level = str(k.get("alert_level") or "unknown").strip().lower()  # info: set level
    erupting = k.get("erupting")  # info: set erupting
    if erupting:  # info: if erupting :
        state = "is erupting"  # info: set state
    elif level in {"advisory", "watch", "warning", "normal"} and erupting is False:  # info: elif level in { "advisory" , "watch" ,
        state = "is not erupting"  # info: set state
    else:  # info: else :
        state = "eruption state unknown"  # info: set state
    color = str(k.get("color_code") or "").lower()  # info: set color
    sp = ["Kilauea report.", generated_at(t),  # info: set sp
          f"Alert level {level}" + (f", aviation color code {color}." if color else "."),  # info: f" Alert level { level } " + (
          f"The volcano {state}."]  # info: volcano state
    if speak_photo:  # info: if speak_photo :
        sp.append(photo_line)  # info: sp . append photo once when not hour-batch
    note = k.get("latest_activity_notice") if erupting and k.get("latest_activity_notice") else k.get("latest_notice")  # info: set note
    note = note if isinstance(note, dict) else {}  # info: set note
    excerpt = _first_sentences(note.get("synopsis") or "")  # info: set excerpt
    if excerpt:  # info: if excerpt :
        sp += ["Here is the latest observatory notice.", excerpt]  # info: set sp
    else:  # info: else :
        sp.append("No HVO headline in this sample.")  # info: sp . append ( "No HVO headline in this sample." )
    if hi.get("kilauea_150km_count") is not None:  # info: if hi . get ( "kilauea_150km_count" ) is
        n = int(hi["kilauea_150km_count"])  # info: set n
        sp.append(f"United States Geological Survey: {n} earthquake{'s' if n != 1 else ''} magnitude 1 or greater within 150 kilometers in the last "  # info: sp . append ( f" United States Geological Survey: { n } earthquake
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
           f"- **Photo:** {photo_line}",  # info: photo line
           f"- **Collected:** {k.get('at')} (USGS HANS)", "", "## Spoken", "", " ".join(sp), ""]
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,



# ====================================================
# SECTION: function b_kilauea_image_check
# What it does: Carly 15-minute USGS HVO still look via kilauea_look (Gemma). Speaks check line plus measured findings.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_kilauea_image_check(t: datetime):  # info: def b_kilauea_image_check
    """Carly Kīlauea observation image check from USGS HVO stills via Geology/scripts/kilauea_look.py."""  # info: docstring
    geo = PACIFIC / "Geology" / "scripts"  # info: set geo
    if str(geo) not in sys.path:  # info: if not on path
        sys.path.insert(0, str(geo))  # info: insert path
    row = {}  # info: set row
    err = ""  # info: set err
    try:  # info: try
        import kilauea_look  # info: import kilauea_look
        row = kilauea_look.observe(t) or {}  # info: set row
    except Exception as exc:  # noqa: BLE001
        err = type(exc).__name__  # info: set err
        row = {}  # info: clear row
    md = [f"# Kilauea image check — {t.isoformat()}", ""]  # info: set md
    viewed = bool(row.get("image"))  # info: set viewed
    sp = [f"Kilauea observation image was checked. Photo viewed: {'yes' if viewed else 'no'}."]  # info: set sp
    if err:  # info: if import/observe failed
        md += [f"_Look failed: {err}_", ""]  # info: md error
        sp.append(f"Vision look failed ({err}).")  # info: sp error
    elif not row:  # info: elif empty
        md += ["_No look row on file._", ""]  # info: md empty
        sp.append("No look result on file.")  # info: sp empty
    else:  # info: else measured
        activity = str(row.get("activity") or "unclear")  # info: set activity
        fountain = bool(row.get("fountaining"))  # info: set fountain
        visible = str(row.get("visible") or "")  # info: set visible
        cam = str(row.get("cam_title") or row.get("cam") or "USGS HVO webcam")  # info: set cam
        finding = str(row.get("sentence") or "")  # info: set finding
        # sentence_for already prefixes the check line; strip duplicate lead-in for spoken parts after the fixed opener
        if finding.lower().startswith("kilauea observation image was checked."):  # info: if prefixed
            rest = finding[len("Kilauea observation image was checked."):].strip()  # info: set rest
            if rest:  # info: if rest
                sp.append(rest)  # info: append measured
        elif finding:  # info: elif raw finding
            sp.append(finding)  # info: append finding
        elif fountain or activity == "fountaining":  # info: elif fountain flag
            sp.append(f"Measured finding: lava fountaining is visible on the {cam} still.")  # info: fountain line
            if visible:  # info: if visible
                sp.append(f"Visible: {visible}.")  # info: visible
        elif activity and activity != "unclear":  # info: elif other activity
            sp.append(f"Measured finding: {activity} on the {cam} still.")  # info: activity line
            if visible:  # info: if visible
                sp.append(f"Visible: {visible}.")  # info: visible
        md += [  # info: md facts
            f"- **Cam:** {cam} (`{row.get('image') or 'n/a'}`)",  # info: cam
            f"- **Activity:** {activity}",  # info: activity
            f"- **Fountaining:** `{fountain}`",  # info: fountain
            f"- **Visible:** {visible or 'n/a'}",  # info: visible
            f"- **Photo viewed:** `{'yes' if viewed else 'no'}`",  # info: photo viewed
            f"- **Source kind:** `{row.get('source_kind') or 'n/a'}`",  # info: source kind
            f"- **Fetched live this check:** `{row.get('fetched_live')}`",  # info: fetched
            f"- **Reference:** {row.get('reference') or 'none'}",  # info: reference
            f"- **Model:** {row.get('model') or 'n/a'}",  # info: model
            f"- **At:** {row.get('at') or t.isoformat()}",  # info: at
            f"- **Error:** {row.get('error') or 'none'}",  # info: error
            "", "## Spoken", "", " ".join(sp), "",  # info: spoken
        ]  # info: ]
        return "\n".join(md), sp  # info: return measured
    md += ["", "## Spoken", "", " ".join(sp), ""]  # info: md spoken fallback
    return "\n".join(md), sp  # info: return fallback


# ====================================================
# SECTION: function _analytics_pull_mod
# What it does: Import Website/scripts/analytics_pull (desk mirror of ML2 daily analytics). Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _analytics_pull_mod():  # info: def _analytics_pull_mod
    sys.path.insert(0, str(PACIFIC / "Website" / "scripts"))  # info: sys . path . insert ( 0 , Website/scripts )
    import analytics_pull  # noqa: E402  (Pacific Website/scripts/analytics_pull.py)
    return analytics_pull  # info: return analytics_pull


# ====================================================
# SECTION: function site_analytics_doc
# What it does: Load today's Mainland analytics JSON from the desk bank (refresh when stale). Returns {} when missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def site_analytics_doc(t: datetime, *, refresh: bool = True) -> dict:  # info: def site_analytics_doc
    """Load today's Mainland analytics JSON from the desk bank (refresh when stale). Returns {} when missing."""  # info: docstring
    day = t.date().isoformat()  # info: set day
    try:  # info: try :
        mod = _analytics_pull_mod()  # info: set mod
        doc = mod.load_daily(day, refresh=refresh)  # info: set doc
    except Exception:  # info: except Exception :
        path = ANALYTICS_DAILY / f"{day}.json"  # info: set path
        doc = jload(path) or {}  # info: set doc
    return doc if isinstance(doc, dict) else {}  # info: return doc if isinstance ( doc , dict ) else {}


# ====================================================
# SECTION: function site_traffic_md_lines
# What it does: Markdown bullets for Home/Radio/API traffic from one analytics daily doc. Honest about partial Home.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def site_traffic_md_lines(doc: dict) -> list[str]:  # info: def site_traffic_md_lines
    """Markdown bullets for Home/Radio/API traffic from one analytics daily doc. Honest about partial Home."""  # info: docstring
    if not doc or not doc.get("ok"):  # info: if not doc or not doc . get ( "ok" ) :
        return ["- Mainland site analytics: not on file"]  # info: return missing bullet
    api = doc.get("api") if isinstance(doc.get("api"), dict) else {}  # info: set api
    radio = doc.get("radio") if isinstance(doc.get("radio"), dict) else {}  # info: set radio
    home = doc.get("home") if isinstance(doc.get("home"), dict) else {}  # info: set home
    proxy = api.get("home_proxy") if isinstance(api.get("home_proxy"), dict) else {}  # info: set proxy
    lines = [  # info: set lines
        f"- Analytics day: {doc.get('day')} ({doc.get('timezone') or 'Pacific/Honolulu'}), schema {doc.get('schema')}",  # info: analytics day line
        f"- API requests / unique visitors: {api.get('requests')} / {api.get('unique_visitors')} (bots {api.get('bots')})",  # info: api line
        f"- Home proxy: {proxy.get('requests')} requests, {proxy.get('unique_visitors')} visitors",  # info: home proxy line
        f"- Home pageviews: {home.get('pageviews')}",  # info: home pageviews line
        f"- Radio listeners: max {radio.get('listeners_max')}, avg {radio.get('listeners_avg')}, ~{radio.get('listen_minutes_est')} listen-minutes est ({radio.get('samples')} samples)",  # info: radio line
    ]  # info: ]
    note = home.get("note") or proxy.get("note")  # info: set note
    if note:  # info: if note :
        lines.append(f"- Note: {note}")  # info: lines . append note
    return lines  # info: return lines


# ====================================================
# SECTION: function site_traffic_spoken
# What it does: Spoken measured Home/Radio/API lines for bandwidth/current desks. No invention when fields are null.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def site_traffic_spoken(doc: dict, t: datetime) -> list[str]:  # info: def site_traffic_spoken
    """Spoken measured Home/Radio/API lines for bandwidth/current desks. No invention when fields are null."""  # info: docstring
    if not doc or not doc.get("ok"):  # info: if not doc or not doc . get ( "ok" ) :
        return ["Mainland site analytics are not on file yet."]  # info: return missing spoken
    api = doc.get("api") if isinstance(doc.get("api"), dict) else {}  # info: set api
    radio = doc.get("radio") if isinstance(doc.get("radio"), dict) else {}  # info: set radio
    home = doc.get("home") if isinstance(doc.get("home"), dict) else {}  # info: set home
    proxy = api.get("home_proxy") if isinstance(api.get("home_proxy"), dict) else {}  # info: set proxy
    out = ["Site traffic for today."]  # info: set out
    if api.get("requests") is not None:  # info: if api . get ( "requests" ) is not None :
        out.append(f"API saw {api.get('requests')} requests from {api.get('unique_visitors')} unique visitors.")  # info: out . append api sentence
        say_change(out, "analytics.api.requests", api.get("requests"), "API requests", t)  # info: say_change api requests
        say_change(out, "analytics.api.unique_visitors", api.get("unique_visitors"), "API unique visitors", t)  # info: say_change api visitors
    if proxy.get("requests") is not None:  # info: if proxy . get ( "requests" ) is not None :
        out.append(f"Home proxy signal: {proxy.get('requests')} requests from {proxy.get('unique_visitors')} visitors.")  # info: home proxy counts
        say_change(out, "analytics.home_proxy.requests", proxy.get("requests"), "Home proxy requests", t)  # info: say_change home proxy
    elif home.get("pageviews") is None:  # info: elif home . get ( "pageviews" ) is None :
        out.append("Full Home pageviews are not on this Mainland feed yet.")  # info: out . append missing home
    if home.get("pageviews") is not None:  # info: if home . get ( "pageviews" ) is not None :
        out.append(f"Home pageviews: {home.get('pageviews')}.")  # info: out . append home pageviews
        say_change(out, "analytics.home.pageviews", home.get("pageviews"), "Home pageviews", t)  # info: say_change home pageviews
    if radio.get("listeners_max") is not None or radio.get("listeners_avg") is not None:  # info: if radio listeners present
        avg = radio.get("listeners_avg")  # info: set avg
        avg_s = f"{avg:.1f}" if isinstance(avg, float) else str(avg)  # info: set avg_s
        mins = radio.get("listen_minutes_est")  # info: set mins
        mins_s = f"{mins:.0f}" if isinstance(mins, float) else str(mins)  # info: set mins_s
        out.append(  # info: out . append
            f"Radio listeners: max {radio.get('listeners_max')}, average {avg_s}, about {mins_s} listen minutes estimated."  # info: radio sentence
        )  # info: )
        say_change(out, "analytics.radio.listeners_max", radio.get("listeners_max"), "Radio listeners max", t)  # info: say_change radio max
        say_change(out, "analytics.radio.listen_minutes_est", radio.get("listen_minutes_est"), "Radio listen minutes", t)  # info: say_change radio minutes
    else:  # info: else :
        out.append("Radio listener samples are not on file yet.")  # info: out . append missing radio
    return out  # info: return out


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
# SECTION: function merged_battery
# What it does: One battery number. Charge is the average of the live packs. Watts are totals. A powered-off pack stays out of both.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def merged_battery(facts: list[dict]) -> dict | None:  # info: def merged_battery
    """One battery number. Charge is the average of the live packs. Watts are totals. A powered-off pack stays out of both."""  # info: docstring
    live = [f for f in facts if f.get("ok") and not f.get("off")]  # info: set live
    if not live:  # info: if not live
        return None  # info: return None

    def total(key):  # info: def total
        vals = [float(f[key]) for f in live if isinstance(f.get(key), (int, float))]  # info: set vals
        if not vals:  # info: if not vals
            return None  # info: return None
        return int(round(sum(vals)))  # info: return total

    socs = [int(f["soc"]) for f in live if isinstance(f.get("soc"), (int, float))]  # info: set socs
    return {  # info: return bank
        "soc": int(round(sum(socs) / len(socs))) if socs else None,  # info: average charge
        "count": len(live),  # info: live pack count
        "solar_w": total("solar_w"),  # info: totaled solar
        "ac_out_w": total("ac_out_w"),  # info: totaled AC out
        "usbc_out_w": total("usbc_out_w"),  # info: totaled USB-C out
    }  # info: end bank


def bank_spoken(bank: dict) -> str:  # info: def bank_spoken
    """The one sentence the desks speak for the merged battery."""  # info: docstring
    bits = []  # info: set bits
    if bank.get("soc") is not None:  # info: if bank . get ( "soc" ) is not None
        word = "pack" if bank.get("count") == 1 else "packs"  # info: set word
        bits.append(f"Battery {bank['soc']} percent across {bank.get('count')} live {word}")  # info: bits . append charge
    watts = []  # info: set watts
    if bank.get("solar_w") is not None:  # info: if solar present
        watts.append(f"solar input {spoken_watts(bank['solar_w'])}")  # info: watts . append solar
    if bank.get("ac_out_w") is not None:  # info: if AC present
        watts.append(f"AC out {spoken_watts(bank['ac_out_w'])}")  # info: watts . append AC
    if bank.get("usbc_out_w") is not None:  # info: if USB-C present
        watts.append(f"USB-C out {spoken_watts(bank['usbc_out_w'])}")  # info: watts . append USB-C
    if watts:  # info: if watts
        bits.append(", ".join(watts))  # info: bits . append watts
    return (". ".join(bits) + ".") if bits else ""  # info: return sentence


# ====================================================
# SECTION: function b_solar_desk
# What it does: Combined energy+solar desk: packs, sun times, newest ch1 still, and this hour's camera look (refreshes when needed).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def wake_stale_packs(t: datetime) -> None:  # info: def wake_stale_packs
    """Run the existing EcoFlow read once when a live pack sample is past the speak threshold."""  # info: docstring
    facts = energy_facts(t)  # info: set facts
    stale = [f for f in facts if f.get("ok") and not f.get("off") and isinstance(f.get("age_min"), int) and f["age_min"] > STALE_MIN]  # info: set stale
    if not stale:  # info: if not stale
        return  # info: return
    script = PACIFIC / "Energy" / "scripts" / "read" / "leapfrog-read.sh"  # info: set script
    if not script.is_file():  # info: if not script . is_file
        return  # info: return
    try:  # info: try
        subprocess.run(["bash", str(script)], timeout=120, check=False)  # info: subprocess . run the existing read
    except (OSError, subprocess.TimeoutExpired):  # info: except
        return  # info: return


def b_solar_desk(t: datetime):  # info: def b_solar_desk
    """Combined energy+solar desk: packs, sun times, newest ch1 still, and this hour's camera look (refreshes when needed)."""  # info: docstring
    wake_stale_packs(t)  # info: wake a stagnant pack before the desk speaks
    facts = energy_facts(t)  # info: set facts
    sun = jload(ENERGY / "sun" / "sun-times_current.json") or {}  # info: set sun
    sp = ["Solar desk.", generated_at(t)]  # info: set sp
    lines, spoken_lines = [], []  # info: lines , spoken_lines = [ ] , [
    for f in facts:  # info: for f in facts :
        if not f["ok"]:  # info: if not f [ "ok" ] :
            lines.append(f"{f['name']}: offline")  # info: lines . append ( f" { f [
            spoken_lines.append(f"{f['name']}: offline")  # info: spoken_lines . append ( f" { f [
            continue  # info: continue
        if f.get("off"):  # info: if f . get ( "off" ) :
            lines.append(off_sentence(f))  # info: lines . append ( off_sentence ( f ) )
            spoken_lines.append(off_sentence(f).rstrip("."))  # info: spoken_lines . append ( off_sentence ( f ) . rstrip ( "." ) )
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
        age_bit = reading_age_clause(f).lstrip(", ")  # info: set age_bit
        if age_bit:  # info: if age_bit :
            bits.append(age_bit)  # info: bits . append ( age_bit )
            sbits.append(age_bit)  # info: sbits . append ( age_bit )
        lines.append(f"{f['name']}: " + ", ".join(bits))  # info: lines . append ( f" { f [
        spoken_lines.append(f"{f['name']}: " + ", ".join(sbits))  # info: spoken_lines . append ( f" { f [
    if ble_voice_on():  # info: pack speech only when BLE voice is on
        if not any(f["ok"] for f in facts):  # info: if not any ( f [ "ok" ]
            sp.append("EcoFlow is offline.")  # info: sp . append ( "EcoFlow is offline." )
        else:  # info: else :
            for f in facts:  # info: for f in facts
                if not f.get("ok"):  # info: if not f . get ( "ok" )
                    sp.append(f"{f['name']}: offline.")  # info: sp . append missing pack
                elif f.get("off"):  # info: elif f . get ( "off" )
                    sp.append(off_sentence(f))  # info: sp . append powered-off pack
            bank = merged_battery(facts)  # info: set bank
            if bank:  # info: if bank
                spoken = bank_spoken(bank)  # info: set spoken
                if spoken:  # info: if spoken
                    sp.append(spoken)  # info: sp . append merged battery
                lines.insert(0, spoken.rstrip("."))  # info: lines . insert merged battery
                if bank.get("soc") is not None:  # info: if bank . get ( "soc" ) is not None
                    say_change(sp, "energy.bank.soc", bank["soc"], "Battery", t)  # info: say_change bank charge
                if bank.get("solar_w") is not None:  # info: if bank . get ( "solar_w" ) is not None
                    say_change(sp, "energy.solar_total", bank["solar_w"], "Solar input", t)  # info: say_change solar total
                out = sum(x for x in (bank.get("ac_out_w"), bank.get("usbc_out_w")) if isinstance(x, (int, float)))  # info: set out
                if bank.get("ac_out_w") is not None or bank.get("usbc_out_w") is not None:  # info: if output watts are present
                    say_change(sp, "energy.bank.output_w", out, "Battery output", t)  # info: say_change bank output
            for f in facts:  # info: for f in facts :
                note = range_clause(f)  # info: set note
                if note:  # info: if note :
                    sp.append(note)  # info: sp . append ( note )
    else:  # info: else BLE pack lines held off
        notice = (  # info: set notice
            "EcoFlow Bluetooth and connection have become programmatically unreliable, "
            "and live statuses will not be available at this time."
        )  # info: )
        sp.append(notice)  # info: speak the hold notice
        lines.insert(0, notice.rstrip("."))  # info: lines . insert hold notice
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
    if str(PACIFIC) not in sys.path:  # info: if str ( PACIFIC ) not in sys . path
        sys.path.insert(0, str(PACIFIC))  # info: sys . path . insert ( 0 , str ( PACIFIC ) )
    from Energy.db.report_json import REPORT_JSON, period_lines  # info: from Energy . db . report_json import REPORT_JSON
    try:  # info: try
        periods = period_lines(json.loads(REPORT_JSON.read_text(encoding="utf-8")))  # info: set periods
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        periods = []  # info: set periods
    for line in periods:  # info: for line in periods
        extra.append(f"- {line}")  # info: extra . append the closed window
    # Hour batch: grab a live ch1 frame, then force Gemma look (do not reuse a pre-sunrise IR cache).
    if os.environ.get("RR_HOUR_BATCH", "0") == "1":  # info: if hour batch
        cam = PACIFIC / "Security" / "Cameras"  # info: set cam
        if str(cam) not in sys.path:  # info: if cam path missing
            sys.path.insert(0, str(cam))  # info: insert cam path
        try:  # info: try live grab with short retries (10s grab job may hold the lock)
            import grab_frame  # info: import grab_frame
            for _attempt in range(12):  # info: for _attempt in range ( 12 )
                try:  # info: try
                    grab_frame.grab_jpeg(channel=1)  # info: grab live ch1
                    break  # info: break on success
                except grab_frame.FramesBusy:  # info: except FramesBusy
                    time.sleep(0.5)  # info: wait for frame-grab job
        except Exception:  # noqa: BLE001
            pass  # info: keep newest on-disk still if grab fails
        try:  # info: try forced look
            import panel_look  # info: import panel_look
            panel_look.observe(t, force=True)  # info: force live look this hour
        except Exception:  # noqa: BLE001
            camera_observation(t)  # info: fall back to normal hour look
    else:  # info: else normal desk
        camera_observation(t)  # info: refresh this hour's ch1 look (was energy_report)
    still = newest_ch1(t)  # info: set still after any live grab
    if still:  # info: if still :
        name = Path(still["path"]).name  # info: set name
        if still["age_min"] > 0:  # info: if still [ "age_min" ] > 0 :
            extra.append(f"- Solar panel still age: {still['age_min']} min (`{name}`)")  # info: extra . append still age
            unit = "minute" if still["age_min"] == 1 else "minutes"  # info: set unit
            sp.append(f"Solar panel still is {still['age_min']} {unit} old.")  # info: sp . append still age once
        else:  # info: else :
            extra.append(f"- Solar panel still: current (`{name}`)")  # info: extra . append current still
    else:  # info: else :
        extra.append("- Solar panel still: not on file")  # info: extra . append missing still
        sp.append("No solar panel still on file.")  # info: sp . append missing still
    look = last_camera_look(t)  # info: set look
    sentence = str(look.get("sentence") or "")  # info: set sentence
    if sentence:  # info: if sentence :
        extra.append(f"- {sentence}")  # info: extra . append sentence
        sp.append(sentence)  # info: sp . append sentence
        if look.get("hour") != t.strftime("%Y-%m-%dT%H") and look.get("age_min") is not None:  # info: if look hour stale
            extra.append(f"- Camera look age: {look['age_min']} min ({look.get('at')})")  # info: extra age
            unit = "minute" if look["age_min"] == 1 else "minutes"  # info: set unit
            sp.append(f"That camera look is {look['age_min']} {unit} old.")  # info: sp age
    else:  # info: else :
        extra.append("- Camera look: not on file")  # info: extra missing
        sp.append("No solar panel camera look on file.")  # info: sp missing
    md = [f"# Solar desk — {t.isoformat()}", ""] + [f"- {x}" for x in lines] + [
        f"- Sun: {sun.get('sunrise', 'n/a')} / {sun.get('sunset', 'n/a')} ({sun.get('date', 'n/a')}, Open-Meteo)",  # info: f" - Sun: { sun . get ( 'sunrise'
    ] + extra + ["", "## Spoken", "", " ".join(sp), "",  # info: ] + extra + [ "" , "## Spoken" , "" , " " . join ( sp ) , "" ,
        "_Source: Energy/layers/periods.json, Energy/sun/sun-times_current.json, the newest ch1 still, and Energy/vision/ch1-look-last.json"
        + (
            " (EcoFlow pack lines on when RR_VOICE_BLE=1)."
            if ble_voice_on()
            else " (EcoFlow Bluetooth and connection programmatically unreliable; live statuses held off)."
        )
        + "_",
        "",
    ]  # info: source footer
    return "\n".join(md), sp  # info: return "\n" . join ( md ) ,


# ====================================================
# SECTION: function b_security_desk
# What it does: G1 host_metrics.security_spoken, unchanged wording, from host_desks.security_snapshot() (counts only).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_security_desk(t: datetime):  # info: def b_security_desk
    """G1 host_metrics.security_spoken, unchanged wording, from host_desks.security_snapshot() (counts only)."""  # info: """G1 host_metrics.security_spoken, unchanged wording, from host_desks.security_snapshot() (counts only)."""
    row = _host_desks().security_snapshot()  # info: set row
    bits = ["Security desk.", generated_at(t)]  # info: set bits
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
        say_change(bits, "security.listen_tcp", row["listen_tcp"], "TCP listeners", t)  # info: say_change listeners
    if row.get("established") is not None:  # info: if row . get ( "established" ) is
        bits.append(f"{row['established']} established connections.")  # info: bits . append ( f" { row [
        say_change(bits, "security.established", row["established"], "Established connections", t)  # info: say_change connections
    if row.get("failed_1h") is not None:  # info: if row . get ( "failed_1h" ) is
        bits.append(f"Failed sign-ins: {row['failed_1h']} in the last hour, {row['failed_24h']} in the last twenty four hours.")  # info: bits . append ( f" Failed sign-ins: { row
        say_change(bits, "security.failed_1h", row["failed_1h"], "Failed sign-ins in the last hour", t)  # info: say_change failed hour
        say_change(bits, "security.failed_24h", row.get("failed_24h"), "Failed sign-ins in twenty four hours", t)  # info: say_change failed day
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
# What it does: Host byte samples (last hour / 24 h) plus Mainland Home/Radio site analytics from the desk bank.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_bandwidth_desk(t: datetime):  # info: def b_bandwidth_desk
    """Host byte samples (last hour / 24 h) plus Mainland Home/Radio site analytics from the desk bank."""  # info: docstring
    hd = _host_desks()  # info: set hd
    net = hd.net_counters()  # info: set net
    if net and not os.environ.get("RR_VOICE_BANDWIDTH_DRY"):  # info: if net and not os . environ . get ( "RR_VOICE_BANDWIDTH_DRY" )
        hd.append_net_sample(net)  # info: hd . append_net_sample ( net )
    hour, day = hd.net_usage_window(3600, now=net), hd.net_usage_window(86400, now=net)  # info: hour , day = hd . net_usage_window
    site = site_analytics_doc(t, refresh=True)  # info: set site
    md = [f"# Bandwidth desk — {t.isoformat()}", "", "## Host link", "",  # info: set md header
          f"- iface: {(net or {}).get('iface')} ({(net or {}).get('link')})",  # info: iface line
          f"- last hour: {hour}", f"- last 24 h: {day}", "", "## Site traffic (Mainland analytics)", ""]  # info: host + site headings
    md += site_traffic_md_lines(site) + [""]  # info: md += site traffic bullets
    bits = ["Bandwidth desk.", generated_at(t), f"This host is on {(net or {}).get('link') or 'network'}."]  # info: set bits
    if hour is None and day is None:  # info: if hour is None and day is None
        md.append("_Not enough host samples yet (needs samples covering 45 min; run `host_desks.py net-sample` every 5 min)._")  # info: md . append host sample note
        bits.append("Bandwidth data is not on file yet.")  # info: bits . append missing host bandwidth
    else:  # info: else :
        sb = hd.spoken_bytes  # info: set sb
        bits.append(f"Last hour: {sb(hour['rx'])} down, {sb(hour['tx'])} up, {sb(hour['total'])} total." if hour else "Last hour is not on file yet.")  # info: bits . append hour
        if hour:  # info: if hour
            say_change(bits, "bandwidth.hour_total", hour["total"], "Last hour total", t)  # info: say_change hour total
        bits.append(f"Last twenty four hours: {sb(day['rx'])} down, {sb(day['tx'])} up, {sb(day['total'])} total." if day  # info: bits . append day
                    else "Last twenty four hours is not on file yet.")  # info: else day missing
        if day:  # info: if day
            say_change(bits, "bandwidth.day_total", day["total"], "Last twenty four hour total", t)  # info: say_change day total
    bits += site_traffic_spoken(site, t)  # info: bits += site traffic spoken
    md += ["## Spoken", "", " ".join(bits), "",  # info: md += spoken
           "_Sources: Pacific System/scripts/host_desks.py (host iface bytes); Database Logs/Website/analytics/daily (ML2 API + radio samples via analytics_pull / pull-from-api.sh). Home pageviews stay null until edge analytics; home_proxy is telemetry Referer www only._", ""]  # info: source footer
    return "\n".join(md), bits  # info: return join md bits

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
    facts, (rows, _), (today, _), h, (tasks, per) = energy_facts(t), alerts(), sfp_today(), host(), open_tasks()  # info: call facts
    sp = [title, generated_at(t), DEV_NOTE + "."]  # info: set sp
    lines = []  # info: set lines
    ok = [f for f in facts if f["ok"] and not f.get("off")]  # info: set ok
    off = [f for f in facts if f.get("off")]  # info: set off
    if ok:  # info: if ok :
        s = "Batteries: " + ", ".join(f"{f['name']} {f['soc']}%" for f in ok)  # info: set s
        solar = sum(f["solar_w"] or 0 for f in ok)  # info: set solar
        # spoken form says "at": "Delta 2 36%" would hit the G1 clock rule ("two thirty six a.m.")
        sp.append("Battery levels: " + ", ".join(f"{f['name']} at {f['soc']}%" for f in ok) + f". Solar input {spoken_watts(solar)}.")  # info: sp . append ( "Battery levels: " + ", " .
        for f in ok:  # info: for f in ok
            if f.get("key"):  # info: if f . get ( "key" )
                say_change(sp, f"energy.{f['key']}.soc", f["soc"], f"{f['name']} state of charge", t)  # info: say_change soc
        say_change(sp, "energy.solar_total", solar, "Solar input", t)  # info: say_change solar total
        lines.append(s + f"; solar input {solar} W")  # info: lines . append ( s + f" ; solar input
    elif not off and ble_voice_on():  # info: elif packs expected and BLE voice on
        sp.append("EcoFlow is offline.")  # info: sp . append ( "EcoFlow is offline." )
        lines.append("EcoFlow: no reading")  # info: lines . append ( "EcoFlow: no reading" )
    for f in off:  # info: for f in off :
        sp.append(off_sentence(f))  # info: sp . append ( off_sentence ( f ) )
        lines.append(off_sentence(f))  # info: lines . append ( off_sentence ( f ) )
    if rows:  # info: if rows :
        sp.append(f"{len(rows)} active weather alert{'s' if len(rows) != 1 else ''}, including {rows[0]['event']}.")  # info: sp . append ( f" { len (
        say_change(sp, "nws.alerts", len(rows), "Active alerts", t)  # info: say_change alerts
    else:  # info: else :
        sp.append("No active HI alerts from the API sample.")  # info: sp . append ( "No active HI alerts from the API sample." )
        say_change(sp, "nws.alerts", 0, "Active alerts", t)  # info: say_change alerts
    lines.append(f"NWS alerts active: {len(rows)}" + (f" ({', '.join(r['event'] for r in rows)})" if rows else ""))  # info: lines . append ( f" NWS alerts active: { len
    if today:  # info: if today :
        first = re.split(r"(?<=\.)\s", today.split(":", 1)[1].strip())[0]  # info: set first
        sp.append(f"Forecast for {today.split(':', 1)[0].lower()}: {first}")  # info: sp . append ( f" Forecast for { today
        lines.append(f"Forecast {today}")  # info: lines . append ( f" Forecast { today
    sp.append(f"Host CPU {h['cpu']}%, memory {h['mem']}% used.")  # info: sp . append ( f" Host CPU { h
    say_change(sp, "system.cpu_pct", h["cpu"], "CPU", t)  # info: say_change cpu
    say_change(sp, "system.mem_pct", h["mem"], "Memory", t)  # info: say_change memory
    lines.append(f"Host CPU {h['cpu']}%, memory {h['mem']}% used")  # info: lines . append ( f" Host CPU { h
    sp.append(f"{tasks} open work order items.")  # info: sp . append ( f" { tasks }
    say_change(sp, "tasks.open", tasks, "Open work orders", t)  # info: say_change open tasks
    lines.append(f"Open work-order items: {tasks}")  # info: lines . append ( f" Open work-order items: { tasks
    summary = llm_summary(lines) if os.environ.get("RR_VOICE_ROLLUP_LLM", "0") == "1" else None  # info: set summary
    if summary:  # info: if summary :
        sp.append(summary)  # info: sp . append ( summary )
    sp.append("End of report.")  # info: sp . append ( "End of report." )
    md = [f"# {title[:-1]} — {t.isoformat()}", "", DEV_NOTE, "", "## Measured", ""] + [f"- {x}" for x in lines]
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
    from speakable import speakable  # info: from speakable import speakable
    t = _UGC.sub("", _WMO_HEAD.sub("", " ".join((text or "").split())))  # info: set t
    t = re.sub(r"\*\*|-{3,}|\s\*\s", " ", t)  # info: set t
    return speakable(t)  # info: return speakable (also strips SUBTRACT / coords / long ids)


# ====================================================
# SECTION: function official_products
# What it does: [{type, text, issued, age_h}] newest-first candidates: HLS (official/), HWO, AFD (poller).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def official_products(t: datetime) -> list[dict]:  # info: def official_products
    """[{type, text, issued, age_h}] newest-first candidates: HLS (official/), HWO, AFD (poller)."""  # info: """[{type, text, issued, age_h}] newest-first candidates: HLS (official/), HWO, AFD (poller)."""
    out = []  # info: set out
    st = jload(OFFICIAL / "official_current.json") or jload(OFFICIAL / "official-last.json") or {}  # info: set st
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
    k = jload(VOLCANOES / "kilauea_current.json") or {}  # info: set k
    storms = [x for x in hurricane_facts(t) if x.get("active")]  # info: set storms
    b = datetime.fromisoformat(boot_at)  # info: set b
    sp = [f"Boot report, {kind} edition.", generated_at(t),  # info: set sp
          (f"The Pacific desk came up at {spoken_clock(b.hour, b.minute)}, {up_min} minutes ago." if up_min < 120 else  # info: call (
           f"The Pacific desk came up at {spoken_clock(b.hour, b.minute)}, about {round(up_min / 60)} hours ago.")  # info: f" The Pacific desk came up at { spoken_clock ( b . hour
          if up_min < 1440 else f"The Pacific desk has been up {up_min // 1440} days."]  # info: if up_min < 1440 else f" The Pacific desk has been up {
    lines = [f"Kind: {kind}", f"Boot: {boot_at} (up {up_min} min)", f"Host CPU {h['cpu']}%, memory {h['mem']}% used"]  # info: set lines
    ok = [f for f in facts if f["ok"] and not f.get("off")]  # info: set ok
    off = [f for f in facts if f.get("off")]  # info: set off
    if ok:  # info: if ok :
        sp.append("Battery levels: " + ", ".join(f"{f['name']} at {f['soc']}%" for f in ok) + ".")  # info: sp . append ( "Battery levels: " + ", " .
        lines.append("Batteries: " + ", ".join(f"{f['name']} {f['soc']}%" for f in ok))  # info: lines . append ( "Batteries: " + ", " .
    elif not off and ble_voice_on():  # info: elif packs expected and BLE voice on
        sp.append("EcoFlow is offline."); lines.append("Batteries: offline")  # info: sp . append ( "EcoFlow is offline." ) ; lines
    for f in off:  # info: for f in off :
        sp.append(off_sentence(f))  # info: sp . append ( off_sentence ( f ) )
        lines.append(off_sentence(f))  # info: lines . append ( off_sentence ( f ) )
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
# What it does: Full current summary of every measured desk, stamped with the clock when the text is built.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_current_report(t: datetime):  # info: def b_current_report
    """Full current summary of every measured desk. The heading is the clock when the text is built."""  # info: docstring
    facts = energy_facts(t)  # info: set facts
    sun = jload(ENERGY / "sun" / "sun-times_current.json") or {}  # info: set sun
    moon = jload(DB / "Weather" / "moon" / "moon_current.json") or jload(ENERGY / "moon" / "moon-last.json") or {}  # info: Weather first
    rows, upd = alerts()  # info: rows , upd = alerts ( )
    issued, groups = sfp_read()  # info: issued , groups = sfp_read ( )
    places = zfp_temps()  # info: set places
    quakes = quake_facts(t)  # info: set quakes
    kilauea = jload(VOLCANOES / "kilauea_current.json") or {}  # info: set kilauea
    mauna = jload(VOLCANOES / "mauna-loa_current.json") or {}  # info: set mauna
    storms = [s for s in hurricane_facts(t) if s.get("active")]  # info: set storms
    import system_perf  # info: import system_perf
    perf = system_perf.sample()  # info: set perf
    desks = _host_desks()  # info: set desks
    sec = desks.security_snapshot()  # info: set sec
    net = desks.net_counters()  # info: set net
    bw_hour, bw_day = desks.net_usage_window(3600, now=net), desks.net_usage_window(86400, now=net)  # info: bw_hour , bw_day = desks . net_usage_window
    still, look = newest_ch1(t), last_camera_look(t)  # info: still , look = newest_ch1 ( t ) , last_camera_look ( t )
    tasks, _per = open_tasks()  # info: tasks , _per = open_tasks ( )
    fresh = [p for p in official_products(t) if p.get("age_h") is not None and p["age_h"] <= OFFICIAL_MAX_H]  # info: set fresh
    md = [f"# Current report — {t.isoformat()}", "", DEV_NOTE, ""]  # info: set md
    sp = ["Current report.", generated_at(t), DEV_NOTE + "."]  # info: set sp
    md += ["## Energy", ""]  # info: md += energy heading
    ok = [f for f in facts if f.get("ok") and not f.get("off")]  # info: set ok
    off = [f for f in facts if f.get("off")]  # info: set off
    if ok:  # info: if ok :
        bank = merged_battery(facts)  # info: set bank
        spoken = bank_spoken(bank) if bank else ""  # info: set spoken
        if spoken:  # info: if spoken
            sp.append(spoken)  # info: sp . append merged battery
            md.append(f"- {spoken.rstrip('.')}")  # info: md . append merged battery
        if bank and bank.get("soc") is not None:  # info: if bank and bank . get ( "soc" ) is not None
            say_change(sp, "energy.bank.soc", bank["soc"], "Battery", t)  # info: say_change bank charge
        if bank and bank.get("solar_w") is not None:  # info: if bank and bank . get ( "solar_w" ) is not None
            say_change(sp, "energy.solar_total", bank["solar_w"], "Solar input", t)  # info: say_change solar total
        for f in ok:  # info: for f in ok :
            age_bit = reading_age_clause(f).lstrip(", ")  # info: set age_bit
            if age_bit:  # info: if age_bit :
                sp.append(f"{f['name']} {age_bit}.")  # info: sp . append ( f" { f [ 'name' ] } { age_bit } . " )
    elif not off and ble_voice_on():  # info: elif packs expected and BLE voice on
        sp.append("EcoFlow is offline.")  # info: sp . append ( "EcoFlow is offline." )
    for f in off:  # info: for f in off :
        sp.append(off_sentence(f))  # info: sp . append ( off_sentence ( f ) )
    if not ble_voice_on():  # info: note BLE hold in markdown only
        md.append("- EcoFlow Bluetooth and connection have become programmatically unreliable; live statuses not available (RR_VOICE_BLE=0).")  # info: md note
    for f in facts:  # info: for f in facts :
        if not f.get("ok"):  # info: if not f . get ( "ok" ) :
            md.append(f"- {f['name']}: no reading")  # info: md . append ( f" - { f [ 'name' ] } : no reading " )
            continue  # info: continue
        if f.get("off"):  # info: if f . get ( "off" ) :
            md.append(f"- {f['name']}: discharged and powered off, last {f['soc']}%")  # info: md . append ( f" - { f [ 'name' ] } : discharged and powered off, last { f [ 'soc' ] } % " )
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
    if sun.get("date") == t.date().isoformat() and sun.get("sunrise") and sun.get("sunset"):  # info: if sun . get ( "date" ) == t . date
        sp.append(f"Sunrise {spoken_hhmm(sun['sunrise'])}, sunset {spoken_hhmm(sun['sunset'])}.".replace("..", "."))  # info: sp . append sun sentence
    else:  # info: else :
        sp.append("Sun times for today are not on file.")  # info: sp . append ( "Sun times for today are not on file." )
    if moon.get("phase_name"):  # info: if moon . get ( "phase_name" ) :
        sp.append(f"Moon is {moon['phase_name']}, {moon.get('illumination', 'n/a')} percent lit.")  # info: sp . append moon sentence
    else:  # info: else :
        sp.append("Moon phase is not on file.")  # info: sp . append ( "Moon phase is not on file." )
    md += ["", "## Weather", ""]  # info: md += weather heading
    # Hour batch already aired nws_weather immediately before this desk — keep md, skip spoken NWS.
    speak_weather = os.environ.get("RR_HOUR_BATCH", "0") != "1"  # info: speak_weather false when hour batch stitches nws_weather first
    if rows:  # info: if rows :
        md += [f"- {r['event']} — {r['area']}" for r in rows]  # info: md += alert lines
        if speak_weather:  # info: if speak_weather :
            sp.append(f"{len(rows)} active weather alert{'s' if len(rows) != 1 else ''}, including {rows[0]['event']}.")  # info: sp . append alert sentence
            say_change(sp, "nws.alerts", len(rows), "Active alerts", t)  # info: say_change alerts
    else:  # info: else :
        md.append("- No active Hawaii alerts")  # info: md . append ( "- No active Hawaii alerts" )
        if speak_weather:  # info: if speak_weather :
            sp.append("No active Hawaii alerts.")  # info: sp . append ( "No active Hawaii alerts." )
            say_change(sp, "nws.alerts", 0, "Active alerts", t)  # info: say_change alerts
    today = None  # info: set today
    if groups and groups[0]["periods"]:  # info: if groups and groups [ 0 ] [ "periods" ] :
        label, body = groups[0]["periods"][0]  # info: label , body = groups [ 0 ] [ "periods" ] [ 0 ]
        today = f"{label}: {body}"  # info: set today
    md.append(f"- State forecast ({issued or 'n/a'}): {today or 'not on file'}")  # info: md . append forecast line
    if today and speak_weather:  # info: if today and speak_weather :
        sp.append(f"Forecast for {today.split(':', 1)[0].lower()}: {re.split(r'(?<=[.]) ', today.split(':', 1)[1].strip())[0]}")  # info: sp . append forecast sentence
    if places:  # info: if places :
        for p in places:  # info: for p in places :
            bits = []  # info: set bits
            if p.get("high"):  # info: if p . get ( "high" ) :
                bits.append(f"high {p['high']}")  # info: bits . append ( f" high { p [ 'high' ] } " )
            if p.get("low"):  # info: if p . get ( "low" ) :
                bits.append(f"low {p['low']}")  # info: bits . append ( f" low { p [ 'low' ] } " )
            md.append(f"- {p['place']}: " + ", ".join(bits))  # info: md . append place line
        if speak_weather:  # info: if speak_weather :
            sp.append("Temperatures. " + ". ".join(f"{p['place']} high {p['high'] or 'n/a'}, low {p['low'] or 'n/a'}" for p in places) + ".")  # info: sp . append temperature sentence
            for p in places:  # info: for p in places
                if p.get("high"):  # info: if p . get ( "high" )
                    say_change(sp, f"nws.{p['place']}.high", p["high"], f"{p['place']} high", t)  # info: say_change high
                if p.get("low"):  # info: if p . get ( "low" )
                    say_change(sp, f"nws.{p['place']}.low", p["low"], f"{p['place']} low", t)  # info: say_change low
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
        local_m25 = len(_m25(list(hi_pack.get("events") or [])))  # info: set local_m25
        sp.append(f"Local earthquakes, last twenty four hours: {local_m25} magnitude 2.5 or greater.")  # info: sp . append quake sentence
        say_change(sp, "quake.hawaii.m25", local_m25, "Local magnitude 2.5 count", t)  # info: say_change local quakes
    else:  # info: else :
        sp.append("Local earthquake data is not on file.")  # info: sp . append ( "Local earthquake data is not on file." )
    if isinstance(kilauea, dict) and kilauea.get("alert_level"):  # info: if isinstance ( kilauea , dict ) and kilauea . get ( "alert_level" ) :
        md.append(f"- Kilauea: {kilauea.get('alert_level')} / {kilauea.get('color_code')}, erupting {kilauea.get('erupting')}")  # info: md . append kilauea line
        sp.append(f"Kilauea alert level {str(kilauea.get('alert_level')).lower()}" + (", erupting." if kilauea.get("erupting") else "."))  # info: sp . append kilauea sentence
    else:  # info: else :
        md.append("- Kilauea: not on file")  # info: md . append ( "- Kilauea: not on file" )
        sp.append("Kilauea status is not on file.")  # info: sp . append ( "Kilauea status is not on file." )
    photo_line = kilauea_photo_summary()  # info: set geology photo line
    md.append(f"- Kilauea photo: {photo_line}")  # info: md . append kilauea photo line
    # Hour batch: image check + kilauea desk own the photo — do not say it a third time here.
    if os.environ.get("RR_HOUR_BATCH", "0") != "1":  # info: if not hour batch
        sp.append(photo_line)  # info: sp . append kilauea photo line
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
    conn, conn_say = system_perf.connectivity_lines(t)  # info: set conn , conn_say
    if conn.get("last_online_at"):  # info: if conn . get ( "last_online_at" )
        md.append(f"- Root server last online: {conn['last_online_at']}")  # info: md . append last online
    if isinstance(conn.get("uptime_pct"), int):  # info: if isinstance
        md.append(f"- Uptime percent: {conn['uptime_pct']}%")  # info: md . append uptime percent
    if isinstance(conn.get("avg_offline_s"), int):  # info: if isinstance
        md.append(f"- Average offline: {conn['avg_offline_s']} s")  # info: md . append average offline
    host_say = f"Host CPU {round(perf['cpu_pct'])}%, memory {round(perf['mem_pct'])}% used, disk {round(perf['disk_pct'])}% used."  # info: set host_say
    if perf.get("temp_c") is not None:  # info: if perf . get ( "temp_c" ) is not None :
        md.append(f"- Temperature {perf['temp_c']} C")  # info: md . append temp line
        host_say = host_say[:-1] + f", temperature {perf['temp_c']} degrees Celsius."  # info: set host_say
    sp.append(host_say)  # info: sp . append ( host_say )
    sp.extend(conn_say)  # info: sp . extend connectivity lines
    mode_row, mode_say = system_perf.power_lines()  # info: set mode_row , mode_say
    if mode_say:  # info: if mode_say
        md.append(f"- Host power mode: {mode_row.get('mode')}")  # info: md . append power mode
        sp.append(mode_say)  # info: sp . append power mode
    say_change(sp, "system.cpu_pct", round(perf["cpu_pct"]), "CPU", t)  # info: say_change cpu
    say_change(sp, "system.mem_pct", round(perf["mem_pct"]), "Memory", t)  # info: say_change memory
    say_change(sp, "system.disk_pct", round(perf["disk_pct"]), "Disk", t)  # info: say_change disk
    if perf.get("temp_c") is not None:  # info: if perf . get ( "temp_c" ) is not None
        say_change(sp, "system.temp_c", perf["temp_c"], "Temperature", t)  # info: say_change temperature
    md += ["", "## Security", ""]  # info: md += security heading
    md.append(f"- Firewall starts on boot: {sec.get('ufw_boot')}")  # info: md . append firewall line
    md.append(f"- SSH active: {sec.get('ssh_active')}")  # info: md . append ssh line
    md.append(f"- TCP listeners: {sec.get('listen_tcp')}")  # info: md . append listeners line
    md.append(f"- Established connections: {sec.get('established')}")  # info: md . append connections line
    md.append(f"- Failed sign-ins, last hour / 24 h: {sec.get('failed_1h')} / {sec.get('failed_24h')}")  # info: md . append failed sign-ins
    if sec.get("failed_1h") is not None:  # info: if sec . get ( "failed_1h" ) is not None :
        sp.append(f"Security. Failed sign-ins {sec.get('failed_1h')} in the last hour, {sec.get('failed_24h')} in the last twenty four hours.")  # info: sp . append security sentence
        say_change(sp, "security.failed_1h", sec.get("failed_1h"), "Failed sign-ins in the last hour", t)  # info: say_change failed hour
        say_change(sp, "security.failed_24h", sec.get("failed_24h"), "Failed sign-ins in twenty four hours", t)  # info: say_change failed day
        say_change(sp, "security.listen_tcp", sec.get("listen_tcp"), "TCP listeners", t)  # info: say_change listeners
        say_change(sp, "security.established", sec.get("established"), "Established connections", t)  # info: say_change connections
    else:  # info: else :
        sp.append("The sign-in log is not readable.")  # info: sp . append ( "The sign-in log is not readable." )
    md += ["", "## Bandwidth", ""]  # info: md += bandwidth heading
    if bw_hour or bw_day:  # info: if bw_hour or bw_day :
        if bw_hour:  # info: if bw_hour :
            md.append(f"- Last hour: {bw_hour['rx']} bytes down, {bw_hour['tx']} bytes up")  # info: md . append hour bytes
            sp.append(f"Last hour bandwidth: {desks.spoken_bytes(bw_hour['rx'])} down, {desks.spoken_bytes(bw_hour['tx'])} up.")  # info: sp . append hour bandwidth
            say_change(sp, "bandwidth.hour_total", bw_hour["total"], "Last hour total", t)  # info: say_change hour total
        if bw_day:  # info: if bw_day :
            md.append(f"- Last 24 h: {bw_day['rx']} bytes down, {bw_day['tx']} bytes up")  # info: md . append day bytes
            say_change(sp, "bandwidth.day_total", bw_day["total"], "Last twenty four hour total", t)  # info: say_change day total
    else:  # info: else :
        md.append("- Not enough samples yet")  # info: md . append ( "- Not enough samples yet" )
        sp.append("Bandwidth data is not on file yet.")  # info: sp . append ( "Bandwidth data is not on file yet." )
    site = site_analytics_doc(t, refresh=True)  # info: set site
    md += ["", "## Site traffic (Mainland analytics)", ""] + site_traffic_md_lines(site)  # info: md += site traffic section
    sp += site_traffic_spoken(site, t)  # info: sp += site traffic spoken
    md += ["", "## Camera", ""]  # info: md += camera heading
    # Hour batch already has solar_desk speaking still age — keep md only here to avoid saying it twice.
    speak_still = os.environ.get("RR_HOUR_BATCH", "0") != "1"  # info: speak_still false when hour batch includes solar_desk
    if still:  # info: if still :
        md.append(f"- Solar panel still age: {still['age_min']} min")  # info: md . append still age
        if speak_still:  # info: if speak_still :
            sp.append(f"Solar panel still is {still['age_min']} minutes old." if still["age_min"] else "Solar panel still is current.")  # info: sp . append still sentence
    else:  # info: else :
        md.append("- Solar panel still: not on file")  # info: md . append ( "- Solar panel still: not on file" )
        if speak_still:  # info: if speak_still :
            sp.append("No solar panel still on file.")  # info: sp . append ( "No solar panel still on file." )
    if look.get("sentence"):  # info: if look . get ( "sentence" ) :
        md.append(f"- {look['sentence']}")  # info: md . append ( f" - { look [ 'sentence' ] } " )
        if speak_still:  # info: if speak_still (solar_desk owns the look on hour batch)
            sp.append(look["sentence"])  # info: sp . append ( look [ "sentence" ] )
    md += ["", "## Official weather", ""]  # info: md += official heading
    if fresh:  # info: if fresh :
        pick = fresh[0]  # info: set pick
        md.append(f"- {pick['type']}, age {pick['age_h']} h")  # info: md . append official line
        sp.append(f"Official weather product {pick['type']} is on file.")  # info: sp . append official sentence
    else:  # info: else :
        md.append("- No fresh Honolulu statement")  # info: md . append ( "- No fresh Honolulu statement" )
        sp.append("No fresh Honolulu weather statement is on file.")  # info: sp . append ( "No fresh Honolulu weather statement is on file." )
    md += ["", "## Work orders", "", f"- Open items: {tasks}", ""]  # info: md += work orders
    sp.append(f"{tasks} open work order items.")  # info: sp . append open tasks
    say_change(sp, "tasks.open", tasks, "Open work orders", t)  # info: say_change open tasks
    sp.append("End of current report.")  # info: sp . append end
    md += ["## Spoken", "", " ".join(sp), ""]  # info: md += spoken
    return "\n".join(md), sp  # info: return "\n" . join ( md ) , sp


# ====================================================
# SECTION: function b_custom_msg
# What it does: Bruce desk — speak Database Media/Audio/Voice/custom_msg_current.txt. Reads that exact path every run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def b_custom_msg(t: datetime):  # info: def b_custom_msg
    """Bruce desk — speak custom_msg_current.txt from the fixed Voice bank path every run."""  # info: docstring
    path = CUSTOM_MSG  # info: exact path every time
    md = [f"# Custom message — {t.isoformat()}", "", f"_Source: `{path}` (read every run)._", ""]  # info: set md
    if not path.is_file():  # info: if not path . is_file ( )
        spoken = ["Custom message file is missing."]  # info: set spoken
        md += ["_File missing._", "", "## Spoken", "", spoken[0], ""]  # info: md += missing
        return "\n".join(md), spoken  # info: return missing
    text = path.read_text(encoding="utf-8", errors="replace")  # info: set text
    spoken = [ln.strip() for ln in text.splitlines() if ln.strip()]  # info: one spoken unit per non-empty line
    if not spoken:  # info: if not spoken
        spoken = ["Custom message file is empty."]  # info: set spoken
    md += ["## Body", "", text.rstrip(), "", "## Spoken", "", " ".join(spoken), ""]  # info: md += body + spoken
    return "\n".join(md), spoken  # info: return "\n" . join ( md ) , spoken


# ====================================================
# SECTION: BUILD
# What it does: Set BUILD.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
BUILD = {"hourly_chime": b_hourly_chime, "nws_weather": b_nws_weather,  # info: set BUILD
         "remaining_tasks": b_remaining_tasks,  # info: remaining tasks
         "earthquake_report": b_earthquake_report, "hurricane_desk": b_hurricane_desk,  # info: "earthquake_report" : b_earthquake_report , "hurricane_desk" : b_hurricane_desk ,
         "kilauea_report": b_kilauea_report, "kilauea_image_check": b_kilauea_image_check, "solar_desk": b_solar_desk, "security_desk": b_security_desk,  # info: kilauea + solar
         "bandwidth_desk": b_bandwidth_desk, "boot_brief": b_boot_brief,  # info: "bandwidth_desk" : b_bandwidth_desk , "boot_brief" : b_boot_brief ,
         "current_report": b_current_report, "custom_msg": b_custom_msg}  # info: "current_report" : b_current_report , "custom_msg" : b_custom_msg


# ====================================================
# SECTION: function write_md
# What it does: write md.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_md(report: str, md: str) -> Path:  # info: def write_md
    path = REPORTS / f"{report}_current.md"  # info: one tree — Media/Audio/Voice/Reports/
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    if path.is_file():  # info: if path . is_file ( ) :
        retire_current(path)  # info: call retire_current
    tmp = path.with_suffix(".md.tmp")  # info: set tmp
    tmp.write_text(md.rstrip() + "\n\n_Template report; measured values only._\n", encoding="utf-8")  # info: tmp . write_text ( md . rstrip (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )
    return path  # info: return path


# ====================================================
# SECTION: function keep_voice_text
# What it does: Move the read and speak transcripts next to the voice WAV.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def keep_voice_text(report: str) -> None:  # info: def keep_voice_text
    """Move the read and speak transcripts next to the voice WAV. They do not stay in test-reports."""  # info: docstring
    audio = DB / "Media" / "Audio" / "Voice"  # info: set audio
    audio.mkdir(parents=True, exist_ok=True)  # info: audio . mkdir ( parents = True , exist_ok = True )
    for suffix in (".read.txt", ".speak.txt"):  # info: for suffix in ( ".read.txt" , ".speak.txt" ) :
        src = REPORTS / f"{report}_current{suffix}"  # info: set src
        if not src.is_file():  # info: if not src . is_file ( ) :
            continue  # info: continue
        dest = audio / src.name  # info: set dest
        if dest.is_file():  # info: if dest . is_file ( ) :
            retire_current(dest)  # info: call retire_current
        os.replace(src, dest)  # info: os . replace ( src , dest )


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
    if report == "custom_msg":  # info: if report == "custom_msg" :
        cmd.append("--no-gate")  # operator-authored text; not a live-facts desk
    if report == "bandwidth_desk":  # info: if report == "bandwidth_desk" :
        import speakers  # info: import speakers
        if not speakers.is_live("bandwidth", " ".join(spoken)):  # info: if not speakers . is_live ( "bandwidth" , " " . join ( spoken ) ) :
            cmd.append("--no-gate")  # info: cmd . append ( "--no-gate" )
    try:  # info: try :
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600 if report == "current_report" else 300)  # info: set p
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
# SECTION: function _replace_spoken
# What it does: Put the trimmed spoken lines back under the Spoken heading.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _replace_spoken(md: str, spoken: list[str]) -> str:  # info: def _replace_spoken
    head = md.split("\n## Spoken", 1)[0].rstrip()  # info: set head
    return head + "\n\n## Spoken\n\n" + " ".join(spoken) + "\n"  # info: return head + spoken


# ====================================================
# SECTION: function _trim_hurricane
# What it does: Drop hurricane lines already spoken by the NWS desk. On failure the original lines stay.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _trim_hurricane(spoken: list[str]) -> list[str]:  # info: def _trim_hurricane
    folder = str(PACIFIC / "Reports" / "pipeline")  # info: set folder
    if folder not in sys.path:  # info: if folder not in sys . path
        sys.path.insert(0, folder)  # info: sys . path . insert
    try:  # info: try
        import owners  # info: import owners
        return owners.trim_hurricane(spoken)  # info: return owners . trim_hurricane
    except Exception:  # info: except Exception
        return spoken  # info: return spoken


# ====================================================
# SECTION: function _canonical_record
# What it does: Save the report sidecar for this window. A store error does not erase the markdown or WAV.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _canonical_record(report: str, md: str, spoken: list, voice: dict, path: Path) -> dict:  # info: def _canonical_record
    folder = str(PACIFIC / "Reports" / "pipeline")  # info: set folder
    if folder not in sys.path:  # info: if folder not in sys . path
        sys.path.insert(0, folder)  # info: sys . path . insert
    try:  # info: try
        import store as report_store  # info: import store as report_store
        saved = report_store.record_voice(report, md, spoken, voice, path)  # info: set saved
        return {"ok": True, "report_id": saved.get("report_id"), "status": saved.get("status")}  # info: return ok
    except Exception as exc:  # info: except Exception as exc
        return {"ok": False, "detail": type(exc).__name__}  # info: return failure


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
    if report == "hurricane_desk":  # info: if report == "hurricane_desk"
        spoken = _trim_hurricane(spoken)  # info: spoken = _trim_hurricane ( spoken )
        md = _replace_spoken(md, spoken)  # info: md = _replace_spoken ( md , spoken )
    res = {"ok": True, "report": report, "md": str(write_md(report, md)), "sentences": len(spoken)}  # info: set res
    if "--no-voice" not in sys.argv and report == "hourly_chime":  # info: if "--no-voice" not in sys . argv and report == "hourly_chime" :
        from hourly_chimes import persona_for, wav_path  # info: from hourly_chimes import persona_for , wav_path
        path = wav_path(t.hour, t.minute)  # info: set path
        who = persona_for(t.hour)  # info: set who
        if not path.is_file():  # info: if not path . is_file ( ) :
            res["voice"] = {"ok": False, "detail": "prebuilt chime missing", "wav": str(path)}  # info: res [ "voice" ] = { "ok" : False
        else:  # info: else :
            res["voice"] = {"ok": True, "mode": "prebuilt", "wav": str(path), "agent": who}  # info: res [ "voice" ] = { "ok" : True , "mode" : "prebuilt"
            # Play the stored chime file only. Never re-encode or re-render here (use radio_push.py --chimes once when the bank changes).
            import voice_deliver  # info: import voice_deliver
            res["deliver"] = voice_deliver.deliver(report, path, " ".join(spoken), KIND[report], report_text=md, who=who, remember_as=t.strftime("%Y-%m-%dT%H:%M"))  # info: res [ "deliver" ] = voice_deliver . deliver
    elif "--no-voice" not in sys.argv:  # info: elif "--no-voice" not in sys . argv :
        import status_cue  # info: import status_cue
        res["status_starting"] = status_cue.play(report, "starting")  # info: res [ "status_starting" ] = status_cue . play ( report , "starting" )
        res["voice"] = voice(report, spoken)  # info: res [ "voice" ] = voice ( report
        if report == "current_report":  # info: if report == "current_report" :
            keep_voice_text(report)  # info: call keep_voice_text
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
            res["status_transit"] = status_cue.play(report, "transit")  # info: res [ "status_transit" ] = status_cue . play ( report , "transit" )
            res["radio"] = radio_push.push_report(report)  # info: res [ "radio" ] = radio_push . push_report ( report )
            res["status_send"] = status_cue.after_push(report, res["radio"])  # info: res [ "status_send" ] = status_cue . after_push ( report , res [ "radio" ] )
    res["canonical"] = _canonical_record(report, md, spoken, res.get("voice") or {}, Path(res["md"]))  # info: res [ "canonical" ] = _canonical_record
    print(json.dumps(res, ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
