#!/usr/bin/env python3
"""23:30 second chance for the optional late roll-up (G1 late-final-report).

Same report as voice_reports.py late_report. Skips when the board slot late is
already done or running. Text only (--no-voice). Never plays audio.

Night sleep: if System/NightSleep/scripts/night_sleep.py exists, call should_run.
A missing Folder means not sleeping (G1 missing night-mode.json). This script
does not implement that gate.

  python3 late_final.py            run the template when the late slot is open
  python3 late_final.py --dry-run  print skip or would-run; write last JSON only
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
PACIFIC = HERE.parents[2]
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
STATE = DB / "Reports" / "board" / "daily-reports-due.json"
LAST = DB / "Reports" / "Late-Final" / "last.json"
LOG = DB / "Logs" / "Reports" / "Late-Final" / "late-final.jsonl"
REPORTS = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))
VOICE = PACIFIC / "Media" / "Voice" / "scripts" / "voice_reports.py"
GATE = PACIFIC / "System" / "NightSleep" / "scripts" / "night_sleep.py"
JOB_ID = "voice_late_final_report"
LATE_HOUR, LATE_MINUTE = 21, 2


def now() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def late_status(t: datetime) -> str:
    """done / running / open. Read-only. Does not seed or rewrite the board."""
    day = t.strftime("%Y-%m-%d")
    try:
        d = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    if isinstance(d, dict) and d.get("day") == day:
        row = (d.get("slots") or {}).get("late")
        if isinstance(row, dict) and row.get("status") in ("done", "running"):
            return str(row["status"])
    f = REPORTS / "late_report_current.md"
    if f.is_file():
        mt = datetime.fromtimestamp(f.stat().st_mtime, HST)
        due = t.replace(hour=LATE_HOUR, minute=LATE_MINUTE, second=0, microsecond=0)
        if mt.date() == t.date() and mt >= due:
            return "done"
    return "open"


def night_skip() -> str | None:
    """None means run. 'night_sleep' means the NightSleep gate said skip.

    A missing gate Folder is not sleeping. Errors in the gate are not sleeping,
    matching G1 night_sleeping() on a bad file.
    """
    if not GATE.is_file():
        return None
    spec = importlib.util.spec_from_file_location("night_sleep", GATE)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        fn = getattr(mod, "should_run", None)
        if not callable(fn):
            return None
        try:
            allowed = fn(JOB_ID)
        except TypeError:
            allowed = fn()
    except Exception:
        return None
    return None if allowed else "night_sleep"


def write_last(payload: dict, dry_run: bool) -> None:
    LAST.parent.mkdir(parents=True, exist_ok=True)
    tmp = LAST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, LAST)
    if dry_run:
        return
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    dry = "--dry-run" in sys.argv
    t = now()
    status = late_status(t)
    base = {"at": t.isoformat(), "job": JOB_ID, "late_status": status, "dry_run": dry,
            "night_sleep_folder": GATE.is_file(), "voice": False}
    skip = night_skip()
    if skip:
        payload = dict(base, result="skip", detail=skip)
    elif status in ("done", "running"):
        payload = dict(base, result="skip", detail="already_done" if status == "done" else "already_running")
    elif dry:
        payload = dict(base, result="would-run", detail="late_slot_open")
    else:
        cmd = ["nice", "-n", "10", sys.executable, str(VOICE), "late_report", "--no-voice"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            ok = p.returncode == 0
            payload = dict(base, result="ran" if ok else "failed", rc=p.returncode,
                           out=(p.stdout or "").strip()[-400:], err=(p.stderr or "").strip()[-400:])
        except (OSError, subprocess.TimeoutExpired) as e:
            payload = dict(base, result="failed", detail=type(e).__name__)
            ok = False
        write_last(payload, dry_run=False)
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload.get("result") == "ran" else 1
    write_last(payload, dry_run=dry)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
