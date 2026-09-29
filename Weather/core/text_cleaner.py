"""Strips NWS/AFOS teletype segment-end markers ($, $$, &, &&) from product
text on ingest, per nws_plan.md Section 4 and config/text_cleaning.yaml.

Pure text transform -- no disk, no network. Rules live in
config/text_cleaning.yaml as data, not hardcoded here, per
weather_skill_architecture.md Section 2's "config as data" rule.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    with open(_CONFIG_DIR / "text_cleaning.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _strip_tokens(text: str, tokens: list[str]) -> str:
    # Longer tokens first (config already orders them that way, but don't
    # rely on caller discipline -- re-sort defensively so "$$" is never
    # partially eaten by a "$" removal happening first).
    for token in sorted(tokens, key=len, reverse=True):
        text = text.replace(token, "")
    return text


def _collapse_blank_lines(text: str, collapse_to: int) -> str:
    # Stripping a lone "$$"/"&&" line leaves a blank line behind (or two
    # adjacent ones) -- collapse runs of 2+ blank lines down to `collapse_to`.
    blank_run = r"\n{" + str(collapse_to + 2) + r",}"
    # Normalize any run of (collapse_to+1 or more) consecutive newlines
    # down to exactly collapse_to+1 newlines (= collapse_to blank lines).
    replacement = "\n" * (collapse_to + 1)
    return re.sub(r"\n{" + str(collapse_to + 2) + r",}", replacement, text)


def clean_text(text: str) -> str:
    """Strip segment markers from a raw product body and collapse the
    resulting blank-line gaps. This is the function every text-product
    fetch runs its body through before it ever touches disk (per
    fetch/_engine.py, when `clean_text_body=True`)."""
    config = _load_config()
    tokens = config.get("strip_tokens", ["$$", "&&", "$", "&"])
    cleaned = _strip_tokens(text, tokens)
    if config.get("collapse_blank_lines", True):
        cleaned = _collapse_blank_lines(cleaned, int(config.get("collapse_blank_lines_to", 1)))
    return cleaned


def clean_json_text_fields(obj: Any) -> Any:
    """Recursively clean ONLY the natural-language fields named in
    config/text_cleaning.yaml's `json_text_fields` allowlist (e.g. alerts
    JSON's `description`/`instruction`/`headline`). Every other field --
    ids, timestamps, geocodes, numbers -- passes through untouched, per
    nws_plan.md Section 4's "never corrupt machine-readable metadata" rule.

    Works on any JSON shape (dict, list, or nested combination -- e.g.
    alerts' `{"features": [{"properties": {...}}]}` envelope) without the
    caller needing to know the exact structure.
    """
    config = _load_config()
    text_fields = set(config.get("json_text_fields", []))
    return _clean_recursive(obj, text_fields)


def _clean_recursive(node: Any, text_fields: set[str]) -> Any:
    if isinstance(node, dict):
        cleaned = {}
        for key, value in node.items():
            if key in text_fields and isinstance(value, str):
                cleaned[key] = clean_text(value)
            else:
                cleaned[key] = _clean_recursive(value, text_fields)
        return cleaned
    if isinstance(node, list):
        return [_clean_recursive(item, text_fields) for item in node]
    return node
