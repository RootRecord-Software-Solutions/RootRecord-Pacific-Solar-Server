#!/usr/bin/env bash
# ==============================================================================
# npu-status.sh — read-only NPU / FLM / inference-lock status (Pacific copy)
# ------------------------------------------------------------------------------
# Copied 2026-09-29 from G2 ~/.ollama/skills/plumbing/scripts/npu-status.sh
# (G2 original KEPT, unchanged). Approved: Library 08-Ideas/2026-09-29-npu-status-pacific-copy.md.
# Re-pointed at the Pacific single-flight.sh (same folder) and the canonical
# plumbing state (2 - RootRecord-Database/Github/plumbing/state).
# Read-only: lists /dev/accel, dpkg packages, lock holder, flm serve / :52625.
# Never loads a model. FLM is ON DEMAND (run-infer.sh): when idle,
# "no flm serve, :52625 closed" is the NORMAL state.
# ==============================================================================
set -euo pipefail  # info: set
PLUMBING="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/System/scripts/plumbing"  # info: set PLUMBING
export RR_PLUMBING_STATE="${RR_PLUMBING_STATE:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Github/plumbing/state}"  # info: export
FLM_PORT="${FLM_PORT:-52625}"  # info: set FLM_PORT

echo "=== accel ==="  # info: echo
ls -la /dev/accel 2>&1 || echo "No data"  # info: ls
echo "=== xrt/npu packages ==="  # info: echo
dpkg -l 2>/dev/null | grep -iE '^ii\s+(libxrt|libze1|linux-firmware-amd-misc|python3-xrt)' || echo "No data"  # info: dpkg
echo "=== single-flight ==="  # info: echo
bash "$PLUMBING/single-flight.sh" status  # info: bash
echo "=== flm (on demand) ==="  # info: echo
flm_pids=$(pgrep -f '(^|/)flm serve' 2>/dev/null | tr '\n' ' ' | sed 's/ $//' || true)  # info: set flm_pids
if ss -ltn 2>/dev/null | grep -qE "[:.]${FLM_PORT}\b"; then port="open"; else port="closed"; fi  # info: if
if [[ -z "$flm_pids" && "$port" == "closed" ]]; then  # info: if
  echo "IDLE (on demand): no flm serve, :${FLM_PORT} closed — normal"  # info: echo
else  # info: else
  echo "ACTIVE: flm serve pid=${flm_pids:-none} :${FLM_PORT} ${port}"  # info: echo
fi  # info: fi
