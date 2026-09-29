#!/usr/bin/env python3
# ==============================================================================
# paths.py — shared filesystem paths for the energy skill
# ------------------------------------------------------------------------------
# Measured data → Database/ENERGY only (not Network, not GitHub telemetry).
# Layout style (standing): keep SECTION banners if this file grows catalogs.
# ==============================================================================
"""Shared paths for energy skill. Measured data → Database/ENERGY only."""
from __future__ import annotations

from pathlib import Path

# ====================================================
# SECTION: SKILL + CONFIG
# ====================================================
# Phase 1: Energy domain root = parent of lib/
SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG = SKILL_ROOT / "config" / "devices.conf"
VENDOR = SKILL_ROOT / "lib" / "vendor"

# ====================================================
# SECTION: MEASURED DATA (Database/ENERGY)
# ====================================================
ENERGY_DATA = Path("/home/rootrecord/Database/ENERGY")
SAMPLES = ENERGY_DATA / "samples"
PORTS = ENERGY_DATA / "ports"
SOC = ENERGY_DATA / "soc"
WATTS = ENERGY_DATA / "watts"

# ====================================================
# SECTION: LOGS + STATE
# ====================================================
LOG_DIR = Path("/home/rootrecord/.ollama/skills/logs/store")
BLE_LOG = LOG_DIR / "ava-ecoflow-ble.log"
STATE_DIR = Path("/home/rootrecord/.ollama/skills/state/store")


def ensure_dirs() -> None:
    """Create measured-data and log directories if missing."""
    for p in (SAMPLES, PORTS, SOC, WATTS, LOG_DIR, STATE_DIR, ENERGY_DATA / "buckets"):
        p.mkdir(parents=True, exist_ok=True)
