#!/usr/bin/env bash
# ==============================================================================
# single-flight.sh — acquire RootRecord inference lock or fail
# Usage:
#   single-flight.sh acquire <job-id>     # exit 0 if got lock, 75 if busy
#   single-flight.sh release <job-id>     # release if we own it
#   single-flight.sh status               # print holder / idle
#   single-flight.sh run <job-id> -- cmd… # hold lock for duration of cmd
# MUST: only one model/agent run at a time on this host.
# ==============================================================================
set -euo pipefail
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
mkdir -p "$RUNTIME" 2>/dev/null || RUNTIME="/tmp"
LOCK="${RR_INFERENCE_LOCK:-$RUNTIME/rootrecord-inference.lock}"
STATE_DIR="${RR_PLUMBING_STATE:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Github/plumbing/state}"
mkdir -p "$STATE_DIR"
HOLDER="$STATE_DIR/holder.txt"

cmd="${1:-status}"
shift || true

acquire() {
  local jid="${1:?job-id}"
  exec 9>"$LOCK"
  if ! flock -n 9; then
    echo "[busy] inference lock held: $(cat "$HOLDER" 2>/dev/null || echo unknown)"
    return 75
  fi
  echo "job=$jid pid=$$ host=$(hostname) ts=$(date -Iseconds)" > "$HOLDER"
  echo "[ok] acquired $jid"
}

release() {
  rm -f "$HOLDER" 2>/dev/null || true
  echo "[ok] released (lock frees when flock holder exits)"
}

status() {
  if [[ -f "$HOLDER" ]]; then
    echo "BUSY $(cat "$HOLDER")"
  else
    echo "IDLE"
  fi
  ls -la "$LOCK" 2>/dev/null || true
}

run() {
  local jid="${1:?job-id}"
  shift
  [[ "${1:-}" == "--" ]] && shift
  exec 9>"$LOCK"
  if ! flock -n 9; then
    echo "[busy] refuse parallel run. holder: $(cat "$HOLDER" 2>/dev/null || echo unknown)" >&2
    exit 75
  fi
  echo "job=$jid pid=$$ ts=$(date -Iseconds) cmd=$*" > "$HOLDER"
  echo "[ok] single-flight RUN $jid"
  set +e
  "$@"
  rc=$?
  set -e
  rm -f "$HOLDER"
  exit "$rc"
}

case "$cmd" in
  acquire) acquire "${1:-}" ;;
  release) release ;;
  status) status ;;
  run) run "$@" ;;
  *) echo "usage: $0 acquire|release|status|run <job-id> -- <cmd…>"; exit 2 ;;
esac
