#!/usr/bin/env bash
# ==============================================================================
# do-stack-reload.sh — full stop/start of poller stack after code pull
# Standing format: stop every poller-operated process, start clean, reopen viewer.
# Does NOT touch ava-ecoflow-ble.
#
# Window policy (2026-09-28 evening):
#   Reopen status window after reload by default (operator wants it back in place).
#   open-poller-window.sh uses fixed geometry (POLLER_WINDOW_GEOMETRY) and a
#   detached gnome-terminal launch so the client hand-off does not race reload.
#   Set OPEN_POLLER_WINDOW=0 to skip the viewer on automated reload.
#   Closing the viewer still stops the whole stack (poller-watch design).
# ==============================================================================
set +e

STACK="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(cd "$STACK/.." && pwd)"
REPO="$(cd "$SCRIPTS/../.." && pwd)"

LOG="${STACK_RELOAD_LOG:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/stack_reload_current.log}"
BAK_ROOT="${BAK_ROOT:-/home/rootrecord/Database/GITHUB}"
FLAG="$BAK_ROOT/flags/reload-poller-stack"
LOCK="/tmp/rootrecord-stack-reload.lock"
STAMP="$BAK_ROOT/flags/last-stack-reload"
STOP="$STACK/stop-poller-stack.sh"
OPEN_WIN="$SCRIPTS/poller/open-poller-window.sh"
CLI="/home/rootrecord/rootserver-poller"
UNIT="rr-rootserver-poller.service"

mkdir -p "$(dirname "$LOG")" "$BAK_ROOT/flags"
exec >>"$LOG" 2>&1

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) do-stack-reload BEGIN pid=$$"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "${XDG_RUNTIME_DIR}/bus" ]]; then
  export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
fi
if [[ -z "${DISPLAY:-}" ]]; then
  if [[ -S /tmp/.X11-unix/X0 ]]; then
    export DISPLAY=:0
  elif [[ -S /tmp/.X11-unix/X1 ]]; then
    export DISPLAY=:1
  fi
fi
if [[ -z "${XAUTHORITY:-}" && -f "/home/rootrecord/.Xauthority" ]]; then
  export XAUTHORITY="/home/rootrecord/.Xauthority"
fi
echo "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
echo "DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unset}"
echo "DISPLAY=${DISPLAY:-unset}"

if [[ -f "$STOP" ]]; then
  echo "running stop-poller-stack.sh"
  bash "$STOP"
else
  echo "stop script missing — fallback kills"
  systemctl --user stop "$UNIT" 2>/dev/null || true
  pkill -f 'rootserver_poller\.py' 2>/dev/null || true
  pkill -f 'cloudflared' 2>/dev/null || true
  pkill -f 'poller-watch\.py' 2>/dev/null || true
fi

rm -f /tmp/ecoflow-ble.lock 2>/dev/null || true
sleep 2

systemctl --user daemon-reload 2>/dev/null || true

started=0
if systemctl --user start "$UNIT" 2>&1; then
  echo "started $UNIT via systemctl"
  started=1
elif [[ -f "$CLI" ]]; then
  echo "systemctl start failed — trying CLI $CLI"
  bash "$CLI" start 2>&1 || "$CLI" start 2>&1
  started=1
  echo "started via CLI"
else
  echo "FAIL: could not start unit or CLI"
fi

sleep 2
if pgrep -f 'rootserver_poller\.py' >/dev/null 2>&1; then
  echo "verify: rootserver_poller.py is running"
elif systemctl --user is-active "$UNIT" >/dev/null 2>&1; then
  echo "verify: $UNIT is active"
else
  echo "verify: WARNING neither poller process nor unit active"
  systemctl --user start "$UNIT" 2>&1 || true
fi

# ---------------------------------------------------------------------------
# Status window — ON by default after reload (operator preference).
# OPEN_POLLER_WINDOW=0 skips. Geometry via POLLER_WINDOW_GEOMETRY.
# ---------------------------------------------------------------------------
window_ok=0
if [[ "${OPEN_POLLER_WINDOW:-1}" == "1" ]]; then
  if [[ -n "${DISPLAY:-}" ]]; then
    if [[ -f "$OPEN_WIN" ]]; then
      echo "opening poller window via open-poller-window.sh"
      # Detached; open-poller-window itself nohups gnome-terminal
      bash "$OPEN_WIN" || echo "WARNING: open-poller-window returned non-zero"
      window_ok=1
    elif [[ -f "$CLI" ]]; then
      echo "opening poller window via CLI window"
      "$CLI" window &
      window_ok=1
    fi
    sleep 1
    if pgrep -f 'poller-watch\.py' >/dev/null 2>&1; then
      echo "verify: poller-watch.py window process running"
    else
      echo "verify: WARNING poller-watch not seen (DISPLAY=$DISPLAY)"
    fi
  else
    echo "DISPLAY unset — cannot open GUI window (unit still started)"
  fi
else
  echo "skip status window (OPEN_POLLER_WINDOW=0)"
fi

date +%s > "$STAMP"
rm -f "$FLAG"
rm -f "$LOCK"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) do-stack-reload END started=$started window=$window_ok"
exit 0
