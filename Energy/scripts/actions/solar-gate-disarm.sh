#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/solar-gate-disarm.sh; G3 Pacific path only.
set -euo pipefail
STATE="${SOLAR_GATE_STATE:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/ports/solar-gate-state.json}"
mkdir -p "$(dirname "$STATE")"
printf '%s\n' "{\"enabled\": false, \"note\": \"policy disarmed\", \"at\": \"$(date -Iseconds)\"}" > "$STATE"
echo "STATUS=OK policy disarmed"
