# ==============================================================================
# FILE: Weather/fetch/maps.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""wwamap PNG + marine zone JPGs live in fetch/alerts.py and fetch/marine.py
respectively (they're pulled by resource category, per the map). This module
owns the remaining map-shaped resource: the best-effort/likely-broken
gfe_graphics page (Tier 6, self-reported broken by HFO -- see
config/resources.yaml `gfe_graphics`).
"""
from __future__ import annotations  # info: from __future__ import annotations

from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine  # info: from fetch import _engine


# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    config = _engine.load_resources_yaml()  # info: set config

    gfe_items = config.get("gfe_graphics") or []  # info: set gfe_items

    if not gfe_items:  # info: if not gfe_items :
        return []  # info: return [ ]

    gfe = gfe_items[0]  # info: set gfe

    outcome = _engine.run_resource(  # info: set outcome
        manifest, base_dir, gfe["id"], gfe["url"],  # info: manifest , base_dir , gfe [ "id" ]
        method="text", clean_text_body=False,  # info: set method
    )  # info: )

    return [outcome]  # info: return [ outcome ]
