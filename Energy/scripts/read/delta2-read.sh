#!/usr/bin/env bash
# ============================================================================
# energy/scripts/read/delta2-read.sh — live EcoFlow BLE read (Delta 2 / B2)
# ----------------------------------------------------------------------------
# WHAT: Snapshot Delta 2 → SQLite (canonical) + legacy JSON last-files.
# HOW:  ROOT/lib/py → lib/read_runner.py --device delta2
# RULE: Never invent watts/SOC. BLE down → non-zero / WAITING.
# Phase 1: ROOT = Pacific Energy/ (relative from this script)
# ============================================================================
set -euo pipefail  # info: set

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"  # info: set ROOT
exec "$ROOT/lib/py" "$ROOT/lib/read_runner.py" --device "delta2"  # info: exec
