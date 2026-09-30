# ==============================================================================
# FILE: Weather/fetch/ndfd_gridpoint.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""api.weather.gov/points/{lat,lon} resolver, Tier 6.

OPEN ITEM (per NWS_Hawaii_Resource_Map.md Section 3 / nws_plan.md Section 9):
the plan flags this resolver as something to build and cache, but never
settles WHICH coordinates to poll -- no lat/lon list was ever specified.
Building this module means picking that list, which is a real content
decision, not a code decision, so it isn't made here.

What this module DOES provide, ready for whenever that list exists: the
resolve-and-cache mechanism itself (`resolve_gridpoint`), a normal
`fetch_all` that reads `config/resources.yaml`'s `ndfd.items[0].points`
key if/when it's added, and returns an empty (not failing) result today
since that key doesn't exist yet.
"""
from __future__ import annotations  # info: from __future__ import annotations

from typing import Any  # info: from typing import Any

from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine  # info: from fetch import _engine

_gridpoint_cache: dict[tuple[float, float], str] = {}  # (lat, lon) -> resolved forecast URL


# ====================================================
# SECTION: function resolve_gridpoint
# What it does: Returns the cached NDFD gridpoint forecast URL for (lat, lon), resolving and caching it via api.weather.gov/points/{lat},{lon} on first use. Per the plan: resolve once, never re-re
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def resolve_gridpoint(lat: float, lon: float) -> str:  # info: def resolve_gridpoint
    """Returns the cached NDFD gridpoint forecast URL for (lat, lon),
    resolving and caching it via api.weather.gov/points/{lat},{lon} on
    first use. Per the plan: resolve once, never re-resolve on every poll.
    """
    key = (lat, lon)  # info: set key
    if key in _gridpoint_cache:  # info: if key in _gridpoint_cache :
        return _gridpoint_cache[key]  # info: return _gridpoint_cache [ key ]

    import json  # info: import json
    from core import http_client  # info: from core import http_client

    url = f"https://api.weather.gov/points/{lat},{lon}"  # info: set url
    result = http_client.get(url, accept="application/geo+json")  # info: set result
    envelope = json.loads(result.content.decode("utf-8"))  # info: set envelope
    forecast_url = envelope["properties"]["forecastGridData"]  # info: set forecast_url
    _gridpoint_cache[key] = forecast_url  # info: _gridpoint_cache [ key ] = forecast_url
    return forecast_url  # info: return forecast_url


# ====================================================
# SECTION: function fetch_all
# What it does: Reads `config/resources.yaml`'s `ndfd.items[0].points` list (`items[0]` being the `points_resolver` entry) -- see this module's docstring. Returns an empty list rather than raising
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    """Reads `config/resources.yaml`'s `ndfd.items[0].points` list
    (`items[0]` being the `points_resolver` entry) -- see this module's
    docstring. Returns an empty list rather than raising if `points` isn't
    configured, so scheduler/run_cycle.py's Tier 6 dispatch doesn't need a
    special case for "not configured yet".

    BUGFIX (this session): `ndfd.items` in `config/resources.yaml` is a
    LIST (one dict per resource entry), matching every other category in
    that file -- not a dict itself. The original version did
    `config["ndfd"].get("items", {})` and then `.get("points")` on the
    result, which is a list, so `isinstance(..., dict)` was always False
    and this returned `[]` unconditionally, even once a `points` key was
    added. Now correctly looks up the `points_resolver` entry inside the
    list.
    """
    config = _engine.load_resources_yaml()  # info: set config
    ndfd_items: list[dict[str, Any]] = config.get("ndfd", {}).get("items", [])  # info: set ndfd_items
    resolver_entry = next((item for item in ndfd_items if item.get("id") == "points_resolver"), None)  # info: set resolver_entry
    points = resolver_entry.get("points") if resolver_entry else None  # info: set points
    if not points:  # info: if not points :
        return []  # info: return [ ]

    outcomes = []  # info: set outcomes
    for point in points:  # info: for point in points :
        forecast_url = resolve_gridpoint(point["lat"], point["lon"])  # info: set forecast_url
        resource_id = f"ndfd_gridpoint_{point['id']}"  # info: set resource_id
        outcomes.append(  # info: outcomes . append (
            _engine.run_resource(  # info: _engine . run_resource (
                manifest, base_dir, resource_id, forecast_url,  # info: manifest , base_dir , resource_id , forecast_url ,
                method="json", resource_id_hint=resource_id,  # info: set method
            )  # info: )
        )  # info: )
    return outcomes  # info: return outcomes
