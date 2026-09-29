"""wwamap PNG + marine zone JPGs live in fetch/alerts.py and fetch/marine.py
respectively (they're pulled by resource category, per the map). This module
owns the remaining map-shaped resource: the best-effort/likely-broken
gfe_graphics page (Tier 6, self-reported broken by HFO -- see
config/resources.yaml `gfe_graphics`).
"""
from __future__ import annotations

from core.manifest import Manifest
from fetch import _engine


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()

    gfe_items = config.get("gfe_graphics") or []

    if not gfe_items:
        return []

    gfe = gfe_items[0]

    outcome = _engine.run_resource(
        manifest, base_dir, gfe["id"], gfe["url"],
        method="text", clean_text_body=False,
    )

    return [outcome]
