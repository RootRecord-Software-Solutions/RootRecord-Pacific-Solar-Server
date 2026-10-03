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
# If both watt files are stale, make sure hci0 is powered on, then read.
# Powering the adapter off stranded it. A second check waits out the cooldown.
set -euo pipefail  # info: set
ROOT="$(cd "$(dirname "$0")" && pwd)"  # info: set ROOT
WATTS="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/watts"  # info: set WATTS
LOCK="/tmp/ecoflow-ble.lock"  # info: set LOCK
STALE_SEC=180  # info: set STALE_SEC
RESET_STAMP="/tmp/ecoflow-ble-adapter-reset"  # info: set RESET_STAMP
exec 9>"$LOCK"  # info: exec
if ! flock -n 9; then  # info: if
  echo "ecoflow read already running"  # info: echo
  exit 0  # info: exit
fi  # info: fi

# ====================================================
# SECTION: function file_age
# What it does: Seconds since the watt file was written. A missing file is stale.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
file_age() {  # info: file_age
  local path="$1"  # info: set path
  if [[ ! -f "$path" ]]; then  # info: if
    echo "$STALE_SEC"  # info: echo
    return 0  # info: return
  fi  # info: fi
  echo $(( $(date +%s) - $(stat -c %Y "$path") ))  # info: echo
}  # info: file_age

# ====================================================
# SECTION: function both_packs_stale
# What it does: True when Delta 2 and River 2 Pro watt files are both at least STALE_SEC old.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
both_packs_stale() {  # info: both_packs_stale
  local age  # info: set age
  age="$(file_age "$WATTS/delta2-last.json")"  # info: set age
  if (( age < STALE_SEC )); then  # info: if
    return 1  # info: return
  fi  # info: fi
  age="$(file_age "$WATTS/river2pro-last.json")"  # info: set age
  if (( age < STALE_SEC )); then  # info: if
    return 1  # info: return
  fi  # info: fi
  return 0  # info: return
}  # info: both_packs_stale

# ====================================================
# SECTION: function reset_adapter_if_both_stale
# What it does: Power hci0 on when both packs are stale, at most once per STALE_SEC. Does not power it off and does not restart bluetoothd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
reset_adapter_if_both_stale() {  # info: reset_adapter_if_both_stale
  local stamp_age  # info: set stamp_age
  if ! both_packs_stale; then  # info: if
    return 0  # info: return
  fi  # info: fi
  stamp_age="$(file_age "$RESET_STAMP")"  # info: set stamp_age
  if (( stamp_age < STALE_SEC )); then  # info: if
    echo "both packs stale — adapter check still in cooldown (${stamp_age}s)"  # info: echo
    return 0  # info: return
  fi  # info: fi
  echo "both packs stale — ensuring hci0 is powered on"  # info: echo
  bluetoothctl power on >/dev/null 2>&1 || true  # info: bluetoothctl power on
  date +%s >"$RESET_STAMP"  # info: date
  sleep 2  # info: sleep
}  # info: reset_adapter_if_both_stale

reset_adapter_if_both_stale  # info: call reset_adapter_if_both_stale
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
