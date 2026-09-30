# ==============================================================================
# FILE: Weather/core/text_cleaner.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Strips NWS/AFOS teletype segment-end markers ($, $$, &, &&) from product
text on ingest, per nws_plan.md Section 4 and config/text_cleaning.yaml.

Pure text transform -- no disk, no network. Rules live in
config/text_cleaning.yaml as data, not hardcoded here, per
weather_skill_architecture.md Section 2's "config as data" rule.
"""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re
from functools import lru_cache  # info: from functools import lru_cache
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

import yaml  # info: import yaml

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"  # info: set _CONFIG_DIR


# ====================================================
# SECTION: function _load_config
# What it does:  load config.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@lru_cache(maxsize=1)  # info: decorator lru_cache ( maxsize
def _load_config() -> dict[str, Any]:  # info: def _load_config
    with open(_CONFIG_DIR / "text_cleaning.yaml", encoding="utf-8") as f:  # info: with open ( _CONFIG_DIR / "text_cleaning.yaml" , encoding
        return yaml.safe_load(f)  # info: return yaml . safe_load ( f )


# ====================================================
# SECTION: function _strip_tokens
# What it does:  strip tokens.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _strip_tokens(text: str, tokens: list[str]) -> str:  # info: def _strip_tokens
    # Longer tokens first (config already orders them that way, but don't
    # rely on caller discipline -- re-sort defensively so "$$" is never
    # partially eaten by a "$" removal happening first).
    for token in sorted(tokens, key=len, reverse=True):  # info: for token in sorted ( tokens , key
        text = text.replace(token, "")  # info: set text
    return text  # info: return text


# ====================================================
# SECTION: function _collapse_blank_lines
# What it does:  collapse blank lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _collapse_blank_lines(text: str, collapse_to: int) -> str:  # info: def _collapse_blank_lines
    # Stripping a lone "$$"/"&&" line leaves a blank line behind (or two
    # adjacent ones) -- collapse runs of 2+ blank lines down to `collapse_to`.
    blank_run = r"\n{" + str(collapse_to + 2) + r",}"  # info: set blank_run
    # Normalize any run of (collapse_to+1 or more) consecutive newlines
    # down to exactly collapse_to+1 newlines (= collapse_to blank lines).
    replacement = "\n" * (collapse_to + 1)  # info: set replacement
    return re.sub(r"\n{" + str(collapse_to + 2) + r",}", replacement, text)  # info: return re . sub ( r"\n{" + str


# ====================================================
# SECTION: function clean_text
# What it does: Strip segment markers from a raw product body and collapse the resulting blank-line gaps. This is the function every text-product fetch runs its body through before it ever touches
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clean_text(text: str) -> str:  # info: def clean_text
    """Strip segment markers from a raw product body and collapse the
    resulting blank-line gaps. This is the function every text-product
    fetch runs its body through before it ever touches disk (per
    fetch/_engine.py, when `clean_text_body=True`)."""
    config = _load_config()  # info: set config
    tokens = config.get("strip_tokens", ["$$", "&&", "$", "&"])  # info: set tokens
    cleaned = _strip_tokens(text, tokens)  # info: set cleaned
    if config.get("collapse_blank_lines", True):  # info: if config . get ( "collapse_blank_lines" , True
        cleaned = _collapse_blank_lines(cleaned, int(config.get("collapse_blank_lines_to", 1)))  # info: set cleaned
    return cleaned  # info: return cleaned


# ====================================================
# SECTION: function clean_json_text_fields
# What it does: Recursively clean ONLY the natural-language fields named in config/text_cleaning.yaml's `json_text_fields` allowlist (e.g. alerts JSON's `description`/`instruction`/`headline`). Ev
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clean_json_text_fields(obj: Any) -> Any:  # info: def clean_json_text_fields
    """Recursively clean ONLY the natural-language fields named in
    config/text_cleaning.yaml's `json_text_fields` allowlist (e.g. alerts
    JSON's `description`/`instruction`/`headline`). Every other field --
    ids, timestamps, geocodes, numbers -- passes through untouched, per
    nws_plan.md Section 4's "never corrupt machine-readable metadata" rule.

    Works on any JSON shape (dict, list, or nested combination -- e.g.
    alerts' `{"features": [{"properties": {...}}]}` envelope) without the
    caller needing to know the exact structure.
    """
    config = _load_config()  # info: set config
    text_fields = set(config.get("json_text_fields", []))  # info: set text_fields
    return _clean_recursive(obj, text_fields)  # info: return _clean_recursive ( obj , text_fields )


# ====================================================
# SECTION: function _clean_recursive
# What it does:  clean recursive.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clean_recursive(node: Any, text_fields: set[str]) -> Any:  # info: def _clean_recursive
    if isinstance(node, dict):  # info: if isinstance ( node , dict ) :
        cleaned = {}  # info: set cleaned
        for key, value in node.items():  # info: for key , value in node . items
            if key in text_fields and isinstance(value, str):  # info: if key in text_fields and isinstance ( value
                cleaned[key] = clean_text(value)  # info: cleaned [ key ] = clean_text ( value
            else:  # info: else :
                cleaned[key] = _clean_recursive(value, text_fields)  # info: cleaned [ key ] = _clean_recursive ( value
        return cleaned  # info: return cleaned
    if isinstance(node, list):  # info: if isinstance ( node , list ) :
        return [_clean_recursive(item, text_fields) for item in node]  # info: return [ _clean_recursive ( item , text_fields )
    return node  # info: return node
