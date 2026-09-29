"""Smoke tests for alerts/dedupe.py."""
from __future__ import annotations

from alerts.dedupe import dedupe_by_event_and_county, by_county


def _alert(id_, event, same, sent):
    return {"id": id_, "properties": {
        "event": event, "geocode": {"SAME": [same]}, "sent": sent, "areaDesc": "",
    }}


def test_keeps_newest_sent_for_same_event_and_county():
    alerts = [
        _alert("a1", "Flood Watch", "015003", "2026-09-24T01:00:00-10:00"),
        _alert("a2", "Flood Watch", "015003", "2026-09-24T03:00:00-10:00"),  # reissued, newer
    ]
    result = dedupe_by_event_and_county(alerts)
    assert len(result) == 1
    assert result[0]["id"] == "a2"


def test_different_counties_both_survive():
    alerts = [
        _alert("a1", "High Surf Advisory", "015003", "2026-09-24T01:00:00-10:00"),  # honolulu
        _alert("a2", "High Surf Advisory", "015007", "2026-09-24T01:00:00-10:00"),  # kauai
    ]
    result = dedupe_by_event_and_county(alerts)
    assert len(result) == 2


def test_by_county_groups_after_dedupe():
    alerts = [_alert("a1", "Flood Watch", "015003", "2026-09-24T01:00:00-10:00")]
    grouped = by_county(alerts)
    assert grouped == {"honolulu": ["Flood Watch"]}
