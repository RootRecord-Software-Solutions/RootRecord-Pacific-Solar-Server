# ==============================================================================
# FILE: Weather/alerts/dedupe.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Event+county dedupe, keep-newest-sent logic. NWS frequently reissues the
same alert (renewed/updated) under a new `id` -- this collapses those to one
entry per (event, county) so downstream reporting doesn't repeat itself.
"""
from __future__ import annotations  # info: from __future__ import annotations

from typing import Any  # info: from typing import Any

from alerts.county_map import county_keys_for_alert  # info: from alerts . county_map import county_keys_for_alert


# ====================================================
# SECTION: function _sent_time
# What it does:  sent time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _sent_time(props: dict[str, Any]) -> str:  # info: def _sent_time
    # ISO 8601 strings sort correctly as plain strings for this purpose.
    return props.get("sent") or props.get("effective") or ""  # info: return props . get ( "sent" ) or


# ====================================================
# SECTION: function dedupe_by_event_and_county
# What it does: Given a list of raw alert features (each with a `properties` dict), return one alert per (event, county) pair -- the most recently `sent` one wins. An alert covering multiple count
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def dedupe_by_event_and_county(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:  # info: def dedupe_by_event_and_county
    """Given a list of raw alert features (each with a `properties` dict),
    return one alert per (event, county) pair -- the most recently `sent`
    one wins. An alert covering multiple counties can still "win" for each
    of its counties independently.
    """
    best: dict[tuple[str, str], dict[str, Any]] = {}  # info: set best

    for alert in alerts:  # info: for alert in alerts :
        props = alert.get("properties", {})  # info: set props
        event = props.get("event", "Unknown")  # info: set event
        counties = county_keys_for_alert(props) or {"_unmapped"}  # info: set counties
        sent = _sent_time(props)  # info: set sent

        for county in counties:  # info: for county in counties :
            key = (event, county)  # info: set key
            current_best = best.get(key)  # info: set current_best
            if current_best is None or _sent_time(current_best.get("properties", {})) < sent:  # info: if current_best is None or _sent_time ( current_best
                best[key] = alert  # info: best [ key ] = alert

    # Preserve a stable, de-duplicated list (each unique alert object appears
    # once even if it won for multiple counties).
    seen_ids = set()  # info: set seen_ids
    result = []  # info: set result
    for alert in best.values():  # info: for alert in best . values ( )
        alert_id = alert.get("id") or id(alert)  # info: set alert_id
        if alert_id not in seen_ids:  # info: if alert_id not in seen_ids :
            seen_ids.add(alert_id)  # info: seen_ids . add ( alert_id )
            result.append(alert)  # info: result . append ( alert )
    return result  # info: return result


# ====================================================
# SECTION: function by_county
# What it does: Event names grouped by county key, after dedupe.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def by_county(alerts: list[dict[str, Any]]) -> dict[str, list[str]]:  # info: def by_county
    """Event names grouped by county key, after dedupe."""  # info: """Event names grouped by county key, after dedupe."""
    deduped = dedupe_by_event_and_county(alerts)  # info: set deduped
    grouped: dict[str, list[str]] = {}  # info: set grouped
    for alert in deduped:  # info: for alert in deduped :
        props = alert.get("properties", {})  # info: set props
        event = props.get("event", "Unknown")  # info: set event
        for county in county_keys_for_alert(props):  # info: for county in county_keys_for_alert ( props ) :
            grouped.setdefault(county, []).append(event)  # info: grouped . setdefault ( county , [ ]
    return grouped  # info: return grouped
