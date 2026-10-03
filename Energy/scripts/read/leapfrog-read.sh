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
# Adapter power cycle is owned by schedule function ble_adapter_cycle — this
# script only reads. Adapter on is Energy/lib/adapter_on.py via ble_client._scan.
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
river_src=""  # info: set river_src
if [[ -f "$river" ]]; then  # info: if
  river_src="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("source") or "")' "$river" 2>/dev/null || true)"  # info: set river_src
fi  # info: fi
set +e  # info: set
if [[ "$river_src" != ble && "$river_src" != ble+cloud ]]; then  # info: River has no live BLE sample, so read Delta before the auth miss
  bash "$ROOT/delta2-read.sh"  # info: bash delta first
  code=$?  # info: set code
  bash "$ROOT/river2pro-read.sh"  # info: then try River
  if [[ "$code" -ne 0 && "$?" -eq 0 ]]; then  # info: if
    code=0  # info: set code
  fi  # info: fi
else  # info: else
  pick="river2pro"  # info: set pick
  if [[ -f "$river" && -f "$delta" && "$delta" -ot "$river" ]]; then  # info: if
    pick="delta2"  # info: set pick
  elif [[ ! -f "$delta" && -f "$river" ]]; then  # info: elif
    pick="delta2"  # info: set pick
  fi  # info: fi
  other="delta2"  # info: set other
  if [[ "$pick" == "delta2" ]]; then  # info: if
    other="river2pro"  # info: set other
  fi  # info: fi
  bash "$ROOT/${pick}-read.sh"  # info: bash the older pack
  code=$?  # info: set code
  if [[ "$code" -ne 0 ]]; then  # info: if the older pack was not read
    bash "$ROOT/${other}-read.sh"  # info: bash the other pack
    if [[ "$?" -eq 0 ]]; then  # info: if
      code=0  # info: set code
    fi  # info: fi
  fi  # info: fi
fi  # info: fi
set -e  # info: set
python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/telegram/scripts/desk-live.py"  # info: rewrite the agent desk from the last files
exit "$code"  # info: exit
