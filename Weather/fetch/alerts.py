# ==============================================================================
# FILE: Weather/fetch/alerts.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""api.weather.gov/alerts/active?area=HI -- Tier 0, the one true
minute-level resource. Raw fetch/archive only; county mapping, severity
tagging, and dedupe are alerts/'s job (a different top-level folder), not
this fetch module's.
"""
from __future__ import annotations  # info: from __future__ import annotations

from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine  # info: from fetch import _engine

ALERTS_URL = "https://api.weather.gov/alerts/active?area=HI"  # info: set ALERTS_URL
WWAMAP_URL = "https://www.weather.gov/wwamap/png/hfo.png"  # info: set WWAMAP_URL


# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str, only: set[str] | None = None) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    outcomes = []  # info: set outcomes
    if only is None or "alerts_active_hi" in only:  # info: if only is None or "alerts_active_hi" in only
        outcomes.append(_engine.run_resource(  # info: outcomes . append ( _engine . run_resource (
            manifest, base_dir, "alerts_active_hi", ALERTS_URL,  # info: manifest , base_dir , "alerts_active_hi" , ALERTS_URL ,
            method="json",  # info: set method
            accept="application/geo+json",  # info: set accept
            resource_id_hint="area=HI",  # info: set resource_id_hint
            clean_text_body=True,  # cleans only description/instruction/headline fields
        ))  # info: ) )
    if only is None or "wwamap_png" in only:  # info: if only is None or "wwamap_png" in only
        outcomes.append(_engine.run_resource(  # info: outcomes . append ( _engine . run_resource (
            manifest, base_dir, "wwamap_png", WWAMAP_URL,  # info: manifest , base_dir , "wwamap_png" , WWAMAP_URL ,
            method="image",  # info: set method
        ))  # info: ) )
    return outcomes  # info: return outcomes
