# ==============================================================================
# FILE: Communications/live-wx/scripts/live_wx.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Live NWS + hurricane lines for chat (G3 port of G1 weather/live-wx/scripts/live_wx.py, 2026-09-29). Do not invent.

  python3 live_wx.py            point forecast from api.weather.gov (one GET chain, 10 s timeout) + alerts/hurricane from Database
  python3 live_wx.py --offline  no HTTP: alerts + hurricane lines from Database only (forecast line says DOWN)

Ported unchanged: _pick_period (prefer tonight after 18:00 / before 05:00), _period_line, _alert_line (Big Island grouping),
_wx_period_lines (current + next two periods). Changed: G1 used httpx + the origin app's markdown / hurricane services;
G3 uses urllib, reads NWS HI alerts from the weather poller's Database file, and the nearest storm from
Media/Voice/scripts/voice_reports.py hurricane_facts (G3 track.json). On demand only; not wired to council chat (BLOCKED).
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
import sys  # info: import sys
import urllib.request  # info: import urllib . request
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parents[2]  # info: set PACIFIC
sys.path.insert(0, str(PACIFIC / "Media" / "Voice" / "scripts"))  # info: sys . path . insert ( 0 ,
import voice_reports as vr  # noqa: E402  (ALERTS path, hurricane_facts; module import has no side effects)

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
UA = {"User-Agent": "RootRecord-Pacific/3 (live-wx; contact via rootrecord)", "Accept": "application/geo+json"}  # info: set UA
POINT = "https://api.weather.gov/points/19.5429,-155.0372"  # G1 point (Puna / Volcano side)
TIMEOUT = 10  # info: set TIMEOUT


# ====================================================
# SECTION: function _pick_period
# What it does:  pick period.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pick_period(periods: list[dict], hour: int) -> dict | None:  # info: def _pick_period
    if not periods:  # info: if not periods :
        return None  # info: return None
    if hour >= 18 or hour < 5:  # info: if hour >= 18 or hour < 5
        for p in periods:  # info: for p in periods :
            if "tonight" in str(p.get("name") or "").lower():  # info: if "tonight" in str ( p . get
                return p  # info: return p
        if "afternoon" in str(periods[0].get("name") or "").lower() and len(periods) > 1:  # info: if "afternoon" in str ( periods [ 0
            return periods[1]  # info: return periods [ 1 ]
    return periods[0]  # info: return periods [ 0 ]


# ====================================================
# SECTION: function _period_line
# What it does:  period line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _period_line(p: dict) -> str:  # info: def _period_line
    name = p.get("name") or "?"  # info: set name
    temp = p.get("temperature")  # info: set temp
    unit = p.get("temperatureUnit") or "F"  # info: set unit
    bits = [f"{name}", f"{temp}{unit}" if temp is not None else ""]  # info: set bits
    if p.get("shortForecast"):  # info: if p . get ( "shortForecast" ) :
        bits.append(str(p["shortForecast"]))  # info: bits . append ( str ( p [
    if p.get("windSpeed"):  # info: if p . get ( "windSpeed" ) :
        bits.append(f"wind {p['windSpeed']}")  # info: bits . append ( f" wind { p
    if p.get("windGust"):  # info: if p . get ( "windGust" ) :
        bits.append(f"gusts {p['windGust']}")  # info: bits . append ( f" gusts { p
    return ", ".join(b for b in bits if b)  # info: return ", " . join ( b for b


# ====================================================
# SECTION: function _alert_line
# What it does:  alert line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _alert_line(alerts: list[dict]) -> str:  # info: def _alert_line
    if not alerts:  # info: if not alerts :
        return "HI alerts: none active"  # info: return "HI alerts: none active"
    grouped: dict[str, bool] = {}  # info: set grouped
    order: list[str] = []  # info: set order
    for a in alerts[:8]:  # info: for a in alerts [ : 8 ]
        ev = str(a.get("event") or "alert")  # info: set ev
        bi = bool(re.search(r"Big Island|Puna|Kona|Hilo|Kohala|Kaʻū|Kau", str(a.get("areas") or ""), re.I))  # info: set bi
        if ev not in grouped:  # info: if ev not in grouped :
            order.append(ev)  # info: order . append ( ev )
            grouped[ev] = bi  # info: grouped [ ev ] = bi
        else:  # info: else :
            grouped[ev] = grouped[ev] or bi  # info: grouped [ ev ] = grouped [ ev
    return "HI alerts: " + "; ".join(f"{ev} (Big Island in area)" if grouped[ev] else ev for ev in order)  # info: return "HI alerts: " + "; " . join ( f"


# ====================================================
# SECTION: function _get
# What it does:  get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(url: str) -> dict:  # info: def _get
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:  # info: with urllib . request . urlopen ( urllib
        return json.loads(r.read(2_000_000))  # info: return json . loads ( r . read


# ====================================================
# SECTION: function forecast_periods
# What it does: forecast periods.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def forecast_periods() -> tuple[list[dict], str]:  # info: def forecast_periods
    try:  # info: try :
        fc = (_get(POINT).get("properties") or {}).get("forecast")  # info: set fc
        periods = ((_get(fc).get("properties") or {}).get("periods") or []) if fc else []  # info: set periods
        return periods, "live NWS " + datetime.now(HST).strftime("%H:%M HST")  # info: return periods , "live NWS " + datetime . now
    except Exception as e:  # noqa: BLE001
        return [], f"NWS fetch failed: {type(e).__name__}"  # info: return [ ] , f" NWS fetch failed: { type


# ====================================================
# SECTION: function alerts_from_db
# What it does: alerts from db.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def alerts_from_db() -> tuple[list[dict], str]:  # info: def alerts_from_db
    try:  # info: try :
        d = json.loads(vr.ALERTS.read_text(encoding="utf-8"))  # info: set d
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return [], "alerts file missing"  # info: return [ ] , "alerts file missing"
    out = [{"event": (f.get("properties") or {}).get("event") or "Unknown",  # info: set out
            "areas": (f.get("properties") or {}).get("areaDesc") or ""} for f in (d.get("features") or [])[:8]]  # info: call "areas"
    return out, f"alerts file updated {d.get('updated') or '?'}"  # info: return out , f" alerts file updated { d .


# ====================================================
# SECTION: function hurricane_line
# What it does: hurricane line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hurricane_line() -> str:  # info: def hurricane_line
    storms = [s for s in vr.hurricane_facts(datetime.now(HST)) if s.get("active")]  # info: set storms
    if not storms:  # info: if not storms :
        return "Nearest Hurricane from a Hawaiian island: none on the board."  # info: return "Nearest Hurricane from a Hawaiian island: none on the board."
    s = storms[0]  # info: set s
    if s["nm"] >= vr.HAWAII_THREAT_NM:  # info: if s [ "nm" ] >= vr .
        return (f"Pacific basin cyclone (not a Hawaiʻi threat): {s['label']} {s['name']}, {s['nm']} nm from {s['island']}. "  # info: return ( f" Pacific basin cyclone (not a Hawaiʻi threat): { s [ 'label'
                f"Do not alarm. Sample {s['polled_at']}.")  # info: f" Do not alarm. Sample { s [ 'polled_at' ] }
    return f"Nearest Hurricane from a Hawaiian island: {s['label']} {s['name']}, {s['nm']} nm from {s['island']}. Sample {s['polled_at']}."  # info: return f" Nearest Hurricane from a Hawaiian island: { s [ 'label' ]


# ====================================================
# SECTION: function _wx_period_lines
# What it does:  wx period lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _wx_period_lines(periods: list[dict], stamp: str, *, hour: int, max_n: int = 3) -> list[str]:  # info: def _wx_period_lines
    if not periods:  # info: if not periods :
        return [f"Weather ({stamp}): DOWN"]  # info: return [ f" Weather ( { stamp } ): DOWN
    picked = _pick_period(periods, hour)  # info: set picked
    start = next((i for i, p in enumerate(periods) if p is picked), 0)  # info: set start
    return [(f"Weather ({stamp}): " if i == 0 else "Next: ") + _period_line(p)  # info: return [ ( f" Weather ( { stamp }
            for i, p in enumerate(periods[start:start + max(1, max_n)])]  # info: for i , p in enumerate ( periods


# ====================================================
# SECTION: function weather_lines
# What it does: weather lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def weather_lines(offline: bool = False) -> list[str]:  # info: def weather_lines
    hour = datetime.now(HST).hour  # info: set hour
    periods, stamp = ([], "offline") if offline else forecast_periods()  # info: periods , stamp = ( [ ] ,
    alerts, _ = alerts_from_db()  # info: alerts , _ = alerts_from_db ( )
    return _wx_period_lines(periods, stamp, hour=hour) + [_alert_line(alerts), hurricane_line()]  # info: return _wx_period_lines ( periods , stamp , hour


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    lines = weather_lines(offline="--offline" in sys.argv)  # info: set lines
    print(json.dumps({"ok": True, "at": datetime.now(HST).isoformat(timespec="seconds"), "lines": lines}, ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
