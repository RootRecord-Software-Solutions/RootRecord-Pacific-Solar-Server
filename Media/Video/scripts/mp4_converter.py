#!/usr/bin/env python3
"""Still image + audio -> MP4 (G3 port of G1 mp4-converter/scripts/mp4_converter.py). ON DEMAND, no job.

  python3 mp4_converter.py --audio FILE.{mp3,wav} [--thumb IMAGE] [--out FILE.mp4] [--current FILE.mp4]

Same ffmpeg recipe as G1 (loop still, libx264 -tune stillimage, yuv420p, AAC 192k, -shortest, +faststart), run at
nice 10 with a 180 s timeout. G3 changes (documented): stdlib only, no Ava-Core `config`; default output
Database Media/Video/<stem>.mp4 (git-ignored *.mp4); default still = RR_BROADCAST_THUMB env or --thumb (G1 used
config.DAILY_BROADCAST_THUMB / THUMBNAIL_PATH — no G3 equivalent yet); WAV accepted (G3 voice writes WAV, G1 MP3);
--current copies the MP4 only (G1 also copied the MP3 into AUDIO_CURRENT_DIR). No upload / broadcast.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
MP4_DIR = DB / "Media" / "Video"


def daily_thumbnail(explicit: Path | None = None) -> Path | None:
    for cand in (explicit, Path(os.environ["RR_BROADCAST_THUMB"]) if os.environ.get("RR_BROADCAST_THUMB") else None):
        if cand and cand.is_file():
            return cand
    return None


def convert(audio: Path, *, thumbnail: Path | None = None, out_path: Path | None = None,
            current_path: Path | None = None) -> tuple[Path | None, str]:
    if not audio.is_file() or audio.suffix.lower() not in {".mp3", ".wav"}:
        return None, "audio missing or not .mp3/.wav"
    dest = out_path or (MP4_DIR / audio.with_suffix(".mp4").name)
    thumb = daily_thumbnail(thumbnail)
    if not thumb:
        return None, "no thumbnail (--thumb or RR_BROADCAST_THUMB)"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None, "ffmpeg not found"
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["nice", "-n", "10", ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-i", str(thumb),
           "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac",
           "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(dest)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"ffmpeg failed: {type(e).__name__}"
    if not dest.is_file():
        return None, "no output"
    if current_path:
        current_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, current_path)
    return dest, "ok"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Still-image + audio -> MP4")
    p.add_argument("--audio", "--mp3", dest="audio", required=True)
    p.add_argument("--out", default="")
    p.add_argument("--thumb", default="")
    p.add_argument("--current", default="")
    a = p.parse_args(argv)
    dest, why = convert(Path(a.audio), thumbnail=Path(a.thumb) if a.thumb else None,
                        out_path=Path(a.out) if a.out else None, current_path=Path(a.current) if a.current else None)
    print(json.dumps({"ok": bool(dest), "mp4": str(dest) if dest else None, "detail": why}))
    return 0 if dest else 1


if __name__ == "__main__":
    sys.exit(main())
