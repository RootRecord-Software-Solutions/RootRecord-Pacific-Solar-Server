# ==============================================================================
# FILE: Products/scripts/Companions/scripts/start-ava-companions.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
echo "target is not on this desk" >&2; exit 1  # info: echo
# Companion processes that should be up whenever Ava is online.
# Origin (:8787) is launch.sh. No Electron.
# Do not launch OBS here.
set -u  # info: set
export PATH="${HOME}/.local/bin:/usr/local/bin:${PATH}"  # info: export
export DISPLAY="${DISPLAY:-:0}"  # info: export
AVA_ROOT="/home/rootrecord/.ollama/skills/origin"  # info: set AVA_ROOT
TOGGLE_FILE="${AVA_STATE_DIR:-$HOME/.ollama/skills/state/store}/feature-toggles.json"  # info: set TOGGLE_FILE
LOG="${AVA_LOGS_DIR:-$HOME/.ollama/skills/logs/store}/companions.log"  # info: set LOG
mkdir -p "$(dirname "$LOG")"  # info: mkdir
exec >>"${LOG}" 2>&1  # info: exec
echo "---- $(date -Iseconds) start-ava-companions ----"  # info: echo

# ====================================================
# SECTION: function feature_on
# What it does: feature on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
feature_on() {  # info: feature_on
  local key="$1"  # info: local
  [ -f "$TOGGLE_FILE" ] || return 1  # info: command
  grep -E "\"${key}\"[[:space:]]*:[[:space:]]*true" "$TOGGLE_FILE" >/dev/null 2>&1  # info: grep
}  # info: command

# Discord + Slack conversation poller. Origin already long-polls Telegram
# for /subscribe — leave Telegram to origin so getUpdates does not conflict.
POLLER_ROOT="${HOME}/ava/workstations/rootmc-web/rootmc-ava"  # info: set POLLER_ROOT
if ! feature_on companions_poller; then  # info: if
  echo "poller skipped (feature companions_poller off)"  # info: echo
elif [[ -x "${POLLER_ROOT}/scripts/start-poller.sh" ]] && [[ -d "${POLLER_ROOT}/node_modules" ]]; then  # info: elif
  if ! ps -eo args= | grep -q '[n]ode src/poller.mjs'; then  # info: if
    echo "starting discord/slack poller"  # info: echo
    (  # info: command
      cd "${POLLER_ROOT}"  # info: cd
      nohup ./scripts/start-poller-discord-slack.sh >>"${LOG%/*}/poller.out" 2>&1 &  # info: nohup
    )  # info: command
  else  # info: else
    echo "poller already running"  # info: echo
  fi  # info: fi
else  # info: else
  echo "poller skipped (missing ${POLLER_ROOT})"  # info: echo
fi  # info: fi

# Weather GIF collector — only if the working directory still exists
WG_DIR="/home/ava-core/Desktop/ava-weather-gif-collector-hawaii-pacific-v7./ava-weather-gif-collector"  # info: set WG_DIR
if [[ -d "${WG_DIR}" ]] && [[ -f "${WG_DIR}/weathergifs.py" ]]; then  # info: if
  systemctl --user enable --now ava-weather-gifs.service || true  # info: systemctl
else  # info: else
  echo "weather GIFs collector missing on disk — leaving unit stopped"  # info: echo
  systemctl --user disable --now ava-weather-gifs.service >/dev/null 2>&1 || true  # info: systemctl
fi  # info: fi

echo "OBS not auto-started (open OBS yourself; Ava Ops obs toggle only allows jobs)"  # info: echo

# Snap-proof copy of layouts / profiles / overlays (non-blocking).
if [[ -x "${HOME}/ava/ava-core-v2/scripts/backup-obs.sh" ]]; then  # info: if
  nohup "${HOME}/ava/ava-core-v2/scripts/backup-obs.sh" >/dev/null 2>&1 &  # info: nohup
fi  # info: fi

# Local-edge gateway :8791 if the Node tree is installed
GW="${HOME}/ava/workstations/rootmc-scripts/local-edge/gateway"  # info: set GW
if ! feature_on local_edge; then  # info: if
  echo "local-edge skipped (feature local_edge off)"  # info: echo
elif [[ -f "${GW}/server.mjs" ]] && [[ -d "${GW}/node_modules" ]]; then  # info: elif
  if ! ss -ltn 2>/dev/null | grep -q ':8791 '; then  # info: if
    echo "starting local-edge gateway :8791"  # info: echo
    (  # info: command
      cd "${GW}"  # info: cd
      nohup node server.mjs >>"${LOG%/*}/local-edge-8791.log" 2>&1 &  # info: nohup
    )  # info: command
  fi  # info: fi
fi  # info: fi

echo "companions done"  # info: echo
