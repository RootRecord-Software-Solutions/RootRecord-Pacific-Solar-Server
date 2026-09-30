#!/usr/bin/env python3
"""Live NWS + hurricane lines for chat (G3 port of G1 weather/live-wx/scripts/live_wx.py, 2026-09-29). Do not invent.

  python3 live_wx.py            point forecast from api.weather.gov (one GET chain, 10 s timeout) + alerts/hurricane from Database
  python3 live_wx.py --offline  no HTTP: alerts + hurricane lines from Database only (forecast line says DOWN)

Ported unchanged: _pick_period (prefer tonight after 18:00 / before 05:00), _period_line, _alert_line (Big Island grouping),
_wx_period_lines (current + next two periods). Changed: G1 used httpx + the origin app's markdown / hurricane services;
G3 uses urllib, reads NWS HI alerts from the weather poller's Database file, and the nearest storm from
Media/Voice/scripts/voice_reports.py hurricane_facts (G3 track.json). On demand only; not wired to council chat (BLOCKED).
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parents[2]
sys.path.insert(0, str(PACIFIC / "Media" / "Voice" / "scripts"))
import voice_reports as vr  # noqa: E402  (ALERTS path, hurricane_facts; module import has no side effects)

HST = ZoneInfo("Pacific/Honolulu")
UA = {"User-Agent": "RootRecord-Pacific/3 (live-wx; contact via rootrecord)", "Accept": "application/geo+json"}
POINT = "https://api.weather.gov/points/19.5429,-155.0372"  # G1 point (Puna / Volcano side)
TIMEOUT = 10


def _pick_period(periods: list[dict], hour: int) -> dict | None:
    if not periods:
        return None
    if hour >= 18 or hour < 5:
        for p in periods:
            if "tonight" in str(p.get("name") or "").lower():
                return p
        if "afternoon" in str(periods[0].get("name") or "").lower() and len(periods) > 1:
            return periods[1]
    return periods[0]


def _period_line(p: dict) -> str:
    name = p.get("name") or "?"
    temp = p.get("temperature")
    unit = p.get("temperatureUnit") or "F"
    bits = [f"{name}", f"{temp}{unit}" if temp is not None else ""]
    if p.get("shortForecast"):
        bits.append(str(p["shortForecast"]))
    if p.get("windSpeed"):
        bits.append(f"wind {p['windSpeed']}")
    if p.get("windGust"):
        bits.append(f"gusts {p['windGust']}")
    return ", ".join(b for b in bits if b)


def _alert_line(alerts: list[dict]) -> str:
    if not alerts:
        return "HI alerts: none active"
    grouped: dict[str, bool] = {}
    order: list[str] = []
    for a in alerts[:8]:
        ev = str(a.get("event") or "alert")
        bi = bool(re.search(r"Big Island|Puna|Kona|Hilo|Kohala|Kaʻū|Kau", str(a.get("areas") or ""), re.I))
        if ev not in grouped:
            order.append(ev)
            grouped[ev] = bi
        else:
            grouped[ev] = grouped[ev] or bi
    return "HI alerts: " + "; ".join(f"{ev} (Big Island in area)" if grouped[ev] else ev for ev in order)


def _get(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:
        return json.loads(r.read(2_000_000))


def forecast_periods() -> tuple[list[dict], str]:
    try:
        fc = (_get(POINT).get("properties") or {}).get("forecast")
        periods = ((_get(fc).get("properties") or {}).get("periods") or []) if fc else []
        return periods, "live NWS " + datetime.now(HST).strftime("%H:%M HST")
    except Exception as e:  # noqa: BLE001
        return [], f"NWS fetch failed: {type(e).__name__}"


def alerts_from_db() -> tuple[list[dict], str]:
    try:
        d = json.loads(vr.ALERTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], "alerts file missing"
    out = [{"event": (f.get("properties") or {}).get("event") or "Unknown",
            "areas": (f.get("properties") or {}).get("areaDesc") or ""} for f in (d.get("features") or [])[:8]]
    return out, f"alerts file updated {d.get('updated') or '?'}"


def hurricane_line() -> str:
    storms = [s for s in vr.hurricane_facts(datetime.now(HST)) if s.get("active")]
    if not storms:
        return "Nearest Hurricane from a Hawaiian island: none on the board."
    s = storms[0]
    if s["nm"] >= vr.HAWAII_THREAT_NM:
        return (f"Pacific basin cyclone (not a Hawaiʻi threat): {s['label']} {s['name']}, {s['nm']} nm from {s['island']}. "
                f"Do not alarm. Sample {s['polled_at']}.")
    return f"Nearest Hurricane from a Hawaiian island: {s['label']} {s['name']}, {s['nm']} nm from {s['island']}. Sample {s['polled_at']}."


def _wx_period_lines(periods: list[dict], stamp: str, *, hour: int, max_n: int = 3) -> list[str]:
    if not periods:
        return [f"Weather ({stamp}): DOWN"]
    picked = _pick_period(periods, hour)
    start = next((i for i, p in enumerate(periods) if p is picked), 0)
    return [(f"Weather ({stamp}): " if i == 0 else "Next: ") + _period_line(p)
            for i, p in enumerate(periods[start:start + max(1, max_n)])]


def weather_lines(offline: bool = False) -> list[str]:
    hour = datetime.now(HST).hour
    periods, stamp = ([], "offline") if offline else forecast_periods()
    alerts, _ = alerts_from_db()
    return _wx_period_lines(periods, stamp, hour=hour) + [_alert_line(alerts), hurricane_line()]


def main() -> int:
    lines = weather_lines(offline="--offline" in sys.argv)
    print(json.dumps({"ok": True, "at": datetime.now(HST).isoformat(timespec="seconds"), "lines": lines}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
