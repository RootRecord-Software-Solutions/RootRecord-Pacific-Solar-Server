#!/usr/bin/env bash
# ==============================================================================
# ensure-weather-poller.sh — check-and-start launcher for the weather skill's
# scheduler daemon (weather/scripts/run_poller.py)
# ------------------------------------------------------------------------------
# Called from jobs.py ON_BOOT (priority 8). Same check-and-start pattern as
# the other persistent services in this stack (a-eyes cam server,
# council-relay, Ollama, FLM): if the process is already up, do nothing; if
# not, start it detached and return quickly. The job dispatcher runs this
# to completion with a timeout (see jobs.py) -- it does NOT run the daemon
# itself, since that loop never returns.
#
# The daemon fetches every tier once immediately on start (all fetch
# modules + hurricanes), then keeps its own internal per-tier cadence
# forever -- see weather/scheduler/run_cycle.py's run_forever().
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -u  # info: set

# ====================================================
# SECTION: PATHS
# ====================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"  # info: set SCRIPT_DIR
SKILLS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"  # info: set SKILLS_ROOT
WEATHER_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"  # Pacific Weather/ (imported from G2 2026-09-29)
ENTRY="$WEATHER_ROOT/scripts/run_poller.py"  # info: set ENTRY

DEFAULT_LOG_DIR="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Weather/Hawai'i/logs"  # info: set DEFAULT_LOG_DIR
LOG_DIR="${WEATHER_LOG_DIR:-$DEFAULT_LOG_DIR}"  # info: set LOG_DIR
LOG_FILE="$LOG_DIR/weather-poller.log"  # info: set LOG_FILE

MATCH_PATTERN='[Ww]eather/scripts/run_poller\.py'  # also sees a G2 instance (no parallel owners)

# ====================================================
# SECTION: ALREADY RUNNING? -- idempotent, exit clean
# ====================================================
if pgrep -f "$MATCH_PATTERN" >/dev/null 2>&1; then  # info: if
  echo "[ensure-weather-poller] already running -- nothing to do"  # info: echo
  exit 0  # info: exit
fi  # info: fi

if [[ ! -f "$ENTRY" ]]; then  # info: if
  echo "[ensure-weather-poller] FAIL missing $ENTRY"  # info: echo
  exit 1  # info: exit
fi  # info: fi

# ====================================================
# SECTION: START (detached, survives this job's own exit)
# ====================================================
mkdir -p "$LOG_DIR"  # info: mkdir

echo "[ensure-weather-poller] starting -- entry=$ENTRY log=$LOG_FILE"  # info: echo
PY="${WEATHER_PYTHON:-$WEATHER_ROOT/.venv/bin/python}"  # info: set PY
nohup setsid "$PY" "$ENTRY" >>"$LOG_FILE" 2>&1 &  # info: nohup
disown  # info: disown

sleep 1  # info: sleep
if pgrep -f "$MATCH_PATTERN" >/dev/null 2>&1; then  # info: if
  echo "[ensure-weather-poller] verify: weather poller is running"  # info: echo
  exit 0  # info: exit
fi  # info: fi

echo "[ensure-weather-poller] WARNING: process not seen right after start -- check $LOG_FILE"  # info: echo
exit 0  # info: exit
