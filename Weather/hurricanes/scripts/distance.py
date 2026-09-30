# ==============================================================================
# FILE: Weather/hurricanes/scripts/distance.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""The '800nmi from Hawaii = relevant' threshold logic, isolated per
weather_skill_architecture.md Section 5. Pure math -- no I/O, no network.
"""
from __future__ import annotations  # info: from __future__ import annotations

import math  # info: import math

# Honolulu, roughly central to the Hawaiian island chain -- used as the
# reference point for the relevance radius. Ported from the old system.
HAWAII_REFERENCE_LAT = 21.3069  # info: set HAWAII_REFERENCE_LAT
HAWAII_REFERENCE_LON = -157.8583  # info: set HAWAII_REFERENCE_LON

RELEVANCE_RADIUS_NMI = 800.0  # info: set RELEVANCE_RADIUS_NMI
EARTH_RADIUS_NMI = 3440.065  # mean Earth radius in nautical miles


# ====================================================
# SECTION: function great_circle_distance_nmi
# What it does: Haversine great-circle distance in nautical miles.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def great_circle_distance_nmi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:  # info: def great_circle_distance_nmi
    """Haversine great-circle distance in nautical miles."""  # info: """Haversine great-circle distance in nautical miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)  # info: phi1 , phi2 = math . radians (
    dphi = math.radians(lat2 - lat1)  # info: set dphi
    dlambda = math.radians(lon2 - lon1)  # info: set dlambda

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2  # info: set a
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # info: set c
    return EARTH_RADIUS_NMI * c  # info: return EARTH_RADIUS_NMI * c


# ====================================================
# SECTION: function distance_from_hawaii_nmi
# What it does: distance from hawaii nmi.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def distance_from_hawaii_nmi(lat: float, lon: float) -> float:  # info: def distance_from_hawaii_nmi
    return great_circle_distance_nmi(HAWAII_REFERENCE_LAT, HAWAII_REFERENCE_LON, lat, lon)  # info: return great_circle_distance_nmi ( HAWAII_REFERENCE_LAT , HAWAII_REFERENCE_LON , lat


# ====================================================
# SECTION: function is_within_relevance_radius
# What it does: is within relevance radius.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_within_relevance_radius(lat: float, lon: float) -> bool:  # info: def is_within_relevance_radius
    return distance_from_hawaii_nmi(lat, lon) <= RELEVANCE_RADIUS_NMI  # info: return distance_from_hawaii_nmi ( lat , lon ) <=


# ====================================================
# SECTION: function is_relevant
# What it does: Full relevance rule per references/sources.md: within 800nmi OR already carries a CPHC advisory number (NHC/CPHC has already judged it in-area, regardless of raw distance).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_relevant(*, lat: float, lon: float, has_cphc_advisory: bool) -> bool:  # info: def is_relevant
    """Full relevance rule per references/sources.md: within 800nmi OR
    already carries a CPHC advisory number (NHC/CPHC has already judged it
    in-area, regardless of raw distance).
    """
    if has_cphc_advisory:  # info: if has_cphc_advisory :
        return True  # info: return True
    return is_within_relevance_radius(lat, lon)  # info: return is_within_relevance_radius ( lat , lon )
