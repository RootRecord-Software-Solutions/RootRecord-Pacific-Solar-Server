#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/solar-gate-arm.sh; G3 Pacific path only.
set -euo pipefail
STATE="${SOLAR_GATE_STATE:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/ports/solar-gate-state.json}"
mkdir -p "$(dirname "$STATE")"
printf '%s\n' "{\"enabled\": true, \"pv_gate_w\": 400, \"note\": \"policy armed; USB toggles via delta2-usb-*; no live PV invented\", \"at\": \"$(date -Iseconds)\"}" > "$STATE"
echo "STATUS=OK policy armed (no watts invented)"
