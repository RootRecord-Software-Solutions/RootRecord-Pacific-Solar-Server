#!/usr/bin/env bash
# ==============================================================================
# # INFO — ensure exactly one council-relay.py (python) is running
# ------------------------------------------------------------------------------
# HOW TO ADD: do not add a second poller.
# Match MUST be ^python3 …council-relay.py — plain -f 'council-relay.py' false-positives
# on pgrep/bash that merely mention the name.
# Runtime log: /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/
# ==============================================================================
set -euo pipefail  # info: set
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set HERE
LOG="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/council-relay.log"  # info: set LOG
mkdir -p "$(dirname "$LOG")"  # info: mkdir

# ====================================================
# SECTION: function relay_up
# What it does: relay up.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
relay_up() {  # info: relay_up
  pgrep -f '^python3 .+/council-relay\.py' >/dev/null 2>&1  # info: pgrep
}  # info: command

# ====================================================
# SECTION: function legacy_up
# What it does: legacy up.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
legacy_up() {  # info: legacy_up
  pgrep -f '^python3 .+apps\.council' >/dev/null 2>&1  # info: pgrep
}  # info: command

if relay_up; then  # info: if
  echo "[ok] council-relay already running"  # info: echo
  exit 0  # info: exit
fi  # info: fi
if legacy_up; then  # info: if
  echo "[warn] legacy apps.council running — not starting relay (409 risk)"  # info: echo
  exit 0  # info: exit
fi  # info: fi
# Replies are opt-in: RR_RELAY_REPLIES=1 lets the relay infer+post; default 0 = quiet (poll/login only). 2026-09-29.
export RR_RELAY_REPLIES="${RR_RELAY_REPLIES:-0}"  # info: export
# Council chat stays on the NPU. RR_NPU_ONLY skips the Ollama fallback. RR_NPU_PERSONA loads
# Database/AI/FLM/Personas/<voice>.json (full system text). Image and speech stay off this process.
export RR_NPU_ONLY=1  # info: export
export RR_NPU_PERSONA=1  # info: export
# Strongest weight already installed on the NPU. The 1B default stays for other callers.
export FLM_MODEL="${FLM_MODEL:-llama3.2:3b}"  # info: export
# PYTHONUNBUFFERED: log lines appear immediately (2026-09-29; argv unchanged so the pgrep matches still work).
PYTHONUNBUFFERED=1 nohup python3 "$HERE/council-relay.py" >>"$LOG" 2>&1 &  # info: set PYTHONUNBUFFERED
pid=$!  # info: set pid
sleep 3  # info: sleep
if ! kill -0 "$pid" 2>/dev/null; then  # info: if
  echo "[FAIL] council-relay pid=$pid exited within 3s — last log: $(tail -n 1 "$LOG" 2>/dev/null | sed -E 's/[0-9]{6,}:[A-Za-z0-9_-]{25,}/[REDACTED]/g')"  # info: echo
  exit 1  # info: exit
fi  # info: fi
echo "[ok] council-relay started pid=$pid → $LOG"  # info: echo
