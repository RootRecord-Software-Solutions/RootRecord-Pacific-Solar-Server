#!/usr/bin/env bash
# ==============================================================================
# # INFO — ensure exactly one council-relay.py (python) is running
# ------------------------------------------------------------------------------
# HOW TO ADD: do not add a second poller.
# Match MUST be ^python3 …council-relay.py — plain -f 'council-relay.py' false-positives
# on pgrep/bash that merely mention the name.
# Bak: /home/rootrecord/Database/GITHUB/
# ==============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG=/home/rootrecord/Database/GITHUB/logs/council-relay.log
mkdir -p "$(dirname "$LOG")"

relay_up() {
  pgrep -f '^python3 .+/council-relay\.py' >/dev/null 2>&1
}

legacy_up() {
  pgrep -f '^python3 .+apps\.council' >/dev/null 2>&1
}

if relay_up; then
  echo "[ok] council-relay already running"
  exit 0
fi
if legacy_up; then
  echo "[warn] legacy apps.council running — not starting relay (409 risk)"
  exit 0
fi
nohup python3 "$HERE/council-relay.py" >>"$LOG" 2>&1 &
echo "[ok] council-relay started pid=$! → $LOG"
