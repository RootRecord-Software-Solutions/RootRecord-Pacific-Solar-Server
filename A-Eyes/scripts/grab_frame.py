#!/usr/bin/env python3
"""Grab one JPEG still from a camera channel and save it to the Database.

This script does exactly one thing: pull a single frame via RTSP/ffmpeg
and write it to /home/rootrecord/Database/A-EYES/frames/. Nothing else
reads it, mirrors it, or serves it — that's the gateway's job.
"""
from __future__ import annotations
import fcntl
import json
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CONN_PATH = SKILL / "store" / "CONNECTION.json"
MASTER_KEY = Path("/home/rootrecord/master/master-key.env")
DB_FRAMES = Path("/home/rootrecord/Database/A-EYES/frames")

FRAMES_LOCK_PATH = Path("/tmp/a-eyes-frames.lock")

# Extra pixels cut off the RIGHT edge on top of crop_right_pct (Night Owl watermark).
# ~20px more than the percentage crop alone.
DEFAULT_CROP_RIGHT_PX = 20


class FramesBusy(RuntimeError):
    """Raised when the frames lock couldn't be acquired."""


@contextmanager
def frames_lock(blocking: bool = True, timeout: float = 10.0):
    FRAMES_LOCK_PATH.touch(exist_ok=True)
    fh = open(FRAMES_LOCK_PATH, "r+")
    try:
        if blocking:
            deadline = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise FramesBusy(f"frames lock still busy after {timeout:.0f}s")
                    time.sleep(0.1)
        else:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise FramesBusy("frames lock busy — skipping this grab")
        yield
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        fh.close()


def load_master_key(name: str) -> str:
    if not MASTER_KEY.is_file():
        raise FileNotFoundError(f"missing {MASTER_KEY}")
    for line in MASTER_KEY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'")
    raise KeyError(f"{name} not found in {MASTER_KEY}")


def load_conn() -> dict:
    if not CONN_PATH.is_file():
        raise FileNotFoundError(f"missing {CONN_PATH}")
    return json.loads(CONN_PATH.read_text(encoding="utf-8"))


def crop_right_pct() -> float:
    """Fraction of frame width to cut off the RIGHT edge. Env wins over CONNECTION.json."""
    import os
    env = os.environ.get("AEYES_CROP_RIGHT_PCT")
    if env is not None:
        try:
            return max(0.0, min(0.5, float(env)))
        except ValueError:
            pass
    try:
        pct = (load_conn().get("capture") or {}).get("crop_right_pct")
        return max(0.0, min(0.5, float(pct))) if pct is not None else 0.0
    except (FileNotFoundError, TypeError, ValueError):
        return 0.0


def crop_right_px() -> int:
    """Extra pixels off the RIGHT edge (on top of crop_right_pct). Default 20."""
    import os
    env = os.environ.get("AEYES_CROP_RIGHT_PX")
    if env is not None:
        try:
            return max(0, min(200, int(env)))
        except ValueError:
            pass
    try:
        px = (load_conn().get("capture") or {}).get("crop_right_px")
        if px is not None:
            return max(0, min(200, int(px)))
    except (FileNotFoundError, TypeError, ValueError):
        pass
    return DEFAULT_CROP_RIGHT_PX


def rtsp_url(channel: int = 1, stream: int = 0) -> str:
    conn = load_conn()
    lan = conn.get("lan") or {}
    urls = lan.get("rtsp_urls") or {}
    key = "channel_main" if int(stream) == 0 else "channel_sub"
    tmpl = urls.get(key) or urls.get("channel_main")
    user = lan.get("rtsp_user") or "admin"
    pw = load_master_key("AEYES_RTSP_PASSWORD")
    if not tmpl:
        ip = lan.get("ip") or "192.168.1.33"
        return f"rtsp://{user}:{pw}@{ip}:554/user={user}&password={pw}&channel={channel}&stream={stream}"
    return tmpl.replace("{USER}", user).replace("{PASS}", pw).replace("{N}", str(channel))


def grab_jpeg(channel: int = 1, stream: int = 0) -> Path:
    with frames_lock(blocking=False):
        DB_FRAMES.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = DB_FRAMES / f"ch{channel}-{ts}.jpg"
        url = rtsp_url(channel, stream)
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-rtsp_transport", "tcp",
            "-i", url,
            "-frames:v", "1",
        ]
        pct = crop_right_pct()
        px = crop_right_px()
        if pct > 0 or px > 0:
            # Keep left side (timestamp OSD). Cut right by pct fraction + extra px.
            # width = trunc((iw*(1-pct) - px)/2)*2  (even), x=0, full height.
            cmd += [
                "-vf",
                f"crop=trunc((iw*(1-{pct})-{px})/2)*2:ih:0:0",
            ]
        cmd += ["-q:v", "2", str(path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0 or not path.is_file() or path.stat().st_size < 100:
            err = (r.stderr or r.stdout or "ffmpeg failed").strip()[:300]
            raise RuntimeError(err or "empty jpeg")
        return path


if __name__ == "__main__":
    from datetime import datetime
    ch = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    t0 = datetime.now()
    try:
        path = grab_jpeg(channel=ch)
        kb = path.stat().st_size / 1024
        ts = t0.strftime("%H:%M:%S")
        dt = (datetime.now() - t0).total_seconds()
        print(f"  {ts}  \U0001F4F7  a-eyes  ch{ch} \u2192 {path.name}  ({kb:.1f} KB, {dt:.2f}s)")
    except FramesBusy as e:
        ts = t0.strftime("%H:%M:%S")
        print(f"  {ts}  \u23ed  a-eyes  ch{ch} SKIPPED: {e}")
        sys.exit(0)
    except Exception as e:
        ts = t0.strftime("%H:%M:%S")
        print(f"  {ts}  \u2717  a-eyes  ch{ch} FAILED: {str(e)[:150]}")
        sys.exit(1)
