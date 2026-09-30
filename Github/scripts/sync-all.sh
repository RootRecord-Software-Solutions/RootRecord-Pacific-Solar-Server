#!/usr/bin/env bash
# ==============================================================================
# sync-all.sh — iterate enabled repos.conf → push-repo-once.sh
# ------------------------------------------------------------------------------
# Called by jobs.py github_sync_all (interval_sec=5).
# Post-pull stack reload is handled per repo by push-repo-once.sh (mark_code_pulled).
# ==============================================================================
set -euo pipefail  # info: set

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set HERE
# shellcheck disable=SC1091
source "$HERE/common.sh"  # info: source
ensure_bak_root  # info: ensure_bak_root
mkdir -p "$BAK_ROOT/flags"  # info: mkdir

while IFS=$'\t' read -r id enabled mode local_path slug remote_name; do  # info: while
  [[ "$id" =~ ^#.*$ || -z "${id:-}" ]] && continue
  [[ "$enabled" == "1" ]] || continue  # info: command
  success=0  # info: set success
  for attempt in 1 2 3; do  # info: for
    if bash "$HERE/push-repo-once.sh" "$id"; then  # info: if
      success=1  # info: set success
      break  # info: break
    fi  # info: fi
    echo "↻ [$id] sync retry $attempt/3"  # info: echo
    sleep 2  # info: sleep
  done  # info: done
  (( success )) || echo "✗ [$id] sync failed after 3 attempts (continuing)"  # info: command
done < <(grep -v '^#' "$REPOS_CONF" | grep -v '^[[:space:]]*$')

