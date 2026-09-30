# ==============================================================================
# FILE: Weather/alerts/county_map.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""SAME/UGC -> county key, plus area-text regex fallback when a geocode is
missing. Ported from the old nws-hawaii module's working approach. Data
lives in config/counties.yaml; this file is the logic that reads it.
"""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re
from functools import lru_cache  # info: from functools import lru_cache
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

import yaml  # info: import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "counties.yaml"  # info: set _CONFIG_PATH


# ====================================================
# SECTION: function _load
# What it does:  load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@lru_cache(maxsize=1)  # info: decorator lru_cache ( maxsize
def _load() -> dict[str, Any]:  # info: def _load
    with open(_CONFIG_PATH, encoding="utf-8") as f:  # info: with open ( _CONFIG_PATH , encoding = "utf-8"
        return yaml.safe_load(f)  # info: return yaml . safe_load ( f )


# ====================================================
# SECTION: function _same_to_key
# What it does:  same to key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@lru_cache(maxsize=1)  # info: decorator lru_cache ( maxsize
def _same_to_key() -> dict[str, str]:  # info: def _same_to_key
    return {c["same"]: c["key"] for c in _load()["counties"]}  # info: return { c [ "same" ] : c


# ====================================================
# SECTION: function _area_patterns
# What it does:  area patterns.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@lru_cache(maxsize=1)  # info: decorator lru_cache ( maxsize
def _area_patterns() -> list[tuple[str, re.Pattern[str]]]:  # info: def _area_patterns
    flags = re.IGNORECASE if "IGNORECASE" in _load().get("regex_flags", []) else 0  # info: set flags
    return [(c["key"], re.compile(c["area_text_pattern"], flags)) for c in _load()["counties"]]  # info: return [ ( c [ "key" ] ,


# ====================================================
# SECTION: function county_keys_for_alert
# What it does: Given an alert's `properties` dict from api.weather.gov alert JSON, return the set of county keys it applies to. SAME geocode is authoritative when present; falls back to areaDesc 
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def county_keys_for_alert(props: dict[str, Any]) -> set[str]:  # info: def county_keys_for_alert
    """Given an alert's `properties` dict from api.weather.gov alert JSON,
    return the set of county keys it applies to. SAME geocode is
    authoritative when present; falls back to areaDesc regex matching only
    when no SAME codes are present at all.
    """
    geocode = props.get("geocode") or {}  # info: set geocode
    same_codes = geocode.get("SAME") or []  # info: set same_codes

    keys: set[str] = set()  # info: set keys
    same_map = _same_to_key()  # info: set same_map
    for code in same_codes:  # info: for code in same_codes :
        key = same_map.get(str(code))  # info: set key
        if key:  # info: if key :
            keys.add(key)  # info: keys . add ( key )

    if keys:  # info: if keys :
        return keys  # info: return keys

    # Fallback: no usable SAME geocode -- try matching areaDesc text.
    area_desc = props.get("areaDesc", "") or ""  # info: set area_desc
    for key, pattern in _area_patterns():  # info: for key , pattern in _area_patterns ( )
        if pattern.search(area_desc):  # info: if pattern . search ( area_desc ) :
            keys.add(key)  # info: keys . add ( key )

    return keys  # info: return keys


# ====================================================
# SECTION: function speech_order
# What it does: speech order.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speech_order() -> list[str]:  # info: def speech_order
    return list(_load()["speech_order"])  # info: return list ( _load ( ) [ "speech_order"


# ====================================================
# SECTION: function speech_name
# What it does: speech name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speech_name(county_key: str) -> str:  # info: def speech_name
    for c in _load()["counties"]:  # info: for c in _load ( ) [ "counties"
        if c["key"] == county_key:  # info: if c [ "key" ] == county_key :
            return c["speech"]  # info: return c [ "speech" ]
    return county_key  # info: return county_key
