# ==============================================================================
# FILE: Energy/scripts/actions/solar-gate-arm.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/solar-gate-arm.sh; G3 Pacific path only.
set -euo pipefail  # info: set
STATE="${SOLAR_GATE_STATE:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/ports/solar-gate-state.json}"  # info: set STATE
mkdir -p "$(dirname "$STATE")"  # info: mkdir
printf '%s\n' "{\"enabled\": true, \"pv_gate_w\": 400, \"note\": \"policy armed; USB toggles via delta2-usb-*; no live PV invented\", \"at\": \"$(date -Iseconds)\"}" > "$STATE"  # info: printf
echo "STATUS=OK policy armed (no watts invented)"  # info: echo
