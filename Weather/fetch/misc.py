# ==============================================================================
# FILE: Weather/fetch/misc.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Static/miscellaneous weather resources that do not fit text/image categories."""  # info: """Static/miscellaneous weather resources that do not fit text/image categories."""
from __future__ import annotations  # info: from __future__ import annotations
from core.manifest import Manifest  # info: from core . manifest import Manifest
from core import hst_time  # info: from core import hst_time
from fetch import _engine  # info: from fetch import _engine

# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str, only: set[str] | None = None) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    config = _engine.load_resources_yaml()  # info: set config
    outcomes = []  # info: set outcomes
    for item in config.get("misc", []):  # info: for item in config . get ( "misc"
        if only is not None and item.get("id") not in only:  # info: if only is not None and item .
            continue  # info: continue
        url = item.get("url")  # info: set url
        if item.get("url_template"):  # info: if item . get ( "url_template" ) :
            year = hst_time.hst_now().year  # info: set year
            url = item["url_template"].format(year=year)  # info: set url
        if not url:  # info: if not url :
            continue  # info: continue
        outcomes.append(_engine.run_resource(  # info: outcomes . append ( _engine . run_resource (
            manifest, base_dir, item["id"], url,  # info: manifest , base_dir , item [ "id" ]
            method=item.get("method", "binary"),  # info: set method
            expected_ext=item.get("expected_ext"),  # info: set expected_ext
        ))  # info: ) )
    return outcomes  # info: return outcomes
