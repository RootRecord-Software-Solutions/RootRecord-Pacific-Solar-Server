#!/usr/bin/env python3
"""US all-states weather dataset. Stdlib only.

  python3 fetch_us_states.py [--force] [--dry-run] [--verbose] [--state WY]

Reads US rows from Geology/config/global-locations.json (shared; not copied).
Open-Meteo always. NOAA/NWS only when NWS_USER_AGENT is set in master-key.env.
Does not replace the Hawaiʻi weather poller.

Writes (Database, gitignored under Weather/):
  Weather/US-States/weather.db
  Weather/US-States/us-last.json
Logs:
  Logs/Weather/US-States/fetch-us-states.log

One HTTP attempt, 10 s timeout, 0.2 s between calls. No delivery.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from envload import nws_user_agent  # noqa: E402

PACIFIC = Path(__file__).resolve().parents[3]
LOCATIONS_FILE = PACIFIC / "Geology" / "config" / "global-locations.json"
DB_ROOT = Path(os.environ.get(
    "RR_DATABASE_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
))
DATA = DB_ROOT / "Weather" / "US-States"
LOG_DIR = DB_ROOT / "Logs" / "Weather" / "US-States"
DB_PATH = DATA / "weather.db"
LAST_PATH = DATA / "us-last.json"
LOG_PATH = LOG_DIR / "fetch-us-states.log"
LOCK_PATH = Path("/tmp/fetch_us_states.lock")

TIMEOUT = 10
REQUEST_DELAY = 0.2
MIN_SECONDS = 55 * 60
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
PLAIN_UA = "RootRecord-US-States/1.0 (+https://rootrecord.cloud)"

STATE_CODES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "hawaiʻi": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN",
    "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI",
    "wyoming": "WY", "district of columbia": "DC", "washington dc": "DC", "dc": "DC",
}


def state_code(*parts: Any) -> str:
    for p in parts:
        if p is None:
            continue
        s = str(p).strip()
        if len(s) == 2 and s.isalpha():
            return s.upper()
        key = re.sub(r"[^a-zʻ']+", " ", s.lower()).strip().replace("ʻ", "").replace("'", "")
        if key in STATE_CODES:
            return STATE_CODES[key]
        slug = key.replace(" ", "-")
        for name, code in STATE_CODES.items():
            if name.replace(" ", "-") == slug:
                return code
    return ""


def slugify(value: str) -> str:
    value = value.lower().replace("ʻ", "").replace("'", "")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "place"


def load_locations() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    if not LOCATIONS_FILE.is_file():
        return rows
    data = json.loads(LOCATIONS_FILE.read_text(encoding="utf-8"))
    for loc in data.get("locations") or []:
        cc = str(loc.get("country_code") or "").upper()
        cname = str(loc.get("country_name") or "").lower()
        if cc not in ("US", "USA") and "united states" not in cname:
            continue
        code = state_code(loc.get("admin1_code"), loc.get("admin1_name"), loc.get("admin1_slug"))
        name = str(loc.get("name") or "").strip()
        if not code or not name:
            continue
        try:
            lat = float(loc["lat"])
            lon = float(loc["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        key = (code, slugify(name))
        if key in seen:
            continue
        seen.add(key)
        region = str(loc.get("region") or loc.get("admin1_name") or code)
        rows.append({
            "external_id": loc.get("id") or f"us-{code.lower()}-{slugify(name)}",
            "name": name,
            "slug": loc.get("slug") or slugify(name),
            "lat": lat,
            "lon": lon,
            "country_code": "US",
            "admin1_code": code,
            "admin1_name": loc.get("admin1_name") or code,
            "region": region,
            "island": region if code == "HI" else "",
        })
    rows.sort(key=lambda r: (r["admin1_code"], r["name"]))
    return rows


def http_json(url: str, headers: dict[str, str] | None = None, params: dict | None = None) -> tuple[dict | None, str]:
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    req = Request(url, headers=headers or {"User-Agent": PLAIN_UA, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return None, f"http {exc.code}"
    except URLError:
        return None, "network error"
    except TimeoutError:
        return None, "timeout"
    except OSError:
        return None, "os error"
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None, "bad json"
    if not isinstance(parsed, dict):
        return None, "not an object"
    return parsed, ""


def fetch_open_meteo(lat: float, lon: float) -> tuple[dict | None, str]:
    return http_json(OPEN_METEO, params={
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_10m,wind_direction_10m",
        "daily": "sunrise,sunset",
        "timezone": "auto",
        "forecast_days": 1,
    })


def parse_open_meteo(obj: dict) -> dict[str, Any]:
    cur = obj.get("current") or {}
    daily = obj.get("daily") or {}
    sunrise = (daily.get("sunrise") or [None])[0]
    sunset = (daily.get("sunset") or [None])[0]
    sun_date = str(sunrise)[:10] if sunrise else None
    return {
        "obs_ts": cur.get("time"),
        "temp_c": cur.get("temperature_2m"),
        "wind_kph": cur.get("wind_speed_10m"),
        "wind_deg": cur.get("wind_direction_10m"),
        "precip": cur.get("precipitation"),
        "humidity": cur.get("relative_humidity_2m"),
        "cloud": cur.get("cloud_cover"),
        "sunrise": sunrise,
        "sunset": sunset,
        "sun_date": sun_date,
    }


def fetch_nws(lat: float, lon: float, ua: str) -> tuple[dict | None, str]:
    headers = {"User-Agent": ua, "Accept": "application/geo+json"}
    points, err = http_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}", headers=headers)
    time.sleep(REQUEST_DELAY)
    if not points:
        return None, err or "points failed"
    stations_url = (points.get("properties") or {}).get("observationStations")
    if not stations_url:
        return None, "no observationStations"
    stations, err = http_json(stations_url, headers=headers)
    time.sleep(REQUEST_DELAY)
    if not stations:
        return None, err or "stations failed"
    features = stations.get("features") or []
    if not features:
        return None, "no stations"
    props = features[0].get("properties") or {}
    station_id = props.get("stationIdentifier")
    if not station_id:
        station_id = str(features[0].get("id") or "").rstrip("/").split("/")[-1]
    if not station_id:
        return None, "no station id"
    obs, err = http_json(
        f"https://api.weather.gov/stations/{station_id}/observations/latest",
        headers=headers,
    )
    return obs, err


def _quantity(val: Any, kind: str) -> float | None:
    if not isinstance(val, dict) or val.get("value") is None:
        return None
    v = float(val["value"])
    unit = str(val.get("unitCode") or "")
    if kind == "temp":
        if "degF" in unit:
            return (v - 32) * 5 / 9
        return v
    if kind == "wind":
        if "m_s" in unit:
            return v * 3.6
        if "mi_h" in unit or "mph" in unit:
            return v * 1.60934
        return v
    return v


def parse_nws(obj: dict) -> dict[str, Any]:
    props = obj.get("properties") or {}
    return {
        "obs_ts": props.get("timestamp"),
        "temp_c": _quantity(props.get("temperature"), "temp"),
        "wind_kph": _quantity(props.get("windSpeed"), "wind"),
        "wind_deg": _quantity(props.get("windDirection"), "deg"),
        "humidity": _quantity(props.get("relativeHumidity"), "pct"),
    }


def ensure_db(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY,
            island TEXT,
            name TEXT,
            lat REAL,
            lon REAL,
            country_code TEXT DEFAULT 'US',
            admin1_code TEXT,
            region TEXT,
            external_id TEXT,
            UNIQUE(island, name)
        )
        """
    )
    for col, definition in (
        ("country_code", "TEXT"),
        ("admin1_code", "TEXT"),
        ("region", "TEXT"),
        ("external_id", "TEXT"),
    ):
        try:
            c.execute(f"ALTER TABLE locations ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY,
            location_id INTEGER,
            provider TEXT,
            obs_ts TEXT,
            forecast_from TEXT,
            forecast_to TEXT,
            ts_utc TEXT,
            raw TEXT,
            temp_c REAL,
            wind_kph REAL,
            wind_deg REAL,
            precipitation_mm REAL,
            humidity_pct REAL,
            cloud_pct REAL,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(location_id, provider, obs_ts)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_sun (
            id INTEGER PRIMARY KEY,
            location_id INTEGER,
            date TEXT,
            sunrise TEXT,
            sunset TEXT,
            UNIQUE(location_id, date)
        )
        """
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_weather_location ON weather(location_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_locations_admin1 ON locations(admin1_code)")
    conn.commit()


def save_location(conn: sqlite3.Connection, loc: dict[str, Any], dry_run: bool) -> int:
    island = loc.get("island") or loc.get("region") or loc["admin1_code"]
    if dry_run:
        return 0
    row = conn.execute("SELECT id FROM locations WHERE island=? AND name=?", (island, loc["name"])).fetchone()
    if row:
        conn.execute(
            """
            UPDATE locations
            SET lat=?, lon=?, country_code=?, admin1_code=?, region=?, external_id=COALESCE(?, external_id)
            WHERE id=?
            """,
            (loc["lat"], loc["lon"], loc["country_code"], loc["admin1_code"], loc.get("region") or island, loc.get("external_id"), row[0]),
        )
        conn.commit()
        return int(row[0])
    cur = conn.execute(
        """
        INSERT INTO locations (island, name, lat, lon, country_code, admin1_code, region, external_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (island, loc["name"], loc["lat"], loc["lon"], loc["country_code"], loc["admin1_code"], loc.get("region") or island, loc.get("external_id")),
    )
    conn.commit()
    return int(cur.lastrowid)


def upsert_weather(conn: sqlite3.Connection, location_id: int, provider: str, obs_ts: str | None, raw_obj: dict, fields: dict[str, Any], dry_run: bool) -> tuple[bool, bool]:
    key_obs = obs_ts or datetime.now(timezone.utc).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    raw = json.dumps(raw_obj)[:200000]
    row = None if dry_run or location_id == 0 else conn.execute(
        "SELECT id FROM weather WHERE location_id=? AND provider=? AND obs_ts=?",
        (location_id, provider, key_obs),
    ).fetchone()
    if dry_run:
        return True, False
    values = (
        fields.get("temp_c"), fields.get("wind_kph"), fields.get("wind_deg"),
        fields.get("precip"), fields.get("humidity"), fields.get("cloud"),
    )
    if row:
        conn.execute(
            """
            UPDATE weather SET ts_utc=?, raw=?, temp_c=?, wind_kph=?, wind_deg=?,
              precipitation_mm=?, humidity_pct=?, cloud_pct=?, updated_at=?
            WHERE id=?
            """,
            (now, raw, *values, now, row[0]),
        )
        conn.commit()
        return False, True
    conn.execute(
        """
        INSERT INTO weather (
          location_id, provider, obs_ts, forecast_from, forecast_to, ts_utc, raw,
          temp_c, wind_kph, wind_deg, precipitation_mm, humidity_pct, cloud_pct,
          created_at, updated_at
        ) VALUES (?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (location_id, provider, key_obs, now, raw, *values, now, now),
    )
    conn.commit()
    return True, False


def upsert_sun(conn: sqlite3.Connection, location_id: int, sunrise: str | None, sunset: str | None, sun_date: str | None, dry_run: bool) -> None:
    if dry_run or not sun_date or location_id == 0:
        return
    row = conn.execute("SELECT id FROM daily_sun WHERE location_id=? AND date=?", (location_id, sun_date)).fetchone()
    if row:
        conn.execute("UPDATE daily_sun SET sunrise=?, sunset=? WHERE id=?", (sunrise, sunset, row[0]))
    else:
        conn.execute(
            "INSERT INTO daily_sun (location_id, date, sunrise, sunset) VALUES (?, ?, ?, ?)",
            (location_id, sun_date, sunrise, sunset),
        )
    conn.commit()


def write_last(rows: list[dict[str, Any]], dry_run: bool) -> None:
    if dry_run:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "location_count": len({(r["admin1_code"], r["name"]) for r in rows}),
        "rows": rows,
    }
    tmp = LAST_PATH.with_name(LAST_PATH.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(LAST_PATH)


def log_line(text: str, dry_run: bool) -> None:
    print(text)
    if dry_run:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now(timezone.utc).isoformat()} {text}\n")


def acquire_lock() -> bool:
    try:
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return False
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return True


def release_lock() -> None:
    try:
        LOCK_PATH.unlink()
    except FileNotFoundError:
        pass


def run_once(force: bool, dry_run: bool, verbose: bool, only_state: str | None) -> int:
    locations = load_locations()
    if only_state:
        code = state_code(only_state) or only_state.upper()
        locations = [x for x in locations if x["admin1_code"] == code]
    if verbose:
        print(f"Locations to collect: {len(locations)}")
    if not locations:
        log_line("No US locations matched", dry_run)
        return 1

    nws_ua = nws_user_agent()
    if not dry_run:
        DATA.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=60)
    else:
        conn = None
    try:
        if conn is not None:
            ensure_db(conn)
            last = conn.execute("SELECT v FROM meta WHERE k=?", ("us_last_run",)).fetchone()
            last_ts = float(last[0]) if last and last[0] else 0.0
            now_ts = time.time()
            if not force and (now_ts - last_ts) < MIN_SECONDS:
                if verbose:
                    print(f"Skipping: last run {int(now_ts - last_ts)}s ago")
                return 0
        if not dry_run and not acquire_lock():
            if verbose:
                print("Another collector holds the lock")
            return 0
        total_new = total_updated = total_errors = 0
        last_rows: list[dict[str, Any]] = []
        try:
            for loc in locations:
                if verbose:
                    print(f"{loc['admin1_code']} · {loc['name']}")
                loc_id = save_location(conn, loc, dry_run) if conn is not None or dry_run else 0
                if conn is None and not dry_run:
                    loc_id = 0
                om, om_err = fetch_open_meteo(loc["lat"], loc["lon"])
                time.sleep(REQUEST_DELAY)
                if om:
                    parsed = parse_open_meteo(om)
                    if conn is not None:
                        ins, upd = upsert_weather(conn, loc_id, "open-meteo", parsed["obs_ts"], om, parsed, dry_run)
                        total_new += int(ins)
                        total_updated += int(upd)
                        upsert_sun(conn, loc_id, parsed["sunrise"], parsed["sunset"], parsed["sun_date"], dry_run)
                    else:
                        total_new += 1
                    last_rows.append({
                        "admin1_code": loc["admin1_code"],
                        "name": loc["name"],
                        "lat": loc["lat"],
                        "lon": loc["lon"],
                        "provider": "open-meteo",
                        "obs_ts": parsed["obs_ts"],
                        "temp_c": parsed["temp_c"],
                        "wind_kph": parsed["wind_kph"],
                        "humidity_pct": parsed["humidity"],
                        "precipitation_mm": parsed["precip"],
                    })
                else:
                    total_errors += 1
                    if verbose:
                        print(f"  open-meteo error: {om_err}")
                if nws_ua:
                    nws, nws_err = fetch_nws(loc["lat"], loc["lon"], nws_ua)
                    time.sleep(REQUEST_DELAY)
                    if nws and conn is not None:
                        parsed_n = parse_nws(nws)
                        ins, upd = upsert_weather(conn, loc_id, "nws", parsed_n["obs_ts"], nws, parsed_n, dry_run)
                        total_new += int(ins)
                        total_updated += int(upd)
                        last_rows.append({
                            "admin1_code": loc["admin1_code"],
                            "name": loc["name"],
                            "lat": loc["lat"],
                            "lon": loc["lon"],
                            "provider": "nws",
                            "obs_ts": parsed_n["obs_ts"],
                            "temp_c": parsed_n["temp_c"],
                            "wind_kph": parsed_n["wind_kph"],
                            "humidity_pct": parsed_n["humidity"],
                            "precipitation_mm": None,
                        })
                    elif not nws:
                        total_errors += 1
                        if verbose:
                            print(f"  nws error: {nws_err}")
                elif verbose:
                    print("  nws skipped: NWS_USER_AGENT unset")
            if conn is not None and not dry_run:
                now_iso = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                    ("us_last_run", str(time.time())),
                )
                conn.execute(
                    "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                    ("us_last_successful_run", now_iso),
                )
                conn.commit()
            write_last(last_rows, dry_run)
            log_line(
                f"US weather run: locations={len(locations)} new={total_new} updated={total_updated} errors={total_errors}",
                dry_run,
            )
        finally:
            if not dry_run:
                release_lock()
    finally:
        if conn is not None:
            conn.close()
    return 0


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Collect US state weather into Database Weather/US-States")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--state", help="Only one state code or name (e.g. WY or Wyoming)")
    args = p.parse_args()
    raise SystemExit(run_once(force=args.force, dry_run=args.dry_run, verbose=args.verbose, only_state=args.state))


if __name__ == "__main__":
    main()
