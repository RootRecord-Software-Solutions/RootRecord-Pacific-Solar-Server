#!/usr/bin/env python3
"""Send a finished voice report to the ML1 radio library.

Hawaii writes the WAV. This script encodes it and replaces that one
<report>_current.opus on the radio tree.

Modes (RR_RADIO_MODE):
  remote — SSH/SCP to live ML1 host only
  local  — write into desk US-Mainland-One/rootrecord-radio/ (ML1 down fail-safe)
  auto   — try remote; on SSH failure fall back to local (default)

Live remote reports stay under /home/ubuntu/rootrecord-radio/audio/reports
(outside git). Local fail-safe uses the desk checkout so the station can run
via ML1 ./station.sh when the host is not transmitting.
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
ML1_DESK = Path(
    os.environ.get(
        "RR_RADIO_LOCAL_ROOT",
        "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/2 - RootRecord-US-Mainland-One/rootrecord-radio",
    )
)
# Desk SSH host name for the tunnel hostname ml1.rootrecord.cloud.
HOST = os.environ.get("RR_RADIO_SSH", "ml1")
REMOTE = os.environ.get(
    "RR_RADIO_REMOTE",
    "/home/ubuntu/rootrecord-radio/audio",
)
# Live reports stay outside the git checkout on the remote host.
REPORTS_REMOTE = os.environ.get(
    "RR_RADIO_REPORTS",
    "/home/ubuntu/rootrecord-radio/audio/reports",
)
KEEP_REPORT = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*_current\.(?:ogg|opus)$")
MUSIC = Path(
    os.environ.get(
        "RR_RADIO_MUSIC",
        str(ML1_DESK / "audio" / "music"),
    )
)
REPORT_NAME = re.compile(r"^[a-z0-9_]+$")
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]
DAYPARTS = ("morning_report", "midday_report", "late_report")


def radio_mode() -> str:
    """remote | local | auto."""
    v = (os.environ.get("RR_RADIO_MODE") or "auto").strip().lower()
    if v in {"remote", "ssh", "ml1"}:
        return "remote"
    if v in {"local", "desk", "failsafe", "1", "true"}:
        return "local"
    return "auto"


def ml1_reachable() -> bool:
    try:
        r = subprocess.run(
            SSH + [HOST, "true"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def use_local() -> bool:
    mode = radio_mode()
    if mode == "local":
        return True
    if mode == "remote":
        return False
    return not ml1_reachable()


def local_reports_dir() -> Path:
    return ML1_DESK / "audio" / "reports"


def local_audio_dir() -> Path:
    return ML1_DESK / "audio"


def local_runtime_dir() -> Path:
    return ML1_DESK


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


def clear_dayparts(keep: str, *, local: bool) -> bool:
    """Remove the other two daypart opus and ogg files. Leave every other report."""
    if local:
        root = local_reports_dir()
        root.mkdir(parents=True, exist_ok=True)
        for other in DAYPARTS:
            if other == keep:
                continue
            for suf in ("_current.opus", "_current.ogg"):
                path = root / f"{other}{suf}"
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    return False
        return True
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


def prune_reports(*, local: bool) -> bool:
    """Drop junk. Keep *_current.ogg/opus and partials younger than 15 minutes."""
    if local:
        prune_tree(local_reports_dir())
        return True
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


def _encode_opus(wav: Path, tmp: Path) -> bool:
    made = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(wav),
            "-c:a", "libopus", "-b:a", "24k", "-application", "voip", "-ac", "1",
            str(tmp),
        ],
        capture_output=True,
        timeout=180,
    )
    return made.returncode == 0 and tmp.is_file() and tmp.stat().st_size >= 64


def push_report_local(report: str, wav: Path) -> dict:
    """Fail-safe: bank opus into desk ML1 rootrecord-radio/audio/reports/."""
    reports = local_reports_dir()
    reports.mkdir(parents=True, exist_ok=True)
    final_name = f"{report}_current.opus"
    final = reports / final_name
    partial = reports / f".{final_name}.partial"
    old_ogg = reports / f"{report}_current.ogg"
    fd, tmp_name = tempfile.mkstemp(prefix=report + "-", suffix=".opus")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        if not _encode_opus(wav, tmp):
            return {"ok": False, "detail": "encode_failed", "report": report, "mode": "local"}
        partial.write_bytes(tmp.read_bytes())
        if audio_duration(partial) < 0.2:
            partial.unlink(missing_ok=True)
            return {"ok": False, "detail": "invalid_audio", "report": report, "mode": "local"}
        os.replace(partial, final)
        final.chmod(0o644)
        old_ogg.unlink(missing_ok=True)
        if report in DAYPARTS and not clear_dayparts(report, local=True):
            return {"ok": False, "detail": "daypart_clear_failed", "report": report, "mode": "local"}
        if not prune_reports(local=True):
            return {"ok": False, "detail": "prune_failed", "report": report, "mode": "local"}
        staged = stage_on_air(report, local=True)
        return {
            "ok": True,
            "report": report,
            "file": final_name,
            "bytes": final.stat().st_size,
            "mode": "local",
            "path": str(final),
            "stage": staged,
        }
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "detail": "local_write_failed", "report": report, "mode": "local"}
    finally:
        tmp.unlink(missing_ok=True)
        partial.unlink(missing_ok=True)


def push_report(report: str) -> dict:
    if not REPORT_NAME.fullmatch(report):
        return {"ok": False, "detail": "bad_report"}
    if report in DAYPARTS and not daypart_open(report):
        return {"ok": False, "skipped": True, "detail": "outside_daypart", "report": report}
    wav = VOICE / f"{report}_current.wav"
    if not wav.is_file():
        return {"ok": False, "detail": "no_wav", "report": report}

    local = use_local()
    if local:
        return push_report_local(report, wav)

    remote_dir = REPORTS_REMOTE.rstrip("/")
    final_name = f"{report}_current.opus"
    partial = remote_dir + "/." + final_name + ".partial"
    final = remote_dir + "/" + final_name
    old_ogg = remote_dir + "/" + f"{report}_current.ogg"
    fd, tmp_name = tempfile.mkstemp(prefix=report + "-", suffix=".opus")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        if not _encode_opus(wav, tmp):
            return {"ok": False, "detail": "encode_failed", "report": report, "mode": "remote"}
        folder = subprocess.run(
            SSH + [HOST, "mkdir -p -- " + shlex.quote(remote_dir)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if folder.returncode != 0:
            if radio_mode() == "auto":
                return push_report_local(report, wav)
            return {"ok": False, "detail": "remote_dir", "report": report, "mode": "remote"}
        sent = subprocess.run(
            ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", str(tmp), f"{HOST}:{partial}"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if sent.returncode != 0:
            if radio_mode() == "auto":
                return push_report_local(report, wav)
            return {"ok": False, "detail": "send_failed", "report": report, "mode": "remote"}
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
            return {"ok": False, "detail": "invalid_audio", "report": report, "mode": "remote"}
        moved = subprocess.run(
            SSH + [HOST, "mv -f -- " + shlex.quote(partial) + " " + shlex.quote(final)
                   + " && chmod 644 -- " + shlex.quote(final)
                   + " && rm -f -- " + shlex.quote(old_ogg)],
            capture_output=True,
            text=True,
            timeout=40,
        )
        if moved.returncode != 0:
            return {"ok": False, "detail": "replace_failed", "report": report, "mode": "remote"}
        if report in DAYPARTS and not clear_dayparts(report, local=False):
            return {"ok": False, "detail": "daypart_clear_failed", "report": report, "file": final_name}
        if not prune_reports(local=False):
            return {"ok": False, "detail": "prune_failed", "report": report, "file": final_name}
        staged = stage_on_air(report, local=False)
        return {"ok": True, "report": report, "file": final_name, "bytes": tmp.stat().st_size, "mode": "remote", "stage": staged}
    except (OSError, subprocess.TimeoutExpired):
        if radio_mode() == "auto":
            return push_report_local(report, wav)
        return {"ok": False, "detail": "send_failed", "report": report, "mode": "remote"}
    finally:
        tmp.unlink(missing_ok=True)


def air_slot(when: datetime | None = None) -> tuple[int, int]:
    """Next Hawaii :00 or :30 the staged line is waiting for."""
    clock = hawaii_now() if when is None else when.astimezone(ZoneInfo("Pacific/Honolulu"))
    if clock.minute < 30:
        return clock.hour, 30
    return (clock.hour + 1) % 24, 0


def stage_on_air(report: str, *, local: bool | None = None) -> dict:
    """Upload/stage the cue line. Local fail-safe writes into desk ML1 tree."""
    import status_cue
    if report not in status_cue.CUES:
        return {"ok": True, "skipped": True, "detail": "no_stage_type", "report": report}
    if local is None:
        local = use_local()
    hour, minute = air_slot()
    phase = "staged_half" if minute == 30 else "staged_hour"
    wav = status_cue.clip_path(report, phase)
    if wav is None or not wav.is_file():
        return {"ok": False, "detail": "no_cue", "report": report, "phase": phase}
    cue_name = report + ("-half" if minute == 30 else "-hour") + ".opus"
    fd, tmp_name = tempfile.mkstemp(prefix=report + "-stage-", suffix=".opus")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        if not _encode_opus(wav, tmp):
            return {"ok": False, "detail": "encode_failed", "report": report}
        if local:
            cues = local_audio_dir() / "cues"
            stage = local_runtime_dir() / "state" / "stage"
            cues.mkdir(parents=True, exist_ok=True)
            stage.mkdir(parents=True, exist_ok=True)
            dest = cues / cue_name
            dest.write_bytes(tmp.read_bytes())
            dest.chmod(0o644)
            note = {"id": report, "hour": hour, "minute": minute}
            (stage / f"{int(time.time())}-{report}.json").write_text(
                json.dumps(note) + "\n", encoding="utf-8"
            )
            return {
                "ok": True,
                "report": report,
                "slot": f"{hour:02d}:{minute:02d}",
                "file": cue_name,
                "mode": "local",
            }
        audio = str(Path(REPORTS_REMOTE).parent)
        runtime = str(Path(audio).parent)
        remote_cue = audio.rstrip("/") + "/cues/" + cue_name
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
        return {"ok": True, "report": report, "slot": f"{hour:02d}:{minute:02d}", "file": cue_name, "mode": "remote"}
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "detail": "send_failed", "report": report}
    finally:
        tmp.unlink(missing_ok=True)


def push_music() -> dict:
    if not MUSIC.is_dir():
        return {"ok": False, "detail": "no_music"}
    if use_local():
        dest = local_audio_dir() / "music"
        dest.mkdir(parents=True, exist_ok=True)
        sent = subprocess.run(
            ["rsync", "-a", str(MUSIC) + "/", str(dest) + "/"],
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if sent.returncode != 0:
            return {"ok": False, "detail": "local_sync_failed", "mode": "local"}
        return {"ok": True, "music": str(dest), "mode": "local"}
    remote_dir = REMOTE.rstrip("/") + "/music"
    folder = subprocess.run(
        SSH + [HOST, "mkdir -p -- " + shlex.quote(remote_dir)],
        capture_output=True,
        text=True,
        timeout=40,
    )
    if folder.returncode != 0:
        return {"ok": False, "detail": "remote_dir", "mode": "remote"}
    sent = subprocess.run(
        ["rsync", "-a", "-e", "ssh -o BatchMode=yes -o ConnectTimeout=20", str(MUSIC) + "/", f"{HOST}:{remote_dir}/"],
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if sent.returncode != 0:
        return {"ok": False, "detail": "send_failed", "mode": "remote"}
    return {"ok": True, "music": str(MUSIC), "mode": "remote"}


HOUR_DESKS = (
    "system_perf",
    "nws_weather",
    "remaining_tasks",
    "earthquake_report",
    "hurricane_desk",
    "kilauea_report",
    "kilauea_image_check",
    "solar_desk",
    "security_desk",
    "bandwidth_desk",
    "current_report",
)


def push_all() -> dict:
    """Encode every finished hour desk WAV and replace it on ML1 in this send window."""
    results = []
    ok = True
    sent = 0
    for report in HOUR_DESKS:
        if not (VOICE / f"{report}_current.wav").is_file():
            results.append({"ok": True, "skipped": True, "detail": "no_wav", "report": report})
            continue
        one = push_report(report)
        results.append(one)
        if one.get("ok") and not one.get("skipped"):
            sent += 1
        elif not one.get("ok") and not one.get("skipped"):
            ok = False
    return {"ok": ok, "sent": sent, "pushed": results}


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--music":
        result = push_music()
    elif len(sys.argv) == 2 and sys.argv[1] == "--all":
        result = push_all()
    elif len(sys.argv) == 2 and REPORT_NAME.fullmatch(sys.argv[1]):
        result = push_report(sys.argv[1])
    else:
        result = {"ok": False, "detail": "usage: radio_push.py <report>|--all|--music"}
    print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
