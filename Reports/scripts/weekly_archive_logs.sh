#!/usr/bin/env bash
# ============================================================================
# Reports/scripts/weekly_archive_logs.sh — WO-RPT-001 Phase D / WO-ARCH
# ----------------------------------------------------------------------------
# Move closed human operator logs older than the current HST calendar week into
# Documentation/01-operations/archive/YYYY-Www/
# Does NOT touch Work-Orders (closed WOs → Work-Orders/Complete/).
# Does NOT rewrite content. Prefer git mv when run from a Library git checkout.
# ============================================================================
set -euo pipefail

LIBRARY_ROOT="${LIBRARY_ROOT:-/home/rootrecord/RootRecord-Ecosystem/5 - RootRecord-Library}"
LOG_DIR="${LIBRARY_ROOT}/Documentation/01-operations/0 - Human Operator Work Logs"
ARCHIVE_ROOT="${LIBRARY_ROOT}/Documentation/01-operations/archive"
DRY_RUN="${DRY_RUN:-0}"

# ISO week (HST)
WEEK_LABEL="$(TZ=Pacific/Honolulu date '+%G-W%V')"
# Start of current week Monday 00:00 HST as epoch (approx via date)
# Files named YYYY-MM-DD ... — archive if date < this week's Monday
MONDAY="$(TZ=Pacific/Honolulu date -d 'monday this week' '+%Y-%m-%d' 2>/dev/null \
  || TZ=Pacific/Honolulu date -d 'last monday' '+%Y-%m-%d' 2>/dev/null \
  || true)"

if [[ -z "${MONDAY:-}" ]]; then
  # Fallback: keep last 7 days by string compare only if Monday unknown
  CUTOFF="$(TZ=Pacific/Honolulu date -d '7 days ago' '+%Y-%m-%d' 2>/dev/null || TZ=Pacific/Honolulu date '+%Y-%m-%d')"
else
  CUTOFF="$MONDAY"
fi

DEST="${ARCHIVE_ROOT}/${WEEK_LABEL}"
mkdir -p "$DEST"

moved=0
skipped=0

if [[ ! -d "$LOG_DIR" ]]; then
  echo "No log dir: $LOG_DIR" >&2
  exit 0
fi

shopt -s nullglob
for f in "$LOG_DIR"/*.md; do
  base=$(basename "$f")
  # Expect leading YYYY-MM-DD
  if [[ ! "$base" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})[[:space:]] ]]; then
    skipped=$((skipped+1))
    continue
  fi
  fdate="${BASH_REMATCH[1]}"
  # Keep current week (fdate >= CUTOFF)
  if [[ "$fdate" > "$CUTOFF" || "$fdate" == "$CUTOFF" ]]; then
    skipped=$((skipped+1))
    continue
  fi
  # Skip Session auto from today only already handled by cutoff
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "DRY would move: $base → archive/${WEEK_LABEL}/"
  else
    if [[ -d "${LIBRARY_ROOT}/.git" ]]; then
      (cd "$LIBRARY_ROOT" && git mv -f \
        "Documentation/01-operations/0 - Human Operator Work Logs/${base}" \
        "Documentation/01-operations/archive/${WEEK_LABEL}/${base}" 2>/dev/null) \
        || mv -f "$f" "${DEST}/${base}"
    else
      mv -f "$f" "${DEST}/${base}"
    fi
    echo "Moved: $base"
  fi
  moved=$((moved+1))
done

echo "OK weekly archive week=${WEEK_LABEL} cutoff=${CUTOFF} moved=${moved} skipped=${skipped} dry=${DRY_RUN}"
