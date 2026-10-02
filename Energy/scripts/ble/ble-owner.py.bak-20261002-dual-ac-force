# ==============================================================================
# FILE: Energy/scripts/ble/ble-owner.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Single BLE owner process — thin heartbeat. No aggressive pack polling.

Atomic actions take short connect sessions themselves. This process only:
- claims ownership (pid file)
- appends a 1 Hz-friendly heartbeat to the BLE log when woken
- sleeps most of the time (default 30s) to stay thin-solar friendly

Do NOT add device scan loops here until poll buckets are explicitly enabled.
"""
from __future__ import annotations  # info: from __future__ import annotations
import os  # info: import os
import signal  # info: import signal
import sys  # info: import sys
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
# Pacific copy: log/pid live under the canonical RootRecord Database (2026-09-29); override via env.
LOG = Path(os.environ.get("ENERGY_BLE_LOG", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Energy/ava-ecoflow-ble.log"))  # info: set LOG
PID = Path(os.environ.get("ENERGY_BLE_PID", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/state/ava-ecoflow-ble.pid"))  # info: set PID
INTERVAL = float(os.environ.get("ENERGY_BLE_OWNER_INTERVAL_S", "30"))  # info: set INTERVAL
_stop = False  # info: set _stop


# ====================================================
# SECTION: function _log
# What it does:  log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _log(msg: str) -> None:  # info: def _log
    LOG.parent.mkdir(parents=True, exist_ok=True)  # info: LOG . parent . mkdir ( parents =
    line = f"{datetime.now(HST).isoformat(timespec='seconds')} owner: {msg}\n"  # info: set line
    with LOG.open("a", encoding="utf-8") as f:  # info: with LOG . open ( "a" , encoding
        f.write(line)  # info: f . write ( line )
    print(line, end="", flush=True)  # info: call print


# ====================================================
# SECTION: function _handle
# What it does:  handle.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _handle(signum, frame):  # noqa: ARG001
    global _stop  # info: global _stop
    _stop = True  # info: set _stop


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    signal.signal(signal.SIGTERM, _handle)  # info: signal . signal ( signal . SIGTERM ,
    signal.signal(signal.SIGINT, _handle)  # info: signal . signal ( signal . SIGINT ,
    PID.parent.mkdir(parents=True, exist_ok=True)  # info: PID . parent . mkdir ( parents =
    if PID.is_file():  # info: if PID . is_file ( ) :
        try:  # info: try :
            old = int(PID.read_text().strip() or "0")  # info: set old
            os.kill(old, 0)  # info: os . kill ( old , 0 )
            _log(f"refusing start — already owned by pid={old}")  # info: call _log
            return 1  # info: return 1
        except (ProcessLookupError, ValueError, PermissionError):  # info: except ( ProcessLookupError , ValueError , PermissionError )
            pass  # info: pass
    PID.write_text(str(os.getpid()), encoding="utf-8")  # info: PID . write_text ( str ( os .
    _log(f"start pid={os.getpid()} interval_s={INTERVAL} (thin owner; no pack scan)")  # info: call _log
    try:  # info: try :
        while not _stop:  # info: while not _stop :
            _log("heartbeat ok — atomic actions own short BLE sessions; poll buckets disabled")  # info: call _log
            # sleep in 1s slices so SIGTERM is prompt; log-watch can see steady file growth
            for _ in range(int(max(1, INTERVAL))):  # info: for _ in range ( int ( max
                if _stop:  # info: if _stop :
                    break  # info: break
                time.sleep(1)  # info: time . sleep ( 1 )
    finally:  # info: finally :
        _log("stop")  # info: call _log
        try:  # info: try :
            if PID.is_file() and PID.read_text().strip() == str(os.getpid()):  # info: if PID . is_file ( ) and PID
                PID.unlink(missing_ok=True)  # info: PID . unlink ( missing_ok = True )
        except Exception:  # info: except Exception :
            pass  # info: pass
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
