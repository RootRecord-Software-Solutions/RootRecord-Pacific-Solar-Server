# ==============================================================================
# FILE: Energy/scripts/actions/solar-gate-status.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/solar-gate-status.sh; G3 Pacific path only.
set -euo pipefail  # info: set
STATE="${SOLAR_GATE_STATE:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/ports/solar-gate-state.json}"  # info: set STATE
if [[ -f "$STATE" ]]; then cat "$STATE"; else echo "WAITING"; echo "No data - solar gate state not written yet"; exit 2; fi  # info: if
