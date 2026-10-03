# ==============================================================================
# FILE: Energy/scripts/moon_phase.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Current moon phase for Hawaiʻi, pulled and saved.

  python3 moon_phase.py [--force]

Same Open-Meteo host and Volcano / Puna point as sun_times.py. Moonrise and
moonset are saved from that pull. The phase and illumination are the sky at
the fetch instant, not the daily phase number walked forward through the day.
A failed fetch keeps the stored file. One HTTP call, 10 s timeout.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import math  # info: import math
import os  # info: import os
import sys  # info: import sys
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
LAT, LON = 19.43, -155.23  # info: LAT , LON = 19.43 , - 155.23
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
PATH = DB / "Weather" / "moon" / "moon_current.json"  # info: moon lives under Weather, stable *_current bank
LEGACY_PATH = DB / "Energy" / "moon" / "moon-last.json"  # info: read-only fallback while old path drains
OPEN_METEO = ("https://api.open-meteo.com/v1/forecast"  # info: set OPEN_METEO
              f"?latitude={LAT}&longitude={LON}&daily=moon_phase,moonrise,moonset"  # info: f" ?latitude= { LAT } &longitude= { LON
              "&timezone=Pacific/Honolulu&forecast_days=16")  # info: "&timezone=Pacific/Honolulu&forecast_days=16" )
UA = "RootRecord-Pacific-Energy/1.0 (+https://rootrecord.cloud)"  # info: set UA
STALE_SEC = 50 * 60  # info: set STALE_SEC
_TARGETS = ((0.25, "First Quarter"), (0.5, "Full Moon"), (0.75, "Last Quarter"), (1.0, "New Moon"))  # info: set _TARGETS


# ====================================================
# SECTION: function _now
# What it does: Current instant in Hawaiʻi time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now() -> datetime:  # info: def _now
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function _today
# What it does: Today as YYYY-MM-DD in Hawaiʻi.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _today() -> str:  # info: def _today
    return _now().strftime("%Y-%m-%d")  # info: return _now ( ) . strftime ( "%Y-%m-%d" )


# ====================================================
# SECTION: function read
# What it does: Read the saved moon file, or an empty dict.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read() -> dict:  # info: def read
    try:  # info: try :
        raw = json.loads(PATH.read_text(encoding="utf-8"))  # info: set raw
        return raw if isinstance(raw, dict) else {}  # info: return raw if isinstance ( raw , dict
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return {}  # info: return { }


# ====================================================
# SECTION: function write
# What it does: Atomically replace the saved moon file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write(payload: dict) -> dict:  # info: def write
    PATH.parent.mkdir(parents=True, exist_ok=True)  # info: PATH . parent . mkdir ( parents =
    tmp = PATH.with_name(PATH.name + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, PATH)  # info: os . replace ( tmp , PATH )
    return payload  # info: return payload


# ====================================================
# SECTION: function _hhmm_from_iso
# What it does: Clock HH:MM from an Open-Meteo local timestamp.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _hhmm_from_iso(iso) -> str | None:  # info: def _hhmm_from_iso
    raw = str(iso or "").strip()  # info: set raw
    if "T" not in raw:  # info: if "T" not in raw :
        return None  # info: return None
    clock = raw.split("T", 1)[1][:5]  # info: set clock
    return clock if len(clock) == 5 else None  # info: return clock if len ( clock ) == 5 else None


# ====================================================
# SECTION: function phase_name
# What it does: Name a 0–1 moon phase. 0 is new, 0.5 is full.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def phase_name(phase: float, lit: float | None = None) -> str:  # info: def phase_name
    p = phase % 1  # info: set p
    near_half = lit is None or 45 <= lit <= 55  # info: set near_half
    if p < 0.03 or p >= 0.97:  # info: if p < 0.03 or p >= 0.97 :
        return "New Moon"  # info: return "New Moon"
    if p < 0.22:  # info: if p < 0.22 :
        return "Waxing Crescent"  # info: return "Waxing Crescent"
    if p < 0.28:  # info: if p < 0.28 :
        return "First Quarter" if near_half else "Waxing Crescent"  # info: return quarter only near half
    if p < 0.47:  # info: if p < 0.47 :
        return "Waxing Gibbous"  # info: return "Waxing Gibbous"
    if p < 0.53:  # info: if p < 0.53 :
        return "Full Moon"  # info: return "Full Moon"
    if p < 0.72:  # info: if p < 0.72 :
        return "Waning Gibbous"  # info: return "Waning Gibbous"
    if p < 0.78:  # info: if p < 0.78 :
        if not near_half:  # info: if the disc is not near half
            return "Waning Gibbous" if (lit or 0) > 55 else "Waning Crescent"  # info: stay gibbous or crescent
        return "Last Quarter"  # info: return "Last Quarter"
    return "Waning Crescent"  # info: return "Waning Crescent"


# ====================================================
# SECTION: function illumination_pct
# What it does: Lit fraction of the disc as a percent from the phase number.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def illumination_pct(phase: float) -> int:  # info: def illumination_pct
    lit = (1 - math.cos(2 * math.pi * (phase % 1))) / 2  # info: set lit
    return int(round(lit * 100))  # info: return int ( round ( lit * 100 ) )


_RAD = math.pi / 180  # info: set _RAD
_OBLIQ = _RAD * 23.4397  # info: set _OBLIQ
_J1970 = 2440588  # info: set _J1970
_J2000 = 2451545  # info: set _J2000


# ====================================================
# SECTION: function _sky
# What it does: Phase 0–1 and lit fraction at an instant. 0 is new, 0.5 is full.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _sky(moment: datetime) -> tuple[float, float]:  # info: def _sky
    instant = moment.astimezone(HST)  # info: set instant
    day = instant.timestamp() / 86400 - 0.5 + _J1970 - _J2000  # info: set day

    def right_ascension(lng: float, lat: float) -> float:  # info: def right_ascension
        return math.atan2(math.sin(lng) * math.cos(_OBLIQ) - math.tan(lat) * math.sin(_OBLIQ), math.cos(lng))  # info: return math . atan2 ( math . sin ( lng ) * math . cos ( _OBLIQ ) - math . tan ( lat ) * math . sin ( _OBLIQ ) , math . cos ( lng ) )

    def declination(lng: float, lat: float) -> float:  # info: def declination
        return math.asin(math.sin(lat) * math.cos(_OBLIQ) + math.cos(lat) * math.sin(_OBLIQ) * math.sin(lng))  # info: return math . asin ( math . sin ( lat ) * math . cos ( _OBLIQ ) + math . cos ( lat ) * math . sin ( _OBLIQ ) * math . sin ( lng ) )

    mean = _RAD * (357.5291 + 0.98560028 * day)  # info: set mean
    center = _RAD * (1.9148 * math.sin(mean) + 0.02 * math.sin(2 * mean) + 0.0003 * math.sin(3 * mean))  # info: set center
    sun_lng = mean + center + _RAD * 102.9372 + math.pi  # info: set sun_lng
    sun_dec, sun_ra = declination(sun_lng, 0.0), right_ascension(sun_lng, 0.0)  # info: sun_dec , sun_ra = declination ( sun_lng , 0.0 ) , right_ascension ( sun_lng , 0.0 )
    moon_mean = _RAD * (134.963 + 13.064993 * day)  # info: set moon_mean
    moon_lng = _RAD * (218.316 + 13.176396 * day) + _RAD * 6.289 * math.sin(moon_mean)  # info: set moon_lng
    moon_lat = _RAD * 5.128 * math.sin(_RAD * (93.272 + 13.229350 * day))  # info: set moon_lat
    moon_ra, moon_dec = right_ascension(moon_lng, moon_lat), declination(moon_lng, moon_lat)  # info: moon_ra , moon_dec = right_ascension ( moon_lng , moon_lat ) , declination ( moon_lng , moon_lat )
    moon_dist = 385001 - 20905 * math.cos(moon_mean)  # info: set moon_dist
    sep = math.acos(max(-1.0, min(1.0, math.sin(sun_dec) * math.sin(moon_dec) + math.cos(sun_dec) * math.cos(moon_dec) * math.cos(sun_ra - moon_ra))))  # info: set sep
    inc = math.atan2(149598000 * math.sin(sep), moon_dist - 149598000 * math.cos(sep))  # info: set inc
    angle = math.atan2(math.cos(sun_dec) * math.sin(sun_ra - moon_ra), math.sin(sun_dec) * math.cos(moon_dec) - math.cos(sun_dec) * math.sin(moon_dec) * math.cos(sun_ra - moon_ra))  # info: set angle
    phase = (0.5 + 0.5 * inc * (-1 if angle < 0 else 1) / math.pi) % 1  # info: set phase
    lit = (1 + math.cos(inc)) / 2  # info: set lit
    return phase, lit  # info: return phase , lit


# ====================================================
# SECTION: function _next_named
# What it does: Hawaiʻi date of the next new, quarter, or full moon after now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _next_named(now: datetime, phase: float) -> tuple[str | None, str | None]:  # info: def _next_named
    target = next((mark for mark, _name in _TARGETS if mark > phase + 0.01), None)  # info: set target
    if target is None:  # info: if target is None :
        return None, None  # info: return None , None
    name = dict(_TARGETS)[target]  # info: set name
    previous = phase  # info: set previous
    for step in range(1, 20 * 48):  # info: for step in range ( 1 , 20 * 48 ) :
        moment = now + timedelta(minutes=30 * step)  # info: set moment
        current, _lit = _sky(moment)  # info: current , _lit = _sky ( moment )
        crossed = previous < target <= current or (target == 1 and current < previous)  # info: set crossed
        if crossed:  # info: if crossed :
            return name, moment.astimezone(HST).strftime("%Y-%m-%d")  # info: return name , moment . astimezone ( HST ) . strftime ( "%Y-%m-%d" )
        previous = current  # info: set previous
    return None, None  # info: return None , None


# ====================================================
# SECTION: function _fresh
# What it does: True when the saved file is for today and younger than the stale window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fresh(stored: dict) -> bool:  # info: def _fresh
    if stored.get("date") != _today() or stored.get("phase") is None:  # info: if stored . get ( "date" ) != _today ( )
        return False  # info: return False
    stamp = str(stored.get("fetched_at") or "")  # info: set stamp
    try:  # info: try :
        fetched = datetime.fromisoformat(stamp)  # info: set fetched
    except ValueError:  # info: except ValueError :
        return False  # info: return False
    if fetched.tzinfo is None:  # info: if fetched . tzinfo is None :
        fetched = fetched.replace(tzinfo=HST)  # info: set fetched
    return (_now() - fetched).total_seconds() < STALE_SEC  # info: return ( _now ( ) - fetched ) . total_seconds ( ) < STALE_SEC


# ====================================================
# SECTION: function refresh_if_stale
# What it does: Pull Open-Meteo when the saved moon file is stale. Keep the file on failure.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def refresh_if_stale(*, force: bool = False) -> dict:  # info: def refresh_if_stale
    stored = read()  # info: set stored
    if not force and _fresh(stored):  # info: if not force and _fresh ( stored ) :
        return dict(stored, ok=True, refreshed=False)  # info: return dict ( stored , ok = True , refreshed = False
    try:  # info: try :
        with urlopen(Request(OPEN_METEO, headers={"User-Agent": UA}), timeout=10) as response:  # info: with urlopen ( Request ( OPEN_METEO , headers
            daily = (json.loads(response.read().decode("utf-8")) or {}).get("daily") or {}  # info: set daily
        dates = daily.get("time") or []  # info: set dates
        rises = daily.get("moonrise") or []  # info: set rises
        sets = daily.get("moonset") or []  # info: set sets
        today = _today()  # info: set today
        index = dates.index(today) if today in dates else -1  # info: set index
        now = _now()  # info: set now
        phase, lit = _sky(now)  # info: phase , lit = _sky ( now )
        lit_pct = int(round(lit * 100))  # info: set lit_pct
        phases = daily.get("moon_phase") or []  # info: set phases
        if 0 <= index < len(phases):  # info: if the calendar phase is present
            try:  # info: try
                meteo = float(phases[index])  # info: set meteo
                meteo_pct = illumination_pct(meteo)  # info: set meteo_pct
                if abs(meteo_pct - lit_pct) > 5:  # info: if the two percents disagree
                    phase, lit_pct = meteo, meteo_pct  # info: keep the calendar-day phase
            except (TypeError, ValueError):  # info: except
                pass  # info: pass
        next_name, next_date = _next_named(now, phase)  # info: next_name , next_date = _next_named ( now , phase )
        payload = {  # info: set payload
            "date": today,  # info: "date" : today ,
            "phase": round(phase, 4),  # info: "phase" : round ( phase , 4 ) ,
            "phase_name": phase_name(phase, lit_pct),  # info: "phase_name" : phase_name ( phase , lit_pct ) ,
            "illumination": lit_pct,  # info: "illumination" : lit_pct ,
            "moonrise": _hhmm_from_iso(rises[index] if 0 <= index < len(rises) else None),  # info: "moonrise" : _hhmm_from_iso ( rises [ index ] if 0 <= index
            "moonset": _hhmm_from_iso(sets[index] if 0 <= index < len(sets) else None),  # info: "moonset" : _hhmm_from_iso ( sets [ index ] if 0 <= index
            "next_phase": next_name,  # info: "next_phase" : next_name ,
            "next_phase_date": next_date,  # info: "next_phase_date" : next_date ,
            "source": "calculated",  # info: "source" : "calculated" ,
            "lat": LAT,  # info: "lat" : LAT ,
            "lon": LON,  # info: "lon" : LON ,
            "fetched_at": now.isoformat(),  # info: "fetched_at" : now . isoformat ( ) ,
        }  # info: }
        if index >= 0 and index + 1 < len(dates):  # info: if index >= 0 and index + 1 < len ( dates ) :
            payload["next_date"] = dates[index + 1]  # info: payload [ "next_date" ] = dates [ index + 1
        return dict(write(payload), ok=True, refreshed=True)  # info: return dict ( write ( payload ) , ok = True , refreshed = True
    except Exception as exc:  # noqa: BLE001
        return dict(stored, ok=bool(stored.get("phase") is not None), refreshed=False, error=f"{type(exc).__name__}: {exc}"[:200])  # info: return dict ( stored , ok = bool (


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    result = refresh_if_stale(force="--force" in sys.argv)  # info: set result
    kept = {key: result.get(key) for key in ("ok", "date", "phase", "phase_name", "illumination", "next_phase", "next_phase_date", "refreshed", "error")}  # info: set kept
    print(json.dumps(kept))  # info: call print
    raise SystemExit(0 if result.get("ok") else 1)  # info: raise SystemExit ( 0 if result . get ( "ok" ) else 1
