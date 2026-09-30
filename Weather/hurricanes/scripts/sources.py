# ==============================================================================
# FILE: Weather/hurricanes/scripts/sources.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""CurrentStorms.json (NHC) baseline poll + CPHC TCM/TCP/TCD/TCU pulls for
whatever storm(s) pass the relevance filter. Writes into
Database/Weather/Hawai'i/hurricanes/tracking/ -- same core/ mechanism
(http_client, hst_time) as every other part of weather/, no special-casing.

RAMMB/JTWC are intentionally NOT called here yet -- see
hurricanes/references/sources.md; hosts/paths aren't confirmed.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

from core import http_client, hst_time  # info: from core import http_client , hst_time
from hurricanes.scripts.distance import is_relevant  # info: from hurricanes . scripts . distance import is_relevant

CURRENT_STORMS_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"  # info: set CURRENT_STORMS_URL

CPHC_PRODUCT_TYPES = ["TCM", "TCP", "TCD", "TCU", "HLS"]  # info: set CPHC_PRODUCT_TYPES
CPHC_PRODUCT_URL_TEMPLATE = "https://api.weather.gov/products/types/{ptype}/locations/HFO"  # info: set CPHC_PRODUCT_URL_TEMPLATE


# ====================================================
# SECTION: function fetch_current_storms
# What it does: Returns the raw list of active storm entries from NHC's structured feed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_current_storms() -> list[dict[str, Any]]:  # info: def fetch_current_storms
    """Returns the raw list of active storm entries from NHC's structured feed."""  # info: """Returns the raw list of active storm entries from NHC's structured feed."""
    result = http_client.get(CURRENT_STORMS_URL, accept="application/json")  # info: set result
    if result.content is None:  # info: if result . content is None :
        return []  # info: return [ ]
    envelope = json.loads(result.content.decode("utf-8"))  # info: set envelope
    return envelope.get("activeStorms", [])  # info: return envelope . get ( "activeStorms" , [


# ====================================================
# SECTION: function relevant_storms
# What it does: Filter NHC's global storm list down to ones CPHC/Hawaii should care about, per the 800nmi-or-CPHC-advisory rule.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def relevant_storms(storms: list[dict[str, Any]]) -> list[dict[str, Any]]:  # info: def relevant_storms
    """Filter NHC's global storm list down to ones CPHC/Hawaii should care
    about, per the 800nmi-or-CPHC-advisory rule.
    """
    out = []  # info: set out
    for storm in storms:  # info: for storm in storms :
        try:  # info: try :
            lat = float(storm.get("latitudeNumeric", storm.get("lat", 0.0)))  # info: set lat
            lon = float(storm.get("longitudeNumeric", storm.get("lon", 0.0)))  # info: set lon
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            continue  # info: continue
        has_cphc_advisory = str(storm.get("id", "")).upper().startswith("CP")  # info: set has_cphc_advisory
        if is_relevant(lat=lat, lon=lon, has_cphc_advisory=has_cphc_advisory):  # info: if is_relevant ( lat = lat , lon
            out.append(storm)  # info: out . append ( storm )
    return out  # info: return out


# ====================================================
# SECTION: function _storm_tracking_dir
# What it does:  storm tracking dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _storm_tracking_dir(hurricanes_base_dir: str, storm_name: str, first_seen_iso: str) -> Path:  # info: def _storm_tracking_dir
    # <storm_name>_<TIMESTAMP> per weather_skill_architecture.md Section 5 --
    # TIMESTAMP is when we first started tracking this storm, not "now", so
    # the folder name is stable across the storm's lifetime.
    safe_ts = first_seen_iso.replace(":", "").replace("-", "")  # info: set safe_ts
    return Path(hurricanes_base_dir) / "tracking" / f"{storm_name}_{safe_ts}"  # info: return Path ( hurricanes_base_dir ) / "tracking" /


# ====================================================
# SECTION: function update_track
# What it does: Append this poll's position to the storm's track.json, creating the storm's tracking folder on first sight.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def update_track(hurricanes_base_dir: str, storm: dict[str, Any]) -> Path:  # info: def update_track
    """Append this poll's position to the storm's track.json, creating the
    storm's tracking folder on first sight.
    """
    storm_name = storm.get("name", storm.get("id", "unknown_storm")).replace(" ", "_")  # info: set storm_name
    now = hst_time.hst_now().isoformat()  # info: set now

    # Find an existing folder for this storm (any TIMESTAMP suffix) or start one.
    tracking_root = Path(hurricanes_base_dir) / "tracking"  # info: set tracking_root
    existing = sorted(tracking_root.glob(f"{storm_name}_*")) if tracking_root.is_dir() else []  # info: set existing
    storm_dir = existing[0] if existing else _storm_tracking_dir(hurricanes_base_dir, storm_name, now)  # info: set storm_dir
    storm_dir.mkdir(parents=True, exist_ok=True)  # info: storm_dir . mkdir ( parents = True ,
    (storm_dir / "sources").mkdir(exist_ok=True)  # info: call (

    track_path = storm_dir / "track.json"  # info: set track_path
    track = json.loads(track_path.read_text()) if track_path.is_file() else {"storm_name": storm_name, "positions": []}  # info: set track
    track["positions"].append({  # info: track [ "positions" ] . append ( {
        "polled_at_hst": now,  # info: "polled_at_hst" : now ,
        "lat": storm.get("latitudeNumeric", storm.get("lat")),  # info: "lat" : storm . get ( "latitudeNumeric" ,
        "lon": storm.get("longitudeNumeric", storm.get("lon")),  # info: "lon" : storm . get ( "longitudeNumeric" ,
        "intensity": storm.get("intensity"),  # info: "intensity" : storm . get ( "intensity" )
        "classification": storm.get("classification"),  # info: "classification" : storm . get ( "classification" )
    })  # info: } )
    track_path.write_text(json.dumps(track, indent=2, ensure_ascii=False), encoding="utf-8")  # info: track_path . write_text ( json . dumps (
    return storm_dir  # info: return storm_dir


# ====================================================
# SECTION: function poll
# What it does: Full baseline-poll cycle: fetch CurrentStorms.json, filter to relevant storms, update each one's track.json. Per-storm TCM/TCP/TCD/TCU advisory text pulls are left to a follow-up p
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poll(hurricanes_base_dir: str) -> list[Path]:  # info: def poll
    """Full baseline-poll cycle: fetch CurrentStorms.json, filter to
    relevant storms, update each one's track.json. Per-storm TCM/TCP/TCD/TCU
    advisory text pulls are left to a follow-up pass once a storm is
    confirmed relevant (kept separate so the cheap baseline check never
    blocks on the more expensive per-storm advisory fetches).
    """
    storms = fetch_current_storms()  # info: set storms
    relevant = relevant_storms(storms)  # info: set relevant
    return [update_track(hurricanes_base_dir, storm) for storm in relevant]  # info: return [ update_track ( hurricanes_base_dir , storm )
