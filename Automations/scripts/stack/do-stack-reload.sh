#!/usr/bin/env bash
# ==============================================================================
# do-stack-reload.sh — full stop/start of poller stack after code pull
# Standing format: stop every poller-operated process, start clean, reopen viewer.
# Does NOT touch ava-ecoflow-ble.
#
# Window policy (2026-09-30):
#   Reopen Root Monitor after reload by default (operator wants it instead of the terminal).
#   open-root-monitor.sh starts the GTK panel only. It does not start or restart the poller.
#   Set OPEN_POLLER_WINDOW=0 to skip the viewer on automated reload.
#   The terminal dashboard stays available from the menu (open-poller-window.sh).
#   Closing the viewer never stops the stack.
# ==============================================================================
set +e  # info: set

STACK="$(cd "$(dirname "$0")" && pwd)"  # info: set STACK
SCRIPTS="$(cd "$STACK/.." && pwd)"  # info: set SCRIPTS
REPO="$(cd "$SCRIPTS/../.." && pwd)"  # info: set REPO

LOG="${STACK_RELOAD_LOG:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/stack_reload_current.log}"  # info: set LOG
BAK_ROOT="${BAK_ROOT:-/home/rootrecord/Database/GITHUB}"  # info: set BAK_ROOT
FLAG="$BAK_ROOT/flags/reload-poller-stack"  # info: set FLAG
LOCK="/tmp/rootrecord-stack-reload.lock"  # info: set LOCK
STAMP="$BAK_ROOT/flags/last-stack-reload"  # info: set STAMP
STOP="$STACK/stop-poller-stack.sh"  # info: set STOP
OPEN_WIN="$REPO/Apps/Control-Panel/Packaging/open-root-monitor.sh"  # info: set OPEN_WIN
CLI="/home/rootrecord/rootserver-poller"  # info: set CLI
UNIT="rr-rootserver-poller.service"  # info: set UNIT

mkdir -p "$(dirname "$LOG")" "$BAK_ROOT/flags"  # info: mkdir
exec >>"$LOG" 2>&1  # info: exec

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) do-stack-reload BEGIN pid=$$"  # info: echo

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"  # info: export
if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "${XDG_RUNTIME_DIR}/bus" ]]; then  # info: if
  export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"  # info: export
fi  # info: fi
if [[ -z "${DISPLAY:-}" ]]; then  # info: if
  if [[ -S /tmp/.X11-unix/X0 ]]; then  # info: if
    export DISPLAY=:0  # info: export
  elif [[ -S /tmp/.X11-unix/X1 ]]; then  # info: elif
    export DISPLAY=:1  # info: export
  fi  # info: fi
fi  # info: fi
if [[ -z "${XAUTHORITY:-}" && -f "/home/rootrecord/.Xauthority" ]]; then  # info: if
  export XAUTHORITY="/home/rootrecord/.Xauthority"  # info: export
fi  # info: fi
echo "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"  # info: echo
echo "DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unset}"  # info: echo
echo "DISPLAY=${DISPLAY:-unset}"  # info: echo

if [[ -f "$STOP" ]]; then  # info: if
  echo "running stop-poller-stack.sh"  # info: echo
  bash "$STOP"  # info: bash
else  # info: else
  echo "stop script missing — fallback kills"  # info: echo
  systemctl --user stop "$UNIT" 2>/dev/null || true  # info: systemctl
  pkill -f 'rootserver_poller\.py' 2>/dev/null || true  # info: pkill
  pkill -f 'cloudflared' 2>/dev/null || true  # info: pkill
  pkill -f 'poller-watch\.py' 2>/dev/null || true  # info: pkill
fi  # info: fi

rm -f /tmp/ecoflow-ble.lock 2>/dev/null || true  # info: rm
sleep 2  # info: sleep

systemctl --user daemon-reload 2>/dev/null || true  # info: systemctl

started=0  # info: set started
if systemctl --user start "$UNIT" 2>&1; then  # info: if
  echo "started $UNIT via systemctl"  # info: echo
  started=1  # info: set started
elif [[ -f "$CLI" ]]; then  # info: elif
  echo "systemctl start failed — trying CLI $CLI"  # info: echo
  bash "$CLI" start 2>&1 || "$CLI" start 2>&1  # info: bash
  started=1  # info: set started
  echo "started via CLI"  # info: echo
else  # info: else
  echo "FAIL: could not start unit or CLI"  # info: echo
fi  # info: fi

sleep 2  # info: sleep
if pgrep -f 'rootserver_poller\.py' >/dev/null 2>&1; then  # info: if
  echo "verify: rootserver_poller.py is running"  # info: echo
elif systemctl --user is-active "$UNIT" >/dev/null 2>&1; then  # info: elif
  echo "verify: $UNIT is active"  # info: echo
else  # info: else
  echo "verify: WARNING neither poller process nor unit active"  # info: echo
  systemctl --user start "$UNIT" 2>&1 || true  # info: systemctl
fi  # info: fi

# ---------------------------------------------------------------------------
# Status window — ON by default after reload (operator preference).
# OPEN_POLLER_WINDOW=0 skips. Geometry via POLLER_WINDOW_GEOMETRY.
# ---------------------------------------------------------------------------
window_ok=0  # info: set window_ok
if [[ "${OPEN_POLLER_WINDOW:-1}" == "1" ]]; then  # info: if
  if [[ -n "${DISPLAY:-}" ]]; then  # info: if
    if [[ -f "$OPEN_WIN" ]]; then  # info: if
      echo "opening Root Monitor"  # info: echo
      bash "$OPEN_WIN" || echo "WARNING: open-root-monitor returned non-zero"  # info: bash
      window_ok=1  # info: set window_ok
    elif [[ -f "$CLI" ]]; then  # info: elif
      echo "opening poller window via CLI window"  # info: echo
      "$CLI" window &  # info: command
      window_ok=1  # info: set window_ok
    fi  # info: fi
    sleep 1  # info: sleep
    if pgrep -f 'poller-(watch|dashboard)\.py' >/dev/null 2>&1; then  # info: if
      echo "verify: poller viewer window process running"  # info: echo
    else  # info: else
      echo "verify: WARNING poller-watch not seen (DISPLAY=$DISPLAY)"  # info: echo
    fi  # info: fi
  else  # info: else
    echo "DISPLAY unset — cannot open GUI window (unit still started)"  # info: echo
  fi  # info: fi
else  # info: else
  echo "skip status window (OPEN_POLLER_WINDOW=0)"  # info: echo
fi  # info: fi

date +%s > "$STAMP"  # info: date
rm -f "$FLAG"  # info: rm
rm -f "$LOCK"  # info: rm
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) do-stack-reload END started=$started window=$window_ok"  # info: echo
exit 0  # info: exit
