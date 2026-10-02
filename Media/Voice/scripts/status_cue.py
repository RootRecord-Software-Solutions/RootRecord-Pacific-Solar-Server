#!/usr/bin/env python3
# ==============================================================================
# status_cue.py — four prebuilt local lines per desk. No chime. No Kokoro here.
# starting plays before render. transit plays as the send starts.
# failed plays when the send does not land. sent plays after Mainland One
# has the file (radio_push ffprobe + mv). RR_VOICE_STATUS=0 skips playback.
# ==============================================================================
from __future__ import annotations

import os
import subprocess
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
CLIPS = Path(os.environ.get("RR_VOICE_CLIPS", str(DB / "Media" / "Audio" / "Voice" / "Clips")))

# Ten generating desks. The hourly chime is a replay of files, not a render.
TYPES = {
    "system_perf": ("Bruce", "System"),
    "nws_weather": ("Ava", "NWS"),
    "energy_report": ("Carly", "Energy"),
    "remaining_tasks": ("Bruce", "Remaining tasks"),
    "earthquake_report": ("Carly", "Earthquake"),
    "kilauea_report": ("Carly", "Kilauea"),
    "solar_desk": ("Bruce", "Solar"),
    "security_desk": ("Carly", "Security"),
    "bandwidth_desk": ("Carly", "Bandwidth"),
    "current_report": ("Ava", "Current"),
}

PHASES = (
    ("starting", "{label} report is about to generate."),
    ("transit", "{label} report has been generated and is in transit."),
    ("failed", "{label} report was generated but failed to send."),
    ("sent", "{label} report was sent successfully."),
)

# The slot is named in the line. The station plays the short notification sound before it.
STAGED = (
    ("staged_hour", "{label} report has been staged for the hour."),
    ("staged_half", "{label} report has been staged for the half hour."),
)


def catalog_rows() -> list[dict]:
    rows = []
    for report, (persona, label) in TYPES.items():
        for phase, template in PHASES + STAGED:
            rows.append({
                "persona": persona,
                "slug": f"{report}_{phase}",
                "text": template.format(label=label),
                "kinds": [report, "status"],
                "source": "local status cue",
            })
    return rows


def clip_path(report: str, phase: str) -> Path | None:
    row = TYPES.get(report)
    if row is None:
        return None
    persona, _label = row
    return CLIPS / persona / f"{report}_{phase}.wav"


def play(report: str, phase: str) -> dict:
    """Play one prebuilt line. A missing file or a gated flag does not fail the report."""
    if os.environ.get("RR_VOICE_STATUS", "1") == "0":
        return {"ok": True, "skipped": True, "detail": "status_off", "phase": phase}
    path = clip_path(report, phase)
    if path is None:
        return {"ok": True, "skipped": True, "detail": "no_status_type", "phase": phase}
    if not path.is_file():
        return {"ok": False, "detail": "audio_missing", "phase": phase, "wav": str(path)}
    try:
        subprocess.run(["aplay", "-q", str(path)], check=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "detail": "play_failed", "phase": phase, "error": str(exc)[:200]}
    return {"ok": True, "played": True, "phase": phase, "wav": str(path)}


def after_push(report: str, radio: dict | None) -> dict | None:
    """Success is the Mainland receipt. A skip is not a failed send."""
    if not radio:
        return None
    if radio.get("ok"):
        return play(report, "sent")
    if radio.get("skipped"):
        return {"ok": True, "skipped": True, "detail": "send_skipped", "phase": "sent"}
    return play(report, "failed")
