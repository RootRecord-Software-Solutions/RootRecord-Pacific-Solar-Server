# ==============================================================================
# FILE: Weather/tests/alerts/test_county_map.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for alerts/county_map.py against config/counties.yaml."""  # info: """Smoke tests for alerts/county_map.py against config/counties.yaml."""
from __future__ import annotations  # info: from __future__ import annotations

from alerts.county_map import county_keys_for_alert, speech_name, speech_order  # info: from alerts . county_map import county_keys_for_alert , speech_name


# ====================================================
# SECTION: function test_same_geocode_is_authoritative
# What it does: test same geocode is authoritative.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_same_geocode_is_authoritative():  # info: def test_same_geocode_is_authoritative
    props = {"geocode": {"SAME": ["015003"]}, "areaDesc": "irrelevant text"}  # info: set props
    assert county_keys_for_alert(props) == {"honolulu"}  # info: assert county_keys_for_alert ( props ) == { "honolulu"


# ====================================================
# SECTION: function test_multiple_same_codes
# What it does: test multiple same codes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_multiple_same_codes():  # info: def test_multiple_same_codes
    props = {"geocode": {"SAME": ["015003", "015009"]}, "areaDesc": ""}  # info: set props
    assert county_keys_for_alert(props) == {"honolulu", "maui"}  # info: assert county_keys_for_alert ( props ) == { "honolulu"


# ====================================================
# SECTION: function test_falls_back_to_area_text_when_no_geocode
# What it does: test falls back to area text when no geocode.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_falls_back_to_area_text_when_no_geocode():  # info: def test_falls_back_to_area_text_when_no_geocode
    props = {"geocode": {}, "areaDesc": "Kona and Hilo districts"}  # info: set props
    assert county_keys_for_alert(props) == {"hawaii"}  # info: assert county_keys_for_alert ( props ) == { "hawaii"


# ====================================================
# SECTION: function test_no_match_returns_empty_set
# What it does: test no match returns empty set.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_no_match_returns_empty_set():  # info: def test_no_match_returns_empty_set
    props = {"geocode": {}, "areaDesc": "Nothing recognizable here"}  # info: set props
    assert county_keys_for_alert(props) == set()  # info: assert county_keys_for_alert ( props ) == set (


# ====================================================
# SECTION: function test_speech_name_and_order
# What it does: test speech name and order.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_speech_name_and_order():  # info: def test_speech_name_and_order
    assert speech_name("kauai") == "Kauai County"  # info: assert speech_name ( "kauai" ) == "Kauai County"
    order = speech_order()  # info: set order
    assert order.index("honolulu") < order.index("kalawao")  # info: assert order . index ( "honolulu" ) <
