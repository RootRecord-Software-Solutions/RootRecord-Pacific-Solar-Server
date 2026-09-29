#!/usr/bin/env bash
# ============================================================================
# github/scripts/setup-all-remotes.sh — ensure remotes for every enabled repo
# ----------------------------------------------------------------------------
# WHAT: Loop repos.conf and run setup-remote.sh for each enabled id.
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/common.sh"
ensure_bak_root
while IFS=$'\t' read -r id enabled mode local_path slug remote_name; do
  [[ "$id" =~ ^#.*$ || -z "${id:-}" ]] && continue
  [[ "$enabled" == "1" ]] || continue
  bash "$HERE/setup-remote.sh" "$id" || true
done < <(grep -v '^#' "$REPOS_CONF" | grep -v '^[[:space:]]*$')
echo "[ok] setup-all-remotes done"
