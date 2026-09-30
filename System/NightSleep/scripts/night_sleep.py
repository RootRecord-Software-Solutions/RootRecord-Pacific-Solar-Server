#!/usr/bin/env python3
"""Night-sleep scheduler gate (package NightSleep).

Reads Database System/NightSleep/night-mode.json. Missing or invalid file means
not sleeping. Does not write that flag, compute sunrise, or touch hardware.
The poller calls should_run only when RR_NIGHT_SLEEP=1 at process start.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
DATA = DB / "System" / "NightSleep"
STATE = DATA / "night-mode.json"
LAST = DATA / "last-skip.json"
LOG_DIR = DB / "Logs" / "System" / "NightSleep"
LOG_FILE = LOG_DIR / "night-sleep.log"

# Live ids that match G1 NIGHT_POLL, plus poller jobs that must keep running.
ALLOW = frozenset({
    "weather_poller",
    "geology_collect",
    "geology_kilauea_cams",
    "council_quake_telegram",
    "heartbeat",
    "ecoflow_read_boot",
    "ecoflow_read_cycle",
    "ensure_tunnel_online",
    "service_supervisor",
    "sys_stats_cycle",
    "network_globe_hawaii",
    "security_camera_server",
    "security_camera_frame_grab",
})


def gate_enabled() -> bool:
    return os.environ.get("RR_NIGHT_SLEEP", "0").strip() == "1"


def sleeping(path: Path | None = None) -> bool:
    p = path or STATE
    try:
        if not p.is_file():
            return False
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
        return bool(data.get("sleeping"))
    except Exception:
        return False


def _record_skip(job_id: str) -> None:
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        LAST.write_text(
            json.dumps({"job_id": job_id, "skipped": True, "at": stamp}) + "\n",
            encoding="utf-8",
        )
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} night sleep skip {job_id}\n")
    except Exception:
        return


def should_run(job_id: str, *, enabled: bool | None = None, state_path: Path | None = None) -> bool:
    """True when this job may run. Fail open when the gate is off or the file is bad."""
    if enabled is None:
        enabled = gate_enabled()
    if not enabled:
        return True
    jid = str(job_id or "")
    if jid in ALLOW:
        return True
    if not sleeping(state_path):
        return True
    _record_skip(jid)
    return False


def _check() -> int:
    import tempfile

    fd, name = tempfile.mkstemp(prefix="night-mode-", suffix=".json")
    os.close(fd)
    path = Path(name)
    try:
        path.write_text(json.dumps({"sleeping": True}), encoding="utf-8")
        if not should_run("weather_poller", enabled=True, state_path=path):
            print("FAIL weather_poller skipped while sleeping", file=sys.stderr)
            return 1
        if should_run("voice_late_report", enabled=True, state_path=path):
            print("FAIL voice_late_report ran while sleeping", file=sys.stderr)
            return 1
        if not LAST.is_file() or "voice_late_report" not in LAST.read_text(encoding="utf-8"):
            print("FAIL last-skip record missing", file=sys.stderr)
            return 1
        path.unlink()
        if not should_run("weather_poller", enabled=True, state_path=path):
            print("FAIL weather_poller blocked with no file", file=sys.stderr)
            return 1
        if not should_run("voice_late_report", enabled=True, state_path=path):
            print("FAIL voice_late_report blocked with no file", file=sys.stderr)
            return 1
        if not should_run("voice_late_report", enabled=False, state_path=path):
            print("FAIL gate-off blocked a job", file=sys.stderr)
            return 1
    finally:
        path.unlink(missing_ok=True)
    print("PASS night-sleep gate")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        raise SystemExit(_check())
    print("night-sleep gate installed; RR_NIGHT_SLEEP default off")
