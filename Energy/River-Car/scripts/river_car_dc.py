#!/usr/bin/env python3
"""River 2 Pro car/12V policy for external drives. Dry-run unless execute is signed off.

Never switches AC. Never calls the EcoFlow cloud API. The only actuator is the live
BLE scripts river2pro-dc-on.sh / river2pro-dc-off.sh, and only when --execute is
set and RR_RIVER_CAR_EXECUTE=1.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
PACIFIC = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server")
DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
STATE_DIR = DATABASE / "Energy" / "River-Car"
LOG_DIR = DATABASE / "Logs" / "Energy" / "River-Car"
SAMPLES = DATABASE / "Energy" / "samples"
PORTS = DATABASE / "Energy" / "ports"
ACTIONS = PACIFIC / "Energy" / "scripts" / "actions"
STATE_NAME = "river-car-dc.json"
LOG_NAME = "river-car.log"
PURPOSE = "external-drives"
EXECUTE_ENV = "RR_RIVER_CAR_EXECUTE"


def _log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(HST).isoformat(timespec='seconds')} {msg}\n"
    with (LOG_DIR / LOG_NAME).open("a", encoding="utf-8") as fh:
        fh.write(line)


def state_path() -> Path:
    return STATE_DIR / STATE_NAME


def load_state() -> dict[str, Any]:
    base: dict[str, Any] = {
        "purpose": PURPOSE,
        "wanted": False,
        "last_car_on": None,
        "last_action": None,
        "last_action_at": None,
        "note": "External drives on River car DC. Default off. Copy is a stub. No AC.",
    }
    path = state_path()
    if not path.is_file():
        return base
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return base
    if isinstance(raw, dict):
        base.update(raw)
    return base


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = state_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return bool(int(value))
    if isinstance(value, str):
        token = value.strip().lower()
        if token in {"1", "true", "on", "yes"}:
            return True
        if token in {"0", "false", "off", "no"}:
            return False
    return None


def _dc_from_payload(raw: dict[str, Any]) -> bool | None:
    fields = raw.get("fields") if isinstance(raw.get("fields"), dict) else raw
    if isinstance(fields, dict) and "dc_12v_port" in fields:
        return _boolish(fields.get("dc_12v_port"))
    if "readback" in raw:
        return _boolish(raw.get("readback"))
    return None


def last_car_on() -> bool | None:
    """Last stored River 2 Pro dc_12v_port. Does not poll BLE or the cloud."""
    candidates: list[Path] = []
    port = PORTS / "river2pro-last.json"
    if port.is_file():
        candidates.append(port)
    reads = sorted(SAMPLES.glob("read-river2pro-*.json"))
    if reads:
        candidates.append(reads[-1])
    best: Path | None = None
    best_mtime = -1.0
    for path in candidates:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime >= best_mtime:
            best_mtime = mtime
            best = path
    if best is None:
        return None
    try:
        raw = json.loads(best.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return _dc_from_payload(raw)


def execute_allowed() -> bool:
    return os.environ.get(EXECUTE_ENV, "0") == "1"


def _spawn_dc(want_on: bool) -> dict[str, Any]:
    """Run the live BLE action script. Callers must pass the execute gate first."""
    name = "river2pro-dc-on.sh" if want_on else "river2pro-dc-off.sh"
    script = ACTIONS / name
    if not script.is_file():
        return {"ok": False, "error": "missing_action_script", "script": name}
    try:
        proc = subprocess.run(
            [str(script)],
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": type(exc).__name__, "script": name}
    tail = (proc.stdout or "").strip().splitlines()
    status = next((line for line in tail if line.startswith("STATUS=")), "")
    return {
        "ok": proc.returncode == 0 and status == "STATUS=OK",
        "returncode": proc.returncode,
        "status": status or None,
        "script": name,
    }


def set_car(*, want_on: bool, execute: bool = False, force: bool = False) -> dict[str, Any]:
    """Want the car port on or off. execute=False is dry-run and does not spawn."""
    st = load_state()
    already = last_car_on()
    report: dict[str, Any] = {
        "ok": True,
        "wanted": bool(want_on),
        "execute": bool(execute),
        "would": "car_on" if want_on else "car_off",
        "already_on": already,
        "spawned": False,
    }
    if not want_on and already is True and not force:
        st["wanted"] = True
        st["last_action"] = "leave_on_manual"
        st["last_action_at"] = time.time()
        st["last_car_on"] = True
        save_state(st)
        report["action"] = "leave_on_manual"
        report["left_on"] = True
        report["would"] = "leave_on"
        _log("leave_on_manual")
        return report
    st["wanted"] = bool(want_on)
    st["purpose"] = PURPOSE
    if not execute:
        action = f"dry_run_{'on' if want_on else 'off'}"
        st["last_action"] = action
        st["last_action_at"] = time.time()
        save_state(st)
        report["action"] = action
        _log(action)
        return report
    if not execute_allowed():
        st["last_action"] = "execute_refused"
        st["last_skip_reason"] = EXECUTE_ENV
        st["last_action_at"] = time.time()
        save_state(st)
        report["ok"] = False
        report["action"] = "execute_refused"
        report["error"] = "refused"
        report["reason"] = f"{EXECUTE_ENV} is not 1"
        _log("execute_refused")
        return report
    switched = _spawn_dc(want_on)
    report["spawned"] = True
    report["switch"] = {k: switched.get(k) for k in ("ok", "returncode", "status", "error", "script")}
    if not switched.get("ok"):
        report["ok"] = False
        st["last_action"] = f"switch_failed_{'on' if want_on else 'off'}"
        st["last_skip_reason"] = switched.get("error") or switched.get("status")
        st["last_action_at"] = time.time()
        save_state(st)
        report["action"] = st["last_action"]
        _log(report["action"])
        return report
    st["last_action"] = "on" if want_on else "off"
    st["last_action_at"] = time.time()
    st["last_car_on"] = bool(want_on)
    st["last_skip_reason"] = None
    save_state(st)
    report["action"] = st["last_action"]
    _log(f"switched {report['action']}")
    return report


def status() -> dict[str, Any]:
    st = load_state()
    return {
        "ok": True,
        "purpose": PURPOSE,
        "wanted": bool(st.get("wanted")),
        "last_car_on": last_car_on(),
        "last_action": st.get("last_action"),
        "state_path": str(state_path()),
        "execute_gate": EXECUTE_ENV,
        "execute_allowed": execute_allowed(),
        "backup_job": False,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="River 2 Pro car DC for external drives (dry-run default).")
    parser.add_argument("--on", action="store_true", help="Want car DC on (drives).")
    parser.add_argument("--off", action="store_true", help="Want car DC off (drives idle).")
    parser.add_argument("--status", action="store_true", help="Read state and the last stored car flag.")
    parser.add_argument("--execute", action="store_true", help="Run the live BLE script. Refuses unless RR_RIVER_CAR_EXECUTE=1.")
    args = parser.parse_args(argv)
    if args.on and args.off:
        print(json.dumps({"ok": False, "error": "on_and_off"}))
        return 2
    if args.execute and not args.on and not args.off:
        print(json.dumps({"ok": False, "error": "refused", "reason": f"{EXECUTE_ENV} action missing"}))
        return 1
    if args.status or (not args.on and not args.off):
        print(json.dumps(status(), indent=2))
        return 0
    report = set_car(want_on=bool(args.on), execute=bool(args.execute))
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
