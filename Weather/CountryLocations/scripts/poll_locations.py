#!/usr/bin/env python3
"""Current Open-Meteo conditions for the CountryLocations allowlist.

Empty allowlist: exit 0, write status, do not call Open-Meteo.
No archive backfill. Does not touch the Hawaiʻi weather poller.

  python3 poll_locations.py
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent.parent
ALLOWLIST = HERE / "config" / "allowlist.json"
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
OUT = DB / "Weather" / "CountryLocations"
LOG_DIR = DB / "Logs" / "Weather" / "CountryLocations"
LOG_PATH = LOG_DIR / "poll_locations.log"
STATUS_PATH = OUT / "status-last.json"
UA = "RootRecord-Pacific/3 country-locations"
TIMEOUT = 20
FORECAST = "https://api.open-meteo.com/v1/forecast"


def load_allowlist(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("allowlist must be a JSON list")
    return data


def valid_entry(entry: object) -> dict | None:
    if not isinstance(entry, dict):
        return None
    loc_id = entry.get("id")
    lat = entry.get("lat")
    lon = entry.get("lon")
    if not isinstance(loc_id, str) or not loc_id:
        return None
    if isinstance(lat, bool) or isinstance(lon, bool):
        return None
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    return {"id": loc_id, "lat": float(lat), "lon": float(lon), "name": entry.get("name") or loc_id}


def fetch_current(entry: dict) -> dict:
    query = urllib.parse.urlencode(
        {
            "latitude": entry["lat"],
            "longitude": entry["lon"],
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
            "timezone": "UTC",
        }
    )
    req = urllib.request.Request(FORECAST + "?" + query, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        payload = json.load(response)
    current = payload.get("current") or {}
    return {
        "id": entry["id"],
        "name": entry["name"],
        "lat": entry["lat"],
        "lon": entry["lon"],
        "obs_ts": current.get("time"),
        "temp_c": current.get("temperature_2m"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "wind_kph": current.get("wind_speed_10m"),
        "precipitation_mm": current.get("precipitation"),
        "provider": "open-meteo",
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_allowlist(ALLOWLIST)
    entries = [item for item in (valid_entry(row) for row in raw) if item]
    skipped = len(raw) - len(entries)
    fetched: list[str] = []
    http_calls = 0
    if entries:
        for entry in entries:
            obs = fetch_current(entry)
            http_calls += 1
            write_json(OUT / f"{entry['id']}-last.json", obs)
            fetched.append(entry["id"])
    payload = {
        "ok": True,
        "locations": len(entries),
        "skipped": skipped,
        "http_calls": http_calls,
        "fetched": fetched,
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),
    }
    write_json(STATUS_PATH, payload)
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(
            f"{payload['updated_at']} locations={payload['locations']} http_calls={payload['http_calls']}\n"
        )
    return payload


def main() -> int:
    payload = run()
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
