#!/usr/bin/env python3
# ==============================================================================
# config.py — minimal INI reader for devices.conf (stdlib only)
# ------------------------------------------------------------------------------
# Env overlay: ECOFLOW_*_SN / NAME from master-key.env win when present
# (same source of truth BLE already uses).
# ==============================================================================
"""Minimal INI reader for devices.conf (stdlib only)."""
from __future__ import annotations

import configparser
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from paths import CONFIG  # noqa: E402


def load(path: Path | None = None) -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.read(path or CONFIG)
    return cp


def device(alias: str) -> dict:
    """Return one device section as a plain dict, with env SN/name overlay."""
    cp = load()
    if alias not in cp:
        raise KeyError(f"unknown device alias: {alias}")
    d = dict(cp[alias])
    try:
        from envload import env_sn, env_name
        sn = env_sn(alias)
        name = env_name(alias)
        if sn:
            d["sn"] = sn
        if name:
            d["name"] = name
    except Exception:
        pass
    return d
