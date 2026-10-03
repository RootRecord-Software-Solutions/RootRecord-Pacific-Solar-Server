#!/usr/bin/env bash
# Force AC ON for one pack when it is on BLE. Never reads cloud-fallback. Never forces AC off.
set -euo pipefail
ALIAS="${1:-}"
DRY=0
if [[ "${2:-}" == "--dry-run" ]]; then DRY=1; fi
if [[ "$ALIAS" != "river2pro" && "$ALIAS" != "delta2" ]]; then
  echo "usage: $0 river2pro|delta2 [--dry-run]" >&2
  exit 2
fi
ROOT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy"
DB="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy"
SIGHT="$DB/state/ble-sight-${ALIAS}.json"
SAMPLES="$DB/samples"
LOG="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Energy/${ALIAS}-ac-force.log"
if [[ "$ALIAS" == "river2pro" ]]; then
  LOG="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Energy/river2pro-ac-recover.log"
fi
mkdir -p "$(dirname "$LOG")"
AC_ON="$ROOT/scripts/actions/${ALIAS}-ac-on.sh"
FRESH=180
log_line() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') ${ALIAS}-ac-force: $*" | tee -a "$LOG"; }
IFS=$'\t' read -r seen sage detail < <(python3 - "$SIGHT" << 'PY'
import json, os, sys, time
path = sys.argv[1]
if not os.path.isfile(path):
    print("0\t999999\tmissing")
    raise SystemExit
data = json.load(open(path, encoding="utf-8"))
age = max(0, int(time.time() - float(data.get("at_epoch") or 0)))
print(f"{1 if data.get('seen') else 0}\t{age}\t{data.get('detail') or ''}")
PY
)
IFS=$'\t' read -r ble_age ac_flag ac_out < <(python3 - "$SAMPLES" "$ALIAS" << 'PY'
import glob, json, os, sys, time
samples, alias = sys.argv[1], sys.argv[2]
files = glob.glob(os.path.join(samples, f"read-{alias}-*.json"))
if not files:
    print("999999\tnone\t")
    raise SystemExit
path = max(files, key=os.path.getmtime)
age = max(0, int(time.time() - os.path.getmtime(path)))
try:
    data = json.load(open(path, encoding="utf-8"))
except Exception:
    print(f"{age}\tbad\t")
    raise SystemExit
if data.get("source") != "ble":
    print(f"{age}\tnot_ble\t")
    raise SystemExit
fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
flag = fields.get("ac_ports")
name = "true" if flag is True else "false" if flag is False else "null"
out = fields.get("ac_output_power")
print(f"{age}\t{name}\t{'' if out is None else out}")
PY
)
in_range=0
if [[ "$ble_age" -le "$FRESH" && "$ac_flag" != "not_ble" && "$ac_flag" != "bad" && "$ac_flag" != "none" ]]; then in_range=1; fi
if [[ "$in_range" -eq 0 ]]; then
  if [[ "$seen" == "1" && "$sage" -le "$FRESH" ]]; then
    log_line "no-op sample_stale sight_age=${sage}s ble_age=${ble_age}s ac_ports=${ac_flag} — reader owns the radio until a fresh BLE sample"
    exit 0
  fi
  log_line "no-op out_of_range sight=${seen} sight_age=${sage}s ble_age=${ble_age}s ac_ports=${ac_flag} detail=${detail}"
  exit 0
fi
if [[ "$ble_age" -le "$FRESH" && "$ac_flag" == "true" ]]; then
  log_line "no-op ble_ac_already_on ble_age=${ble_age}s ac_out=${ac_out:-null} sight_age=${sage}s"
  exit 0
fi
if [[ "$DRY" -eq 1 ]]; then
  log_line "dry-run WOULD_RUN_ac_on ble_age=${ble_age}s ac_ports=${ac_flag} sight=${seen} sight_age=${sage}s"
  exit 0
fi
exec 9>/tmp/ecoflow-ble.lock
if ! flock -n 9; then
  log_line "no-op ble_busy"
  exit 0
fi
log_line "run ac_on reason=in_range ble_age=${ble_age}s ac_ports=${ac_flag} sight=${seen} sight_age=${sage}s"
rc=0
bash "$AC_ON" || rc=$?
if [[ "$rc" -eq 0 ]]; then
  log_line "ok ac_on_finished"
  exit 0
fi
log_line "fail ac_on_exit=${rc}"
exit 1
