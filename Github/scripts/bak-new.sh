#!/usr/bin/env bash
# ============================================================================
# github/scripts/bak-new.sh — ensure Database/GITHUB bak tree exists
# ----------------------------------------------------------------------------
# WHAT: mkdir flags/worktrees/logs under BAK_ROOT
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/common.sh"
ensure_bak_root
echo "[ok] bak root $BAK_ROOT"
