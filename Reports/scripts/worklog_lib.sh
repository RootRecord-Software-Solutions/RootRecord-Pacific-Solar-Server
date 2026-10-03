#!/usr/bin/env bash
# Offline work auto-doc — FULL /home/rootrecord (pruned blobs).
# Path/size/mtime only. NO keystrokes, mouse, clipboard, or file contents.
# Pacific Reports/ (WO-RPT-001). Ported from G2 reports/scripts with hygiene enhancements.
set -euo pipefail  # info: set

WORKLOG_DIR="${WORKLOG_DIR:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Worklog}"  # info: set WORKLOG_DIR
CURRENT="${WORKLOG_DIR}/worklog_current.md"  # info: set CURRENT
STATE="${WORKLOG_DIR}/.last_scan"  # info: set STATE
HOUR_MARK="${WORKLOG_DIR}/.hour_start"  # info: set HOUR_MARK
ENV_FILE="${ENV_FILE:-/home/rootrecord/master/master-key.env}"  # info: set ENV_FILE
PID_FILE="${WORKLOG_DIR}/.poller.pid"  # info: set PID_FILE
SEEN_FILE="${WORKLOG_DIR}/.seen_index"  # info: set SEEN_FILE
SEEN_DIRS="${WORKLOG_DIR}/.seen_dirs"  # info: set SEEN_DIRS
HOME_ROOT="/home/rootrecord"  # info: set HOME_ROOT
PACIFIC_ECO="${PACIFIC_ECO:-/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server}"  # info: set PACIFIC_ECO

# ====================================================
# SECTION: function ensure_dirs
# What it does: ensure dirs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ensure_dirs() {  # info: ensure_dirs
  mkdir -p "$WORKLOG_DIR"  # info: mkdir
  chmod 700 "$WORKLOG_DIR" 2>/dev/null || true  # info: chmod
  if [[ ! -f "$CURRENT" ]]; then  # info: if
    printf '# Worklog current\n\nStarted: %s\nScope: full %s (pruned models/snap/cache/git-blobs)\n\n' \
      "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$HOME_ROOT" > "$CURRENT"  # info: command
    chmod 600 "$CURRENT" 2>/dev/null || true  # info: chmod
  fi  # info: fi
  [[ -f "$HOUR_MARK" ]] || date '+%Y%m%d%H' > "$HOUR_MARK"  # info: command
  [[ -f "${WORKLOG_DIR}/.segment_start" ]] || date '+%Y%m%d-%H%M%S' > "${WORKLOG_DIR}/.segment_start"  # info: command
  [[ -f "$STATE" ]] || date '+%s' > "$STATE"  # info: command
  [[ -f "$SEEN_FILE" ]] || : > "$SEEN_FILE"  # info: command
  [[ -f "$SEEN_DIRS" ]] || : > "$SEEN_DIRS"  # info: command
}  # info: command

# Tag Pacific domain when path is under a known domain folder (enhancement).
# ====================================================
# SECTION: function domain_tag
# What it does: domain tag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
domain_tag() {  # info: domain_tag
  local p="$1"  # info: local
  case "$p" in  # info: case
    *"/RootRecord-Pacific-Solar-Server/Automations"*|*/Automations/*) echo "domain=Automations" ;;  # info: command
    *"/RootRecord-Pacific-Solar-Server/Energy"*|*/Energy/*) echo "domain=Energy" ;;  # info: command
    *"/RootRecord-Pacific-Solar-Server/System"*|*/System/*) echo "domain=System" ;;  # info: command
    *"/RootRecord-Pacific-Solar-Server/Reports"*|*/Reports/*) echo "domain=Reports" ;;  # info: command
    *"/RootRecord-Pacific-Solar-Server/Communications"*|*/Communications/*) echo "domain=Communications" ;;  # info: command
    *"/RootRecord-Pacific-Solar-Server/Github"*|*/Github/*) echo "domain=Github" ;;  # info: command
    *"/RootRecord-Pacific-Solar-Server/Weather"*|*/Weather/*) echo "domain=Weather" ;;  # info: command
    *"/RootRecord-Pacific-Solar-Server/Geology"*|*/Geology/*) echo "domain=Geology" ;;  # info: command
    *"/RootRecord-Pacific-Solar-Server/Security"*|*/Security/*) echo "domain=Security" ;;  # info: command
    *"/RootRecord-Library"*|*/RootRecord-Library/*) echo "domain=Library" ;;  # info: command
    *"/Database/"*) echo "domain=Database" ;;  # info: command
    *) echo "domain=" ;;  # info: command
  esac  # info: esac
}  # info: command

# Paths we never log (and find prunes most of these)
# ====================================================
# SECTION: function should_skip
# What it does: should skip.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
should_skip() {  # info: should_skip
  local p="$1"  # info: local
  case "$p" in  # info: case
    */RootRecord-Database/Worklog/*|*/RootRecord-Database/Worklog) return 0 ;;  # info: command
    # Private (Alexander 2026-09-29): never log these trees
    */Desktop/"old txt"/*|*/Desktop/"old txt") return 0 ;;  # info: command
    */"I'll sort these models tomorrow"/*|*/"I'll sort these models tomorrow") return 0 ;;  # info: command
    */RootRecord-Database/KEYLOGGER/*|*/RootRecord-Database/KEYLOGGER) return 0 ;;  # info: command
    */RootRecord-Database/Github/*|*/RootRecord-Database/Github) return 0 ;;  # info: command
    */.git/*|*/.git) return 0 ;;  # info: command
    */node_modules/*|*/__pycache__/*|*/.cache/*) return 0 ;;  # info: command
    */.ollama/models/*|*/.ollama/models) return 0 ;;  # info: command
    */.ollama/old\ skills/*|*/.ollama/old\ skills) return 0 ;;  # info: command
    */.ollama/github-history/*|*/.ollama/github-history) return 0 ;;  # info: command
    */snap/*|*/snap) return 0 ;;  # info: command
    */.npm/*|*/.gradle/*|*/.cargo/*) return 0 ;;  # info: command
    *.log|*/logs/store/*|*/logs/*) return 0 ;;  # info: command
    */.poller.pid|*/.last_scan|*/.hour_start|*/.segment_start|*/.seen_index|*/.seen_dirs|*/poller.out) return 0 ;;  # info: command
    # Hygiene (WO-RPT-001): never surface agent transcript dumps or obvious secret filenames
    */agent-transcripts/*|*/agent-transcripts) return 0 ;;  # info: command
    *.jsonl) return 0 ;;  # info: command
    *credentials*|*.pem|*.p12|*id_rsa*|*id_ed25519*) return 0 ;;  # info: command
    */master-key.env|*/.cloudflared/*|*/.env|*/.env.*) return 0 ;;  # info: command
    */.venv/*|*/.venv) return 0 ;;  # info: command
    */old\ ollama/*|*/old\ ollama) return 0 ;;  # info: command
    */RootRecord-Ecosystem-SNAPSHOT/*|*/RootRecord-Ecosystem-SNAPSHOT) return 0 ;;  # info: command
    */RootRecord-Ecosystem-SNAPSHOT-CLEAN/*|*/RootRecord-Ecosystem-SNAPSHOT-CLEAN) return 0 ;;  # info: command
    */.config/*|*/.config) return 0 ;;  # info: command
    */Media/Images/*|*/Media/Images|*/Media/Timelapses/*|*/Media/Timelapses) return 0 ;;  # info: command
    */Energy/samples/*|*/Energy/samples|*/Energy/layers/*|*/Energy/layers|*/System/samples/*|*/System/samples|*/System/layers/*|*/System/layers) return 0 ;;  # info: command
  esac  # info: esac
  return 1  # info: return
}  # info: command

# find expression: prune heavy subtrees, then match type+newermt
# Usage: find_changed <since_epoch> <type:f|d>
# ====================================================
# SECTION: function find_changed
# What it does: find changed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
find_changed() {  # info: find_changed
  local since="$1" typ="$2"  # info: local
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
      -path "$HOME_ROOT/old ollama" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem-SNAPSHOT" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem-SNAPSHOT-CLEAN" -o \
      -path "$HOME_ROOT/.config" -o \
      -name .git -o \
      -name node_modules -o \
      -name __pycache__ -o \
      -name .venv -o \
      -name agent-transcripts -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Images" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Timelapses" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/samples" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem/2 - RootRecord-Database/System/samples" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/layers" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem/2 - RootRecord-Database/System/layers" -o \
      -path "$HOME_ROOT/RootRecord-Ecosystem/2 - RootRecord-Database/Logs" \
    \) -prune -o \
    -type "$typ" -newermt "@${since}" -print 2>/dev/null  # info: -type
}  # info: command

# ====================================================
# SECTION: function rotate_if_hour
# What it does: rotate if hour.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
rotate_if_hour() {  # info: rotate_if_hour
  local now_h old_h seg_start end name  # info: local
  now_h=$(date '+%Y%m%d%H')  # info: set now_h
  old_h=$(cat "$HOUR_MARK" 2>/dev/null || echo "$now_h")  # info: set old_h
  if [[ "$now_h" != "$old_h" ]]; then  # info: if
    seg_start=$(cat "${WORKLOG_DIR}/.segment_start" 2>/dev/null || echo "$old_h")  # info: set seg_start
    end=$(date '+%Y%m%d-%H%M%S')  # info: set end
    name="${seg_start}-${end}.md"  # info: set name
    [[ -f "$CURRENT" ]] && mv "$CURRENT" "${WORKLOG_DIR}/${name}" && chmod 600 "${WORKLOG_DIR}/${name}" 2>/dev/null || true  # info: command
    printf '# Worklog current\n\nStarted: %s\nScope: full %s (pruned models/snap/cache/git-blobs)\n\n' \
      "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$HOME_ROOT" > "$CURRENT"  # info: command
    chmod 600 "$CURRENT" 2>/dev/null || true  # info: chmod
    echo "$now_h" > "$HOUR_MARK"  # info: echo
    date '+%Y%m%d-%H%M%S' > "${WORKLOG_DIR}/.segment_start"  # info: date
  fi  # info: fi
}  # info: command

# ====================================================
# SECTION: function scrub_log
# What it does: scrub log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
scrub_log() {  # info: scrub_log
  [[ -f "$CURRENT" && -f "$ENV_FILE" ]] || return 0  # info: command
  local tmp patterns=0 key val esc  # info: local
  tmp=$(mktemp)  # info: set tmp
  while IFS= read -r line || [[ -n "$line" ]]; do  # info: while
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue  # info: command
    [[ "$line" != *=* ]] && continue  # info: command
    key="${line%%=*}"; val="${line#*=}"; val="${val%$'\r'}"
    [[ "$val" =~ ^\".*\"$ ]] && val="${val:1:-1}"  # info: command
    [[ "$val" =~ ^\'.*\'$ ]] && val="${val:1:-1}"  # info: command
    [[ ${#val} -lt 8 ]] && continue
    if [[ "$key" == *_KEYLOG_DELETE || "$key" == *_WORKLOG_DELETE ]] || \
       { [[ "$key" =~ (KEY|TOKEN|SECRET|PASS|PASSWORD|CRED) ]] && [[ ${#val} -ge 12 ]]; }; then
      esc=$(printf '%s' "$val" | sed -e 's/[\\/&.^$*[\]]/\\&/g')  # info: set esc
      printf 's/%s/[REDACTED]/g\n' "$esc" >> "$tmp"  # info: printf
      patterns=$((patterns+1))  # info: set patterns
    fi  # info: fi
  done < "$ENV_FILE"  # info: done
  if [[ "$patterns" -gt 0 ]]; then  # info: if
    sed -f "$tmp" "$CURRENT" > "${CURRENT}.scrub" && mv "${CURRENT}.scrub" "$CURRENT"  # info: sed
    chmod 600 "$CURRENT" 2>/dev/null || true  # info: chmod
  fi  # info: fi
  rm -f "$tmp"  # info: rm
}  # info: command

# ====================================================
# SECTION: function scan_once
# What it does: scan once.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
scan_once() {  # info: scan_once
  ensure_dirs  # info: ensure_dirs
  rotate_if_hour  # info: rotate_if_hour
  local now since tmp_list f sz mt key mt_h tag  # info: local
  now=$(date '+%Y-%m-%d %H:%M:%S %Z')  # info: set now
  since=$(cat "$STATE" 2>/dev/null || date '+%s')  # info: set since
  since=$((since - 90))  # info: set since
  tmp_list=$(mktemp)  # info: set tmp_list

  while IFS= read -r f; do  # info: while
    should_skip "$f" && continue  # info: should_skip
    [[ -e "$f" ]] || continue  # info: command
    sz=$(stat -c '%s' "$f" 2>/dev/null || echo 0)  # info: set sz
    mt=$(stat -c '%Y' "$f" 2>/dev/null || echo 0)  # info: set mt
    key="${f}|${sz}|${mt}"  # info: set key
    grep -Fxq "$key" "$SEEN_FILE" 2>/dev/null && continue  # info: grep
    if grep -F "${f}|" "$SEEN_FILE" >/dev/null 2>&1; then  # info: if
      printf 'MOD_FILE\t%s\t%s\t%s\n' "$key" "$f" "$sz"  # info: printf
    else  # info: else
      printf 'NEW_FILE\t%s\t%s\t%s\n' "$key" "$f" "$sz"  # info: printf
    fi  # info: fi
  done < <(find_changed "$since" f) >> "$tmp_list" || true  # info: done

  while IFS= read -r f; do  # info: while
    should_skip "$f" && continue  # info: should_skip
    [[ -d "$f" ]] || continue  # info: command
    [[ "$f" == "$HOME_ROOT" ]] && continue  # info: command
    mt=$(stat -c '%Y' "$f" 2>/dev/null || echo 0)  # info: set mt
    key="${f}|dir|${mt}"  # info: set key
    grep -Fxq "$f" "$SEEN_DIRS" 2>/dev/null && continue  # info: grep
    printf 'NEW_DIR\t%s\t%s\t0\n' "$key" "$f"  # info: printf
  done < <(find_changed "$since" d) >> "$tmp_list" || true  # info: done

  local check_tmp  # info: local
  check_tmp=$(mktemp)  # info: set check_tmp
  tail -n 500 "$SEEN_FILE" 2>/dev/null | cut -d'|' -f1 | sort -u > "$check_tmp" || true  # info: tail
  tail -n 300 "$SEEN_DIRS" 2>/dev/null | sort -u >> "$check_tmp" || true  # info: tail
  sort -u "$check_tmp" -o "$check_tmp"  # info: sort
  while IFS= read -r f; do  # info: while
    [[ -z "$f" ]] && continue  # info: command
    should_skip "$f" && continue  # info: should_skip
    if [[ ! -e "$f" ]]; then  # info: if
      printf 'DELETED\t%s|gone\t%s\t0\n' "$f" "$f"  # info: printf
    fi  # info: fi
  done < "$check_tmp" >> "$tmp_list" || true  # info: done
  rm -f "$check_tmp"  # info: rm

  if [[ -s "$tmp_list" ]]; then  # info: if
    {  # info: command
      echo "### $now"
      while IFS=$'\t' read -r kind key f sz; do  # info: while
        [[ -z "${f:-}" ]] && continue  # info: command
        case "$kind" in  # info: case
          NEW_FILE|MOD_FILE)  # info: NEW_FILE
            should_skip "$f" && continue  # info: should_skip
            mt_h=$(stat -c '%y' "$f" 2>/dev/null | cut -d. -f1 || echo '?')  # info: set mt_h
            sz=$(stat -c '%s' "$f" 2>/dev/null || echo "${sz:-?}")  # info: set sz
            tag=$(domain_tag "$f")  # info: set tag
            if [[ -n "$tag" && "$tag" != "domain=" ]]; then  # info: if
              printf -- '- %s %s | size=%s | mtime=%s | %s | source_job=worklog_scan\n' \
                "$kind" "$f" "$sz" "$mt_h" "$tag"  # info: command
            else  # info: else
              printf -- '- %s %s | size=%s | mtime=%s | source_job=worklog_scan\n' \
                "$kind" "$f" "$sz" "$mt_h"  # info: command
            fi  # info: fi
            if [[ -f "$SEEN_FILE" ]]; then  # info: if
              grep -vF "${f}|" "$SEEN_FILE" > "${SEEN_FILE}.tmp" 2>/dev/null || true  # info: grep
              mv "${SEEN_FILE}.tmp" "$SEEN_FILE"  # info: mv
            fi  # info: fi
            printf '%s\n' "$key" >> "$SEEN_FILE"  # info: printf
            ;;  # info: command
          NEW_DIR)  # info: NEW_DIR
            should_skip "$f" && continue  # info: should_skip
            mt_h=$(stat -c '%y' "$f" 2>/dev/null | cut -d. -f1 || echo '?')  # info: set mt_h
            tag=$(domain_tag "$f")  # info: set tag
            if [[ -n "$tag" && "$tag" != "domain=" ]]; then  # info: if
              printf -- '- NEW_DIR %s | mtime=%s | %s | source_job=worklog_scan\n' "$f" "$mt_h" "$tag"  # info: printf
            else  # info: else
              printf -- '- NEW_DIR %s | mtime=%s | source_job=worklog_scan\n' "$f" "$mt_h"  # info: printf
            fi  # info: fi
            printf '%s\n' "$f" >> "$SEEN_DIRS"  # info: printf
            ;;  # info: command
          DELETED)  # info: DELETED
            printf -- '- DELETED %s | source_job=worklog_scan\n' "$f"  # info: printf
            grep -vF "${f}|" "$SEEN_FILE" > "${SEEN_FILE}.tmp" 2>/dev/null || true  # info: grep
            mv "${SEEN_FILE}.tmp" "$SEEN_FILE" 2>/dev/null || true  # info: mv
            grep -vxF "$f" "$SEEN_DIRS" > "${SEEN_DIRS}.tmp" 2>/dev/null || true  # info: grep
            mv "${SEEN_DIRS}.tmp" "$SEEN_DIRS" 2>/dev/null || true  # info: mv
            ;;  # info: command
        esac  # info: esac
      done < "$tmp_list"  # info: done
      echo  # info: echo
    } >> "$CURRENT"  # info: command
  fi  # info: fi
  rm -f "$tmp_list"  # info: rm
  date '+%s' > "$STATE"  # info: date
  scrub_log  # info: scrub_log
}  # info: command
