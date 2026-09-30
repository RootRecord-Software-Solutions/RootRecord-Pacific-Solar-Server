# ==============================================================================
# FILE: Weather/US-States/scripts/fetch_us_states.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import sqlite3  # info: import sqlite3
import sys  # info: import sys
import time  # info: import time
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from urllib.error import HTTPError, URLError  # info: from urllib . error import HTTPError , URLError
from urllib.parse import urlencode  # info: from urllib . parse import urlencode
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
sys.path.insert(0, str(ROOT / "lib"))  # info: sys . path . insert ( 0 ,
from envload import nws_user_agent  # noqa: E402

PACIFIC = Path(__file__).resolve().parents[3]  # info: set PACIFIC
LOCATIONS_FILE = PACIFIC / "Geology" / "config" / "global-locations.json"  # info: set LOCATIONS_FILE
DB_ROOT = Path(os.environ.get(  # info: set DB_ROOT
    "RR_DATABASE_ROOT",  # info: "RR_DATABASE_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database" ,
))  # info: ) )
DATA = DB_ROOT / "Weather" / "US-States"  # info: set DATA
LOG_DIR = DB_ROOT / "Logs" / "Weather" / "US-States"  # info: set LOG_DIR
DB_PATH = DATA / "weather.db"  # info: set DB_PATH
LAST_PATH = DATA / "us-last.json"  # info: set LAST_PATH
LOG_PATH = LOG_DIR / "fetch-us-states.log"  # info: set LOG_PATH
LOCK_PATH = Path("/tmp/fetch_us_states.lock")  # info: set LOCK_PATH

TIMEOUT = 10  # info: set TIMEOUT
REQUEST_DELAY = 0.2  # info: set REQUEST_DELAY
MIN_SECONDS = 55 * 60  # info: set MIN_SECONDS
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"  # info: set OPEN_METEO
PLAIN_UA = "RootRecord-US-States/1.0 (+https://rootrecord.cloud)"  # info: set PLAIN_UA

# ====================================================
# SECTION: STATE_CODES
# What it does: Set STATE_CODES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
STATE_CODES = {  # info: set STATE_CODES
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",  # info: "alabama" : "AL" , "alaska" : "AK" ,
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",  # info: "colorado" : "CO" , "connecticut" : "CT" ,
    "hawaii": "HI", "hawaiʻi": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN",  # info: "hawaii" : "HI" , "hawaiʻi" : "HI" ,
    "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",  # info: "iowa" : "IA" , "kansas" : "KS" ,
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",  # info: "maryland" : "MD" , "massachusetts" : "MA" ,
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",  # info: "mississippi" : "MS" , "missouri" : "MO" ,
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",  # info: "new hampshire" : "NH" , "new jersey" : "NJ" ,
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",  # info: "north carolina" : "NC" , "north dakota" : "ND" ,
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",  # info: "oregon" : "OR" , "pennsylvania" : "PA" ,
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",  # info: "south dakota" : "SD" , "tennessee" : "TN" ,
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI",  # info: "virginia" : "VA" , "washington" : "WA" ,
    "wyoming": "WY", "district of columbia": "DC", "washington dc": "DC", "dc": "DC",  # info: "wyoming" : "WY" , "district of columbia" : "DC" ,
}  # info: }


# ====================================================
# SECTION: function state_code
# What it does: state code.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def state_code(*parts: Any) -> str:  # info: def state_code
    for p in parts:  # info: for p in parts :
        if p is None:  # info: if p is None :
            continue  # info: continue
        s = str(p).strip()  # info: set s
        if len(s) == 2 and s.isalpha():  # info: if len ( s ) == 2 and
            return s.upper()  # info: return s . upper ( )
        key = re.sub(r"[^a-zʻ']+", " ", s.lower()).strip().replace("ʻ", "").replace("'", "")  # info: set key
        if key in STATE_CODES:  # info: if key in STATE_CODES :
            return STATE_CODES[key]  # info: return STATE_CODES [ key ]
        slug = key.replace(" ", "-")  # info: set slug
        for name, code in STATE_CODES.items():  # info: for name , code in STATE_CODES . items
            if name.replace(" ", "-") == slug:  # info: if name . replace ( " " , "-"
                return code  # info: return code
    return ""  # info: return ""


# ====================================================
# SECTION: function slugify
# What it does: slugify.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def slugify(value: str) -> str:  # info: def slugify
    value = value.lower().replace("ʻ", "").replace("'", "")  # info: set value
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")  # info: set value
    return value or "place"  # info: return value or "place"


# ====================================================
# SECTION: function load_locations
# What it does: load locations.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_locations() -> list[dict[str, Any]]:  # info: def load_locations
    rows: list[dict[str, Any]] = []  # info: set rows
    seen: set[tuple[str, str]] = set()  # info: set seen
    if not LOCATIONS_FILE.is_file():  # info: if not LOCATIONS_FILE . is_file ( ) :
        return rows  # info: return rows
    data = json.loads(LOCATIONS_FILE.read_text(encoding="utf-8"))  # info: set data
    for loc in data.get("locations") or []:  # info: for loc in data . get ( "locations"
        cc = str(loc.get("country_code") or "").upper()  # info: set cc
        cname = str(loc.get("country_name") or "").lower()  # info: set cname
        if cc not in ("US", "USA") and "united states" not in cname:  # info: if cc not in ( "US" , "USA"
            continue  # info: continue
        code = state_code(loc.get("admin1_code"), loc.get("admin1_name"), loc.get("admin1_slug"))  # info: set code
        name = str(loc.get("name") or "").strip()  # info: set name
        if not code or not name:  # info: if not code or not name :
            continue  # info: continue
        try:  # info: try :
            lat = float(loc["lat"])  # info: set lat
            lon = float(loc["lon"])  # info: set lon
        except (KeyError, TypeError, ValueError):  # info: except ( KeyError , TypeError , ValueError )
            continue  # info: continue
        key = (code, slugify(name))  # info: set key
        if key in seen:  # info: if key in seen :
            continue  # info: continue
        seen.add(key)  # info: seen . add ( key )
        region = str(loc.get("region") or loc.get("admin1_name") or code)  # info: set region
        rows.append({  # info: rows . append ( {
            "external_id": loc.get("id") or f"us-{code.lower()}-{slugify(name)}",  # info: "external_id" : loc . get ( "id" )
            "name": name,  # info: "name" : name ,
            "slug": loc.get("slug") or slugify(name),  # info: "slug" : loc . get ( "slug" )
            "lat": lat,  # info: "lat" : lat ,
            "lon": lon,  # info: "lon" : lon ,
            "country_code": "US",  # info: "country_code" : "US" ,
            "admin1_code": code,  # info: "admin1_code" : code ,
            "admin1_name": loc.get("admin1_name") or code,  # info: "admin1_name" : loc . get ( "admin1_name" )
            "region": region,  # info: "region" : region ,
            "island": region if code == "HI" else "",  # info: "island" : region if code == "HI" else
        })  # info: } )
    rows.sort(key=lambda r: (r["admin1_code"], r["name"]))  # info: rows . sort ( key = lambda r
    return rows  # info: return rows


# ====================================================
# SECTION: function http_json
# What it does: http json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def http_json(url: str, headers: dict[str, str] | None = None, params: dict | None = None) -> tuple[dict | None, str]:  # info: def http_json
    if params:  # info: if params :
        url = url + ("&" if "?" in url else "?") + urlencode(params)  # info: set url
    req = Request(url, headers=headers or {"User-Agent": PLAIN_UA, "Accept": "application/json"})  # info: set req
    try:  # info: try :
        with urlopen(req, timeout=TIMEOUT) as resp:  # info: with urlopen ( req , timeout = TIMEOUT
            body = resp.read().decode("utf-8", errors="replace")  # info: set body
    except HTTPError as exc:  # info: except HTTPError as exc :
        return None, f"http {exc.code}"  # info: return None , f" http { exc .
    except URLError:  # info: except URLError :
        return None, "network error"  # info: return None , "network error"
    except TimeoutError:  # info: except TimeoutError :
        return None, "timeout"  # info: return None , "timeout"
    except OSError:  # info: except OSError :
        return None, "os error"  # info: return None , "os error"
    try:  # info: try :
        parsed = json.loads(body)  # info: set parsed
    except json.JSONDecodeError:  # info: except json . JSONDecodeError :
        return None, "bad json"  # info: return None , "bad json"
    if not isinstance(parsed, dict):  # info: if not isinstance ( parsed , dict )
        return None, "not an object"  # info: return None , "not an object"
    return parsed, ""  # info: return parsed , ""


# ====================================================
# SECTION: function fetch_open_meteo
# What it does: fetch open meteo.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_open_meteo(lat: float, lon: float) -> tuple[dict | None, str]:  # info: def fetch_open_meteo
    return http_json(OPEN_METEO, params={  # info: return http_json ( OPEN_METEO , params = {
        "latitude": lat,  # info: "latitude" : lat ,
        "longitude": lon,  # info: "longitude" : lon ,
        "current": "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_10m,wind_direction_10m",  # info: "current" : "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_10m,wind_direction_10m" 
        "daily": "sunrise,sunset",  # info: "daily" : "sunrise,sunset" ,
        "timezone": "auto",  # info: "timezone" : "auto" ,
        "forecast_days": 1,  # info: "forecast_days" : 1 ,
    })  # info: } )


# ====================================================
# SECTION: function parse_open_meteo
# What it does: parse open meteo.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_open_meteo(obj: dict) -> dict[str, Any]:  # info: def parse_open_meteo
    cur = obj.get("current") or {}  # info: set cur
    daily = obj.get("daily") or {}  # info: set daily
    sunrise = (daily.get("sunrise") or [None])[0]  # info: set sunrise
    sunset = (daily.get("sunset") or [None])[0]  # info: set sunset
    sun_date = str(sunrise)[:10] if sunrise else None  # info: set sun_date
    return {  # info: return {
        "obs_ts": cur.get("time"),  # info: "obs_ts" : cur . get ( "time" )
        "temp_c": cur.get("temperature_2m"),  # info: "temp_c" : cur . get ( "temperature_2m" )
        "wind_kph": cur.get("wind_speed_10m"),  # info: "wind_kph" : cur . get ( "wind_speed_10m" )
        "wind_deg": cur.get("wind_direction_10m"),  # info: "wind_deg" : cur . get ( "wind_direction_10m" )
        "precip": cur.get("precipitation"),  # info: "precip" : cur . get ( "precipitation" )
        "humidity": cur.get("relative_humidity_2m"),  # info: "humidity" : cur . get ( "relative_humidity_2m" )
        "cloud": cur.get("cloud_cover"),  # info: "cloud" : cur . get ( "cloud_cover" )
        "sunrise": sunrise,  # info: "sunrise" : sunrise ,
        "sunset": sunset,  # info: "sunset" : sunset ,
        "sun_date": sun_date,  # info: "sun_date" : sun_date ,
    }  # info: }


# ====================================================
# SECTION: function fetch_nws
# What it does: fetch nws.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_nws(lat: float, lon: float, ua: str) -> tuple[dict | None, str]:  # info: def fetch_nws
    headers = {"User-Agent": ua, "Accept": "application/geo+json"}  # info: set headers
    points, err = http_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}", headers=headers)  # info: points , err = http_json ( f" https://api.weather.gov/points/
    time.sleep(REQUEST_DELAY)  # info: time . sleep ( REQUEST_DELAY )
    if not points:  # info: if not points :
        return None, err or "points failed"  # info: return None , err or "points failed"
    stations_url = (points.get("properties") or {}).get("observationStations")  # info: set stations_url
    if not stations_url:  # info: if not stations_url :
        return None, "no observationStations"  # info: return None , "no observationStations"
    stations, err = http_json(stations_url, headers=headers)  # info: stations , err = http_json ( stations_url ,
    time.sleep(REQUEST_DELAY)  # info: time . sleep ( REQUEST_DELAY )
    if not stations:  # info: if not stations :
        return None, err or "stations failed"  # info: return None , err or "stations failed"
    features = stations.get("features") or []  # info: set features
    if not features:  # info: if not features :
        return None, "no stations"  # info: return None , "no stations"
    props = features[0].get("properties") or {}  # info: set props
    station_id = props.get("stationIdentifier")  # info: set station_id
    if not station_id:  # info: if not station_id :
        station_id = str(features[0].get("id") or "").rstrip("/").split("/")[-1]  # info: set station_id
    if not station_id:  # info: if not station_id :
        return None, "no station id"  # info: return None , "no station id"
    obs, err = http_json(  # info: obs , err = http_json (
        f"https://api.weather.gov/stations/{station_id}/observations/latest",  # info: f" https://api.weather.gov/stations/ { station_id } /observations/latest " ,
        headers=headers,  # info: set headers
    )  # info: )
    return obs, err  # info: return obs , err


# ====================================================
# SECTION: function _quantity
# What it does:  quantity.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _quantity(val: Any, kind: str) -> float | None:  # info: def _quantity
    if not isinstance(val, dict) or val.get("value") is None:  # info: if not isinstance ( val , dict )
        return None  # info: return None
    v = float(val["value"])  # info: set v
    unit = str(val.get("unitCode") or "")  # info: set unit
    if kind == "temp":  # info: if kind == "temp" :
        if "degF" in unit:  # info: if "degF" in unit :
            return (v - 32) * 5 / 9  # info: return ( v - 32 ) * 5
        return v  # info: return v
    if kind == "wind":  # info: if kind == "wind" :
        if "m_s" in unit:  # info: if "m_s" in unit :
            return v * 3.6  # info: return v * 3.6
        if "mi_h" in unit or "mph" in unit:  # info: if "mi_h" in unit or "mph" in unit
            return v * 1.60934  # info: return v * 1.60934
        return v  # info: return v
    return v  # info: return v


# ====================================================
# SECTION: function parse_nws
# What it does: parse nws.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_nws(obj: dict) -> dict[str, Any]:  # info: def parse_nws
    props = obj.get("properties") or {}  # info: set props
    return {  # info: return {
        "obs_ts": props.get("timestamp"),  # info: "obs_ts" : props . get ( "timestamp" )
        "temp_c": _quantity(props.get("temperature"), "temp"),  # info: "temp_c" : _quantity ( props . get (
        "wind_kph": _quantity(props.get("windSpeed"), "wind"),  # info: "wind_kph" : _quantity ( props . get (
        "wind_deg": _quantity(props.get("windDirection"), "deg"),  # info: "wind_deg" : _quantity ( props . get (
        "humidity": _quantity(props.get("relativeHumidity"), "pct"),  # info: "humidity" : _quantity ( props . get (
    }  # info: }


# ====================================================
# SECTION: function ensure_db
# What it does: ensure db.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_db(conn: sqlite3.Connection) -> None:  # info: def ensure_db
    c = conn.cursor()  # info: set c
    c.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")  # info: c . execute ( "CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)" )
    c.execute(  # info: c . execute (
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
    )  # info: )
    for col, definition in (  # info: for col , definition in (
        ("country_code", "TEXT"),  # info: call (
        ("admin1_code", "TEXT"),  # info: call (
        ("region", "TEXT"),  # info: call (
        ("external_id", "TEXT"),  # info: call (
    ):  # info: ) :
        try:  # info: try :
            c.execute(f"ALTER TABLE locations ADD COLUMN {col} {definition}")  # info: c . execute ( f" ALTER TABLE locations ADD COLUMN { col
        except sqlite3.OperationalError:  # info: except sqlite3 . OperationalError :
            pass  # info: pass
    c.execute(  # info: c . execute (
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
    )  # info: )
    c.execute(  # info: c . execute (
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
    )  # info: )
    c.execute("CREATE INDEX IF NOT EXISTS idx_weather_location ON weather(location_id)")  # info: c . execute ( "CREATE INDEX IF NOT EXISTS idx_weather_location ON weather(location_id)" )
    c.execute("CREATE INDEX IF NOT EXISTS idx_locations_admin1 ON locations(admin1_code)")  # info: c . execute ( "CREATE INDEX IF NOT EXISTS idx_locations_admin1 ON locations(admin1_code)" )
    conn.commit()  # info: conn . commit ( )


# ====================================================
# SECTION: function save_location
# What it does: save location.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_location(conn: sqlite3.Connection, loc: dict[str, Any], dry_run: bool) -> int:  # info: def save_location
    island = loc.get("island") or loc.get("region") or loc["admin1_code"]  # info: set island
    if dry_run:  # info: if dry_run :
        return 0  # info: return 0
    row = conn.execute("SELECT id FROM locations WHERE island=? AND name=?", (island, loc["name"])).fetchone()  # info: set row
    if row:  # info: if row :
        conn.execute(  # info: conn . execute (
            """
            UPDATE locations
            SET lat=?, lon=?, country_code=?, admin1_code=?, region=?, external_id=COALESCE(?, external_id)
            WHERE id=?
            """,
            (loc["lat"], loc["lon"], loc["country_code"], loc["admin1_code"], loc.get("region") or island, loc.get("external_id"), row[0]),  # info: call (
        )  # info: )
        conn.commit()  # info: conn . commit ( )
        return int(row[0])  # info: return int ( row [ 0 ] )
    cur = conn.execute(  # info: set cur
        """
        INSERT INTO locations (island, name, lat, lon, country_code, admin1_code, region, external_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (island, loc["name"], loc["lat"], loc["lon"], loc["country_code"], loc["admin1_code"], loc.get("region") or island, loc.get("external_id")),  # info: call (
    )  # info: )
    conn.commit()  # info: conn . commit ( )
    return int(cur.lastrowid)  # info: return int ( cur . lastrowid )


# ====================================================
# SECTION: function upsert_weather
# What it does: upsert weather.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def upsert_weather(conn: sqlite3.Connection, location_id: int, provider: str, obs_ts: str | None, raw_obj: dict, fields: dict[str, Any], dry_run: bool) -> tuple[bool, bool]:  # info: def upsert_weather
    key_obs = obs_ts or datetime.now(timezone.utc).isoformat()  # info: set key_obs
    now = datetime.now(timezone.utc).isoformat()  # info: set now
    raw = json.dumps(raw_obj)[:200000]  # info: set raw
    row = None if dry_run or location_id == 0 else conn.execute(  # info: set row
        "SELECT id FROM weather WHERE location_id=? AND provider=? AND obs_ts=?",  # info: "SELECT id FROM weather WHERE location_id=? AND provider=? AND obs_ts=?" ,
        (location_id, provider, key_obs),  # info: call (
    ).fetchone()  # info: ) . fetchone ( )
    if dry_run:  # info: if dry_run :
        return True, False  # info: return True , False
    values = (  # info: set values
        fields.get("temp_c"), fields.get("wind_kph"), fields.get("wind_deg"),  # info: fields . get ( "temp_c" ) , fields
        fields.get("precip"), fields.get("humidity"), fields.get("cloud"),  # info: fields . get ( "precip" ) , fields
    )  # info: )
    if row:  # info: if row :
        conn.execute(  # info: conn . execute (
            """
            UPDATE weather SET ts_utc=?, raw=?, temp_c=?, wind_kph=?, wind_deg=?,
              precipitation_mm=?, humidity_pct=?, cloud_pct=?, updated_at=?
            WHERE id=?
            """,
            (now, raw, *values, now, row[0]),  # info: call (
        )  # info: )
        conn.commit()  # info: conn . commit ( )
        return False, True  # info: return False , True
    conn.execute(  # info: conn . execute (
        """
        INSERT INTO weather (
          location_id, provider, obs_ts, forecast_from, forecast_to, ts_utc, raw,
          temp_c, wind_kph, wind_deg, precipitation_mm, humidity_pct, cloud_pct,
          created_at, updated_at
        ) VALUES (?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (location_id, provider, key_obs, now, raw, *values, now, now),  # info: call (
    )  # info: )
    conn.commit()  # info: conn . commit ( )
    return True, False  # info: return True , False


# ====================================================
# SECTION: function upsert_sun
# What it does: upsert sun.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def upsert_sun(conn: sqlite3.Connection, location_id: int, sunrise: str | None, sunset: str | None, sun_date: str | None, dry_run: bool) -> None:  # info: def upsert_sun
    if dry_run or not sun_date or location_id == 0:  # info: if dry_run or not sun_date or location_id ==
        return  # info: return
    row = conn.execute("SELECT id FROM daily_sun WHERE location_id=? AND date=?", (location_id, sun_date)).fetchone()  # info: set row
    if row:  # info: if row :
        conn.execute("UPDATE daily_sun SET sunrise=?, sunset=? WHERE id=?", (sunrise, sunset, row[0]))  # info: conn . execute ( "UPDATE daily_sun SET sunrise=?, sunset=? WHERE id=?" , ( sunrise
    else:  # info: else :
        conn.execute(  # info: conn . execute (
            "INSERT INTO daily_sun (location_id, date, sunrise, sunset) VALUES (?, ?, ?, ?)",  # info: "INSERT INTO daily_sun (location_id, date, sunrise, sunset) VALUES (?, ?, ?, ?)" ,
            (location_id, sun_date, sunrise, sunset),  # info: call (
        )  # info: )
    conn.commit()  # info: conn . commit ( )


# ====================================================
# SECTION: function write_last
# What it does: write last.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_last(rows: list[dict[str, Any]], dry_run: bool) -> None:  # info: def write_last
    if dry_run:  # info: if dry_run :
        return  # info: return
    DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
    payload = {  # info: set payload
        "updated_at": datetime.now(timezone.utc).isoformat(),  # info: "updated_at" : datetime . now ( timezone .
        "location_count": len({(r["admin1_code"], r["name"]) for r in rows}),  # info: "location_count" : len ( { ( r [
        "rows": rows,  # info: "rows" : rows ,
    }  # info: }
    tmp = LAST_PATH.with_name(LAST_PATH.name + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(LAST_PATH)  # info: tmp . replace ( LAST_PATH )


# ====================================================
# SECTION: function log_line
# What it does: log line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_line(text: str, dry_run: bool) -> None:  # info: def log_line
    print(text)  # info: call print
    if dry_run:  # info: if dry_run :
        return  # info: return
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    with LOG_PATH.open("a", encoding="utf-8") as fh:  # info: with LOG_PATH . open ( "a" , encoding
        fh.write(f"{datetime.now(timezone.utc).isoformat()} {text}\n")  # info: fh . write ( f" { datetime .


# ====================================================
# SECTION: function acquire_lock
# What it does: acquire lock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def acquire_lock() -> bool:  # info: def acquire_lock
    try:  # info: try :
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)  # info: set fd
    except FileExistsError:  # info: except FileExistsError :
        return False  # info: return False
    os.write(fd, str(os.getpid()).encode())  # info: os . write ( fd , str (
    os.close(fd)  # info: os . close ( fd )
    return True  # info: return True


# ====================================================
# SECTION: function release_lock
# What it does: release lock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def release_lock() -> None:  # info: def release_lock
    try:  # info: try :
        LOCK_PATH.unlink()  # info: LOCK_PATH . unlink ( )
    except FileNotFoundError:  # info: except FileNotFoundError :
        pass  # info: pass


# ====================================================
# SECTION: function run_once
# What it does: run once.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_once(force: bool, dry_run: bool, verbose: bool, only_state: str | None) -> int:  # info: def run_once
    locations = load_locations()  # info: set locations
    if only_state:  # info: if only_state :
        code = state_code(only_state) or only_state.upper()  # info: set code
        locations = [x for x in locations if x["admin1_code"] == code]  # info: set locations
    if verbose:  # info: if verbose :
        print(f"Locations to collect: {len(locations)}")  # info: call print
    if not locations:  # info: if not locations :
        log_line("No US locations matched", dry_run)  # info: call log_line
        return 1  # info: return 1

    nws_ua = nws_user_agent()  # info: set nws_ua
    if not dry_run:  # info: if not dry_run :
        DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
        conn = sqlite3.connect(str(DB_PATH), timeout=60)  # info: set conn
    else:  # info: else :
        conn = None  # info: set conn
    try:  # info: try :
        if conn is not None:  # info: if conn is not None :
            ensure_db(conn)  # info: call ensure_db
            last = conn.execute("SELECT v FROM meta WHERE k=?", ("us_last_run",)).fetchone()  # info: set last
            last_ts = float(last[0]) if last and last[0] else 0.0  # info: set last_ts
            now_ts = time.time()  # info: set now_ts
            if not force and (now_ts - last_ts) < MIN_SECONDS:  # info: if not force and ( now_ts - last_ts
                if verbose:  # info: if verbose :
                    print(f"Skipping: last run {int(now_ts - last_ts)}s ago")  # info: call print
                return 0  # info: return 0
        if not dry_run and not acquire_lock():  # info: if not dry_run and not acquire_lock ( )
            if verbose:  # info: if verbose :
                print("Another collector holds the lock")  # info: call print
            return 0  # info: return 0
        total_new = total_updated = total_errors = 0  # info: set total_new
        last_rows: list[dict[str, Any]] = []  # info: set last_rows
        try:  # info: try :
            for loc in locations:  # info: for loc in locations :
                if verbose:  # info: if verbose :
                    print(f"{loc['admin1_code']} · {loc['name']}")  # info: call print
                loc_id = save_location(conn, loc, dry_run) if conn is not None or dry_run else 0  # info: set loc_id
                if conn is None and not dry_run:  # info: if conn is None and not dry_run :
                    loc_id = 0  # info: set loc_id
                om, om_err = fetch_open_meteo(loc["lat"], loc["lon"])  # info: om , om_err = fetch_open_meteo ( loc [
                time.sleep(REQUEST_DELAY)  # info: time . sleep ( REQUEST_DELAY )
                if om:  # info: if om :
                    parsed = parse_open_meteo(om)  # info: set parsed
                    if conn is not None:  # info: if conn is not None :
                        ins, upd = upsert_weather(conn, loc_id, "open-meteo", parsed["obs_ts"], om, parsed, dry_run)  # info: ins , upd = upsert_weather ( conn ,
                        total_new += int(ins)  # info: set total_new
                        total_updated += int(upd)  # info: set total_updated
                        upsert_sun(conn, loc_id, parsed["sunrise"], parsed["sunset"], parsed["sun_date"], dry_run)  # info: call upsert_sun
                    else:  # info: else :
                        total_new += 1  # info: set total_new
                    last_rows.append({  # info: last_rows . append ( {
                        "admin1_code": loc["admin1_code"],  # info: "admin1_code" : loc [ "admin1_code" ] ,
                        "name": loc["name"],  # info: "name" : loc [ "name" ] ,
                        "lat": loc["lat"],  # info: "lat" : loc [ "lat" ] ,
                        "lon": loc["lon"],  # info: "lon" : loc [ "lon" ] ,
                        "provider": "open-meteo",  # info: "provider" : "open-meteo" ,
                        "obs_ts": parsed["obs_ts"],  # info: "obs_ts" : parsed [ "obs_ts" ] ,
                        "temp_c": parsed["temp_c"],  # info: "temp_c" : parsed [ "temp_c" ] ,
                        "wind_kph": parsed["wind_kph"],  # info: "wind_kph" : parsed [ "wind_kph" ] ,
                        "humidity_pct": parsed["humidity"],  # info: "humidity_pct" : parsed [ "humidity" ] ,
                        "precipitation_mm": parsed["precip"],  # info: "precipitation_mm" : parsed [ "precip" ] ,
                    })  # info: } )
                else:  # info: else :
                    total_errors += 1  # info: set total_errors
                    if verbose:  # info: if verbose :
                        print(f"  open-meteo error: {om_err}")  # info: call print
                if nws_ua:  # info: if nws_ua :
                    nws, nws_err = fetch_nws(loc["lat"], loc["lon"], nws_ua)  # info: nws , nws_err = fetch_nws ( loc [
                    time.sleep(REQUEST_DELAY)  # info: time . sleep ( REQUEST_DELAY )
                    if nws and conn is not None:  # info: if nws and conn is not None :
                        parsed_n = parse_nws(nws)  # info: set parsed_n
                        ins, upd = upsert_weather(conn, loc_id, "nws", parsed_n["obs_ts"], nws, parsed_n, dry_run)  # info: ins , upd = upsert_weather ( conn ,
                        total_new += int(ins)  # info: set total_new
                        total_updated += int(upd)  # info: set total_updated
                        last_rows.append({  # info: last_rows . append ( {
                            "admin1_code": loc["admin1_code"],  # info: "admin1_code" : loc [ "admin1_code" ] ,
                            "name": loc["name"],  # info: "name" : loc [ "name" ] ,
                            "lat": loc["lat"],  # info: "lat" : loc [ "lat" ] ,
                            "lon": loc["lon"],  # info: "lon" : loc [ "lon" ] ,
                            "provider": "nws",  # info: "provider" : "nws" ,
                            "obs_ts": parsed_n["obs_ts"],  # info: "obs_ts" : parsed_n [ "obs_ts" ] ,
                            "temp_c": parsed_n["temp_c"],  # info: "temp_c" : parsed_n [ "temp_c" ] ,
                            "wind_kph": parsed_n["wind_kph"],  # info: "wind_kph" : parsed_n [ "wind_kph" ] ,
                            "humidity_pct": parsed_n["humidity"],  # info: "humidity_pct" : parsed_n [ "humidity" ] ,
                            "precipitation_mm": None,  # info: "precipitation_mm" : None ,
                        })  # info: } )
                    elif not nws:  # info: elif not nws :
                        total_errors += 1  # info: set total_errors
                        if verbose:  # info: if verbose :
                            print(f"  nws error: {nws_err}")  # info: call print
                elif verbose:  # info: elif verbose :
                    print("  nws skipped: NWS_USER_AGENT unset")  # info: call print
            if conn is not None and not dry_run:  # info: if conn is not None and not dry_run
                now_iso = datetime.now(timezone.utc).isoformat()  # info: set now_iso
                conn.execute(  # info: conn . execute (
                    "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",  # info: "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v" ,
                    ("us_last_run", str(time.time())),  # info: call (
                )  # info: )
                conn.execute(  # info: conn . execute (
                    "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",  # info: "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v" ,
                    ("us_last_successful_run", now_iso),  # info: call (
                )  # info: )
                conn.commit()  # info: conn . commit ( )
            write_last(last_rows, dry_run)  # info: call write_last
            log_line(  # info: call log_line
                f"US weather run: locations={len(locations)} new={total_new} updated={total_updated} errors={total_errors}",  # info: f" US weather run: locations= { len ( locations ) }
                dry_run,  # info: dry_run ,
            )  # info: )
        finally:  # info: finally :
            if not dry_run:  # info: if not dry_run :
                release_lock()  # info: call release_lock
    finally:  # info: finally :
        if conn is not None:  # info: if conn is not None :
            conn.close()  # info: conn . close ( )
    return 0  # info: return 0


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    import argparse  # info: import argparse
    p = argparse.ArgumentParser(description="Collect US state weather into Database Weather/US-States")  # info: set p
    p.add_argument("--force", action="store_true")  # info: p . add_argument ( "--force" , action =
    p.add_argument("--dry-run", action="store_true")  # info: p . add_argument ( "--dry-run" , action =
    p.add_argument("--verbose", action="store_true")  # info: p . add_argument ( "--verbose" , action =
    p.add_argument("--state", help="Only one state code or name (e.g. WY or Wyoming)")  # info: p . add_argument ( "--state" , help =
    args = p.parse_args()  # info: set args
    raise SystemExit(run_once(force=args.force, dry_run=args.dry_run, verbose=args.verbose, only_state=args.state))  # info: raise SystemExit ( run_once ( force = args


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
