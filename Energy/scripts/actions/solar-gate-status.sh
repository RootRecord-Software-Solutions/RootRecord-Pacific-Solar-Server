#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/solar-gate-status.sh; G3 Pacific path only.
set -euo pipefail
STATE="${SOLAR_GATE_STATE:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/ENERGY/ports/solar-gate-state.json}"
if [[ -f "$STATE" ]]; then cat "$STATE"; else echo "WAITING"; echo "No data - solar gate state not written yet"; exit 2; fi
