#!/usr/bin/env bash
# ============================================================================
# Reports/scripts/daily_roll_up.sh — WO-RPT-001 Phase C
# ----------------------------------------------------------------------------
# Summarize today's Database/WORKLOG activity into a Library session-style file.
# Measured counts only — no invented narrative. Secrets never copied.
# ============================================================================
set -euo pipefail

WORKLOG_DIR="${WORKLOG_DIR:-/home/rootrecord/Database/WORKLOG}"
LIBRARY_ROOT="${LIBRARY_ROOT:-/home/rootrecord/RootRecord-Ecosystem/5 - RootRecord-Library}"
LOG_DIR="${LIBRARY_ROOT}/Documentation/01-operations/0 - Human Operator Work Logs"
TODAY="$(TZ=Pacific/Honolulu date '+%Y-%m-%d')"
NOW_HM="$(TZ=Pacific/Honolulu date '+%H:%M')"
OUT="${LOG_DIR}/${TODAY} System Operator Worklog — Session auto.md"

mkdir -p "$LOG_DIR"

# Collect today's lines from current + rotated segments named with today's date prefix
tmp=$(mktemp)
{
  [[ -f "${WORKLOG_DIR}/worklog_current.md" ]] && cat "${WORKLOG_DIR}/worklog_current.md"
  # rotated: *YYYYMMDD* or contain today's ISO in content headers
  find "$WORKLOG_DIR" -maxdepth 1 -type f -name '*.md' ! -name 'worklog_current.md' -print0 2>/dev/null \
    | while IFS= read -r -d '' f; do
        base=$(basename "$f")
        case "$base" in
          *"${TODAY//-/}"*|*"${TODAY}"*) cat "$f" ;;
        esac
      done
} > "$tmp" 2>/dev/null || true

count_kind() {
  local k="$1"
  grep -cE "^- ${k} " "$tmp" 2>/dev/null || echo 0
}

count_domain() {
  local d="$1"
  grep -cE "domain=${d}" "$tmp" 2>/dev/null || echo 0
}

NEW_F=$(count_kind NEW_FILE)
MOD_F=$(count_kind MOD_FILE)
NEW_D=$(count_kind NEW_DIR)
DEL=$(count_kind DELETED)
# normalize newlines from echo 0
NEW_F=${NEW_F//$'\n'/}; MOD_F=${MOD_F//$'\n'/}; NEW_D=${NEW_D//$'\n'/}; DEL=${DEL//$'\n'/}

DOM_LINES=""
for d in Automations Energy System Reports Communications Github Weather Geology Security Library Database; do
  c=$(count_domain "$d")
  c=${c//$'\n'/}
  [[ "$c" -gt 0 ]] 2>/dev/null && DOM_LINES+="| ${d} | ${c} |"$'\n'
done
[[ -z "$DOM_LINES" ]] && DOM_LINES="| (none tagged) | 0 |"$'\n'

# Migration progress stub (static known LIVE domains — measured from Pacific tree presence)
MIG=""
PACIFIC="${PACIFIC:-/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server}"
for pair in "Energy:Energy" "System:System" "Reports:Reports" "Automations:Automations"; do
  name="${pair%%:*}"; path="${pair##*:}"
  if [[ -d "${PACIFIC}/${path}" ]]; then
    MIG+="- **${name}:** domain folder present on Pacific"$'\n'
  fi
done

cat > "$OUT" <<EOF
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

Filename:

```text
${TODAY} System Operator Worklog — Session auto.md
```

Weekly archive (logs): move closed sessions older than the current week into
Documentation/01-operations/archive/YYYY-Www/ without rewriting content.
EOF

chmod 600 "$OUT" 2>/dev/null || true
rm -f "$tmp"
echo "OK wrote ${OUT}"
