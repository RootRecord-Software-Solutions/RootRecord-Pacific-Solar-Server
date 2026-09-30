# ==============================================================================
# FILE: Weather/hurricanes/scripts/global_board.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Worldwide tropical cyclone board (G3 port of G1 weather/hurricane-tracker/scripts/hurricane_tracker.py, 2026-09-29).

  python3 global_board.py   NHC CurrentStorms + RAMMB tc_realtime + JTWC ABPW / ABIO -> Database
                            Weather/Hawai'i/hurricanes/global/storms-last.json (git-ignored with /Weather/), print a summary

Standalone and additive: the weather poller's hurricanes/scripts/sources.py keeps the Hawaiʻi-relevant NHC track.json
files; this adds the G1 global board (Atlantic / Pacific / West Pacific / Indian / Southern Hemisphere).
Ported unchanged: _parse_latlon, _class_label, _basin_name, _windy, _enrich (Florida + Hawaiʻi distance, score, focus),
_from_nhc, _from_rammb, _from_jtwc (+ storm_track.parse_jtwc_moving), _merge (max 14, invests only if close / al / cp).
Also: RAMMB per-storm page (IR gif URL + track tables), storm_track attach / persist, storm_plot text file.
Not ported: NWS radar links, OBS mode / scenes (OBS BLOCKED). Four source GETs plus one storm page per kept storm
(14 s timeout each). Current files only; nothing deleted.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import logging  # info: import logging
import math  # info: import math
import os  # info: import os
import re  # info: import re
import sys  # info: import sys
import urllib.request  # info: import urllib . request
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

_SCRIPTS = Path(__file__).resolve().parent  # info: set _SCRIPTS
if str(_SCRIPTS) not in sys.path:  # info: if str ( _SCRIPTS ) not in sys
    sys.path.insert(0, str(_SCRIPTS))  # info: sys . path . insert ( 0 ,
import storm_plot  # noqa: E402
import storm_track  # noqa: E402

log = logging.getLogger("rr.hurricane_global")  # info: set log
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
OUT = DB / "Weather" / "Hawai'i" / "hurricanes" / "global"  # info: set OUT
HAWAII_THREAT_NM = 800  # info: set HAWAII_THREAT_NM
UA = "RootRecord-Pacific/3 (hurricane global board)"  # info: set UA
NHC_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"  # info: set NHC_URL
RAMMB_URL = "https://rammb-data.cira.colostate.edu/tc_realtime/"  # info: set RAMMB_URL
RAMMB_STORM = "https://rammb-data.cira.colostate.edu/tc_realtime/storm.asp?storm_identifier={id}"  # info: set RAMMB_STORM
JTWC_ABPW = "https://www.metoc.navy.mil/jtwc/products/abpwweb.txt"  # info: set JTWC_ABPW
JTWC_ABIO = "https://www.metoc.navy.mil/jtwc/products/abioweb.txt"  # info: set JTWC_ABIO
# ====================================================
# SECTION: _JTWC_DIR
# What it does: Set _JTWC_DIR.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_JTWC_DIR = {  # info: set _JTWC_DIR
    "NORTH": 0.0,  # info: "NORTH" : 0.0 ,
    "NORTH-NORTHEAST": 22.5,  # info: "NORTH-NORTHEAST" : 22.5 ,
    "NORTHEAST": 45.0,  # info: "NORTHEAST" : 45.0 ,
    "EAST-NORTHEAST": 67.5,  # info: "EAST-NORTHEAST" : 67.5 ,
    "EAST": 90.0,  # info: "EAST" : 90.0 ,
    "EAST-SOUTHEAST": 112.5,  # info: "EAST-SOUTHEAST" : 112.5 ,
    "SOUTHEAST": 135.0,  # info: "SOUTHEAST" : 135.0 ,
    "SOUTH-SOUTHEAST": 157.5,  # info: "SOUTH-SOUTHEAST" : 157.5 ,
    "SOUTH": 180.0,  # info: "SOUTH" : 180.0 ,
    "SOUTH-SOUTHWEST": 202.5,  # info: "SOUTH-SOUTHWEST" : 202.5 ,
    "SOUTHWEST": 225.0,  # info: "SOUTHWEST" : 225.0 ,
    "WEST-SOUTHWEST": 247.5,  # info: "WEST-SOUTHWEST" : 247.5 ,
    "WEST": 270.0,  # info: "WEST" : 270.0 ,
    "WEST-NORTHWEST": 292.5,  # info: "WEST-NORTHWEST" : 292.5 ,
    "NORTHWEST": 315.0,  # info: "NORTHWEST" : 315.0 ,
    "NORTH-NORTHWEST": 337.5,  # info: "NORTH-NORTHWEST" : 337.5 ,
}  # info: }

# ====================================================
# SECTION: FLORIDA
# What it does: Set FLORIDA.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
FLORIDA = {  # info: set FLORIDA
    "Miami": (25.7617, -80.1918),  # info: call "Miami"
    "Tampa": (27.9506, -82.4572),  # info: call "Tampa"
    "Key West": (24.5551, -81.7800),  # info: call "Key West"
    "Jacksonville": (30.3322, -81.6557),  # info: call "Jacksonville"
}  # info: }

# ====================================================
# SECTION: HAWAII
# What it does: Set HAWAII.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
HAWAII = {  # info: set HAWAII
    "Honolulu": (21.3069, -157.8583),  # info: call "Honolulu"
    "Hilo": (19.7297, -155.0900),  # info: call "Hilo"
    "Līhuʻe": (21.9811, -159.3711),  # info: call "Līhuʻe"
    "Kona": (19.6390, -155.9969),  # info: call "Kona"
}  # info: }


# ====================================================
# SECTION: function parse_jtwc_moving
# What it does: parse jtwc moving.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_jtwc_moving(text: str) -> tuple[float | None, int | None]:  # info: def parse_jtwc_moving
    blob = text or ""  # info: set blob
    up = blob.upper()  # info: set up
    if re.search(r"NEARLY\s+STATIONARY|\bSTATIONARY\b", up):  # info: if re . search ( r"NEARLY\s+STATIONARY|\bSTATIONARY\b" , up
        return None, 0  # info: return None , 0
    m = re.search(  # info: set m
        r"MOVING\s+(?:SLOWLY\s+|RAPIDLY\s+)?([A-Z][A-Z\-]*WARD)(?:\s+AT\s+(\d{1,2})\s+KNOTS)?",  # info: r"MOVING\s+(?:SLOWLY\s+|RAPIDLY\s+)?([A-Z][A-Z\-]*WARD)(?:\s+AT\s+(\d{1,2})\s+KNOTS)?" ,
        up,  # info: up ,
    )  # info: )
    if not m:  # info: if not m :
        return None, None  # info: return None , None
    raw = m.group(1).replace("WARDS", "").replace("WARD", "")  # info: set raw
    deg = _JTWC_DIR.get(raw)  # info: set deg
    kt = int(m.group(2)) if m.group(2) else None  # info: set kt
    return deg, kt  # info: return deg , kt


# ====================================================
# SECTION: function _get
# What it does:  get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(url: str, timeout: float = 14) -> str:  # info: def _get
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})  # info: set req
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # info: with urllib . request . urlopen ( req
        return resp.read().decode("utf-8", "replace")  # info: return resp . read ( ) . decode


# ====================================================
# SECTION: function _haversine_km
# What it does:  haversine km.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:  # info: def _haversine_km
    lat1, lon1 = map(math.radians, a)  # info: lat1 , lon1 = map ( math .
    lat2, lon2 = map(math.radians, b)  # info: lat2 , lon2 = map ( math .
    dlat, dlon = lat2 - lat1, lon2 - lon1  # info: dlat , dlon = lat2 - lat1 ,
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2  # info: set h
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))  # info: return 6371.0 * 2 * math . asin


# ====================================================
# SECTION: function _nm
# What it does:  nm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _nm(km: float) -> float:  # info: def _nm
    return km * 0.539957  # info: return km * 0.539957


# ====================================================
# SECTION: function _parse_latlon
# What it does:  parse latlon.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _parse_latlon(lat: str | float | None, lon: str | float | None) -> tuple[float | None, float | None]:  # info: def _parse_latlon
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):  # info: if isinstance ( lat , ( int ,
        return float(lat), float(lon)  # info: return float ( lat ) , float (

    def one(val: str | None, pos: str, neg: str) -> float | None:  # info: def one
        if not val:  # info: if not val :
            return None  # info: return None
        s = str(val).strip().upper().replace(" ", "")  # info: set s
        m = re.match(r"^([+-]?\d+(?:\.\d+)?)([NSEW])?$", s)  # info: set m
        if not m:  # info: if not m :
            return None  # info: return None
        n = float(m.group(1))  # info: set n
        hemi = m.group(2)  # info: set hemi
        if hemi in {neg}:  # info: if hemi in { neg } :
            n = -abs(n)  # info: set n
        elif hemi in {pos}:  # info: elif hemi in { pos } :
            n = abs(n)  # info: set n
        return n  # info: return n

    return one(str(lat) if lat is not None else None, "N", "S"), one(  # info: return one ( str ( lat ) if
        str(lon) if lon is not None else None, "E", "W"  # info: call str
    )  # info: )


# ====================================================
# SECTION: function _class_label
# What it does:  class label.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _class_label(code: str, knots: int | None, text: str = "") -> str:  # info: def _class_label
    blob = f"{code} {text}".upper()  # info: set blob
    kt = knots or 0  # info: set kt
    if "INVEST" in blob:  # info: if "INVEST" in blob :
        return "Invest"  # info: return "Invest"
    if kt >= 137 or "CAT 5" in blob or "CATEGORY 5" in blob:  # info: if kt >= 137 or "CAT 5" in blob
        return "Category 5 hurricane"  # info: return "Category 5 hurricane"
    if kt >= 113 or "CAT 4" in blob:  # info: if kt >= 113 or "CAT 4" in blob
        return "Category 4 hurricane"  # info: return "Category 4 hurricane"
    if kt >= 96 or "CAT 3" in blob or "MAJOR" in blob:  # info: if kt >= 96 or "CAT 3" in blob
        return "Major hurricane"  # info: return "Major hurricane"
    if kt >= 83 or "CAT 2" in blob:  # info: if kt >= 83 or "CAT 2" in blob
        return "Category 2 hurricane"  # info: return "Category 2 hurricane"
    if kt >= 64 or code in {"HU", "TY", "MH"} or "HURRICANE" in blob or "TYPHOON" in blob:  # info: if kt >= 64 or code in {
        return "Hurricane" if "TYPHOON" not in blob else "Typhoon"  # info: return "Hurricane" if "TYPHOON" not in blob else
    if kt >= 34 or code in {"TS", "STS", "TC"} or "TROPICAL STORM" in blob:  # info: if kt >= 34 or code in {
        return "Tropical storm"  # info: return "Tropical storm"
    if "DEPRESSION" in blob or code in {"TD", "SD"}:  # info: if "DEPRESSION" in blob or code in {
        return "Tropical depression"  # info: return "Tropical depression"
    return (text or code or "Tropical cyclone").strip()  # info: return ( text or code or "Tropical cyclone" )


# ====================================================
# SECTION: function _basin_name
# What it does:  basin name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _basin_name(code: str) -> str:  # info: def _basin_name
    return {  # info: return {
        "al": "Atlantic",  # info: "al" : "Atlantic" ,
        "ep": "Eastern Pacific",  # info: "ep" : "Eastern Pacific" ,
        "cp": "Central Pacific",  # info: "cp" : "Central Pacific" ,
        "wp": "Western Pacific",  # info: "wp" : "Western Pacific" ,
        "io": "North Indian",  # info: "io" : "North Indian" ,
        "sh": "Southern Hemisphere",  # info: "sh" : "Southern Hemisphere" ,
    }.get(code[:2].lower(), code.upper())  # info: } . get ( code [ : 2


# ====================================================
# SECTION: function _windy
# What it does:  windy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _windy(lat: float | None, lon: float | None, zoom: int = 6) -> str:  # info: def _windy
    if lat is None or lon is None:  # info: if lat is None or lon is None
        return "https://www.windy.com/-Hurricane-tracker/hurricanes?hurricanes,20,-40,3,p:cities"  # info: return "https://www.windy.com/-Hurricane-tracker/hurricanes?hurricanes,20,-40,3,p:cities"
    return (  # info: return (
        "https://www.windy.com/-Hurricane-tracker/hurricanes"  # info: "https://www.windy.com/-Hurricane-tracker/hurricanes"
        f"?hurricanes,{lat:.3f},{lon:.3f},{zoom},p:cities"  # info: f" ?hurricanes, { lat : .3f } ,
    )  # info: )


# ====================================================
# SECTION: function _enrich
# What it does:  enrich.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _enrich(storm: dict) -> dict:  # info: def _enrich
    lat, lon = storm.get("lat"), storm.get("lon")  # info: lat , lon = storm . get (
    fl = {}  # info: set fl
    hi = {}  # info: set hi
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):  # info: if isinstance ( lat , ( int ,
        fl = {  # info: set fl
            name: round(_nm(_haversine_km((lat, lon), pos)), 0)  # info: set name
            for name, pos in FLORIDA.items()  # info: for name , pos in FLORIDA . items
        }  # info: }
        hi = {  # info: set hi
            name: round(_nm(_haversine_km((lat, lon), pos)), 0)  # info: set name
            for name, pos in HAWAII.items()  # info: for name , pos in HAWAII . items
        }  # info: }
    nearest_fl = min(fl.values()) if fl else None  # info: set nearest_fl
    nearest_hi = min(hi.values()) if hi else None  # info: set nearest_hi
    knots = int(storm.get("knots") or 0)  # info: set knots
    invest = bool(storm.get("invest"))  # info: set invest
    basin = str(storm.get("basin") or "")  # info: set basin
    score = knots  # info: set score
    if nearest_fl is not None:  # info: if nearest_fl is not None :
        if nearest_fl < 2500:  # info: if nearest_fl < 2500 :
            score += 500 + int((2500 - nearest_fl) / 4)  # info: set score
        if nearest_fl < 800:  # info: if nearest_fl < 800 :
            score += 400  # info: set score
    if nearest_hi is not None:  # info: if nearest_hi is not None :
        if nearest_hi < 2500:  # info: if nearest_hi < 2500 :
            score += 550 + int((2500 - nearest_hi) / 4)  # info: set score
        if nearest_hi < 800:  # info: if nearest_hi < 800 :
            score += 450  # info: set score
    if basin == "al":  # info: if basin == "al" :
        score += 180  # info: set score
    if basin == "cp":  # info: if basin == "cp" :
        score += 220  # info: set score
    if basin == "ep" and nearest_hi and nearest_hi < 2000:  # info: if basin == "ep" and nearest_hi and nearest_hi
        score += 120  # info: set score
    if invest:  # info: if invest :
        score -= 90  # info: set score
    name = str(storm.get("name") or storm.get("id") or "Storm")  # info: set name
    scene = f"Storm · {name.title() if name.isupper() else name}"  # info: set scene
    if invest:  # info: if invest :
        scene = f"Storm · {str(storm.get('id') or name).upper()}"  # info: set scene
    storm.update(  # info: storm . update (
        {  # info: {
            "florida_nm": fl,  # info: "florida_nm" : fl ,
            "hawaii_nm": hi,  # info: "hawaii_nm" : hi ,
            "nearest_florida_nm": nearest_fl,  # info: "nearest_florida_nm" : nearest_fl ,
            "nearest_hawaii_nm": nearest_hi,  # info: "nearest_hawaii_nm" : nearest_hi ,
            "focus": (  # info: call "focus"
                "florida"  # info: "florida"
                if nearest_fl is not None and (nearest_hi is None or nearest_fl <= nearest_hi) and nearest_fl < HAWAII_THREAT_NM  # info: if nearest_fl is not None and ( nearest_hi
                else "hawaii"  # info: else "hawaii"
                if nearest_hi is not None and nearest_hi < HAWAII_THREAT_NM  # info: if nearest_hi is not None and nearest_hi <
                else "global"  # info: else "global"
            ),  # info: ) ,
            "score": score,  # info: "score" : score ,
            "scene": scene[:80],  # info: "scene" : scene [ : 80 ] ,
            "label": storm.get("label") or _class_label(str(storm.get("class") or ""), knots, name),  # info: "label" : storm . get ( "label" )
            "windy_url": _windy(lat, lon, 6 if not invest else 5),  # info: "windy_url" : _windy ( lat , lon ,
            "mph": round(knots * 1.15078) if knots else None,  # info: "mph" : round ( knots * 1.15078 )
        }  # info: }
    )  # info: )
    return storm  # info: return storm


# ====================================================
# SECTION: function _from_nhc
# What it does:  from nhc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _from_nhc(raw: dict) -> list[dict]:  # info: def _from_nhc
    out = []  # info: set out
    for s in raw.get("activeStorms") or []:  # info: for s in raw . get ( "activeStorms"
        lat, lon = s.get("latitudeNumeric"), s.get("longitudeNumeric")  # info: lat , lon = s . get (
        if lat is None:  # info: if lat is None :
            lat, lon = _parse_latlon(s.get("latitude"), s.get("longitude"))  # info: lat , lon = _parse_latlon ( s .
        sid = str(s.get("id") or "").lower()  # info: set sid
        basin = sid[:2]  # info: set basin
        try:  # info: try :
            knots = int(float(s.get("intensity") or 0))  # info: set knots
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            knots = 0  # info: set knots
        name = str(s.get("name") or sid).strip()  # info: set name
        klass = str(s.get("classification") or "")  # info: set klass
        bin_no = str(s.get("binNumber") or "")  # info: set bin_no
        graphics = ""  # info: set graphics
        if bin_no:  # info: if bin_no :
            graphics = f"https://www.nhc.noaa.gov/graphics_{bin_no.lower()}.shtml?cone"  # info: set graphics
        out.append(  # info: out . append (
            _enrich(  # info: call _enrich
                {  # info: {
                    "id": sid,  # info: "id" : sid ,
                    "source": "nhc",  # info: "source" : "nhc" ,
                    "basin": basin,  # info: "basin" : basin ,
                    "basin_name": _basin_name(basin),  # info: "basin_name" : _basin_name ( basin ) ,
                    "name": name,  # info: "name" : name ,
                    "class": klass,  # info: "class" : klass ,
                    "knots": knots,  # info: "knots" : knots ,
                    "mb": _to_int(s.get("pressure")),  # info: "mb" : _to_int ( s . get (
                    "lat": lat,  # info: "lat" : lat ,
                    "lon": lon,  # info: "lon" : lon ,
                    "movement_dir": s.get("movementDir"),  # info: "movement_dir" : s . get ( "movementDir" )
                    "movement_kt": s.get("movementSpeed"),  # info: "movement_kt" : s . get ( "movementSpeed" )
                    "updated": s.get("lastUpdate"),  # info: "updated" : s . get ( "lastUpdate" )
                    "advisory_url": ((s.get("publicAdvisory") or {}).get("url")),  # info: call "advisory_url"
                    "cone_url": graphics,  # info: "cone_url" : graphics ,
                    "invest": name.upper() in {"INVEST", "UNKNOWN"} or "INVEST" in klass.upper(),  # info: "invest" : name . upper ( ) in
                }  # info: }
            )  # info: )
        )  # info: )
    return out  # info: return out


# ====================================================
# SECTION: function _to_int
# What it does:  to int.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _to_int(v) -> int | None:  # info: def _to_int
    try:  # info: try :
        return int(float(v))  # info: return int ( float ( v ) )
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return None  # info: return None


# ====================================================
# SECTION: function _from_rammb
# What it does:  from rammb.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _from_rammb(html: str) -> list[dict]:  # info: def _from_rammb
    out = []  # info: set out
    for m in re.finditer(  # info: for m in re . finditer (
        r'storm_identifier=([a-z0-9]+)[^>]*>\s*([A-Z0-9]+)\s*-\s*([^<]+)',  # info: r'storm_identifier=([a-z0-9]+)[^>]*>\s*([A-Z0-9]+)\s*-\s*([^<]+)' ,
        html,  # info: html ,
        re.I,  # info: re . I ,
    ):  # info: ) :
        sid = m.group(1).lower()  # info: set sid
        label = re.sub(r"<br\s*/?>", "", m.group(3), flags=re.I).strip()  # info: set label
        basin = sid[:2]  # info: set basin
        invest = "INVEST" in label.upper()  # info: set invest
        year = sid[4:8] if len(sid) >= 8 else datetime.now(timezone.utc).strftime("%Y")  # info: set year
        num = sid[2:4]  # info: set num
        ir = (  # info: set ir
            "https://rammb-data.cira.colostate.edu/tc_realtime/products/storms/"  # info: "https://rammb-data.cira.colostate.edu/tc_realtime/products/storms/"
            f"{year}{basin}{num}/4kmirimg/{year}{basin}{num}_4kmirimg.gif"  # info: f" { year } { basin } {
        )  # info: )
        out.append(  # info: out . append (
            {  # info: {
                "id": sid,  # info: "id" : sid ,
                "source": "rammb",  # info: "source" : "rammb" ,
                "basin": basin,  # info: "basin" : basin ,
                "basin_name": _basin_name(basin),  # info: "basin_name" : _basin_name ( basin ) ,
                "name": "INVEST" if invest else re.sub(r"^(Major\s+)?(Hurricane|Typhoon|Tropical Storm|Tropical Depression)\s+", "", label, flags=re.I).strip() or sid,  # info: "name" : "INVEST" if invest else re .
                "class": "INVEST" if invest else "",  # info: "class" : "INVEST" if invest else "" ,
                "label": label.title() if not invest else "Invest",  # info: "label" : label . title ( ) if
                "rammb_url": RAMMB_STORM.format(id=sid),  # info: "rammb_url" : RAMMB_STORM . format ( id =
                "ir_guess": ir,  # info: "ir_guess" : ir ,
                "invest": invest,  # info: "invest" : invest ,
            }  # info: }
        )  # info: )
    return out  # info: return out


# ====================================================
# SECTION: function _rammb_ir
# What it does:  rammb ir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _rammb_ir(sid: str, html: str) -> str | None:  # info: def _rammb_ir
    if len(sid) < 8:  # info: if len ( sid ) < 8 :
        m = None  # info: set m
    else:  # info: else :
        m = re.search(  # info: set m
            rf"/tc_realtime/products/storms/[^\"']+{re.escape(sid[4:8] + sid[:2] + sid[2:4])}?[^\"']*4kmirimg[^\"']+\.gif",  # info: rf" /tc_realtime/products/storms/[^\"']+ { re . escape ( sid
            html,  # info: html ,
            re.I,  # info: re . I ,
        )  # info: )
    if not m:  # info: if not m :
        m = re.search(r"/tc_realtime/products/storms/[^\"']+4kmirimg[^\"']+\.gif", html, re.I)  # info: set m
    if not m:  # info: if not m :
        return None  # info: return None
    return "https://rammb-data.cira.colostate.edu" + m.group(0)  # info: return "https://rammb-data.cira.colostate.edu" + m . group ( 0


# ====================================================
# SECTION: function _fill_storm_page
# What it does:  fill storm page.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fill_storm_page(storm: dict) -> None:  # info: def _fill_storm_page
    sid = str(storm.get("id") or "")  # info: set sid
    if not sid:  # info: if not sid :
        return  # info: return
    try:  # info: try :
        html = _get(RAMMB_STORM.format(id=sid))  # info: set html
    except Exception as e:  # noqa: BLE001
        log.info("rammb storm page skip %s: %s", sid, e)  # info: log . info ( "rammb storm page skip %s: %s" , sid ,
        return  # info: return
    if not html:  # info: if not html :
        return  # info: return
    if not storm.get("ir_url"):  # info: if not storm . get ( "ir_url" )
        ir = _rammb_ir(sid, html)  # info: set ir
        if ir:  # info: if ir :
            storm["ir_url"] = ir  # info: storm [ "ir_url" ] = ir
    try:  # info: try :
        storm_track.apply_rammb_page(storm, html)  # info: storm_track . apply_rammb_page ( storm , html )
    except Exception as e:  # noqa: BLE001
        log.info("rammb track parse skip %s: %s", sid, e)  # info: log . info ( "rammb track parse skip %s: %s" , sid ,


# ====================================================
# SECTION: function _from_jtwc
# What it does:  from jtwc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _from_jtwc(text: str, default_basin: str) -> list[dict]:  # info: def _from_jtwc
    out = []  # info: set out
    # Named warning: TROPICAL STORM 17W (SAUDEL) WAS LOCATED NEAR 8.5N 154.1E ... 35 KNOTS
    named = re.compile(  # info: set named
        r"(TYPHOON|HURRICANE|TROPICAL STORM|TROPICAL DEPRESSION)\s+(\d{1,2})([WEPACS])"  # info: r"(TYPHOON|HURRICANE|TROPICAL STORM|TROPICAL DEPRESSION)\s+(\d{1,2})([WEPACS])"
        r"(?:\s+\(([A-Z][A-Z0-9\- ]+)\))?.*?NEAR\s+(\d+\.?\d*)([NS])\s+(\d+\.?\d*)([EW])"  # info: r"(?:\s+\(([A-Z][A-Z0-9\- ]+)\))?.*?NEAR\s+(\d+\.?\d*)([NS])\s+(\d+\.?\d*)([EW])"
        r".{0,500}?MAXIMUM\s+SUSTAINED\s+SURFACE\s+WINDS WERE ESTIMATED AT (\d{2,3})\s+KNOTS",  # info: r".{0,500}?MAXIMUM\s+SUSTAINED\s+SURFACE\s+WINDS WERE ESTIMATED AT (\d{2,3})\s+KNOTS" ,
        re.I | re.S,  # info: re . I | re . S ,
    )  # info: )
    for m in named.finditer(text):  # info: for m in named . finditer ( text
        num = int(m.group(2))  # info: set num
        hemi = m.group(3).lower()  # info: set hemi
        basin = {"w": "wp", "e": "ep", "p": "cp", "a": "al", "c": "cp", "s": "sh"}.get(hemi, default_basin)  # info: set basin
        lat = float(m.group(5)) * (1 if m.group(6).upper() == "N" else -1)  # info: set lat
        lon = float(m.group(7)) * (1 if m.group(8).upper() == "E" else -1)  # info: set lon
        name = (m.group(4) or f"{num}{hemi.upper()}").strip()  # info: set name
        move_dir, move_kt = parse_jtwc_moving(m.group(0))  # info: move_dir , move_kt = parse_jtwc_moving ( m .
        out.append(  # info: out . append (
            {  # info: {
                "id": f"{basin}{num:02d}{datetime.now(timezone.utc).year}",  # info: "id" : f" { basin } { num
                "source": "jtwc",  # info: "source" : "jtwc" ,
                "basin": basin,  # info: "basin" : basin ,
                "name": name,  # info: "name" : name ,
                "class": m.group(1),  # info: "class" : m . group ( 1 )
                "knots": int(m.group(9)),  # info: "knots" : int ( m . group (
                "lat": lat,  # info: "lat" : lat ,
                "lon": lon,  # info: "lon" : lon ,
                "movement_dir": move_dir,  # info: "movement_dir" : move_dir ,
                "movement_kt": move_kt,  # info: "movement_kt" : move_kt ,
                "movement_source": "jtwc" if move_dir is not None or move_kt is not None else None,  # info: "movement_source" : "jtwc" if move_dir is not None
                "invest": False,  # info: "invest" : False ,
            }  # info: }
        )  # info: )
    invest = re.compile(  # info: set invest
        r"INVEST\s+(\d{2})([WEPACS]).*?NEAR\s+(\d+\.?\d*)([NS])\s+(\d+\.?\d*)([EW])"  # info: r"INVEST\s+(\d{2})([WEPACS]).*?NEAR\s+(\d+\.?\d*)([NS])\s+(\d+\.?\d*)([EW])"
        r".{0,500}?(\d{2,3})\s+(?:TO\s+\d{2,3}\s+)?KNOTS",  # info: r".{0,500}?(\d{2,3})\s+(?:TO\s+\d{2,3}\s+)?KNOTS" ,
        re.I | re.S,  # info: re . I | re . S ,
    )  # info: )
    for m in invest.finditer(text):  # info: for m in invest . finditer ( text
        num = int(m.group(1))  # info: set num
        hemi = m.group(2).lower()  # info: set hemi
        basin = {"w": "wp", "e": "ep", "p": "cp", "s": "sh", "a": "io", "c": "io"}.get(hemi, default_basin)  # info: set basin
        lat = float(m.group(3)) * (1 if m.group(4).upper() == "N" else -1)  # info: set lat
        lon = float(m.group(5)) * (1 if m.group(6).upper() == "E" else -1)  # info: set lon
        out.append(  # info: out . append (
            {  # info: {
                "id": f"{basin}{num:02d}{datetime.now(timezone.utc).year}",  # info: "id" : f" { basin } { num
                "source": "jtwc",  # info: "source" : "jtwc" ,
                "basin": basin,  # info: "basin" : basin ,
                "name": "INVEST",  # info: "name" : "INVEST" ,
                "class": "INVEST",  # info: "class" : "INVEST" ,
                "knots": int(m.group(7)),  # info: "knots" : int ( m . group (
                "lat": lat,  # info: "lat" : lat ,
                "lon": lon,  # info: "lon" : lon ,
                "invest": True,  # info: "invest" : True ,
            }  # info: }
        )  # info: )
    return out  # info: return out


# ====================================================
# SECTION: function _merge
# What it does:  merge.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _merge(rows: list[dict]) -> list[dict]:  # info: def _merge
    by: dict[str, dict] = {}  # info: set by
    for row in rows:  # info: for row in rows :
        sid = str(row.get("id") or "").lower()  # info: set sid
        if not sid:  # info: if not sid :
            continue  # info: continue
        cur = by.get(sid)  # info: set cur
        if not cur:  # info: if not cur :
            by[sid] = row  # info: by [ sid ] = row
            continue  # info: continue
        for k, v in row.items():  # info: for k , v in row . items
            if v in (None, "", [], {}):  # info: if v in ( None , "" ,
                continue  # info: continue
            if k in {"lat", "lon", "knots", "mb"} and cur.get(k) in (None, 0, ""):  # info: if k in { "lat" , "lon" ,
                cur[k] = v  # info: cur [ k ] = v
            elif k not in cur or cur[k] in (None, "", []):  # info: elif k not in cur or cur [
                cur[k] = v  # info: cur [ k ] = v
            elif k == "source" and v == "nhc":  # info: elif k == "source" and v == "nhc"
                cur[k] = v  # info: cur [ k ] = v
        if row.get("source") == "nhc":  # info: if row . get ( "source" ) ==
            for k in ("name", "class", "cone_url", "advisory_url", "updated"):  # info: for k in ( "name" , "class" ,
                if row.get(k):  # info: if row . get ( k ) :
                    cur[k] = row[k]  # info: cur [ k ] = row [ k
    storms = [_enrich(s) for s in by.values()]  # info: set storms
    storms.sort(key=lambda s: (-int(s.get("score") or 0), -int(s.get("knots") or 0)))  # info: storms . sort ( key = lambda s
    kept: list[dict] = []  # info: set kept
    for s in storms:  # info: for s in storms :
        if not s.get("invest"):  # info: if not s . get ( "invest" )
            kept.append(s)  # info: kept . append ( s )
            continue  # info: continue
        nfl, nhi = s.get("nearest_florida_nm"), s.get("nearest_hawaii_nm")  # info: nfl , nhi = s . get (
        close = (nfl is not None and nfl < 2200) or (nhi is not None and nhi < HAWAII_THREAT_NM)  # info: set close
        if close or s.get("basin") in {"al", "cp"}:  # info: if close or s . get ( "basin"
            kept.append(s)  # info: kept . append ( s )
    return kept[:14]  # info: return kept [ : 14 ]


# ====================================================
# SECTION: function refresh
# What it does: refresh.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def refresh() -> dict:  # info: def refresh
    rows, sources, errors = [], [], {}  # info: rows , sources , errors = [ ]
    for key, url in (("nhc", NHC_URL), ("rammb", RAMMB_URL), ("jtwc-wp", JTWC_ABPW), ("jtwc-io", JTWC_ABIO)):  # info: for key , url in ( ( "nhc"
        try:  # info: try :
            raw = _get(url)  # info: set raw
        except Exception as e:  # noqa: BLE001
            errors[key] = f"{type(e).__name__}: {e}"[:200]  # info: errors [ key ] = f" { type
            continue  # info: continue
        try:  # info: try :
            if key == "nhc":  # info: if key == "nhc" :
                rows.extend(_from_nhc(json.loads(raw)))  # info: rows . extend ( _from_nhc ( json .
            elif key == "rammb":  # info: elif key == "rammb" :
                rows.extend(_from_rammb(raw))  # info: rows . extend ( _from_rammb ( raw )
            else:  # info: else :
                rows.extend(_from_jtwc(raw, "wp" if key == "jtwc-wp" else "io"))  # info: rows . extend ( _from_jtwc ( raw ,
            sources.append(key)  # info: sources . append ( key )
        except Exception as e:  # noqa: BLE001
            errors[key] = f"parse {type(e).__name__}: {e}"[:200]  # info: errors [ key ] = f" parse {
    storms = _merge(rows)  # info: set storms
    storm_track.TRACKS_PATH = OUT / "storm-tracks.json"  # info: storm_track . TRACKS_PATH = OUT / "storm-tracks.json"
    for storm in storms[:14]:  # info: for storm in storms [ : 14 ]
        _fill_storm_page(storm)  # info: call _fill_storm_page
    storms = [_enrich(s) for s in storms]  # info: set storms
    for storm in storms:  # info: for storm in storms :
        try:  # info: try :
            storm_track.attach_track(storm, persist=True)  # info: storm_track . attach_track ( storm , persist =
        except Exception as e:  # noqa: BLE001
            log.info("storm track persist skip %s: %s", storm.get("id"), e)  # info: log . info ( "storm track persist skip %s: %s" , storm .
    return {"ok": bool(sources), "ts": datetime.now(timezone.utc).isoformat(),  # info: return { "ok" : bool ( sources )
            "at": datetime.now(HST).isoformat(timespec="seconds"), "sources": sources, "errors": errors,  # info: "at" : datetime . now ( HST )
            "count": len(storms), "storms": storms}  # info: "count" : len ( storms ) , "storms"


# ====================================================
# SECTION: function _append_log
# What it does:  append log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _append_log(payload: dict) -> None:  # info: def _append_log
    try:  # info: try :
        log_dir = DB / "Logs" / "Weather" / "hurricanes"  # info: set log_dir
        log_dir.mkdir(parents=True, exist_ok=True)  # info: log_dir . mkdir ( parents = True ,
        tracked = sum(  # info: set tracked
            1 for s in payload.get("storms") or []  # info: 1 for s in payload . get (
            if s.get("track_history") or s.get("forecast_track")  # info: if s . get ( "track_history" ) or
        )  # info: )
        line = (  # info: set line
            f"{payload.get('at')} ok={payload.get('ok')} storms={payload.get('count')} "  # info: f" { payload . get ( 'at' )
            f"with_tracks={tracked} sources={','.join(payload.get('sources') or [])}\n"  # info: f" with_tracks= { tracked } sources= { ','
        )  # info: )
        with (log_dir / "global-board.log").open("a", encoding="utf-8") as fh:  # info: with ( log_dir / "global-board.log" ) . open
            fh.write(line)  # info: fh . write ( line )
    except OSError as e:  # info: except OSError as e :
        log.info("hurricane log skip: %s", e)  # info: log . info ( "hurricane log skip: %s" , e )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    payload = refresh()  # info: set payload
    OUT.mkdir(parents=True, exist_ok=True)  # info: OUT . mkdir ( parents = True ,
    tmp = OUT / "storms-last.json.tmp"  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, OUT / "storms-last.json")  # info: os . replace ( tmp , OUT /
    storm_plot.BOARD_DIR = OUT  # info: storm_plot . BOARD_DIR = OUT
    storm_plot.write_plot(payload)  # info: storm_plot . write_plot ( payload )
    _append_log(payload)  # info: call _append_log
    print(json.dumps({"ok": payload["ok"], "sources": payload["sources"], "errors": payload["errors"], "count": payload["count"],  # info: call print
                      "storms": [f"{s.get('label')} {s.get('name')} ({s.get('basin')}, {s.get('knots')} kt, "  # info: "storms" : [ f" { s . get
                                 f"nearest HI {s.get('nearest_hawaii_nm')} nm, src {s.get('source')})" for s in payload["storms"]]},  # info: f" nearest HI { s . get ( 'nearest_hawaii_nm'
                     ensure_ascii=False))  # info: set ensure_ascii
    return 0 if payload["ok"] else 1  # info: return 0 if payload [ "ok" ] else


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
