#!/usr/bin/env python3
"""Thin BLE connect helper. Honest when eflib/bleak missing."""
from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from paths import VENDOR, ensure_dirs  # noqa: E402
from config import device as device_cfg  # noqa: E402
from envload import user_id, load_env  # noqa: E402

MFG_KEY = 0xB5B5

# Optional env overrides for known aliases (legacy). Prefer devices.conf mac=.
_MAC_ENV_BY_ALIAS = {
    "delta2": "AVA_ECOFLOW_BLE_MAC",
    "river2pro": "AVA_ECOFLOW_RIVER_BLE_MAC",
}


class BleUnavailable(RuntimeError):
    pass


def _prep_path() -> None:
    ensure_dirs()
    extra = os.environ.get("ENERGY_EFLIB_PATH", "").strip()
    if extra:
        sys.path.insert(0, extra)
    if VENDOR.is_dir():
        sys.path.insert(0, str(VENDOR))


def eflib_ready() -> tuple[bool, str]:
    _prep_path()
    try:
        import bleak  # noqa: F401
    except Exception as e:
        return False, f"bleak missing: {e}"
    try:
        import eflib  # noqa: F401
    except Exception as e:
        return False, f"eflib missing: {e} (set ENERGY_EFLIB_PATH or drop vendor under lib/vendor)"
    return True, "ok"


async def _scan(mac: str, seconds: float = 10.0):
    from bleak import BleakScanner
    want = mac.upper()
    found = {}

    def _cb(d, adv):
        if (d.address or "").upper() == want:
            found["rec"] = (d, adv)

    async with BleakScanner(detection_callback=_cb):
        await asyncio.sleep(seconds)
    return found.get("rec")


def _resolve_mac(alias: str, cfg: dict) -> str:
    """Env override if present, else devices.conf mac=. Never invent a MAC."""
    env_key = _MAC_ENV_BY_ALIAS.get(alias, "")
    if env_key:
        from_env = (os.environ.get(env_key, "") or "").strip()
        if from_env:
            return from_env
    return (cfg.get("mac", "") or "").strip()


async def connect(alias: str):
    """Connect Device for alias. Raises BleUnavailable on missing deps/device."""
    ok, reason = eflib_ready()
    if not ok:
        raise BleUnavailable(reason)
    load_env()
    uid = user_id()
    if not uid:
        raise BleUnavailable("AVA_ECOFLOW_USER_ID not set (env file missing or empty)")
    cfg = device_cfg(alias)
    mac = _resolve_mac(alias, cfg)
    if not mac:
        raise BleUnavailable(
            f"no MAC for {alias} (set mac= in devices.conf or env override; do not invent)"
        )
    sn = cfg.get("sn", "")
    mod = cfg.get("eflib_module", "")
    if not mod:
        raise BleUnavailable(f"no eflib_module for {alias}")
    import importlib
    Device = importlib.import_module(mod).Device
    rec = await _scan(mac)
    if not rec:
        raise BleUnavailable(f"device not seen in scan mac={mac}")
    ble, adv = rec
    device = Device(ble, adv, sn)
    await device.connect(user_id=uid, max_attempts=3)
    return device


async def apply_bool(alias: str, method: str, want: bool) -> dict:
    device = await connect(alias)
    try:
        # connect() returns before the background auth task finishes (encrypt type 7: _encryption is None
        # until then) so send_packet asserts. Wait for AUTHENTICATED, then let the first heartbeat land.
        state = await asyncio.wait_for(device.wait_until_authenticated_or_error(), timeout=20)
        if not state.authenticated:
            raise BleUnavailable(f"auth not completed: {state}")
        await asyncio.sleep(1.0)
        fn = getattr(device, method, None)
        if fn is None:
            raise BleUnavailable(f"{alias} has no method {method}")
        await fn(want)
        await asyncio.sleep(1.5)
        field = method.replace("enable_", "")
        val = getattr(device, field, None)
        if method == "enable_disable_grid_bypass":
            val = getattr(device, "disable_grid_bypass", None)
        return {
            "alias": alias,
            "method": method,
            "want": want,
            "readback": val,
            "soc": getattr(device, "battery_level", None) or getattr(device, "soc", None),
        }
    finally:
        try:
            await device.disconnect()
        except Exception:
            pass
