#!/usr/bin/env bash
# ============================================================================
# github/scripts/poll-and-push.sh — legacy one-shot sync-all wrapper
# ----------------------------------------------------------------------------
# WHAT: Prefer poller github_sync_all; this is a manual fallback only.
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$HERE/sync-all.sh"
