#!/usr/bin/env python3
# ==============================================================================
# paths.py — shared filesystem paths for the Energy domain
# ------------------------------------------------------------------------------
# Measured data → RootRecord Database authority (not Network, not GitHub telemetry).
# ==============================================================================
"""Shared paths for Energy domain. Measured data → canonical RootRecord Database."""
from __future__ import annotations

from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG = SKILL_ROOT / "config" / "devices.conf"
VENDOR = SKILL_ROOT / "lib" / "vendor"

# Canonical Database root.
DATABASE_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")

ENERGY_DATA = DATABASE_ROOT / "Energy"
SAMPLES = ENERGY_DATA / "samples"
PORTS = ENERGY_DATA / "ports"
SOC = ENERGY_DATA / "soc"
WATTS = ENERGY_DATA / "watts"

LOG_DIR = DATABASE_ROOT / "Logs" / "Energy"
BLE_LOG = LOG_DIR / "ecoflow-ble.log"
STATE_DIR = ENERGY_DATA / "state"
# Cloud quota snapshots. Created only when a signed-off cloud read writes.
CLOUD_QUOTA = ENERGY_DATA / "Cloud-Quota"
CLOUD_QUOTA_LOG = LOG_DIR / "Cloud-Quota"


def ensure_dirs() -> None:
    for p in (SAMPLES, PORTS, SOC, WATTS, LOG_DIR, STATE_DIR, ENERGY_DATA / "buckets"):
        p.mkdir(parents=True, exist_ok=True)
