"""Smoke tests for alerts/severity.py."""
from __future__ import annotations

from alerts.severity import severity_rank, is_critical, is_routine


def test_extreme_outranks_moderate():
    assert severity_rank({"severity": "Extreme"}) > severity_rank({"severity": "Moderate"})


def test_tornado_warning_always_critical_even_if_severity_missing():
    props = {"event": "Tornado Warning"}
    assert is_critical(props) is True
    assert is_routine(props) is False


def test_severe_or_worse_is_critical():
    assert is_critical({"event": "Flood Advisory", "severity": "Severe"}) is True


def test_minor_advisory_is_routine():
    assert is_routine({"event": "Small Craft Advisory", "severity": "Minor"}) is True
