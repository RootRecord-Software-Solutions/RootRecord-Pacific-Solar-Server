# ==============================================================================
# FILE: Weather/hurricanes/scripts/narration.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Builds the plain-language 'toward/away, lat/lon, ocean region' summary.
Text only, no I/O -- takes track data in, returns a string out. Ported
concept from the old system's narration approach.
"""
from __future__ import annotations  # info: from __future__ import annotations

from typing import Any  # info: from typing import Any

from hurricanes.scripts.distance import distance_from_hawaii_nmi  # info: from hurricanes . scripts . distance import distance_from_hawaii_nmi


# ====================================================
# SECTION: function _ocean_region
# What it does:  ocean region.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ocean_region(lon: float) -> str:  # info: def _ocean_region
    # Central Pacific (CPHC) is roughly 140W-180; west of 180 (i.e. the
    # positive-longitude side of the dateline, e.g. 170) is Western Pacific
    # (JTWC territory); east of 140W (toward the Americas) is Eastern
    # Pacific (NHC).
    #
    # BUGFIX (this session): the original version only ever matched
    # lon <= -180 for "Western Pacific" and fell through to "Eastern
    # Pacific" for ALL positive longitudes below 180 -- so a storm at e.g.
    # 170 (genuinely Western Pacific, near Guam/Philippines) was mislabeled
    # Eastern Pacific. Positive longitudes now correctly route to Western
    # Pacific. See tests/hurricanes/test_narration.py for the regression
    # case.
    if lon >= 180 or lon <= -180:  # info: if lon >= 180 or lon <= -
        return "Western Pacific"  # info: return "Western Pacific"
    if lon <= -140:  # info: if lon <= - 140 :
        return "Central Pacific"  # info: return "Central Pacific"
    if lon < 0:  # info: if lon < 0 :
        return "Eastern Pacific"  # info: return "Eastern Pacific"
    return "Western Pacific"  # 0 <= lon < 180


# ====================================================
# SECTION: function _bearing_trend
# What it does: Toward or away from Hawaii, based on the last two polled positions.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _bearing_trend(positions: list[dict[str, Any]]) -> str:  # info: def _bearing_trend
    """Toward or away from Hawaii, based on the last two polled positions."""  # info: """Toward or away from Hawaii, based on the last two polled positions."""
    if len(positions) < 2:  # info: if len ( positions ) < 2 :
        return "movement not yet established"  # info: return "movement not yet established"
    prev, latest = positions[-2], positions[-1]  # info: prev , latest = positions [ - 2
    try:  # info: try :
        prev_dist = distance_from_hawaii_nmi(float(prev["lat"]), float(prev["lon"]))  # info: set prev_dist
        latest_dist = distance_from_hawaii_nmi(float(latest["lat"]), float(latest["lon"]))  # info: set latest_dist
    except (TypeError, ValueError, KeyError):  # info: except ( TypeError , ValueError , KeyError )
        return "movement not yet established"  # info: return "movement not yet established"

    if latest_dist < prev_dist - 5:  # info: if latest_dist < prev_dist - 5 :
        return "moving toward Hawaii"  # info: return "moving toward Hawaii"
    if latest_dist > prev_dist + 5:  # info: if latest_dist > prev_dist + 5 :
        return "moving away from Hawaii"  # info: return "moving away from Hawaii"
    return "holding roughly steady relative to Hawaii"  # info: return "holding roughly steady relative to Hawaii"


# ====================================================
# SECTION: function narrate
# What it does: Builds a one-paragraph plain-language summary from a storm's track.json contents (as loaded by hurricanes/scripts/sources.py).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def narrate(track: dict[str, Any]) -> str:  # info: def narrate
    """Builds a one-paragraph plain-language summary from a storm's
    track.json contents (as loaded by hurricanes/scripts/sources.py).
    """
    storm_name = track.get("storm_name", "Unnamed system")  # info: set storm_name
    positions = track.get("positions", [])  # info: set positions
    if not positions:  # info: if not positions :
        return f"{storm_name}: no position data on file yet."  # info: return f" { storm_name } : no position data on file yet. "

    latest = positions[-1]  # info: set latest
    lat, lon = latest.get("lat"), latest.get("lon")  # info: lat , lon = latest . get (
    intensity = latest.get("intensity", "intensity unknown")  # info: set intensity
    classification = latest.get("classification", "unclassified system")  # info: set classification
    region = _ocean_region(float(lon)) if lon is not None else "unknown ocean region"  # info: set region
    distance = f"{distance_from_hawaii_nmi(float(lat), float(lon)):.0f} nautical miles from Hawaii" \
        if lat is not None and lon is not None else "distance unknown"  # info: if lat is not None and lon is
    trend = _bearing_trend(positions)  # info: set trend

    return (  # info: return (
        f"{storm_name} ({classification}, {intensity}) is in the {region}, "  # info: f" { storm_name } ( { classification }
        f"currently {distance}, {trend}."  # info: f" currently { distance } , { trend
    )  # info: )
