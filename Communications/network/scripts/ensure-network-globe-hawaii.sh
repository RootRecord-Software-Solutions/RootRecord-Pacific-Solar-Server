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
set -u  # info: set

# ====================================================
# SECTION: CONFIG
# ====================================================
UNIT="network-globe-hawaii.service"  # info: set UNIT

# ====================================================
# SECTION: ALREADY RUNNING? -- idempotent
# ====================================================
if systemctl --user is-active --quiet "$UNIT" 2>/dev/null; then  # info: if
  echo "[ensure-network-globe-hawaii] already running -- nothing to do"  # info: echo
  exit 0  # info: exit
fi  # info: fi

# ====================================================
# SECTION: START
# ====================================================
echo "[ensure-network-globe-hawaii] starting $UNIT"  # info: echo
systemctl --user start "$UNIT" 2>&1 || {  # info: systemctl
  echo "[ensure-network-globe-hawaii] FAIL: could not start $UNIT"  # info: echo
  exit 1  # info: exit
}  # info: command

sleep 1  # info: sleep

if systemctl --user is-active --quiet "$UNIT" 2>/dev/null; then  # info: if
  echo "[ensure-network-globe-hawaii] verify: $UNIT is active"  # info: echo
  exit 0  # info: exit
fi  # info: fi

echo "[ensure-network-globe-hawaii] WARNING: $UNIT did not become active"  # info: echo
systemctl --user status "$UNIT" --no-pager 2>&1 || true  # info: systemctl
exit 1  # info: exit
