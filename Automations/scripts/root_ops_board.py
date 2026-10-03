# ==============================================================================
# FILE: Automations/scripts/root_ops_board.py
# What this file is: read-only JSON board for the Root Ops phone app.
# It uses the same files and process checks as the poller and Root Monitor.
# No tokens, no camera credentials, no private paths.
# ==============================================================================
"""GET /api/ops/mobile-dashboard body. Measured files and process checks only."""

from __future__ import annotations

import json
import socket
import time
from datetime import datetime
from pathlib import Path

ECO = Path("/home/rootrecord/RootRecord-Ecosystem")
DB = ECO / "2 - RootRecord-Database"
ENERGY = DB / "Energy"
GEOLOGY = DB / "Geology"
WEATHER = DB / "Weather" / "Hawai'i" / "reports" / "0 Level Processing" / "Hawaii_State_Weather_Report_current.md"
SYSTEM_STATUS = DB / "System" / "status" / "system-status.json"

# Same rows as poller-dashboard.py SERVICES.
SERVICES = (
    ("poller", "Poller", ("Automations/scripts/rootserver_poller.py",)),
    ("relay", "Telegram relay", ("telegram/scripts/council-relay.py",)),
    ("ble", "EcoFlow BLE", ("scripts/ble/ble-owner.py",)),
    ("globe", "Hawaii globe", ("local-data-globe/collector.js",)),
    ("cam", "Cameras", ("cam_server.py",)),
    ("ollama", "Ollama", ("ollama",)),
    ("tunnel", "Cloudflare tunnel", ("cloudflared",)),
)

_mc_cache = {"at": 0.0, "online": None, "latency_ms": None}


def build_board() -> dict:
    services = _services()
    power = _power()
    host = _host()
    kilauea = _volcano()
    quakes = _quakes()
    weather = _weather()
    minecraft = _minecraft()
    cam_up = any(row["id"] == "cam" and row["up"] for row in services)
    return {
        "ok": True,
        "board_ok": True,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "host_name": "rootrecord-software-solutions",
        "power": power,
        "host": host,
        "weather": weather,
        "kilauea": kilauea,
        "quakes": quakes,
        "minecraft": minecraft,
        "services": services,
        "servers": minecraft["servers"],
        "tunnel": {
            "process_count": 1 if any(row["id"] == "tunnel" and row["up"] for row in services) else 0,
            "metrics_ok": any(row["id"] == "tunnel" and row["up"] for row in services),
            "note": "rootserver.rootrecord.cloud → poller :8799",
        },
        "media": {
            "public": {
                "exists": cam_up,
                "path": "A-EYES on this desk",
                "types": ["ch1", "ch2", "ch3", "ch4"] if cam_up else [],
            }
        },
    }


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _num(blob, key):
    if isinstance(blob, dict) and isinstance(blob.get(key), (int, float)):
        return blob[key]
    return None


def _metric(status, name):
    current = (status or {}).get("current") if isinstance(status, dict) else None
    metrics = current.get("metrics") if isinstance(current, dict) else None
    row = metrics.get(name) if isinstance(metrics, dict) else None
    if isinstance(row, dict) and isinstance(row.get("value"), (int, float)):
        return row["value"]
    return None


def _power() -> dict:
    delta_soc = _read_json(ENERGY / "soc" / "delta2-last.json")
    river_soc = _read_json(ENERGY / "soc" / "river2pro-last.json")
    delta_w = _read_json(ENERGY / "watts" / "delta2-last.json")
    river_w = _read_json(ENERGY / "watts" / "river2pro-last.json")
    d_soc = _num(delta_soc, "soc")
    r_soc = _num(river_soc, "soc")
    devices = []
    if isinstance(river_soc, dict) or isinstance(river_w, dict):
        devices.append({
            "label": "River 2 Pro",
            "soc": None if r_soc is None else int(round(r_soc)),
            "online": r_soc is not None,
            "pv_w": _num(river_w, "solar_input_power"),
            "ac_out_w": _num(river_w, "ac_output_power"),
            "input_kind": "B1",
        })
    if isinstance(delta_soc, dict) or isinstance(delta_w, dict):
        devices.append({
            "label": "Delta 2",
            "soc": None if d_soc is None else int(round(d_soc)),
            "online": d_soc is not None,
            "pv_w": _num(delta_w, "solar_input_power"),
            "ac_out_w": _num(delta_w, "ac_output_power"),
            "ebatt_w": _num(delta_w, "ac_input_power"),
            "input_kind": "B2",
        })
    solar = _num(delta_w, "solar_input_power")
    if solar is None:
        solar = _num(river_w, "solar_input_power")
    load = _num(delta_w, "ac_output_power")
    if load is None:
        load = _num(river_w, "ac_output_power")
    stamps = [
        blob.get("at")
        for blob in (delta_soc, river_soc, delta_w, river_w)
        if isinstance(blob, dict) and blob.get("at")
    ]
    lap = _laptop_battery()
    return {
        "ok": bool(devices),
        "live": d_soc is not None or r_soc is not None,
        "source": "EcoFlow BLE samples on this desk",
        "battery_pct": d_soc if d_soc is not None else r_soc,
        "solar_in_w": solar,
        "load_w": load,
        "state": "Live" if (d_soc is not None or r_soc is not None) else "Waiting",
        "devices": devices,
        "detail": lap,
        "updated_at": stamps[-1] if stamps else None,
    }


def _laptop_battery() -> str | None:
    try:
        ps = Path("/sys/class/power_supply")
        bat = next((b for b in sorted(ps.glob("BAT*")) if (b / "capacity").exists()), None)
        if bat is None:
            return None
        ac = any(
            (m / "online").read_text().strip() == "1"
            for m in ps.iterdir()
            if (m / "type").exists()
            and (m / "type").read_text().strip() == "Mains"
            and (m / "online").exists()
        )
        cap = (bat / "capacity").read_text().strip()
        status = (bat / "status").read_text().strip()
        return f"Desk battery {cap}% {status} {'on AC' if ac else 'on battery'}"
    except OSError:
        return None


def _host() -> dict:
    status = _read_json(SYSTEM_STATUS)
    cpu = _metric(status, "cpu_percent")
    mem = _metric(status, "mem_used_percent")
    total = _metric(status, "mem_total_bytes")
    avail = _metric(status, "mem_available_bytes")
    used = None
    total_gb = None
    if isinstance(total, (int, float)) and isinstance(avail, (int, float)):
        total_gb = round(total / (1024 ** 3), 2)
        used = round((total - avail) / (1024 ** 3), 2)
    name = None
    if isinstance(status, dict):
        name = status.get("host") or (status.get("current") or {}).get("host")
    return {
        "ok": cpu is not None or mem is not None,
        "cpu_pct": cpu,
        "mem_pct": mem,
        "mem_used_gb": used,
        "mem_total_gb": total_gb,
        "load1": _metric(status, "load1"),
        "load5": _metric(status, "load5"),
        "load15": _metric(status, "load15"),
        "host_name": name or "rootrecord-software-solutions",
        "updated_at": (status or {}).get("generated_at") if isinstance(status, dict) else None,
    }


def _volcano() -> dict:
    kilauea = _read_json(GEOLOGY / "Volcanoes" / "kilauea-last.json")
    mauna = _read_json(GEOLOGY / "Volcanoes" / "mauna-loa-last.json")
    quakes = _read_json(GEOLOGY / "Earthquakes" / "hawaii-last.json")
    if not isinstance(kilauea, dict):
        return {"ok": False}
    notice = kilauea.get("latest_notice") if isinstance(kilauea.get("latest_notice"), dict) else {}
    synopsis = notice.get("synopsis") or kilauea.get("headline")
    ml = ""
    if isinstance(mauna, dict) and mauna.get("alert_level"):
        color = mauna.get("color_code") or ""
        ml = f" Mauna Loa {mauna.get('alert_level')}" + (f" / {color}." if color else ".")
    level = kilauea.get("alert_level") or ""
    color = kilauea.get("color_code") or ""
    label = level if not color else f"{level} / {color}"
    largest = quakes.get("largest") if isinstance(quakes, dict) else None
    max_mag = largest.get("mag") if isinstance(largest, dict) else None
    return {
        "ok": True,
        "alert_level": label,
        "multiplier": kilauea.get("multiplier"),
        "events_nearby": quakes.get("count") if isinstance(quakes, dict) else None,
        "max_magnitude": max_mag,
        "updated_at": kilauea.get("at"),
        "detail": ((synopsis or "") + ml).strip() or None,
        "source": "USGS Hawaiian Volcano Observatory",
    }


def _quake_rows(blob, limit):
    if not isinstance(blob, dict):
        return []
    rows = []
    for event in (blob.get("events") or [])[:limit]:
        if not isinstance(event, dict):
            continue
        rows.append({
            "id": event.get("id"),
            "mag": event.get("mag"),
            "place": event.get("place"),
            "time": _epoch_ms(event.get("time_utc") or event.get("time_hst")),
        })
    return rows


def _epoch_ms(stamp):
    if not isinstance(stamp, str) or not stamp:
        return None
    try:
        return int(datetime.fromisoformat(stamp).timestamp() * 1000)
    except ValueError:
        return None


def _quakes() -> dict:
    hawaii = _read_json(GEOLOGY / "Earthquakes" / "hawaii-last.json")
    globe = _read_json(GEOLOGY / "Earthquakes" / "global-last.json")
    if not isinstance(hawaii, dict) and not isinstance(globe, dict):
        return {"global": [], "island": []}
    fetched = None
    if isinstance(hawaii, dict):
        fetched = hawaii.get("at")
    return {
        "island": _quake_rows(hawaii, 8),
        "global": _quake_rows(globe, 5),
        "fetched_at": fetched,
    }


def _weather() -> dict:
    try:
        with WEATHER.open("r", encoding="utf-8", errors="replace") as handle:
            head = handle.read(6000)
    except OSError:
        return {"ok": False, "detail": "Hawaii state weather report is not on disk"}
    generated = None
    forecast = None
    for line in head.splitlines():
        if generated is None and line.startswith("- **Generated:**"):
            generated = line.split("**Generated:**", 1)[-1].strip()
        if forecast is None and line.startswith(".TODAY..."):
            forecast = line.removeprefix(".TODAY...").strip()
        if generated and forecast:
            break
    return {
        "ok": True,
        "period": "Today",
        "forecast": forecast,
        "updated_at": generated,
        "detail": "NWS Honolulu zone forecast, from the Hawaii state weather report.",
        "alerts_active": 0,
    }


def _services() -> list:
    cmdlines = _cmdlines()
    rows = []
    for sid, label, needles in SERVICES:
        up = any(any(needle in line for needle in needles) for line in cmdlines)
        rows.append({"id": sid, "label": label, "up": up})
    return rows


def _cmdlines() -> list:
    found = []
    proc = Path("/proc")
    try:
        names = list(proc.iterdir())
    except OSError:
        return found
    for entry in names:
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        if raw.strip():
            found.append(raw)
    return found


def _minecraft() -> dict:
    now = time.time()
    if _mc_cache["online"] is None or now - _mc_cache["at"] > 30:
        online, latency = _tcp("play.rootmc.net", 25565, 1.5)
        _mc_cache["at"] = now
        _mc_cache["online"] = online
        _mc_cache["latency_ms"] = latency
    live_status = "online" if _mc_cache["online"] else "offline"
    return {
        "ok": True,
        "live": {
            "host": "play.rootmc.net",
            "port": 25565,
            "online": bool(_mc_cache["online"]),
            "latency_ms": _mc_cache["latency_ms"],
        },
        "test": {
            "host": "ava-core",
            "name": "OptiPlex",
            "online": False,
            "probed": False,
            "detail": "Test host is ava-core on the OptiPlex. This desk does not probe it.",
        },
        "servers": [
            {
                "id": "prod",
                "name": "RootMC",
                "status": live_status,
                "address": "play.rootmc.net",
            },
            {
                "id": "test",
                "name": "ava-core",
                "status": "unknown",
                "address": "OptiPlex",
            },
        ],
    }


def _tcp(host: str, port: int, timeout: float):
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, int((time.perf_counter() - started) * 1000)
    except OSError:
        return False, None


if __name__ == "__main__":
    print(json.dumps(build_board(), indent=2)[:5000])
