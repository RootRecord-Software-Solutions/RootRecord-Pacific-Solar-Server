#!/usr/bin/env bash
# ==============================================================================
# timelapse_hourly.sh — Pacific A-Eyes hourly timelapse wrapper
# Calls the migrated timelapse engine for the completed hour.
# ==============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/timelapse_engine.py" hourly "$@"
