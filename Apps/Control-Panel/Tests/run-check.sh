# ==============================================================================
# FILE: Apps/Control-Panel/Tests/run-check.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# run-check.sh — headless test for Root Monitor (added 2026-09-29; settings/SSH/network pages 2026-09-29 pm). No window is shown.
# Runs --check with the camera viewer OFF and ON at nice 10 under /usr/bin/time and strace,
# and proves that with the viewer OFF no camera image under Media/Images is opened or listed
# and no connection to cam_server :8791 is made. Writes results to $OUT (default /tmp).
set -uo pipefail  # info: set
HERE="$(cd "$(dirname "$0")/.." && pwd)"  # info: set HERE
OUT="${1:-/tmp/rr-control-panel-check}"  # info: set OUT
mkdir -p "$OUT"  # info: mkdir
avail_mb=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)  # info: set avail_mb
if (( avail_mb < 2048 )); then echo "BLOCKED: MemAvailable ${avail_mb} MB < 2048 MB"; exit 3; fi  # info: if
rc=0  # info: set rc
for mode in off on; do  # info: for
  echo "=== --check --camera-viewer $mode (MemAvailable ${avail_mb} MB) ==="  # info: echo
  /usr/bin/time -v -o "$OUT/time-$mode.txt" nice -n 10 /usr/bin/python3 "$HERE/rr_control_panel.py" --check --camera-viewer "$mode" \
    >"$OUT/check-$mode.txt" 2>"$OUT/check-$mode.err" || rc=1  # info: command
  cat "$OUT/check-$mode.txt"  # info: cat
  grep -E 'Maximum resident|User time|System time|Elapsed' "$OUT/time-$mode.txt"  # info: grep
  if command -v strace >/dev/null 2>&1; then  # info: if
    nice -n 10 strace -f -qq -e trace=openat,open,getdents64,connect -o "$OUT/strace-$mode.txt" \
      /usr/bin/python3 "$HERE/rr_control_panel.py" --check --no-starlink --camera-viewer "$mode" >/dev/null 2>&1 || true  # info: /usr/bin/python3
    imgs=$(grep -c 'Media/Images' "$OUT/strace-$mode.txt" || true)  # info: set imgs
    conns=$(grep -E 'connect\(' "$OUT/strace-$mode.txt" | grep -c 'sin_port=htons(8791)' || true)  # info: set conns
    echo "strace ($mode): Media/Images syscalls=$imgs · connects to :8791=$conns"  # info: echo
    if [[ "$mode" == off && ( "$imgs" != 0 || "$conns" != 0 ) ]]; then echo "FAIL: camera work while viewer OFF"; rc=1; fi  # info: if
  fi  # info: fi
done  # info: done
echo "=== settings editor unit tests (temporary copies only) ==="  # info: echo
nice -n 10 /usr/bin/python3 "$HERE/Tests/test_settings_io.py" | tee "$OUT/test-settings-io.txt" || rc=1  # info: nice
echo "=== toggle-button tests (no window; AWS ssh stubbed, nothing written) ==="  # info: echo
nice -n 10 /usr/bin/python3 "$HERE/Tests/test_toggle_buttons.py" | tee "$OUT/test-toggle-buttons.txt" || rc=1  # info: nice
exit $rc  # info: exit
