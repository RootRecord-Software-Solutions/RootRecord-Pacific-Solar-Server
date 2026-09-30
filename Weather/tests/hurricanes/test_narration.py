# ==============================================================================
# FILE: Weather/tests/hurricanes/test_narration.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for hurricanes/scripts/narration.py. No network, no disk."""  # info: """Smoke tests for hurricanes/scripts/narration.py. No network, no disk."""
from __future__ import annotations  # info: from __future__ import annotations

from hurricanes.scripts.narration import narrate, _ocean_region, _bearing_trend  # info: from hurricanes . scripts . narration import narrate


# ====================================================
# SECTION: function test_ocean_region_central_pacific
# What it does: test ocean region central pacific.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_ocean_region_central_pacific():  # info: def test_ocean_region_central_pacific
    assert _ocean_region(-150) == "Central Pacific"  # info: assert _ocean_region ( - 150 ) == "Central Pacific"
    assert _ocean_region(-180) == "Western Pacific"  # info: assert _ocean_region ( - 180 ) == "Western Pacific"
    assert _ocean_region(-140) == "Central Pacific"  # info: assert _ocean_region ( - 140 ) == "Central Pacific"


# ====================================================
# SECTION: function test_ocean_region_eastern_pacific
# What it does: test ocean region eastern pacific.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_ocean_region_eastern_pacific():  # info: def test_ocean_region_eastern_pacific
    assert _ocean_region(-100) == "Eastern Pacific"  # info: assert _ocean_region ( - 100 ) == "Eastern Pacific"
    assert _ocean_region(-0.01) == "Eastern Pacific"  # info: assert _ocean_region ( - 0.01 ) == "Eastern Pacific"


# ====================================================
# SECTION: function test_ocean_region_western_pacific_negative_side
# What it does: test ocean region western pacific negative side.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_ocean_region_western_pacific_negative_side():  # info: def test_ocean_region_western_pacific_negative_side
    assert _ocean_region(-180) == "Western Pacific"  # info: assert _ocean_region ( - 180 ) == "Western Pacific"
    assert _ocean_region(180) == "Western Pacific"  # info: assert _ocean_region ( 180 ) == "Western Pacific"


# ====================================================
# SECTION: function test_ocean_region_western_pacific_positive_longitude_regression
# What it does: test ocean region western pacific positive longitude regression.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_ocean_region_western_pacific_positive_longitude_regression():  # info: def test_ocean_region_western_pacific_positive_longitude_regression
    # Regression: a storm at 170E (near Guam/Philippines) is genuinely
    # Western Pacific. Before this session's fix, any positive longitude
    # below 180 fell through to "Eastern Pacific".
    assert _ocean_region(170) == "Western Pacific"  # info: assert _ocean_region ( 170 ) == "Western Pacific"
    assert _ocean_region(120) == "Western Pacific"  # info: assert _ocean_region ( 120 ) == "Western Pacific"
    assert _ocean_region(0) == "Western Pacific"  # info: assert _ocean_region ( 0 ) == "Western Pacific"


# ====================================================
# SECTION: function test_bearing_trend_needs_at_least_two_positions
# What it does: test bearing trend needs at least two positions.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_bearing_trend_needs_at_least_two_positions():  # info: def test_bearing_trend_needs_at_least_two_positions
    assert _bearing_trend([]) == "movement not yet established"  # info: assert _bearing_trend ( [ ] ) == "movement not yet established"
    assert _bearing_trend([{"lat": 21.3, "lon": -157.8}]) == "movement not yet established"  # info: assert _bearing_trend ( [ { "lat" : 21.3


# ====================================================
# SECTION: function test_bearing_trend_toward_hawaii
# What it does: test bearing trend toward hawaii.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_bearing_trend_toward_hawaii():  # info: def test_bearing_trend_toward_hawaii
    positions = [  # info: set positions
        {"lat": 25.0, "lon": -150.0},  # info: { "lat" : 25.0 , "lon" : -
        {"lat": 22.0, "lon": -156.0},  # closer to Hawaii reference point
    ]  # info: ]
    assert _bearing_trend(positions) == "moving toward Hawaii"  # info: assert _bearing_trend ( positions ) == "moving toward Hawaii"


# ====================================================
# SECTION: function test_bearing_trend_away_from_hawaii
# What it does: test bearing trend away from hawaii.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_bearing_trend_away_from_hawaii():  # info: def test_bearing_trend_away_from_hawaii
    positions = [  # info: set positions
        {"lat": 22.0, "lon": -156.0},  # info: { "lat" : 22.0 , "lon" : -
        {"lat": 25.0, "lon": -150.0},  # farther from Hawaii reference point
    ]  # info: ]
    assert _bearing_trend(positions) == "moving away from Hawaii"  # info: assert _bearing_trend ( positions ) == "moving away from Hawaii"


# ====================================================
# SECTION: function test_bearing_trend_handles_malformed_positions
# What it does: test bearing trend handles malformed positions.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_bearing_trend_handles_malformed_positions():  # info: def test_bearing_trend_handles_malformed_positions
    positions = [{"lat": "bad", "lon": -156.0}, {"lat": 22.0, "lon": -156.0}]  # info: set positions
    assert _bearing_trend(positions) == "movement not yet established"  # info: assert _bearing_trend ( positions ) == "movement not yet established"


# ====================================================
# SECTION: function test_narrate_with_no_positions
# What it does: test narrate with no positions.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_narrate_with_no_positions():  # info: def test_narrate_with_no_positions
    result = narrate({"storm_name": "Test Storm", "positions": []})  # info: set result
    assert result == "Test Storm: no position data on file yet."  # info: assert result == "Test Storm: no position data on file yet."


# ====================================================
# SECTION: function test_narrate_full_summary_contains_expected_pieces
# What it does: test narrate full summary contains expected pieces.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_narrate_full_summary_contains_expected_pieces():  # info: def test_narrate_full_summary_contains_expected_pieces
    track = {  # info: set track
        "storm_name": "Hurricane Test",  # info: "storm_name" : "Hurricane Test" ,
        "positions": [  # info: "positions" : [
            {"lat": 25.0, "lon": -150.0, "intensity": "90 kt", "classification": "Hurricane"},  # info: { "lat" : 25.0 , "lon" : -
            {"lat": 22.0, "lon": -156.0, "intensity": "100 kt", "classification": "Hurricane"},  # info: { "lat" : 22.0 , "lon" : -
        ],  # info: ] ,
    }  # info: }
    result = narrate(track)  # info: set result
    assert "Hurricane Test" in result  # info: assert "Hurricane Test" in result
    assert "Hurricane" in result  # info: assert "Hurricane" in result
    assert "100 kt" in result  # info: assert "100 kt" in result
    assert "Central Pacific" in result  # info: assert "Central Pacific" in result
    assert "nautical miles from Hawaii" in result  # info: assert "nautical miles from Hawaii" in result
    assert "moving toward Hawaii" in result  # info: assert "moving toward Hawaii" in result


# ====================================================
# SECTION: function test_narrate_missing_lat_lon_falls_back_gracefully
# What it does: test narrate missing lat lon falls back gracefully.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_narrate_missing_lat_lon_falls_back_gracefully():  # info: def test_narrate_missing_lat_lon_falls_back_gracefully
    track = {"storm_name": "Ghost Storm", "positions": [{"intensity": "unknown"}]}  # info: set track
    result = narrate(track)  # info: set result
    assert "distance unknown" in result  # info: assert "distance unknown" in result
    assert "unknown ocean region" in result  # info: assert "unknown ocean region" in result
