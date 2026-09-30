#!/usr/bin/env python3
"""Play one Kokoro WAV already on disk. Speakers stay closed unless gated.

  python3 play.py --report NAME [--dry-run | --play] [--force]
  python3 play.py --clip Persona/slug [--dry-run | --play] [--force]

Default is --dry-run. That writes last-play.json and does not open a device.
Live play needs both RR_PLAYBACK=1 and --play, then uses aplay.
Quiet hours 22:00–06:00 HST skip a live play unless --force.
--force does not bypass RR_PLAYBACK. A second caller gets busy.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
DB = Path(os.environ.get(
    "RR_DATABASE_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
))
VOICE = DB / "Media" / "Audio" / "Voice"
STATE = DB / "Media" / "Playback"
LOG_DIR = DB / "Logs" / "Media" / "Playback"
LAST = STATE / "last-play.json"
LOCK = STATE / "play.lock"
PERSONAS = {"Ava", "Bruce", "Carly"}
NAME = re.compile(r"[A-Za-z0-9_-]+")
CLIP = re.compile(r"(Ava|Bruce|Carly)/[A-Za-z0-9_-]+")


def now_hst() -> datetime:
    return datetime.now(HST)


def quiet_hours(now: datetime | None = None) -> bool:
    hour = (now or now_hst()).hour
    return hour >= 22 or hour < 6


def resolve(report: str | None, clip: str | None) -> Path:
    """Map a report name or Persona/slug onto a WAV under Voice. Refuse anything else."""
    if bool(report) == bool(clip):
        raise ValueError("pass one of --report or --clip")
    if report is not None:
        if not NAME.fullmatch(report):
            raise ValueError("refused")
        path = (VOICE / f"{report}_current.wav").resolve()
    else:
        if not CLIP.fullmatch(clip or ""):
            raise ValueError("refused")
        persona, slug = (clip or "").split("/", 1)
        if persona not in PERSONAS:
            raise ValueError("refused")
        path = (VOICE / "Clips" / persona / f"{slug}.wav").resolve()
    voice = VOICE.resolve()
    if not path.is_relative_to(voice):
        raise ValueError("refused")
    return path


def emit(payload: dict, code: int, *, state: bool = True) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    body = dict(payload)
    body["at"] = now_hst().isoformat()
    if state:
        LAST.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    line = json.dumps(body, ensure_ascii=False)
    with (LOG_DIR / "playback.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play one existing Kokoro WAV.")
    parser.add_argument("--report", help="Voice/<name>_current.wav")
    parser.add_argument("--clip", help="Voice/Clips/<Persona>/<slug>.wav")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Record intent. Do not open a device.")
    mode.add_argument("--play", action="store_true", help="Open the speaker. Needs RR_PLAYBACK=1.")
    parser.add_argument("--force", action="store_true", help="Allow live play during quiet hours.")
    args = parser.parse_args(argv)
    dry = not args.play

    try:
        path = resolve(args.report, args.clip)
    except ValueError as exc:
        detail = "refused" if str(exc) == "refused" else "bad_args"
        return emit({
            "ok": False,
            "played": False,
            "detail": detail,
            "report": args.report,
            "clip": args.clip,
        }, 1)

    STATE.mkdir(parents=True, exist_ok=True)
    lock_fh = LOCK.open("a", encoding="utf-8")
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_fh.close()
        # Do not overwrite last-play.json. The holder of the lock owns that file.
        return emit({
            "ok": True,
            "played": False,
            "detail": "busy",
            "report": args.report,
            "clip": args.clip,
            "path": str(path),
        }, 3, state=False)

    present = path.is_file() and path.stat().st_size > 0
    base = {
        "report": args.report,
        "clip": args.clip,
        "path": str(path),
        "played": False,
    }
    try:
        if dry:
            base["ok"] = True
            base["detail"] = "dry_run" if present else "audio_missing"
            return emit(base, 0)

        if os.environ.get("RR_PLAYBACK", "0") != "1":
            base["ok"] = False
            base["detail"] = "playback_gated"
            return emit(base, 2)

        if quiet_hours() and not args.force:
            base["ok"] = True
            base["detail"] = "quiet_hours"
            return emit(base, 0)

        if not present:
            base["ok"] = True
            base["detail"] = "audio_missing"
            return emit(base, 0)

        try:
            subprocess.run(["aplay", "-q", str(path)], check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            base["ok"] = False
            base["detail"] = "play_failed"
            base["error"] = str(exc)[:200]
            return emit(base, 1)

        base["ok"] = True
        base["played"] = True
        base["detail"] = "played"
        return emit(base, 0)
    finally:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        lock_fh.close()


if __name__ == "__main__":
    sys.exit(main())
