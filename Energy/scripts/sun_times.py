# ==============================================================================
# FILE: Energy/scripts/sun_times.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Daily sunrise / sunset in Hawaiʻi time (G3 port of G1 reports/sort/hourly-solar-weather/scripts/sun_times.py).

  python3 sun_times.py [refresh|facts] [--force]

Stdlib port: same Open-Meteo query (19.43, -155.23 — Volcano / Puna, "same patch as the weather desk"), same payload
keys (date, sunrise, sunset, *_iso, next_*), same refresh-if-stale rule (one fetch per HST day unless --force) and the
same facts() fields (after_sunset / before_sunrise). State file moved from G1 STATE_DIR/sun-times.json to Database
Energy/sun/sun-times-last.json (solar context for the Energy desk). A failed fetch keeps the stored file.
Light: one HTTP call, 10 s timeout. Schedule: hourly is plenty (jobs.py, on unless RR_SUN_TIMES=0). Live numbers only.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
LAT, LON = 19.43, -155.23  # info: LAT , LON = 19.43 , - 155.23
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
PATH = DB / "Energy" / "sun" / "sun-times-last.json"  # info: set PATH
OPEN_METEO = ("https://api.open-meteo.com/v1/forecast"  # info: set OPEN_METEO
              f"?latitude={LAT}&longitude={LON}&daily=sunrise,sunset&timezone=Pacific/Honolulu&forecast_days=2")  # info: f" ?latitude= { LAT } &longitude= { LON
UA = "RootRecord-Pacific-Energy/1.0 (+https://rootrecord.cloud)"  # info: set UA


# ====================================================
# SECTION: function _today
# What it does:  today.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _today() -> str:  # info: def _today
    return datetime.now(HST).strftime("%Y-%m-%d")  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function read
# What it does: read.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read() -> dict:  # info: def read
    try:  # info: try :
        raw = json.loads(PATH.read_text(encoding="utf-8"))  # info: set raw
        return raw if isinstance(raw, dict) else {}  # info: return raw if isinstance ( raw , dict
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return {}  # info: return { }


# ====================================================
# SECTION: function _hhmm_from_iso
# What it does:  hhmm from iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _hhmm_from_iso(iso: str) -> str:  # info: def _hhmm_from_iso
    raw = str(iso or "").strip()  # info: set raw
    if "T" in raw:  # info: if "T" in raw :
        raw = raw.split("T", 1)[1]  # info: set raw
    return raw[:5]  # info: return raw [ : 5 ]


# ====================================================
# SECTION: function write
# What it does: write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write(payload: dict) -> dict:  # info: def write
    PATH.parent.mkdir(parents=True, exist_ok=True)  # info: PATH . parent . mkdir ( parents =
    tmp = PATH.with_name(PATH.name + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, PATH)  # info: os . replace ( tmp , PATH )
    return payload  # info: return payload


# ====================================================
# SECTION: function refresh_if_stale
# What it does: refresh if stale.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def refresh_if_stale(*, force: bool = False) -> dict:  # info: def refresh_if_stale
    stored = read()  # info: set stored
    if not force and stored.get("date") == _today() and stored.get("sunrise") and stored.get("sunset"):  # info: if not force and stored . get (
        return dict(stored, refreshed=False)  # info: return dict ( stored , refreshed = False
    try:  # info: try :
        with urlopen(Request(OPEN_METEO, headers={"User-Agent": UA}), timeout=10) as r:  # info: with urlopen ( Request ( OPEN_METEO , headers
            daily = (json.loads(r.read().decode("utf-8")) or {}).get("daily") or {}  # info: set daily
        times = daily.get("time") or []  # info: set times
        rises, sets = daily.get("sunrise") or [], daily.get("sunset") or []  # info: rises , sets = daily . get (
        today = _today()  # info: set today
        if times and today not in times:  # info: if times and today not in times :
            return dict(stored, refreshed=False, error="today missing from forecast")  # info: return dict ( stored , refreshed = False
        idx = times.index(today) if today in times else 0  # info: set idx
        if idx >= len(rises) or idx >= len(sets) or not rises or not sets:  # info: if idx >= len ( rises ) or idx >= len ( sets ) or not rises or not sets :
            return dict(stored, refreshed=False, error="no daily sunrise/sunset")  # info: return dict ( stored , refreshed = False
        payload = {"date": times[idx] if idx < len(times) else today, "sunrise": _hhmm_from_iso(rises[idx]), "sunset": _hhmm_from_iso(sets[idx]),  # info: set payload
                   "sunrise_iso": rises[idx], "sunset_iso": sets[idx], "source": "open-meteo", "lat": LAT, "lon": LON,  # info: "sunrise_iso" : rises [ idx ] , "sunset_iso"
                   "fetched_at": datetime.now(HST).replace(microsecond=0).isoformat()}  # info: "fetched_at" : datetime . now ( HST )
        nxt = idx + 1  # info: set nxt
        if nxt < len(rises):  # info: if nxt < len ( rises ) :
            payload["next_date"] = times[nxt] if nxt < len(times) else (datetime.now(HST) + timedelta(days=1)).strftime("%Y-%m-%d")  # info: payload [ "next_date" ] = times [ nxt ] if nxt < len ( times ) else ( datetime
            payload["next_sunrise"] = _hhmm_from_iso(rises[nxt])  # info: payload [ "next_sunrise" ] = _hhmm_from_iso ( rises
            payload["next_sunrise_iso"] = rises[nxt]  # info: payload [ "next_sunrise_iso" ] = rises [ nxt
        return dict(write(payload), refreshed=True)  # info: return dict ( write ( payload ) ,
    except Exception as e:  # noqa: BLE001
        return dict(stored, refreshed=False, error=f"{type(e).__name__}: {e}"[:200])  # info: return dict ( stored , refreshed = False


# ====================================================
# SECTION: function parse_hhmm
# What it does: parse hhmm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_hhmm(value: str) -> tuple[int, int] | None:  # info: def parse_hhmm
    raw = str(value or "").strip()  # info: set raw
    if ":" not in raw:  # info: if ":" not in raw :
        return None  # info: return None
    hh, mm = raw.split(":", 1)  # info: hh , mm = raw . split (
    try:  # info: try :
        h, m = int(hh), int(mm[:2])  # info: h , m = int ( hh )
    except ValueError:  # info: except ValueError :
        return None  # info: return None
    return (h, m) if 0 <= h <= 23 and 0 <= m <= 59 else None  # info: return ( h , m ) if 0


# ====================================================
# SECTION: function _at_today
# What it does:  at today.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _at_today(hhmm: str) -> datetime | None:  # info: def _at_today
    parsed = parse_hhmm(hhmm)  # info: set parsed
    if not parsed:  # info: if not parsed :
        return None  # info: return None
    return datetime.now(HST).replace(hour=parsed[0], minute=parsed[1], second=0, microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function facts
# What it does: facts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def facts(force: bool = False) -> dict:  # info: def facts
    stored = refresh_if_stale(force=force)  # info: set stored
    now = datetime.now(HST)  # info: set now
    rise, sett = _at_today(stored.get("sunrise") or ""), _at_today(stored.get("sunset") or "")  # info: rise , sett = _at_today ( stored .
    return {"ok": bool(stored.get("sunrise") and stored.get("sunset")), "date": stored.get("date") or _today(),  # info: return { "ok" : bool ( stored .
            "sunrise": stored.get("sunrise") or "", "sunset": stored.get("sunset") or "",  # info: "sunrise" : stored . get ( "sunrise" )
            "sunrise_iso": stored.get("sunrise_iso"), "sunset_iso": stored.get("sunset_iso"),  # info: "sunrise_iso" : stored . get ( "sunrise_iso" )
            "after_sunset": bool(sett and now > sett), "before_sunrise": bool(rise and now < rise),  # info: "after_sunset" : bool ( sett and now >
            "source": stored.get("source") or "", "now_hst": now.strftime("%H:%M"),  # info: "source" : stored . get ( "source" )
            "refreshed": stored.get("refreshed"), "error": stored.get("error")}  # info: "refreshed" : stored . get ( "refreshed" )


# ====================================================
# SECTION: function in_day_start_window
# What it does: First desk-awake after sunrise and before 14:00 HST (G1, unchanged).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def in_day_start_window(now: datetime | None = None) -> bool:  # info: def in_day_start_window
    """First desk-awake after sunrise and before 14:00 HST (G1, unchanged)."""  # info: """First desk-awake after sunrise and before 14:00 HST (G1, unchanged)."""
    now = now or datetime.now(HST)  # info: set now
    if now.hour >= 14:  # info: if now . hour >= 14 :
        return False  # info: return False
    rise = _at_today((read() or refresh_if_stale()).get("sunrise") or "06:00")  # info: set rise
    if rise is None:  # info: if rise is None :
        return 6 <= now.hour < 14  # info: return 6 <= now . hour < 14
    return now >= rise and now.hour < 14  # info: return now >= rise and now . hour


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    out = facts(force="--force" in sys.argv)  # info: set out
    print(json.dumps(out))  # info: call print
    raise SystemExit(0 if out["ok"] else 1)  # info: raise SystemExit ( 0 if out [ "ok"
