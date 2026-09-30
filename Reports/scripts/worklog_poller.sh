# ==============================================================================
# FILE: Reports/scripts/worklog_poller.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Runs until killed. Logging only while this process lives. Full-home scan ~90s interval.
# Prefer jobs.py worklog_scan (Pacific) over a second long-lived poller.
set -euo pipefail  # info: set
DIR="$(cd "$(dirname "$0")" && pwd)"  # info: set DIR
# shellcheck source=/dev/null
source "$DIR/worklog_lib.sh"  # info: source
ensure_dirs  # info: ensure_dirs
if [[ -f "$PID_FILE" ]]; then  # info: if
  old=$(cat "$PID_FILE" || true)  # info: set old
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then  # info: if
    echo "Already running pid=$old" >&2  # info: echo
    exit 1  # info: exit
  fi  # info: fi
fi  # info: fi
echo $$ > "$PID_FILE"  # info: echo
trap 'rm -f "$PID_FILE"; exit 0' INT TERM EXIT  # info: trap
echo "worklog poller start pid=$$ scope=$HOME_ROOT (scan every 90s)"  # info: echo
while true; do  # info: while
  scan_once || true  # info: scan_once
  sleep 90  # info: sleep
done  # info: done
