# ==============================================================================
# FILE: Weather/tests/core/test_text_cleaner.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for core/text_cleaner.py against nws_plan.md Section 4."""  # info: """Smoke tests for core/text_cleaner.py against nws_plan.md Section 4."""
from __future__ import annotations  # info: from __future__ import annotations

from core.text_cleaner import clean_text, clean_json_text_fields  # info: from core . text_cleaner import clean_text , clean_json_text_fields


# ====================================================
# SECTION: function test_strips_segment_markers
# What it does: test strips segment markers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_strips_segment_markers():  # info: def test_strips_segment_markers
    raw = "HAWAII STATE FOREST\nFORECAST TEXT HERE\n$$\n"  # info: set raw
    cleaned = clean_text(raw)  # info: set cleaned
    assert "$$" not in cleaned  # info: assert "$$" not in cleaned
    assert "FORECAST TEXT HERE" in cleaned  # info: assert "FORECAST TEXT HERE" in cleaned


# ====================================================
# SECTION: function test_collapses_blank_lines_left_by_stripped_markers
# What it does: test collapses blank lines left by stripped markers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_collapses_blank_lines_left_by_stripped_markers():  # info: def test_collapses_blank_lines_left_by_stripped_markers
    raw = "line one\n$$\n\n\nline two\n"  # info: set raw
    cleaned = clean_text(raw)  # info: set cleaned
    assert "\n\n\n\n" not in cleaned  # info: assert "\n\n\n\n" not in cleaned


# ====================================================
# SECTION: function test_json_text_fields_cleaned_structured_fields_untouched
# What it does: test json text fields cleaned structured fields untouched.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_json_text_fields_cleaned_structured_fields_untouched():  # info: def test_json_text_fields_cleaned_structured_fields_untouched
    obj = {  # info: set obj
        "id": "urn:nws:1$2",  # not a text field -- must survive untouched
        "properties": {  # info: "properties" : {
            "description": "Winds up to 40 mph.$$",  # info: "description" : "Winds up to 40 mph.$$" ,
            "effective": "2026-09-24T04:00:00-10:00",  # info: "effective" : "2026-09-24T04:00:00-10:00" ,
        },  # info: } ,
    }  # info: }
    cleaned = clean_json_text_fields(obj)  # info: set cleaned
    assert cleaned["id"] == "urn:nws:1$2"  # info: assert cleaned [ "id" ] == "urn:nws:1$2"
    assert "$$" not in cleaned["properties"]["description"]  # info: assert "$$" not in cleaned [ "properties" ]
    assert cleaned["properties"]["effective"] == "2026-09-24T04:00:00-10:00"  # info: assert cleaned [ "properties" ] [ "effective" ]


# ====================================================
# SECTION: function test_json_list_of_features_geojson_shape
# What it does: test json list of features geojson shape.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_json_list_of_features_geojson_shape():  # info: def test_json_list_of_features_geojson_shape
    obj = {"features": [{"properties": {"headline": "Flood Watch&&", "id": "abc&123"}}]}  # info: set obj
    cleaned = clean_json_text_fields(obj)  # info: set cleaned
    assert "&&" not in cleaned["features"][0]["properties"]["headline"]  # info: assert "&&" not in cleaned [ "features" ]
    # "id" is not in the json_text_fields allowlist -- left alone.
    assert cleaned["features"][0]["properties"]["id"] == "abc&123"  # info: assert cleaned [ "features" ] [ 0 ]
