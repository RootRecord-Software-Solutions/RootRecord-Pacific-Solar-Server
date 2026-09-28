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
set -u

# ====================================================
# SECTION: PATHS
# ====================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WEATHER_ROOT="$SKILLS_ROOT/weather"
ENTRY="$WEATHER_ROOT/scripts/run_poller.py"

LOG_DIR="/home/rootrecord/Database/WEATHER/Hawai'i/logs"
LOG_FILE="$LOG_DIR/weather-poller.log"

MATCH_PATTERN='weather/scripts/run_poller\.py'

# ====================================================
# SECTION: ALREADY RUNNING? -- idempotent, exit clean
# ====================================================
if pgrep -f "$MATCH_PATTERN" >/dev/null 2>&1; then
  echo "[ensure-weather-poller] already running -- nothing to do"
  exit 0
fi

if [[ ! -f "$ENTRY" ]]; then
  echo "[ensure-weather-poller] FAIL missing $ENTRY"
  exit 1
fi

# ====================================================
# SECTION: START (detached, survives this job's own exit)
# ====================================================
mkdir -p "$LOG_DIR"

echo "[ensure-weather-poller] starting -- entry=$ENTRY log=$LOG_FILE"
nohup setsid /home/rootrecord/.ollama/skills/weather/.venv/bin/python "$ENTRY" >>"$LOG_FILE" 2>&1 &
disown

sleep 1
if pgrep -f "$MATCH_PATTERN" >/dev/null 2>&1; then
  echo "[ensure-weather-poller] verify: weather poller is running"
  exit 0
fi

echo "[ensure-weather-poller] WARNING: process not seen right after start -- check $LOG_FILE"
exit 0
