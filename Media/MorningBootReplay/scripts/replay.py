#!/usr/bin/env python3
"""Replay today's morning boot_brief WAV until noon HST. No TTS. No speaker.

  python3 replay.py arm
  python3 replay.py run --dry-run
  python3 replay.py disarm --reason operator

Hands the WAV to Media/Playback/scripts/play.py --report boot_brief --dry-run.
This folder never passes --play and never calls aplay. Speaker playback stays
off until Alexander signs off on the player.

State: Database Media/MorningBootReplay/morning-boot-replay.json
Logs:  Database Logs/Media/MorningBootReplay/replay.log
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parents[2]
DB = Path(os.environ.get(
    "RR_DATABASE_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
))
STATE_DIR = DB / "Media" / "MorningBootReplay"
STATE_PATH = STATE_DIR / "morning-boot-replay.json"
LOG_DIR = DB / "Logs" / "Media" / "MorningBootReplay"
VOICE = DB / "Media" / "Audio" / "Voice"
WAV_NAME = "boot_brief_current.wav"
PLAYER = PACIFIC / "Media" / "Playback" / "scripts" / "play.py"
DATED = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def now_hst() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def _load() -> dict:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATE_PATH)


def _log(payload: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with (LOG_DIR / "replay.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)


def _noon(day: datetime) -> datetime:
    return day.replace(hour=12, minute=0, second=0, microsecond=0)


def midday_done(today: str) -> bool:
    path = DB / "Reports" / "board" / "daily-reports-due.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict) or data.get("day") != today:
        return False
    mid = (data.get("slots") or {}).get("midday") or {}
    return str(mid.get("status") or "") == "done"


def default_wav() -> Path:
    return (VOICE / WAV_NAME).resolve()


def morning_wav(path: Path, today: str) -> str | None:
    """Return a refusal reason, or None when the file is today's morning boot WAV."""
    voice = VOICE.resolve()
    try:
        if not path.is_relative_to(voice):
            return "outside_voice"
    except ValueError:
        return "outside_voice"
    if not path.is_file() or path.stat().st_size <= 0:
        return "wav_missing"
    low = path.name.lower()
    if "midday" in low or "evening" in low or "late-report" in low:
        return "wrong_wav_type"
    dated = DATED.search(path.name)
    if dated and dated.group(1) != today:
        return "stale_wav_day"
    try:
        mt = datetime.fromtimestamp(path.stat().st_mtime, HST)
    except OSError:
        return "wav_stat_failed"
    if mt.strftime("%Y-%m-%d") != today or mt.hour >= 12:
        return "stale_wav_mtime"
    return None


def disarm(reason: str) -> dict:
    now = now_hst()
    st = _load()
    if not st:
        result = {"ok": True, "skipped": True, "reason": "no_state"}
        _log(result)
        return result
    was = bool(st.get("enabled"))
    st["enabled"] = False
    st["play_once"] = False
    st["stopped_at"] = now.isoformat()
    st["stop_reason"] = str(reason or "operator")[:160]
    _save(st)
    result = {"ok": True, "disarmed": True, "was_enabled": was, "reason": st["stop_reason"]}
    _log(result)
    return result


def arm() -> dict:
    now = now_hst()
    today = now.strftime("%Y-%m-%d")
    path = default_wav()
    why = morning_wav(path, today)
    if why:
        result = {"ok": False, "armed": False, "detail": why, "wav": str(path)}
        _log(result)
        return result
    st = _load()
    st.update({
        "enabled": True,
        "day": today,
        "until": _noon(now).isoformat(),
        "play_once": False,
        "wav": str(path),
        "current": str(path),
        "armed_at": now.isoformat(),
    })
    st.pop("stopped_at", None)
    st.pop("stop_reason", None)
    _save(st)
    result = {"ok": True, "armed": True, "day": today, "until": st["until"], "wav": str(path)}
    _log(result)
    return result


def _handoff(path: Path) -> dict:
    if not PLAYER.is_file():
        return {"ok": False, "detail": "report_playback_missing", "function": "Report playback"}
    proc = subprocess.run(
        [sys.executable, str(PLAYER), "--report", "boot_brief", "--dry-run"],
        capture_output=True,
        text=True,
        timeout=60,
        env=os.environ.copy(),
    )
    last = (proc.stdout or "").strip().splitlines()
    try:
        body = json.loads(last[-1]) if last else {}
    except ValueError:
        body = {"detail": "player_output"}
    body["rc"] = proc.returncode
    if path.name != WAV_NAME:
        body["note"] = "player reads boot_brief_current.wav"
    return body


def run(dry_run: bool = True) -> dict:
    """Decide, then hand off with --dry-run. dry_run is always the speaker mode."""
    del dry_run  # this folder never opens a speaker
    now = now_hst()
    today = now.strftime("%Y-%m-%d")
    st = _load()
    if not st.get("enabled"):
        # A disarm for today stays off. A new morning WAV may arm once.
        if str(st.get("day") or "") == today or midday_done(today):
            result = {"ok": True, "skipped": True, "reason": "disabled"}
            _log(result)
            return result
        armed = arm()
        if not armed.get("armed"):
            return armed
        st = _load()

    until_raw = str(st.get("until") or "").strip()
    try:
        until = datetime.fromisoformat(until_raw)
        if until.tzinfo is None:
            until = until.replace(tzinfo=HST)
    except ValueError:
        until = _noon(now)
    noon = _noon(until)
    if until > noon:
        until = noon
    if now >= until:
        return disarm("past_until")

    armed_day = str(st.get("day") or st.get("armed_day") or "").strip()
    if not armed_day:
        for key in ("until", "armed_at"):
            raw = str(st.get(key) or "")
            if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
                armed_day = raw[:10]
                break
    if armed_day and armed_day != today:
        return disarm("stale_day")

    if midday_done(today):
        return disarm("midday_ok")

    play_once = bool(st.get("play_once"))
    if not play_once and now.minute != 32:
        result = {"ok": True, "skipped": True, "reason": "not_:32"}
        _log(result)
        return result

    path = default_wav()
    why = morning_wav(path, today)
    if why in {"wrong_wav_type", "stale_wav_day", "stale_wav_mtime"}:
        return disarm(why)
    if why:
        result = {"ok": False, "played": False, "detail": why, "wav": str(path)}
        _log(result)
        return result

    player = _handoff(path)
    # play.py reports audio_missing with ok=true. Only a dry-run of the real file counts.
    if player.get("rc") != 0 or player.get("detail") != "dry_run":
        result = {"ok": False, "played": False, "detail": player.get("detail") or "player_failed", "player": player, "wav": str(path)}
        _log(result)
        return result

    st["play_once"] = False
    st["last_played_at"] = now.isoformat()
    st["last_played"] = str(path)
    _save(st)
    result = {
        "ok": True,
        "played": True,
        "wav": str(path),
        "play_once_cleared": play_once,
        "player": player.get("detail"),
        "speaker": False,
    }
    _log(result)
    return result


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = "run"
    if args and args[0] in {"arm", "run", "disarm"}:
        cmd = args.pop(0)
    reason = "operator"
    if "--reason" in args:
        i = args.index("--reason")
        if i + 1 < len(args):
            reason = args[i + 1]
    if cmd == "arm":
        result = arm()
    elif cmd == "disarm":
        result = disarm(reason)
    else:
        result = run(dry_run=True)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
