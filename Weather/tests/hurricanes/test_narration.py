"""Smoke tests for hurricanes/scripts/narration.py. No network, no disk."""
from __future__ import annotations

from hurricanes.scripts.narration import narrate, _ocean_region, _bearing_trend


def test_ocean_region_central_pacific():
    assert _ocean_region(-150) == "Central Pacific"
    assert _ocean_region(-180) == "Western Pacific"
    assert _ocean_region(-140) == "Central Pacific"


def test_ocean_region_eastern_pacific():
    assert _ocean_region(-100) == "Eastern Pacific"
    assert _ocean_region(-0.01) == "Eastern Pacific"


def test_ocean_region_western_pacific_negative_side():
    assert _ocean_region(-180) == "Western Pacific"
    assert _ocean_region(180) == "Western Pacific"


def test_ocean_region_western_pacific_positive_longitude_regression():
    # Regression: a storm at 170E (near Guam/Philippines) is genuinely
    # Western Pacific. Before this session's fix, any positive longitude
    # below 180 fell through to "Eastern Pacific".
    assert _ocean_region(170) == "Western Pacific"
    assert _ocean_region(120) == "Western Pacific"
    assert _ocean_region(0) == "Western Pacific"


def test_bearing_trend_needs_at_least_two_positions():
    assert _bearing_trend([]) == "movement not yet established"
    assert _bearing_trend([{"lat": 21.3, "lon": -157.8}]) == "movement not yet established"


def test_bearing_trend_toward_hawaii():
    positions = [
        {"lat": 25.0, "lon": -150.0},
        {"lat": 22.0, "lon": -156.0},  # closer to Hawaii reference point
    ]
    assert _bearing_trend(positions) == "moving toward Hawaii"


def test_bearing_trend_away_from_hawaii():
    positions = [
        {"lat": 22.0, "lon": -156.0},
        {"lat": 25.0, "lon": -150.0},  # farther from Hawaii reference point
    ]
    assert _bearing_trend(positions) == "moving away from Hawaii"


def test_bearing_trend_handles_malformed_positions():
    positions = [{"lat": "bad", "lon": -156.0}, {"lat": 22.0, "lon": -156.0}]
    assert _bearing_trend(positions) == "movement not yet established"


def test_narrate_with_no_positions():
    result = narrate({"storm_name": "Test Storm", "positions": []})
    assert result == "Test Storm: no position data on file yet."


def test_narrate_full_summary_contains_expected_pieces():
    track = {
        "storm_name": "Hurricane Test",
        "positions": [
            {"lat": 25.0, "lon": -150.0, "intensity": "90 kt", "classification": "Hurricane"},
            {"lat": 22.0, "lon": -156.0, "intensity": "100 kt", "classification": "Hurricane"},
        ],
    }
    result = narrate(track)
    assert "Hurricane Test" in result
    assert "Hurricane" in result
    assert "100 kt" in result
    assert "Central Pacific" in result
    assert "nautical miles from Hawaii" in result
    assert "moving toward Hawaii" in result


def test_narrate_missing_lat_lon_falls_back_gracefully():
    track = {"storm_name": "Ghost Storm", "positions": [{"intensity": "unknown"}]}
    result = narrate(track)
    assert "distance unknown" in result
    assert "unknown ocean region" in result
