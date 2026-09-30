#!/usr/bin/env python3
# ==============================================================================
# paths.py — shared filesystem paths for the Energy domain
# ------------------------------------------------------------------------------
# Measured data → RootRecord Database authority (not Network, not GitHub telemetry).
# ==============================================================================
"""Shared paths for Energy domain. Measured data → canonical RootRecord Database."""  # info: """Shared paths for Energy domain. Measured data → canonical RootRecord Database."""
from __future__ import annotations  # info: from __future__ import annotations

from pathlib import Path  # info: from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent  # info: set SKILL_ROOT
CONFIG = SKILL_ROOT / "config" / "devices.conf"  # info: set CONFIG
VENDOR = SKILL_ROOT / "lib" / "vendor"  # info: set VENDOR

# Canonical Database root.
DATABASE_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE_ROOT

ENERGY_DATA = DATABASE_ROOT / "Energy"  # info: set ENERGY_DATA
SAMPLES = ENERGY_DATA / "samples"  # info: set SAMPLES
PORTS = ENERGY_DATA / "ports"  # info: set PORTS
SOC = ENERGY_DATA / "soc"  # info: set SOC
WATTS = ENERGY_DATA / "watts"  # info: set WATTS

LOG_DIR = DATABASE_ROOT / "Logs" / "Energy"  # info: set LOG_DIR
BLE_LOG = LOG_DIR / "ecoflow-ble.log"  # info: set BLE_LOG
STATE_DIR = ENERGY_DATA / "state"  # info: set STATE_DIR
# Cloud quota snapshots. Created only when a signed-off cloud read writes.
CLOUD_QUOTA = ENERGY_DATA / "Cloud-Quota"  # info: set CLOUD_QUOTA
CLOUD_QUOTA_LOG = LOG_DIR / "Cloud-Quota"  # info: set CLOUD_QUOTA_LOG


# ====================================================
# SECTION: function ensure_dirs
# What it does: ensure dirs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_dirs() -> None:  # info: def ensure_dirs
    for p in (SAMPLES, PORTS, SOC, WATTS, LOG_DIR, STATE_DIR, ENERGY_DATA / "buckets"):  # info: for p in ( SAMPLES , PORTS ,
        p.mkdir(parents=True, exist_ok=True)  # info: p . mkdir ( parents = True ,
