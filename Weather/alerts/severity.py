# ==============================================================================
# FILE: Weather/alerts/severity.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Tags an alert's severity tier, isolated so the threshold can change
without touching county-mapping or dedupe logic. Input is a single alert's
`properties` dict from api.weather.gov alert JSON.
"""
from __future__ import annotations  # info: from __future__ import annotations

from typing import Any  # info: from typing import Any

# api.weather.gov's own `severity` field values, ranked worst-first. Anything
# not in this list (rare/unknown) is treated as "Unknown" -- see below.
_SEVERITY_RANK = {"Extreme": 4, "Severe": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}  # info: set _SEVERITY_RANK

# Event names that are life-safety-critical regardless of the API's own
# severity field -- some NWS event types (e.g. Tornado Warning) should never
# be treated as routine even if severity metadata is missing/stale.
# ====================================================
# SECTION: _ALWAYS_CRITICAL_EVENTS
# What it does: Set _ALWAYS_CRITICAL_EVENTS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_ALWAYS_CRITICAL_EVENTS = {  # info: set _ALWAYS_CRITICAL_EVENTS
    "tornado warning",  # info: "tornado warning" ,
    "flash flood warning",  # info: "flash flood warning" ,
    "tsunami warning",  # info: "tsunami warning" ,
    "hurricane warning",  # info: "hurricane warning" ,
    "extreme wind warning",  # info: "extreme wind warning" ,
}  # info: }


# ====================================================
# SECTION: function severity_rank
# What it does: severity rank.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def severity_rank(props: dict[str, Any]) -> int:  # info: def severity_rank
    return _SEVERITY_RANK.get(props.get("severity", "Unknown"), 0)  # info: return _SEVERITY_RANK . get ( props . get


# ====================================================
# SECTION: function is_critical
# What it does: True for anything that should be surfaced/spoken immediately, regardless of the routine polling cadence.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_critical(props: dict[str, Any]) -> bool:  # info: def is_critical
    """True for anything that should be surfaced/spoken immediately,
    regardless of the routine polling cadence."""
    event = (props.get("event") or "").strip().lower()  # info: set event
    if event in _ALWAYS_CRITICAL_EVENTS:  # info: if event in _ALWAYS_CRITICAL_EVENTS :
        return True  # info: return True
    return severity_rank(props) >= _SEVERITY_RANK["Severe"]  # info: return severity_rank ( props ) >= _SEVERITY_RANK [


# ====================================================
# SECTION: function is_routine
# What it does: is routine.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_routine(props: dict[str, Any]) -> bool:  # info: def is_routine
    return not is_critical(props)  # info: return not is_critical ( props )
