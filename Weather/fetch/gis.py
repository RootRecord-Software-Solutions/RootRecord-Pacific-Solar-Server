# ==============================================================================
# FILE: Weather/fetch/gis.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Deterministically discover and fetch the newest NWS GIS boundary artifacts.

The NWS GIS catalog pages expose the current versioned ZIP/DBX downloads.
We keep the catalog page itself and fetch the newest matching artifact so
the resource does not become stale when NWS changes its publication date.
"""
from __future__ import annotations  # info: from __future__ import annotations
import re  # info: import re
from datetime import datetime  # info: from datetime import datetime
from urllib.parse import urljoin  # info: from urllib . parse import urljoin
from core.manifest import Manifest  # info: from core . manifest import Manifest
from core import http_client  # info: from core import http_client
from fetch import _engine  # info: from fetch import _engine

# ====================================================
# SECTION: CATALOGS
# What it does: Set CATALOGS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
CATALOGS = {  # info: set CATALOGS
    "nws_public_counties": ("https://www.weather.gov/gis/Counties", r'href="([^"]+\.zip)"'),  # info: call "nws_public_counties"
    "nws_public_zones": ("https://www.weather.gov/gis/publiczones", r'href="([^"]+\.zip)"'),  # info: call "nws_public_zones"
    "nws_zone_county": ("https://www.weather.gov/gis/ZoneCounty", r'href="([^"]+\.dbx)"'),  # info: call "nws_zone_county"
    "nws_cwa_boundaries": ("https://www.weather.gov/gis/CWABounds", r'href="([^"]+\.zip)"'),  # info: call "nws_cwa_boundaries"
    "nws_fire_zones": ("https://www.weather.gov/gis/firezones", r'href="([^"]+\.zip)"'),  # info: call "nws_fire_zones"
    "nws_marine_zones": ("https://www.weather.gov/gis/MarineZones", r'href="([^"]+\.zip)"'),  # info: call "nws_marine_zones"
}  # info: }

# ====================================================
# SECTION: function _latest
# What it does:  latest.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _latest(html: str, pattern: str) -> str | None:  # info: def _latest
    matches = re.findall(pattern, html, flags=re.I)  # info: set matches
    if not matches:  # info: if not matches :
        return None  # info: return None

    def key(value: str):  # info: def key
        # NWS versioned GIS files use ddmonyy (for example c_16ap26.zip).
        m = re.search(r"(?:^|[_-])(\d{2}[a-z]{3}\d{2})(?:\.|$)", value, re.I)  # info: set m
        if not m:  # info: if not m :
            return (0, datetime.min, value.lower())  # info: return ( 0 , datetime . min ,
        try:  # info: try :
            return (1, datetime.strptime(m.group(1).lower(), "%d%b%y"), value.lower())  # info: return ( 1 , datetime . strptime (
        except ValueError:  # info: except ValueError :
            return (0, datetime.min, value.lower())  # info: return ( 0 , datetime . min ,

    return max(matches, key=key)  # info: return max ( matches , key = key

# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str):  # info: def fetch_all
    outcomes = []  # info: set outcomes
    for resource_id, (catalog_url, pattern) in CATALOGS.items():  # info: for resource_id , ( catalog_url , pattern )
        try:  # info: try :
            html = http_client.get(catalog_url, accept="text/html").content or b""  # info: set html
            href = _latest(html.decode("utf-8", errors="replace"), pattern)  # info: set href
        except Exception:  # info: except Exception :
            href = None  # info: set href
        # Preserve the authoritative catalog page itself. The catalog
        # is evidence for which version was selected and is archived
        # separately from the downloaded GIS artifact.
        outcomes.append(_engine.run_resource(  # info: outcomes . append ( _engine . run_resource (
            manifest, base_dir, f"{resource_id}_catalog", catalog_url,  # info: manifest , base_dir , f" { resource_id }
            method="binary", expected_ext="html"  # info: set method
        ))  # info: ) )
        if not href:  # info: if not href :
            continue  # info: continue
        url = urljoin(catalog_url, href)  # info: set url
        outcomes.append(_engine.run_resource(  # info: outcomes . append ( _engine . run_resource (
            manifest, base_dir, resource_id, url, method="binary"  # info: manifest , base_dir , resource_id , url ,
        ))  # info: ) )
    return outcomes  # info: return outcomes
