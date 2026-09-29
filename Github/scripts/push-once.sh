#!/usr/bin/env bash
# ============================================================================
# github/scripts/push-once.sh — thin wrapper: push skills once
# ----------------------------------------------------------------------------
# WHAT: Calls push-repo-once.sh skills
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$HERE/push-repo-once.sh" skills
