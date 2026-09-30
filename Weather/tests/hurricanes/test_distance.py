# ==============================================================================
# FILE: Weather/tests/hurricanes/test_distance.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for hurricanes/scripts/distance.py. No network, no disk."""  # info: """Smoke tests for hurricanes/scripts/distance.py. No network, no disk."""
from __future__ import annotations  # info: from __future__ import annotations

from hurricanes.scripts.distance import (  # info: from hurricanes . scripts . distance import (
    great_circle_distance_nmi,  # info: great_circle_distance_nmi ,
    distance_from_hawaii_nmi,  # info: distance_from_hawaii_nmi ,
    is_within_relevance_radius,  # info: is_within_relevance_radius ,
    is_relevant,  # info: is_relevant ,
    HAWAII_REFERENCE_LAT,  # info: HAWAII_REFERENCE_LAT ,
    HAWAII_REFERENCE_LON,  # info: HAWAII_REFERENCE_LON ,
    RELEVANCE_RADIUS_NMI,  # info: RELEVANCE_RADIUS_NMI ,
)  # info: )


# ====================================================
# SECTION: function test_distance_from_a_point_to_itself_is_zero
# What it does: test distance from a point to itself is zero.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_distance_from_a_point_to_itself_is_zero():  # info: def test_distance_from_a_point_to_itself_is_zero
    d = great_circle_distance_nmi(21.3, -157.8, 21.3, -157.8)  # info: set d
    assert d < 1e-6  # info: assert d < 1e-6


# ====================================================
# SECTION: function test_distance_from_hawaii_reference_point_is_zero
# What it does: test distance from hawaii reference point is zero.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_distance_from_hawaii_reference_point_is_zero():  # info: def test_distance_from_hawaii_reference_point_is_zero
    d = distance_from_hawaii_nmi(HAWAII_REFERENCE_LAT, HAWAII_REFERENCE_LON)  # info: set d
    assert d < 1e-6  # info: assert d < 1e-6


# ====================================================
# SECTION: function test_known_antipodal_ish_distance_is_roughly_half_earth_circumference
# What it does: test known antipodal ish distance is roughly half earth circumference.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_known_antipodal_ish_distance_is_roughly_half_earth_circumference():  # info: def test_known_antipodal_ish_distance_is_roughly_half_earth_circumference
    # Point roughly on the opposite side of the globe from Honolulu.
    d = great_circle_distance_nmi(21.3069, -157.8583, -21.3069, 22.1417)  # info: set d
    # Half the great-circle circumference is pi * R.
    import math  # info: import math
    assert abs(d - math.pi * 3440.065) < 5  # info: assert abs ( d - math . pi


# ====================================================
# SECTION: function test_point_just_inside_relevance_radius_is_within
# What it does: test point just inside relevance radius is within.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_point_just_inside_relevance_radius_is_within():  # info: def test_point_just_inside_relevance_radius_is_within
    # Roughly 1 degree of latitude south of Hawaii is ~60nmi -- well inside.
    assert is_within_relevance_radius(HAWAII_REFERENCE_LAT - 1, HAWAII_REFERENCE_LON) is True  # info: assert is_within_relevance_radius ( HAWAII_REFERENCE_LAT - 1 , HAWAII_REFERENCE_LON


# ====================================================
# SECTION: function test_point_far_away_is_not_within_relevance_radius
# What it does: test point far away is not within relevance radius.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_point_far_away_is_not_within_relevance_radius():  # info: def test_point_far_away_is_not_within_relevance_radius
    # Antipodal-ish point is far beyond 800nmi.
    assert is_within_relevance_radius(-21.3069, 22.1417) is False  # info: assert is_within_relevance_radius ( - 21.3069 , 22.1417 )


# ====================================================
# SECTION: function test_is_relevant_true_when_within_radius_even_without_advisory
# What it does: test is relevant true when within radius even without advisory.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_is_relevant_true_when_within_radius_even_without_advisory():  # info: def test_is_relevant_true_when_within_radius_even_without_advisory
    assert is_relevant(lat=HAWAII_REFERENCE_LAT, lon=HAWAII_REFERENCE_LON, has_cphc_advisory=False) is True  # info: assert is_relevant ( lat = HAWAII_REFERENCE_LAT , lon


# ====================================================
# SECTION: function test_is_relevant_true_when_advisory_present_even_if_far
# What it does: test is relevant true when advisory present even if far.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_is_relevant_true_when_advisory_present_even_if_far():  # info: def test_is_relevant_true_when_advisory_present_even_if_far
    assert is_relevant(lat=-21.3069, lon=22.1417, has_cphc_advisory=True) is True  # info: assert is_relevant ( lat = - 21.3069 ,


# ====================================================
# SECTION: function test_is_relevant_false_when_far_and_no_advisory
# What it does: test is relevant false when far and no advisory.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_is_relevant_false_when_far_and_no_advisory():  # info: def test_is_relevant_false_when_far_and_no_advisory
    assert is_relevant(lat=-21.3069, lon=22.1417, has_cphc_advisory=False) is False  # info: assert is_relevant ( lat = - 21.3069 ,


# ====================================================
# SECTION: function test_relevance_radius_matches_documented_threshold
# What it does: test relevance radius matches documented threshold.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_relevance_radius_matches_documented_threshold():  # info: def test_relevance_radius_matches_documented_threshold
    assert RELEVANCE_RADIUS_NMI == 800.0  # info: assert RELEVANCE_RADIUS_NMI == 800.0
