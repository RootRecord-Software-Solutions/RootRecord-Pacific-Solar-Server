"""Tags an alert's severity tier, isolated so the threshold can change
without touching county-mapping or dedupe logic. Input is a single alert's
`properties` dict from api.weather.gov alert JSON.
"""
from __future__ import annotations

from typing import Any

# api.weather.gov's own `severity` field values, ranked worst-first. Anything
# not in this list (rare/unknown) is treated as "Unknown" -- see below.
_SEVERITY_RANK = {"Extreme": 4, "Severe": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}

# Event names that are life-safety-critical regardless of the API's own
# severity field -- some NWS event types (e.g. Tornado Warning) should never
# be treated as routine even if severity metadata is missing/stale.
_ALWAYS_CRITICAL_EVENTS = {
    "tornado warning",
    "flash flood warning",
    "tsunami warning",
    "hurricane warning",
    "extreme wind warning",
}


def severity_rank(props: dict[str, Any]) -> int:
    return _SEVERITY_RANK.get(props.get("severity", "Unknown"), 0)


def is_critical(props: dict[str, Any]) -> bool:
    """True for anything that should be surfaced/spoken immediately,
    regardless of the routine polling cadence."""
    event = (props.get("event") or "").strip().lower()
    if event in _ALWAYS_CRITICAL_EVENTS:
        return True
    return severity_rank(props) >= _SEVERITY_RANK["Severe"]


def is_routine(props: dict[str, Any]) -> bool:
    return not is_critical(props)
