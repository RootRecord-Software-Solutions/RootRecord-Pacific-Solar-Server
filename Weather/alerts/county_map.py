"""SAME/UGC -> county key, plus area-text regex fallback when a geocode is
missing. Ported from the old nws-hawaii module's working approach. Data
lives in config/counties.yaml; this file is the logic that reads it.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "counties.yaml"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def _same_to_key() -> dict[str, str]:
    return {c["same"]: c["key"] for c in _load()["counties"]}


@lru_cache(maxsize=1)
def _area_patterns() -> list[tuple[str, re.Pattern[str]]]:
    flags = re.IGNORECASE if "IGNORECASE" in _load().get("regex_flags", []) else 0
    return [(c["key"], re.compile(c["area_text_pattern"], flags)) for c in _load()["counties"]]


def county_keys_for_alert(props: dict[str, Any]) -> set[str]:
    """Given an alert's `properties` dict from api.weather.gov alert JSON,
    return the set of county keys it applies to. SAME geocode is
    authoritative when present; falls back to areaDesc regex matching only
    when no SAME codes are present at all.
    """
    geocode = props.get("geocode") or {}
    same_codes = geocode.get("SAME") or []

    keys: set[str] = set()
    same_map = _same_to_key()
    for code in same_codes:
        key = same_map.get(str(code))
        if key:
            keys.add(key)

    if keys:
        return keys

    # Fallback: no usable SAME geocode -- try matching areaDesc text.
    area_desc = props.get("areaDesc", "") or ""
    for key, pattern in _area_patterns():
        if pattern.search(area_desc):
            keys.add(key)

    return keys


def speech_order() -> list[str]:
    return list(_load()["speech_order"])


def speech_name(county_key: str) -> str:
    for c in _load()["counties"]:
        if c["key"] == county_key:
            return c["speech"]
    return county_key
