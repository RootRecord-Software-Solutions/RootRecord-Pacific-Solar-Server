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
"""WiZ local UDP driver: discover / status / on / off / dim / temp / restore."""
from __future__ import annotations

import json
import socket
import sys
import time

PORT = 38899
DEFAULT_TIMEOUT = 3.0
BROADCASTS = ("255.255.255.255", "192.168.1.255")
# registration with register:false is the documented read-only discovery probe
REGISTRATION = {"method": "registration",
                "params": {"phoneMac": "AAAAAAAAAAAA", "register": False,
                           "phoneIp": "1.2.3.4", "id": "1"}}
GET_PILOT = {"method": "getPilot", "params": {}}


def _sock(timeout: float) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(timeout)
    return s


def request(ip: str, method: str, params: dict | None = None,
            timeout: float = DEFAULT_TIMEOUT, retries: int = 2) -> dict:
    """Unicast one JSON request; retry (UDP) and return the parsed reply."""
    msg = json.dumps({"method": method, "params": params or {}}).encode()
    last_err = "no reply"
    for _ in range(retries + 1):
        s = _sock(timeout / (retries + 1) if retries else timeout)
        try:
            s.sendto(msg, (ip, PORT))
            while True:
                data, addr = s.recvfrom(4096)
                if addr[0] != ip:
                    continue
                reply = json.loads(data.decode("utf-8", "replace"))
                if "error" in reply:
                    raise RuntimeError(f"{method} error: {reply['error']}")
                return reply
        except socket.timeout:
            last_err = f"timeout waiting for {method} from {ip}"
        finally:
            s.close()
    raise TimeoutError(last_err)


def discover(timeout: float = DEFAULT_TIMEOUT, sweep: str | None = None) -> list[dict]:
    """Broadcast getPilot + registration; collect replies for `timeout` seconds.

    ufw on the desk drops unsolicited replies to a broadcast (no conntrack match), so
    `sweep="192.168.1"` also unicasts getPilot to every host of that /24 (254 tiny UDP
    packets, 4 ms apart; replies are conntrack-matched and pass the firewall).
    """
    found: dict[str, dict] = {}
    s = _sock(0.3)
    try:
        for payload in (GET_PILOT, REGISTRATION):
            for bc in BROADCASTS:
                try:
                    s.sendto(json.dumps(payload).encode(), (bc, PORT))
                except OSError:
                    pass
        if sweep:
            msg = json.dumps(GET_PILOT).encode()
            for host in range(1, 255):
                try:
                    s.sendto(msg, (f"{sweep}.{host}", PORT))
                except OSError:
                    pass
                time.sleep(0.004)
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                data, addr = s.recvfrom(4096)
            except socket.timeout:
                continue
            try:
                reply = json.loads(data.decode("utf-8", "replace"))
            except ValueError:
                continue
            ip = addr[0]
            d = found.setdefault(ip, {"ip": ip})
            res = reply.get("result") or {}
            if reply.get("method") == "getPilot":
                d["pilot"] = res
            if res.get("mac"):
                d["mac"] = res["mac"]
    finally:
        s.close()
    out = []
    for ip in sorted(found, key=lambda x: tuple(int(p) for p in x.split("."))):
        d = found[ip]
        try:
            cfg = request(ip, "getSystemConfig", timeout=2.0).get("result", {})
            d["module"] = cfg.get("moduleName")
            d["fw"] = cfg.get("fwVersion")
            d.setdefault("mac", cfg.get("mac"))
        except Exception as e:  # noqa: BLE001
            d["module_error"] = str(e)
        if "pilot" not in d:
            try:
                d["pilot"] = request(ip, "getPilot", timeout=2.0).get("result", {})
            except Exception as e:  # noqa: BLE001
                d["pilot_error"] = str(e)
        out.append(d)
    return out


def status(ip: str) -> dict:
    return request(ip, "getPilot").get("result", {})


def set_pilot(ip: str, params: dict) -> dict:
    return request(ip, "setPilot", params)


def on(ip: str) -> dict:
    return set_pilot(ip, {"state": True})


def off(ip: str) -> dict:
    return set_pilot(ip, {"state": False})


def dim(ip: str, pct: int) -> dict:
    pct = max(10, min(100, int(pct)))
    return set_pilot(ip, {"state": True, "dimming": pct})


def temp(ip: str, kelvin: int) -> dict:
    kelvin = max(2200, min(6500, int(kelvin)))
    return set_pilot(ip, {"state": True, "temp": kelvin})


def restore_params(saved: dict) -> dict:
    """Build setPilot params that reproduce a saved getPilot result."""
    if not saved.get("state"):
        return {"state": False}
    p: dict = {"state": True}
    if "dimming" in saved:
        p["dimming"] = saved["dimming"]
    scene = saved.get("sceneId") or 0
    if scene:
        p["sceneId"] = scene
        if "speed" in saved:
            p["speed"] = saved["speed"]
    elif saved.get("temp"):
        p["temp"] = saved["temp"]
    elif any(k in saved for k in ("r", "g", "b")):
        for k in ("r", "g", "b", "c", "w"):
            if k in saved:
                p[k] = saved[k]
    elif any(k in saved for k in ("c", "w")):
        for k in ("c", "w"):
            if k in saved:
                p[k] = saved[k]
    return p


def restore(ip: str, saved: dict) -> dict:
    return set_pilot(ip, restore_params(saved))


COMPARE_KEYS = ("state", "dimming", "temp", "sceneId", "r", "g", "b", "c", "w", "speed")


def same_state(a: dict, b: dict) -> bool:
    if not a.get("state") and not b.get("state"):
        return True
    return all(a.get(k) == b.get(k) for k in COMPARE_KEYS)


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print(open(__file__).read().split('"""')[0].split("# CLI:")[1].split("# ====")[0])
        return 0
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "discover":
            t = float(rest[rest.index("--timeout") + 1]) if "--timeout" in rest else DEFAULT_TIMEOUT
            sw = rest[rest.index("--sweep") + 1] if "--sweep" in rest else None
            res = discover(t, sw)
        elif cmd == "status":
            res = status(rest[0])
        elif cmd == "on":
            res = on(rest[0])
        elif cmd == "off":
            res = off(rest[0])
        elif cmd == "dim":
            res = dim(rest[0], int(rest[1]))
        elif cmd == "temp":
            res = temp(rest[0], int(rest[1]))
        elif cmd == "restore":
            res = restore(rest[0], json.loads(rest[1]))
        else:
            print(json.dumps({"ok": False, "error": f"unknown command {cmd}"}))
            return 1
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
