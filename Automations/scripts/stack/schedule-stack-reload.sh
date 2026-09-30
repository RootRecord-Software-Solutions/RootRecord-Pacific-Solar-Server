#!/usr/bin/env bash
# ==============================================================================
# schedule-stack-reload.sh — queue a deferred full stack reload
# ==============================================================================
set -euo pipefail  # info: set

STACK="$(cd "$(dirname "$0")" && pwd)"  # info: set STACK
SCRIPTS="$(cd "$STACK/.." && pwd)"  # info: set SCRIPTS
REPO="$(cd "$SCRIPTS/../.." && pwd)"  # info: set REPO

DO_RELOAD="$STACK/do-stack-reload.sh"  # info: set DO_RELOAD
BAK_ROOT="${BAK_ROOT:-/home/rootrecord/Database/GITHUB}"  # info: set BAK_ROOT
FLAG="$BAK_ROOT/flags/reload-poller-stack"  # info: set FLAG
LOCK="/tmp/rootrecord-stack-reload.lock"  # info: set LOCK
LOG="${STACK_RELOAD_LOG:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/stack_reload_current.log}"  # info: set LOG

mkdir -p "$(dirname "$LOG")" "$BAK_ROOT/flags"  # info: mkdir

echo "[reload] log=$LOG"  # info: echo

if [[ -f "$LOCK" ]]; then  # info: if
  age=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || echo 0) ))  # info: set age
  if [[ "$age" -lt 120 ]]; then  # info: if
    echo "[reload] already scheduled (lock age=${age}s) — skip"  # info: echo
    exit 0  # info: exit
  fi  # info: fi
  rm -f "$LOCK"  # info: rm
fi  # info: fi

touch "$LOCK"  # info: touch
touch "$FLAG"  # info: touch

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

if command -v systemd-run >/dev/null 2>&1; then  # info: if
  if systemd-run --user --on-active=8s --timer-property=AccuracySec=1s \
      /bin/bash "$DO_RELOAD" 2>>"$LOG"; then  # info: /bin/bash
    echo "[reload] scheduled via systemd-run --on-active=8s"  # info: echo
    echo "[reload] scheduled (log=$LOG)"  # info: echo
    exit 0  # info: exit
  fi  # info: fi
fi  # info: fi

nohup setsid /bin/bash -c "sleep 8; exec /bin/bash '$DO_RELOAD'" >>"$LOG" 2>&1 &  # info: nohup
echo "[reload] scheduled via nohup (8s)"  # info: echo
echo "[reload] scheduled (log=$LOG)"  # info: echo
exit 0  # info: exit
