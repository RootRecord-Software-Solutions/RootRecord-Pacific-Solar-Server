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
# If both watt files are stale, power-cycle hci0 once, then read. A second
# cycle waits until the cooldown passes so a dead scan cannot bounce the radio
# on every timer tick.
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
# What it does: Power-cycle hci0 when both packs are stale, at most once per STALE_SEC. Does not restart bluetoothd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
reset_adapter_if_both_stale() {  # info: reset_adapter_if_both_stale
  local stamp_age  # info: set stamp_age
  if ! both_packs_stale; then  # info: if
    return 0  # info: return
  fi  # info: fi
  stamp_age="$(file_age "$RESET_STAMP")"  # info: set stamp_age
  if (( stamp_age < STALE_SEC )); then  # info: if
    echo "both packs stale — adapter reset still in cooldown (${stamp_age}s)"  # info: echo
    return 0  # info: return
  fi  # info: fi
  echo "both packs stale — power-cycling hci0"  # info: echo
  bluetoothctl power off >/dev/null 2>&1 || true  # info: bluetoothctl power off
  bluetoothctl power on >/dev/null 2>&1 || true  # info: bluetoothctl power on
  date +%s >"$RESET_STAMP"  # info: date
  sleep 2  # info: sleep
}  # info: reset_adapter_if_both_stale

reset_adapter_if_both_stale  # info: call reset_adapter_if_both_stale
delta="$WATTS/delta2-last.json"  # info: set delta
river="$WATTS/river2pro-last.json"  # info: set river
pick="river2pro"  # info: set pick
if [[ -f "$river" && -f "$delta" && "$delta" -ot "$river" ]]; then  # info: if
  pick="delta2"  # info: set pick
elif [[ ! -f "$delta" && -f "$river" ]]; then  # info: elif
  pick="delta2"  # info: set pick
fi  # info: fi
exec bash "$ROOT/${pick}-read.sh"  # info: exec
