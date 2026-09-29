"""Event+county dedupe, keep-newest-sent logic. NWS frequently reissues the
same alert (renewed/updated) under a new `id` -- this collapses those to one
entry per (event, county) so downstream reporting doesn't repeat itself.
"""
from __future__ import annotations

from typing import Any

from alerts.county_map import county_keys_for_alert


def _sent_time(props: dict[str, Any]) -> str:
    # ISO 8601 strings sort correctly as plain strings for this purpose.
    return props.get("sent") or props.get("effective") or ""


def dedupe_by_event_and_county(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Given a list of raw alert features (each with a `properties` dict),
    return one alert per (event, county) pair -- the most recently `sent`
    one wins. An alert covering multiple counties can still "win" for each
    of its counties independently.
    """
    best: dict[tuple[str, str], dict[str, Any]] = {}

    for alert in alerts:
        props = alert.get("properties", {})
        event = props.get("event", "Unknown")
        counties = county_keys_for_alert(props) or {"_unmapped"}
        sent = _sent_time(props)

        for county in counties:
            key = (event, county)
            current_best = best.get(key)
            if current_best is None or _sent_time(current_best.get("properties", {})) < sent:
                best[key] = alert

    # Preserve a stable, de-duplicated list (each unique alert object appears
    # once even if it won for multiple counties).
    seen_ids = set()
    result = []
    for alert in best.values():
        alert_id = alert.get("id") or id(alert)
        if alert_id not in seen_ids:
            seen_ids.add(alert_id)
            result.append(alert)
    return result


def by_county(alerts: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Event names grouped by county key, after dedupe."""
    deduped = dedupe_by_event_and_county(alerts)
    grouped: dict[str, list[str]] = {}
    for alert in deduped:
        props = alert.get("properties", {})
        event = props.get("event", "Unknown")
        for county in county_keys_for_alert(props):
            grouped.setdefault(county, []).append(event)
    return grouped
