# ==============================================================================
# FILE: Energy/scripts/watchdog/river2pro-ac-recover.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Local River 2 Pro AC recover: when fresh SOC >= 5% OR fresh AC input power >= 50W
# and AC ports are off, run river2pro-ac-on.sh so Starlink/net can return after a cut.
# Does not delete collectors, does not force AC off, and no-ops when AC is on.
set -euo pipefail  # info: set

SOC_MIN=5  # info: set SOC_MIN
FRESH_SEC=300  # info: set FRESH_SEC
COOLDOWN_SEC=120  # info: set COOLDOWN_SEC
DB="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy"  # info: set DB
SOC_FILE="$DB/soc/river2pro-last.json"  # info: set SOC_FILE
PORTS_FILE="$DB/ports/river2pro-last.json"  # info: set PORTS_FILE
WATTS_FILE="$DB/watts/river2pro-last.json"  # info: set WATTS_FILE
SAMPLES_DIR="$DB/samples"  # info: set SAMPLES_DIR
STATE_DIR="$DB/state"  # info: set STATE_DIR
STAMP="$STATE_DIR/river2pro-ac-recover.last-attempt"  # info: set STAMP
LOG="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Energy/river2pro-ac-recover.log"  # info: set LOG
AC_ON="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/scripts/actions/river2pro-ac-on.sh"  # info: set AC_ON
DRY_RUN=0  # info: set DRY_RUN

# ====================================================
# SECTION: function usage
# What it does: Print usage and exit. Does not touch AC or collectors.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
usage() {  # info: usage
  echo "Usage: $0 [--dry-run]"  # info: echo
  exit 2  # info: exit
}  # info: usage

# ====================================================
# SECTION: function log_line
# What it does: Append one light HST log line and echo it. Does not rotate or delete logs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
log_line() {  # info: log_line
  local msg="$1"  # info: set msg
  local line  # info: set line
  line="$(date '+%Y-%m-%dT%H:%M:%S%z') river2pro-ac-recover: $msg"  # info: set line
  mkdir -p "$(dirname "$LOG")"  # info: mkdir
  echo "$line" | tee -a "$LOG"  # info: echo tee
}  # info: log_line

# ====================================================
# SECTION: function file_age_sec
# What it does: Seconds since mtime; missing file returns a large stale age.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
file_age_sec() {  # info: file_age_sec
  local path="$1"  # info: set path
  if [[ ! -f "$path" ]]; then  # info: if
    echo 999999  # info: echo
    return 0  # info: return
  fi  # info: fi
  echo $(( $(date +%s) - $(stat -c %Y "$path") ))  # info: echo
}  # info: file_age_sec

# ====================================================
# SECTION: function read_soc
# What it does: Print SOC number from river2pro-last.json or empty on failure.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
read_soc() {  # info: read_soc
  python3 - "$SOC_FILE" <<'PY'  # info: python3
import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path, encoding="utf-8"))
    soc = data.get("soc")
    if soc is None:
        sys.exit(0)
    print(float(soc))
except Exception:
    sys.exit(0)
PY
}  # info: read_soc

# ====================================================
# SECTION: function latest_ac_snapshot
# What it does: Pick newest ports or read-river2pro sample; print path TAB ac_ports (true/false/null) TAB age seconds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
latest_ac_snapshot() {  # info: latest_ac_snapshot
  python3 - "$PORTS_FILE" "$SAMPLES_DIR" <<'PY'  # info: python3
import json, os, sys, glob, time
ports = sys.argv[1]
samples_dir = sys.argv[2]
candidates = []
if os.path.isfile(ports):
    candidates.append(ports)
candidates.extend(glob.glob(os.path.join(samples_dir, "read-river2pro-*.json")))
if not candidates:
    print("\tnull\t999999")
    sys.exit(0)
path = max(candidates, key=os.path.getmtime)
try:
    data = json.load(open(path, encoding="utf-8"))
except Exception:
    print(f"{path}\tnull\t999999")
    sys.exit(0)
fields = data.get("fields") if isinstance(data.get("fields"), dict) else data
val = fields.get("ac_ports") if isinstance(fields, dict) else None
if val is True:
    flag = "true"
elif val is False:
    flag = "false"
else:
    flag = "null"
print(f"{path}\t{flag}\t{max(0, int(time.time() - os.path.getmtime(path)))}")
PY
}  # info: latest_ac_snapshot

# ====================================================
# SECTION: function latest_input_snapshot
# What it does: Pick newest River input-power JSON and print path TAB field TAB watts TAB age seconds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
latest_input_snapshot() {  # info: latest_input_snapshot
  python3 - "$WATTS_FILE" "$SAMPLES_DIR" <<'PY'  # info: python3
import json, os, sys, glob, time
watts = sys.argv[1]
samples_dir = sys.argv[2]
candidates = []
if os.path.isfile(watts):
    candidates.append(watts)
candidates.extend(glob.glob(os.path.join(samples_dir, "read-river2pro-*.json")))
for path in sorted(candidates, key=os.path.getmtime, reverse=True):
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else data
    if not isinstance(fields, dict):
        continue
    for key in ("ac_input_power", "input_watts", "input_power", "charge_watts"):
        value = fields.get(key)
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        print(f"{path}\t{key}\t{number:g}\t{max(0, int(time.time() - os.path.getmtime(path)))}")
        sys.exit(0)
print("\t\t\t999999")
PY
}  # info: latest_input_snapshot

# ====================================================
# SECTION: function in_cooldown
# What it does: True when a prior AC-on attempt stamp is younger than COOLDOWN_SEC.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
in_cooldown() {  # info: in_cooldown
  local age  # info: set age
  age="$(file_age_sec "$STAMP")"  # info: set age
  if (( age < COOLDOWN_SEC )); then  # info: if
    return 0  # info: return
  fi  # info: fi
  return 1  # info: return
}  # info: in_cooldown

# ====================================================
# SECTION: function mark_attempt
# What it does: Refresh the cooldown stamp after an AC-on attempt. Does not clear collectors.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
mark_attempt() {  # info: mark_attempt
  mkdir -p "$STATE_DIR"  # info: mkdir
  date +%s >"$STAMP"  # info: date
}  # info: mark_attempt

# ====================================================
# SECTION: function main
# What it does: Decide whether to run river2pro-ac-on.sh; no-op when AC is on, inputs are stale, or neither trigger is ready.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
main() {  # info: main
  if [[ "${1:-}" == "--dry-run" ]]; then  # info: if
    DRY_RUN=1  # info: set DRY_RUN
  elif [[ -n "${1:-}" ]]; then  # info: elif
    usage  # info: usage
  fi  # info: fi

  local soc_age=999999 soc="" ac_path="" ac_flag="" ac_age=999999  # info: set signal locals
  local input_path="" input_key="" input_watts="" input_age=999999  # info: set input locals
  local soc_ready=0 input_ready=0 trigger_reason=""  # info: set trigger flags

  if [[ -f "$SOC_FILE" ]]; then  # info: if
    soc_age="$(file_age_sec "$SOC_FILE")"  # info: set soc_age
    soc="$(read_soc || true)"  # info: set soc
    if [[ -n "$soc" ]] && (( soc_age <= FRESH_SEC )); then  # info: if
      if awk -v s="$soc" -v m="$SOC_MIN" 'BEGIN { exit !(s+0 >= m+0) }'; then  # info: if
        soc_ready=1  # info: set soc_ready
        trigger_reason="soc"  # info: set trigger_reason
      fi  # info: fi
    fi  # info: fi
  fi  # info: fi

  IFS=$'\t' read -r ac_path ac_flag ac_age < <(latest_ac_snapshot)  # info: read AC snapshot
  IFS=$'\t' read -r input_path input_key input_watts input_age < <(latest_input_snapshot)  # info: read input snapshot
  if [[ -n "$input_watts" ]] && (( input_age <= FRESH_SEC )); then  # info: if
    if awk -v w="$input_watts" 'BEGIN { exit !(w+0 >= 50) }'; then  # info: if
      input_ready=1  # info: set input_ready
      if [[ "$soc_ready" -eq 0 ]]; then  # info: if
        trigger_reason="input_watts"  # info: set trigger_reason
      else  # info: else
        trigger_reason="soc_or_input_watts"  # info: set trigger_reason
      fi  # info: fi
    fi  # info: fi
  fi  # info: fi

  if [[ "$ac_flag" == "true" ]]; then  # info: if
    log_line "no-op ac_already_on soc=${soc:-null} soc_age=${soc_age}s input_watts=${input_watts:-null} input_key=${input_key:-none} input_age=${input_age}s ac_age=${ac_age}s src=$(basename "${ac_path:-none}")"  # info: log_line
    return 0  # info: return
  fi  # info: fi
  if [[ "$ac_flag" != "false" || "$ac_age" -gt "$FRESH_SEC" ]]; then  # info: if
    log_line "no-op ac_unknown_or_stale soc=${soc:-null} soc_age=${soc_age}s input_watts=${input_watts:-null} input_key=${input_key:-none} input_age=${input_age}s ac_ports=${ac_flag:-null} ac_age=${ac_age}s"  # info: log_line
    return 0  # info: return
  fi  # info: fi

  if [[ "$soc_ready" -eq 0 && "$input_ready" -eq 0 ]]; then  # info: if
    log_line "no-op triggers_not_ready soc=${soc:-null} soc_age=${soc_age}s min=${SOC_MIN} input_watts=${input_watts:-null} input_key=${input_key:-none} input_age=${input_age}s input_min=50 ac_ports=${ac_flag} ac_age=${ac_age}s"  # info: log_line
    return 0  # info: return
  fi  # info: fi

  if in_cooldown; then  # info: if
    log_line "no-op cooldown reason=${trigger_reason} soc=${soc:-null} soc_age=${soc_age}s input_watts=${input_watts:-null} input_key=${input_key:-none} input_age=${input_age}s ac_ports=${ac_flag} ac_age=${ac_age}s remaining_lt=${COOLDOWN_SEC}s"  # info: log_line
    return 0  # info: return
  fi  # info: fi

  if [[ "$DRY_RUN" -eq 1 ]]; then  # info: if
    log_line "dry-run WOULD_RUN_ac_on reason=${trigger_reason} soc=${soc:-null} soc_age=${soc_age}s input_watts=${input_watts:-null} input_key=${input_key:-none} input_age=${input_age}s ac_ports=${ac_flag} ac_age=${ac_age}s"  # info: log_line
    return 0  # info: return
  fi  # info: fi

  if [[ ! -x "$AC_ON" && ! -f "$AC_ON" ]]; then  # info: if
    log_line "fail missing_ac_on_script path=$AC_ON"  # info: log_line
    return 1  # info: return
  fi  # info: fi

  log_line "run ac_on reason=${trigger_reason} soc=${soc:-null} soc_age=${soc_age}s input_watts=${input_watts:-null} input_key=${input_key:-none} input_age=${input_age}s ac_ports=${ac_flag} ac_age=${ac_age}s src=$(basename "${ac_path:-none}")"  # info: log_line
  mark_attempt  # info: mark_attempt
  local rc=0  # info: set rc
  bash "$AC_ON" || rc=$?  # info: bash AC_ON
  if [[ "$rc" -eq 0 ]]; then  # info: if
    log_line "ok ac_on_finished reason=${trigger_reason} soc=${soc:-null} input_watts=${input_watts:-null} input_key=${input_key:-none}"  # info: log_line
    return 0  # info: return
  fi  # info: fi
  log_line "fail ac_on_exit=${rc} reason=${trigger_reason} soc=${soc:-null} input_watts=${input_watts:-null} input_key=${input_key:-none}"  # info: log_line
  return 1  # info: return
}  # info: main

main "$@"  # info: main
