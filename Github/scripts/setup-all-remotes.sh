#!/usr/bin/env bash
# ============================================================================
# github/scripts/setup-all-remotes.sh — ensure remotes for every enabled repo
# ----------------------------------------------------------------------------
# WHAT: Loop repos.conf and run setup-remote.sh for each enabled id.
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail  # info: set
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set HERE
# shellcheck disable=SC1091
source "$HERE/common.sh"  # info: source
ensure_bak_root  # info: ensure_bak_root
while IFS=$'\t' read -r id enabled mode local_path slug remote_name; do  # info: while
  [[ "$id" =~ ^#.*$ || -z "${id:-}" ]] && continue
  [[ "$enabled" == "1" ]] || continue  # info: command
  bash "$HERE/setup-remote.sh" "$id" || true  # info: bash
done < <(grep -v '^#' "$REPOS_CONF" | grep -v '^[[:space:]]*$')
echo "[ok] setup-all-remotes done"  # info: echo
