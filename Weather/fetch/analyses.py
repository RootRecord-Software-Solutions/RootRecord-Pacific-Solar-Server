# ==============================================================================
# FILE: Weather/fetch/analyses.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Streamline/surface/seastate analysis charts. Data-driven from
config/resources.yaml (`analyses:` section) -- the cycle-based gif families
(00/06/12/18Z) are expanded here rather than enumerated by hand in YAML.
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
    analyses = config["analyses"]  # info: set analyses
    outcomes = []  # info: set outcomes

    for item in analyses["items"]:  # info: for item in analyses [ "items" ] :
        outcomes.append(  # info: outcomes . append (
            _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")  # info: _engine . run_resource ( manifest , base_dir ,
        )  # info: )

    cycle_families = analyses.get("cycle_gif_families", {})  # info: set cycle_families
    for family in cycle_families.get("families", []):  # info: for family in cycle_families . get ( "families"
        stem = family["stem"]  # info: set stem
        base_url = family["base_url"]  # info: set base_url
        for cycle in family["cycles"]:  # info: for cycle in family [ "cycles" ] :
            resource_id = f"analyses_{stem}_{cycle}"  # info: set resource_id
            url = f"{base_url}{stem}_{cycle}.gif"  # info: set url
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(manifest, base_dir, resource_id, url, method="image")  # info: _engine . run_resource ( manifest , base_dir ,
            )  # info: )

    return outcomes  # info: return outcomes
