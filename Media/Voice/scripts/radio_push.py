#!/usr/bin/env python3
"""Send a finished voice report to the Mainland radio library.

Hawaii writes the WAV. This script encodes it and replaces that one
<report>_current.ogg over SSH. Older copies and any other name in the
reports folder are removed. It never downloads. Music is a separate
one-way copy of the library that already sits on this desk.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
VOICE = DB / "Media" / "Audio" / "Voice"
HOST = os.environ.get("RR_RADIO_SSH", "rr-aws-ip")
REMOTE = os.environ.get(
    "RR_RADIO_REMOTE",
    "/home/ubuntu/US-Mainland-Server/communications/rootrecord-radio/audio",
)
# Live reports stay outside the git checkout. A pull must not restore an older file.
REPORTS_REMOTE = os.environ.get(
    "RR_RADIO_REPORTS",
    "/home/ubuntu/rootrecord-radio/audio/reports",
)
KEEP_REPORT = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*_current\.ogg$")
MUSIC = Path(os.environ.get(
    "RR_RADIO_MUSIC",
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/2 - RootRecord-US-Mainland-Server/communications/rootrecord-radio/audio/music",
))
REPORT_NAME = re.compile(r"^[a-z0-9_]+$")
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]


PARTIAL_AGE = 15 * 60


def prune_tree(root: Path, now: float | None = None) -> list[str]:
    """Remove junk from a reports directory. Keep live names and fresh partials."""
    removed: list[str] = []
    stamp = time.time() if now is None else now
    root.mkdir(parents=True, exist_ok=True)
    for name in os.listdir(root):
        path = root / name
        if not path.is_file() and not path.is_symlink():
            continue
        if name == ".gitkeep" or KEEP_REPORT.fullmatch(name):
            continue
        if name.endswith(".partial"):
            age = stamp - path.stat().st_mtime
            if age < PARTIAL_AGE:
                continue
        path.unlink()
        removed.append(name)
    return removed


def audio_duration(path: Path) -> float:
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=40,
    )
    if probe.returncode != 0:
        return 0.0
    try:
        return float((probe.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        return 0.0


def prune_reports() -> bool:
    """Drop remote junk. Keep *_current.ogg and partials younger than 15 minutes."""
    remote_dir = REPORTS_REMOTE.rstrip("/")
    script = (
        "RR_RADIO_REPORTS=" + shlex.quote(remote_dir)
        + " RR_RADIO_KEEP=" + shlex.quote(KEEP_REPORT.pattern)
        + " RR_RADIO_PARTIAL_AGE=" + str(PARTIAL_AGE)
        + " python3 - <<'PY'\n"
        "import os, re, time\n"
        "root = os.environ['RR_RADIO_REPORTS']\n"
        "keep = re.compile(os.environ['RR_RADIO_KEEP'])\n"
        "max_age = int(os.environ['RR_RADIO_PARTIAL_AGE'])\n"
        "now = time.time()\n"
        "os.makedirs(root, exist_ok=True)\n"
        "for name in os.listdir(root):\n"
        "    path = os.path.join(root, name)\n"
        "    if not os.path.isfile(path) and not os.path.islink(path):\n"
        "        continue\n"
        "    if name == '.gitkeep' or keep.fullmatch(name):\n"
        "        continue\n"
        "    if name.endswith('.partial') and now - os.path.getmtime(path) < max_age:\n"
        "        continue\n"
        "    os.remove(path)\n"
        "PY"
    )
    cleaned = subprocess.run(
        SSH + [HOST, script],
        capture_output=True,
        text=True,
        timeout=40,
    )
    return cleaned.returncode == 0


def push_report(report: str) -> dict:
    if not REPORT_NAME.fullmatch(report):
        return {"ok": False, "detail": "bad_report"}
    wav = VOICE / f"{report}_current.wav"
    if not wav.is_file():
        return {"ok": False, "detail": "no_wav", "report": report}
    remote_dir = REPORTS_REMOTE.rstrip("/")
    final_name = f"{report}_current.ogg"
    partial = remote_dir + "/." + final_name + ".partial"
    final = remote_dir + "/" + final_name
    fd, tmp_name = tempfile.mkstemp(prefix=report + "-", suffix=".ogg")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        made = subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "5", str(tmp)],
            capture_output=True,
            timeout=180,
        )
        if made.returncode != 0 or not tmp.is_file() or tmp.stat().st_size < 64:
            return {"ok": False, "detail": "encode_failed", "report": report}
        folder = subprocess.run(
            SSH + [HOST, "mkdir -p -- " + shlex.quote(remote_dir)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if folder.returncode != 0:
            return {"ok": False, "detail": "remote_dir", "report": report}
        sent = subprocess.run(
            ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", str(tmp), f"{HOST}:{partial}"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if sent.returncode != 0:
            return {"ok": False, "detail": "send_failed", "report": report}
        checked = subprocess.run(
            SSH + [HOST, "ffprobe -v error -select_streams a:0 -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "
                   + shlex.quote(partial)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        duration = 0.0
        try:
            duration = float((checked.stdout or "").strip().splitlines()[-1])
        except (ValueError, IndexError):
            duration = 0.0
        if checked.returncode != 0 or duration < 0.2:
            subprocess.run(
                SSH + [HOST, "rm -f -- " + shlex.quote(partial)],
                capture_output=True,
                text=True,
                timeout=40,
            )
            return {"ok": False, "detail": "invalid_audio", "report": report}
        moved = subprocess.run(
            SSH + [HOST, "mv -f -- " + shlex.quote(partial) + " " + shlex.quote(final)
                   + " && chmod 644 -- " + shlex.quote(final)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if moved.returncode != 0:
            return {"ok": False, "detail": "replace_failed", "report": report}
        if not prune_reports():
            return {"ok": False, "detail": "prune_failed", "report": report, "file": final_name}
        return {"ok": True, "report": report, "file": final_name, "bytes": tmp.stat().st_size}
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "detail": "send_failed", "report": report}
    finally:
        tmp.unlink(missing_ok=True)


def push_music() -> dict:
    if not MUSIC.is_dir():
        return {"ok": False, "detail": "no_music"}
    remote_dir = REMOTE.rstrip("/") + "/music"
    folder = subprocess.run(
        SSH + [HOST, "mkdir -p -- " + shlex.quote(remote_dir)],
        capture_output=True,
        text=True,
        timeout=40,
    )
    if folder.returncode != 0:
        return {"ok": False, "detail": "remote_dir"}
    sent = subprocess.run(
        ["rsync", "-a", "-e", "ssh -o BatchMode=yes -o ConnectTimeout=20", str(MUSIC) + "/", f"{HOST}:{remote_dir}/"],
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if sent.returncode != 0:
        return {"ok": False, "detail": "send_failed"}
    return {"ok": True, "music": str(MUSIC)}


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--music":
        result = push_music()
    elif len(sys.argv) == 2 and REPORT_NAME.fullmatch(sys.argv[1]):
        result = push_report(sys.argv[1])
    else:
        result = {"ok": False, "detail": "usage: radio_push.py <report>|--music"}
    print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
