#!/usr/bin/env python3
# ==============================================================================
# smart_devices_collect.py — Energy/Smart-Devices status collector (read-only)
# ------------------------------------------------------------------------------
# 2026-09-29. Reads WiZ bulbs (UDP 38899, stdlib) + Tuya BSD01 plugs (tinytuya, venv)
# and writes Database Energy/Smart-Devices/*-last.json:
#   wiz_current.json        every known/discovered bulb: ip, mac, module, state, dimming, temp
#   plugs_current.json      every configured plug: ip, version, on/off or BLOCKED (never keys)
#   collector_current.json  summary (ok, at, counts, per-source ms/errors)
# NEVER switches anything. Wi-Fi only — does not touch BLE (ble-owner.py owns hci0).
#
# Usage:
#   nice -n 10 python3 smart_devices_collect.py [--discover] [--dry-run]
#     --discover  also broadcast + /24 unicast sweep for WiZ bulbs (manual runs)
# Poller: jobs.py EVERY_SECONDS id=smart_devices_collect, OFF unless RR_SMART_DEVICES=1
#         is in the poller's environment at poller start.
# ==============================================================================
"""Energy smart-device status collector -> Database Energy/Smart-Devices/*-last.json."""  # info: """Energy smart-device status collector -> Database Energy/Smart-Devices/*-last.json."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent  # info: set HERE
ROOT = HERE.parent  # info: set ROOT
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
import wiz  # noqa: E402
import tuya  # noqa: E402  (stdlib at import; tinytuya only inside venv calls)

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DATABASE_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE_ROOT
OUT = Path(os.environ.get("RR_SMART_DEVICES_OUT", str(DATABASE_ROOT / "Energy" / "Smart-Devices")))  # info: set OUT
WIZ_CONFIG = ROOT / "config" / "wiz-devices.json"  # info: set WIZ_CONFIG
VENV_PY = ROOT / ".venv" / "bin" / "python"  # info: set VENV_PY


# ====================================================
# SECTION: function now
# What it does: now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> str:  # info: def now
    return datetime.now(HST).isoformat(timespec="seconds")  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function write_json
# What it does: write json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_json(path: Path, obj: dict, dry: bool) -> None:  # info: def write_json
    if dry:  # info: if dry :
        print(f"--- {path.name}\n{json.dumps(obj, indent=2)}")  # info: call print
        return  # info: return
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_name(path.name + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function collect_wiz
# What it does: collect wiz.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def collect_wiz(discover: bool) -> dict:  # info: def collect_wiz
    t0 = time.monotonic()  # info: set t0
    cfg = json.loads(WIZ_CONFIG.read_text(encoding="utf-8")) if WIZ_CONFIG.is_file() else {}  # info: set cfg
    known = cfg.get("bulbs", {})  # info: set known
    bulbs: dict[str, dict] = {}  # info: set bulbs
    errors = []  # info: set errors
    if discover:  # info: if discover :
        try:  # info: try :
            for d in wiz.discover(3.0, cfg.get("sweep_subnet")):  # info: for d in wiz . discover ( 3.0
                key = d.get("mac") or d["ip"]  # info: set key
                bulbs[key] = {"name": key, "ip": d["ip"], "mac": d.get("mac"),  # info: bulbs [ key ] = { "name" :
                              "module": d.get("module"), "fw": d.get("fw"),  # info: "module" : d . get ( "module" )
                              "pilot": d.get("pilot"), "source": "discover"}  # info: "pilot" : d . get ( "pilot" )
        except Exception as e:  # noqa: BLE001
            errors.append(f"discover: {e}")  # info: errors . append ( f" discover: { e
    for name, k in known.items():  # info: for name , k in known . items
        ip = k.get("ip")  # info: set ip
        if not ip:  # info: if not ip :
            continue  # info: continue
        entry = bulbs.setdefault(k.get("mac") or ip, {"name": name, "ip": ip, "mac": k.get("mac"),  # info: set entry
                                                     "module": k.get("module"), "source": "config"})  # info: "module" : k . get ( "module" )
        entry["name"] = name  # info: entry [ "name" ] = name
        if entry.get("pilot"):  # info: if entry . get ( "pilot" ) :
            continue  # info: continue
        try:  # info: try :
            entry["pilot"] = wiz.status(ip)  # info: entry [ "pilot" ] = wiz . status
        except Exception as e:  # noqa: BLE001
            entry["error"] = str(e)  # info: entry [ "error" ] = str ( e
            errors.append(f"{name}@{ip}: {e}")  # info: errors . append ( f" { name }
    out = []  # info: set out
    for b in bulbs.values():  # info: for b in bulbs . values ( )
        p = b.pop("pilot", None) or {}  # info: set p
        b.update({  # info: b . update ( {
            "reachable": bool(p),  # info: "reachable" : bool ( p ) ,
            "on": p.get("state") if p else None,  # info: "on" : p . get ( "state" )
            "dimming": p.get("dimming"),  # info: "dimming" : p . get ( "dimming" )
            "temp": p.get("temp"),  # info: "temp" : p . get ( "temp" )
            "sceneId": p.get("sceneId"),  # info: "sceneId" : p . get ( "sceneId" )
            "rgb": [p[c] for c in ("r", "g", "b")] if all(c in p for c in ("r", "g", "b")) else None,  # info: "rgb" : [ p [ c ] for
            "rssi": p.get("rssi"),  # info: "rssi" : p . get ( "rssi" )
            "state": "PASS" if p else "FAIL",  # info: "state" : "PASS" if p else "FAIL" ,
        })  # info: } )
        out.append(b)  # info: out . append ( b )
    return {"ok": not errors, "at": now(), "kind": "wiz", "count": len(out),  # info: return { "ok" : not errors , "at"
            "state": "PASS" if out and not errors else ("BLOCKED" if not out else "FAIL"),  # info: "state" : "PASS" if out and not errors
            "note": None if out else "no WiZ bulb answered on UDP 38899 (not on this LAN / powered off / not yet added to config)",  # info: "note" : None if out else "no WiZ bulb answered on UDP 38899 (not on this LAN / powered off / not yet added to
            "devices": out, "errors": errors, "ms": int((time.monotonic() - t0) * 1000)}  # info: "devices" : out , "errors" : errors ,


# ====================================================
# SECTION: function collect_plugs
# What it does: collect plugs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def collect_plugs() -> dict:  # info: def collect_plugs
    t0 = time.monotonic()  # info: set t0
    chk = tuya.config_check()  # info: set chk
    devices, errors = [], []  # info: devices , errors = [ ] , [
    for name, c in chk["plugs"].items():  # info: for name , c in chk [ "plugs"
        d = {"name": name, "ip": c.get("ip"), "version": c.get("version"), "on": None}  # info: set d
        if not c["ready"]:  # info: if not c [ "ready" ] :
            d.update({"state": "BLOCKED", "missing": c["missing"]})  # info: d . update ( { "state" : "BLOCKED"
        elif not VENV_PY.is_file():  # info: elif not VENV_PY . is_file ( ) :
            d.update({"state": "BLOCKED", "error": "venv missing (Energy/Smart-Devices/.venv)"})  # info: d . update ( { "state" : "BLOCKED"
        else:  # info: else :
            try:  # info: try :
                r = subprocess.run([str(VENV_PY), str(HERE / "tuya.py"), "status", name],  # info: set r
                                   capture_output=True, text=True, timeout=10)  # info: set capture_output
                res = json.loads(r.stdout or "{}")  # info: set res
                d.update({"on": res.get("on"), "dps": res.get("dps"),  # info: d . update ( { "on" : res
                          "state": "PASS" if res.get("ok") else "FAIL",  # info: "state" : "PASS" if res . get (
                          "error": None if res.get("ok") else res.get("error")})  # info: "error" : None if res . get (
            except Exception as e:  # noqa: BLE001
                d.update({"state": "FAIL", "error": str(e)})  # info: d . update ( { "state" : "FAIL"
        if d.get("error"):  # info: if d . get ( "error" ) :
            errors.append(f"{name}: {d['error']}")  # info: errors . append ( f" { name }
        devices.append(d)  # info: devices . append ( d )
    blocked_note = None  # info: set blocked_note
    if not devices:  # info: if not devices :
        blocked_note = ("BLOCKED: no local_key yet. Pair BSD01 in Smart Life + link Tuya IoT cloud "  # info: set blocked_note
                        "(tinytuya wizard) -> config/tuya-devices.local.json, or flash Tasmota/ESPHome.")  # info: "(tinytuya wizard) -> config/tuya-devices.local.json, or flash Tasmota/ESPHome." )
    return {"ok": not errors, "at": now(), "kind": "tuya-bsd01", "count": len(devices),  # info: return { "ok" : not errors , "at"
            "state": "BLOCKED" if not devices or all(x["state"] == "BLOCKED" for x in devices)  # info: "state" : "BLOCKED" if not devices or all
            else ("PASS" if not errors else "FAIL"),  # info: else ( "PASS" if not errors else "FAIL"
            "note": blocked_note, "devices": devices, "errors": errors,  # info: "note" : blocked_note , "devices" : devices ,
            "ms": int((time.monotonic() - t0) * 1000)}  # info: "ms" : int ( ( time . monotonic


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    dry = "--dry-run" in argv  # info: set dry
    w = collect_wiz("--discover" in argv)  # info: set w
    p = collect_plugs()  # info: set p
    write_json(OUT / "wiz_current.json", w, dry)  # info: call write_json
    write_json(OUT / "plugs_current.json", p, dry)  # info: call write_json
    summary = {"ok": True, "at": now(), "dry_run": dry,  # info: set summary
               "gate": "RR_SMART_DEVICES", "gate_on": os.environ.get("RR_SMART_DEVICES", "0") == "1",  # info: "gate" : "RR_SMART_DEVICES" , "gate_on" : os .
               "sources": {k: {"state": v["state"], "count": v["count"], "ms": v["ms"],  # info: "sources" : { k : { "state" :
                               "errors": v["errors"][:5]} for k, v in (("wiz", w), ("plugs", p))},  # info: "errors" : v [ "errors" ] [ :
               "files": ["wiz_current.json", "plugs_current.json"]}  # info: "files" : [ "wiz_current.json" , "plugs_current.json" ] }
    write_json(OUT / "collector_current.json", summary, dry)  # info: call write_json
    print(json.dumps({"ok": True, "wiz": w["state"], "wiz_count": w["count"],  # info: call print
                      "plugs": p["state"], "plugs_count": p["count"], "out": str(OUT)}))  # info: "plugs" : p [ "state" ] , "plugs_count"
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv[1:]))  # info: raise SystemExit ( main ( sys . argv
