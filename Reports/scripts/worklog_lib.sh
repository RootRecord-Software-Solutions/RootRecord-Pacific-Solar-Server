#!/usr/bin/env bash
# Offline work auto-doc — FULL /home/rootrecord (pruned blobs).
# Path/size/mtime only. NO keystrokes, mouse, clipboard, or file contents.
# Pacific Reports/ (WO-RPT-001). Ported from G2 reports/scripts with hygiene enhancements.
set -euo pipefail

WORKLOG_DIR="${WORKLOG_DIR:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Worklog}"
CURRENT="${WORKLOG_DIR}/worklog_current.md"
STATE="${WORKLOG_DIR}/.last_scan"
HOUR_MARK="${WORKLOG_DIR}/.hour_start"
ENV_FILE="${ENV_FILE:-/home/rootrecord/master/master-key.env}"
PID_FILE="${WORKLOG_DIR}/.poller.pid"
SEEN_FILE="${WORKLOG_DIR}/.seen_index"
SEEN_DIRS="${WORKLOG_DIR}/.seen_dirs"
HOME_ROOT="/home/rootrecord"
PACIFIC_ECO="${PACIFIC_ECO:-/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server}"

ensure_dirs() {
  mkdir -p "$WORKLOG_DIR"
  chmod 700 "$WORKLOG_DIR" 2>/dev/null || true
  if [[ ! -f "$CURRENT" ]]; then
    printf '# Worklog current\n\nStarted: %s\nScope: full %s (pruned models/snap/cache/git-blobs)\n\n' \
      "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$HOME_ROOT" > "$CURRENT"
    chmod 600 "$CURRENT" 2>/dev/null || true
  fi
  [[ -f "$HOUR_MARK" ]] || date '+%Y%m%d%H' > "$HOUR_MARK"
  [[ -f "${WORKLOG_DIR}/.segment_start" ]] || date '+%Y%m%d-%H%M%S' > "${WORKLOG_DIR}/.segment_start"
  [[ -f "$STATE" ]] || date '+%s' > "$STATE"
  [[ -f "$SEEN_FILE" ]] || : > "$SEEN_FILE"
  [[ -f "$SEEN_DIRS" ]] || : > "$SEEN_DIRS"
}

# Tag Pacific domain when path is under a known domain folder (enhancement).
domain_tag() {
  local p="$1"
  case "$p" in
    *"/RootRecord-Pacific-Solar-Server/Automations"*|*/Automations/*) echo "domain=Automations" ;;
    *"/RootRecord-Pacific-Solar-Server/Energy"*|*/Energy/*) echo "domain=Energy" ;;
    *"/RootRecord-Pacific-Solar-Server/System"*|*/System/*) echo "domain=System" ;;
    *"/RootRecord-Pacific-Solar-Server/Reports"*|*/Reports/*) echo "domain=Reports" ;;
    *"/RootRecord-Pacific-Solar-Server/Communications"*|*/Communications/*) echo "domain=Communications" ;;
    *"/RootRecord-Pacific-Solar-Server/Github"*|*/Github/*) echo "domain=Github" ;;
    *"/RootRecord-Pacific-Solar-Server/Weather"*|*/Weather/*) echo "domain=Weather" ;;
    *"/RootRecord-Pacific-Solar-Server/Geology"*|*/Geology/*) echo "domain=Geology" ;;
    *"/RootRecord-Pacific-Solar-Server/Security"*|*/Security/*) echo "domain=Security" ;;
    *"/RootRecord-Library"*|*/RootRecord-Library/*) echo "domain=Library" ;;
    *"/Database/"*) echo "domain=Database" ;;
    *) echo "domain=" ;;
  esac
}

# Paths we never log (and find prunes most of these)
should_skip() {
  local p="$1"
  case "$p" in
    */RootRecord-Database/Worklog/*|*/RootRecord-Database/Worklog) return 0 ;;
    # Private (Alexander 2026-09-29): never log these trees
    */Desktop/"old txt"/*|*/Desktop/"old txt") return 0 ;;
    */"I'll sort these models tomorrow"/*|*/"I'll sort these models tomorrow") return 0 ;;
    */RootRecord-Database/KEYLOGGER/*|*/RootRecord-Database/KEYLOGGER) return 0 ;;
    */RootRecord-Database/Github/*|*/RootRecord-Database/Github) return 0 ;;
    */.git/*|*/.git) return 0 ;;
    */node_modules/*|*/__pycache__/*|*/.cache/*) return 0 ;;
    */.ollama/models/*|*/.ollama/models) return 0 ;;
    */.ollama/old\ skills/*|*/.ollama/old\ skills) return 0 ;;
    */.ollama/github-history/*|*/.ollama/github-history) return 0 ;;
    */snap/*|*/snap) return 0 ;;
    */.npm/*|*/.gradle/*|*/.cargo/*) return 0 ;;
    *.log|*/logs/store/*|*/logs/*) return 0 ;;
    */.poller.pid|*/.last_scan|*/.hour_start|*/.segment_start|*/.seen_index|*/.seen_dirs|*/poller.out) return 0 ;;
    # Hygiene (WO-RPT-001): never surface agent transcript dumps or obvious secret filenames
    */agent-transcripts/*|*/agent-transcripts) return 0 ;;
    *.jsonl) return 0 ;;
    *credentials*|*.pem|*.p12|*id_rsa*|*id_ed25519*) return 0 ;;
    */master-key.env|*/.cloudflared/*|*/.env|*/.env.*) return 0 ;;
  esac
  return 1
}

# find expression: prune heavy subtrees, then match type+newermt
# Usage: find_changed <since_epoch> <type:f|d>
find_changed() {
  local since="$1" typ="$2"
  find "$HOME_ROOT" -xdev \
    \( \
      -path "$HOME_ROOT/Database/WORKLOG" -o \
      -path "$HOME_ROOT/Desktop/old txt" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem/I'll sort these models tomorrow" -o \
      -path "$HOME_ROOT/Database/KEYLOGGER" -o \
      -path "$HOME_ROOT/Database/GITHUB" -o \
      -path "$HOME_ROOT/.ollama/models" -o \
      -path "$HOME_ROOT/.ollama/old skills" -o \
      -path "$HOME_ROOT/.ollama/github-history" -o \
      -path "$HOME_ROOT/snap" -o \
      -path "$HOME_ROOT/.cache" -o \
      -path "$HOME_ROOT/.npm" -o \
      -path "$HOME_ROOT/.gradle" -o \
      -path "$HOME_ROOT/.cargo" -o \
      -path "$HOME_ROOT/.cloudflared" -o \
      -name .git -o \
      -name node_modules -o \
      -name __pycache__ -o \
      -name agent-transcripts \
    \) -prune -o \
    -type "$typ" -newermt "@${since}" -print 2>/dev/null
}

rotate_if_hour() {
  local now_h old_h seg_start end name
  now_h=$(date '+%Y%m%d%H')
  old_h=$(cat "$HOUR_MARK" 2>/dev/null || echo "$now_h")
  if [[ "$now_h" != "$old_h" ]]; then
    seg_start=$(cat "${WORKLOG_DIR}/.segment_start" 2>/dev/null || echo "$old_h")
    end=$(date '+%Y%m%d-%H%M%S')
    name="${seg_start}-${end}.md"
    [[ -f "$CURRENT" ]] && mv "$CURRENT" "${WORKLOG_DIR}/${name}" && chmod 600 "${WORKLOG_DIR}/${name}" 2>/dev/null || true
    printf '# Worklog current\n\nStarted: %s\nScope: full %s (pruned models/snap/cache/git-blobs)\n\n' \
      "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$HOME_ROOT" > "$CURRENT"
    chmod 600 "$CURRENT" 2>/dev/null || true
    echo "$now_h" > "$HOUR_MARK"
    date '+%Y%m%d-%H%M%S' > "${WORKLOG_DIR}/.segment_start"
  fi
}

scrub_log() {
  [[ -f "$CURRENT" && -f "$ENV_FILE" ]] || return 0
  local tmp patterns=0 key val esc
  tmp=$(mktemp)
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" != *=* ]] && continue
    key="${line%%=*}"; val="${line#*=}"; val="${val%$'\r'}"
    [[ "$val" =~ ^\".*\"$ ]] && val="${val:1:-1}"
    [[ "$val" =~ ^\'.*\'$ ]] && val="${val:1:-1}"
    [[ ${#val} -lt 8 ]] && continue
    if [[ "$key" == *_KEYLOG_DELETE || "$key" == *_WORKLOG_DELETE ]] || \
       { [[ "$key" =~ (KEY|TOKEN|SECRET|PASS|PASSWORD|CRED) ]] && [[ ${#val} -ge 12 ]]; }; then
      esc=$(printf '%s' "$val" | sed -e 's/[\\/&.^$*[\]]/\\&/g')
      printf 's/%s/[REDACTED]/g\n' "$esc" >> "$tmp"
      patterns=$((patterns+1))
    fi
  done < "$ENV_FILE"
  if [[ "$patterns" -gt 0 ]]; then
    sed -f "$tmp" "$CURRENT" > "${CURRENT}.scrub" && mv "${CURRENT}.scrub" "$CURRENT"
    chmod 600 "$CURRENT" 2>/dev/null || true
  fi
  rm -f "$tmp"
}

scan_once() {
  ensure_dirs
  rotate_if_hour
  local now since tmp_list f sz mt key mt_h tag
  now=$(date '+%Y-%m-%d %H:%M:%S %Z')
  since=$(cat "$STATE" 2>/dev/null || date '+%s')
  since=$((since - 90))
  tmp_list=$(mktemp)

  while IFS= read -r f; do
    should_skip "$f" && continue
    [[ -e "$f" ]] || continue
    sz=$(stat -c '%s' "$f" 2>/dev/null || echo 0)
    mt=$(stat -c '%Y' "$f" 2>/dev/null || echo 0)
    key="${f}|${sz}|${mt}"
    grep -Fxq "$key" "$SEEN_FILE" 2>/dev/null && continue
    if grep -F "${f}|" "$SEEN_FILE" >/dev/null 2>&1; then
      printf 'MOD_FILE\t%s\t%s\t%s\n' "$key" "$f" "$sz"
    else
      printf 'NEW_FILE\t%s\t%s\t%s\n' "$key" "$f" "$sz"
    fi
  done < <(find_changed "$since" f) >> "$tmp_list" || true

  while IFS= read -r f; do
    should_skip "$f" && continue
    [[ -d "$f" ]] || continue
    [[ "$f" == "$HOME_ROOT" ]] && continue
    mt=$(stat -c '%Y' "$f" 2>/dev/null || echo 0)
    key="${f}|dir|${mt}"
    grep -Fxq "$f" "$SEEN_DIRS" 2>/dev/null && continue
    printf 'NEW_DIR\t%s\t%s\t0\n' "$key" "$f"
  done < <(find_changed "$since" d) >> "$tmp_list" || true

  local check_tmp
  check_tmp=$(mktemp)
  tail -n 500 "$SEEN_FILE" 2>/dev/null | cut -d'|' -f1 | sort -u > "$check_tmp" || true
  tail -n 300 "$SEEN_DIRS" 2>/dev/null | sort -u >> "$check_tmp" || true
  sort -u "$check_tmp" -o "$check_tmp"
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    should_skip "$f" && continue
    if [[ ! -e "$f" ]]; then
      printf 'DELETED\t%s|gone\t%s\t0\n' "$f" "$f"
    fi
  done < "$check_tmp" >> "$tmp_list" || true
  rm -f "$check_tmp"

  if [[ -s "$tmp_list" ]]; then
    {
      echo "### $now"
      while IFS=$'\t' read -r kind key f sz; do
        [[ -z "${f:-}" ]] && continue
        case "$kind" in
          NEW_FILE|MOD_FILE)
            should_skip "$f" && continue
            mt_h=$(stat -c '%y' "$f" 2>/dev/null | cut -d. -f1 || echo '?')
            sz=$(stat -c '%s' "$f" 2>/dev/null || echo "${sz:-?}")
            tag=$(domain_tag "$f")
            if [[ -n "$tag" && "$tag" != "domain=" ]]; then
              printf -- '- %s %s | size=%s | mtime=%s | %s | source_job=worklog_scan\n' \
                "$kind" "$f" "$sz" "$mt_h" "$tag"
            else
              printf -- '- %s %s | size=%s | mtime=%s | source_job=worklog_scan\n' \
                "$kind" "$f" "$sz" "$mt_h"
            fi
            if [[ -f "$SEEN_FILE" ]]; then
              grep -vF "${f}|" "$SEEN_FILE" > "${SEEN_FILE}.tmp" 2>/dev/null || true
              mv "${SEEN_FILE}.tmp" "$SEEN_FILE"
            fi
            printf '%s\n' "$key" >> "$SEEN_FILE"
            ;;
          NEW_DIR)
            should_skip "$f" && continue
            mt_h=$(stat -c '%y' "$f" 2>/dev/null | cut -d. -f1 || echo '?')
            tag=$(domain_tag "$f")
            if [[ -n "$tag" && "$tag" != "domain=" ]]; then
              printf -- '- NEW_DIR %s | mtime=%s | %s | source_job=worklog_scan\n' "$f" "$mt_h" "$tag"
            else
              printf -- '- NEW_DIR %s | mtime=%s | source_job=worklog_scan\n' "$f" "$mt_h"
            fi
            printf '%s\n' "$f" >> "$SEEN_DIRS"
            ;;
          DELETED)
            printf -- '- DELETED %s | source_job=worklog_scan\n' "$f"
            grep -vF "${f}|" "$SEEN_FILE" > "${SEEN_FILE}.tmp" 2>/dev/null || true
            mv "${SEEN_FILE}.tmp" "$SEEN_FILE" 2>/dev/null || true
            grep -vxF "$f" "$SEEN_DIRS" > "${SEEN_DIRS}.tmp" 2>/dev/null || true
            mv "${SEEN_DIRS}.tmp" "$SEEN_DIRS" 2>/dev/null || true
            ;;
        esac
      done < "$tmp_list"
      echo
    } >> "$CURRENT"
  fi
  rm -f "$tmp_list"
  date '+%s' > "$STATE"
  scrub_log
}
