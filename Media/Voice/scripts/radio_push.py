#!/usr/bin/env python3
"""Send a finished voice report to the Mainland radio library.

Hawaii writes the WAV. This script encodes it and replaces that one
<report>_current.opus over SSH to the desk host ml1 (tunnel hostname
ml1.rootrecord.cloud). The file lands in the runtime reports directory,
outside the git checkout, so a pull cannot restore it. Older copies and
any other name in the reports folder are removed. A report that is still
.ogg stays until this report replaces it. It never downloads. The music
bed arrives with the Mainland git pull.
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
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
VOICE = DB / "Media" / "Audio" / "Voice"
# Desk SSH host name for the tunnel hostname ml1.rootrecord.cloud.
# An address change must not retarget this push at the raw IP.
HOST = os.environ.get("RR_RADIO_SSH", "ml1")
REMOTE = os.environ.get(
    "RR_RADIO_REMOTE",
    "/home/ubuntu/US-Mainland-Server/communications/rootrecord-radio/audio",
)
# Live reports stay outside the git checkout. A pull must not restore an older file.
REPORTS_REMOTE = os.environ.get(
    "RR_RADIO_REPORTS",
    "/home/ubuntu/rootrecord-radio/audio/reports",
)
KEEP_REPORT = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*_current\.(?:ogg|opus)$")
MUSIC = Path(os.environ.get(
    "RR_RADIO_MUSIC",
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/2 - RootRecord-US-Mainland-One/communications/rootrecord-radio/audio/music",
))
REPORT_NAME = re.compile(r"^[a-z0-9_]+$")
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]
# Pacific/Honolulu. End is exclusive. Late wraps past midnight until 09:00.
DAYPARTS = ("morning_report", "midday_report", "late_report")


def hawaii_now() -> datetime:
    return datetime.now(ZoneInfo("Pacific/Honolulu"))


def daypart_open(report: str, when: datetime | None = None) -> bool:
    """True when this id is the one rollup the Hawaii clock may keep."""
    if report not in DAYPARTS:
        return True
    clock = when.astimezone(ZoneInfo("Pacific/Honolulu")) if when is not None else hawaii_now()
    minute = clock.hour * 60 + clock.minute
    if report == "morning_report":
        return 9 * 60 <= minute < 12 * 60
    if report == "midday_report":
        return 12 * 60 <= minute < 21 * 60
    return minute >= 21 * 60 or minute < 9 * 60


def clear_remote_dayparts(keep: str) -> bool:
    """Remove the other two daypart opus and ogg files. Leave every other report."""
    remote_dir = REPORTS_REMOTE.rstrip("/")
    stale: list[str] = []
    for other in DAYPARTS:
        if other == keep:
            continue
        stale.append(remote_dir + "/" + other + "_current.opus")
        stale.append(remote_dir + "/" + other + "_current.ogg")
    cleared = subprocess.run(
        SSH + [HOST, "rm -f -- " + " ".join(shlex.quote(name) for name in stale)],
        capture_output=True,
        text=True,
        timeout=40,
    )
    return cleared.returncode == 0


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
    """Drop remote junk. Keep *_current.ogg and *_current.opus, and partials younger than 15 minutes."""
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
    if report in DAYPARTS and not daypart_open(report):
        return {"ok": False, "skipped": True, "detail": "outside_daypart", "report": report}
    wav = VOICE / f"{report}_current.wav"
    if not wav.is_file():
        return {"ok": False, "detail": "no_wav", "report": report}
    remote_dir = REPORTS_REMOTE.rstrip("/")
    final_name = f"{report}_current.opus"
    partial = remote_dir + "/." + final_name + ".partial"
    final = remote_dir + "/" + final_name
    old_ogg = remote_dir + "/" + f"{report}_current.ogg"
    fd, tmp_name = tempfile.mkstemp(prefix=report + "-", suffix=".opus")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        made = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(wav),
                "-c:a", "libopus", "-b:a", "24k", "-application", "voip", "-ac", "1",
                str(tmp),
            ],
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
                   + " && chmod 644 -- " + shlex.quote(final)
                   + " && rm -f -- " + shlex.quote(old_ogg)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if moved.returncode != 0:
            return {"ok": False, "detail": "replace_failed", "report": report}
        if report in DAYPARTS and not clear_remote_dayparts(report):
            return {"ok": False, "detail": "daypart_clear_failed", "report": report, "file": final_name}
        if not prune_reports():
            return {"ok": False, "detail": "prune_failed", "report": report, "file": final_name}
        staged = stage_on_air(report)
        return {"ok": True, "report": report, "file": final_name, "bytes": tmp.stat().st_size, "stage": staged}
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "detail": "send_failed", "report": report}
    finally:
        tmp.unlink(missing_ok=True)


def air_slot(when: datetime | None = None) -> tuple[int, int]:
    """Next Hawaii :00 or :30 the staged line is waiting for."""
    clock = hawaii_now() if when is None else when.astimezone(ZoneInfo("Pacific/Honolulu"))
    if clock.minute < 30:
        return clock.hour, 30
    return (clock.hour + 1) % 24, 0


def stage_on_air(report: str) -> dict:
    """Upload the staged line if needed, then ask the station to speak it.

    The station plays it after the report that is speaking, or immediately
    when the mixer is quiet. The short notification sound plays first.
    The full spoken clock chime does not.
    """
    import status_cue
    if report not in status_cue.TYPES:
        return {"ok": True, "skipped": True, "detail": "no_stage_type", "report": report}
    hour, minute = air_slot()
    phase = "staged_half" if minute == 30 else "staged_hour"
    wav = status_cue.clip_path(report, phase)
    if wav is None or not wav.is_file():
        return {"ok": False, "detail": "no_cue", "report": report, "phase": phase}
    audio = str(Path(REPORTS_REMOTE).parent)
    runtime = str(Path(audio).parent)
    cue_name = report + ("-half" if minute == 30 else "-hour") + ".opus"
    remote_cue = audio.rstrip("/") + "/cues/" + cue_name
    fd, tmp_name = tempfile.mkstemp(prefix=report + "-stage-", suffix=".opus")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        made = subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav), "-c:a", "libopus", "-b:a", "24k", "-application", "voip", "-ac", "1", str(tmp)],
            capture_output=True,
            timeout=60,
        )
        if made.returncode != 0 or tmp.stat().st_size < 64:
            return {"ok": False, "detail": "encode_failed", "report": report}
        folder = subprocess.run(
            SSH + [HOST, "mkdir -p -- " + shlex.quote(audio.rstrip("/") + "/cues") + " " + shlex.quote(runtime.rstrip("/") + "/state/stage")],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if folder.returncode != 0:
            return {"ok": False, "detail": "remote_dir", "report": report}
        partial = remote_cue + ".partial"
        sent = subprocess.run(
            ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", str(tmp), f"{HOST}:{partial}"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if sent.returncode != 0:
            return {"ok": False, "detail": "send_failed", "report": report}
        moved = subprocess.run(
            SSH + [HOST, "mv -f -- " + shlex.quote(partial) + " " + shlex.quote(remote_cue) + " && chmod 644 -- " + shlex.quote(remote_cue)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if moved.returncode != 0:
            return {"ok": False, "detail": "replace_failed", "report": report}
        note = json.dumps({"id": report, "hour": hour, "minute": minute})
        stamp = f"{int(time.time())}-{report}"
        remote_note = runtime.rstrip("/") + "/state/stage/" + stamp + ".json"
        noted = subprocess.run(
            SSH + [HOST, "printf %s " + shlex.quote(note) + " > " + shlex.quote(remote_note)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if noted.returncode != 0:
            return {"ok": False, "detail": "queue_failed", "report": report}
        return {"ok": True, "report": report, "slot": f"{hour:02d}:{minute:02d}", "file": cue_name}
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
