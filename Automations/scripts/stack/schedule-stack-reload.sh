#!/usr/bin/env bash
# ==============================================================================
# schedule-stack-reload.sh — arm deferred full stack reload after skills pull
# ------------------------------------------------------------------------------
# Standing format for all future builds.
# Prefers systemd-run --user --on-active=8s; falls back to nohup/setsid.
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -u

# ====================================================
# SECTION: PATHS
# ====================================================
BAK_ROOT="${BAK_ROOT:-/home/rootrecord/Database/GITHUB}"
FLAG="$BAK_ROOT/flags/reload-poller-stack"
LOCK="/tmp/rootrecord-stack-reload.lock"
STAMP="$BAK_ROOT/flags/last-stack-reload"
LOG="/home/rootrecord/.ollama/skills/logs/store/stack-reload.log"
DO_RELOAD="/home/rootrecord/.ollama/skills/automations/scripts/do-stack-reload.sh"

mkdir -p "$(dirname "$LOG")" "$BAK_ROOT/flags"

# ====================================================
# SECTION: GUARDS (flag / lock / debounce)
# ====================================================
if [[ ! -f "$FLAG" ]]; then
  echo "[reload] no flag — nothing to do"
  exit 0
fi

if ! ( set -o noclobber; echo "$$" > "$LOCK" ) 2>/dev/null; then
  if [[ -f "$LOCK" ]]; then
    age=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || echo 0) ))
    if (( age > 300 )); then
      echo "[reload] clearing stale lock (age=${age}s)"
      rm -f "$LOCK"
      echo "$$" > "$LOCK" || true
    else
      echo "[reload] already in progress — skip"
      exit 0
    fi
  fi
fi

if [[ -f "$STAMP" ]]; then
  last=$(cat "$STAMP" 2>/dev/null || echo 0)
  now=$(date +%s)
  if [[ "$last" =~ ^[0-9]+$ ]] && (( now - last < 45 )); then
    echo "[reload] debounced (last reload epoch=$last)"
    rm -f "$LOCK"
    exit 0
  fi
fi

if [[ ! -f "$DO_RELOAD" ]]; then
  echo "[reload] FAIL missing $DO_RELOAD"
  rm -f "$LOCK"
  exit 1
fi

# ====================================================
# SECTION: SCHEDULE (systemd-run or nohup/setsid)
# ====================================================
echo "[reload] armed — full poller stack stop/start in 8s"
echo "[reload] log=$LOG"
echo "[reload] runner=$DO_RELOAD"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "${XDG_RUNTIME_DIR}/bus" ]]; then
  export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
fi

scheduled=0
if command -v systemd-run >/dev/null 2>&1; then
  if systemd-run --user --on-active=8s --unit=rootrecord-stack-reload.service \
      --description="RootRecord poller stack reload after GitHub pull" \
      /bin/bash "$DO_RELOAD" 2>>"$LOG"; then
    echo "[reload] scheduled via systemd-run --user --on-active=8s"
    scheduled=1
  else
    echo "[reload] systemd-run failed — falling back to nohup"
  fi
fi

if [[ "$scheduled" -eq 0 ]]; then
  nohup setsid /bin/bash -c "sleep 8; exec /bin/bash '$DO_RELOAD'" >>"$LOG" 2>&1 &
  echo "[reload] scheduled via nohup/setsid pid=$!"
fi

echo "[reload] scheduled (log=$LOG)"
exit 0
