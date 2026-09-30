# ==============================================================================
# FILE: Weather/fetch/radar.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""radar.weather.gov/ridge/standard/HAWAII_loop.gif (static, Tier 6) + FTM
radar status text. The interactive Ridge2 tile viewer is explicitly out of
scope -- see config/resources.yaml `radar.interactive_reference_only`.
"""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re

from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine  # info: from fetch import _engine

# /hfo/FTM is a real HTML page (not a plain-text product like the
# api.weather.gov or product.php resources), reporting all FOUR Hawaii
# radars' outage status separately, each inside its own <pre> block:
#   <strong>NAME (CODE)&nbsp;<a href="...">...</a></strong></p>
#   <p>    <pre>STATUS TEXT</pre></p>
# A single "grab the first <pre>" extractor (like
# text_products_fallback.extract_pre_text) would silently drop the other
# three radars' status -- this keeps each block paired with its own label.
# Confirmed against a live fetch of /hfo/FTM on 2026-09-25/26.
_FTM_BLOCK_RE = re.compile(  # info: set _FTM_BLOCK_RE
    r'<strong>([^<]*?)&nbsp;<a[^>]*>.*?</strong>\s*</p>\s*<p>\s*<pre>(.*?)</pre>',  # info: r'<strong>([^<]*?)&nbsp;<a[^>]*>.*?</strong>\s*</p>\s*<p>\s*<pre>(.*?)</pre>' ,
    re.DOTALL,  # info: re . DOTALL ,
)  # info: )


# ====================================================
# SECTION: function extract_ftm_status
# What it does: Pulls each per-radar status block out of /hfo/FTM's HTML page, keeping each radar's own label attached to its message so four separate statuses don't collapse into one unlabeled bl
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def extract_ftm_status(html_bytes: bytes) -> str:  # info: def extract_ftm_status
    """Pulls each per-radar status block out of /hfo/FTM's HTML page,
    keeping each radar's own label attached to its message so four separate
    statuses don't collapse into one unlabeled blob.
    """
    html = html_bytes.decode("utf-8", errors="replace")  # info: set html
    blocks = _FTM_BLOCK_RE.findall(html)  # info: set blocks
    if not blocks:  # info: if not blocks :
        raise ValueError("no radar status blocks found -- page shape may have changed")  # info: raise ValueError ( "no radar status blocks found -- page shape may have changed" )

    sections = []  # info: set sections
    for label, body in blocks:  # info: for label , body in blocks :
        label = label.strip()  # info: set label
        for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
            label = label.replace(entity, char)  # info: set label
            body = body.replace(entity, char)  # info: set body
        sections.append(f"{label}\n{body.strip()}")  # info: sections . append ( f" { label }

    return "\n\n----\n\n".join(sections)  # info: return "\n\n----\n\n" . join ( sections )


# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    config = _engine.load_resources_yaml()  # info: set config
    radar = config["radar"]  # info: set radar
    outcomes = []  # info: set outcomes

    for item in radar["items"]:  # info: for item in radar [ "items" ] :
        method = item.get("method", "image")  # info: set method
        if method == "image":  # info: if method == "image" :
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")  # info: _engine . run_resource ( manifest , base_dir ,
            )  # info: )
        else:  # ftm_radar_status -- HTML page, 4 per-radar <pre> blocks (see extract_ftm_status)
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(  # info: _engine . run_resource (
                    manifest, base_dir, item["id"], item["url"],  # info: manifest , base_dir , item [ "id" ]
                    method="text", clean_text_body=True,  # info: set method
                    extract_text=extract_ftm_status,  # info: set extract_text
                )  # info: )
            )  # info: )

    return outcomes  # info: return outcomes
