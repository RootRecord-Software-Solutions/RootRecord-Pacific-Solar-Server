# ==============================================================================
# FILE: Security/Cameras/timelapse_engine.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import subprocess  # info: import subprocess
import sys  # info: import sys
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent  # info: set SCRIPTS
sys.path.insert(0, str(SCRIPTS))  # info: sys . path . insert ( 0 ,
from grab_frame import DB_FRAMES, frames_lock, FramesBusy  # noqa: E402

# ---------------------------------------------------------------------------
# Derived directories — all hang off DB_FRAMES, never re-typed by hand.
# ---------------------------------------------------------------------------
BASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Timelapses")  # info: set BASE
FRAMES = DB_FRAMES                             # .../frames
VIDEO_CHUNKS = BASE / "video_chunks"  # info: set VIDEO_CHUNKS
FINAL_OUTPUT = BASE / "final_output"  # info: set FINAL_OUTPUT
ARCHIVE = BASE / "_archive"  # info: set ARCHIVE

# ---------------------------------------------------------------------------
# Config (env-overridable)
# ---------------------------------------------------------------------------
import os  # info: import os
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

CHANNEL = int(os.environ.get("A_EYES_TIMELAPSE_CHANNEL", "1"))  # info: set CHANNEL
LOCAL_TZ = ZoneInfo(os.environ.get("A_EYES_TIMELAPSE_TZ", "Pacific/Honolulu"))  # info: set LOCAL_TZ
WINDOW_START_HOUR = int(os.environ.get("A_EYES_TIMELAPSE_START_HOUR", "5"))   # 5:00 AM
WINDOW_END_HOUR = int(os.environ.get("A_EYES_TIMELAPSE_END_HOUR", "19"))     # 7:00 PM exclusive → last hour is 18
TARGET_TOTAL_SECONDS = float(os.environ.get("A_EYES_TIMELAPSE_TOTAL_SEC", "180"))  # 3 min master
MASTER_FPS = int(os.environ.get("A_EYES_TIMELAPSE_FPS", "68"))  # info: set MASTER_FPS
ARCHIVE_NOT_DELETE = os.environ.get("A_EYES_TIMELAPSE_ARCHIVE", "1") != "0"  # info: set ARCHIVE_NOT_DELETE

WINDOW_HOURS = WINDOW_END_HOUR - WINDOW_START_HOUR                # 14 (05–18 inclusive)
SECONDS_PER_HOUR_CHUNK = TARGET_TOTAL_SECONDS / WINDOW_HOURS       # ~12.86s per hour


# ====================================================
# SECTION: function log
# What it does: log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log(msg: str) -> None:  # info: def log
    ts = datetime.now(LOCAL_TZ).strftime("%H:%M:%S")  # info: set ts
    print(f"  {ts}  \U0001F3AC  a-eyes-timelapse  {msg}", flush=True)  # info: call print


# ====================================================
# SECTION: function _now_local
# What it does:  now local.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now_local() -> datetime:  # info: def _now_local
    return datetime.now(LOCAL_TZ)  # info: return datetime . now ( LOCAL_TZ )


# ====================================================
# SECTION: function _frame_local_dt
# What it does: grab_frame.py stamps filenames as ch<N>-YYYYMMDDTHHMMSSZ.jpg in UTC.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _frame_local_dt(p: Path) -> datetime | None:  # info: def _frame_local_dt
    """grab_frame.py stamps filenames as ch<N>-YYYYMMDDTHHMMSSZ.jpg in UTC."""  # info: """grab_frame.py stamps filenames as ch<N>-YYYYMMDDTHHMMSSZ.jpg in UTC."""
    try:  # info: try :
        ts_part = p.stem.split("-", 1)[1]  # info: set ts_part
        dt_utc = datetime.strptime(ts_part, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC"))  # info: set dt_utc
        return dt_utc.astimezone(LOCAL_TZ)  # info: return dt_utc . astimezone ( LOCAL_TZ )
    except (IndexError, ValueError):  # info: except ( IndexError , ValueError ) :
        return None  # info: return None


# ====================================================
# SECTION: function _hour_frames
# What it does: Every frame for local date_str / hour on CHANNEL, oldest first.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _hour_frames(date_str: str, hour: int) -> list[Path]:  # info: def _hour_frames
    """Every frame for local date_str / hour on CHANNEL, oldest first."""  # info: """Every frame for local date_str / hour on CHANNEL, oldest first."""
    out = []  # info: set out
    for p in FRAMES.glob(f"ch{CHANNEL}-*.jpg"):  # info: for p in FRAMES . glob ( f"
        local_dt = _frame_local_dt(p)  # info: set local_dt
        if local_dt and local_dt.strftime("%Y%m%d") == date_str and local_dt.hour == hour:  # info: if local_dt and local_dt . strftime ( "%Y%m%d"
            out.append((local_dt, p))  # info: out . append ( ( local_dt , p
    out.sort(key=lambda t: t[0])  # info: out . sort ( key = lambda t
    return [p for _, p in out]  # info: return [ p for _ , p in


# ====================================================
# SECTION: function _run_ffmpeg
# What it does:  run ffmpeg.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _run_ffmpeg(cmd: list[str], *, timeout: int = 900) -> tuple[int, str]:  # info: def _run_ffmpeg
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)  # info: set r
    err = (r.stderr or r.stdout or "").strip()  # info: set err
    if r.returncode != 0 and not err:  # info: if r . returncode != 0 and not
        err = "ffmpeg failed with no stderr (exit {})".format(r.returncode)  # info: set err
    return r.returncode, err[:500]  # info: return r . returncode , err [ :


# ====================================================
# SECTION: function compile_hour
# What it does: Compile one completed hour's frames into video_chunks/hour_HH.mp4.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def compile_hour(date_str: str, hour: int, *, force: bool = False) -> Path | None:  # info: def compile_hour
    """Compile one completed hour's frames into video_chunks/hour_HH.mp4."""  # info: """Compile one completed hour's frames into video_chunks/hour_HH.mp4."""
    VIDEO_CHUNKS.mkdir(parents=True, exist_ok=True)  # info: VIDEO_CHUNKS . mkdir ( parents = True ,
    out_path = VIDEO_CHUNKS / f"hour_{hour:02d}.mp4"  # info: set out_path
    if out_path.is_file() and not force:  # info: if out_path . is_file ( ) and not
        try:  # info: try :
            with frames_lock(blocking=True, timeout=30):  # info: with frames_lock ( blocking = True , timeout
                leftovers = _hour_frames(date_str, hour)  # info: set leftovers
                if leftovers:  # info: if leftovers :
                    _retire_frames(date_str, hour, leftovers)  # info: call _retire_frames
        except FramesBusy:  # info: except FramesBusy :
            pass  # info: pass
        log(f"hour {hour:02d} already compiled, skipping")  # info: call log
        return out_path  # info: return out_path

    try:  # info: try :
        with frames_lock(blocking=True, timeout=30):  # info: with frames_lock ( blocking = True , timeout
            frames = _hour_frames(date_str, hour)  # info: set frames
    except FramesBusy as e:  # info: except FramesBusy as e :
        log(f"hour {hour:02d} deferred — {e}")  # info: call log
        return None  # info: return None
    if not frames:  # info: if not frames :
        log(f"hour {hour:02d} has no frames yet, skipping")  # info: call log
        return None  # info: return None

    duration_each = SECONDS_PER_HOUR_CHUNK / len(frames)  # info: set duration_each
    concat_list = VIDEO_CHUNKS / f".hour_{hour:02d}.concat.txt"  # info: set concat_list
    with concat_list.open("w") as f:  # info: with concat_list . open ( "w" ) as
        for p in frames:  # info: for p in frames :
            f.write(f"file '{p.as_posix()}'\n")  # info: f . write ( f" file ' { p
            f.write(f"duration {duration_each:.6f}\n")  # info: f . write ( f" duration { duration_each
        f.write(f"file '{frames[-1].as_posix()}'\n")  # info: f . write ( f" file ' { frames

    tmp_out = out_path.with_suffix(".tmp.mp4")  # info: set tmp_out
    cmd = [  # info: set cmd
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",  # info: "ffmpeg" , "-y" , "-hide_banner" , "-loglevel" ,
        "-f", "concat", "-safe", "0", "-i", str(concat_list),  # info: "-f" , "concat" , "-safe" , "0" ,
        "-vf", f"fps={MASTER_FPS},format=yuv420p",  # info: "-vf" , f" fps= { MASTER_FPS } ,format=yuv420p
        "-r", str(MASTER_FPS),  # info: "-r" , str ( MASTER_FPS ) ,
        str(tmp_out),  # info: call str
    ]  # info: ]
    code, err = _run_ffmpeg(cmd, timeout=600)  # info: code , err = _run_ffmpeg ( cmd ,
    concat_list.unlink(missing_ok=True)  # info: concat_list . unlink ( missing_ok = True )
    if code != 0 or not tmp_out.is_file():  # info: if code != 0 or not tmp_out .
        log(f"hour {hour:02d} FAILED: {err or 'ffmpeg failed'}")  # info: call log
        tmp_out.unlink(missing_ok=True)  # info: tmp_out . unlink ( missing_ok = True )
        return None  # info: return None
    tmp_out.replace(out_path)  # info: tmp_out . replace ( out_path )
    log(f"hour {hour:02d} \u2192 {out_path.name}  ({len(frames)} frames, {duration_each * len(frames):.2f}s)")  # info: call log

    try:  # info: try :
        with frames_lock(blocking=True, timeout=30):  # info: with frames_lock ( blocking = True , timeout
            _retire_frames(date_str, hour, frames)  # info: call _retire_frames
    except FramesBusy as e:  # info: except FramesBusy as e :
        log(f"hour {hour:02d} compiled but frames NOT retired yet — {e} (will retry next catchup)")  # info: call log
    return out_path  # info: return out_path


# ====================================================
# SECTION: function _retire_frames
# What it does: Move (or delete) hour frames out of frames/ after a successful compile.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _retire_frames(date_str: str, hour: int, frames: list[Path]) -> None:  # info: def _retire_frames
    """Move (or delete) hour frames out of frames/ after a successful compile."""  # info: """Move (or delete) hour frames out of frames/ after a successful compile."""
    if ARCHIVE_NOT_DELETE:  # info: if ARCHIVE_NOT_DELETE :
        dest_dir = ARCHIVE / date_str / f"hour_{hour:02d}"  # info: set dest_dir
        dest_dir.mkdir(parents=True, exist_ok=True)  # info: dest_dir . mkdir ( parents = True ,
        for p in frames:  # info: for p in frames :
            try:  # info: try :
                p.replace(dest_dir / p.name)  # info: p . replace ( dest_dir / p .
            except OSError as e:  # info: except OSError as e :
                log(f"hour {hour:02d} archive move failed for {p.name}: {e}")  # info: call log
        log(f"hour {hour:02d} frames archived \u2192 {dest_dir}")  # info: call log
    else:  # info: else :
        for p in frames:  # info: for p in frames :
            try:  # info: try :
                p.unlink()  # info: p . unlink ( )
            except OSError as e:  # info: except OSError as e :
                log(f"hour {hour:02d} delete failed for {p.name}: {e}")  # info: call log
        log(f"hour {hour:02d} frames wiped ({len(frames)} files)")  # info: call log


# ====================================================
# SECTION: function daily_render
# What it does: Stitch all hour_HH.mp4 chunks into master_stitched_timelapse.mp4 (MP4 only).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def daily_render(date_str: str, *, force: bool = False) -> Path | None:  # info: def daily_render
    """Stitch all hour_HH.mp4 chunks into master_stitched_timelapse.mp4 (MP4 only)."""  # info: """Stitch all hour_HH.mp4 chunks into master_stitched_timelapse.mp4 (MP4 only)."""
    FINAL_OUTPUT.mkdir(parents=True, exist_ok=True)  # info: FINAL_OUTPUT . mkdir ( parents = True ,
    master = FINAL_OUTPUT / "master_stitched_timelapse.mp4"  # info: set master

    chunks = sorted(VIDEO_CHUNKS.glob("hour_*.mp4"))  # info: set chunks
    if not chunks:  # info: if not chunks :
        log("daily render: no hourly chunks found, nothing to stitch")  # info: call log
        return None  # info: return None
    if master.is_file() and not force:  # info: if master . is_file ( ) and not
        log("daily render already done, skipping")  # info: call log
        return master  # info: return master

    concat_list = VIDEO_CHUNKS / ".daily.concat.txt"  # info: set concat_list
    with concat_list.open("w") as f:  # info: with concat_list . open ( "w" ) as
        for c in chunks:  # info: for c in chunks :
            f.write(f"file '{c.as_posix()}'\n")  # info: f . write ( f" file ' { c

    tmp_master = master.with_suffix(".tmp.mp4")  # info: set tmp_master
    cmd = [  # info: set cmd
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",  # info: "ffmpeg" , "-y" , "-hide_banner" , "-loglevel" ,
        "-f", "concat", "-safe", "0", "-i", str(concat_list),  # info: "-f" , "concat" , "-safe" , "0" ,
        "-c", "copy",  # info: "-c" , "copy" ,
        str(tmp_master),  # info: call str
    ]  # info: ]
    code, err = _run_ffmpeg(cmd, timeout=600)  # info: code , err = _run_ffmpeg ( cmd ,
    concat_list.unlink(missing_ok=True)  # info: concat_list . unlink ( missing_ok = True )
    if code != 0 or not tmp_master.is_file():  # info: if code != 0 or not tmp_master .
        log(f"daily render FAILED (master): {err or 'ffmpeg failed'}")  # info: call log
        tmp_master.unlink(missing_ok=True)  # info: tmp_master . unlink ( missing_ok = True )
        return None  # info: return None
    tmp_master.replace(master)  # info: tmp_master . replace ( master )
    log(f"master \u2192 {master.name}  ({len(chunks)} hourly chunks, MP4 only)")  # info: call log
    return master  # info: return master


# ====================================================
# SECTION: function catchup
# What it does: Boot-time recovery: compile any missing completed hours today; daily stitch if past 19:00.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def catchup() -> None:  # info: def catchup
    """Boot-time recovery: compile any missing completed hours today; daily stitch if past 19:00."""  # info: """Boot-time recovery: compile any missing completed hours today; daily stitch if past 19:00."""
    now = _now_local()  # info: set now
    date_str = now.strftime("%Y%m%d")  # info: set date_str
    log(f"catchup: checking {date_str}, now={now.strftime('%H:%M')} HST")  # info: call log

    last_completed_hour = min(now.hour, WINDOW_END_HOUR) - 1  # info: set last_completed_hour
    for hour in range(WINDOW_START_HOUR, last_completed_hour + 1):  # info: for hour in range ( WINDOW_START_HOUR , last_completed_hour
        if hour >= WINDOW_END_HOUR:  # info: if hour >= WINDOW_END_HOUR :
            break  # info: break
        compile_hour(date_str, hour)  # info: call compile_hour

    if now.hour >= WINDOW_END_HOUR:  # info: if now . hour >= WINDOW_END_HOUR :
        daily_render(date_str)  # info: call daily_render
    else:  # info: else :
        log("catchup: window still open today, skipping daily render")  # info: call log


# ====================================================
# SECTION: function cli
# What it does: cli.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cli() -> None:  # info: def cli
    ap = argparse.ArgumentParser()  # info: set ap
    sub = ap.add_subparsers(dest="cmd", required=True)  # info: set sub

    p_hourly = sub.add_parser("hourly", help="compile one completed hour")  # info: set p_hourly
    p_hourly.add_argument("--hour", type=int, default=None, help="0-23, default = hour that just ended")  # info: p_hourly . add_argument ( "--hour" , type =
    p_hourly.add_argument("--date", type=str, default=None, help="YYYYMMDD, default = today")  # info: p_hourly . add_argument ( "--date" , type =
    p_hourly.add_argument("--force", action="store_true")  # info: p_hourly . add_argument ( "--force" , action =

    p_daily = sub.add_parser("daily", help="stitch the day's hourly MP4s into master (no GIF)")  # info: set p_daily
    p_daily.add_argument("--date", type=str, default=None, help="YYYYMMDD, default = today")  # info: p_daily . add_argument ( "--date" , type =
    p_daily.add_argument("--force", action="store_true")  # info: p_daily . add_argument ( "--force" , action =

    sub.add_parser("catchup", help="boot-time: do whatever was missed")  # info: sub . add_parser ( "catchup" , help =

    args = ap.parse_args()  # info: set args
    now = _now_local()  # info: set now

    if args.cmd == "hourly":  # info: if args . cmd == "hourly" :
        date_str = args.date or now.strftime("%Y%m%d")  # info: set date_str
        hour = args.hour if args.hour is not None else (now - timedelta(hours=1)).hour  # info: set hour
        if hour < WINDOW_START_HOUR or hour >= WINDOW_END_HOUR:  # info: if hour < WINDOW_START_HOUR or hour >= WINDOW_END_HOUR
            log(  # info: call log
                f"hour {hour:02d} is outside the "  # info: f" hour { hour : 02d } is outside the
                f"{WINDOW_START_HOUR:02d}:00-{WINDOW_END_HOUR:02d}:00 window, skipping"  # info: f" { WINDOW_START_HOUR : 02d } :00- {
            )  # info: )
            return  # info: return
        compile_hour(date_str, hour, force=args.force)  # info: call compile_hour
    elif args.cmd == "daily":  # info: elif args . cmd == "daily" :
        date_str = args.date or now.strftime("%Y%m%d")  # info: set date_str
        daily_render(date_str, force=args.force)  # info: call daily_render
    elif args.cmd == "catchup":  # info: elif args . cmd == "catchup" :
        catchup()  # info: call catchup


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    cli()  # info: call cli
