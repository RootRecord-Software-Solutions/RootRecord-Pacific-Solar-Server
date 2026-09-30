# ==============================================================================
# FILE: Weather/hurricanes/scripts/storm_track.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Storm location, history, official forecast, and motion vs Hawaiʻi.

File facts only. RAMMB history/forecast and NHC/JTWC motion — no invented tracks.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import math  # info: import math
import os  # info: import os
import re  # info: import re
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

_DB = Path(os.environ.get(  # info: set _DB
    "RR_DATABASE_ROOT",  # info: "RR_DATABASE_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database" ,
))  # info: ) )
TRACKS_PATH = _DB / "Weather" / "Hawai'i" / "hurricanes" / "global" / "storm-tracks.json"  # info: set TRACKS_PATH
HAWAII_THREAT_NM = 800  # info: set HAWAII_THREAT_NM
LIHUE = (21.9811, -159.3711)  # info: set LIHUE
# ====================================================
# SECTION: HAWAII
# What it does: Set HAWAII.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
HAWAII = {  # info: set HAWAII
    "Honolulu": (21.3069, -157.8583),  # info: call "Honolulu"
    "Hilo": (19.7297, -155.0900),  # info: call "Hilo"
    "Līhuʻe": LIHUE,  # info: "Līhuʻe" : LIHUE ,
    "Kona": (19.6390, -155.9969),  # info: call "Kona"
}  # info: }

_EIGHT = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")  # info: set _EIGHT
# ====================================================
# SECTION: _EIGHT_WORD
# What it does: Set _EIGHT_WORD.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_EIGHT_WORD = (  # info: set _EIGHT_WORD
    "north",  # info: "north" ,
    "northeast",  # info: "northeast" ,
    "east",  # info: "east" ,
    "southeast",  # info: "southeast" ,
    "south",  # info: "south" ,
    "southwest",  # info: "southwest" ,
    "west",  # info: "west" ,
    "northwest",  # info: "northwest" ,
)  # info: )
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
# SECTION: function _haversine_nm
# What it does:  haversine nm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _haversine_nm(a: tuple[float, float], b: tuple[float, float]) -> float:  # info: def _haversine_nm
    lat1, lon1 = map(math.radians, a)  # info: lat1 , lon1 = map ( math .
    lat2, lon2 = map(math.radians, b)  # info: lat2 , lon2 = map ( math .
    dlat, dlon = lat2 - lat1, lon2 - lon1  # info: dlat , dlon = lat2 - lat1 ,
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2  # info: set h
    km = 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))  # info: set km
    return km * 0.539957  # info: return km * 0.539957


# ====================================================
# SECTION: function bearing_deg
# What it does: bearing deg.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:  # info: def bearing_deg
    p1, p2 = math.radians(lat1), math.radians(lat2)  # info: p1 , p2 = math . radians (
    dl = math.radians(lon2 - lon1)  # info: set dl
    y = math.sin(dl) * math.cos(p2)  # info: set y
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)  # info: set x
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0  # info: return ( math . degrees ( math .


# ====================================================
# SECTION: function compass8
# What it does: compass8.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def compass8(deg: float) -> str:  # info: def compass8
    idx = int((deg + 22.5) // 45) % 8  # info: set idx
    return _EIGHT[idx]  # info: return _EIGHT [ idx ]


# ====================================================
# SECTION: function compass8_word
# What it does: compass8 word.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def compass8_word(deg: float) -> str:  # info: def compass8_word
    idx = int((deg + 22.5) // 45) % 8  # info: set idx
    return _EIGHT_WORD[idx]  # info: return _EIGHT_WORD [ idx ]


# ====================================================
# SECTION: function nearest_hawaii_nm
# What it does: nearest hawaii nm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def nearest_hawaii_nm(lat: float, lon: float) -> tuple[str, float]:  # info: def nearest_hawaii_nm
    best_name = "Līhuʻe"  # info: set best_name
    best = 9e9  # info: set best
    for name, pos in HAWAII.items():  # info: for name , pos in HAWAII . items
        nm = _haversine_nm((lat, lon), pos)  # info: set nm
        if nm < best:  # info: if nm < best :
            best = nm  # info: set best
            best_name = name  # info: set best_name
    return best_name, round(best, 0)  # info: return best_name , round ( best , 0


# ====================================================
# SECTION: function ocean_region
# What it does: Named ocean box from lat/lon. Not a landfall call.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ocean_region(lat: float, lon: float) -> dict[str, str]:  # info: def ocean_region
    """Named ocean box from lat/lon. Not a landfall call."""  # info: """Named ocean box from lat/lon. Not a landfall call."""
    island, nm = nearest_hawaii_nm(lat, lon)  # info: island , nm = nearest_hawaii_nm ( lat ,
    if nm < HAWAII_THREAT_NM:  # info: if nm < HAWAII_THREAT_NM :
        return {  # info: return {
            "id": "hawaii",  # info: "id" : "hawaii" ,
            "name": "Near the Hawaiian Islands",  # info: "name" : "Near the Hawaiian Islands" ,
            "note": f"Inside {HAWAII_THREAT_NM:.0f} nmi of {island}.",  # info: "note" : f" Inside { HAWAII_THREAT_NM : .0f
        }  # info: }
    if -180.0 <= lon <= -140.0 and 5.0 <= lat <= 32.0:  # info: if - 180.0 <= lon <= - 140.0
        return {  # info: return {
            "id": "cpac",  # info: "id" : "cpac" ,
            "name": "Central North Pacific",  # info: "name" : "Central North Pacific" ,
            "note": "Hawaiian longitudes, still outside the local 800 nmi gate." if nm < 1800 else "Central Pacific, not a local Hawaiʻi threat on distance.",  # info: "note" : "Hawaiian longitudes, still outside the local 800 nmi gate." if nm < 1800 else
        }  # info: }
    if -140.0 < lon <= -80.0 and 0.0 <= lat <= 35.0:  # info: if - 140.0 < lon <= - 80.0
        return {  # info: return {
            "id": "epac",  # info: "id" : "epac" ,
            "name": "Eastern North Pacific",  # info: "name" : "Eastern North Pacific" ,
            "note": "Mexico/Central America side of the Pacific, not west of Kauaʻi.",  # info: "note" : "Mexico/Central America side of the Pacific, not west of Kauaʻi." ,
        }  # info: }
    if -100.0 <= lon <= 0.0 and 5.0 <= lat <= 50.0:  # info: if - 100.0 <= lon <= 0.0 and
        return {  # info: return {
            "id": "atlantic",  # info: "id" : "atlantic" ,
            "name": "North Atlantic",  # info: "name" : "North Atlantic" ,
            "note": "Atlantic basin. Not the Hawaiian Islands.",  # info: "note" : "Atlantic basin. Not the Hawaiian Islands." ,
        }  # info: }
    if 100.0 <= lon <= 180.0 and -5.0 <= lat <= 45.0:  # info: if 100.0 <= lon <= 180.0 and -
        if lat >= 20.0 and 120.0 <= lon <= 150.0:  # info: if lat >= 20.0 and 120.0 <= lon
            return {  # info: return {
                "id": "wpac-japan",  # info: "id" : "wpac-japan" ,
                "name": "Western North Pacific (Japan / East China / Philippine Sea)",  # info: "name" : "Western North Pacific (Japan / East China / Philippine Sea)" ,
                "note": "West of the date line, Asia/Japan side. West of Kauaʻi is not toward Hawaiʻi.",  # info: "note" : "West of the date line, Asia/Japan side. West of Kauaʻi is not toward Hawaiʻi." ,
            }  # info: }
        return {  # info: return {
            "id": "wpac",  # info: "id" : "wpac" ,
            "name": "Western North Pacific",  # info: "name" : "Western North Pacific" ,
            "note": "West of the date line. Asia/Japan waters, not the Hawaiian Islands.",  # info: "note" : "West of the date line. Asia/Japan waters, not the Hawaiian Islands." ,
        }  # info: }
    if -180.0 <= lon < -160.0:  # info: if - 180.0 <= lon < - 160.0
        return {  # info: return {
            "id": "dateline",  # info: "id" : "dateline" ,
            "name": "West of Hawaiʻi / date line approach",  # info: "name" : "West of Hawaiʻi / date line approach" ,
            "note": "Between the date line and Kauaʻi longitudes.",  # info: "note" : "Between the date line and Kauaʻi longitudes." ,
        }  # info: }
    return {  # info: return {
        "id": "other",  # info: "id" : "other" ,
        "name": "Outside the Hawaiʻi / EastPac / WestPac desks",  # info: "name" : "Outside the Hawaiʻi / EastPac / WestPac desks" ,
        "note": "Mapped position is not a Hawaiian-island board storm on distance.",  # info: "note" : "Mapped position is not a Hawaiian-island board storm on distance." ,
    }  # info: }


# ====================================================
# SECTION: function angle_delta
# What it does: angle delta.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def angle_delta(a: float, b: float) -> float:  # info: def angle_delta
    d = abs((a - b) % 360.0)  # info: set d
    return min(d, 360.0 - d)  # info: return min ( d , 360.0 - d


# ====================================================
# SECTION: function hawaii_approach
# What it does: toward / away / abeam from the storm's course vs bearing to Līhuʻe.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hawaii_approach(lat: float, lon: float, course_deg: float | None) -> str:  # info: def hawaii_approach
    """toward / away / abeam from the storm's course vs bearing to Līhuʻe."""  # info: """toward / away / abeam from the storm's course vs bearing to Līhuʻe."""
    if course_deg is None:  # info: if course_deg is None :
        return "unknown"  # info: return "unknown"
    to_hi = bearing_deg(lat, lon, LIHUE[0], LIHUE[1])  # info: set to_hi
    delta = angle_delta(course_deg, to_hi)  # info: set delta
    if delta <= 50:  # info: if delta <= 50 :
        return "toward"  # info: return "toward"
    if delta >= 130:  # info: if delta >= 130 :
        return "away"  # info: return "away"
    return "abeam"  # info: return "abeam"


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
# SECTION: function _strip_html
# What it does:  strip html.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _strip_html(html: str) -> str:  # info: def _strip_html
    t = re.sub(r"(?is)<script.*?</script>", " ", html or "")  # info: set t
    t = re.sub(r"(?is)<style.*?</style>", " ", t)  # info: set t
    t = re.sub(r"<[^>]+>", " ", t)  # info: set t
    return re.sub(r"\s+", " ", t).strip()  # info: return re . sub ( r"\s+" , " "


# ====================================================
# SECTION: function parse_rammb_tracks
# What it does: Official RAMMB tables on the storm page. Empty if the page has none.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_rammb_tracks(html: str) -> dict[str, list[dict[str, Any]]]:  # info: def parse_rammb_tracks
    """Official RAMMB tables on the storm page. Empty if the page has none."""  # info: """Official RAMMB tables on the storm page. Empty if the page has none."""
    text = _strip_html(html)  # info: set text
    forecast: list[dict[str, Any]] = []  # info: set forecast
    history: list[dict[str, Any]] = []  # info: set history
    fm = re.search(  # info: set fm
        r"Forecast Hour Latitude Longitude Intensity(.*?)(?:Forecast Track Archive|Track History|About Forecast)",  # info: r"Forecast Hour Latitude Longitude Intensity(.*?)(?:Forecast Track Archive|Track History|About Forecast)" ,
        text,  # info: text ,
        re.I,  # info: re . I ,
    )  # info: )
    if fm:  # info: if fm :
        for m in re.finditer(  # info: for m in re . finditer (
            r"(-?\d+)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(\d{1,3})",  # info: r"(-?\d+)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(\d{1,3})" ,
            fm.group(1),  # info: fm . group ( 1 ) ,
        ):  # info: ) :
            hour, lat, lon, kt = int(m.group(1)), float(m.group(2)), float(m.group(3)), int(m.group(4))  # info: hour , lat , lon , kt =
            if lon > 180:  # info: if lon > 180 :
                lon -= 360  # info: set lon
            forecast.append({"hour": hour, "lat": lat, "lon": lon, "knots": kt})  # info: forecast . append ( { "hour" : hour
    hm = re.search(  # info: set hm
        r"Track History Synoptic Time Latitude Longitude Intensity(.*?)(?:About Track History|Enhanced Infrared|Satellite)",  # info: r"Track History Synoptic Time Latitude Longitude Intensity(.*?)(?:About Track History|Enhanced Infrared|Satell
        text,  # info: text ,
        re.I,  # info: re . I ,
    )  # info: )
    if hm:  # info: if hm :
        for m in re.finditer(  # info: for m in re . finditer (
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(\d{1,3})",  # info: r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(\d{1,3})" ,
            hm.group(1),  # info: hm . group ( 1 ) ,
        ):  # info: ) :
            lat, lon = float(m.group(2)), float(m.group(3))  # info: lat , lon = float ( m .
            if lon > 180:  # info: if lon > 180 :
                lon -= 360  # info: set lon
            history.append({"ts": m.group(1), "lat": lat, "lon": lon, "knots": int(m.group(4))})  # info: history . append ( { "ts" : m
        history.sort(key=lambda r: str(r.get("ts") or ""))  # info: history . sort ( key = lambda r
    return {"forecast": forecast, "history": history}  # info: return { "forecast" : forecast , "history" :


# ====================================================
# SECTION: function course_from_fixes
# What it does: course from fixes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def course_from_fixes(fixes: list[dict[str, Any]]) -> dict[str, Any]:  # info: def course_from_fixes
    pts = [f for f in fixes if isinstance(f.get("lat"), (int, float)) and isinstance(f.get("lon"), (int, float))]  # info: set pts
    if len(pts) < 2:  # info: if len ( pts ) < 2 :
        return {"course_deg": None, "course_compass": None, "course_kt": None, "leg_nm": None}  # info: return { "course_deg" : None , "course_compass" :
    a, b = pts[-2], pts[-1]  # info: a , b = pts [ - 2
    nm = _haversine_nm((float(a["lat"]), float(a["lon"])), (float(b["lat"]), float(b["lon"])))  # info: set nm
    course = bearing_deg(float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"]))  # info: set course
    kt = None  # info: set kt
    ta, tb = str(a.get("ts") or ""), str(b.get("ts") or "")  # info: ta , tb = str ( a .
    if len(ta) >= 16 and len(tb) >= 16 and ta[:16] != tb[:16]:  # info: if len ( ta ) >= 16 and
        try:  # info: try :
            from datetime import datetime  # info: from datetime import datetime

            fa = datetime.fromisoformat(ta.replace("Z", "").replace(" ", "T")[:16])  # info: set fa
            fb = datetime.fromisoformat(tb.replace("Z", "").replace(" ", "T")[:16])  # info: set fb
            hours = abs((fb - fa).total_seconds()) / 3600.0  # info: set hours
            if 0.4 <= hours <= 48:  # info: if 0.4 <= hours <= 48 :
                kt = int(round(nm / hours))  # info: set kt
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            kt = None  # info: set kt
    return {  # info: return {
        "course_deg": round(course, 0),  # info: "course_deg" : round ( course , 0 )
        "course_compass": compass8_word(course),  # info: "course_compass" : compass8_word ( course ) ,
        "course_kt": kt,  # info: "course_kt" : kt ,
        "leg_nm": round(nm, 0),  # info: "leg_nm" : round ( nm , 0 )
    }  # info: }


# ====================================================
# SECTION: function _fmt_pos
# What it does:  fmt pos.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fmt_pos(lat: float, lon: float) -> str:  # info: def _fmt_pos
    ns = "N" if lat >= 0 else "S"  # info: set ns
    ew = "E" if lon >= 0 else "W"  # info: set ew
    return f"{abs(lat):.1f}{ns} {abs(lon):.1f}{ew}"  # info: return f" { abs ( lat ) :


# ====================================================
# SECTION: function forecast_vs_hawaii
# What it does: forecast vs hawaii.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def forecast_vs_hawaii(now_lat: float, now_lon: float, forecast: list[dict[str, Any]]) -> dict[str, Any]:  # info: def forecast_vs_hawaii
    if not forecast:  # info: if not forecast :
        return {  # info: return {
            "summary": "No official forecast track on file.",  # info: "summary" : "No official forecast track on file." ,
            "end_nm": None,  # info: "end_nm" : None ,
            "closer": None,  # info: "closer" : None ,
            "end_region": None,  # info: "end_region" : None ,
        }  # info: }
    end = forecast[-1]  # info: set end
    _, now_nm = nearest_hawaii_nm(now_lat, now_lon)  # info: _ , now_nm = nearest_hawaii_nm ( now_lat ,
    isle, end_nm = nearest_hawaii_nm(float(end["lat"]), float(end["lon"]))  # info: isle , end_nm = nearest_hawaii_nm ( float (
    region = ocean_region(float(end["lat"]), float(end["lon"]))  # info: set region
    closer = end_nm < now_nm - 150 and end_nm < 1800  # info: set closer
    hour = end.get("hour")  # info: set hour
    hour_s = f"hour {hour}" if hour is not None else "end"  # info: set hour_s
    if closer and end_nm < HAWAII_THREAT_NM:  # info: if closer and end_nm < HAWAII_THREAT_NM :
        extra = f" Forecast point comes inside {HAWAII_THREAT_NM:.0f} nmi of {isle}."  # info: set extra
    elif closer:  # info: elif closer :
        extra = f" Forecast comes closer to {isle} but stays outside {HAWAII_THREAT_NM:.0f} nmi on this file."  # info: set extra
    else:  # info: else :
        extra = f" Forecast stays away from Hawaiʻi ({int(end_nm)} nmi from {isle} at {hour_s})."  # info: set extra
    summary = (  # info: set summary
        f"RAMMB forecast on file ends {_fmt_pos(float(end['lat']), float(end['lon']))} "  # info: f" RAMMB forecast on file ends { _fmt_pos ( float ( end
        f"({region['name']}).{extra} Not a landfall call."  # info: call f"
    )  # info: )
    return {  # info: return {
        "summary": summary,  # info: "summary" : summary ,
        "end_nm": end_nm,  # info: "end_nm" : end_nm ,
        "closer": closer,  # info: "closer" : closer ,
        "end_region": region["id"],  # info: "end_region" : region [ "id" ] ,
        "end_lat": end.get("lat"),  # info: "end_lat" : end . get ( "lat" )
        "end_lon": end.get("lon"),  # info: "end_lon" : end . get ( "lon" )
        "end_hour": hour,  # info: "end_hour" : hour ,
    }  # info: }


# ====================================================
# SECTION: function load_tracks
# What it does: load tracks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_tracks() -> dict[str, Any]:  # info: def load_tracks
    path = TRACKS_PATH  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return {}  # info: return { }
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {}  # info: return { }
    return data if isinstance(data, dict) else {}  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function save_tracks
# What it does: save tracks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_tracks(data: dict[str, Any]) -> None:  # info: def save_tracks
    TRACKS_PATH.parent.mkdir(parents=True, exist_ok=True)  # info: TRACKS_PATH . parent . mkdir ( parents =
    tmp = TRACKS_PATH.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(TRACKS_PATH)  # info: tmp . replace ( TRACKS_PATH )


# ====================================================
# SECTION: function attach_track
# What it does: Mutate storm with region, motion, history, official forecast, vs-Hawaiʻi.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def attach_track(storm: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:  # info: def attach_track
    """Mutate storm with region, motion, history, official forecast, vs-Hawaiʻi."""  # info: """Mutate storm with region, motion, history, official forecast, vs-Hawaiʻi."""
    lat, lon = storm.get("lat"), storm.get("lon")  # info: lat , lon = storm . get (
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):  # info: if not isinstance ( lat , ( int
        storm.setdefault("region", None)  # info: storm . setdefault ( "region" , None )
        storm.setdefault("hawaii_approach", "unknown")  # info: storm . setdefault ( "hawaii_approach" , "unknown" )
        return storm  # info: return storm

    region = ocean_region(float(lat), float(lon))  # info: set region
    history = storm.get("track_history") if isinstance(storm.get("track_history"), list) else []  # info: set history
    forecast = storm.get("forecast_track") if isinstance(storm.get("forecast_track"), list) else []  # info: set forecast

    sid = str(storm.get("id") or "").lower()  # info: set sid
    store = load_tracks() if persist else {}  # info: set store
    slot = store.get(sid) if isinstance(store.get(sid), dict) else {}  # info: set slot
    if not history and isinstance(slot.get("history"), list):  # info: if not history and isinstance ( slot .
        history = slot["history"]  # info: set history
    if not forecast and isinstance(slot.get("forecast"), list):  # info: if not forecast and isinstance ( slot .
        forecast = slot["forecast"]  # info: set forecast

    if persist and sid:  # info: if persist and sid :
        if history:  # info: if history :
            slot["history"] = history[-24:]  # info: slot [ "history" ] = history [ -
        if forecast:  # info: if forecast :
            slot["forecast"] = forecast  # info: slot [ "forecast" ] = forecast
        slot["lat"] = lat  # info: slot [ "lat" ] = lat
        slot["lon"] = lon  # info: slot [ "lon" ] = lon
        store[sid] = slot  # info: store [ sid ] = slot
        save_tracks(store)  # info: call save_tracks

    course = course_from_fixes(history) if len(history) >= 2 else {  # info: set course
        "course_deg": None,  # info: "course_deg" : None ,
        "course_compass": None,  # info: "course_compass" : None ,
        "course_kt": None,  # info: "course_kt" : None ,
        "leg_nm": None,  # info: "leg_nm" : None ,
    }  # info: }
    move_deg = storm.get("movement_dir")  # info: set move_deg
    move_kt = storm.get("movement_kt")  # info: set move_kt
    try:  # info: try :
        move_deg_f = float(move_deg) if move_deg is not None else None  # info: set move_deg_f
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        move_deg_f = None  # info: set move_deg_f
    try:  # info: try :
        move_kt_i = int(round(float(move_kt))) if move_kt is not None else None  # info: set move_kt_i
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        move_kt_i = None  # info: set move_kt_i
    if move_deg_f is None and course.get("course_deg") is not None:  # info: if move_deg_f is None and course . get
        move_deg_f = float(course["course_deg"])  # info: set move_deg_f
        storm["movement_dir"] = move_deg_f  # info: storm [ "movement_dir" ] = move_deg_f
        storm["movement_source"] = "track_history"  # info: storm [ "movement_source" ] = "track_history"
    if move_kt_i is None and course.get("course_kt") is not None:  # info: if move_kt_i is None and course . get
        move_kt_i = int(course["course_kt"])  # info: set move_kt_i
        storm["movement_kt"] = move_kt_i  # info: storm [ "movement_kt" ] = move_kt_i
    if move_deg_f is not None and storm.get("movement_source") != "track_history":  # info: if move_deg_f is not None and storm .
        storm["movement_source"] = storm.get("movement_source") or storm.get("source") or "advisory"  # info: storm [ "movement_source" ] = storm . get

    approach = hawaii_approach(float(lat), float(lon), move_deg_f)  # info: set approach
    fc = forecast_vs_hawaii(float(lat), float(lon), forecast)  # info: set fc
    bear = bearing_deg(LIHUE[0], LIHUE[1], float(lat), float(lon))  # info: set bear
    move_word = compass8_word(move_deg_f) if move_deg_f is not None else None  # info: set move_word
    if approach == "toward":  # info: if approach == "toward" :
        vs = "toward Hawaiʻi"  # info: set vs
    elif approach == "away":  # info: elif approach == "away" :
        vs = "away from Hawaiʻi"  # info: set vs
    elif approach == "abeam":  # info: elif approach == "abeam" :
        vs = "abeam of Hawaiʻi (not aimed at the islands)"  # info: set vs
    else:  # info: else :
        vs = "motion vs Hawaiʻi unknown"  # info: set vs
    move_s = ""  # info: set move_s
    if move_word:  # info: if move_word :
        kt_s = f" at {move_kt_i} kt" if move_kt_i is not None else ""  # info: set kt_s
        move_s = f"Moving {move_word}{kt_s}, {vs}."  # info: set move_s
    elif move_kt_i == 0:  # info: elif move_kt_i == 0 :
        move_s = "Nearly stationary."  # info: set move_s
    hist_s = ""  # info: set hist_s
    if len(history) >= 2:  # info: if len ( history ) >= 2 :
        a, b = history[0], history[-1]  # info: a , b = history [ 0 ]
        hist_s = (  # info: set hist_s
            f"RAMMB history {len(history)} fixes: "  # info: f" RAMMB history { len ( history ) }
            f"{_fmt_pos(float(a['lat']), float(a['lon']))} → {_fmt_pos(float(b['lat']), float(b['lon']))}."  # info: f" { _fmt_pos ( float ( a [
        )  # info: )
    track_summary = " ".join(  # info: set track_summary
        x for x in (region["name"] + ".", move_s, hist_s, vs.capitalize() + "." if not move_s else "") if x  # info: x for x in ( region [ "name"
    ).strip()  # info: ) . strip ( )

    storm.update(  # info: storm . update (
        {  # info: {
            "region": region["id"],  # info: "region" : region [ "id" ] ,
            "region_name": region["name"],  # info: "region_name" : region [ "name" ] ,
            "region_note": region["note"],  # info: "region_note" : region [ "note" ] ,
            "hawaii_approach": approach,  # info: "hawaii_approach" : approach ,
            "bearing_from_lihue_deg": round(bear, 0),  # info: "bearing_from_lihue_deg" : round ( bear , 0 )
            "bearing_from_lihue": compass8_word(bear),  # info: "bearing_from_lihue" : compass8_word ( bear ) ,
            "track_history": history,  # info: "track_history" : history ,
            "forecast_track": forecast,  # info: "forecast_track" : forecast ,
            "track_summary": track_summary,  # info: "track_summary" : track_summary ,
            "forecast_summary": fc["summary"],  # info: "forecast_summary" : fc [ "summary" ] ,
            "forecast_closer_to_hawaii": fc["closer"],  # info: "forecast_closer_to_hawaii" : fc [ "closer" ] ,
            "forecast_end_hawaii_nm": fc["end_nm"],  # info: "forecast_end_hawaii_nm" : fc [ "end_nm" ] ,
            "movement_compass": move_word,  # info: "movement_compass" : move_word ,
        }  # info: }
    )  # info: )
    return storm  # info: return storm


# ====================================================
# SECTION: function apply_rammb_page
# What it does: apply rammb page.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_rammb_page(storm: dict[str, Any], html: str) -> dict[str, Any]:  # info: def apply_rammb_page
    parsed = parse_rammb_tracks(html)  # info: set parsed
    if parsed["history"]:  # info: if parsed [ "history" ] :
        storm["track_history"] = parsed["history"]  # info: storm [ "track_history" ] = parsed [ "history"
        last = parsed["history"][-1]  # info: set last
        if storm.get("lat") is None:  # info: if storm . get ( "lat" ) is
            storm["lat"] = last["lat"]  # info: storm [ "lat" ] = last [ "lat"
            storm["lon"] = last["lon"]  # info: storm [ "lon" ] = last [ "lon"
        if not storm.get("knots") and last.get("knots"):  # info: if not storm . get ( "knots" )
            storm["knots"] = last["knots"]  # info: storm [ "knots" ] = last [ "knots"
        storm["updated"] = last.get("ts")  # info: storm [ "updated" ] = last . get
    if parsed["forecast"]:  # info: if parsed [ "forecast" ] :
        storm["forecast_track"] = parsed["forecast"]  # info: storm [ "forecast_track" ] = parsed [ "forecast"
        z = parsed["forecast"][0]  # info: set z
        if storm.get("lat") is None:  # info: if storm . get ( "lat" ) is
            storm["lat"] = z["lat"]  # info: storm [ "lat" ] = z [ "lat"
            storm["lon"] = z["lon"]  # info: storm [ "lon" ] = z [ "lon"
        if z.get("knots") and not storm.get("knots"):  # info: if z . get ( "knots" ) and
            storm["knots"] = z["knots"]  # info: storm [ "knots" ] = z [ "knots"
    return storm  # info: return storm
