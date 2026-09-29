#!/usr/bin/env python3
"""Daily sunrise / sunset in Hawaiʻi time (G3 port of G1 reports/sort/hourly-solar-weather/scripts/sun_times.py).

  python3 sun_times.py [refresh|facts] [--force]

Stdlib port: same Open-Meteo query (19.43, -155.23 — Volcano / Puna, "same patch as the weather desk"), same payload
keys (date, sunrise, sunset, *_iso, next_*), same refresh-if-stale rule (one fetch per HST day unless --force) and the
same facts() fields (after_sunset / before_sunrise). State file moved from G1 STATE_DIR/sun-times.json to Database
Energy/sun/sun-times-last.json (solar context for the Energy desk). A failed fetch keeps the stored file.
Light: one HTTP call, 10 s timeout. Schedule: hourly is plenty (jobs.py, gated RR_SUN_TIMES=1). Live numbers only.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
LAT, LON = 19.43, -155.23
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
PATH = DB / "Energy" / "sun" / "sun-times-last.json"
OPEN_METEO = ("https://api.open-meteo.com/v1/forecast"
              f"?latitude={LAT}&longitude={LON}&daily=sunrise,sunset&timezone=Pacific/Honolulu&forecast_days=2")
UA = "RootRecord-Pacific-Energy/1.0 (+https://rootrecord.cloud)"


def _today() -> str:
    return datetime.now(HST).strftime("%Y-%m-%d")


def read() -> dict:
    try:
        raw = json.loads(PATH.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, ValueError):
        return {}


def _hhmm_from_iso(iso: str) -> str:
    raw = str(iso or "").strip()
    if "T" in raw:
        raw = raw.split("T", 1)[1]
    return raw[:5]


def write(payload: dict) -> dict:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PATH.with_name(PATH.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, PATH)
    return payload


def refresh_if_stale(*, force: bool = False) -> dict:
    stored = read()
    if not force and stored.get("date") == _today() and stored.get("sunrise") and stored.get("sunset"):
        return dict(stored, refreshed=False)
    try:
        with urlopen(Request(OPEN_METEO, headers={"User-Agent": UA}), timeout=10) as r:
            daily = (json.loads(r.read().decode("utf-8")) or {}).get("daily") or {}
        rises, sets = daily.get("sunrise") or [], daily.get("sunset") or []
        if not rises or not sets:
            return dict(stored, refreshed=False, error="no daily sunrise/sunset")
        payload = {"date": _today(), "sunrise": _hhmm_from_iso(rises[0]), "sunset": _hhmm_from_iso(sets[0]),
                   "sunrise_iso": rises[0], "sunset_iso": sets[0], "source": "open-meteo", "lat": LAT, "lon": LON,
                   "fetched_at": datetime.now(HST).replace(microsecond=0).isoformat()}
        if len(rises) > 1:
            payload["next_date"] = (datetime.now(HST) + timedelta(days=1)).strftime("%Y-%m-%d")
            payload["next_sunrise"] = _hhmm_from_iso(rises[1])
            payload["next_sunrise_iso"] = rises[1]
        return dict(write(payload), refreshed=True)
    except Exception as e:  # noqa: BLE001
        return dict(stored, refreshed=False, error=f"{type(e).__name__}: {e}"[:200])


def parse_hhmm(value: str) -> tuple[int, int] | None:
    raw = str(value or "").strip()
    if ":" not in raw:
        return None
    hh, mm = raw.split(":", 1)
    try:
        h, m = int(hh), int(mm[:2])
    except ValueError:
        return None
    return (h, m) if 0 <= h <= 23 and 0 <= m <= 59 else None


def _at_today(hhmm: str) -> datetime | None:
    parsed = parse_hhmm(hhmm)
    if not parsed:
        return None
    return datetime.now(HST).replace(hour=parsed[0], minute=parsed[1], second=0, microsecond=0)


def facts(force: bool = False) -> dict:
    stored = refresh_if_stale(force=force)
    now = datetime.now(HST)
    rise, sett = _at_today(stored.get("sunrise") or ""), _at_today(stored.get("sunset") or "")
    return {"ok": bool(stored.get("sunrise") and stored.get("sunset")), "date": stored.get("date") or _today(),
            "sunrise": stored.get("sunrise") or "", "sunset": stored.get("sunset") or "",
            "sunrise_iso": stored.get("sunrise_iso"), "sunset_iso": stored.get("sunset_iso"),
            "after_sunset": bool(sett and now > sett), "before_sunrise": bool(rise and now < rise),
            "source": stored.get("source") or "", "now_hst": now.strftime("%H:%M"),
            "refreshed": stored.get("refreshed"), "error": stored.get("error")}


def in_day_start_window(now: datetime | None = None) -> bool:
    """First desk-awake after sunrise and before 14:00 HST (G1, unchanged)."""
    now = now or datetime.now(HST)
    if now.hour >= 14:
        return False
    rise = _at_today((read() or refresh_if_stale()).get("sunrise") or "06:00")
    if rise is None:
        return 6 <= now.hour < 14
    return now >= rise and now.hour < 14


if __name__ == "__main__":
    out = facts(force="--force" in sys.argv)
    print(json.dumps(out))
    raise SystemExit(0 if out["ok"] else 1)
