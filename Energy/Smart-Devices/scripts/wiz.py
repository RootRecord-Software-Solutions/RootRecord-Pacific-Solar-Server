#!/usr/bin/env python3
# ==============================================================================
# wiz.py — WiZ smart bulb local driver (stdlib only, UDP 38899 JSON API)
# ------------------------------------------------------------------------------
# Energy/Smart-Devices (2026-09-29). Local LAN only; no cloud, no account, no keys.
# Wi-Fi device — does NOT touch BLE (ble-owner.py owns the adapter).
#
# CLI:
#   wiz.py discover [--timeout 3] [--sweep 192.168.1]
#                                          broadcast getPilot + registration, JSON list;
#                                          --sweep adds a unicast getPilot to .1-.254 of that /24
#                                          (needed on the desk: ufw drops replies to broadcasts)
#   wiz.py status  <ip>                    getPilot (+ getSystemConfig module/mac)
#   wiz.py on      <ip>
#   wiz.py off     <ip>
#   wiz.py dim     <ip> <10-100>           brightness %
#   wiz.py temp    <ip> <2200-6500>        colour temperature K
#   wiz.py restore <ip> '<getPilot result json>'   put a saved state back exactly
# Every command prints one JSON object/list on stdout. Exit 0 ok, 1 error/no reply.
# ==============================================================================
"""WiZ local UDP driver: discover / status / on / off / dim / temp / restore."""  # info: """WiZ local UDP driver: discover / status / on / off / dim / temp / restore."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import socket  # info: import socket
import sys  # info: import sys
import time  # info: import time

PORT = 38899  # info: set PORT
DEFAULT_TIMEOUT = 3.0  # info: set DEFAULT_TIMEOUT
BROADCASTS = ("255.255.255.255", "192.168.1.255")  # info: set BROADCASTS
# registration with register:false is the documented read-only discovery probe
REGISTRATION = {"method": "registration",  # info: set REGISTRATION
                "params": {"phoneMac": "AAAAAAAAAAAA", "register": False,  # info: "params" : { "phoneMac" : "AAAAAAAAAAAA" , "register"
                           "phoneIp": "1.2.3.4", "id": "1"}}  # info: "phoneIp" : "1.2.3.4" , "id" : "1" }
GET_PILOT = {"method": "getPilot", "params": {}}  # info: set GET_PILOT


# ====================================================
# SECTION: function _sock
# What it does:  sock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _sock(timeout: float) -> socket.socket:  # info: def _sock
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # info: set s
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # info: s . setsockopt ( socket . SOL_SOCKET ,
    s.settimeout(timeout)  # info: s . settimeout ( timeout )
    return s  # info: return s


# ====================================================
# SECTION: function request
# What it does: Unicast one JSON request; retry (UDP) and return the parsed reply.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def request(ip: str, method: str, params: dict | None = None,  # info: def request
            timeout: float = DEFAULT_TIMEOUT, retries: int = 2) -> dict:  # info: set timeout
    """Unicast one JSON request; retry (UDP) and return the parsed reply."""  # info: """Unicast one JSON request; retry (UDP) and return the parsed reply."""
    msg = json.dumps({"method": method, "params": params or {}}).encode()  # info: set msg
    last_err = "no reply"  # info: set last_err
    for _ in range(retries + 1):  # info: for _ in range ( retries + 1
        s = _sock(timeout / (retries + 1) if retries else timeout)  # info: set s
        try:  # info: try :
            s.sendto(msg, (ip, PORT))  # info: s . sendto ( msg , ( ip
            while True:  # info: while True :
                data, addr = s.recvfrom(4096)  # info: data , addr = s . recvfrom (
                if addr[0] != ip:  # info: if addr [ 0 ] != ip :
                    continue  # info: continue
                reply = json.loads(data.decode("utf-8", "replace"))  # info: set reply
                if "error" in reply:  # info: if "error" in reply :
                    raise RuntimeError(f"{method} error: {reply['error']}")  # info: raise RuntimeError ( f" { method } error:
                return reply  # info: return reply
        except socket.timeout:  # info: except socket . timeout :
            last_err = f"timeout waiting for {method} from {ip}"  # info: set last_err
        finally:  # info: finally :
            s.close()  # info: s . close ( )
    raise TimeoutError(last_err)  # info: raise TimeoutError ( last_err )


# ====================================================
# SECTION: function discover
# What it does: Broadcast getPilot + registration; collect replies for `timeout` seconds. ufw on the desk drops unsolicited replies to a broadcast (no conntrack match), so `sweep="192.168.1"` also
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def discover(timeout: float = DEFAULT_TIMEOUT, sweep: str | None = None) -> list[dict]:  # info: def discover
    """Broadcast getPilot + registration; collect replies for `timeout` seconds.

    ufw on the desk drops unsolicited replies to a broadcast (no conntrack match), so
    `sweep="192.168.1"` also unicasts getPilot to every host of that /24 (254 tiny UDP
    packets, 4 ms apart; replies are conntrack-matched and pass the firewall).
    """
    found: dict[str, dict] = {}  # info: set found
    s = _sock(0.3)  # info: set s
    try:  # info: try :
        for payload in (GET_PILOT, REGISTRATION):  # info: for payload in ( GET_PILOT , REGISTRATION )
            for bc in BROADCASTS:  # info: for bc in BROADCASTS :
                try:  # info: try :
                    s.sendto(json.dumps(payload).encode(), (bc, PORT))  # info: s . sendto ( json . dumps (
                except OSError:  # info: except OSError :
                    pass  # info: pass
        if sweep:  # info: if sweep :
            msg = json.dumps(GET_PILOT).encode()  # info: set msg
            for host in range(1, 255):  # info: for host in range ( 1 , 255
                try:  # info: try :
                    s.sendto(msg, (f"{sweep}.{host}", PORT))  # info: s . sendto ( msg , ( f"
                except OSError:  # info: except OSError :
                    pass  # info: pass
                time.sleep(0.004)  # info: time . sleep ( 0.004 )
        end = time.monotonic() + timeout  # info: set end
        while time.monotonic() < end:  # info: while time . monotonic ( ) < end
            try:  # info: try :
                data, addr = s.recvfrom(4096)  # info: data , addr = s . recvfrom (
            except socket.timeout:  # info: except socket . timeout :
                continue  # info: continue
            try:  # info: try :
                reply = json.loads(data.decode("utf-8", "replace"))  # info: set reply
            except ValueError:  # info: except ValueError :
                continue  # info: continue
            ip = addr[0]  # info: set ip
            d = found.setdefault(ip, {"ip": ip})  # info: set d
            res = reply.get("result") or {}  # info: set res
            if reply.get("method") == "getPilot":  # info: if reply . get ( "method" ) ==
                d["pilot"] = res  # info: d [ "pilot" ] = res
            if res.get("mac"):  # info: if res . get ( "mac" ) :
                d["mac"] = res["mac"]  # info: d [ "mac" ] = res [ "mac"
    finally:  # info: finally :
        s.close()  # info: s . close ( )
    out = []  # info: set out
    for ip in sorted(found, key=lambda x: tuple(int(p) for p in x.split("."))):  # info: for ip in sorted ( found , key
        d = found[ip]  # info: set d
        try:  # info: try :
            cfg = request(ip, "getSystemConfig", timeout=2.0).get("result", {})  # info: set cfg
            d["module"] = cfg.get("moduleName")  # info: d [ "module" ] = cfg . get
            d["fw"] = cfg.get("fwVersion")  # info: d [ "fw" ] = cfg . get
            d.setdefault("mac", cfg.get("mac"))  # info: d . setdefault ( "mac" , cfg .
        except Exception as e:  # noqa: BLE001
            d["module_error"] = str(e)  # info: d [ "module_error" ] = str ( e
        if "pilot" not in d:  # info: if "pilot" not in d :
            try:  # info: try :
                d["pilot"] = request(ip, "getPilot", timeout=2.0).get("result", {})  # info: d [ "pilot" ] = request ( ip
            except Exception as e:  # noqa: BLE001
                d["pilot_error"] = str(e)  # info: d [ "pilot_error" ] = str ( e
        out.append(d)  # info: out . append ( d )
    return out  # info: return out


# ====================================================
# SECTION: function status
# What it does: status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def status(ip: str) -> dict:  # info: def status
    return request(ip, "getPilot").get("result", {})  # info: return request ( ip , "getPilot" ) .


# ====================================================
# SECTION: function set_pilot
# What it does: set pilot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_pilot(ip: str, params: dict) -> dict:  # info: def set_pilot
    return request(ip, "setPilot", params)  # info: return request ( ip , "setPilot" , params


# ====================================================
# SECTION: function on
# What it does: on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def on(ip: str) -> dict:  # info: def on
    return set_pilot(ip, {"state": True})  # info: return set_pilot ( ip , { "state" :


# ====================================================
# SECTION: function off
# What it does: off.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def off(ip: str) -> dict:  # info: def off
    return set_pilot(ip, {"state": False})  # info: return set_pilot ( ip , { "state" :


# ====================================================
# SECTION: function dim
# What it does: dim.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def dim(ip: str, pct: int) -> dict:  # info: def dim
    pct = max(10, min(100, int(pct)))  # info: set pct
    return set_pilot(ip, {"state": True, "dimming": pct})  # info: return set_pilot ( ip , { "state" :


# ====================================================
# SECTION: function temp
# What it does: temp.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def temp(ip: str, kelvin: int) -> dict:  # info: def temp
    kelvin = max(2200, min(6500, int(kelvin)))  # info: set kelvin
    return set_pilot(ip, {"state": True, "temp": kelvin})  # info: return set_pilot ( ip , { "state" :


# ====================================================
# SECTION: function restore_params
# What it does: Build setPilot params that reproduce a saved getPilot result.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def restore_params(saved: dict) -> dict:  # info: def restore_params
    """Build setPilot params that reproduce a saved getPilot result."""  # info: """Build setPilot params that reproduce a saved getPilot result."""
    if not saved.get("state"):  # info: if not saved . get ( "state" )
        return {"state": False}  # info: return { "state" : False }
    p: dict = {"state": True}  # info: set p
    if "dimming" in saved:  # info: if "dimming" in saved :
        p["dimming"] = saved["dimming"]  # info: p [ "dimming" ] = saved [ "dimming"
    scene = saved.get("sceneId") or 0  # info: set scene
    if scene:  # info: if scene :
        p["sceneId"] = scene  # info: p [ "sceneId" ] = scene
        if "speed" in saved:  # info: if "speed" in saved :
            p["speed"] = saved["speed"]  # info: p [ "speed" ] = saved [ "speed"
    elif saved.get("temp"):  # info: elif saved . get ( "temp" ) :
        p["temp"] = saved["temp"]  # info: p [ "temp" ] = saved [ "temp"
    elif any(k in saved for k in ("r", "g", "b")):  # info: elif any ( k in saved for k
        for k in ("r", "g", "b", "c", "w"):  # info: for k in ( "r" , "g" ,
            if k in saved:  # info: if k in saved :
                p[k] = saved[k]  # info: p [ k ] = saved [ k
    elif any(k in saved for k in ("c", "w")):  # info: elif any ( k in saved for k
        for k in ("c", "w"):  # info: for k in ( "c" , "w" )
            if k in saved:  # info: if k in saved :
                p[k] = saved[k]  # info: p [ k ] = saved [ k
    return p  # info: return p


# ====================================================
# SECTION: function restore
# What it does: restore.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def restore(ip: str, saved: dict) -> dict:  # info: def restore
    return set_pilot(ip, restore_params(saved))  # info: return set_pilot ( ip , restore_params ( saved


COMPARE_KEYS = ("state", "dimming", "temp", "sceneId", "r", "g", "b", "c", "w", "speed")  # info: set COMPARE_KEYS


# ====================================================
# SECTION: function same_state
# What it does: same state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def same_state(a: dict, b: dict) -> bool:  # info: def same_state
    if not a.get("state") and not b.get("state"):  # info: if not a . get ( "state" )
        return True  # info: return True
    return all(a.get(k) == b.get(k) for k in COMPARE_KEYS)  # info: return all ( a . get ( k


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    if not argv or argv[0] in ("-h", "--help"):  # info: if not argv or argv [ 0 ]
        print(__doc__)  # info: call print
        print(open(__file__).read().split('"""')[0].split("# CLI:")[1].split("# ====")[0])
        return 0  # info: return 0
    cmd, rest = argv[0], argv[1:]  # info: cmd , rest = argv [ 0 ]
    try:  # info: try :
        if cmd == "discover":  # info: if cmd == "discover" :
            t = float(rest[rest.index("--timeout") + 1]) if "--timeout" in rest else DEFAULT_TIMEOUT  # info: set t
            sw = rest[rest.index("--sweep") + 1] if "--sweep" in rest else None  # info: set sw
            res = discover(t, sw)  # info: set res
        elif cmd == "status":  # info: elif cmd == "status" :
            res = status(rest[0])  # info: set res
        elif cmd == "on":  # info: elif cmd == "on" :
            res = on(rest[0])  # info: set res
        elif cmd == "off":  # info: elif cmd == "off" :
            res = off(rest[0])  # info: set res
        elif cmd == "dim":  # info: elif cmd == "dim" :
            res = dim(rest[0], int(rest[1]))  # info: set res
        elif cmd == "temp":  # info: elif cmd == "temp" :
            res = temp(rest[0], int(rest[1]))  # info: set res
        elif cmd == "restore":  # info: elif cmd == "restore" :
            res = restore(rest[0], json.loads(rest[1]))  # info: set res
        else:  # info: else :
            print(json.dumps({"ok": False, "error": f"unknown command {cmd}"}))  # info: call print
            return 1  # info: return 1
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}))  # info: call print
        return 1  # info: return 1
    print(json.dumps(res, indent=2))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv[1:]))  # info: raise SystemExit ( main ( sys . argv
