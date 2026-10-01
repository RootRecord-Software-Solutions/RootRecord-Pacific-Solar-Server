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

Same Open-Meteo host and Volcano / Puna point as sun_times.py. Daily moon_phase
for 16 days is saved under Database Energy/moon/moon-last.json. The current
phase is the day's value moved forward by the fraction of the HST day toward
tomorrow. A failed fetch keeps the stored file. One HTTP call, 10 s timeout.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import math  # info: import math
import os  # info: import os
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
LAT, LON = 19.43, -155.23  # info: LAT , LON = 19.43 , - 155.23
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
PATH = DB / "Energy" / "moon" / "moon-last.json"  # info: set PATH
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
def phase_name(phase: float) -> str:  # info: def phase_name
    p = phase % 1  # info: set p
    if p < 0.03 or p >= 0.97:  # info: if p < 0.03 or p >= 0.97 :
        return "New Moon"  # info: return "New Moon"
    if p < 0.22:  # info: if p < 0.22 :
        return "Waxing Crescent"  # info: return "Waxing Crescent"
    if p < 0.28:  # info: if p < 0.28 :
        return "First Quarter"  # info: return "First Quarter"
    if p < 0.47:  # info: if p < 0.47 :
        return "Waxing Gibbous"  # info: return "Waxing Gibbous"
    if p < 0.53:  # info: if p < 0.53 :
        return "Full Moon"  # info: return "Full Moon"
    if p < 0.72:  # info: if p < 0.72 :
        return "Waning Gibbous"  # info: return "Waning Gibbous"
    if p < 0.78:  # info: if p < 0.78 :
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


# ====================================================
# SECTION: function _phase_now
# What it does: Move today's phase toward tomorrow by the fraction of the HST day.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _phase_now(today_phase: float, next_phase, now: datetime) -> float:  # info: def _phase_now
    if next_phase is None:  # info: if next_phase is None :
        return float(today_phase) % 1  # info: return float ( today_phase ) % 1
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)  # info: set start
    frac = (now - start).total_seconds() / 86400  # info: set frac
    start_phase = float(today_phase)  # info: set start_phase
    end_phase = float(next_phase)  # info: set end_phase
    if end_phase < start_phase - 0.5:  # info: if end_phase < start_phase - 0.5 :
        end_phase += 1  # info: set end_phase
    return (start_phase + (end_phase - start_phase) * frac) % 1  # info: return ( start_phase + ( end_phase - start_phase


# ====================================================
# SECTION: function _unwrap
# What it does: Keep the daily phase series increasing across a new moon.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _unwrap(dates: list, phases: list) -> list[tuple[str, float]]:  # info: def _unwrap
    rows: list[tuple[str, float]] = []  # info: set rows
    previous = None  # info: set previous
    for date, phase in zip(dates, phases):  # info: for date , phase in zip ( dates , phases )
        if phase is None:  # info: if phase is None :
            continue  # info: continue
        try:  # info: try :
            value = float(phase)  # info: set value
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            continue  # info: continue
        carried = value  # info: set carried
        if previous is not None and value < previous - 0.5:  # info: if previous is not None and value < previous
            carried = value + 1  # info: set carried
        rows.append((str(date), carried))  # info: rows . append ( ( str ( date ) , carried
        previous = carried  # info: set previous
    return rows  # info: return rows


# ====================================================
# SECTION: function _next_named
# What it does: Date of the next new, quarter, or full moon in the pulled series.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _next_named(rows: list[tuple[str, float]], today: str, current: float) -> tuple[str | None, str | None]:  # info: def _next_named
    today_row = next((row for row in rows if row[0] == today), None)  # info: set today_row
    base = today_row[1] if today_row else current  # info: set base
    target = next((mark for mark, _name in _TARGETS if mark > base + 0.02), None)  # info: set target
    if target is None:  # info: if target is None :
        return None, None  # info: return None , None
    name = dict(_TARGETS)[target]  # info: set name
    best = None  # info: set best
    for date, value in rows:  # info: for date , value in rows :
        if date <= today:  # info: if date <= today :
            continue  # info: continue
        dist = abs(value - target)  # info: set dist
        if best is None or dist < best[0]:  # info: if best is None or dist < best [ 0 ] :
            best = (dist, date)  # info: set best
    if best is None or best[0] > 0.08:  # info: if best is None or best [ 0 ] > 0.08 :
        return None, None  # info: return None , None
    return name, best[1]  # info: return name , best [ 1 ]


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
        phases = daily.get("moon_phase") or []  # info: set phases
        rises = daily.get("moonrise") or []  # info: set rises
        sets = daily.get("moonset") or []  # info: set sets
        today = _today()  # info: set today
        if today not in dates:  # info: if today not in dates :
            return dict(stored, ok=bool(stored.get("phase") is not None), refreshed=False, error="no phase for today")  # info: return dict ( stored , ok = bool (
        index = dates.index(today)  # info: set index
        today_phase = phases[index] if index < len(phases) else None  # info: set today_phase
        if today_phase is None:  # info: if today_phase is None :
            return dict(stored, ok=bool(stored.get("phase") is not None), refreshed=False, error="empty moon phase")  # info: return dict ( stored , ok = bool (
        tomorrow = phases[index + 1] if index + 1 < len(phases) else None  # info: set tomorrow
        now = _now()  # info: set now
        phase = _phase_now(float(today_phase), tomorrow, now)  # info: set phase
        rows = _unwrap(dates, phases)  # info: set rows
        next_name, next_date = _next_named(rows, today, phase)  # info: next_name , next_date = _next_named ( rows , today , phase
        payload = {  # info: set payload
            "date": today,  # info: "date" : today ,
            "phase": round(phase, 4),  # info: "phase" : round ( phase , 4 ) ,
            "phase_day": round(float(today_phase), 4),  # info: "phase_day" : round ( float ( today_phase ) , 4 ) ,
            "phase_name": phase_name(phase),  # info: "phase_name" : phase_name ( phase ) ,
            "illumination": illumination_pct(phase),  # info: "illumination" : illumination_pct ( phase ) ,
            "moonrise": _hhmm_from_iso(rises[index] if index < len(rises) else None),  # info: "moonrise" : _hhmm_from_iso ( rises [ index ] if
            "moonset": _hhmm_from_iso(sets[index] if index < len(sets) else None),  # info: "moonset" : _hhmm_from_iso ( sets [ index ] if
            "next_phase": next_name,  # info: "next_phase" : next_name ,
            "next_phase_date": next_date,  # info: "next_phase_date" : next_date ,
            "source": "open-meteo",  # info: "source" : "open-meteo" ,
            "lat": LAT,  # info: "lat" : LAT ,
            "lon": LON,  # info: "lon" : LON ,
            "fetched_at": now.isoformat(),  # info: "fetched_at" : now . isoformat ( ) ,
        }  # info: }
        if index + 1 < len(dates):  # info: if index + 1 < len ( dates ) :
            payload["next_date"] = dates[index + 1]  # info: payload [ "next_date" ] = dates [ index + 1
        return dict(write(payload), ok=True, refreshed=True)  # info: return dict ( write ( payload ) , ok = True , refreshed = True
    except Exception as exc:  # noqa: BLE001
        return dict(stored, ok=bool(stored.get("phase") is not None), refreshed=False, error=f"{type(exc).__name__}: {exc}"[:200])  # info: return dict ( stored , ok = bool (


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    result = refresh_if_stale(force="--force" in sys.argv)  # info: set result
    kept = {key: result.get(key) for key in ("ok", "date", "phase", "phase_name", "illumination", "next_phase", "next_phase_date", "refreshed", "error")}  # info: set kept
    print(json.dumps(kept))  # info: call print
    raise SystemExit(0 if result.get("ok") else 1)  # info: raise SystemExit ( 0 if result . get ( "ok" ) else 1
