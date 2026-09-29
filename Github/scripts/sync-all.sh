#!/usr/bin/env bash
# ==============================================================================
# sync-all.sh — iterate enabled repos.conf → push-repo-once.sh
# ------------------------------------------------------------------------------
# Called by automations jobs.py  github_sync_all  (every ~300s).
# After skills code is pulled, schedules full poller stack reload.
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -euo pipefail

# ====================================================
# SECTION: SETUP
# ====================================================
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/common.sh"
ensure_bak_root
mkdir -p "$BAK_ROOT/flags"

RELOAD_SCRIPT="/home/rootrecord/.ollama/skills/automations/scripts/schedule-stack-reload.sh"

# ====================================================
# SECTION: SYNC EACH ENABLED REPO
# ====================================================
while IFS=$'\t' read -r id enabled mode local_path slug remote_name; do
  [[ "$id" =~ ^#.*$ || -z "${id:-}" ]] && continue
  [[ "$enabled" == "1" ]] || continue
  success=0
  for attempt in 1 2 3; do
    if bash "$HERE/push-repo-once.sh" "$id"; then
      success=1
      break
    fi
    echo "↻ [$id] sync retry $attempt/3"
    sleep 2
  done
  (( success )) || echo "✗ [$id] sync failed after 3 attempts (continuing)"
done < <(grep -v '^#' "$REPOS_CONF" | grep -v '^[[:space:]]*$')

# ====================================================
# SECTION: STACK RELOAD (if skills code was pulled)
# Always invoke via bash (file may not be +x after git pull).
# ====================================================
if [[ -f "$BAK_ROOT/flags/reload-poller-stack" ]]; then
  if [[ -f "$RELOAD_SCRIPT" ]]; then
    echo "↻ reload flag present — scheduling full poller stack reload"
    bash "$RELOAD_SCRIPT" || echo "⚠ schedule-stack-reload failed (flag left for next cycle)"
  else
    echo "⚠ reload flag set but missing file: $RELOAD_SCRIPT"
  fi
fi
