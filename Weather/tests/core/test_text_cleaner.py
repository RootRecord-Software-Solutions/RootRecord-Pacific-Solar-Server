"""Smoke tests for core/text_cleaner.py against nws_plan.md Section 4."""
from __future__ import annotations

from core.text_cleaner import clean_text, clean_json_text_fields


def test_strips_segment_markers():
    raw = "HAWAII STATE FOREST\nFORECAST TEXT HERE\n$$\n"
    cleaned = clean_text(raw)
    assert "$$" not in cleaned
    assert "FORECAST TEXT HERE" in cleaned


def test_collapses_blank_lines_left_by_stripped_markers():
    raw = "line one\n$$\n\n\nline two\n"
    cleaned = clean_text(raw)
    assert "\n\n\n\n" not in cleaned


def test_json_text_fields_cleaned_structured_fields_untouched():
    obj = {
        "id": "urn:nws:1$2",  # not a text field -- must survive untouched
        "properties": {
            "description": "Winds up to 40 mph.$$",
            "effective": "2026-09-24T04:00:00-10:00",
        },
    }
    cleaned = clean_json_text_fields(obj)
    assert cleaned["id"] == "urn:nws:1$2"
    assert "$$" not in cleaned["properties"]["description"]
    assert cleaned["properties"]["effective"] == "2026-09-24T04:00:00-10:00"


def test_json_list_of_features_geojson_shape():
    obj = {"features": [{"properties": {"headline": "Flood Watch&&", "id": "abc&123"}}]}
    cleaned = clean_json_text_fields(obj)
    assert "&&" not in cleaned["features"][0]["properties"]["headline"]
    # "id" is not in the json_text_fields allowlist -- left alone.
    assert cleaned["features"][0]["properties"]["id"] == "abc&123"
