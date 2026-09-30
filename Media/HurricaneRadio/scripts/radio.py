#!/usr/bin/env python3
"""Hand the hurricane desk WAV to Report playback. No speaker.

  python3 radio.py run

Always passes --dry-run. Never calls aplay. Never loads Kokoro.
Skips with night_sleep when System/NightSleep says sleeping.
A missing player is player_missing. A missing WAV is audio_missing.
A busy player is the overlap skip.

State: Database Media/HurricaneRadio/last-radio.json
Logs:  Database Logs/Media/HurricaneRadio/radio.log
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent
PACIFIC = Path(os.environ.get(
    "RR_PACIFIC_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server",
))
DB = Path(os.environ.get(
    "RR_DATABASE_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
))
STATE_DIR = DB / "Media" / "HurricaneRadio"
STATE_PATH = STATE_DIR / "last-radio.json"
LOG_DIR = DB / "Logs" / "Media" / "HurricaneRadio"
LOG_PATH = LOG_DIR / "radio.log"
PLAYER = PACIFIC / "Media" / "Playback" / "scripts" / "play.py"
NIGHT = PACIFIC / "System" / "NightSleep" / "scripts" / "night_sleep.py"
REPORT = "hurricane_desk"


def now_hst() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def _write_state(payload: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    body = dict(payload)
    body["at"] = now_hst().isoformat()
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATE_PATH)


def _log(payload: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)


def night_sleeping() -> bool:
    """Read NightSleep.sleeping. Missing module or a bad file means not sleeping."""
    if not NIGHT.is_file():
        return False
    spec = importlib.util.spec_from_file_location("rr_night_sleep", NIGHT)
    if spec is None or spec.loader is None:
        return False
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return bool(mod.sleeping())


def _handoff() -> dict:
    proc = subprocess.run(
        [sys.executable, str(PLAYER), "--report", REPORT, "--dry-run"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=os.environ.copy(),
    )
    detail = None
    played = False
    line = (proc.stdout or "").strip().splitlines()
    if line:
        try:
            body = json.loads(line[-1])
        except ValueError:
            body = {}
        detail = body.get("detail")
        played = bool(body.get("played"))
    if proc.returncode != 0 and not detail:
        detail = f"player_rc_{proc.returncode}"
    return {"detail": detail, "played": played, "rc": proc.returncode}


def run() -> dict:
    if night_sleeping():
        result = {"ok": True, "played": False, "detail": "night_sleep", "report": REPORT}
        _write_state(result)
        _log(result)
        return result

    if not PLAYER.is_file():
        result = {
            "ok": False,
            "played": False,
            "detail": "player_missing",
            "function": "Report playback",
            "report": REPORT,
        }
        _write_state(result)
        _log(result)
        return result

    player = _handoff()
    detail = str(player.get("detail") or "player_output")
    result = {
        "ok": player.get("rc") in {0, 3},
        "played": False,
        "detail": detail,
        "report": REPORT,
        "speaker": False,
    }
    _write_state(result)
    _log(result)
    return result


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] not in {"run"}:
        result = {"ok": False, "played": False, "detail": "bad_args"}
        _log(result)
        return 1
    result = run()
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
