"""Builds the plain-language 'toward/away, lat/lon, ocean region' summary.
Text only, no I/O -- takes track data in, returns a string out. Ported
concept from the old system's narration approach.
"""
from __future__ import annotations

from typing import Any

from hurricanes.scripts.distance import distance_from_hawaii_nmi


def _ocean_region(lon: float) -> str:
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
    if lon >= 180 or lon <= -180:
        return "Western Pacific"
    if lon <= -140:
        return "Central Pacific"
    if lon < 0:
        return "Eastern Pacific"
    return "Western Pacific"  # 0 <= lon < 180


def _bearing_trend(positions: list[dict[str, Any]]) -> str:
    """Toward or away from Hawaii, based on the last two polled positions."""
    if len(positions) < 2:
        return "movement not yet established"
    prev, latest = positions[-2], positions[-1]
    try:
        prev_dist = distance_from_hawaii_nmi(float(prev["lat"]), float(prev["lon"]))
        latest_dist = distance_from_hawaii_nmi(float(latest["lat"]), float(latest["lon"]))
    except (TypeError, ValueError, KeyError):
        return "movement not yet established"

    if latest_dist < prev_dist - 5:
        return "moving toward Hawaii"
    if latest_dist > prev_dist + 5:
        return "moving away from Hawaii"
    return "holding roughly steady relative to Hawaii"


def narrate(track: dict[str, Any]) -> str:
    """Builds a one-paragraph plain-language summary from a storm's
    track.json contents (as loaded by hurricanes/scripts/sources.py).
    """
    storm_name = track.get("storm_name", "Unnamed system")
    positions = track.get("positions", [])
    if not positions:
        return f"{storm_name}: no position data on file yet."

    latest = positions[-1]
    lat, lon = latest.get("lat"), latest.get("lon")
    intensity = latest.get("intensity", "intensity unknown")
    classification = latest.get("classification", "unclassified system")
    region = _ocean_region(float(lon)) if lon is not None else "unknown ocean region"
    distance = f"{distance_from_hawaii_nmi(float(lat), float(lon)):.0f} nautical miles from Hawaii" \
        if lat is not None and lon is not None else "distance unknown"
    trend = _bearing_trend(positions)

    return (
        f"{storm_name} ({classification}, {intensity}) is in the {region}, "
        f"currently {distance}, {trend}."
    )
