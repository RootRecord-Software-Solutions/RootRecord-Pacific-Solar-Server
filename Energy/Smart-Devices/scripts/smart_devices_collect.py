#!/usr/bin/env python3
# ==============================================================================
# smart_devices_collect.py — Energy/Smart-Devices status collector (read-only)
# ------------------------------------------------------------------------------
# 2026-09-29. Reads WiZ bulbs (UDP 38899, stdlib) + Tuya BSD01 plugs (tinytuya, venv)
# and writes Database Energy/Smart-Devices/*-last.json:
#   wiz-last.json        every known/discovered bulb: ip, mac, module, state, dimming, temp
#   plugs-last.json      every configured plug: ip, version, on/off or BLOCKED (never keys)
#   collector-last.json  summary (ok, at, counts, per-source ms/errors)
# NEVER switches anything. Wi-Fi only — does not touch BLE (ble-owner.py owns hci0).
#
# Usage:
#   nice -n 10 python3 smart_devices_collect.py [--discover] [--dry-run]
#     --discover  also broadcast + /24 unicast sweep for WiZ bulbs (manual runs)
# Poller: jobs.py EVERY_SECONDS id=smart_devices_collect, OFF unless RR_SMART_DEVICES=1
#         is in the poller's environment at poller start.
# ==============================================================================
"""Energy smart-device status collector -> Database Energy/Smart-Devices/*-last.json."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import wiz  # noqa: E402
import tuya  # noqa: E402  (stdlib at import; tinytuya only inside venv calls)

HST = ZoneInfo("Pacific/Honolulu")
DATABASE_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
OUT = Path(os.environ.get("RR_SMART_DEVICES_OUT", str(DATABASE_ROOT / "Energy" / "Smart-Devices")))
WIZ_CONFIG = ROOT / "config" / "wiz-devices.json"
VENV_PY = ROOT / ".venv" / "bin" / "python"


def now() -> str:
    return datetime.now(HST).isoformat(timespec="seconds")


def write_json(path: Path, obj: dict, dry: bool) -> None:
    if dry:
        print(f"--- {path.name}\n{json.dumps(obj, indent=2)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def collect_wiz(discover: bool) -> dict:
    t0 = time.monotonic()
    cfg = json.loads(WIZ_CONFIG.read_text(encoding="utf-8")) if WIZ_CONFIG.is_file() else {}
    known = cfg.get("bulbs", {})
    bulbs: dict[str, dict] = {}
    errors = []
    if discover:
        try:
            for d in wiz.discover(3.0, cfg.get("sweep_subnet")):
                key = d.get("mac") or d["ip"]
                bulbs[key] = {"name": key, "ip": d["ip"], "mac": d.get("mac"),
                              "module": d.get("module"), "fw": d.get("fw"),
                              "pilot": d.get("pilot"), "source": "discover"}
        except Exception as e:  # noqa: BLE001
            errors.append(f"discover: {e}")
    for name, k in known.items():
        ip = k.get("ip")
        if not ip:
            continue
        entry = bulbs.setdefault(k.get("mac") or ip, {"name": name, "ip": ip, "mac": k.get("mac"),
                                                     "module": k.get("module"), "source": "config"})
        entry["name"] = name
        if entry.get("pilot"):
            continue
        try:
            entry["pilot"] = wiz.status(ip)
        except Exception as e:  # noqa: BLE001
            entry["error"] = str(e)
            errors.append(f"{name}@{ip}: {e}")
    out = []
    for b in bulbs.values():
        p = b.pop("pilot", None) or {}
        b.update({
            "reachable": bool(p),
            "on": p.get("state") if p else None,
            "dimming": p.get("dimming"),
            "temp": p.get("temp"),
            "sceneId": p.get("sceneId"),
            "rgb": [p[c] for c in ("r", "g", "b")] if all(c in p for c in ("r", "g", "b")) else None,
            "rssi": p.get("rssi"),
            "state": "PASS" if p else "FAIL",
        })
        out.append(b)
    return {"ok": not errors, "at": now(), "kind": "wiz", "count": len(out),
            "state": "PASS" if out and not errors else ("BLOCKED" if not out else "FAIL"),
            "note": None if out else "no WiZ bulb answered on UDP 38899 (not on this LAN / powered off / not yet added to config)",
            "devices": out, "errors": errors, "ms": int((time.monotonic() - t0) * 1000)}


def collect_plugs() -> dict:
    t0 = time.monotonic()
    chk = tuya.config_check()
    devices, errors = [], []
    for name, c in chk["plugs"].items():
        d = {"name": name, "ip": c.get("ip"), "version": c.get("version"), "on": None}
        if not c["ready"]:
            d.update({"state": "BLOCKED", "missing": c["missing"]})
        elif not VENV_PY.is_file():
            d.update({"state": "BLOCKED", "error": "venv missing (Energy/Smart-Devices/.venv)"})
        else:
            try:
                r = subprocess.run([str(VENV_PY), str(HERE / "tuya.py"), "status", name],
                                   capture_output=True, text=True, timeout=10)
                res = json.loads(r.stdout or "{}")
                d.update({"on": res.get("on"), "dps": res.get("dps"),
                          "state": "PASS" if res.get("ok") else "FAIL",
                          "error": None if res.get("ok") else res.get("error")})
            except Exception as e:  # noqa: BLE001
                d.update({"state": "FAIL", "error": str(e)})
        if d.get("error"):
            errors.append(f"{name}: {d['error']}")
        devices.append(d)
    blocked_note = None
    if not devices:
        blocked_note = ("BLOCKED: no local_key yet. Pair BSD01 in Smart Life + link Tuya IoT cloud "
                        "(tinytuya wizard) -> config/tuya-devices.local.json, or flash Tasmota/ESPHome.")
    return {"ok": not errors, "at": now(), "kind": "tuya-bsd01", "count": len(devices),
            "state": "BLOCKED" if not devices or all(x["state"] == "BLOCKED" for x in devices)
            else ("PASS" if not errors else "FAIL"),
            "note": blocked_note, "devices": devices, "errors": errors,
            "ms": int((time.monotonic() - t0) * 1000)}


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    w = collect_wiz("--discover" in argv)
    p = collect_plugs()
    write_json(OUT / "wiz-last.json", w, dry)
    write_json(OUT / "plugs-last.json", p, dry)
    summary = {"ok": True, "at": now(), "dry_run": dry,
               "gate": "RR_SMART_DEVICES", "gate_on": os.environ.get("RR_SMART_DEVICES", "0") == "1",
               "sources": {k: {"state": v["state"], "count": v["count"], "ms": v["ms"],
                               "errors": v["errors"][:5]} for k, v in (("wiz", w), ("plugs", p))},
               "files": ["wiz-last.json", "plugs-last.json"]}
    write_json(OUT / "collector-last.json", summary, dry)
    print(json.dumps({"ok": True, "wiz": w["state"], "wiz_count": w["count"],
                      "plugs": p["state"], "plugs_count": p["count"], "out": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
