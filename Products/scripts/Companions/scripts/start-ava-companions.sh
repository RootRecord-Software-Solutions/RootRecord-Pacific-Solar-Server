#!/usr/bin/env bash
# Companion processes that should be up whenever Ava is online.
# Origin (:8787) is launch.sh. No Electron.
# Do not launch OBS here.
set -u
export PATH="${HOME}/.local/bin:/usr/local/bin:${PATH}"
export DISPLAY="${DISPLAY:-:0}"
AVA_ROOT="/home/rootrecord/.ollama/skills/origin"
TOGGLE_FILE="${AVA_STATE_DIR:-$HOME/.ollama/skills/state/store}/feature-toggles.json"
LOG="${AVA_LOGS_DIR:-$HOME/.ollama/skills/logs/store}/companions.log"
mkdir -p "$(dirname "$LOG")"
exec >>"${LOG}" 2>&1
echo "---- $(date -Iseconds) start-ava-companions ----"

feature_on() {
  local key="$1"
  [ -f "$TOGGLE_FILE" ] || return 1
  grep -E "\"${key}\"[[:space:]]*:[[:space:]]*true" "$TOGGLE_FILE" >/dev/null 2>&1
}

# Discord + Slack conversation poller. Origin already long-polls Telegram
# for /subscribe — leave Telegram to origin so getUpdates does not conflict.
POLLER_ROOT="${HOME}/ava/workstations/rootmc-web/rootmc-ava"
if ! feature_on companions_poller; then
  echo "poller skipped (feature companions_poller off)"
elif [[ -x "${POLLER_ROOT}/scripts/start-poller.sh" ]] && [[ -d "${POLLER_ROOT}/node_modules" ]]; then
  if ! ps -eo args= | grep -q '[n]ode src/poller.mjs'; then
    echo "starting discord/slack poller"
    (
      cd "${POLLER_ROOT}"
      nohup ./scripts/start-poller-discord-slack.sh >>"${LOG%/*}/poller.out" 2>&1 &
    )
  else
    echo "poller already running"
  fi
else
  echo "poller skipped (missing ${POLLER_ROOT})"
fi

# Weather GIF collector — only if the working directory still exists
WG_DIR="/home/ava-core/Desktop/ava-weather-gif-collector-hawaii-pacific-v7./ava-weather-gif-collector"
if [[ -d "${WG_DIR}" ]] && [[ -f "${WG_DIR}/weathergifs.py" ]]; then
  systemctl --user enable --now ava-weather-gifs.service || true
else
  echo "weather GIFs collector missing on disk — leaving unit stopped"
  systemctl --user disable --now ava-weather-gifs.service >/dev/null 2>&1 || true
fi

echo "OBS not auto-started (open OBS yourself; Ava Ops obs toggle only allows jobs)"

# Snap-proof copy of layouts / profiles / overlays (non-blocking).
if [[ -x "${HOME}/ava/ava-core-v2/scripts/backup-obs.sh" ]]; then
  nohup "${HOME}/ava/ava-core-v2/scripts/backup-obs.sh" >/dev/null 2>&1 &
fi

# Local-edge gateway :8791 if the Node tree is installed
GW="${HOME}/ava/workstations/rootmc-scripts/local-edge/gateway"
if ! feature_on local_edge; then
  echo "local-edge skipped (feature local_edge off)"
elif [[ -f "${GW}/server.mjs" ]] && [[ -d "${GW}/node_modules" ]]; then
  if ! ss -ltn 2>/dev/null | grep -q ':8791 '; then
    echo "starting local-edge gateway :8791"
    (
      cd "${GW}"
      nohup node server.mjs >>"${LOG%/*}/local-edge-8791.log" 2>&1 &
    )
  fi
fi

echo "companions done"
