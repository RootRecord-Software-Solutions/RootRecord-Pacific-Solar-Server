# ==============================================================================
# FILE: Weather/tests/alerts/test_dedupe.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for alerts/dedupe.py."""  # info: """Smoke tests for alerts/dedupe.py."""
from __future__ import annotations  # info: from __future__ import annotations

from alerts.dedupe import dedupe_by_event_and_county, by_county  # info: from alerts . dedupe import dedupe_by_event_and_county , by_county


# ====================================================
# SECTION: function _alert
# What it does:  alert.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _alert(id_, event, same, sent):  # info: def _alert
    return {"id": id_, "properties": {  # info: return { "id" : id_ , "properties" :
        "event": event, "geocode": {"SAME": [same]}, "sent": sent, "areaDesc": "",  # info: "event" : event , "geocode" : { "SAME"
    }}  # info: } }


# ====================================================
# SECTION: function test_keeps_newest_sent_for_same_event_and_county
# What it does: test keeps newest sent for same event and county.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_keeps_newest_sent_for_same_event_and_county():  # info: def test_keeps_newest_sent_for_same_event_and_county
    alerts = [  # info: set alerts
        _alert("a1", "Flood Watch", "015003", "2026-09-24T01:00:00-10:00"),  # info: call _alert
        _alert("a2", "Flood Watch", "015003", "2026-09-24T03:00:00-10:00"),  # reissued, newer
    ]  # info: ]
    result = dedupe_by_event_and_county(alerts)  # info: set result
    assert len(result) == 1  # info: assert len ( result ) == 1
    assert result[0]["id"] == "a2"  # info: assert result [ 0 ] [ "id" ]


# ====================================================
# SECTION: function test_different_counties_both_survive
# What it does: test different counties both survive.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_different_counties_both_survive():  # info: def test_different_counties_both_survive
    alerts = [  # info: set alerts
        _alert("a1", "High Surf Advisory", "015003", "2026-09-24T01:00:00-10:00"),  # honolulu
        _alert("a2", "High Surf Advisory", "015007", "2026-09-24T01:00:00-10:00"),  # kauai
    ]  # info: ]
    result = dedupe_by_event_and_county(alerts)  # info: set result
    assert len(result) == 2  # info: assert len ( result ) == 2


# ====================================================
# SECTION: function test_by_county_groups_after_dedupe
# What it does: test by county groups after dedupe.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_by_county_groups_after_dedupe():  # info: def test_by_county_groups_after_dedupe
    alerts = [_alert("a1", "Flood Watch", "015003", "2026-09-24T01:00:00-10:00")]  # info: set alerts
    grouped = by_county(alerts)  # info: set grouped
    assert grouped == {"honolulu": ["Flood Watch"]}  # info: assert grouped == { "honolulu" : [ "Flood Watch"
