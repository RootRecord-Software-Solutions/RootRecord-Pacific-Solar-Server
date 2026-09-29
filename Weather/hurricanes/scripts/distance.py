"""The '800nmi from Hawaii = relevant' threshold logic, isolated per
weather_skill_architecture.md Section 5. Pure math -- no I/O, no network.
"""
from __future__ import annotations

import math

# Honolulu, roughly central to the Hawaiian island chain -- used as the
# reference point for the relevance radius. Ported from the old system.
HAWAII_REFERENCE_LAT = 21.3069
HAWAII_REFERENCE_LON = -157.8583

RELEVANCE_RADIUS_NMI = 800.0
EARTH_RADIUS_NMI = 3440.065  # mean Earth radius in nautical miles


def great_circle_distance_nmi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine great-circle distance in nautical miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_NMI * c


def distance_from_hawaii_nmi(lat: float, lon: float) -> float:
    return great_circle_distance_nmi(HAWAII_REFERENCE_LAT, HAWAII_REFERENCE_LON, lat, lon)


def is_within_relevance_radius(lat: float, lon: float) -> bool:
    return distance_from_hawaii_nmi(lat, lon) <= RELEVANCE_RADIUS_NMI


def is_relevant(*, lat: float, lon: float, has_cphc_advisory: bool) -> bool:
    """Full relevance rule per references/sources.md: within 800nmi OR
    already carries a CPHC advisory number (NHC/CPHC has already judged it
    in-area, regardless of raw distance).
    """
    if has_cphc_advisory:
        return True
    return is_within_relevance_radius(lat, lon)
