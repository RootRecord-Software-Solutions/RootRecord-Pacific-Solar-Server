#!/usr/bin/env bash
# ============================================================================
# Reports/scripts/daily_roll_up.sh — WO-RPT-001 Phase C
# ----------------------------------------------------------------------------
# Summarize today's Database/WORKLOG activity into a Library session-style file.
# Measured counts only — no invented narrative. Secrets never copied.
# ============================================================================
set -euo pipefail  # info: set

WORKLOG_DIR="${WORKLOG_DIR:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Worklog}"  # info: set WORKLOG_DIR
LIBRARY_ROOT="${LIBRARY_ROOT:-/home/rootrecord/RootRecord-Ecosystem/5 - RootRecord-Library}"  # info: set LIBRARY_ROOT
LOG_DIR="${LIBRARY_ROOT}/Documentation/01-Operations/0 - Human Operator Work Logs"  # info: set LOG_DIR
TODAY="$(TZ=Pacific/Honolulu date '+%Y-%m-%d')"  # info: set TODAY
NOW_HM="$(TZ=Pacific/Honolulu date '+%H:%M')"  # info: set NOW_HM
OUT="${LOG_DIR}/${TODAY} System Operator Worklog — Session auto.md"  # info: set OUT

mkdir -p "$LOG_DIR"  # info: mkdir

# Collect today's lines from current + rotated segments named with today's date prefix
tmp=$(mktemp)  # info: set tmp
{  # info: command
  [[ -f "${WORKLOG_DIR}/worklog_current.md" ]] && cat "${WORKLOG_DIR}/worklog_current.md"  # info: command
  # rotated: *YYYYMMDD* or contain today's ISO in content headers
  find "$WORKLOG_DIR" -maxdepth 1 -type f -name '*.md' ! -name 'worklog_current.md' -print0 2>/dev/null \
    | while IFS= read -r -d '' f; do  # info: command
        base=$(basename "$f")  # info: set base
        case "$base" in  # info: case
          *"${TODAY//-/}"*|*"${TODAY}"*) cat "$f" ;;  # info: command
        esac  # info: esac
      done  # info: done
} > "$tmp" 2>/dev/null || true  # info: command

# ====================================================
# SECTION: function count_kind
# What it does: count kind.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
count_kind() {  # info: count_kind
  local k="$1"  # info: local
  grep -cE "^- ${k} " "$tmp" 2>/dev/null || echo 0  # info: grep
}  # info: command

# ====================================================
# SECTION: function count_domain
# What it does: count domain.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
count_domain() {  # info: count_domain
  local d="$1"  # info: local
  grep -cE "domain=${d}" "$tmp" 2>/dev/null || echo 0  # info: grep
}  # info: command

NEW_F=$(count_kind NEW_FILE)  # info: set NEW_F
MOD_F=$(count_kind MOD_FILE)  # info: set MOD_F
NEW_D=$(count_kind NEW_DIR)  # info: set NEW_D
DEL=$(count_kind DELETED)  # info: set DEL
# normalize newlines from echo 0
NEW_F=${NEW_F//$'\n'/}; MOD_F=${MOD_F//$'\n'/}; NEW_D=${NEW_D//$'\n'/}; DEL=${DEL//$'\n'/}  # info: set NEW_F

DOM_LINES=""  # info: set DOM_LINES
for d in Automations Energy System Reports Communications Github Weather Geology Security Library Database; do  # info: for
  c=$(count_domain "$d")  # info: set c
  c=${c//$'\n'/}  # info: set c
  [[ "$c" -gt 0 ]] 2>/dev/null && DOM_LINES+="| ${d} | ${c} |"$'\n'  # info: command
done  # info: done
[[ -z "$DOM_LINES" ]] && DOM_LINES="| (none tagged) | 0 |"$'\n'  # info: command

# Migration progress stub (static known LIVE domains — measured from Pacific tree presence)
MIG=""  # info: set MIG
PACIFIC="${PACIFIC:-/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server}"  # info: set PACIFIC
for pair in "Energy:Energy" "System:System" "Reports:Reports" "Automations:Automations"; do  # info: for
  name="${pair%%:*}"; path="${pair##*:}"
  if [[ -d "${PACIFIC}/${path}" ]]; then  # info: if
    MIG+="- **${name}:** domain folder present on Pacific"$'\n'  # info: MIG
  fi  # info: fi
done  # info: done

cat > "$OUT" <<EOF  # info: cat
# System Operator Worklog — Session auto

**Date:** ${TODAY}  
**Session:** Automated daily roll-up (WO-RPT-001 Phase C)  
**Timezone:** HST  
**Window:** day → ${NOW_HM} HST  
**Status:** CLOSED  
**Operator:** RootRecord (auto)

---

## Purpose

Machine summary of offline work auto-doc activity for ${TODAY}.  
Counts only — path/size/mtime events from Database/WORKLOG. No secrets, no file contents.

---

## Event counts (measured)

| Kind | Count |
| --- | --- |
| NEW_FILE | ${NEW_F} |
| MOD_FILE | ${MOD_F} |
| NEW_DIR | ${NEW_D} |
| DELETED | ${DEL} |

### By domain tag

| Domain | Count |
| --- | --- |
${DOM_LINES}
---

## Migration progress (auto stub)

${MIG}
- **G2 residuals still expected:** plumbing, telegram, a-eyes, energy actions (until WO-SRV-001)
- **WO-RPT-001:** Phase B LIVE; Phase C this file; Phase D weekly log archive

---

## Explicit non-goals

- Does not invent session narrative or checklist completions
- Does not replace human Session NN logs
- Does not archive files (see weekly_archive_logs.sh)

---

## State at roll-up (~${NOW_HM} HST)

- **Runtime:** worklog_scan → Pacific Reports/scripts
- **Machine log:** ${WORKLOG_DIR}/worklog_current.md
- **This file:** ${OUT}
- **Next useful step:** Human session log if needed; residual path imports; Phase D Sunday archive

**Status:** Auto roll-up written ${TODAY} ${NOW_HM} HST.

---

## Archive note

Filename: ${TODAY} System Operator Worklog — Session auto.md

Weekly archive (logs): move closed sessions older than the current week into
Documentation/01-Operations/Archive/YYYY-Www/ without rewriting content.
EOF

chmod 600 "$OUT" 2>/dev/null || true  # info: chmod
rm -f "$tmp"  # info: rm
echo "OK wrote ${OUT}"  # info: echo
