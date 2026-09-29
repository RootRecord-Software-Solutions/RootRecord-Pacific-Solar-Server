"""Smoke tests for hurricanes/scripts/distance.py. No network, no disk."""
from __future__ import annotations

from hurricanes.scripts.distance import (
    great_circle_distance_nmi,
    distance_from_hawaii_nmi,
    is_within_relevance_radius,
    is_relevant,
    HAWAII_REFERENCE_LAT,
    HAWAII_REFERENCE_LON,
    RELEVANCE_RADIUS_NMI,
)


def test_distance_from_a_point_to_itself_is_zero():
    d = great_circle_distance_nmi(21.3, -157.8, 21.3, -157.8)
    assert d < 1e-6


def test_distance_from_hawaii_reference_point_is_zero():
    d = distance_from_hawaii_nmi(HAWAII_REFERENCE_LAT, HAWAII_REFERENCE_LON)
    assert d < 1e-6


def test_known_antipodal_ish_distance_is_roughly_half_earth_circumference():
    # Point roughly on the opposite side of the globe from Honolulu.
    d = great_circle_distance_nmi(21.3069, -157.8583, -21.3069, 22.1417)
    # Half the great-circle circumference is pi * R.
    import math
    assert abs(d - math.pi * 3440.065) < 5


def test_point_just_inside_relevance_radius_is_within():
    # Roughly 1 degree of latitude south of Hawaii is ~60nmi -- well inside.
    assert is_within_relevance_radius(HAWAII_REFERENCE_LAT - 1, HAWAII_REFERENCE_LON) is True


def test_point_far_away_is_not_within_relevance_radius():
    # Antipodal-ish point is far beyond 800nmi.
    assert is_within_relevance_radius(-21.3069, 22.1417) is False


def test_is_relevant_true_when_within_radius_even_without_advisory():
    assert is_relevant(lat=HAWAII_REFERENCE_LAT, lon=HAWAII_REFERENCE_LON, has_cphc_advisory=False) is True


def test_is_relevant_true_when_advisory_present_even_if_far():
    assert is_relevant(lat=-21.3069, lon=22.1417, has_cphc_advisory=True) is True


def test_is_relevant_false_when_far_and_no_advisory():
    assert is_relevant(lat=-21.3069, lon=22.1417, has_cphc_advisory=False) is False


def test_relevance_radius_matches_documented_threshold():
    assert RELEVANCE_RADIUS_NMI == 800.0
