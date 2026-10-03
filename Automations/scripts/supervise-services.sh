#!/usr/bin/env bash
# ==============================================================================
# supervise-services.sh — mid-session auto-recovery for council relay
# ------------------------------------------------------------------------------
# Approved: Library 08-Ideas/2026-09-29-weather-relay-auto-recovery.md (Alexander).
# Called from jobs.py EVERY_SECONDS job `service_supervisor` (every 300 s).
# jobs.py is read once at poller start, so this only runs after the NEXT poller start.
#
# For each service: detect with the SAME pgrep pattern its ensure script uses.
#   alive -> nothing (one "alive" line).
#   dead  -> run the SAME ensure script the ON_BOOT job uses (WARN line), with
#            backoff: at most MAX_RESTARTS per WINDOW_SEC (default 3 per 30 min).
#            A further death inside the window -> one BLOCKED line and no more
#            attempts until the service is seen alive again (block then clears).
#
# Modes:
#   (default)            act (respawn when dead, subject to backoff)
#   --dry-run | --check  detection only: never starts anything, never writes the
#                        live backoff state; prints alive / WOULD-RESPAWN / WOULD-BLOCK
#   --pretend-dead SVC   (test aid, dry-run only) treat SVC (relay) as dead
#   --state-dir DIR      backoff state dir (default $XDG_RUNTIME_DIR/rootrecord-supervisor;
#                        tmpfs, resets at reboot, never in git). In --dry-run, state is
#                        only recorded when --state-dir is given explicitly (tests).
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -u  # info: set

# ====================================================
# SECTION: CONFIG
# ====================================================
PACIFIC="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"  # info: set PACIFIC
MAX_RESTARTS="${RR_SUPERVISOR_MAX_RESTARTS:-3}"  # info: set MAX_RESTARTS
WINDOW_SEC="${RR_SUPERVISOR_WINDOW_SEC:-1800}"  # info: set WINDOW_SEC
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"  # info: set RUNTIME
[[ -d "$RUNTIME" && -w "$RUNTIME" ]] || RUNTIME="/tmp"  # info: command
STATE_DIR="$RUNTIME/rootrecord-supervisor"  # info: set STATE_DIR
STATE_EXPLICIT=0  # info: set STATE_EXPLICIT
DRY=0  # info: set DRY
PRETEND=""  # info: set PRETEND

# id | pgrep pattern (same as the ensure script) | ensure command (same as the ON_BOOT job) | cwd
SERVICES=(  # info: set SERVICES
  "relay|^python3 .+/council-relay\.py|$PACIFIC/Communications/telegram/scripts/ensure-relay.sh|$PACIFIC/Communications/telegram"  # info: command
)  # info: command

while [[ $# -gt 0 ]]; do
  case "$1" in  # info: case
    --dry-run|--check) DRY=1 ;;  # info: --dry-run
    --pretend-dead) PRETEND="${2:-}"; shift ;;  # info: --pretend-dead
    --state-dir) STATE_DIR="${2:?dir}"; STATE_EXPLICIT=1; shift ;;  # info: --state-dir
    -h|--help) sed -n '2,26p' "$0"; exit 0 ;;  # info: -h
    *) echo "[supervisor] unknown arg: $1" >&2; exit 2 ;;  # info: command
  esac  # info: esac
  shift  # info: shift
done  # info: done
if [[ -n "$PRETEND" && "$DRY" != 1 ]]; then  # info: if
  echo "[supervisor] --pretend-dead is only allowed with --dry-run" >&2; exit 2  # info: echo
fi  # info: fi
WRITE_STATE=1  # info: set WRITE_STATE
[[ "$DRY" == 1 && "$STATE_EXPLICIT" == 0 ]] && WRITE_STATE=0  # info: command
[[ "$WRITE_STATE" == 1 ]] && mkdir -p "$STATE_DIR"  # info: command

# ====================================================
# SECTION: HELPERS
# ====================================================
ts() { date -Iseconds; }  # info: ts

# restarts inside the window (epoch seconds, one per line)
recent_restarts() {  # info: recent_restarts
  local f="$STATE_DIR/$1.restarts" now cutoff  # info: local
  now=$(date +%s); cutoff=$((now - WINDOW_SEC))  # info: set now
  [[ -f "$f" ]] || { echo 0; return; }  # info: command
  awk -v c="$cutoff" '$1 >= c' "$f" | wc -l  # info: awk
}  # info: command

# ====================================================
# SECTION: function prune_restarts
# What it does: prune restarts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
prune_restarts() {  # info: prune_restarts
  local f="$STATE_DIR/$1.restarts" cutoff  # info: local
  cutoff=$(( $(date +%s) - WINDOW_SEC ))  # info: set cutoff
  [[ -f "$f" ]] || return 0  # info: command
  awk -v c="$cutoff" '$1 >= c' "$f" > "$f.tmp" && mv -f "$f.tmp" "$f"  # info: awk
}  # info: command

# ====================================================
# SECTION: CHECK EACH SERVICE
# ====================================================
mode="act"; [[ "$DRY" == 1 ]] && mode="dry-run"  # info: set mode
for row in "${SERVICES[@]}"; do  # info: for
  IFS='|' read -r sid pat ensure cwd <<<"$row"  # info: set IFS
  blocked="$STATE_DIR/$sid.blocked"  # info: set blocked
  pids=$(pgrep -f "$pat" 2>/dev/null | tr '\n' ' ' | sed 's/ $//')  # info: set pids
  if [[ "$PRETEND" == "$sid" ]]; then pids=""; fi  # info: if

  if [[ -n "$pids" ]]; then  # info: if
    echo "[supervisor] $sid alive pid=$pids ($mode)"  # info: echo
    if [[ "$WRITE_STATE" == 1 && -f "$blocked" ]]; then  # info: if
      rm -f "$blocked"; echo "[supervisor] $sid seen alive — BLOCKED cleared"  # info: rm
    fi  # info: fi
    [[ "$WRITE_STATE" == 1 ]] && prune_restarts "$sid"  # info: command
    continue  # info: continue
  fi  # info: fi

  if [[ -f "$blocked" ]]; then  # info: if
    echo "[supervisor] $sid DEAD — BLOCKED since $(cat "$blocked" 2>/dev/null) (no retry; restart the stack or start it by hand)"  # info: echo
    continue  # info: continue
  fi  # info: fi

  n=$(recent_restarts "$sid")  # info: set n
  if (( n >= MAX_RESTARTS )); then  # info: if
    if [[ "$DRY" == 1 ]]; then  # info: if
      echo "[supervisor] $sid DEAD — WOULD-BLOCK ($n restarts in last ${WINDOW_SEC}s >= $MAX_RESTARTS)"  # info: echo
    else  # info: else
      echo "[supervisor] BLOCKED $sid: $n restarts in last ${WINDOW_SEC}s (max $MAX_RESTARTS) — giving up until it is seen alive"  # info: echo
    fi  # info: fi
    [[ "$WRITE_STATE" == 1 ]] && ts > "$blocked"  # info: command
    continue  # info: continue
  fi  # info: fi

  if [[ "$DRY" == 1 ]]; then  # info: if
    echo "[supervisor] $sid DEAD — WOULD-RESPAWN via $(basename "$ensure") (attempt $((n + 1))/$MAX_RESTARTS in window)"  # info: echo
    [[ "$WRITE_STATE" == 1 ]] && date +%s >> "$STATE_DIR/$sid.restarts"  # info: command
    continue  # info: continue
  fi  # info: fi

  echo "[supervisor] WARN $sid dead — respawning via $(basename "$ensure") (attempt $((n + 1))/$MAX_RESTARTS in ${WINDOW_SEC}s)"  # info: echo
  date +%s >> "$STATE_DIR/$sid.restarts"  # info: date
  out=$(cd "$cwd" && bash "$ensure" 2>&1); rc=$?  # info: set out
  echo "[supervisor] $sid ensure rc=$rc: $(printf '%s' "$out" | tail -n 1 | sed -E 's/[0-9]{6,}:[A-Za-z0-9_-]{25,}/[REDACTED]/g')"  # info: echo
done  # info: done
exit 0  # info: exit
