#!/usr/bin/env bash
# ==============================================================================
# schedule-stack-reload.sh — queue a deferred full stack reload
# ==============================================================================
set -euo pipefail

STACK="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(cd "$STACK/.." && pwd)"
REPO="$(cd "$SCRIPTS/../.." && pwd)"

DO_RELOAD="$STACK/do-stack-reload.sh"
BAK_ROOT="${BAK_ROOT:-/home/rootrecord/Database/GITHUB}"
FLAG="$BAK_ROOT/flags/reload-poller-stack"
LOCK="/tmp/rootrecord-stack-reload.lock"
LOG="${STACK_RELOAD_LOG:-/home/rootrecord/Database/LOGS/Automations/stack-reload.log}"

mkdir -p "$(dirname "$LOG")" "$BAK_ROOT/flags"

echo "[reload] log=$LOG"

if [[ -f "$LOCK" ]]; then
  age=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || echo 0) ))
  if [[ "$age" -lt 120 ]]; then
    echo "[reload] already scheduled (lock age=${age}s) — skip"
    exit 0
  fi
  rm -f "$LOCK"
fi

touch "$LOCK"
touch "$FLAG"

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

# Prefer systemd-run so the job survives the calling shell
if command -v systemd-run >/dev/null 2>&1; then
  if systemd-run --user --on-active=8s --timer-property=AccuracySec=1s \
      /bin/bash "$DO_RELOAD" 2>>"$LOG"; then
    echo "[reload] scheduled via systemd-run --on-active=8s"
    echo "[reload] scheduled (log=$LOG)"
    exit 0
  fi
fi

# Fallback: detached sleep + reload
nohup setsid /bin/bash -c "sleep 8; exec /bin/bash '$DO_RELOAD'" >>"$LOG" 2>&1 &
echo "[reload] scheduled via nohup (8s)"
echo "[reload] scheduled (log=$LOG)"
exit 0
