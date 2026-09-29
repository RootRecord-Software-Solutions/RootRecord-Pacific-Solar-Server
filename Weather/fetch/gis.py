"""Deterministically discover and fetch the newest NWS GIS boundary artifacts.

The NWS GIS catalog pages expose the current versioned ZIP/DBX downloads.
We keep the catalog page itself and fetch the newest matching artifact so
the resource does not become stale when NWS changes its publication date.
"""
from __future__ import annotations
import re
from datetime import datetime
from urllib.parse import urljoin
from core.manifest import Manifest
from core import http_client
from fetch import _engine

CATALOGS = {
    "nws_public_counties": ("https://www.weather.gov/gis/Counties", r'href="([^"]+\.zip)"'),
    "nws_public_zones": ("https://www.weather.gov/gis/publiczones", r'href="([^"]+\.zip)"'),
    "nws_zone_county": ("https://www.weather.gov/gis/ZoneCounty", r'href="([^"]+\.dbx)"'),
    "nws_cwa_boundaries": ("https://www.weather.gov/gis/CWABounds", r'href="([^"]+\.zip)"'),
    "nws_fire_zones": ("https://www.weather.gov/gis/firezones", r'href="([^"]+\.zip)"'),
    "nws_marine_zones": ("https://www.weather.gov/gis/MarineZones", r'href="([^"]+\.zip)"'),
}

def _latest(html: str, pattern: str) -> str | None:
    matches = re.findall(pattern, html, flags=re.I)
    if not matches:
        return None

    def key(value: str):
        # NWS versioned GIS files use ddmonyy (for example c_16ap26.zip).
        m = re.search(r"(?:^|[_-])(\d{2}[a-z]{3}\d{2})(?:\.|$)", value, re.I)
        if not m:
            return (0, datetime.min, value.lower())
        try:
            return (1, datetime.strptime(m.group(1).lower(), "%d%b%y"), value.lower())
        except ValueError:
            return (0, datetime.min, value.lower())

    return max(matches, key=key)

def fetch_all(manifest: Manifest, base_dir: str):
    outcomes = []
    for resource_id, (catalog_url, pattern) in CATALOGS.items():
        try:
            html = http_client.get(catalog_url, accept="text/html").content or b""
            href = _latest(html.decode("utf-8", errors="replace"), pattern)
        except Exception:
            href = None
        # Preserve the authoritative catalog page itself. The catalog
        # is evidence for which version was selected and is archived
        # separately from the downloaded GIS artifact.
        outcomes.append(_engine.run_resource(
            manifest, base_dir, f"{resource_id}_catalog", catalog_url,
            method="binary", expected_ext="html"
        ))
        if not href:
            continue
        url = urljoin(catalog_url, href)
        outcomes.append(_engine.run_resource(
            manifest, base_dir, resource_id, url, method="binary"
        ))
    return outcomes
