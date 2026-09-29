"""api.weather.gov/alerts/active?area=HI -- Tier 0, the one true
minute-level resource. Raw fetch/archive only; county mapping, severity
tagging, and dedupe are alerts/'s job (a different top-level folder), not
this fetch module's.
"""
from __future__ import annotations

from core.manifest import Manifest
from fetch import _engine

ALERTS_URL = "https://api.weather.gov/alerts/active?area=HI"
WWAMAP_URL = "https://www.weather.gov/wwamap/png/hfo.png"


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    alerts_outcome = _engine.run_resource(
        manifest, base_dir, "alerts_active_hi", ALERTS_URL,
        method="json",
        accept="application/geo+json",
        resource_id_hint="area=HI",
        clean_text_body=True,  # cleans only description/instruction/headline fields
    )
    map_outcome = _engine.run_resource(
        manifest, base_dir, "wwamap_png", WWAMAP_URL,
        method="image",
    )
    return [alerts_outcome, map_outcome]
