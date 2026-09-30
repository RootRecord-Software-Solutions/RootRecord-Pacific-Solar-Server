# ==============================================================================
# FILE: Weather/CountryLocations/scripts/poll_locations.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Current Open-Meteo conditions for country places the /locations page serves.

An empty allowlist means every non-US place in Geology/config/global-locations.json.
US places stay on Weather/US-States. A non-empty allowlist restricts to those ids.
No archive backfill. Does not touch the Hawaiʻi weather poller.

  python3 poll_locations.py
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import time  # info: import time
import urllib.parse  # info: import urllib . parse
import urllib.request  # info: import urllib . request
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from urllib.error import HTTPError, URLError  # info: from urllib . error import HTTPError , URLError
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent.parent  # info: set HERE
PACIFIC = HERE.parents[1]  # info: set PACIFIC
ALLOWLIST = HERE / "config" / "allowlist.json"  # info: set ALLOWLIST
CATALOG = PACIFIC / "Geology" / "config" / "global-locations.json"  # info: set CATALOG
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
OUT = DB / "Weather" / "CountryLocations"  # info: set OUT
LOG_DIR = DB / "Logs" / "Weather" / "CountryLocations"  # info: set LOG_DIR
LOG_PATH = LOG_DIR / "poll_locations.log"  # info: set LOG_PATH
STATUS_PATH = OUT / "status-last.json"  # info: set STATUS_PATH
LAST_PATH = OUT / "locations-last.json"  # info: set LAST_PATH
UA = "RootRecord-Pacific/3 country-locations"  # info: set UA
TIMEOUT = 10  # info: set TIMEOUT
PAUSE = 0.2  # info: set PAUSE
MIN_AGE = timedelta(minutes=55)  # info: set MIN_AGE
FORECAST = "https://api.open-meteo.com/v1/forecast"  # info: set FORECAST


# ====================================================
# SECTION: function load_allowlist
# What it does: load allowlist.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_allowlist(path: Path) -> list:  # info: def load_allowlist
    data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    if not isinstance(data, list):  # info: if not isinstance ( data , list )
        raise ValueError("allowlist must be a JSON list")  # info: raise ValueError ( "allowlist must be a JSON list" )
    return data  # info: return data


# ====================================================
# SECTION: function catalog_rows
# What it does: catalog rows.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def catalog_rows() -> list[dict]:  # info: def catalog_rows
    data = json.loads(CATALOG.read_text(encoding="utf-8"))  # info: set data
    rows = data.get("locations") if isinstance(data, dict) else data  # info: set rows
    if not isinstance(rows, list):  # info: if not isinstance ( rows , list )
        raise ValueError("global-locations.json has no locations list")  # info: raise ValueError ( "global-locations.json has no locations list" )
    places = []  # info: set places
    for row in rows:  # info: for row in rows :
        if not isinstance(row, dict):  # info: if not isinstance ( row , dict )
            continue  # info: continue
        if str(row.get("country_code") or "") == "US":  # info: if str ( row . get ( "country_code"
            continue  # info: continue
        item = valid_entry(row)  # info: set item
        if item:  # info: if item :
            item["country_code"] = row.get("country_code") or ""  # info: item [ "country_code" ] = row . get
            item["country_name"] = row.get("country_name") or item["country_code"]  # info: item [ "country_name" ] = row . get
            places.append(item)  # info: places . append ( item )
    return places  # info: return places


# ====================================================
# SECTION: function select_places
# What it does: select places.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def select_places(raw: list) -> list[dict]:  # info: def select_places
    catalog = catalog_rows()  # info: set catalog
    if not raw:  # info: if not raw :
        return catalog  # info: return catalog
    wanted = []  # info: set wanted
    for row in raw:  # info: for row in raw :
        if isinstance(row, str):  # info: if isinstance ( row , str ) :
            wanted.append(row)  # info: wanted . append ( row )
        elif isinstance(row, dict) and isinstance(row.get("id"), str):  # info: elif isinstance ( row , dict ) and
            wanted.append(row["id"])  # info: wanted . append ( row [ "id" ]
    by_id = {place["id"]: place for place in catalog}  # info: set by_id
    chosen = []  # info: set chosen
    for loc_id in wanted:  # info: for loc_id in wanted :
        if loc_id in by_id:  # info: if loc_id in by_id :
            chosen.append(by_id[loc_id])  # info: chosen . append ( by_id [ loc_id ]
            continue  # info: continue
        direct = valid_entry(next((row for row in raw if isinstance(row, dict) and row.get("id") == loc_id), None))  # info: set direct
        if direct:  # info: if direct :
            chosen.append(direct)  # info: chosen . append ( direct )
    return chosen  # info: return chosen


# ====================================================
# SECTION: function valid_entry
# What it does: valid entry.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def valid_entry(entry: object) -> dict | None:  # info: def valid_entry
    if not isinstance(entry, dict):  # info: if not isinstance ( entry , dict )
        return None  # info: return None
    loc_id = entry.get("id")  # info: set loc_id
    lat = entry.get("lat")  # info: set lat
    lon = entry.get("lon")  # info: set lon
    if not isinstance(loc_id, str) or not loc_id:  # info: if not isinstance ( loc_id , str )
        return None  # info: return None
    if isinstance(lat, bool) or isinstance(lon, bool):  # info: if isinstance ( lat , bool ) or
        return None  # info: return None
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):  # info: if not isinstance ( lat , ( int
        return None  # info: return None
    return {"id": loc_id, "lat": float(lat), "lon": float(lon), "name": entry.get("name") or loc_id}  # info: return { "id" : loc_id , "lat" :


# ====================================================
# SECTION: function fetch_current
# What it does: fetch current.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_current(entry: dict) -> dict:  # info: def fetch_current
    query = urllib.parse.urlencode(  # info: set query
        {  # info: {
            "latitude": entry["lat"],  # info: "latitude" : entry [ "lat" ] ,
            "longitude": entry["lon"],  # info: "longitude" : entry [ "lon" ] ,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",  # info: "current" : "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation" ,
            "timezone": "UTC",  # info: "timezone" : "UTC" ,
        }  # info: }
    )  # info: )
    base = {  # info: set base
        "id": entry["id"],  # info: "id" : entry [ "id" ] ,
        "name": entry["name"],  # info: "name" : entry [ "name" ] ,
        "country_code": entry.get("country_code") or "",  # info: "country_code" : entry . get ( "country_code" )
        "country_name": entry.get("country_name") or "",  # info: "country_name" : entry . get ( "country_name" )
        "lat": entry["lat"],  # info: "lat" : entry [ "lat" ] ,
        "lon": entry["lon"],  # info: "lon" : entry [ "lon" ] ,
        "provider": "open-meteo",  # info: "provider" : "open-meteo" ,
    }  # info: }
    req = urllib.request.Request(FORECAST + "?" + query, headers={"User-Agent": UA})  # info: set req
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:  # info: with urllib . request . urlopen ( req
            payload = json.load(response)  # info: set payload
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):  # info: except ( HTTPError , URLError , TimeoutError ,
        return {**base, "obs_ts": None, "temp_c": None, "error": "fetch_failed"}  # info: return { ** base , "obs_ts" : None
    current = payload.get("current") or {}  # info: set current
    return {  # info: return {
        **base,  # info: ** base ,
        "obs_ts": current.get("time"),  # info: "obs_ts" : current . get ( "time" )
        "temp_c": current.get("temperature_2m"),  # info: "temp_c" : current . get ( "temperature_2m" )
        "humidity_pct": current.get("relative_humidity_2m"),  # info: "humidity_pct" : current . get ( "relative_humidity_2m" )
        "wind_kph": current.get("wind_speed_10m"),  # info: "wind_kph" : current . get ( "wind_speed_10m" )
        "precipitation_mm": current.get("precipitation"),  # info: "precipitation_mm" : current . get ( "precipitation" )
    }  # info: }


# ====================================================
# SECTION: function write_json
# What it does: write json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_json(path: Path, payload: dict) -> None:  # info: def write_json
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function snapshot_is_fresh
# What it does: snapshot is fresh.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def snapshot_is_fresh() -> bool:  # info: def snapshot_is_fresh
    if "--force" in sys.argv or not LAST_PATH.is_file():  # info: if "--force" in sys . argv or not
        return False  # info: return False
    try:  # info: try :
        payload = json.loads(LAST_PATH.read_text(encoding="utf-8"))  # info: set payload
        stamp = datetime.fromisoformat(payload["updated_at"])  # info: set stamp
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):  # info: except ( OSError , json . JSONDecodeError ,
        return False  # info: return False
    if stamp.tzinfo is None:  # info: if stamp . tzinfo is None :
        stamp = stamp.replace(tzinfo=HST)  # info: set stamp
    return datetime.now(HST) - stamp < MIN_AGE  # info: return datetime . now ( HST ) -


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run() -> dict:  # info: def run
    OUT.mkdir(parents=True, exist_ok=True)  # info: OUT . mkdir ( parents = True ,
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    if snapshot_is_fresh():  # info: if snapshot_is_fresh ( ) :
        return {  # info: return {
            "ok": True,  # info: "ok" : True ,
            "http_calls": 0,  # info: "http_calls" : 0 ,
            "note": "snapshot_fresh",  # info: "note" : "snapshot_fresh" ,
            "updated_at": datetime.now(HST).isoformat(timespec="seconds"),  # info: "updated_at" : datetime . now ( HST )
        }  # info: }
    raw = load_allowlist(ALLOWLIST)  # info: set raw
    entries = select_places(raw)  # info: set entries
    rows = []  # info: set rows
    http_calls = 0  # info: set http_calls
    for index, entry in enumerate(entries):  # info: for index , entry in enumerate ( entries
        if index:  # info: if index :
            time.sleep(PAUSE)  # info: time . sleep ( PAUSE )
        obs = fetch_current(entry)  # info: set obs
        http_calls += 1  # info: set http_calls
        write_json(OUT / f"{entry['id']}-last.json", obs)  # info: call write_json
        rows.append(obs)  # info: rows . append ( obs )
    updated_at = datetime.now(HST).isoformat(timespec="seconds")  # info: set updated_at
    write_json(  # info: call write_json
        LAST_PATH,  # info: LAST_PATH ,
        {"ok": True, "updated_at": updated_at, "rows": rows},  # info: { "ok" : True , "updated_at" : updated_at
    )  # info: )
    payload = {  # info: set payload
        "ok": True,  # info: "ok" : True ,
        "locations": len(entries),  # info: "locations" : len ( entries ) ,
        "skipped": max(0, len(raw) - len(entries)) if raw else 0,  # info: "skipped" : max ( 0 , len (
        "http_calls": http_calls,  # info: "http_calls" : http_calls ,
        "fetched": [row["id"] for row in rows if row.get("temp_c") is not None],  # info: "fetched" : [ row [ "id" ] for
        "updated_at": updated_at,  # info: "updated_at" : updated_at ,
    }  # info: }
    write_json(STATUS_PATH, payload)  # info: call write_json
    with LOG_PATH.open("a", encoding="utf-8") as log:  # info: with LOG_PATH . open ( "a" , encoding
        log.write(  # info: log . write (
            f"{payload['updated_at']} locations={payload['locations']} http_calls={payload['http_calls']}\n"  # info: f" { payload [ 'updated_at' ] } locations=
        )  # info: )
    return payload  # info: return payload


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    payload = run()  # info: set payload
    print(json.dumps(payload))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
