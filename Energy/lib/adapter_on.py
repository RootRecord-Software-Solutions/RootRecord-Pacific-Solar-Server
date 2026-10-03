# ==============================================================================
# FILE: Energy/lib/adapter_on.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Unblock / power on / one recovery cycle for the Bluetooth adapter. No reboot."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import subprocess  # info: import subprocess
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path

COOLDOWN_SEC = 90  # info: set COOLDOWN_SEC
STAMP = Path(os.environ.get("RR_BLE_RECOVER_STAMP", "/tmp/ecoflow-adapter-recover"))  # info: set STAMP
LOCK = Path("/tmp/ecoflow-ble.lock")  # info: set LOCK
AUTH_SKIP = ("NeedBindInstallFirst", "NeedBind")  # info: set AUTH_SKIP


# ====================================================
# SECTION: function _run
# What it does: Run one argv list. Return (code, combined text).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _run(argv: list[str], timeout: float = 20) -> tuple[int, str]:  # info: def _run
    try:  # info: try
        ran = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)  # info: set ran
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except
        return 1, str(exc)  # info: return
    return ran.returncode, ((ran.stdout or "") + (ran.stderr or "")).strip()  # info: return


# ====================================================
# SECTION: function drop_stale_lock
# What it does: Remove /tmp/ecoflow-ble.lock only when flock would succeed (no live holder).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def drop_stale_lock() -> str:  # info: def drop_stale_lock
    if not LOCK.is_file():  # info: if not LOCK . is_file ( ) :
        return "no_lock"  # info: return
    code, _ = _run(["flock", "-n", str(LOCK), "true"], timeout=5)  # info: set code
    if code != 0:  # info: live holder
        return "held"  # info: return
    try:  # info: try
        LOCK.unlink()  # info: LOCK . unlink ( )
        return "dropped"  # info: return
    except OSError:  # info: except OSError
        return "drop_fail"  # info: return


# ====================================================
# SECTION: function ensure_adapter_on
# What it does: rfkill unblock bluetooth, then bluetoothctl power on (retry if Busy).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_adapter_on() -> dict:  # info: def ensure_adapter_on
    t0 = time.perf_counter()  # info: set t0
    code, detail = _run(["rfkill", "unblock", "bluetooth"])  # info: set code
    if code != 0:  # info: if code != 0 :
        elapsed = time.perf_counter() - t0  # info: set elapsed
        print(f"adapter_on FAIL unblock  {elapsed:.3f}s", flush=True)  # info: call print
        return {"ok": False, "tries": 0, "elapsed_s": elapsed, "detail": detail or "rfkill unblock failed", "step": "unblock"}  # info: return
    ran_code = 1  # info: set ran_code
    tries = 0  # info: set tries
    last = ""  # info: set last
    for tries in range(1, 5):  # info: for tries in range ( 1 , 5 ) :
        ran_code, last = _run(["bluetoothctl", "power", "on"])  # info: set ran_code
        if ran_code == 0:  # info: if ran_code == 0 :
            break  # info: break
        time.sleep(0.75)  # info: time . sleep ( 0.75 )
    elapsed = time.perf_counter() - t0  # info: set elapsed
    ok = ran_code == 0  # info: set ok
    if elapsed >= 0.05 or tries > 1 or not ok:  # info: if slow or fail
        print(f"adapter_on {'OK' if ok else 'FAIL'}  tries={tries}  {elapsed:.3f}s", flush=True)  # info: call print
    return {"ok": ok, "tries": tries, "elapsed_s": elapsed, "detail": last, "step": "power_on"}  # info: return


# ====================================================
# SECTION: function cycle_adapter
# What it does: Power off, pause, power on. Measured. No bluetoothd restart.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cycle_adapter() -> dict:  # info: def cycle_adapter
    t0 = time.perf_counter()  # info: set t0
    _run(["bluetoothctl", "power", "off"])  # info: power off
    time.sleep(2.0)  # info: time . sleep ( 2.0 )
    on = ensure_adapter_on()  # info: set on
    elapsed = time.perf_counter() - t0  # info: set elapsed
    print(f"adapter_cycle {'OK' if on.get('ok') else 'FAIL'}  {elapsed:.3f}s", flush=True)  # info: call print
    return {"ok": bool(on.get("ok")), "elapsed_s": elapsed, "step": "cycle", "detail": on.get("detail") or ""}  # info: return


# ====================================================
# SECTION: function reset_hci
# What it does: One hciconfig reset when the binary exists. No sudo, no reboot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def reset_hci() -> dict:  # info: def reset_hci
    t0 = time.perf_counter()  # info: set t0
    which, _ = _run(["which", "hciconfig"], timeout=5)  # info: set which
    if which != 0:  # info: if which != 0 :
        elapsed = time.perf_counter() - t0  # info: set elapsed
        return {"ok": False, "elapsed_s": elapsed, "step": "hci_reset", "detail": "hciconfig_absent"}  # info: return
    code, detail = _run(["hciconfig", "hci0", "reset"], timeout=15)  # info: set code
    time.sleep(1.0)  # info: time . sleep ( 1.0 )
    on = ensure_adapter_on()  # info: set on
    elapsed = time.perf_counter() - t0  # info: set elapsed
    ok = code == 0 and bool(on.get("ok"))  # info: set ok
    print(f"adapter_hci_reset {'OK' if ok else 'FAIL'}  {elapsed:.3f}s  {detail or on.get('detail') or ''}", flush=True)  # info: call print
    return {"ok": ok, "elapsed_s": elapsed, "step": "hci_reset", "detail": detail or on.get("detail") or ""}  # info: return


# ====================================================
# SECTION: function recover_adapter
# What it does: One recovery ladder per cooldown: stale lock, cycle, optional hci reset.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def recover_adapter(reason: str) -> dict:  # info: def recover_adapter
    if any(bit in (reason or "") for bit in AUTH_SKIP):  # info: if auth
        return {"ok": False, "skipped": True, "step": "auth", "detail": reason, "elapsed_s": 0.0}  # info: return
    now = time.time()  # info: set now
    try:  # info: try
        last = float(STAMP.read_text(encoding="utf-8").strip() or "0")  # info: set last
    except (OSError, ValueError):  # info: except
        last = 0.0  # info: set last
    if last and (now - last) < COOLDOWN_SEC:  # info: if cooldown
        return {"ok": False, "skipped": True, "step": "cooldown", "detail": reason, "elapsed_s": 0.0}  # info: return
    t0 = time.perf_counter()  # info: set t0
    lock = drop_stale_lock()  # info: set lock
    cyc = cycle_adapter()  # info: set cyc
    hci = {"ok": True, "detail": "skipped"}  # info: set hci
    if not cyc.get("ok"):  # info: if cycle failed
        hci = reset_hci()  # info: set hci
    try:  # info: try
        STAMP.write_text(str(now), encoding="utf-8")  # info: STAMP . write_text
    except OSError:  # info: except OSError
        pass  # info: pass
    elapsed = time.perf_counter() - t0  # info: set elapsed
    ok = bool(cyc.get("ok") or hci.get("ok"))  # info: set ok
    print(f"adapter_recover {'OK' if ok else 'FAIL'}  reason={reason}  lock={lock}  {elapsed:.3f}s", flush=True)  # info: call print
    return {"ok": ok, "skipped": False, "step": "recover", "detail": reason, "elapsed_s": elapsed, "lock": lock}  # info: return
