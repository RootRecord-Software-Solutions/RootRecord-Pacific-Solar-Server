#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/delta2-usb-off.sh; G3 Pacific path only.
# Atomic BLE action; honest WAITING/FAIL semantics remain in action_runner.py.
set -euo pipefail
ROOT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy"
exec "$ROOT/lib/py" "$ROOT/lib/action_runner.py" \
  --device "delta2" \
  --method "enable_usb_ports" \
  --want "off" \
  --label "Delta2 USB OFF"
