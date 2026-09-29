#!/usr/bin/env bash
# ============================================================================
# energy/scripts/read/river2pro-read.sh — live EcoFlow BLE read (River 2 Pro / B1)
# ----------------------------------------------------------------------------
# WHAT: Snapshot River 2 Pro → SQLite (canonical) + legacy JSON last-files.
# HOW:  ROOT/lib/py → lib/read_runner.py --device river2pro
# RULE: Never invent watts/SOC. BLE down → non-zero / WAITING.
# Phase 1: ROOT = Pacific Energy/ (relative from this script)
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
exec "$ROOT/lib/py" "$ROOT/lib/read_runner.py" --device "river2pro"
