# ==============================================================================
# FILE: Energy/lib/ble_client.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Thin BLE connect helper. Honest when eflib/bleak missing."""  # info: """Thin BLE connect helper. Honest when eflib/bleak missing."""
from __future__ import annotations  # info: from __future__ import annotations
import asyncio  # info: import asyncio
import json  # info: import json
import time  # info: import time
import os  # info: import os
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
if str(HERE) not in sys.path:  # info: if str ( HERE ) not in sys
    sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,

from paths import VENDOR, STATE_DIR, ensure_dirs  # noqa: E402
from config import device as device_cfg  # noqa: E402
from envload import user_id, load_env  # noqa: E402
from adapter_on import ensure_adapter_on, recover_adapter  # noqa: E402

MFG_KEY = 0xB5B5  # info: set MFG_KEY

# Optional env overrides for known aliases (legacy). Prefer devices.conf mac=.
_MAC_ENV_BY_ALIAS = {  # info: set _MAC_ENV_BY_ALIAS
    "delta2": "AVA_ECOFLOW_BLE_MAC",  # info: "delta2" : "AVA_ECOFLOW_BLE_MAC" ,
    "river2pro": "AVA_ECOFLOW_RIVER_BLE_MAC",  # info: "river2pro" : "AVA_ECOFLOW_RIVER_BLE_MAC" ,
}  # info: }


# ====================================================
# SECTION: class BleUnavailable
# What it does: BleUnavailable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class BleUnavailable(RuntimeError):  # info: class BleUnavailable
    pass  # info: pass


# ====================================================
# SECTION: function _prep_path
# What it does:  prep path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _prep_path() -> None:  # info: def _prep_path
    ensure_dirs()  # info: call ensure_dirs
    extra = os.environ.get("ENERGY_EFLIB_PATH", "").strip()  # info: set extra
    if extra:  # info: if extra :
        sys.path.insert(0, extra)  # info: sys . path . insert ( 0 ,
    if VENDOR.is_dir():  # info: if VENDOR . is_dir ( ) :
        sys.path.insert(0, str(VENDOR))  # info: sys . path . insert ( 0 ,


# ====================================================
# SECTION: function eflib_ready
# What it does: eflib ready.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def eflib_ready() -> tuple[bool, str]:  # info: def eflib_ready
    _prep_path()  # info: call _prep_path
    try:  # info: try :
        import bleak  # noqa: F401
    except Exception as e:  # info: except Exception as e :
        return False, f"bleak missing: {e}"  # info: return False , f" bleak missing: { e }
    try:  # info: try :
        import eflib  # noqa: F401
    except Exception as e:  # info: except Exception as e :
        return False, f"eflib missing: {e} (set ENERGY_EFLIB_PATH or drop vendor under lib/vendor)"  # info: return False , f" eflib missing: { e }
    return True, "ok"  # info: return True , "ok"


# ====================================================
# SECTION: function _scan
# What it does: Return as soon as the MAC is advertised. Waiting out the full window makes the connect use a stale advertisement.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================

def note_sight(alias: str, seen: bool, detail: str) -> None:  # info: def note_sight
    """Record that this MAC was or was not on the air. No credentials."""  # info: docstring
    ensure_dirs()  # info: call ensure_dirs
    path = STATE_DIR / f"ble-sight-{alias}.json"  # info: set path
    path.write_text(json.dumps({  # info: path.write_text
        "alias": alias,  # info: alias
        "seen": bool(seen),  # info: seen
        "detail": (detail or "")[:160],  # info: detail
        "at_epoch": time.time(),  # info: at_epoch
    }), encoding="utf-8")  # info: encoding


async def _scan(mac: str, seconds: float = 10.0):  # info: async def
    ensure_adapter_on()  # info: call ensure_adapter_on
    from bleak import BleakScanner  # info: from bleak import BleakScanner
    want = mac.upper()  # info: set want
    found = {}  # info: set found

    def _cb(d, adv):  # info: def _cb
        if (d.address or "").upper() == want and "rec" not in found:  # info: first sight of this MAC
            found["rec"] = (d, adv)  # info: found [ "rec" ] = ( d ,

    async with BleakScanner(detection_callback=_cb):  # info: async with
        deadline = asyncio.get_running_loop().time() + seconds  # info: set deadline
        while "rec" not in found:  # info: while the MAC has not been seen
            remaining = deadline - asyncio.get_running_loop().time()  # info: set remaining
            if remaining <= 0:  # info: if the window is over
                break  # info: break
            await asyncio.sleep(min(0.2, remaining))  # info: short poll so connect is not delayed
    return found.get("rec")  # info: return found . get ( "rec" )


# ====================================================
# SECTION: function _resolve_mac
# What it does: Env override if present, else devices.conf mac=. Never invent a MAC.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _resolve_mac(alias: str, cfg: dict) -> str:  # info: def _resolve_mac
    """Env override if present, else devices.conf mac=. Never invent a MAC."""  # info: """Env override if present, else devices.conf mac=. Never invent a MAC."""
    env_key = _MAC_ENV_BY_ALIAS.get(alias, "")  # info: set env_key
    if env_key:  # info: if env_key :
        from_env = (os.environ.get(env_key, "") or "").strip()  # info: set from_env
        if from_env:  # info: if from_env :
            return from_env  # info: return from_env
    return (cfg.get("mac", "") or "").strip()  # info: return ( cfg . get ( "mac" ,


# ====================================================
# SECTION: function connect
# What it does: Connect Device for alias. Raises BleUnavailable on missing deps/device.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
async def connect(alias: str):  # info: async def
    """Connect Device for alias. Raises BleUnavailable on missing deps/device."""  # info: """Connect Device for alias. Raises BleUnavailable on missing deps/device."""
    ok, reason = eflib_ready()  # info: ok , reason = eflib_ready ( )
    if not ok:  # info: if not ok :
        raise BleUnavailable(reason)  # info: raise BleUnavailable ( reason )
    load_env()  # info: call load_env
    uid = user_id()  # info: set uid
    if not uid:  # info: if not uid :
        raise BleUnavailable("AVA_ECOFLOW_USER_ID not set (env file missing or empty)")  # info: raise BleUnavailable ( "AVA_ECOFLOW_USER_ID not set (env file missing or empty)" )
    cfg = device_cfg(alias)  # info: set cfg
    mac = _resolve_mac(alias, cfg)  # info: set mac
    if not mac:  # info: if not mac :
        raise BleUnavailable(  # info: raise BleUnavailable (
            f"no MAC for {alias} (set mac= in devices.conf or env override; do not invent)"  # info: f" no MAC for { alias } (set mac= in devices.conf or env override; do not invent) "
        )  # info: )
    sn = cfg.get("sn", "")  # info: set sn
    mod = cfg.get("eflib_module", "")  # info: set mod
    if not mod:  # info: if not mod :
        raise BleUnavailable(f"no eflib_module for {alias}")  # info: raise BleUnavailable ( f" no eflib_module for { alias }
    import importlib  # info: import importlib
    Device = importlib.import_module(mod).Device  # info: set Device
    rec = await _scan(mac, 8.0)  # info: set rec
    if not rec:  # info: if not rec :
        rec = await _scan(mac, 8.0)  # info: one retry so a busy radio is not treated as gone
    if not rec:  # info: if not rec :
        recover_adapter("scan_miss")  # info: call recover_adapter
        rec = await _scan(mac, 8.0)  # info: set rec
        if not rec:  # info: if not rec :
            rec = await _scan(mac, 8.0)  # info: one more scan after recover
    if not rec:  # info: if not rec :
        note_sight(alias, False, "not_seen")  # info: pack not on the air
        raise BleUnavailable(f"device not seen in scan mac={mac}")  # info: raise BleUnavailable ( f" device not seen in scan mac= { mac }
    note_sight(alias, True, "seen")  # info: advertisement seen; session may still fail auth
    last_err = None  # info: set last_err
    for attempt in range(2):  # info: two connect tries; first sighting is often a stale advertisement
        ble, adv = rec  # info: ble , adv = rec
        device = Device(ble, adv, sn)  # info: set device
        try:  # info: try
            await device.connect(user_id=uid, max_attempts=3)  # info: await device . connect ( user_id = uid
            return device  # info: return device
        except Exception as exc:  # info: except Exception as exc
            last_err = exc  # info: set last_err
            try:  # info: try
                await device.disconnect()  # info: await device . disconnect ( )
            except Exception:  # info: except Exception
                pass  # info: pass
            kind = type(exc).__name__  # info: set kind
            if attempt == 0:  # info: if attempt == 0 :
                if "NeedBind" not in kind:  # info: auth reject is not a radio wedge
                    recover_adapter(f"connect_{kind}")  # info: call recover_adapter
                await asyncio.sleep(0.8)  # info: brief gap before a fresh scan
                rec = await _scan(mac, 8.0)  # info: set rec
                if not rec:  # info: if not rec :
                    note_sight(alias, False, "not_seen_retry")  # info: pack vanished on retry
                    break  # info: break
                note_sight(alias, True, "seen_retry")  # info: second sighting
    raise BleUnavailable(f"connect failed after sight mac={mac} err={type(last_err).__name__ if last_err else 'none'}")  # info: raise after retries


BIND_INSTALL = "NeedBindInstallFirst"  # info: set BIND_INSTALL


# ====================================================
# SECTION: function await_session
# What it does: Wait for BLE auth. NeedBindInstallFirst still proceeds for a read or a switch. It is not a re-pair.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
async def await_session(device, timeout: float = 20):  # info: async def await_session
    state, exc = await asyncio.wait_for(device.wait_until_authenticated_or_error(return_exc=True), timeout=timeout)  # info: set state , exc
    kind = type(exc).__name__ if exc is not None else "none"  # info: set kind
    authed = bool(getattr(state, "authenticated", False))  # info: set authed
    # NeedBindInstallFirst is a hard miss — pack will not send PD heartbeats. Do not proceed.
    return state, kind, authed  # info: return state , kind , authed


# ====================================================
# SECTION: function apply_bool
# What it does: apply bool.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
async def apply_bool(alias: str, method: str, want: bool) -> dict:  # info: async def
    device = await connect(alias)  # info: set device
    try:  # info: try :
        # connect() returns before the background auth task finishes (encrypt type 7: _encryption is None
        # until then) so send_packet asserts. Wait for AUTHENTICATED, then let the first heartbeat land.
        state, kind, proceed = await await_session(device, timeout=20)  # info: set state , kind , proceed
        if not proceed:  # info: if not proceed
            raise BleUnavailable(f"auth not completed: {state} exc={kind}")  # info: raise named auth failure
        if getattr(state, "authenticated", False):  # info: if authenticated
            await asyncio.sleep(1.0)  # info: await asyncio . sleep ( 1.0 )
        fn = getattr(device, method, None)  # info: set fn
        if fn is None:  # info: if fn is None :
            raise BleUnavailable(f"{alias} has no method {method}")  # info: raise BleUnavailable ( f" { alias } has no method
        await fn(want)  # info: call await
        await asyncio.sleep(1.5)  # info: await asyncio . sleep ( 1.5 )
        field = method.replace("enable_", "")  # info: set field
        val = getattr(device, field, None)  # info: set val
        if method == "enable_disable_grid_bypass":  # info: if method == "enable_disable_grid_bypass" :
            val = getattr(device, "disable_grid_bypass", None)  # info: set val
        return {  # info: return {
            "alias": alias,  # info: "alias" : alias ,
            "method": method,  # info: "method" : method ,
            "want": want,  # info: "want" : want ,
            "readback": val,  # info: "readback" : val ,
            "auth": kind,  # info: "auth" : kind ,
            "soc": getattr(device, "battery_level", None) or getattr(device, "soc", None),  # info: "soc" : getattr ( device , "battery_level" ,
        }  # info: }
    finally:  # info: finally :
        try:  # info: try :
            await device.disconnect()  # info: await device . disconnect ( )
        except Exception:  # info: except Exception :
            pass  # info: pass
