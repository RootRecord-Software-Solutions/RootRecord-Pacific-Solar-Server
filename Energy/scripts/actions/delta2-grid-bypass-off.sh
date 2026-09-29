#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/delta2-grid-bypass-off.sh; G3 Pacific path only.
# Atomic BLE action; honest WAITING/FAIL semantics remain in action_runner.py.
set -euo pipefail
ROOT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy"
exec "$ROOT/lib/py" "$ROOT/lib/action_runner.py" \
  --device "delta2" \
  --method "disable_grid_bypass" \
  --want "off" \
  --label "Delta2 grid bypass OFF"
