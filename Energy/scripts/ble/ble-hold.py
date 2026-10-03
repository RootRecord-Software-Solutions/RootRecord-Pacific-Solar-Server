# ==============================================================================
# FILE: Energy/scripts/ble/ble-hold.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Hold one EcoFlow GATT session open and refresh samples until SIGTERM."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import asyncio  # info: import asyncio
import os  # info: import os
import signal  # info: import signal
import sys  # info: import sys
import time  # info: import time
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

ENERGY = Path(__file__).resolve().parents[2]  # info: set ENERGY
LIB = ENERGY / "lib"  # info: set LIB
PACIFIC = ENERGY.parent  # info: set PACIFIC
sys.path.insert(0, str(PACIFIC))  # info: Pacific root for Energy.db
sys.path.insert(0, str(PACIFIC / "System" / "lib"))  # info: shared current bank
sys.path.insert(0, str(LIB))  # info: Energy/lib wins for paths

from ble_client import connect, await_session, BleUnavailable  # noqa: E402
from Energy.db.condense import ensure_layers  # noqa: E402
from Energy.db.ingest import persist_eflow_device  # noqa: E402
import read_runner as rr  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
LOCK = Path("/tmp/ecoflow-ble.lock")  # info: set LOCK
SAMPLE_SEC = float(os.environ.get("ENERGY_BLE_HOLD_SAMPLE_S", "15"))  # info: set SAMPLE_SEC
RECONNECT_SEC = float(os.environ.get("ENERGY_BLE_HOLD_RECONNECT_S", "5"))  # info: set RECONNECT_SEC
# NeedBindInstallFirst often lands heartbeats late; stay on the link before giving up.
EMPTY_GRACE_SEC = float(os.environ.get("ENERGY_BLE_HOLD_EMPTY_GRACE_S", "90"))  # info: set EMPTY_GRACE_SEC
_stop = False  # info: set _stop


# ====================================================
# SECTION: function _handle
# What it does: Stop the hold loop on SIGTERM or SIGINT.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _handle(signum, frame):  # noqa: ARG001
    global _stop  # info: global _stop
    _stop = True  # info: set _stop


# ====================================================
# SECTION: function _log
# What it does: Print one hold line with HST time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _log(msg: str) -> None:  # info: def _log
    print(f"{datetime.now(HST).isoformat(timespec='seconds')} hold: {msg}", flush=True)  # info: call print


# ====================================================
# SECTION: function _publish
# What it does: Persist one live BLE sample from the open device into layers + JSON.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _publish(alias: str, device) -> str:  # info: def _publish
    fields = rr._fields_from_ble(device)  # info: set fields
    if not rr._has_data(fields):  # info: if not rr . _has_data ( fields ) :
        return "empty"  # info: return "empty"
    if rr._missing_inverter_watts(fields) and not rr._ac_outlet_on(fields):  # info: if inverter silent and outlet off
        rr._zero_missing_inverter_watts(fields)  # info: write 0 W for missing inverter fields
        rr._stamp_device_watts(device, fields)  # info: stamp the device object so persist matches
    observed_at = (  # info: set observed_at
        datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")  # info: UTC Z
    )  # info: )
    ensure_layers()  # info: call ensure_layers
    persist_eflow_device(device, alias, observed_at)  # info: call persist_eflow_device
    other = rr._collect_other_ac_outs(alias)  # info: set other
    charge = rr.derive_charge_source(fields, "ble", other, alias)  # info: set charge
    snap = rr._write_json_from_db(alias, "ble", charge)  # info: rebuild JSON from 1sec.db
    if not snap:  # info: if not snap
        return "db_miss"  # info: return "db_miss"
    f = snap["fields"]  # info: set f
    return (  # info: return (
        f"soc={f.get('soc')} ac_out={f.get('ac_output_power')} "  # info: soc and ac_out
        f"pv={f.get('solar_input_power')} usbc={f.get('usbc_output_power')} src=ble"  # info: pv usbc src
    )  # info: )


# ====================================================
# SECTION: function _keep_lcd_awake
# What it does: Set LCD timeout to never-off. LCD sleep drops EcoFlow BLE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
async def _keep_lcd_awake(device, alias: str) -> None:  # info: async def _keep_lcd_awake
    fn = getattr(device, "set_screen_timeout", None)  # info: set fn
    if fn is None:  # info: if this pack has no LCD timeout write
        _log(f"{alias} no set_screen_timeout on device")  # info: call _log
        return  # info: return
    try:  # info: try
        await fn(0)  # info: 0 = never off (lcdOffSec)
        _log(f"{alias} lcd timeout set to never-off")  # info: call _log
    except Exception as exc:  # info: except Exception as exc
        _log(f"{alias} lcd keep-awake failed {type(exc).__name__}: {exc}")  # info: call _log


# ====================================================
# SECTION: function _session
# What it does: Connect, keep LCD awake, sample until the link drops or stop is set.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
async def _session(alias: str) -> None:  # info: async def _session
    device = await connect(alias)  # info: set device
    try:  # info: try
        state, kind, proceed = await await_session(device, timeout=18)  # info: set state , kind , proceed
        if not proceed:  # info: if not proceed
            raise BleUnavailable(f"auth not completed state={state} exc={kind}")  # info: raise
        if getattr(state, "authenticated", False):  # info: if authenticated
            await asyncio.sleep(1.5)  # info: let the first heartbeat land
        _log(f"{alias} connected auth={kind} — holding link")  # info: call _log
        # Do not write LCD config until heartbeats land — a write while the screen is
        # asleep tears the link (NeedBind + NotConnectedError).
        empty_since = time.time()  # info: set empty_since
        got_data = False  # info: set got_data
        lcd_locked = False  # info: set lcd_locked
        lcd_nudge_at = 0.0  # info: set lcd_nudge_at
        while not _stop:  # info: while not _stop
            line = _publish(alias, device)  # info: set line
            if line == "empty":  # info: if fields have not landed yet
                waited = time.time() - empty_since  # info: set waited
                _log(f"{alias} waiting fields ({waited:.0f}s/{EMPTY_GRACE_SEC:.0f}s) — tap River LCD to wake BLE")  # info: call _log
                if got_data or waited >= EMPTY_GRACE_SEC:  # info: after a good streak, or past grace, reconnect
                    raise BleUnavailable("fields empty on held session (LCD sleep?)")  # info: raise so we reconnect
                await asyncio.sleep(2)  # info: poll soon; do not drop the GATT session
                continue  # info: continue
            empty_since = time.time()  # info: reset empty clock after a real sample
            got_data = True  # info: set got_data
            _log(f"{alias} sample {line}")  # info: call _log
            if not lcd_locked or time.time() - lcd_nudge_at > 300:  # info: latch never-off after first live sample
                await _keep_lcd_awake(device, alias)  # info: call _keep_lcd_awake
                lcd_locked = True  # info: set lcd_locked
                lcd_nudge_at = time.time()  # info: set lcd_nudge_at
            for _ in range(int(max(1, SAMPLE_SEC))):  # info: sleep in 1 s slices for SIGTERM
                if _stop:  # info: if _stop
                    break  # info: break
                await asyncio.sleep(1)  # info: await asyncio . sleep ( 1 )
    finally:  # info: finally
        try:  # info: try
            await device.disconnect()  # info: await device . disconnect ( )
        except Exception:  # info: except Exception
            pass  # info: pass
        _log(f"{alias} disconnected")  # info: call _log


# ====================================================
# SECTION: function main
# What it does: Claim the BLE lock and keep one pack connected.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    p = argparse.ArgumentParser()  # info: set p
    p.add_argument("--device", default="river2pro")  # info: default to the live pack
    args = p.parse_args()  # info: set args
    alias = args.device  # info: set alias
    signal.signal(signal.SIGTERM, _handle)  # info: signal . signal ( signal . SIGTERM ,
    signal.signal(signal.SIGINT, _handle)  # info: signal . signal ( signal . SIGINT ,
    lock_fd = os.open(str(LOCK), os.O_CREAT | os.O_RDWR, 0o666)  # info: set lock_fd
    import fcntl  # info: import fcntl
    try:  # info: try
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # info: non-blocking exclusive lock
    except BlockingIOError:  # info: except BlockingIOError
        _log("refusing start — ecoflow-ble.lock already held")  # info: call _log
        return 1  # info: return 1
    _log(f"start alias={alias} sample_s={SAMPLE_SEC}")  # info: call _log
    try:  # info: try
        while not _stop:  # info: while not _stop
            try:  # info: try
                asyncio.run(_session(alias))  # info: asyncio . run ( _session ( alias ) )
            except BleUnavailable as exc:  # info: except BleUnavailable as exc
                _log(f"{alias} miss {exc}")  # info: call _log
            except Exception as exc:  # info: except Exception as exc
                _log(f"{alias} error {type(exc).__name__}: {exc}")  # info: call _log
            if _stop:  # info: if _stop
                break  # info: break
            time.sleep(RECONNECT_SEC)  # info: brief gap before reconnect
    finally:  # info: finally
        try:  # info: try
            fcntl.flock(lock_fd, fcntl.LOCK_UN)  # info: release lock
        except Exception:  # info: except Exception
            pass  # info: pass
        os.close(lock_fd)  # info: os . close ( lock_fd )
        _log("stop")  # info: call _log
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
