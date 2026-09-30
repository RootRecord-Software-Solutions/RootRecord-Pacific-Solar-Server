#!/usr/bin/env python3
"""Append Hawaii radar frames the live poller already saved into one all-time zip.

Does not fetch. Does not delete dated folders. Does not rewrite the zip in memory.
A second run adds nothing when every frame name is already a zip member.

  python3 radar_zip.py
"""
from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
LIVE_ARCHIVE = (
    DB / "Weather" / "Hawai'i" / "hfo" / "radar.weather.gov" / "ridge" / "standard" / "HAWAII_loop" / "archive"
)
PREVIOUS = DB / "Archive" / "Previous-Datasets"
OUT = DB / "Weather" / "RadarZip"
ZIP_PATH = OUT / "radar_archive.zip"
STATE_PATH = OUT / "radar-archive.json"
LOG_DIR = DB / "Logs" / "Weather" / "RadarZip"
LOG_PATH = LOG_DIR / "radar_zip.log"


def _gif_files() -> list[Path]:
    """Live dated archive first, then retention copies. One path per filename."""
    found: dict[str, Path] = {}

    def take(path: Path) -> None:
        if not path.is_file() or path.suffix.lower() != ".gif":
            return
        found.setdefault(path.name, path)

    if LIVE_ARCHIVE.is_dir():
        for path in sorted(LIVE_ARCHIVE.rglob("*.gif")):
            take(path)

    if PREVIOUS.is_dir():
        for root in sorted(PREVIOUS.glob("Weather-*")):
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("HAWAII_loop_*.gif")):
                rel = str(path)
                if "radar.weather.gov" in rel or "HAWAII_loop" in rel:
                    take(path)

    return [found[name] for name in sorted(found)]


def _existing_names(zip_path: Path) -> set[str]:
    if not zip_path.is_file():
        return set()
    with zipfile.ZipFile(zip_path, "r") as archive:
        return set(archive.namelist())


def append_frames() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    frames = _gif_files()
    already = _existing_names(ZIP_PATH)
    added: list[str] = []
    pending = [(path, path.name) for path in frames if path.name not in already]
    if pending:
        with zipfile.ZipFile(ZIP_PATH, "a", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, name in pending:
                archive.write(path, arcname=name)
                added.append(name)
        already = _existing_names(ZIP_PATH)

    payload = {
        "ok": True,
        "zip": str(ZIP_PATH),
        "member_count": len(already),
        "added_count": len(added),
        "added": added,
        "frame_count": len(frames),
        "live_archive": str(LIVE_ARCHIVE),
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),
    }
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATE_PATH)
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(
            f"{payload['updated_at']} added={payload['added_count']} members={payload['member_count']}\n"
        )
    return payload


def main() -> int:
    payload = append_frames()
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
