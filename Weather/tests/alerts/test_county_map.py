"""Smoke tests for alerts/county_map.py against config/counties.yaml."""
from __future__ import annotations

from alerts.county_map import county_keys_for_alert, speech_name, speech_order


def test_same_geocode_is_authoritative():
    props = {"geocode": {"SAME": ["015003"]}, "areaDesc": "irrelevant text"}
    assert county_keys_for_alert(props) == {"honolulu"}


def test_multiple_same_codes():
    props = {"geocode": {"SAME": ["015003", "015009"]}, "areaDesc": ""}
    assert county_keys_for_alert(props) == {"honolulu", "maui"}


def test_falls_back_to_area_text_when_no_geocode():
    props = {"geocode": {}, "areaDesc": "Kona and Hilo districts"}
    assert county_keys_for_alert(props) == {"hawaii"}


def test_no_match_returns_empty_set():
    props = {"geocode": {}, "areaDesc": "Nothing recognizable here"}
    assert county_keys_for_alert(props) == set()


def test_speech_name_and_order():
    assert speech_name("kauai") == "Kauai County"
    order = speech_order()
    assert order.index("honolulu") < order.index("kalawao")
