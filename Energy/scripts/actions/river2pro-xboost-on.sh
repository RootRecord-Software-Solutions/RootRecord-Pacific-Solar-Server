#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/river2pro-xboost-on.sh; G3 Pacific path only.
# Atomic BLE action; honest WAITING/FAIL semantics remain in action_runner.py.
set -euo pipefail
ROOT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy"
exec "$ROOT/lib/py" "$ROOT/lib/action_runner.py" \
  --device "river2pro" \
  --method "enable_xboost" \
  --want "on" \
  --label "River2Pro XBoost ON"
