#!/usr/bin/env python3
"""PythonDrop allowlist runner (package PythonDrop).

Only a script named in config/catalog.json may run, and only when its path
stays inside this package tree. The shipped catalog has no entries, so
status and tick start nothing.

No drop-folder scan, no clock-slot directories, no GUI terminal, no
restart-on-exit, and no listening port.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "catalog.json"
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
DATA = DB / "System" / "PythonDrop"
FIRE_PATH = DATA / "last-fire.json"
LOG_DIR = DB / "Logs" / "System" / "PythonDrop"

INTERVALS = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}
HHMM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
RUN_TIMEOUT_S = 50


def _hst_now() -> datetime:
    return datetime.now(HST)


def _slot(now: datetime) -> str:
    minute = (now.minute // 5) * 5
    return f"{now.hour:02d}:{minute:02d}"


def _schedule_ok(schedule: str) -> bool:
    return schedule in INTERVALS or HHMM.fullmatch(schedule) is not None


def schedule_due(schedule: str, now: datetime) -> bool:
    """True when this HST clock is inside the entry's slot. Deduped per day by the caller."""
    if not _schedule_ok(schedule):
        return False
    slot_minute = (now.minute // 5) * 5
    matched = HHMM.fullmatch(schedule)
    if matched:
        hour = int(matched.group(1))
        minute = int(matched.group(2))
        if minute % 5 == 0:
            return now.hour == hour and slot_minute == minute
        return now.strftime("%H:%M") == schedule
    if schedule == "5m":
        return True
    if schedule == "15m":
        return slot_minute in (0, 15, 30, 45)
    if schedule == "30m":
        return slot_minute in (0, 30)
    return slot_minute == 0


def refusal_reason(root: Path, entry: object) -> str | None:
    """None means the entry is allowed to run. Any string means do not execute it."""
    if not isinstance(entry, dict):
        return "not_an_entry"
    name = entry.get("name")
    rel = entry.get("path")
    schedule = entry.get("schedule")
    if not isinstance(name, str) or not name.strip():
        return "missing_name"
    if not isinstance(rel, str) or not rel.strip():
        return "missing_path"
    if not isinstance(schedule, str) or not _schedule_ok(schedule):
        return "bad_schedule"
    if Path(rel).is_absolute() or rel.startswith("~") or ".." in Path(rel).parts:
        return "path_refused"
    if not rel.endswith(".py"):
        return "not_py"
    try:
        candidate = (root / rel).resolve()
        candidate.relative_to(root.resolve())
    except (OSError, ValueError):
        return "outside_tree"
    if not candidate.is_file():
        return "missing_file"
    return None


def load_catalog(path: Path | None = None) -> tuple[list, str | None]:
    catalog = path or CATALOG
    if not catalog.is_file():
        return [], None
    try:
        data = json.loads(catalog.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], "unreadable"
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return [], "unreadable"
    return entries, None


def select_runnable(entries: list, now: datetime, root: Path | None = None) -> tuple[list, list]:
    """Split catalog entries into (runnable, refused). Refused entries are never spawned."""
    package = root or ROOT
    runnable: list[dict] = []
    refused: list[tuple[dict, str]] = []
    for entry in entries:
        reason = refusal_reason(package, entry)
        if reason:
            refused.append((entry if isinstance(entry, dict) else {}, reason))
            continue
        if schedule_due(str(entry["schedule"]), now):
            runnable.append(entry)
    return runnable, refused


def _fire_id(now: datetime, entry: dict) -> str:
    day = now.strftime("%Y-%m-%d")
    return f"{day}|{entry['schedule']}|{_slot(now)}|{entry['name']}"


def _read_fire() -> dict:
    try:
        data = json.loads(FIRE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "fired": {}}
    if not isinstance(data, dict) or not isinstance(data.get("fired"), dict):
        return {"version": 1, "fired": {}}
    return data


def _write_fire(data: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    FIRE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _spawn(script: Path, fire_id: str) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-]+", "_", fire_id)[:120]
    log_path = LOG_DIR / f"{safe}.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n--- {_hst_now().isoformat()} start {script.name} ---\n")
        handle.flush()
        proc = subprocess.Popen(
            ["python3", str(script)],
            cwd=str(script.parent),
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            rc = proc.wait(timeout=RUN_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                proc.kill()
            rc = -9
        handle.write(f"--- exit {rc} ---\n")
    return int(rc)


def status_report(now: datetime | None = None) -> dict:
    moment = now or _hst_now()
    entries, error = load_catalog()
    if error:
        return {"due": [], "catalog": 0, "spawned": 0, "catalog_error": error}
    runnable, _refused = select_runnable(entries, moment)
    return {
        "due": [str(entry["name"]) for entry in runnable],
        "catalog": len(entries),
        "spawned": 0,
    }


def tick(now: datetime | None = None) -> dict:
    moment = now or _hst_now()
    entries, error = load_catalog()
    if error or not entries:
        report = {"due": [], "catalog": 0, "spawned": 0}
        if error:
            report["catalog_error"] = error
        return report
    runnable, _refused = select_runnable(entries, moment)
    fire = _read_fire()
    fired = dict(fire.get("fired") or {})
    spawned = 0
    for entry in runnable:
        fid = _fire_id(moment, entry)
        if fired.get(fid):
            continue
        script = (ROOT / str(entry["path"])).resolve()
        # Mark before spawn so a crash does not run the same slot twice.
        fired[fid] = int(moment.timestamp())
        cutoff = moment.timestamp() - 3 * 86400
        fire["fired"] = {key: value for key, value in fired.items() if int(value or 0) >= cutoff}
        _write_fire(fire)
        _spawn(script, fid)
        spawned += 1
    return {
        "due": [str(entry["name"]) for entry in runnable],
        "catalog": len(entries),
        "spawned": spawned,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PythonDrop allowlist runner")
    parser.add_argument("command", choices=("status", "tick"))
    args = parser.parse_args(argv)
    if args.command == "status":
        report = status_report()
    else:
        report = tick()
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
