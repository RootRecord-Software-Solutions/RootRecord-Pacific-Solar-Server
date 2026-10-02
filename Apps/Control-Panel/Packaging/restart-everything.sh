# ==============================================================================
# FILE: Apps/Control-Panel/Packaging/restart-everything.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Restart the RootRecord desk stack, then Root Monitor itself.
# Root Monitor starts this in a new session after a confirm click, so this
# script keeps running after the window closes.
# Restarts: poller stack (poller, tunnel, cameras, weather, relay),
# Hawaii network globe, EcoFlow BLE owner, AWS fetch tunnel, then this window.
# Leaves Ollama, GNOME, and the laptop running.
set +e  # info: set

HERE="$(cd "$(dirname "$0")" && pwd)"  # info: set HERE
REPO="$(cd "$HERE/../.." && pwd)"  # info: set REPO
STOP="$REPO/Automations/scripts/stack/stop-poller-stack.sh"  # info: set STOP
OPEN="$HERE/open-root-monitor.sh"  # info: set OPEN
LOG="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/restart_everything_current.log"  # info: set LOG
LOCK="/tmp/rootrecord-restart-everything.lock"  # info: set LOCK
POLLER="rr-rootserver-poller.service"  # info: set POLLER
GLOBE="network-globe-hawaii.service"  # info: set GLOBE
BLE="ava-ecoflow-ble.service"  # info: set BLE
AWS_TUNNEL="rr-aws-fetch-tunnel.service"  # info: set AWS_TUNNEL
STATUS_TIMER="rr-status-snapshot.timer"  # info: set STATUS_TIMER
ECOFLOW_TIMER="rr-ecoflow-read.timer"  # info: set ECOFLOW_TIMER
MONITOR='python3 .*rr_control_panel\.py'  # info: set MONITOR

mkdir -p "$(dirname "$LOG")"  # info: mkdir
exec >>"$LOG" 2>&1  # info: exec

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) restart-everything BEGIN pid=$$"  # info: echo

exec 9>"$LOCK"  # info: exec
if ! flock -n 9; then  # info: if
  echo "already running — leaving the other restart alone"  # info: echo
  exit 0  # info: exit
fi  # info: fi

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"  # info: export
if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "${XDG_RUNTIME_DIR}/bus" ]]; then  # info: if
  export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"  # info: export
fi  # info: fi
if [[ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then  # info: if
  if [[ -S /tmp/.X11-unix/X0 ]]; then  # info: if
    export DISPLAY=:0  # info: export
  elif [[ -S /tmp/.X11-unix/X1 ]]; then  # info: elif
    export DISPLAY=:1  # info: export
  fi  # info: fi
fi  # info: fi
if [[ -z "${XAUTHORITY:-}" && -f "/home/rootrecord/.Xauthority" ]]; then  # info: if
  export XAUTHORITY="/home/rootrecord/.Xauthority"  # info: export
fi  # info: fi
echo "DISPLAY=${DISPLAY:-unset} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset}"  # info: echo

if [[ -f "$STOP" ]]; then  # info: if
  echo "running stop-poller-stack.sh"  # info: echo
  bash "$STOP"  # info: bash
else  # info: else
  echo "stop script missing — stopping $POLLER and $GLOBE"  # info: echo
  systemctl --user stop "$POLLER" "$GLOBE"  # info: systemctl
fi  # info: fi

echo "restarting $BLE"  # info: echo
systemctl --user restart "$BLE"  # info: systemctl
echo "restarting $AWS_TUNNEL"  # info: echo
systemctl --user restart "$AWS_TUNNEL"  # info: systemctl
echo "starting $STATUS_TIMER"  # info: echo
systemctl --user start "$STATUS_TIMER"  # info: systemctl
echo "starting $ECOFLOW_TIMER"  # info: echo
systemctl --user start "$ECOFLOW_TIMER"  # info: systemctl

systemctl --user daemon-reload  # info: systemctl
echo "starting $POLLER"  # info: echo
systemctl --user start "$POLLER"  # info: systemctl
echo "starting $GLOBE"  # info: echo
systemctl --user start "$GLOBE"  # info: systemctl
sleep 2  # info: sleep
systemctl --user is-active "$POLLER" "$BLE" "$GLOBE" "$AWS_TUNNEL" "$STATUS_TIMER" "$ECOFLOW_TIMER"  # info: systemctl

# ====================================================
# SECTION: function wait_monitor_gone
# What it does: Wait until Root Monitor's process is gone. Does not start it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
wait_monitor_gone() {  # info: wait_monitor_gone
  local n=0  # info: local
  while pgrep -f "$MONITOR" >/dev/null 2>&1; do  # info: while
    n=$((n + 1))  # info: set n
    if [[ "$n" -ge 30 ]]; then  # info: if
      return 1  # info: return
    fi  # info: fi
    sleep 0.5  # info: sleep
  done  # info: done
  return 0  # info: return
}  # info: command

echo "closing Root Monitor"  # info: echo
pkill -f "$MONITOR" 2>/dev/null || true  # info: pkill
pkill -f 'Starlink/starlink_status.py' 2>/dev/null || true  # info: pkill
if ! wait_monitor_gone; then  # info: if
  echo "monitor still up — kill -9"  # info: echo
  pkill -9 -f "$MONITOR" 2>/dev/null || true  # info: pkill
  sleep 1  # info: sleep
fi  # info: fi
if pgrep -f "$MONITOR" >/dev/null 2>&1; then  # info: if
  echo "FAIL: Root Monitor still running — not opening a second copy"  # info: echo
  exit 1  # info: exit
fi  # info: fi

sleep 1  # info: sleep
echo "opening Root Monitor"  # info: echo
bash "$OPEN"  # info: bash
sleep 1  # info: sleep
if pgrep -f "$MONITOR" >/dev/null 2>&1; then  # info: if
  echo "verify: Root Monitor is running"  # info: echo
else  # info: else
  echo "verify: WARNING Root Monitor was not seen"  # info: echo
fi  # info: fi
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) restart-everything END"  # info: echo
exit 0  # info: exit
