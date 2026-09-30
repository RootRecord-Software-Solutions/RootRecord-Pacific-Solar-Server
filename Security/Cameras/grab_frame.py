# ==============================================================================
# FILE: Security/Cameras/grab_frame.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Grab one JPEG still from a camera channel and save it to the Database.

This script does exactly one thing: pull a single frame via RTSP/ffmpeg
and write it to /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Images/. Nothing else
reads it, mirrors it, or serves it — that's the gateway's job.
"""
from __future__ import annotations  # info: from __future__ import annotations
import fcntl  # info: import fcntl
import json  # info: import json
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
from contextlib import contextmanager  # info: from contextlib import contextmanager
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

SKILL = Path(__file__).resolve().parent  # info: set SKILL
CONN_PATH = SKILL / "store" / "CONNECTION.json"  # info: set CONN_PATH
MASTER_KEY = Path("/home/rootrecord/master/master-key.env")  # info: set MASTER_KEY
DB_FRAMES = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Images")  # info: set DB_FRAMES

FRAMES_LOCK_PATH = Path("/tmp/security-camera-frames.lock")  # info: set FRAMES_LOCK_PATH

# Extra pixels cut off the RIGHT edge on top of crop_right_pct (Night Owl watermark).
# ~20px more than the percentage crop alone.
DEFAULT_CROP_RIGHT_PX = 20  # info: set DEFAULT_CROP_RIGHT_PX


# ====================================================
# SECTION: class FramesBusy
# What it does: Raised when the frames lock couldn't be acquired.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class FramesBusy(RuntimeError):  # info: class FramesBusy
    """Raised when the frames lock couldn't be acquired."""  # info: """Raised when the frames lock couldn't be acquired."""


# ====================================================
# SECTION: function frames_lock
# What it does: frames lock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@contextmanager  # info: decorator contextmanager
def frames_lock(blocking: bool = True, timeout: float = 10.0):  # info: def frames_lock
    FRAMES_LOCK_PATH.touch(exist_ok=True)  # info: FRAMES_LOCK_PATH . touch ( exist_ok = True )
    fh = open(FRAMES_LOCK_PATH, "r+")  # info: set fh
    try:  # info: try :
        if blocking:  # info: if blocking :
            deadline = time.monotonic() + timeout  # info: set deadline
            while True:  # info: while True :
                try:  # info: try :
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # info: fcntl . flock ( fh . fileno (
                    break  # info: break
                except BlockingIOError:  # info: except BlockingIOError :
                    if time.monotonic() >= deadline:  # info: if time . monotonic ( ) >= deadline
                        raise FramesBusy(f"frames lock still busy after {timeout:.0f}s")  # info: raise FramesBusy ( f" frames lock still busy after { timeout :
                    time.sleep(0.1)  # info: time . sleep ( 0.1 )
        else:  # info: else :
            try:  # info: try :
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # info: fcntl . flock ( fh . fileno (
            except BlockingIOError:  # info: except BlockingIOError :
                raise FramesBusy("frames lock busy — skipping this grab")  # info: raise FramesBusy ( "frames lock busy — skipping this grab" )
        yield  # info: yield
    finally:  # info: finally :
        try:  # info: try :
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)  # info: fcntl . flock ( fh . fileno (
        except OSError:  # info: except OSError :
            pass  # info: pass
        fh.close()  # info: fh . close ( )


# ====================================================
# SECTION: function load_master_key
# What it does: load master key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_master_key(name: str) -> str:  # info: def load_master_key
    if not MASTER_KEY.is_file():  # info: if not MASTER_KEY . is_file ( ) :
        raise FileNotFoundError(f"missing {MASTER_KEY}")  # info: raise FileNotFoundError ( f" missing { MASTER_KEY }
    for line in MASTER_KEY.read_text(encoding="utf-8").splitlines():  # info: for line in MASTER_KEY . read_text ( encoding
        line = line.strip()  # info: set line
        if not line or line.startswith("#") or "=" not in line:
            continue  # info: continue
        k, _, v = line.partition("=")  # info: k , _ , v = line .
        if k.strip() == name:  # info: if k . strip ( ) == name
            return v.strip().strip('"').strip("'")  # info: return v . strip ( ) . strip
    raise KeyError(f"{name} not found in {MASTER_KEY}")  # info: raise KeyError ( f" { name } not found in


# ====================================================
# SECTION: function load_conn
# What it does: load conn.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_conn() -> dict:  # info: def load_conn
    if not CONN_PATH.is_file():  # info: if not CONN_PATH . is_file ( ) :
        raise FileNotFoundError(f"missing {CONN_PATH}")  # info: raise FileNotFoundError ( f" missing { CONN_PATH }
    return json.loads(CONN_PATH.read_text(encoding="utf-8"))  # info: return json . loads ( CONN_PATH . read_text


# ====================================================
# SECTION: function crop_right_pct
# What it does: Fraction of frame width to cut off the RIGHT edge. Env wins over CONNECTION.json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def crop_right_pct() -> float:  # info: def crop_right_pct
    """Fraction of frame width to cut off the RIGHT edge. Env wins over CONNECTION.json."""  # info: """Fraction of frame width to cut off the RIGHT edge. Env wins over CONNECTION.json."""
    import os  # info: import os
    env = os.environ.get("AEYES_CROP_RIGHT_PCT")  # info: set env
    if env is not None:  # info: if env is not None :
        try:  # info: try :
            return max(0.0, min(0.5, float(env)))  # info: return max ( 0.0 , min ( 0.5
        except ValueError:  # info: except ValueError :
            pass  # info: pass
    try:  # info: try :
        pct = (load_conn().get("capture") or {}).get("crop_right_pct")  # info: set pct
        return max(0.0, min(0.5, float(pct))) if pct is not None else 0.0  # info: return max ( 0.0 , min ( 0.5
    except (FileNotFoundError, TypeError, ValueError):  # info: except ( FileNotFoundError , TypeError , ValueError )
        return 0.0  # info: return 0.0


# ====================================================
# SECTION: function crop_right_px
# What it does: Extra pixels off the RIGHT edge (on top of crop_right_pct). Default 20.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def crop_right_px() -> int:  # info: def crop_right_px
    """Extra pixels off the RIGHT edge (on top of crop_right_pct). Default 20."""  # info: """Extra pixels off the RIGHT edge (on top of crop_right_pct). Default 20."""
    import os  # info: import os
    env = os.environ.get("AEYES_CROP_RIGHT_PX")  # info: set env
    if env is not None:  # info: if env is not None :
        try:  # info: try :
            return max(0, min(200, int(env)))  # info: return max ( 0 , min ( 200
        except ValueError:  # info: except ValueError :
            pass  # info: pass
    try:  # info: try :
        px = (load_conn().get("capture") or {}).get("crop_right_px")  # info: set px
        if px is not None:  # info: if px is not None :
            return max(0, min(200, int(px)))  # info: return max ( 0 , min ( 200
    except (FileNotFoundError, TypeError, ValueError):  # info: except ( FileNotFoundError , TypeError , ValueError )
        pass  # info: pass
    return DEFAULT_CROP_RIGHT_PX  # info: return DEFAULT_CROP_RIGHT_PX


# ====================================================
# SECTION: function rtsp_url
# What it does: rtsp url.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def rtsp_url(channel: int = 1, stream: int = 0) -> str:  # info: def rtsp_url
    conn = load_conn()  # info: set conn
    lan = conn.get("lan") or {}  # info: set lan
    urls = lan.get("rtsp_urls") or {}  # info: set urls
    key = "channel_main" if int(stream) == 0 else "channel_sub"  # info: set key
    tmpl = urls.get(key) or urls.get("channel_main")  # info: set tmpl
    user = lan.get("rtsp_user") or "admin"  # info: set user
    pw = load_master_key("AEYES_RTSP_PASSWORD")  # info: set pw
    if not tmpl:  # info: if not tmpl :
        ip = lan.get("ip") or "192.168.1.33"  # info: set ip
        return f"rtsp://{user}:{pw}@{ip}:554/user={user}&password={pw}&channel={channel}&stream={stream}"  # info: return f" rtsp:// { user } : {
    return tmpl.replace("{USER}", user).replace("{PASS}", pw).replace("{N}", str(channel))  # info: return tmpl . replace ( "{USER}" , user


# ====================================================
# SECTION: function grab_jpeg
# What it does: grab jpeg.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def grab_jpeg(channel: int = 1, stream: int = 0) -> Path:  # info: def grab_jpeg
    with frames_lock(blocking=False):  # info: with frames_lock ( blocking = False ) :
        DB_FRAMES.mkdir(parents=True, exist_ok=True)  # info: DB_FRAMES . mkdir ( parents = True ,
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # info: set ts
        path = DB_FRAMES / f"ch{channel}-{ts}.jpg"  # info: set path
        url = rtsp_url(channel, stream)  # info: set url
        cmd = [  # info: set cmd
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",  # info: "ffmpeg" , "-y" , "-hide_banner" , "-loglevel" ,
            "-rtsp_transport", "tcp",  # info: "-rtsp_transport" , "tcp" ,
            "-i", url,  # info: "-i" , url ,
            "-frames:v", "1",  # info: "-frames:v" , "1" ,
        ]  # info: ]
        pct = crop_right_pct()  # info: set pct
        px = crop_right_px()  # info: set px
        if pct > 0 or px > 0:  # info: if pct > 0 or px > 0
            # Keep left side (timestamp OSD). Cut right by pct fraction + extra px.
            # width = trunc((iw*(1-pct) - px)/2)*2  (even), x=0, full height.
            cmd += [  # info: set cmd
                "-vf",  # info: "-vf" ,
                f"crop=trunc((iw*(1-{pct})-{px})/2)*2:ih:0:0",  # info: f" crop=trunc((iw*(1- { pct } )- { px
            ]  # info: ]
        cmd += ["-q:v", "2", str(path)]  # info: set cmd
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # info: set r
        if r.returncode != 0 or not path.is_file() or path.stat().st_size < 100:  # info: if r . returncode != 0 or not
            err = (r.stderr or r.stdout or "ffmpeg failed").strip()[:300]  # info: set err
            raise RuntimeError(err or "empty jpeg")  # info: raise RuntimeError ( err or "empty jpeg" )
        return path  # info: return path


# ====================================================
# SECTION: block if
# What it does: __name__ == '__main__'
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
if __name__ == "__main__":  # info: if __name__ == "__main__" :
    from datetime import datetime  # info: from datetime import datetime
    ch = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # info: set ch
    t0 = datetime.now()  # info: set t0
    try:  # info: try :
        path = grab_jpeg(channel=ch)  # info: set path
        kb = path.stat().st_size / 1024  # info: set kb
        ts = t0.strftime("%H:%M:%S")  # info: set ts
        dt = (datetime.now() - t0).total_seconds()  # info: set dt
        print(f"  {ts}  \U0001F4F7  a-eyes  ch{ch} \u2192 {path.name}  ({kb:.1f} KB, {dt:.2f}s)")  # info: call print
    except FramesBusy as e:  # info: except FramesBusy as e :
        ts = t0.strftime("%H:%M:%S")  # info: set ts
        print(f"  {ts}  \u23ed  a-eyes  ch{ch} SKIPPED: {e}")  # info: call print
        sys.exit(0)  # info: sys . exit ( 0 )
    except Exception as e:  # info: except Exception as e :
        ts = t0.strftime("%H:%M:%S")  # info: set ts
        print(f"  {ts}  \u2717  a-eyes  ch{ch} FAILED: {str(e)[:150]}")  # info: call print
        sys.exit(1)  # info: sys . exit ( 1 )
