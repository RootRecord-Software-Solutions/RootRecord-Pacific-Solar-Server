# ==============================================================================
# FILE: Weather/tests/alerts/test_severity.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for alerts/severity.py."""  # info: """Smoke tests for alerts/severity.py."""
from __future__ import annotations  # info: from __future__ import annotations

from alerts.severity import severity_rank, is_critical, is_routine  # info: from alerts . severity import severity_rank , is_critical


# ====================================================
# SECTION: function test_extreme_outranks_moderate
# What it does: test extreme outranks moderate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_extreme_outranks_moderate():  # info: def test_extreme_outranks_moderate
    assert severity_rank({"severity": "Extreme"}) > severity_rank({"severity": "Moderate"})  # info: assert severity_rank ( { "severity" : "Extreme" }


# ====================================================
# SECTION: function test_tornado_warning_always_critical_even_if_severity_missing
# What it does: test tornado warning always critical even if severity missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_tornado_warning_always_critical_even_if_severity_missing():  # info: def test_tornado_warning_always_critical_even_if_severity_missing
    props = {"event": "Tornado Warning"}  # info: set props
    assert is_critical(props) is True  # info: assert is_critical ( props ) is True
    assert is_routine(props) is False  # info: assert is_routine ( props ) is False


# ====================================================
# SECTION: function test_severe_or_worse_is_critical
# What it does: test severe or worse is critical.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_severe_or_worse_is_critical():  # info: def test_severe_or_worse_is_critical
    assert is_critical({"event": "Flood Advisory", "severity": "Severe"}) is True  # info: assert is_critical ( { "event" : "Flood Advisory" ,


# ====================================================
# SECTION: function test_minor_advisory_is_routine
# What it does: test minor advisory is routine.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_minor_advisory_is_routine():  # info: def test_minor_advisory_is_routine
    assert is_routine({"event": "Small Craft Advisory", "severity": "Minor"}) is True  # info: assert is_routine ( { "event" : "Small Craft Advisory" ,
