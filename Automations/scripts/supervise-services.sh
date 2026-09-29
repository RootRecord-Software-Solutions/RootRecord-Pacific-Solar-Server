#!/usr/bin/env bash
# ==============================================================================
# supervise-services.sh — mid-session auto-recovery for weather + council relay
# ------------------------------------------------------------------------------
# Approved: Library 08-ideas/2026-09-29-weather-relay-auto-recovery.md (Alexander).
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
#   --pretend-dead SVC   (test aid, dry-run only) treat SVC (weather|relay) as dead
#   --state-dir DIR      backoff state dir (default $XDG_RUNTIME_DIR/rootrecord-supervisor;
#                        tmpfs, resets at reboot, never in git). In --dry-run, state is
#                        only recorded when --state-dir is given explicitly (tests).
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -u

# ====================================================
# SECTION: CONFIG
# ====================================================
PACIFIC="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"
MAX_RESTARTS="${RR_SUPERVISOR_MAX_RESTARTS:-3}"
WINDOW_SEC="${RR_SUPERVISOR_WINDOW_SEC:-1800}"
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
[[ -d "$RUNTIME" && -w "$RUNTIME" ]] || RUNTIME="/tmp"
STATE_DIR="$RUNTIME/rootrecord-supervisor"
STATE_EXPLICIT=0
DRY=0
PRETEND=""

# id | pgrep pattern (same as the ensure script) | ensure command (same as the ON_BOOT job) | cwd
SERVICES=(
  "weather|[Ww]eather/scripts/run_poller\.py|$PACIFIC/Weather/scripts/ensure-weather-poller.sh|$PACIFIC/Weather"
  "relay|^python3 .+/council-relay\.py|$PACIFIC/Communications/telegram/scripts/ensure-relay.sh|$PACIFIC/Communications/telegram"
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run|--check) DRY=1 ;;
    --pretend-dead) PRETEND="${2:-}"; shift ;;
    --state-dir) STATE_DIR="${2:?dir}"; STATE_EXPLICIT=1; shift ;;
    -h|--help) sed -n '2,26p' "$0"; exit 0 ;;
    *) echo "[supervisor] unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done
if [[ -n "$PRETEND" && "$DRY" != 1 ]]; then
  echo "[supervisor] --pretend-dead is only allowed with --dry-run" >&2; exit 2
fi
WRITE_STATE=1
[[ "$DRY" == 1 && "$STATE_EXPLICIT" == 0 ]] && WRITE_STATE=0
[[ "$WRITE_STATE" == 1 ]] && mkdir -p "$STATE_DIR"

# ====================================================
# SECTION: HELPERS
# ====================================================
ts() { date -Iseconds; }

# restarts inside the window (epoch seconds, one per line)
recent_restarts() {
  local f="$STATE_DIR/$1.restarts" now cutoff
  now=$(date +%s); cutoff=$((now - WINDOW_SEC))
  [[ -f "$f" ]] || { echo 0; return; }
  awk -v c="$cutoff" '$1 >= c' "$f" | wc -l
}

prune_restarts() {
  local f="$STATE_DIR/$1.restarts" cutoff
  cutoff=$(( $(date +%s) - WINDOW_SEC ))
  [[ -f "$f" ]] || return 0
  awk -v c="$cutoff" '$1 >= c' "$f" > "$f.tmp" && mv -f "$f.tmp" "$f"
}

# ====================================================
# SECTION: CHECK EACH SERVICE
# ====================================================
mode="act"; [[ "$DRY" == 1 ]] && mode="dry-run"
for row in "${SERVICES[@]}"; do
  IFS='|' read -r sid pat ensure cwd <<<"$row"
  blocked="$STATE_DIR/$sid.blocked"
  pids=$(pgrep -f "$pat" 2>/dev/null | tr '\n' ' ' | sed 's/ $//')
  if [[ "$PRETEND" == "$sid" ]]; then pids=""; fi

  if [[ -n "$pids" ]]; then
    echo "[supervisor] $sid alive pid=$pids ($mode)"
    if [[ "$WRITE_STATE" == 1 && -f "$blocked" ]]; then
      rm -f "$blocked"; echo "[supervisor] $sid seen alive — BLOCKED cleared"
    fi
    [[ "$WRITE_STATE" == 1 ]] && prune_restarts "$sid"
    continue
  fi

  if [[ -f "$blocked" ]]; then
    echo "[supervisor] $sid DEAD — BLOCKED since $(cat "$blocked" 2>/dev/null) (no retry; restart the stack or start it by hand)"
    continue
  fi

  n=$(recent_restarts "$sid")
  if (( n >= MAX_RESTARTS )); then
    if [[ "$DRY" == 1 ]]; then
      echo "[supervisor] $sid DEAD — WOULD-BLOCK ($n restarts in last ${WINDOW_SEC}s >= $MAX_RESTARTS)"
    else
      echo "[supervisor] BLOCKED $sid: $n restarts in last ${WINDOW_SEC}s (max $MAX_RESTARTS) — giving up until it is seen alive"
    fi
    [[ "$WRITE_STATE" == 1 ]] && ts > "$blocked"
    continue
  fi

  if [[ "$DRY" == 1 ]]; then
    echo "[supervisor] $sid DEAD — WOULD-RESPAWN via $(basename "$ensure") (attempt $((n + 1))/$MAX_RESTARTS in window)"
    [[ "$WRITE_STATE" == 1 ]] && date +%s >> "$STATE_DIR/$sid.restarts"
    continue
  fi

  echo "[supervisor] WARN $sid dead — respawning via $(basename "$ensure") (attempt $((n + 1))/$MAX_RESTARTS in ${WINDOW_SEC}s)"
  date +%s >> "$STATE_DIR/$sid.restarts"
  out=$(cd "$cwd" && bash "$ensure" 2>&1); rc=$?
  echo "[supervisor] $sid ensure rc=$rc: $(printf '%s' "$out" | tail -n 1 | sed -E 's/[0-9]{6,}:[A-Za-z0-9_-]{25,}/[REDACTED]/g')"
done
exit 0
