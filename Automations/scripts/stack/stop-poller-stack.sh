#!/usr/bin/env bash
# ==============================================================================
# stop-poller-stack.sh — stop EVERY rootserver poller / cloudflared / unit process
# ------------------------------------------------------------------------------
# Used by: Ctrl-C / window close (poller-watch), rootserver-poller stop,
#          do-stack-reload.sh.
# Does NOT stop ava-ecoflow-ble (single BLE owner stays).
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -u  # info: set

# ====================================================
# SECTION: CONFIG
# ====================================================
UNIT=rr-rootserver-poller.service  # info: set UNIT
NETWORK_GLOBE_UNIT=network-globe-hawaii.service  # info: set NETWORK_GLOBE_UNIT

# ====================================================
# SECTION: STOP UNIT
# ====================================================
# IMPORTANT: stop the systemd unit FIRST. This is a deliberate stop, so
# Restart=always will not resurrect the service. Killing the main PID first
# causes systemd to interpret the exit as a failure and restart the stack.
echo "[stop] stopping systemd unit ${UNIT}…"  # info: echo
systemctl --user stop "${UNIT}" 2>/dev/null || true  # info: systemctl

# The Hawaii Network Globe collector owns the live SSH stream. Stop its
# systemd unit before killing the collector so a Restart= policy cannot bring
# the SSH connection back after an intentional stack shutdown.
echo "[stop] stopping ${NETWORK_GLOBE_UNIT}…"  # info: echo
systemctl --user stop "${NETWORK_GLOBE_UNIT}" 2>/dev/null || true  # info: systemctl

# Kill anything still remaining in the service cgroup.
systemctl --user kill --kill-who=all "${UNIT}" 2>/dev/null || true  # info: systemctl

# ====================================================
# SECTION: MATCH KILLS (soft then hard)
# ====================================================
kill_match() {  # info: kill_match
  local pat="$1"  # info: local
  local pids  # info: local
  pids=$(pgrep -f "$pat" 2>/dev/null || true)  # info: set pids
  if [ -n "$pids" ]; then  # info: if
    echo "[stop] kill $pat -> $pids"  # info: echo
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true  # info: kill
  fi  # info: fi
}  # info: command

kill_match 'rootserver_poller\.py'  # info: kill_match
kill_match 'cloudflared'  # info: kill_match
kill_match 'poller-watch\.py'  # info: kill_match
kill_match 'cam_server\.py'  # info: kill_match
kill_match 'coms/ssh/local-data-globe/collector\.js'  # info: kill_match

sleep 1  # info: sleep

for pat in 'rootserver_poller\.py' 'cloudflared' 'poller-watch\.py' 'cam_server\.py' 'coms/ssh/local-data-globe/collector\.js'; do  # info: for
  pids=$(pgrep -f "$pat" 2>/dev/null || true)  # info: set pids
  if [ -n "$pids" ]; then  # info: if
    echo "[stop] kill -9 $pat -> $pids"  # info: echo
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true  # info: kill
  fi  # info: fi
done  # info: done

echo "[stop] stack down."  # info: echo
