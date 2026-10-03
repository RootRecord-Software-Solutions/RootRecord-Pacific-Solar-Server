# ==============================================================================
# FILE: Reports/pipeline/owners.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""One owner per measured fact in a window. Hurricane keeps storm-track lines the weather desk did not say."""
from __future__ import annotations  # info: from __future__ import annotations


# ====================================================
# SECTION: function trim_hurricane
# What it does: Drop hurricane sentences already spoken by the latest NWS report. It does not delete that report.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def trim_hurricane(spoken: list[str]) -> list[str]:  # info: def trim_hurricane
    try:  # info: try
        import store  # info: import store
        nws = store.latest_slug("nws_weather")  # info: set nws
    except Exception:  # info: except Exception
        return list(spoken)  # info: return list ( spoken )
    if not nws:  # info: if not nws
        return list(spoken)  # info: return list ( spoken )
    prior = " ".join(nws.get("spoken") or [])  # info: set prior
    if not prior:  # info: if not prior
        text = " ".join(section.get("text") or "" for section in nws.get("sections") or [])  # info: set text
        prior = text  # info: set prior
    kept = [line for line in spoken if line and line not in prior]  # info: set kept
    if kept:  # info: if kept
        return kept  # info: return kept
    return ["Hurricane desk. Storm facts already spoken are on the weather report."]  # info: return pointer
