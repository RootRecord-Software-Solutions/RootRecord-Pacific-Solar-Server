"""CurrentStorms.json (NHC) baseline poll + CPHC TCM/TCP/TCD/TCU pulls for
whatever storm(s) pass the relevance filter. Writes into
Database/WEATHER/Hawai'i/hurricanes/tracking/ -- same core/ mechanism
(http_client, hst_time) as every other part of weather/, no special-casing.

RAMMB/JTWC are intentionally NOT called here yet -- see
hurricanes/references/sources.md; hosts/paths aren't confirmed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core import http_client, hst_time
from hurricanes.scripts.distance import is_relevant

CURRENT_STORMS_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"

CPHC_PRODUCT_TYPES = ["TCM", "TCP", "TCD", "TCU", "HLS"]
CPHC_PRODUCT_URL_TEMPLATE = "https://api.weather.gov/products/types/{ptype}/locations/HFO"


def fetch_current_storms() -> list[dict[str, Any]]:
    """Returns the raw list of active storm entries from NHC's structured feed."""
    result = http_client.get(CURRENT_STORMS_URL, accept="application/json")
    if result.content is None:
        return []
    envelope = json.loads(result.content.decode("utf-8"))
    return envelope.get("activeStorms", [])


def relevant_storms(storms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter NHC's global storm list down to ones CPHC/Hawaii should care
    about, per the 800nmi-or-CPHC-advisory rule.
    """
    out = []
    for storm in storms:
        try:
            lat = float(storm.get("latitudeNumeric", storm.get("lat", 0.0)))
            lon = float(storm.get("longitudeNumeric", storm.get("lon", 0.0)))
        except (TypeError, ValueError):
            continue
        has_cphc_advisory = str(storm.get("id", "")).upper().startswith("CP")
        if is_relevant(lat=lat, lon=lon, has_cphc_advisory=has_cphc_advisory):
            out.append(storm)
    return out


def _storm_tracking_dir(hurricanes_base_dir: str, storm_name: str, first_seen_iso: str) -> Path:
    # <storm_name>_<TIMESTAMP> per weather_skill_architecture.md Section 5 --
    # TIMESTAMP is when we first started tracking this storm, not "now", so
    # the folder name is stable across the storm's lifetime.
    safe_ts = first_seen_iso.replace(":", "").replace("-", "")
    return Path(hurricanes_base_dir) / "tracking" / f"{storm_name}_{safe_ts}"


def update_track(hurricanes_base_dir: str, storm: dict[str, Any]) -> Path:
    """Append this poll's position to the storm's track.json, creating the
    storm's tracking folder on first sight.
    """
    storm_name = storm.get("name", storm.get("id", "unknown_storm")).replace(" ", "_")
    now = hst_time.hst_now().isoformat()

    # Find an existing folder for this storm (any TIMESTAMP suffix) or start one.
    tracking_root = Path(hurricanes_base_dir) / "tracking"
    existing = sorted(tracking_root.glob(f"{storm_name}_*")) if tracking_root.is_dir() else []
    storm_dir = existing[0] if existing else _storm_tracking_dir(hurricanes_base_dir, storm_name, now)
    storm_dir.mkdir(parents=True, exist_ok=True)
    (storm_dir / "sources").mkdir(exist_ok=True)

    track_path = storm_dir / "track.json"
    track = json.loads(track_path.read_text()) if track_path.is_file() else {"storm_name": storm_name, "positions": []}
    track["positions"].append({
        "polled_at_hst": now,
        "lat": storm.get("latitudeNumeric", storm.get("lat")),
        "lon": storm.get("longitudeNumeric", storm.get("lon")),
        "intensity": storm.get("intensity"),
        "classification": storm.get("classification"),
    })
    track_path.write_text(json.dumps(track, indent=2, ensure_ascii=False), encoding="utf-8")
    return storm_dir


def poll(hurricanes_base_dir: str) -> list[Path]:
    """Full baseline-poll cycle: fetch CurrentStorms.json, filter to
    relevant storms, update each one's track.json. Per-storm TCM/TCP/TCD/TCU
    advisory text pulls are left to a follow-up pass once a storm is
    confirmed relevant (kept separate so the cheap baseline check never
    blocks on the more expensive per-storm advisory fetches).
    """
    storms = fetch_current_storms()
    relevant = relevant_storms(storms)
    return [update_track(hurricanes_base_dir, storm) for storm in relevant]
