#!/usr/bin/env python3
"""Route one spoken line to Kokoro or a gated cloud voice. No speaker.

  python3 -m CloudTTS --engine kokoro
  python3 -m CloudTTS --engine ara
  python3 -m CloudTTS --engine ara --speak   # needs RR_CLOUD_TTS=1

Default engine is kokoro. That writes a route record and does not render.
--engine ara stays gated unless both RR_CLOUD_TTS=1 and --speak are set.
The live path posts to xAI TTS (voice id ara) and does not open a speaker.
Cursor is a text queue in the old synth script. This router does not call it.

State: Database Media/CloudTTS/last-route.json
Logs:  Database Logs/Media/CloudTTS/route.log
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parents[2]
PLAYBACK = PACIFIC / "Media" / "Playback"
DB = Path(os.environ.get(
    "RR_DATABASE_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
))
STATE = DB / "Media" / "CloudTTS"
LOG_DIR = DB / "Logs" / "Media" / "CloudTTS"
LAST = STATE / "last-route.json"
LOCK = STATE / "route.lock"
AUDIO = STATE / "ara-last.mp3"
TTS_URL = "https://api.x.ai/v1/tts"
VOICE_ID = "ara"
MAX_CHARS = 2000

try:
    from .envload import load_env
except ImportError:
    from envload import load_env


def now_hst() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def emit(payload: dict, code: int, *, state: bool = True) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    body = dict(payload)
    body["at"] = now_hst().isoformat()
    body["speaker"] = False
    if state:
        LAST.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    line = json.dumps(body, ensure_ascii=False)
    with (LOG_DIR / "route.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)
    return code


def gated(engine: str) -> dict:
    return {
        "ok": True,
        "engine": engine,
        "called": False,
        "detail": "gated",
        "speaker": False,
    }


def speak_ara(text: str) -> dict:
    """Post to xAI only when the caller has already passed both gates."""
    if os.environ.get("RR_CLOUD_TTS", "0") != "1":
        return gated("ara")
    spoken = " ".join((text or "").split()).strip()
    base = {"engine": "ara", "speaker": False, "called": False}
    if not spoken:
        base["ok"] = False
        base["detail"] = "empty_text"
        return base
    if len(spoken) > MAX_CHARS:
        base["ok"] = False
        base["detail"] = "over_cap"
        return base
    load_env()
    key = (os.environ.get("XAI_API_KEY") or "").strip()
    if not key:
        base["ok"] = False
        base["detail"] = "key_missing"
        return base
    payload = {
        "text": spoken,
        "voice_id": VOICE_ID,
        "language": "en",
        "output_format": {"codec": "mp3", "sample_rate": 44100, "bit_rate": 128000},
        "text_normalization": True,
    }
    req = urllib.request.Request(
        TTS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read()
            status = getattr(resp, "status", 200)
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "engine": "ara",
            "called": True,
            "detail": "http_error",
            "status": exc.code,
            "speaker": False,
        }
    except (urllib.error.URLError, TimeoutError, OSError):
        return {
            "ok": False,
            "engine": "ara",
            "called": True,
            "detail": "http_error",
            "speaker": False,
        }
    if status != 200 or len(body) < 1000:
        return {
            "ok": False,
            "engine": "ara",
            "called": True,
            "detail": "tiny_audio",
            "speaker": False,
        }
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = AUDIO.with_suffix(".mp3.tmp")
    tmp.write_bytes(body)
    os.replace(tmp, AUDIO)
    return {
        "ok": True,
        "engine": "ara",
        "called": True,
        "detail": "ara",
        "path": str(AUDIO),
        "bytes": len(body),
        "speaker": False,
    }


def route(engine: str | None, *, speak: bool = False, text: str = "") -> dict:
    """Choose an engine. Cloud audio stays closed unless both gates are on."""
    name = (engine or "kokoro").strip().lower()
    if name == "kokoro":
        return {
            "ok": True,
            "engine": "kokoro",
            "called": False,
            "detail": "kokoro_local",
            "speaker": False,
        }
    if name == "cursor":
        return {
            "ok": True,
            "engine": "cursor",
            "called": False,
            "detail": "cursor_is_text_queue",
            "speaker": False,
        }
    if name != "ara":
        return {
            "ok": False,
            "engine": name,
            "called": False,
            "detail": "refused",
            "speaker": False,
        }
    if not speak or os.environ.get("RR_CLOUD_TTS", "0") != "1":
        return gated("ara")
    return speak_ara(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route one line to Kokoro or gated Ara.")
    parser.add_argument("--engine", default="kokoro", help="kokoro (default), ara, or cursor")
    parser.add_argument("--speak", action="store_true", help="Cloud call. Needs RR_CLOUD_TTS=1.")
    parser.add_argument("--text", default="", help="Spoken text. Used only on the live Ara path.")
    args = parser.parse_args(argv)

    if not PLAYBACK.is_dir():
        return emit({
            "ok": False,
            "engine": args.engine,
            "called": False,
            "detail": "dependency_missing",
            "dependency": "Report playback",
            "speaker": False,
        }, 1)

    STATE.mkdir(parents=True, exist_ok=True)
    lock_fh = LOCK.open("a", encoding="utf-8")
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_fh.close()
        return emit({
            "ok": True,
            "engine": (args.engine or "kokoro").strip().lower(),
            "called": False,
            "detail": "busy",
            "speaker": False,
        }, 3, state=False)

    try:
        body = route(args.engine, speak=args.speak, text=args.text)
        if body.get("detail") == "gated" and args.speak:
            return emit(body, 2)
        if body.get("detail") in {"refused", "empty_text", "over_cap", "key_missing", "http_error", "tiny_audio"}:
            return emit(body, 1 if body.get("detail") != "key_missing" else 2)
        return emit(body, 0)
    finally:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        lock_fh.close()


if __name__ == "__main__":
    sys.exit(main())
