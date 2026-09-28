#!/usr/bin/env bash
# ==============================================================================
# ensure-network-globe-hawaii.sh — ensure the live Hawaii Network Globe SSH
# collector is running for the current RootRecord poller session.
# ------------------------------------------------------------------------------
# Called from jobs.py ON_BOOT. The collector is intentionally session-owned:
#   poller start -> collector/service start
#   poller stop/exit -> collector/service stop
# This avoids leaving the SSH stream alive after the operator closes the stack.
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -u

# ====================================================
# SECTION: CONFIG
# ====================================================
UNIT="network-globe-hawaii.service"

# ====================================================
# SECTION: ALREADY RUNNING? -- idempotent
# ====================================================
if systemctl --user is-active --quiet "$UNIT" 2>/dev/null; then
  echo "[ensure-network-globe-hawaii] already running -- nothing to do"
  exit 0
fi

# ====================================================
# SECTION: START
# ====================================================
echo "[ensure-network-globe-hawaii] starting $UNIT"
systemctl --user start "$UNIT" 2>&1 || {
  echo "[ensure-network-globe-hawaii] FAIL: could not start $UNIT"
  exit 1
}

sleep 1

if systemctl --user is-active --quiet "$UNIT" 2>/dev/null; then
  echo "[ensure-network-globe-hawaii] verify: $UNIT is active"
  exit 0
fi

echo "[ensure-network-globe-hawaii] WARNING: $UNIT did not become active"
systemctl --user status "$UNIT" --no-pager 2>&1 || true
exit 1
