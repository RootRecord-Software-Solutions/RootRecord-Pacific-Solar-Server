# ==============================================================================
# FILE: Weather/fetch/aviation.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""TAFs, AIRMETs, SIGMETs. Data-driven from config/resources.yaml."""  # info: """TAFs, AIRMETs, SIGMETs. Data-driven from config/resources.yaml."""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re

from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine, text_products_fallback  # info: from fetch import _engine , text_products_fallback


# ====================================================
# SECTION: function extract_phfo_sigmets
# What it does: Keep Honolulu-issued blocks from the Aviation Weather Center SIGMET feed. The raw feed is worldwide. HFO products are the blocks that name PHFO (international, tropical-cyclone, an
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def extract_phfo_sigmets(raw: bytes) -> str:  # info: def extract_phfo_sigmets
    """Keep Honolulu-issued blocks from the Aviation Weather Center SIGMET feed.

    The raw feed is worldwide. HFO products are the blocks that name PHFO
    (international, tropical-cyclone, and volcanic-ash SIGMETs).
    """
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")  # info: set text
    parts = re.split(r"\n(?=Hazard:)", text)  # info: set parts
    kept = [part.strip() for part in parts if "PHFO" in part.upper()]  # info: set kept
    if not kept:  # info: if not kept :
        raise ValueError("no PHFO SIGMET in the international SIGMET feed")  # info: raise ValueError ( "no PHFO SIGMET in the international SIGMET feed" )
    return "\n\n".join(kept)  # info: return "\n\n" . join ( kept )


# ====================================================
# SECTION: function _extract_for
# What it does:  extract for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _extract_for(item: dict):  # info: def _extract_for
    url = item["url"]  # info: set url
    if item["id"] == "aviation_sigmets":  # info: if item [ "id" ] == "aviation_sigmets" :
        return extract_phfo_sigmets  # info: return extract_phfo_sigmets
    if url.endswith(".xml") or "/xml/" in url:  # info: if url . endswith ( ".xml" ) or
        return text_products_fallback.extract_rss_descriptions  # info: return text_products_fallback . extract_rss_descriptions
    return text_products_fallback.extract_pre_text  # info: return text_products_fallback . extract_pre_text


# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str, only: set[str] | None = None) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    config = _engine.load_resources_yaml()  # info: set config
    aviation = config["aviation"]  # info: set aviation
    outcomes = []  # info: set outcomes

    for item in aviation:  # info: for item in aviation :
        if only is not None and item["id"] not in only:  # info: if only is not None and item [
            continue  # info: continue
        outcomes.append(  # info: outcomes . append (
            _engine.run_resource(  # info: _engine . run_resource (
                manifest, base_dir, item["id"], item["url"],  # info: manifest , base_dir , item [ "id" ]
                method="text", clean_text_body=True,  # info: set method
                extract_text=_extract_for(item),  # info: set extract_text
                resource_id_hint=item["id"],  # info: set resource_id_hint
                expected_ext="txt",  # info: set expected_ext
            )  # info: )
        )  # info: )

    return outcomes  # info: return outcomes
