#!/usr/bin/env python3
"""Single BLE owner process — thin heartbeat. No aggressive pack polling.

Atomic actions take short connect sessions themselves. This process only:
- claims ownership (pid file)
- appends a 1 Hz-friendly heartbeat to the BLE log when woken
- sleeps most of the time (default 30s) to stay thin-solar friendly

Do NOT add device scan loops here until poll buckets are explicitly enabled.
"""
from __future__ import annotations
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
# Pacific copy: log/pid live under the canonical RootRecord Database (2026-09-29); override via env.
LOG = Path(os.environ.get("ENERGY_BLE_LOG", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Energy/ava-ecoflow-ble.log"))
PID = Path(os.environ.get("ENERGY_BLE_PID", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/state/ava-ecoflow-ble.pid"))
INTERVAL = float(os.environ.get("ENERGY_BLE_OWNER_INTERVAL_S", "30"))
_stop = False


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(HST).isoformat(timespec='seconds')} owner: {msg}\n"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="", flush=True)


def _handle(signum, frame):  # noqa: ARG001
    global _stop
    _stop = True


def main() -> int:
    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)
    PID.parent.mkdir(parents=True, exist_ok=True)
    if PID.is_file():
        try:
            old = int(PID.read_text().strip() or "0")
            os.kill(old, 0)
            _log(f"refusing start — already owned by pid={old}")
            return 1
        except (ProcessLookupError, ValueError, PermissionError):
            pass
    PID.write_text(str(os.getpid()), encoding="utf-8")
    _log(f"start pid={os.getpid()} interval_s={INTERVAL} (thin owner; no pack scan)")
    try:
        while not _stop:
            _log("heartbeat ok — atomic actions own short BLE sessions; poll buckets disabled")
            # sleep in 1s slices so SIGTERM is prompt; log-watch can see steady file growth
            for _ in range(int(max(1, INTERVAL))):
                if _stop:
                    break
                time.sleep(1)
    finally:
        _log("stop")
        try:
            if PID.is_file() and PID.read_text().strip() == str(os.getpid()):
                PID.unlink(missing_ok=True)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
