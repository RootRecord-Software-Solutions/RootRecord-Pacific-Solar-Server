#!/usr/bin/env python3
"""River 2 Pro car DC drive automation. Copy jobs stay a stub.

Never toggles AC. Default car DC off. A tick does nothing until auto is true
and an enabled copy job exists. Copy is not implemented, so the tick does not
spin disks or run the BLE scripts.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from disk_session import prepare, release, snapshot  # noqa: E402
from river_car_dc import (  # noqa: E402
    PURPOSE,
    STATE_DIR,
    last_car_on,
    load_state as load_car_state,
    status as car_status,
)

STATE_NAME = "drive-automation.json"
LOCK_NAME = "drive-automation.lock"
PURPOSE_AUTO = "external-drives-automation"

DEFAULT: dict[str, Any] = {
    "purpose": PURPOSE_AUTO,
    "auto": False,
    "hold_car_on": False,
    "copy_jobs": [],
    "last_tick": None,
    "last_action": None,
    "last_skip": "auto_off",
    "note": "River car 12V for drives. Copy jobs empty until wired. Never AC.",
}


def state_path() -> Path:
    return STATE_DIR / STATE_NAME


def lock_path() -> Path:
    return STATE_DIR / LOCK_NAME


def load_config() -> dict[str, Any]:
    base = dict(DEFAULT)
    path = state_path()
    if not path.is_file():
        return base
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return base
    if isinstance(raw, dict):
        base.update(raw)
    if not isinstance(base.get("copy_jobs"), list):
        base["copy_jobs"] = []
    base["auto"] = bool(base.get("auto"))
    base["hold_car_on"] = bool(base.get("hold_car_on"))
    return base


def save_config(cfg: dict[str, Any]) -> dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = state_path()
    out = dict(DEFAULT)
    out.update(cfg)
    out["auto"] = bool(out.get("auto"))
    out["hold_car_on"] = bool(out.get("hold_car_on"))
    if not isinstance(out.get("copy_jobs"), list):
        out["copy_jobs"] = []
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return out


def enabled_copy_jobs(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    cfg = cfg if isinstance(cfg, dict) else load_config()
    out: list[dict[str, Any]] = []
    for raw in cfg.get("copy_jobs") or []:
        if not isinstance(raw, dict) or not raw.get("enabled"):
            continue
        if not str(raw.get("id") or "").strip():
            continue
        out.append(raw)
    return out


def run_copy_jobs(jobs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Stub. Does not rsync or unmount."""
    pending = jobs if jobs is not None else enabled_copy_jobs()
    if not pending:
        return {"ok": True, "ran": 0, "skipped": "no_copy_jobs"}
    ids = [str(job.get("id") or "") for job in pending]
    return {
        "ok": False,
        "ran": 0,
        "skipped": "copy_not_implemented",
        "pending": ids,
        "note": "Power path is gated. This stub will not rsync.",
    }


def _try_lock() -> Any:
    path = lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = path.open("a+", encoding="utf-8")
    try:
        import fcntl

        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return None
    return fh


def status(*, live: bool = False) -> dict[str, Any]:
    del live  # kept so the old flag does not start a cloud or BLE read
    cfg = load_config()
    car = car_status()
    disks = snapshot()
    enabled = enabled_copy_jobs(cfg)
    return {
        "ok": True,
        "purpose": PURPOSE,
        "auto": bool(cfg.get("auto")),
        "hold_car_on": bool(cfg.get("hold_car_on")),
        "copy_jobs_configured": len(cfg.get("copy_jobs") or []),
        "copy_jobs_enabled": len(enabled),
        "last_action": cfg.get("last_action"),
        "last_skip": cfg.get("last_skip"),
        "last_tick": cfg.get("last_tick"),
        "car": {
            "wanted": car.get("wanted"),
            "last_car_on": car.get("last_car_on"),
            "last_action": car.get("last_action"),
        },
        "usb_or_sata_present": bool(disks.get("usb_or_sata_present")),
        "nvme_only": bool(disks.get("nvme_only")),
        "backup_copy": False,
        "note": cfg.get("note"),
        "state_path": str(state_path()),
        "car_state": load_car_state().get("last_action"),
    }


def power_on(*, execute: bool = False, wait_s: int = 20) -> dict[str, Any]:
    return prepare(execute=bool(execute), wait_s=wait_s)


def power_off(*, execute: bool = False) -> dict[str, Any]:
    return release(execute=bool(execute))


def session(*, execute: bool = False, hold: bool | None = None, wait_s: int = 20) -> dict[str, Any]:
    """Power on, optional copy stub, power off unless hold or the port was already on."""
    cfg = load_config()
    hold_on = bool(cfg.get("hold_car_on") if hold is None else hold)
    fh = _try_lock()
    if fh is None:
        return {"ok": False, "blocked": "in_progress", "spawned": False}
    try:
        was_on = last_car_on() is True
        on = power_on(execute=bool(execute), wait_s=wait_s)
        report: dict[str, Any] = {
            "ok": bool(on.get("ok")),
            "phase": "session",
            "execute": bool(execute),
            "hold": hold_on,
            "was_already_on": was_on,
            "power_on": on,
            "copy": None,
            "power_off": None,
            "spawned": bool((on.get("car_action") or {}).get("spawned")),
        }
        if not execute:
            report["blocked"] = "dry_run"
            cfg["last_action"] = "dry_run_session"
            cfg["last_skip"] = "dry_run"
            save_config(cfg)
            return report
        if not on.get("ok"):
            report["blocked"] = "power_on_failed"
            cfg["last_action"] = "session_power_on_failed"
            cfg["last_skip"] = on.get("blocked") or "power_on_failed"
            save_config(cfg)
            return report
        copy = run_copy_jobs()
        report["copy"] = copy
        if hold_on or was_on:
            report["power_off"] = {"ok": True, "skipped": "hold" if hold_on else "already_on", "spawned": False}
            report["left_on"] = True
        else:
            off = power_off(execute=True)
            report["power_off"] = off
            report["spawned"] = bool(report["spawned"] or off.get("spawned"))
            report["ok"] = bool(report["ok"] and off.get("ok"))
        cfg["last_action"] = "session"
        cfg["last_skip"] = copy.get("skipped")
        cfg["last_tick"] = time.time()
        save_config(cfg)
        return report
    finally:
        try:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        fh.close()


def tick(*, execute: bool = True) -> dict[str, Any]:
    """Scheduler entry. No BLE script until auto, a copy job, and copy is implemented."""
    cfg = load_config()
    cfg["last_tick"] = time.time()
    if not cfg.get("auto"):
        cfg["last_skip"] = "auto_off"
        save_config(cfg)
        return {"ok": True, "skipped": "auto_off", "execute": bool(execute), "spawned": False}
    jobs = enabled_copy_jobs(cfg)
    if not jobs:
        cfg["last_skip"] = "no_copy_jobs"
        save_config(cfg)
        return {"ok": True, "skipped": "no_copy_jobs", "execute": bool(execute), "spawned": False}
    probe = run_copy_jobs(jobs)
    if probe.get("skipped") == "copy_not_implemented":
        cfg["last_skip"] = "copy_not_implemented"
        save_config(cfg)
        return {
            "ok": True,
            "skipped": "copy_not_implemented",
            "execute": bool(execute),
            "pending": probe.get("pending"),
            "spawned": False,
        }
    return session(execute=bool(execute), hold=bool(cfg.get("hold_car_on")))


def set_auto(on: bool) -> dict[str, Any]:
    cfg = load_config()
    cfg["auto"] = bool(on)
    cfg["last_action"] = "auto_on" if on else "auto_off"
    cfg["last_skip"] = None if on else "auto_off"
    return save_config(cfg)


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, default=str))
    if payload.get("skipped"):
        print(f"skipped={payload['skipped']}")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="River 2 Pro car DC drive automation (dry-run default).")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--on", action="store_true", help="Power drives on.")
    parser.add_argument("--off", action="store_true", help="Power drives off.")
    parser.add_argument("--session", action="store_true", help="On, copy stub, off unless --hold.")
    parser.add_argument("--tick", action="store_true", help="Scheduler tick (respects auto).")
    parser.add_argument("--hold", action="store_true", help="Leave car DC on after session.")
    parser.add_argument("--auto", choices=("on", "off"), help="Enable or disable scheduled sessions.")
    parser.add_argument("--execute", action="store_true", help="Allow the BLE script. Refuses unless RR_RIVER_CAR_EXECUTE=1.")
    args = parser.parse_args(argv)
    if args.auto:
        _emit(set_auto(args.auto == "on"))
        return 0
    flags = sum(bool(x) for x in (args.on, args.off, args.session, args.tick, args.status))
    if flags > 1:
        print(json.dumps({"ok": False, "error": "one_action"}))
        return 2
    if args.execute and not any((args.on, args.off, args.session, args.tick)):
        print(json.dumps({"ok": False, "error": "refused", "spawned": False}))
        return 1
    if args.on:
        out = power_on(execute=bool(args.execute))
        _emit(out)
        return 0 if out.get("ok") else 1
    if args.off:
        out = power_off(execute=bool(args.execute))
        _emit(out)
        return 0 if out.get("ok") else 1
    if args.session:
        out = session(execute=bool(args.execute), hold=bool(args.hold))
        _emit(out)
        return 0 if out.get("ok") else 1
    if args.tick:
        out = tick(execute=bool(args.execute))
        _emit(out)
        return 0
    _emit(status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
