#!/usr/bin/env bash
# ==============================================================================
# sync-all.sh — iterate enabled repos.conf → push-repo-once.sh
# ------------------------------------------------------------------------------
# Called by jobs.py github_sync_all (~300s).
# After Pacific (or legacy skills) code is pulled, schedules full poller stack reload.
# ==============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/common.sh"
ensure_bak_root
mkdir -p "$BAK_ROOT/flags"

RELOAD_SCRIPT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/scripts/stack/schedule-stack-reload.sh"

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

if [[ -f "$BAK_ROOT/flags/reload-poller-stack" ]]; then
  if [[ -f "$RELOAD_SCRIPT" ]]; then
    echo "↻ reload flag present — scheduling full poller stack reload"
    bash "$RELOAD_SCRIPT" || echo "⚠ schedule-stack-reload failed (flag left for next cycle)"
  else
    echo "⚠ reload flag set but missing file: $RELOAD_SCRIPT"
  fi
fi
