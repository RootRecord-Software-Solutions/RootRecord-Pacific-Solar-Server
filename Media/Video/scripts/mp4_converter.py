# ==============================================================================
# FILE: Media/Video/scripts/mp4_converter.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Still image + audio -> MP4 (G3 port of G1 mp4-converter/scripts/mp4_converter.py). ON DEMAND, no job.

  python3 mp4_converter.py --audio FILE.{mp3,wav} [--thumb IMAGE] [--out FILE.mp4] [--current FILE.mp4]

Same ffmpeg recipe as G1 (loop still, libx264 -tune stillimage, yuv420p, AAC 192k, -shortest, +faststart), run at
nice 10 with a 180 s timeout. G3 changes (documented): stdlib only, no Ava-Core `config`; default output
Database Media/Video/<stem>.mp4 (git-ignored *.mp4); default still = RR_BROADCAST_THUMB env or --thumb (G1 used
config.DAILY_BROADCAST_THUMB / THUMBNAIL_PATH — no G3 equivalent yet); WAV accepted (G3 voice writes WAV, G1 MP3);
--current copies the MP4 only (G1 also copied the MP3 into AUDIO_CURRENT_DIR). No upload / broadcast.
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import os  # info: import os
import shutil  # info: import shutil
import subprocess  # info: import subprocess
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
MP4_DIR = DB / "Media" / "Video"  # info: set MP4_DIR


# ====================================================
# SECTION: function daily_thumbnail
# What it does: daily thumbnail.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def daily_thumbnail(explicit: Path | None = None) -> Path | None:  # info: def daily_thumbnail
    for cand in (explicit, Path(os.environ["RR_BROADCAST_THUMB"]) if os.environ.get("RR_BROADCAST_THUMB") else None):  # info: for cand in ( explicit , Path (
        if cand and cand.is_file():  # info: if cand and cand . is_file ( )
            return cand  # info: return cand
    return None  # info: return None


# ====================================================
# SECTION: function convert
# What it does: convert.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def convert(audio: Path, *, thumbnail: Path | None = None, out_path: Path | None = None,  # info: def convert
            current_path: Path | None = None) -> tuple[Path | None, str]:  # info: set current_path
    if not audio.is_file() or audio.suffix.lower() not in {".mp3", ".wav"}:  # info: if not audio . is_file ( ) or
        return None, "audio missing or not .mp3/.wav"  # info: return None , "audio missing or not .mp3/.wav"
    dest = out_path or (MP4_DIR / audio.with_suffix(".mp4").name)  # info: set dest
    thumb = daily_thumbnail(thumbnail)  # info: set thumb
    if not thumb:  # info: if not thumb :
        return None, "no thumbnail (--thumb or RR_BROADCAST_THUMB)"  # info: return None , "no thumbnail (--thumb or RR_BROADCAST_THUMB)"
    ffmpeg = shutil.which("ffmpeg")  # info: set ffmpeg
    if not ffmpeg:  # info: if not ffmpeg :
        return None, "ffmpeg not found"  # info: return None , "ffmpeg not found"
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir ( parents =
    cmd = ["nice", "-n", "10", ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-i", str(thumb),  # info: set cmd
           "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac",  # info: "-i" , str ( audio ) , "-c:v"
           "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(dest)]  # info: "-b:a" , "192k" , "-shortest" , "-movflags" ,
    try:  # info: try :
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)  # info: subprocess . run ( cmd , check =
    except (OSError, subprocess.SubprocessError) as e:  # info: except ( OSError , subprocess . SubprocessError )
        return None, f"ffmpeg failed: {type(e).__name__}"  # info: return None , f" ffmpeg failed: { type (
    if not dest.is_file():  # info: if not dest . is_file ( ) :
        return None, "no output"  # info: return None , "no output"
    if current_path:  # info: if current_path :
        current_path.parent.mkdir(parents=True, exist_ok=True)  # info: current_path . parent . mkdir ( parents =
        shutil.copy2(dest, current_path)  # info: shutil . copy2 ( dest , current_path )
    return dest, "ok"  # info: return dest , "ok"


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    p = argparse.ArgumentParser(description="Still-image + audio -> MP4")  # info: set p
    p.add_argument("--audio", "--mp3", dest="audio", required=True)  # info: p . add_argument ( "--audio" , "--mp3" ,
    p.add_argument("--out", default="")  # info: p . add_argument ( "--out" , default =
    p.add_argument("--thumb", default="")  # info: p . add_argument ( "--thumb" , default =
    p.add_argument("--current", default="")  # info: p . add_argument ( "--current" , default =
    a = p.parse_args(argv)  # info: set a
    dest, why = convert(Path(a.audio), thumbnail=Path(a.thumb) if a.thumb else None,  # info: dest , why = convert ( Path (
                        out_path=Path(a.out) if a.out else None, current_path=Path(a.current) if a.current else None)  # info: set out_path
    print(json.dumps({"ok": bool(dest), "mp4": str(dest) if dest else None, "detail": why}))  # info: call print
    return 0 if dest else 1  # info: return 0 if dest else 1


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
