#!/usr/bin/env python3
# ==============================================================================
# tuya.py — Tuya / Smart Life plug local driver scaffold (BSD01, ESP8266)
# ------------------------------------------------------------------------------
# Energy/Smart-Devices (2026-09-29). Run with the gitignored venv:
#   "Energy/Smart-Devices/.venv/bin/python" Energy/Smart-Devices/scripts/tuya.py <cmd>
#
# CLI:
#   tuya.py listen [--seconds 20]   passive, no key: Tuya UDP broadcasts on 6666/6667/7000
#                                   -> prints id / ip / version only (never keys)
#   tuya.py config-check            which configured plugs have id/ip/local_key/version (no values)
#   tuya.py status <name>           DPS read (needs local_key)        } BLOCKED until a
#   tuya.py on <name> | off <name>  switch DPS 1 (needs local_key)    } local_key exists
#
# Secrets: config/tuya-devices.local.json (gitignored) holds local_key per plug.
# Template: config/tuya-devices.example.json. local_key is NEVER printed or logged.
# Alternative path (no keys): flash Tasmota/ESPHome -> plain HTTP/MQTT; see Library
#   Documentation/00-architecture/Smart-Devices-Energy.md
# ==============================================================================
"""Tuya local driver scaffold: listen (no key) / config-check / status / on / off."""
from __future__ import annotations

import json
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL_CONFIG = ROOT / "config" / "tuya-devices.local.json"
LISTEN_PORTS = (6666, 6667, 7000)  # 3.1 plain / 3.3+ AES(udpkey) / 3.5 app port
REQUIRED = ("id", "ip", "local_key", "version")
SAFE_FIELDS = ("gwId", "devId", "id", "ip", "version", "productKey", "active", "encrypt")


def _decode(data: bytes) -> dict | None:
    try:
        import tinytuya  # venv only
        raw = tinytuya.decrypt_udp(data)
        return json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    except Exception:  # noqa: BLE001
        pass
    # stdlib fallback: 3.1 devices broadcast clear JSON inside the 55AA frame
    try:
        s = data[20:-8].decode("utf-8", "replace")
        return json.loads(s[s.index("{"):s.rindex("}") + 1])
    except Exception:  # noqa: BLE001
        return None


def listen(seconds: float = 20.0) -> dict:
    socks, errors = [], {}
    for port in LISTEN_PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass
        try:
            s.bind(("", port))
            s.setblocking(False)
            socks.append((port, s))
        except OSError as e:
            errors[port] = str(e)
            s.close()
    found: dict[str, dict] = {}
    packets = 0
    end = time.monotonic() + seconds
    try:
        import select
        while time.monotonic() < end:
            r, _, _ = select.select([s for _, s in socks], [], [], 0.5)
            for s in r:
                data, addr = s.recvfrom(4096)
                packets += 1
                msg = _decode(data) or {}
                dev_id = msg.get("gwId") or msg.get("devId") or msg.get("id") or f"unknown@{addr[0]}"
                found[dev_id] = {
                    "id": dev_id,
                    "ip": msg.get("ip") or addr[0],
                    "version": msg.get("version"),
                    "port": s.getsockname()[1],
                    "productKey": msg.get("productKey"),
                }
    finally:
        for _, s in socks:
            s.close()
    return {"ok": True, "seconds": seconds, "ports_bound": [p for p, _ in socks],
            "bind_errors": errors, "packets": packets, "devices": list(found.values())}


def load_config() -> dict:
    if not LOCAL_CONFIG.is_file():
        return {}
    return json.loads(LOCAL_CONFIG.read_text(encoding="utf-8")).get("plugs", {})


def config_check() -> dict:
    plugs = load_config()
    out = {}
    for name, c in plugs.items():
        missing = [k for k in REQUIRED if not str(c.get(k, "")).strip()
                   or str(c.get(k)).startswith("REPLACE")]
        out[name] = {"ready": not missing, "missing": missing,
                     "ip": c.get("ip"), "version": c.get("version")}
    return {"config": str(LOCAL_CONFIG), "exists": LOCAL_CONFIG.is_file(), "plugs": out,
            "state": "READY" if out and all(v["ready"] for v in out.values()) else "BLOCKED"}


def _device(name: str):
    c = load_config().get(name)
    if not c:
        raise KeyError(f"plug '{name}' not in {LOCAL_CONFIG.name} (BLOCKED: no local_key yet)")
    missing = [k for k in REQUIRED if not str(c.get(k, "")).strip() or str(c.get(k)).startswith("REPLACE")]
    if missing:
        raise KeyError(f"plug '{name}' missing {missing} (BLOCKED)")
    import tinytuya  # venv only
    d = tinytuya.OutletDevice(c["id"], c["ip"], c["local_key"], version=float(c["version"]))
    d.set_socketTimeout(3)
    d.set_socketRetryLimit(1)
    return d, int(c.get("switch_dp", 1))


def status(name: str) -> dict:
    d, dp = _device(name)
    st = d.status()
    if "Error" in st:
        return {"ok": False, "error": st.get("Error"), "code": st.get("Err")}
    dps = st.get("dps", {})
    return {"ok": True, "on": dps.get(str(dp)), "dps": dps}


def switch(name: str, on: bool) -> dict:
    d, dp = _device(name)
    r = d.set_status(on, dp)
    return {"ok": "Error" not in (r or {}), "requested": on, "reply": {k: v for k, v in (r or {}).items() if k != "local_key"}}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "listen":
            secs = float(rest[rest.index("--seconds") + 1]) if "--seconds" in rest else 20.0
            res = listen(secs)
        elif cmd == "config-check":
            res = config_check()
        elif cmd == "status":
            res = status(rest[0])
        elif cmd in ("on", "off"):
            res = switch(rest[0], cmd == "on")
        else:
            res = {"ok": False, "error": f"unknown command {cmd}"}
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "state": "BLOCKED" if isinstance(e, KeyError) else "FAIL", "error": (e.args[0] if isinstance(e, KeyError) and e.args else str(e))}
    print(json.dumps(res, indent=2))
    return 0 if res.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
