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
set -euo pipefail  # info: set
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"  # info: set RUNTIME
mkdir -p "$RUNTIME" 2>/dev/null || RUNTIME="/tmp"  # info: mkdir
LOCK="${RR_INFERENCE_LOCK:-$RUNTIME/rootrecord-inference.lock}"  # info: set LOCK
STATE_DIR="${RR_PLUMBING_STATE:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Github/plumbing/state}"  # info: set STATE_DIR
mkdir -p "$STATE_DIR"  # info: mkdir
HOLDER="$STATE_DIR/holder.txt"  # info: set HOLDER

cmd="${1:-status}"  # info: set cmd
shift || true  # info: shift

# ====================================================
# SECTION: function acquire
# What it does: acquire.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
acquire() {  # info: acquire
  local jid="${1:?job-id}"  # info: local
  exec 9>"$LOCK"  # info: exec
  if ! flock -n 9; then  # info: if
    echo "[busy] inference lock held: $(cat "$HOLDER" 2>/dev/null || echo unknown)"  # info: echo
    return 75  # info: return
  fi  # info: fi
  echo "job=$jid pid=$$ host=$(hostname) ts=$(date -Iseconds)" > "$HOLDER"  # info: echo
  echo "[ok] acquired $jid"  # info: echo
}  # info: command

# ====================================================
# SECTION: function release
# What it does: release.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
release() {  # info: release
  rm -f "$HOLDER" 2>/dev/null || true  # info: rm
  echo "[ok] released (lock frees when flock holder exits)"  # info: echo
}  # info: command

# ====================================================
# SECTION: function status
# What it does: status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
status() {  # info: status
  if [[ -f "$HOLDER" ]]; then  # info: if
    echo "BUSY $(cat "$HOLDER")"  # info: echo
  else  # info: else
    echo "IDLE"  # info: echo
  fi  # info: fi
  ls -la "$LOCK" 2>/dev/null || true  # info: ls
}  # info: command

# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
run() {  # info: run
  local jid="${1:?job-id}"  # info: local
  shift  # info: shift
  [[ "${1:-}" == "--" ]] && shift  # info: command
  exec 9>"$LOCK"  # info: exec
  if ! flock -n 9; then  # info: if
    echo "[busy] refuse parallel run. holder: $(cat "$HOLDER" 2>/dev/null || echo unknown)" >&2  # info: echo
    exit 75  # info: exit
  fi  # info: fi
  # Privacy (2026-09-29 g3-voice-reports2): holder.txt = metadata only, never argv (argv carried prompt text).
  # prompt_chars comes from RR_PROMPT_CHARS (callers set it; -1 = unknown). Banner -> stderr, never into replies.
  local c="" a  # info: local
  for a in "$@"; do case "$a" in env|nice|-n|[0-9]*|*=*) ;; *) c="${a##*/}"; break ;; esac; done
  echo "job=$jid caller=${RR_CALLER:-$(cat "/proc/$PPID/comm" 2>/dev/null || echo unknown)} pid=$$ ts=$(date -Iseconds) cmd=${c:-?} prompt_chars=${RR_PROMPT_CHARS:--1}" > "$HOLDER"  # info: echo
  echo "[ok] single-flight RUN $jid" >&2  # info: echo
  set +e  # info: set
  "$@"  # info: command
  rc=$?  # info: set rc
  set -e  # info: set
  rm -f "$HOLDER"  # info: rm
  exit "$rc"  # info: exit
}  # info: command

case "$cmd" in  # info: case
  acquire) acquire "${1:-}" ;;  # info: acquire
  release) release ;;  # info: release
  status) status ;;  # info: status
  run) run "$@" ;;  # info: run
  *) echo "usage: $0 acquire|release|status|run <job-id> -- <cmd…>"; exit 2 ;;  # info: command
esac  # info: esac
