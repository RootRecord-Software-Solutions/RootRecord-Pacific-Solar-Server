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
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
# Pacific copy: log/pid live under the canonical RootRecord Database (2026-09-29); override via env.
LOG = Path(os.environ.get("ENERGY_BLE_LOG", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/logs/ava-ecoflow-ble.log"))  # info: set LOG
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

def _range_line() -> str:  # info: def _range_line
    """Scan both packs when the last sight is stale. Does not open a GATT session."""  # info: docstring
    import json  # info: import json
    sys.path.insert(0, "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/lib")  # info: lib path
    try:  # info: try
        from config import device as device_cfg  # info: devices.conf mac only
        from paths import STATE_DIR, ensure_dirs  # info: state dir
        from ble_client import note_sight, _scan  # info: shared sight writer
    except Exception as exc:  # info: except
        return f"sight_import_fail {type(exc).__name__}"  # info: return
    bits = []  # info: set bits
    stale = []  # info: set stale
    now = time.time()  # info: set now
    for alias in ("river2pro", "delta2"):  # info: both packs
        path = STATE_DIR / f"ble-sight-{alias}.json"  # info: set path
        seen, age, detail = False, 999999, "missing"  # info: defaults
        if path.is_file():  # info: if sight file
            try:  # info: try
                data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
                seen = bool(data.get("seen"))  # info: set seen
                age = max(0, int(now - float(data.get("at_epoch") or 0)))  # info: set age
                detail = str(data.get("detail") or "")[:40]  # info: set detail
            except Exception:  # info: except
                detail = "bad"  # info: set detail
        bits.append(f"{alias} seen={int(seen)} age={age}s {detail}")  # info: append
        if age > 90:  # info: stale sight
            stale.append(alias)  # info: append
    if stale:  # info: if a pack has gone quiet
        import asyncio  # info: import asyncio
        async def _once():  # info: async def
            found = []  # info: set found
            for alias in stale:  # info: for alias
                mac = (device_cfg(alias).get("mac") or "").strip()  # info: mac from devices.conf
                if not mac:  # info: if no mac
                    note_sight(alias, False, "no_mac")  # info: note
                    continue  # info: continue
                rec = await _scan(mac, 6.0)  # info: short scan, no connect
                note_sight(alias, bool(rec), "owner_scan_seen" if rec else "owner_scan_miss")  # info: note
                found.append(f"{alias}:{'seen' if rec else 'miss'}")  # info: append
            return ",".join(found)  # info: return
        try:  # info: try
            bits.append("scan=" + asyncio.run(_once()))  # info: append
        except Exception as exc:  # info: except
            bits.append(f"scan_fail={type(exc).__name__}")  # info: append
    watts = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/watts")  # info: set watts
    stagnant = False  # info: set stagnant
    for name in ("river2pro-last.json", "delta2-last.json"):  # info: for name
        path = watts / name  # info: set path
        age = 999999 if not path.is_file() else max(0, int(now - path.stat().st_mtime))  # info: set age
        if age > 30 * 60:  # info: if the sample is past the speak threshold
            stagnant = True  # info: set stagnant
            bits.append(f"{name} age={age}s")  # info: append
    stamp = Path("/tmp/ecoflow-owner-wake")  # info: set stamp
    stamp_age = 999999 if not stamp.is_file() else max(0, int(now - stamp.stat().st_mtime))  # info: set stamp_age
    if stagnant and stamp_age > 30 * 60:  # info: if a sample stagnated and the wake is not in cooldown
        script = "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/scripts/read/leapfrog-read.sh"  # info: set script
        try:  # info: try
            subprocess.run(["bash", script], timeout=90, check=False)  # info: wake the existing read
            stamp.write_text(str(int(now)))  # info: stamp . write_text
            bits.append("wake=read")  # info: append
        except (OSError, subprocess.TimeoutExpired) as exc:  # info: except
            bits.append(f"wake_fail={type(exc).__name__}")  # info: append
    return " | ".join(bits)  # info: return


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
            _log("heartbeat " + _range_line())  # info: keepalive sight for both packs; GATT stays with the reader
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
