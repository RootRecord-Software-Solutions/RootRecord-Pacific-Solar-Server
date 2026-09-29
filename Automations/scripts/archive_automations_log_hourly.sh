#!/usr/bin/env bash
set -euo pipefail

DATABASE_ROOT="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"
CURRENT_LOG="${DATABASE_ROOT}/Logs/Automations/automations_current.log"
ARCHIVE_DIR="${DATABASE_ROOT}/Logs/Automations/Archive"
LOCK_FILE="/tmp/automations-log-archive.lock"
STAMP="$(date '+%Y-%m-%d_%H00')"
ARCHIVE_LOG="${ARCHIVE_DIR}/automations_${STAMP}.log"

mkdir -p "${ARCHIVE_DIR}"

(
  flock -n 9 || exit 0

  if [[ ! -s "${CURRENT_LOG}" ]]; then
    exit 0
  fi

  cp -- "${CURRENT_LOG}" "${ARCHIVE_LOG}.tmp"
  mv -- "${ARCHIVE_LOG}.tmp" "${ARCHIVE_LOG}"
  : > "${CURRENT_LOG}"
) 9>"${LOCK_FILE}"
