#!/usr/bin/env python3
"""a-eyes timelapse engine — hourly compile, end-of-day master stitch, boot catch-up.

Directory source of truth: this file does NOT hardcode a separate project
root. It imports DB_FRAMES straight from grab_frame.py (the only script
allowed to write into the Database) and derives every other folder from it,
so there is exactly one place (grab_frame.py) that defines where camera
data lives.

    database/a-eyes/                     == DB_FRAMES.parent
    ├── frames/                          == DB_FRAMES   (grab_frame.py writes here, already timestamped)
    ├── video_chunks/                    hour_HH.mp4 per completed hour (05–18)
    ├── final_output/                    master_stitched_timelapse.mp4 only (no GIF)
    └── _archive/YYYYMMDD/hour_HH/       frames moved here after a successful hourly compile

Pipeline:
    1. Every hour (05–18 HST): stitch that hour's frames → video_chunks/hour_HH.mp4
    2. At 19:01 HST: concat all 14 hourly MP4s → final_output/master_stitched_timelapse.mp4

Usage:
    python3 timelapse_engine.py hourly [--hour HH] [--date YYYYMMDD]   # compile one completed hour
    python3 timelapse_engine.py daily  [--date YYYYMMDD]               # stitch the day (MP4 only)
    python3 timelapse_engine.py catchup                                # boot-time: do whatever was missed
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from grab_frame import DB_FRAMES, frames_lock, FramesBusy  # noqa: E402

# ---------------------------------------------------------------------------
# Derived directories — all hang off DB_FRAMES, never re-typed by hand.
# ---------------------------------------------------------------------------
BASE = DB_FRAMES.parent                       # /home/rootrecord/Database/A-EYES
FRAMES = DB_FRAMES                             # .../frames
VIDEO_CHUNKS = BASE / "video_chunks"
FINAL_OUTPUT = BASE / "final_output"
ARCHIVE = BASE / "_archive"

# ---------------------------------------------------------------------------
# Config (env-overridable)
# ---------------------------------------------------------------------------
import os
from zoneinfo import ZoneInfo

CHANNEL = int(os.environ.get("A_EYES_TIMELAPSE_CHANNEL", "1"))
LOCAL_TZ = ZoneInfo(os.environ.get("A_EYES_TIMELAPSE_TZ", "Pacific/Honolulu"))
WINDOW_START_HOUR = int(os.environ.get("A_EYES_TIMELAPSE_START_HOUR", "5"))   # 5:00 AM
WINDOW_END_HOUR = int(os.environ.get("A_EYES_TIMELAPSE_END_HOUR", "19"))     # 7:00 PM exclusive → last hour is 18
TARGET_TOTAL_SECONDS = float(os.environ.get("A_EYES_TIMELAPSE_TOTAL_SEC", "180"))  # 3 min master
MASTER_FPS = int(os.environ.get("A_EYES_TIMELAPSE_FPS", "68"))
ARCHIVE_NOT_DELETE = os.environ.get("A_EYES_TIMELAPSE_ARCHIVE", "1") != "0"

WINDOW_HOURS = WINDOW_END_HOUR - WINDOW_START_HOUR                # 14 (05–18 inclusive)
SECONDS_PER_HOUR_CHUNK = TARGET_TOTAL_SECONDS / WINDOW_HOURS       # ~12.86s per hour


def log(msg: str) -> None:
    ts = datetime.now(LOCAL_TZ).strftime("%H:%M:%S")
    print(f"  {ts}  \U0001F3AC  a-eyes-timelapse  {msg}", flush=True)


def _now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def _frame_local_dt(p: Path) -> datetime | None:
    """grab_frame.py stamps filenames as ch<N>-YYYYMMDDTHHMMSSZ.jpg in UTC."""
    try:
        ts_part = p.stem.split("-", 1)[1]
        dt_utc = datetime.strptime(ts_part, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC"))
        return dt_utc.astimezone(LOCAL_TZ)
    except (IndexError, ValueError):
        return None


def _hour_frames(date_str: str, hour: int) -> list[Path]:
    """Every frame for local date_str / hour on CHANNEL, oldest first."""
    out = []
    for p in FRAMES.glob(f"ch{CHANNEL}-*.jpg"):
        local_dt = _frame_local_dt(p)
        if local_dt and local_dt.strftime("%Y%m%d") == date_str and local_dt.hour == hour:
            out.append((local_dt, p))
    out.sort(key=lambda t: t[0])
    return [p for _, p in out]


def _run_ffmpeg(cmd: list[str], *, timeout: int = 900) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    err = (r.stderr or r.stdout or "").strip()
    if r.returncode != 0 and not err:
        err = "ffmpeg failed with no stderr (exit {})".format(r.returncode)
    return r.returncode, err[:500]


def compile_hour(date_str: str, hour: int, *, force: bool = False) -> Path | None:
    """Compile one completed hour's frames into video_chunks/hour_HH.mp4."""
    VIDEO_CHUNKS.mkdir(parents=True, exist_ok=True)
    out_path = VIDEO_CHUNKS / f"hour_{hour:02d}.mp4"
    if out_path.is_file() and not force:
        try:
            with frames_lock(blocking=True, timeout=30):
                leftovers = _hour_frames(date_str, hour)
                if leftovers:
                    _retire_frames(date_str, hour, leftovers)
        except FramesBusy:
            pass
        log(f"hour {hour:02d} already compiled, skipping")
        return out_path

    try:
        with frames_lock(blocking=True, timeout=30):
            frames = _hour_frames(date_str, hour)
    except FramesBusy as e:
        log(f"hour {hour:02d} deferred — {e}")
        return None
    if not frames:
        log(f"hour {hour:02d} has no frames yet, skipping")
        return None

    duration_each = SECONDS_PER_HOUR_CHUNK / len(frames)
    concat_list = VIDEO_CHUNKS / f".hour_{hour:02d}.concat.txt"
    with concat_list.open("w") as f:
        for p in frames:
            f.write(f"file '{p.as_posix()}'\n")
            f.write(f"duration {duration_each:.6f}\n")
        f.write(f"file '{frames[-1].as_posix()}'\n")

    tmp_out = out_path.with_suffix(".tmp.mp4")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-vf", f"fps={MASTER_FPS},format=yuv420p",
        "-r", str(MASTER_FPS),
        str(tmp_out),
    ]
    code, err = _run_ffmpeg(cmd, timeout=600)
    concat_list.unlink(missing_ok=True)
    if code != 0 or not tmp_out.is_file():
        log(f"hour {hour:02d} FAILED: {err or 'ffmpeg failed'}")
        tmp_out.unlink(missing_ok=True)
        return None
    tmp_out.replace(out_path)
    log(f"hour {hour:02d} \u2192 {out_path.name}  ({len(frames)} frames, {duration_each * len(frames):.2f}s)")

    try:
        with frames_lock(blocking=True, timeout=30):
            _retire_frames(date_str, hour, frames)
    except FramesBusy as e:
        log(f"hour {hour:02d} compiled but frames NOT retired yet — {e} (will retry next catchup)")
    return out_path


def _retire_frames(date_str: str, hour: int, frames: list[Path]) -> None:
    """Move (or delete) hour frames out of frames/ after a successful compile."""
    if ARCHIVE_NOT_DELETE:
        dest_dir = ARCHIVE / date_str / f"hour_{hour:02d}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for p in frames:
            try:
                p.replace(dest_dir / p.name)
            except OSError as e:
                log(f"hour {hour:02d} archive move failed for {p.name}: {e}")
        log(f"hour {hour:02d} frames archived \u2192 {dest_dir}")
    else:
        for p in frames:
            try:
                p.unlink()
            except OSError as e:
                log(f"hour {hour:02d} delete failed for {p.name}: {e}")
        log(f"hour {hour:02d} frames wiped ({len(frames)} files)")


def daily_render(date_str: str, *, force: bool = False) -> Path | None:
    """Stitch all hour_HH.mp4 chunks into master_stitched_timelapse.mp4 (MP4 only)."""
    FINAL_OUTPUT.mkdir(parents=True, exist_ok=True)
    master = FINAL_OUTPUT / "master_stitched_timelapse.mp4"

    chunks = sorted(VIDEO_CHUNKS.glob("hour_*.mp4"))
    if not chunks:
        log("daily render: no hourly chunks found, nothing to stitch")
        return None
    if master.is_file() and not force:
        log("daily render already done, skipping")
        return master

    concat_list = VIDEO_CHUNKS / ".daily.concat.txt"
    with concat_list.open("w") as f:
        for c in chunks:
            f.write(f"file '{c.as_posix()}'\n")

    tmp_master = master.with_suffix(".tmp.mp4")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(tmp_master),
    ]
    code, err = _run_ffmpeg(cmd, timeout=600)
    concat_list.unlink(missing_ok=True)
    if code != 0 or not tmp_master.is_file():
        log(f"daily render FAILED (master): {err or 'ffmpeg failed'}")
        tmp_master.unlink(missing_ok=True)
        return None
    tmp_master.replace(master)
    log(f"master \u2192 {master.name}  ({len(chunks)} hourly chunks, MP4 only)")
    return master


def catchup() -> None:
    """Boot-time recovery: compile any missing completed hours today; daily stitch if past 19:00."""
    now = _now_local()
    date_str = now.strftime("%Y%m%d")
    log(f"catchup: checking {date_str}, now={now.strftime('%H:%M')} HST")

    last_completed_hour = min(now.hour, WINDOW_END_HOUR) - 1
    for hour in range(WINDOW_START_HOUR, last_completed_hour + 1):
        if hour >= WINDOW_END_HOUR:
            break
        compile_hour(date_str, hour)

    if now.hour >= WINDOW_END_HOUR:
        daily_render(date_str)
    else:
        log("catchup: window still open today, skipping daily render")


def cli() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_hourly = sub.add_parser("hourly", help="compile one completed hour")
    p_hourly.add_argument("--hour", type=int, default=None, help="0-23, default = hour that just ended")
    p_hourly.add_argument("--date", type=str, default=None, help="YYYYMMDD, default = today")
    p_hourly.add_argument("--force", action="store_true")

    p_daily = sub.add_parser("daily", help="stitch the day's hourly MP4s into master (no GIF)")
    p_daily.add_argument("--date", type=str, default=None, help="YYYYMMDD, default = today")
    p_daily.add_argument("--force", action="store_true")

    sub.add_parser("catchup", help="boot-time: do whatever was missed")

    args = ap.parse_args()
    now = _now_local()

    if args.cmd == "hourly":
        date_str = args.date or now.strftime("%Y%m%d")
        hour = args.hour if args.hour is not None else (now - timedelta(hours=1)).hour
        if hour < WINDOW_START_HOUR or hour >= WINDOW_END_HOUR:
            log(
                f"hour {hour:02d} is outside the "
                f"{WINDOW_START_HOUR:02d}:00-{WINDOW_END_HOUR:02d}:00 window, skipping"
            )
            return
        compile_hour(date_str, hour, force=args.force)
    elif args.cmd == "daily":
        date_str = args.date or now.strftime("%Y%m%d")
        daily_render(date_str, force=args.force)
    elif args.cmd == "catchup":
        catchup()


if __name__ == "__main__":
    cli()
