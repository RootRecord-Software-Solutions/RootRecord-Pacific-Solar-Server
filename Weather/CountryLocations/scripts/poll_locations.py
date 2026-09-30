#!/usr/bin/env python3
"""Current Open-Meteo conditions for country places the /locations page serves.

An empty allowlist means every non-US place in Geology/config/global-locations.json.
US places stay on Weather/US-States. A non-empty allowlist restricts to those ids.
No archive backfill. Does not touch the Hawaiʻi weather poller.

  python3 poll_locations.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent.parent
PACIFIC = HERE.parents[1]
ALLOWLIST = HERE / "config" / "allowlist.json"
CATALOG = PACIFIC / "Geology" / "config" / "global-locations.json"
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
OUT = DB / "Weather" / "CountryLocations"
LOG_DIR = DB / "Logs" / "Weather" / "CountryLocations"
LOG_PATH = LOG_DIR / "poll_locations.log"
STATUS_PATH = OUT / "status-last.json"
LAST_PATH = OUT / "locations-last.json"
UA = "RootRecord-Pacific/3 country-locations"
TIMEOUT = 10
PAUSE = 0.2
MIN_AGE = timedelta(minutes=55)
FORECAST = "https://api.open-meteo.com/v1/forecast"


def load_allowlist(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("allowlist must be a JSON list")
    return data


def catalog_rows() -> list[dict]:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    rows = data.get("locations") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError("global-locations.json has no locations list")
    places = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("country_code") or "") == "US":
            continue
        item = valid_entry(row)
        if item:
            item["country_code"] = row.get("country_code") or ""
            item["country_name"] = row.get("country_name") or item["country_code"]
            places.append(item)
    return places


def select_places(raw: list) -> list[dict]:
    catalog = catalog_rows()
    if not raw:
        return catalog
    wanted = []
    for row in raw:
        if isinstance(row, str):
            wanted.append(row)
        elif isinstance(row, dict) and isinstance(row.get("id"), str):
            wanted.append(row["id"])
    by_id = {place["id"]: place for place in catalog}
    chosen = []
    for loc_id in wanted:
        if loc_id in by_id:
            chosen.append(by_id[loc_id])
            continue
        direct = valid_entry(next((row for row in raw if isinstance(row, dict) and row.get("id") == loc_id), None))
        if direct:
            chosen.append(direct)
    return chosen


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
    base = {
        "id": entry["id"],
        "name": entry["name"],
        "country_code": entry.get("country_code") or "",
        "country_name": entry.get("country_name") or "",
        "lat": entry["lat"],
        "lon": entry["lon"],
        "provider": "open-meteo",
    }
    req = urllib.request.Request(FORECAST + "?" + query, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return {**base, "obs_ts": None, "temp_c": None, "error": "fetch_failed"}
    current = payload.get("current") or {}
    return {
        **base,
        "obs_ts": current.get("time"),
        "temp_c": current.get("temperature_2m"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "wind_kph": current.get("wind_speed_10m"),
        "precipitation_mm": current.get("precipitation"),
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def snapshot_is_fresh() -> bool:
    if "--force" in sys.argv or not LAST_PATH.is_file():
        return False
    try:
        payload = json.loads(LAST_PATH.read_text(encoding="utf-8"))
        stamp = datetime.fromisoformat(payload["updated_at"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return False
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=HST)
    return datetime.now(HST) - stamp < MIN_AGE


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if snapshot_is_fresh():
        return {
            "ok": True,
            "http_calls": 0,
            "note": "snapshot_fresh",
            "updated_at": datetime.now(HST).isoformat(timespec="seconds"),
        }
    raw = load_allowlist(ALLOWLIST)
    entries = select_places(raw)
    rows = []
    http_calls = 0
    for index, entry in enumerate(entries):
        if index:
            time.sleep(PAUSE)
        obs = fetch_current(entry)
        http_calls += 1
        write_json(OUT / f"{entry['id']}-last.json", obs)
        rows.append(obs)
    updated_at = datetime.now(HST).isoformat(timespec="seconds")
    write_json(
        LAST_PATH,
        {"ok": True, "updated_at": updated_at, "rows": rows},
    )
    payload = {
        "ok": True,
        "locations": len(entries),
        "skipped": max(0, len(raw) - len(entries)) if raw else 0,
        "http_calls": http_calls,
        "fetched": [row["id"] for row in rows if row.get("temp_c") is not None],
        "updated_at": updated_at,
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
