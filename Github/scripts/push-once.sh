#!/usr/bin/env bash
# ============================================================================
# github/scripts/push-once.sh — thin wrapper: push skills once
# ----------------------------------------------------------------------------
# WHAT: Calls push-repo-once.sh skills
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail  # info: set
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set HERE
exec bash "$HERE/push-repo-once.sh" skills  # info: exec
