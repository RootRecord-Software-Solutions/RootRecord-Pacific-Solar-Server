#!/usr/bin/env bash
# ============================================================================
# Reports/scripts/weekly_archive_logs.sh — WO-RPT-001 Phase D / WO-ARCH
# ----------------------------------------------------------------------------
# Move closed human operator logs older than the current HST calendar week into
# Documentation/01-operations/archive/YYYY-Www/
# Does NOT touch Work-Orders (closed WOs → Work-Orders/Complete/).
# Does NOT rewrite content. Prefer git mv when run from a Library git checkout.
# ============================================================================
set -euo pipefail  # info: set

LIBRARY_ROOT="${LIBRARY_ROOT:-/home/rootrecord/RootRecord-Ecosystem/5 - RootRecord-Library}"  # info: set LIBRARY_ROOT
LOG_DIR="${LIBRARY_ROOT}/Documentation/01-operations/0 - Human Operator Work Logs"  # info: set LOG_DIR
ARCHIVE_ROOT="${LIBRARY_ROOT}/Documentation/01-operations/archive"  # info: set ARCHIVE_ROOT
DRY_RUN="${DRY_RUN:-0}"  # info: set DRY_RUN

# ISO week (HST). %u is 1=Monday .. 7=Sunday.
# "monday this week" on GNU date is the upcoming Monday, which would archive
# the current week. Subtract (weekday-1) days so Monday of this week is the cutoff.
WEEK_LABEL="$(TZ=Pacific/Honolulu date '+%G-W%V')"  # info: set WEEK_LABEL
DOW="$(TZ=Pacific/Honolulu date '+%u')"  # info: set DOW
MONDAY="$(TZ=Pacific/Honolulu date -d "$((DOW - 1)) days ago" '+%Y-%m-%d')"  # info: set MONDAY

if [[ -z "${MONDAY:-}" ]]; then  # info: if
  # Fallback: keep last 7 days by string compare only if Monday unknown
  CUTOFF="$(TZ=Pacific/Honolulu date -d '7 days ago' '+%Y-%m-%d' 2>/dev/null || TZ=Pacific/Honolulu date '+%Y-%m-%d')"  # info: set CUTOFF
else  # info: else
  CUTOFF="$MONDAY"  # info: set CUTOFF
fi  # info: fi

DEST="${ARCHIVE_ROOT}/${WEEK_LABEL}"  # info: set DEST
mkdir -p "$DEST"  # info: mkdir

moved=0  # info: set moved
skipped=0  # info: set skipped

if [[ ! -d "$LOG_DIR" ]]; then  # info: if
  echo "No log dir: $LOG_DIR" >&2  # info: echo
  exit 0  # info: exit
fi  # info: fi

shopt -s nullglob  # info: shopt
for f in "$LOG_DIR"/*.md; do  # info: for
  base=$(basename "$f")  # info: set base
  # Expect leading YYYY-MM-DD
  if [[ ! "$base" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})[[:space:]] ]]; then  # info: if
    skipped=$((skipped+1))  # info: set skipped
    continue  # info: continue
  fi  # info: fi
  fdate="${BASH_REMATCH[1]}"  # info: set fdate
  # Keep current week (fdate >= CUTOFF)
  if [[ "$fdate" > "$CUTOFF" || "$fdate" == "$CUTOFF" ]]; then  # info: if
    skipped=$((skipped+1))  # info: set skipped
    continue  # info: continue
  fi  # info: fi
  # Skip Session auto from today only already handled by cutoff
  if [[ "$DRY_RUN" == "1" ]]; then  # info: if
    echo "DRY would move: $base → archive/${WEEK_LABEL}/"  # info: echo
  else  # info: else
    if [[ -d "${LIBRARY_ROOT}/.git" ]]; then  # info: if
      (cd "$LIBRARY_ROOT" && git mv -f \
        "Documentation/01-operations/0 - Human Operator Work Logs/${base}" \
        "Documentation/01-operations/archive/${WEEK_LABEL}/${base}" 2>/dev/null) \
        || mv -f "$f" "${DEST}/${base}"  # info: command
    else  # info: else
      mv -f "$f" "${DEST}/${base}"  # info: mv
    fi  # info: fi
    echo "Moved: $base"  # info: echo
  fi  # info: fi
  moved=$((moved+1))  # info: set moved
done  # info: done

echo "OK weekly archive week=${WEEK_LABEL} cutoff=${CUTOFF} moved=${moved} skipped=${skipped} dry=${DRY_RUN}"  # info: echo
