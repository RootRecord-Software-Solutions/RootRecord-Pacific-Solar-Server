#!/usr/bin/env bash
# ==============================================================================
# voice-render.sh — run voice_generate.py through the RootRecord inference lock.
# Usage: voice-render.sh render|stitch|clips [voice_generate.py args…]
# Single-flight (System/scripts/plumbing/single-flight.sh): refuses (rc 75) if an inference
# or another render holds the lock. nice 10. The Kokoro model lives only inside this one
# process and is freed when it exits (non-resident). No delivery, no playback.
# Added 2026-09-29 (g3-voice-ailog).
# ==============================================================================
set -u  # info: set
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set HERE
PACIFIC="$(cd "$HERE/../../.." && pwd)"  # info: set PACIFIC
SF="$PACIFIC/System/scripts/plumbing/single-flight.sh"  # info: set SF
PY="${RR_VOICE_PY:-$PACIFIC/Media/Voice/.venv/bin/python}"  # info: set PY
[[ -x "$PY" ]] || { echo '{"ok": false, "detail": "voice venv missing: Media/Voice/.venv"}'; exit 3; }  # info: command
MODE="${1:?render|stitch|clips}"  # info: set MODE
exec "$SF" run "voice:$MODE:$(date +%Y%m%d-%H%M%S)" -- nice -n 10 "$PY" "$HERE/voice_generate.py" "$@"  # info: exec
