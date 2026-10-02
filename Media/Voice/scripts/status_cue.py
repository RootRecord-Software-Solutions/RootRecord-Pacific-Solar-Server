#!/usr/bin/env python3
# ==============================================================================
# status_cue.py — four prebuilt local lines per desk. No chime. No Kokoro here.
# starting plays before render. transit plays as the send starts.
# failed plays when the send does not land. sent plays after Mainland One
# has the file (radio_push ffprobe + mv). RR_VOICE_STATUS=0 skips playback.
# ==============================================================================
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
CLIPS = Path(os.environ.get("RR_VOICE_CLIPS", str(DB / "Media" / "Audio" / "Voice" / "Clips")))
STACK_STATE = Path(os.environ.get("RR_VOICE_STACK_STATE", str(DB / "Reports" / "Voice" / "stack-send.json")))
CLOSER = ("Ava", "stack_all_sent", "All reports have been sent successfully. Heavy work may resume.")

# Nine generating desks. The hourly chime is a replay of files, not a render.
TYPES = {
    "system_perf": ("Bruce", "System"),
    "nws_weather": ("Ava", "NWS"),
    "remaining_tasks": ("Bruce", "Remaining tasks"),
    "earthquake_report": ("Carly", "Earthquake"),
    "kilauea_report": ("Carly", "Kilauea"),
    "solar_desk": ("Bruce", "Solar"),
    "security_desk": ("Carly", "Security"),
    "bandwidth_desk": ("Carly", "Bandwidth"),
    "current_report": ("Ava", "Current"),
}

# News is not part of the :12 / :42 stack. Its cues still play, and a send still stages it.
CUES = dict(TYPES)
CUES["news_update"] = ("Ava", "News")

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
    for report, (persona, label) in CUES.items():
        for phase, template in PHASES + STAGED:
            rows.append({
                "persona": persona,
                "slug": f"{report}_{phase}",
                "text": template.format(label=label),
                "kinds": [report, "status"],
                "source": "local status cue",
            })
    persona, slug, text = CLOSER
    rows.append({
        "persona": persona,
        "slug": slug,
        "text": text,
        "kinds": ["status"],
        "source": "local status cue",
    })
    return rows


def cycle_key(when: datetime) -> str:
    """The :12 or :42 stack this clock still belongs to. A run past the hour stays on :42."""
    if when.minute >= 42:
        slot, stamp = 42, when
    elif when.minute >= 12:
        slot, stamp = 12, when
    else:
        slot, stamp = 42, when - timedelta(hours=1)
    return stamp.strftime("%Y-%m-%dT%H") + f":{slot:02d}"


def _load_stack() -> dict:
    try:
        row = json.loads(STACK_STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"cycle": "", "ok": [], "announced": False}
    if not isinstance(row, dict):
        return {"cycle": "", "ok": [], "announced": False}
    ok = row.get("ok") if isinstance(row.get("ok"), list) else []
    return {"cycle": str(row.get("cycle") or ""), "ok": [str(x) for x in ok], "announced": bool(row.get("announced"))}


def _save_stack(row: dict) -> None:
    STACK_STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STACK_STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STACK_STATE)


def note_sent(report: str, when: datetime | None = None) -> dict | None:
    """Remember a Mainland receipt. Speak the closer once the ten desks have all landed this cycle."""
    if report not in TYPES:
        return None
    clock = when or datetime.now().astimezone()
    key = cycle_key(clock)
    row = _load_stack()
    if row["cycle"] != key:
        row = {"cycle": key, "ok": [], "announced": False}
    if report not in row["ok"]:
        row["ok"].append(report)
    ready = (not row["announced"]) and set(TYPES) <= set(row["ok"])
    closer = play_closer() if ready else None
    if closer and closer.get("ok"):
        row["announced"] = True
    _save_stack(row)
    return closer


def clip_path(report: str, phase: str) -> Path | None:
    row = CUES.get(report)
    if row is None:
        return None
    persona, _label = row
    return CLIPS / persona / f"{report}_{phase}.wav"


def play_closer() -> dict:
    """Local line after every desk in the cycle has been received."""
    persona, slug, _text = CLOSER
    path = CLIPS / persona / f"{slug}.wav"
    if os.environ.get("RR_VOICE_STATUS", "1") == "0":
        return {"ok": True, "skipped": True, "detail": "status_off", "phase": "stack_all_sent"}
    if not path.is_file():
        return {"ok": False, "detail": "audio_missing", "phase": "stack_all_sent", "wav": str(path)}
    try:
        subprocess.run(["aplay", "-q", str(path)], check=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "detail": "play_failed", "phase": "stack_all_sent", "error": str(exc)[:200]}
    return {"ok": True, "played": True, "phase": "stack_all_sent", "wav": str(path)}


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
        sent = play(report, "sent")
        closer = note_sent(report)
        if closer:
            sent = dict(sent, stack=closer)
        return sent
    if radio.get("skipped"):
        return {"ok": True, "skipped": True, "detail": "send_skipped", "phase": "sent"}
    return play(report, "failed")
