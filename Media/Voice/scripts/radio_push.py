#!/usr/bin/env python3
"""Send a finished voice report to the Mainland radio library.

Hawaii writes the WAV. This script encodes it and copies that one file up
over SSH. It never downloads. Music is a separate one-way copy of the
library that already sits on this desk.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
VOICE = DB / "Media" / "Audio" / "Voice"
HOST = os.environ.get("RR_RADIO_SSH", "rr-aws-ip")
REMOTE = os.environ.get(
    "RR_RADIO_REMOTE",
    "/home/ubuntu/US-Mainland-Server/communications/rootrecord-radio/audio",
)
MUSIC = Path(os.environ.get(
    "RR_RADIO_MUSIC",
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/2 - RootRecord-US-Mainland-Server/communications/rootrecord-radio/audio/music",
))
REPORT_NAME = re.compile(r"^[a-z0-9_]+$")
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]


def push_report(report: str) -> dict:
    if not REPORT_NAME.fullmatch(report):
        return {"ok": False, "detail": "bad_report"}
    wav = VOICE / f"{report}_current.wav"
    if not wav.is_file():
        return {"ok": False, "detail": "no_wav", "report": report}
    remote_dir = REMOTE.rstrip("/") + "/reports"
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
        moved = subprocess.run(
            SSH + [HOST, "mv -f -- " + shlex.quote(partial) + " " + shlex.quote(final)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if moved.returncode != 0:
            return {"ok": False, "detail": "replace_failed", "report": report}
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
