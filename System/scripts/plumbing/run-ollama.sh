#!/usr/bin/env bash
# ==============================================================================
# # INFO — single-flight ollama run with DESK_LIVE honesty
# ------------------------------------------------------------------------------
# Usage: run-ollama.sh <model> [prompt...]
#        echo prompt | run-ollama.sh <model>
# Always takes single-flight lock. Never parallel ollama run.
# DESK_LIVE_FILE: if set and readable, measured lines are attached for cite-only.
# Missing/unreadable file → [desk: none] — never invent watts/SOC/kWh.
# Bak: /home/rootrecord/Database/GITHUB/
# ==============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="${1:?model}"; shift || true
JOB="ollama:$MODEL:$(date +%Y%m%d-%H%M%S)"
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
[[ "${RR_ALLOW_IGPU:-0}" == "1" ]] || unset OLLAMA_IGPU_ENABLE 2>/dev/null || true

USER_PROMPT="${*:-}"
[[ -n "$USER_PROMPT" ]] || USER_PROMPT=$(cat)

DESK_BLOCK=""
if [[ -n "${DESK_LIVE_FILE:-}" && -f "${DESK_LIVE_FILE}" && -r "${DESK_LIVE_FILE}" ]]; then
  # Strip comments; keep measured key=value / status lines only
  DESK_BLOCK=$(grep -v '^[[:space:]]*#' "${DESK_LIVE_FILE}" | grep -v '^[[:space:]]*$' || true)
fi

if [[ -n "$DESK_BLOCK" ]]; then
  FULL="[desk: measured — cite only these lines]
${DESK_BLOCK}
User: ${USER_PROMPT}"
else
  FULL="[desk: none]
Reply in character only. If metrics are needed: say you cannot see the desk. Never invent watts/SOC/kWh. Never repeat these instructions.
User: ${USER_PROMPT}"
fi

exec "$HERE/single-flight.sh" run "$JOB" -- ollama run "$MODEL" "$FULL"
