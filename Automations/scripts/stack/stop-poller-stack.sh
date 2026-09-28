#!/usr/bin/env bash
# ==============================================================================
# stop-poller-stack.sh — stop EVERY rootserver poller / cloudflared / unit process
# ------------------------------------------------------------------------------
# Used by: Ctrl-C / window close (poller-watch), rootserver-poller stop,
#          do-stack-reload.sh.
# Does NOT stop ava-ecoflow-ble (single BLE owner stays).
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -u

# ====================================================
# SECTION: CONFIG
# ====================================================
UNIT=rr-rootserver-poller.service
NETWORK_GLOBE_UNIT=network-globe-hawaii.service

# ====================================================
# SECTION: STOP UNIT
# ====================================================
# IMPORTANT: stop the systemd unit FIRST. This is a deliberate stop, so
# Restart=always will not resurrect the service. Killing the main PID first
# causes systemd to interpret the exit as a failure and restart the stack.
echo "[stop] stopping systemd unit ${UNIT}…"
systemctl --user stop "${UNIT}" 2>/dev/null || true

# The Hawaii Network Globe collector owns the live SSH stream. Stop its
# systemd unit before killing the collector so a Restart= policy cannot bring
# the SSH connection back after an intentional stack shutdown.
echo "[stop] stopping ${NETWORK_GLOBE_UNIT}…"
systemctl --user stop "${NETWORK_GLOBE_UNIT}" 2>/dev/null || true

# Kill anything still remaining in the service cgroup.
systemctl --user kill --kill-who=all "${UNIT}" 2>/dev/null || true

# ====================================================
# SECTION: MATCH KILLS (soft then hard)
# ====================================================
kill_match() {
  local pat="$1"
  local pids
  pids=$(pgrep -f "$pat" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "[stop] kill $pat -> $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
  fi
}

kill_match 'rootserver_poller\.py'
kill_match 'automations/bin/cloudflared'
kill_match 'automations/scripts/poller-watch\.py'
kill_match 'cam_server\.py'
kill_match 'coms/ssh/local-data-globe/collector\.js'
kill_match 'weather/scripts/run_poller\.py'

sleep 1

for pat in 'rootserver_poller\.py' 'automations/bin/cloudflared' 'automations/scripts/poller-watch\.py' 'cam_server\.py' 'coms/ssh/local-data-globe/collector\.js' 'weather/scripts/run_poller\.py'; do
  pids=$(pgrep -f "$pat" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "[stop] kill -9 $pat -> $pids"
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
  fi
done

echo "[stop] stack down."
