# ==============================================================================
# FILE: Energy/scripts/read/leapfrog-read.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Read the pack whose watt file is older. A wall-clock slot was skipping River
# whenever the poller freed up on an even 5-second boundary.
set -euo pipefail  # info: set
ROOT="$(cd "$(dirname "$0")" && pwd)"  # info: set ROOT
WATTS="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/watts"  # info: set WATTS
LOCK="/tmp/ecoflow-ble.lock"  # info: set LOCK
exec 9>"$LOCK"  # info: exec
if ! flock -n 9; then  # info: if
  echo "ecoflow read already running"  # info: echo
  exit 0  # info: exit
fi  # info: fi
delta="$WATTS/delta2-last.json"  # info: set delta
river="$WATTS/river2pro-last.json"  # info: set river
pick="river2pro"  # info: set pick
if [[ -f "$river" && -f "$delta" && "$delta" -ot "$river" ]]; then  # info: if
  pick="delta2"  # info: set pick
elif [[ ! -f "$delta" && -f "$river" ]]; then  # info: elif
  pick="delta2"  # info: set pick
fi  # info: fi
exec bash "$ROOT/${pick}-read.sh"  # info: exec
