#!/usr/bin/env bash
# ==============================================================================
# sync-all.sh — iterate enabled repos.conf → push-repo-once.sh
# ------------------------------------------------------------------------------
# Called by jobs.py github_sync_all (interval_sec=5).
# Post-pull stack reload is handled per repo by push-repo-once.sh (mark_code_pulled).
# ==============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/common.sh"
ensure_bak_root
mkdir -p "$BAK_ROOT/flags"

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

