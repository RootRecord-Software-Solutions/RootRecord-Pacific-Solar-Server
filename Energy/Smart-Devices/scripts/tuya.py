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
"""Tuya local driver scaffold: listen (no key) / config-check / status / on / off."""  # info: """Tuya local driver scaffold: listen (no key) / config-check / status / on / off."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import socket  # info: import socket
import sys  # info: import sys
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # info: set ROOT
LOCAL_CONFIG = ROOT / "config" / "tuya-devices.local.json"  # info: set LOCAL_CONFIG
LISTEN_PORTS = (6666, 6667, 7000)  # 3.1 plain / 3.3+ AES(udpkey) / 3.5 app port
REQUIRED = ("id", "ip", "local_key", "version")  # info: set REQUIRED
SAFE_FIELDS = ("gwId", "devId", "id", "ip", "version", "productKey", "active", "encrypt")  # info: set SAFE_FIELDS


# ====================================================
# SECTION: function _decode
# What it does:  decode.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _decode(data: bytes) -> dict | None:  # info: def _decode
    try:  # info: try :
        import tinytuya  # venv only
        raw = tinytuya.decrypt_udp(data)  # info: set raw
        return json.loads(raw) if isinstance(raw, (str, bytes)) else raw  # info: return json . loads ( raw ) if
    except Exception:  # noqa: BLE001
        pass  # info: pass
    # stdlib fallback: 3.1 devices broadcast clear JSON inside the 55AA frame
    try:  # info: try :
        s = data[20:-8].decode("utf-8", "replace")  # info: set s
        return json.loads(s[s.index("{"):s.rindex("}") + 1])  # info: return json . loads ( s [ s
    except Exception:  # noqa: BLE001
        return None  # info: return None


# ====================================================
# SECTION: function listen
# What it does: listen.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def listen(seconds: float = 20.0) -> dict:  # info: def listen
    socks, errors = [], {}  # info: socks , errors = [ ] , {
    for port in LISTEN_PORTS:  # info: for port in LISTEN_PORTS :
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # info: set s
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # info: s . setsockopt ( socket . SOL_SOCKET ,
        try:  # info: try :
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # info: s . setsockopt ( socket . SOL_SOCKET ,
        except (AttributeError, OSError):  # info: except ( AttributeError , OSError ) :
            pass  # info: pass
        try:  # info: try :
            s.bind(("", port))  # info: s . bind ( ( "" , port
            s.setblocking(False)  # info: s . setblocking ( False )
            socks.append((port, s))  # info: socks . append ( ( port , s
        except OSError as e:  # info: except OSError as e :
            errors[port] = str(e)  # info: errors [ port ] = str ( e
            s.close()  # info: s . close ( )
    found: dict[str, dict] = {}  # info: set found
    packets = 0  # info: set packets
    end = time.monotonic() + seconds  # info: set end
    try:  # info: try :
        import select  # info: import select
        while time.monotonic() < end:  # info: while time . monotonic ( ) < end
            r, _, _ = select.select([s for _, s in socks], [], [], 0.5)  # info: r , _ , _ = select .
            for s in r:  # info: for s in r :
                data, addr = s.recvfrom(4096)  # info: data , addr = s . recvfrom (
                packets += 1  # info: set packets
                msg = _decode(data) or {}  # info: set msg
                dev_id = msg.get("gwId") or msg.get("devId") or msg.get("id") or f"unknown@{addr[0]}"  # info: set dev_id
                found[dev_id] = {  # info: found [ dev_id ] = {
                    "id": dev_id,  # info: "id" : dev_id ,
                    "ip": msg.get("ip") or addr[0],  # info: "ip" : msg . get ( "ip" )
                    "version": msg.get("version"),  # info: "version" : msg . get ( "version" )
                    "port": s.getsockname()[1],  # info: "port" : s . getsockname ( ) [
                    "productKey": msg.get("productKey"),  # info: "productKey" : msg . get ( "productKey" )
                }  # info: }
    finally:  # info: finally :
        for _, s in socks:  # info: for _ , s in socks :
            s.close()  # info: s . close ( )
    return {"ok": True, "seconds": seconds, "ports_bound": [p for p, _ in socks],  # info: return { "ok" : True , "seconds" :
            "bind_errors": errors, "packets": packets, "devices": list(found.values())}  # info: "bind_errors" : errors , "packets" : packets ,


# ====================================================
# SECTION: function load_config
# What it does: load config.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_config() -> dict:  # info: def load_config
    if not LOCAL_CONFIG.is_file():  # info: if not LOCAL_CONFIG . is_file ( ) :
        return {}  # info: return { }
    return json.loads(LOCAL_CONFIG.read_text(encoding="utf-8")).get("plugs", {})  # info: return json . loads ( LOCAL_CONFIG . read_text


# ====================================================
# SECTION: function config_check
# What it does: config check.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def config_check() -> dict:  # info: def config_check
    plugs = load_config()  # info: set plugs
    out = {}  # info: set out
    for name, c in plugs.items():  # info: for name , c in plugs . items
        missing = [k for k in REQUIRED if not str(c.get(k, "")).strip()  # info: set missing
                   or str(c.get(k)).startswith("REPLACE")]  # info: call or
        out[name] = {"ready": not missing, "missing": missing,  # info: out [ name ] = { "ready" :
                     "ip": c.get("ip"), "version": c.get("version")}  # info: "ip" : c . get ( "ip" )
    return {"config": str(LOCAL_CONFIG), "exists": LOCAL_CONFIG.is_file(), "plugs": out,  # info: return { "config" : str ( LOCAL_CONFIG )
            "state": "READY" if out and all(v["ready"] for v in out.values()) else "BLOCKED"}  # info: "state" : "READY" if out and all (


# ====================================================
# SECTION: function _device
# What it does:  device.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _device(name: str):  # info: def _device
    c = load_config().get(name)  # info: set c
    if not c:  # info: if not c :
        raise KeyError(f"plug '{name}' not in {LOCAL_CONFIG.name} (BLOCKED: no local_key yet)")  # info: raise KeyError ( f" plug ' { name }
    missing = [k for k in REQUIRED if not str(c.get(k, "")).strip() or str(c.get(k)).startswith("REPLACE")]  # info: set missing
    if missing:  # info: if missing :
        raise KeyError(f"plug '{name}' missing {missing} (BLOCKED)")  # info: raise KeyError ( f" plug ' { name }
    import tinytuya  # venv only
    d = tinytuya.OutletDevice(c["id"], c["ip"], c["local_key"], version=float(c["version"]))  # info: set d
    d.set_socketTimeout(3)  # info: d . set_socketTimeout ( 3 )
    d.set_socketRetryLimit(1)  # info: d . set_socketRetryLimit ( 1 )
    return d, int(c.get("switch_dp", 1))  # info: return d , int ( c . get


# ====================================================
# SECTION: function status
# What it does: status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def status(name: str) -> dict:  # info: def status
    d, dp = _device(name)  # info: d , dp = _device ( name )
    st = d.status()  # info: set st
    if "Error" in st:  # info: if "Error" in st :
        return {"ok": False, "error": st.get("Error"), "code": st.get("Err")}  # info: return { "ok" : False , "error" :
    dps = st.get("dps", {})  # info: set dps
    return {"ok": True, "on": dps.get(str(dp)), "dps": dps}  # info: return { "ok" : True , "on" :


# ====================================================
# SECTION: function switch
# What it does: switch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def switch(name: str, on: bool) -> dict:  # info: def switch
    d, dp = _device(name)  # info: d , dp = _device ( name )
    r = d.set_status(on, dp)  # info: set r
    return {"ok": "Error" not in (r or {}), "requested": on, "reply": {k: v for k, v in (r or {}).items() if k != "local_key"}}  # info: return { "ok" : "Error" not in (


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    if not argv:  # info: if not argv :
        print(__doc__)  # info: call print
        return 0  # info: return 0
    cmd, rest = argv[0], argv[1:]  # info: cmd , rest = argv [ 0 ]
    try:  # info: try :
        if cmd == "listen":  # info: if cmd == "listen" :
            secs = float(rest[rest.index("--seconds") + 1]) if "--seconds" in rest else 20.0  # info: set secs
            res = listen(secs)  # info: set res
        elif cmd == "config-check":  # info: elif cmd == "config-check" :
            res = config_check()  # info: set res
        elif cmd == "status":  # info: elif cmd == "status" :
            res = status(rest[0])  # info: set res
        elif cmd in ("on", "off"):  # info: elif cmd in ( "on" , "off" )
            res = switch(rest[0], cmd == "on")  # info: set res
        else:  # info: else :
            res = {"ok": False, "error": f"unknown command {cmd}"}  # info: set res
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "state": "BLOCKED" if isinstance(e, KeyError) else "FAIL", "error": (e.args[0] if isinstance(e, KeyError) and e.args else str(e))}  # info: set res
    print(json.dumps(res, indent=2))  # info: call print
    return 0 if res.get("ok", True) else 1  # info: return 0 if res . get ( "ok"


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv[1:]))  # info: raise SystemExit ( main ( sys . argv
