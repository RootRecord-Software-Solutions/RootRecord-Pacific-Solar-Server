# ==============================================================================
# FILE: Weather/fetch/satellite.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""HFO-hosted IR satellite gifs + the GOES-18 NESDIS sector gif. Reads
its resource list from config/resources.yaml (`satellite:` section) rather
than hardcoding URLs twice.
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
    satellite = config["satellite"]  # info: set satellite
    outcomes = []  # info: set outcomes

    for item in satellite["items"]:  # info: for item in satellite [ "items" ] :
        outcomes.append(  # info: outcomes . append (
            _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")  # info: _engine . run_resource ( manifest , base_dir ,
        )  # info: )

    # Loop frames: {base_url}/{00..10}.gif per sector, per config's
    # loop_frame_sectors block. Each frame gets its own resource id so the
    # manifest/archiver treat them as independent resources (they change
    # independently as the loop advances).
    lfs = satellite.get("loop_frame_sectors", {})  # info: set lfs
    lo, hi = lfs.get("frame_range", [0, 10])  # info: lo , hi = lfs . get (
    for sector in lfs.get("sectors", []):  # info: for sector in lfs . get ( "sectors"
        for frame in range(lo, hi + 1):  # info: for frame in range ( lo , hi
            frame_id = f"satellite_loop_{sector['key']}_{frame:02d}"  # info: set frame_id
            url = f"{sector['base_url']}{frame:02d}.gif"  # info: set url
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(manifest, base_dir, frame_id, url, method="image")  # info: _engine . run_resource ( manifest , base_dir ,
            )  # info: )

    return outcomes  # info: return outcomes
