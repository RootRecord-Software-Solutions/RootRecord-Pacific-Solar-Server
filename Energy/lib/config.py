#!/usr/bin/env python3
# ==============================================================================
# config.py — minimal INI reader for devices.conf (stdlib only)
# ------------------------------------------------------------------------------
# Env overlay: ECOFLOW_*_SN / NAME from master-key.env win when present
# (same source of truth BLE already uses).
# ==============================================================================
"""Minimal INI reader for devices.conf (stdlib only)."""  # info: """Minimal INI reader for devices.conf (stdlib only)."""
from __future__ import annotations  # info: from __future__ import annotations

import configparser  # info: import configparser
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
if str(HERE) not in sys.path:  # info: if str ( HERE ) not in sys
    sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
from paths import CONFIG  # noqa: E402


# ====================================================
# SECTION: function load
# What it does: load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load(path: Path | None = None) -> configparser.ConfigParser:  # info: def load
    cp = configparser.ConfigParser()  # info: set cp
    cp.read(path or CONFIG)  # info: cp . read ( path or CONFIG )
    return cp  # info: return cp


# ====================================================
# SECTION: function device
# What it does: Return one device section as a plain dict, with env SN/name overlay.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def device(alias: str) -> dict:  # info: def device
    """Return one device section as a plain dict, with env SN/name overlay."""  # info: """Return one device section as a plain dict, with env SN/name overlay."""
    cp = load()  # info: set cp
    if alias not in cp:  # info: if alias not in cp :
        raise KeyError(f"unknown device alias: {alias}")  # info: raise KeyError ( f" unknown device alias: { alias }
    d = dict(cp[alias])  # info: set d
    try:  # info: try :
        from envload import env_sn, env_name  # info: from envload import env_sn , env_name
        sn = env_sn(alias)  # info: set sn
        name = env_name(alias)  # info: set name
        if sn:  # info: if sn :
            d["sn"] = sn  # info: d [ "sn" ] = sn
        if name:  # info: if name :
            d["name"] = name  # info: d [ "name" ] = name
    except Exception:  # info: except Exception :
        pass  # info: pass
    return d  # info: return d
