#!/usr/bin/env python3
"""Request reconnect clips after night sleep. Does not open a speaker.

  python3 sunrise_restore.py [--dry-run]

Runs only when Database Media/SunriseRestore/pending.json has pending true.
Reads Energy sun times (no network). Asks Report playback for Ava/battery_reconnect
then Ava/boot_all_systems_running. A missing player or a missing clip is skipped.
Clears pending either way. --dry-run never calls the player and sets played false.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
PACIFIC = Path(os.environ.get(
    "RR_PACIFIC_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server",
))
PENDING = DB / "Media" / "SunriseRestore" / "pending.json"
SUN = DB / "Energy" / "sun" / "sun-times-last.json"
LOG = DB / "Logs" / "Media" / "SunriseRestore" / "sunrise-restore.log"
PLAY = PACIFIC / "Media" / "Playback" / "scripts" / "play.py"
CLIPS = ("battery_reconnect", "boot_all_systems_running")


def _now() -> str:
    return datetime.now(HST).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _log(row: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _sunrise() -> str:
    return str(_read_json(SUN).get("sunrise") or "")


def _request(slug: str, *, dry_run: bool) -> dict:
    if dry_run or not PLAY.is_file():
        return {
            "clip": slug,
            "played": False,
            "reason": None if dry_run else "player_missing",
        }
    cmd = [sys.executable, str(PLAY), "--clip", f"Ava/{slug}", "--dry-run"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"clip": slug, "played": False, "reason": type(exc).__name__}
    detail = None
    line = (proc.stdout or "").strip().splitlines()
    if line:
        try:
            detail = json.loads(line[-1]).get("detail")
        except ValueError:
            detail = None
    if proc.returncode != 0 and not detail:
        detail = f"player_rc_{proc.returncode}"
    return {"clip": slug, "played": False, "reason": detail}


def maybe_run(*, dry_run: bool = False) -> dict:
    state = _read_json(PENDING)
    if not state.get("pending"):
        out = {"ok": True, "skipped": True, "reason": "not_pending", "played": False}
        return out
    clips = [_request(slug, dry_run=dry_run) for slug in CLIPS]
    cleared = {**state, "pending": False, "cleared_at": _now()}
    _write_json(PENDING, cleared)
    out = {
        "ok": True,
        "ran": True,
        "clips": [row["clip"] for row in clips],
        "played": False,
        "sunrise": _sunrise(),
        "player": str(PLAY) if PLAY.is_file() else "missing",
        "requests": clips,
    }
    _log({"at": _now(), **out})
    return out


def main() -> int:
    out = maybe_run(dry_run="--dry-run" in sys.argv)
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
