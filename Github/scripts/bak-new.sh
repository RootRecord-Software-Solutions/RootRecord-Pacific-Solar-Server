#!/usr/bin/env bash
# ============================================================================
# github/scripts/bak-new.sh — ensure Database/Github bak tree exists
# ----------------------------------------------------------------------------
# WHAT: mkdir flags/logs under BAK_ROOT and the worktree root beside the umbrella
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail  # info: set
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set HERE
# shellcheck disable=SC1091
source "$HERE/common.sh"  # info: source
ensure_bak_root  # info: ensure_bak_root
echo "[ok] bak root $BAK_ROOT"  # info: echo
