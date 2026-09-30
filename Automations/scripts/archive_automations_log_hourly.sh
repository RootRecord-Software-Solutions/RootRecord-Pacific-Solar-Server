# ==============================================================================
# FILE: Automations/scripts/archive_automations_log_hourly.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
set -euo pipefail  # info: set

DATABASE_ROOT="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"  # info: set DATABASE_ROOT
CURRENT_LOG="${DATABASE_ROOT}/Logs/Automations/automations_current.log"  # info: set CURRENT_LOG
ARCHIVE_DIR="${DATABASE_ROOT}/Logs/Automations/Archive"  # info: set ARCHIVE_DIR
LOCK_FILE="/tmp/automations-log-archive.lock"  # info: set LOCK_FILE
STAMP="$(date '+%Y-%m-%d_%H00')"  # info: set STAMP
ARCHIVE_LOG="${ARCHIVE_DIR}/automations_${STAMP}.log"  # info: set ARCHIVE_LOG

mkdir -p "${ARCHIVE_DIR}"  # info: mkdir

(  # info: command
  flock -n 9 || exit 0  # info: flock

  if [[ ! -s "${CURRENT_LOG}" ]]; then  # info: if
    exit 0  # info: exit
  fi  # info: fi

  cp -- "${CURRENT_LOG}" "${ARCHIVE_LOG}.tmp"  # info: cp
  mv -- "${ARCHIVE_LOG}.tmp" "${ARCHIVE_LOG}"  # info: mv
  : > "${CURRENT_LOG}"  # info: command
) 9>"${LOCK_FILE}"  # info: command
