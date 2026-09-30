# ==============================================================================
# FILE: Products/scripts/Companions/scripts/start-dev-desk.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
echo "target is not on this desk" >&2; exit 1  # info: echo
# Dev-Desk — same job as Windows C:\Users\rootr\ava\windows\start_desk.py
# This folder is the Electron window. Live origin is RootRecord/Ava-Core.
# JSON/sqlite live in ~/.ollama/skills/{database,state,logs}/store. Media is $HOME/Media.
set -euo pipefail  # info: set

export PATH="${HOME}/.local/bin:/usr/local/bin:${PATH}"  # info: export

DESK_ROOT="/home/rootrecord/.ollama/skills/companions/dev-desk"  # info: set DESK_ROOT
AVA_ROOT="${AVA_HOME:-/home/rootrecord/.ollama/skills/origin}"  # info: set AVA_ROOT
AVA_STATE_DIR="${AVA_STATE_DIR:-$HOME/.ollama/skills/state/store}"  # info: set AVA_STATE_DIR
LOG_DIR="${AVA_LOGS_DIR:-$HOME/.ollama/skills/logs/store}"  # info: set LOG_DIR
mkdir -p "${LOG_DIR}" "${AVA_STATE_DIR}" || true  # info: mkdir

exec >>"${LOG_DIR}/dev-desk.log" 2>&1  # info: exec
echo "---- $(date -Iseconds) start-dev-desk desk=${DESK_ROOT} ava=${AVA_ROOT} ----"  # info: echo

export AVA_HOME="${AVA_ROOT}"  # info: export
export AVA_HANDOFF="${AVA_ROOT}"  # info: export
export ROOTMC_ENV_FILE="${AVA_ROOT}/.env"  # info: export
export AVA_ENV_FILE="${AVA_ROOT}/.env"  # info: export
export AVA_DESKTOP_UI=1  # info: export
export AVA_RICH_PRESENCE="${AVA_RICH_PRESENCE:-1}"  # info: export
export AVA_PORT="${AVA_PORT:-8787}"  # info: export
export DATA_DIR="${DATA_DIR:-$HOME/.ollama/skills/database/store}"  # info: export
export STATE_DIR="${STATE_DIR:-$AVA_STATE_DIR}"  # info: export
export RUNTIME_LOGS="${RUNTIME_LOGS:-$LOG_DIR}"  # info: export

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then  # info: if
  export DISPLAY="${DISPLAY:-:0}"  # info: export
fi  # info: fi

if [[ -f "${AVA_STATE_DIR}/power-off.json" ]]; then  # info: if
  rm -f "${AVA_STATE_DIR}/power-off.json"  # info: rm
  echo "cleared power-off.json"  # info: echo
fi  # info: fi

UID_NUM="$(id -u)"  # info: set UID_NUM
export PULSE_SERVER="${PULSE_SERVER:-unix:/run/user/${UID_NUM}/pulse/native}"  # info: export
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/${UID_NUM}}"  # info: export

cd "${DESK_ROOT}"  # info: cd

if [[ ! -d node_modules/electron ]]; then  # info: if
  echo "Installing Electron desktop deps…"  # info: echo
  npm install --prefer-offline 2>&1 || npm install  # info: npm
fi  # info: fi

ELECTRON_BIN="${DESK_ROOT}/node_modules/.bin/electron"  # info: set ELECTRON_BIN
ELECTRON_DIST="${DESK_ROOT}/node_modules/electron/dist/electron"  # info: set ELECTRON_DIST

if [[ ! -x "${ELECTRON_BIN}" && ! -x "${ELECTRON_DIST}" ]]; then  # info: if
  echo "ERROR: electron binary missing — run: cd ${DESK_ROOT} && npm install" >&2  # info: echo
  exit 1  # info: exit
fi  # info: fi

unset ELECTRON_RUN_AS_NODE || true  # info: unset
export ELECTRON_DISABLE_SANDBOX="${ELECTRON_DISABLE_SANDBOX:-1}"  # info: export
export ELECTRON_OZONE_PLATFORM_HINT="${ELECTRON_OZONE_PLATFORM_HINT:-auto}"  # info: export

echo "Starting Dev-Desk (origin ${AVA_ROOT} :8787)"  # info: echo
if [[ -x "${ELECTRON_DIST}" ]]; then  # info: if
  exec "${ELECTRON_DIST}" --no-sandbox --ozone-platform-hint=auto .  # info: exec
fi  # info: fi
exec "${ELECTRON_BIN}" --no-sandbox --ozone-platform-hint=auto .  # info: exec
