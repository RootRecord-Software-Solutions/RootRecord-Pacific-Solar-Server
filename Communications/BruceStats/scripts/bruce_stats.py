#!/usr/bin/env python3
"""Bruce measured desk sample from live host and EcoFlow last files.

Once per hour slot at 07, 15, and 21 HST. Dry-run by default: no Telegram,
no token load. Never invents watts. A missing last file is DOWN.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
PACIFIC = ROOT.parents[1]
DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
HOST_LAST = DB / "System" / "last" / "host-last.json"
ENERGY = DB / "Energy"
DATA = DB / "Communications" / "BruceStats"
LOG_DIR = DB / "Logs" / "Communications" / "BruceStats"
SLOT_NAME = "slot.json"
TEXT_NAME = "last-text.txt"
LOG_NAME = "bruce-stats.jsonl"
HST = ZoneInfo("Pacific/Honolulu")
HOURS = (7, 15, 21)
PACKS = (("delta2", "DELTA 2"), ("river2pro", "RIVER 2 PRO"))
WATT_KEYS = (
    ("ac_output_power", "AC out"),
    ("solar_input_power", "solar"),
    ("ac_input_power", "AC in"),
    ("usbc_output_power", "USB-C out"),
)

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def send_enabled() -> bool:
    return os.environ.get("RR_BRUCE_STATS_SEND", "0").strip() == "1"


def load_json(path: Path):
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _field(fields: dict, name: str):
    row = fields.get(name)
    if not isinstance(row, dict):
        return None
    return _num(row.get("value"))


def host_line(snap) -> str:
    if not isinstance(snap, dict):
        return "Host: DOWN"
    fields = snap.get("fields") if isinstance(snap.get("fields"), dict) else {}
    bits = []
    at = str(snap.get("at") or "").strip()
    if at:
        bits.append(f"last {at}")
    cpu = _field(fields, "cpu_percent")
    mem = _field(fields, "mem_used_percent")
    load1 = _field(fields, "load1")
    if cpu is not None:
        bits.append(f"CPU {cpu:g}%")
    if mem is not None:
        bits.append(f"RAM {mem:g}%")
    if load1 is not None:
        bits.append(f"load {load1:g}")
    if not bits:
        return "Host: DOWN"
    return "Host: " + ", ".join(bits)


def pack_phrase(label: str, soc, watts) -> str:
    if soc is None and watts is None:
        return f"{label}: DOWN"
    bits = [label]
    soc_at = ""
    if isinstance(soc, dict):
        level = _num(soc.get("soc"))
        if level is not None:
            bits.append(f"SOC {level:g}%")
        soc_at = str(soc.get("at") or "").strip()
        if soc_at:
            bits.append(f"at {soc_at}")
    else:
        bits.append("SOC DOWN")
    if isinstance(watts, dict):
        for key, name in WATT_KEYS:
            amount = _num(watts.get(key))
            if amount is not None:
                bits.append(f"{name} {amount:g} W")
        watt_at = str(watts.get("at") or "").strip()
        if watt_at and not soc_at:
            bits.append(f"at {watt_at}")
    else:
        bits.append("watts DOWN")
    return " ".join(bits)


def ecoflow_line(energy: Path) -> str:
    parts = []
    for alias, label in PACKS:
        parts.append(
            pack_phrase(
                label,
                load_json(energy / "soc" / f"{alias}-last.json"),
                load_json(energy / "watts" / f"{alias}-last.json"),
            )
        )
    return "EcoFlow: " + " | ".join(parts)


def build_text(host_path: Path, energy: Path) -> str:
    return (
        "Desk sample (measured)\n"
        f"{host_line(load_json(host_path))}\n"
        f"{ecoflow_line(energy)}\n"
        "\n"
        "Bruce Monitor"
    )


def slot_key(now: datetime) -> str:
    return f"{now.strftime('%Y-%m-%d')}-{now.hour}"


def append_log(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def deliver(text: str) -> dict:
    """Telegram stays off unless RR_BRUCE_STATS_SEND=1. Never prints the token.

    Chat id comes from CouncilQuake's council_chat_id. That folder's maybe_send
    posts as Carly, so this function does not call it.
    """
    if not send_enabled():
        return {"ok": True, "sent": False, "detail": "send gate off"}
    quake_scripts = PACIFIC / "Communications" / "CouncilQuake" / "scripts"
    if not (quake_scripts / "quake_posts.py").is_file():
        return {"ok": False, "sent": False, "detail": "Council quake Telegram posts folder missing"}
    if str(quake_scripts) not in sys.path:
        sys.path.insert(0, str(quake_scripts))
    from envload import bruce_token
    from quake_posts import council_chat_id

    token = bruce_token()
    chat = council_chat_id()
    if not token or not chat or not text.strip():
        return {"ok": False, "sent": False, "detail": "missing token, chat, or text"}
    body = json.dumps(
        {"chat_id": chat, "text": text[:3900], "disable_web_page_preview": True}
    ).encode()
    import urllib.request

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.load(response)
    return {"ok": bool(payload.get("ok")), "sent": bool(payload.get("ok")), "detail": "sendMessage"}


def run(
    host_path: Path,
    energy: Path,
    data_dir: Path,
    log_path: Path,
    *,
    force: bool = False,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(HST)
    slot = slot_key(now)
    slot_path = data_dir / SLOT_NAME
    prior = load_json(slot_path) or {}
    if not force and now.hour not in HOURS:
        row = {"ok": True, "skipped": True, "detail": "off slot", "slot": slot, "sent": False}
        print(json.dumps(row))
        return row
    if not force and prior.get("last_slot") == slot:
        row = {"ok": True, "skipped": True, "detail": "already", "slot": slot, "sent": False}
        print(json.dumps(row))
        return row
    text = build_text(host_path, energy)
    delivery = deliver(text)
    save_json(
        slot_path,
        {
            "last_slot": slot,
            "sent": bool(delivery.get("sent")),
            "updated": now.isoformat(timespec="seconds"),
        },
    )
    text_path = data_dir / TEXT_NAME
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(text + "\n", encoding="utf-8")
    row = {
        "at": now.isoformat(timespec="seconds"),
        "detail": delivery.get("detail"),
        "ok": bool(delivery.get("ok")),
        "sent": bool(delivery.get("sent")),
        "skipped": False,
        "slot": slot,
    }
    append_log(log_path, row)
    print(text)
    print(json.dumps({"sent": row["sent"], "slot": slot, "detail": row["detail"]}))
    return row


def self_test() -> int:
    """Fixture last files print the desk sample, write a slot, and do not post."""
    import urllib.request

    def _forbid(*_args, **_kwargs):
        raise AssertionError("HTTP is not allowed on the dry run")

    urllib.request.urlopen = _forbid
    os.environ["RR_BRUCE_STATS_SEND"] = "0"
    host = {
        "at": "2026-09-30T17:18:00Z",
        "fields": {
            "cpu_percent": {"value": 12.5},
            "mem_used_percent": {"value": 40},
            "load1": {"value": 0.5},
        },
    }
    when = datetime(2026, 9, 30, 7, 18, tzinfo=HST)
    with tempfile.TemporaryDirectory(prefix="bruce-stats-") as tmp:
        root = Path(tmp)
        host_path = root / "host-last.json"
        energy = root / "Energy"
        data = root / "data"
        log_path = root / "bruce-stats.jsonl"
        host_path.write_text(json.dumps(host), encoding="utf-8")
        (energy / "soc").mkdir(parents=True)
        (energy / "watts").mkdir(parents=True)
        (energy / "soc" / "delta2-last.json").write_text(
            json.dumps({"soc": 4, "at": "2026-09-30T07:18:00-10:00"}), encoding="utf-8"
        )
        (energy / "watts" / "delta2-last.json").write_text(
            json.dumps({"ac_output_power": 69, "solar_input_power": 0}), encoding="utf-8"
        )
        (energy / "soc" / "river2pro-last.json").write_text(
            json.dumps({"soc": 1, "at": "2026-09-30T07:18:00-10:00"}), encoding="utf-8"
        )
        first = run(host_path, energy, data, log_path, now=when)
        text = (data / TEXT_NAME).read_text(encoding="utf-8")
        if "Desk sample (measured)" not in text or not text.startswith("Desk sample"):
            print("FAIL heading", file=sys.stderr)
            return 1
        if "Host: last 2026-09-30T17:18:00Z, CPU 12.5%, RAM 40%, load 0.5" not in text:
            print("FAIL host line", file=sys.stderr)
            return 1
        if "EcoFlow: DELTA 2 SOC 4% at 2026-09-30T07:18:00-10:00, AC out 69 W, solar 0 W" not in text:
            print("FAIL ecoflow line", file=sys.stderr)
            return 1
        if "RIVER 2 PRO SOC 1%" not in text or "watts DOWN" not in text:
            print("FAIL missing watts marked DOWN", file=sys.stderr)
            return 1
        if "Bruce Monitor" not in text:
            print("FAIL signature", file=sys.stderr)
            return 1
        slot = json.loads((data / SLOT_NAME).read_text(encoding="utf-8"))
        if slot.get("last_slot") != "2026-09-30-7" or slot.get("sent") or first.get("sent"):
            print("FAIL slot", file=sys.stderr)
            return 1
        second = run(host_path, energy, data, log_path, now=when)
        if not second.get("skipped") or second.get("detail") != "already":
            print("FAIL second run", file=sys.stderr)
            return 1
        off = run(host_path, energy, data, log_path, now=when.replace(hour=8), force=False)
        if off.get("detail") != "off slot":
            print("FAIL off slot", file=sys.stderr)
            return 1
    print("PASS bruce stats dry-run")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    host = HOST_LAST
    energy = ENERGY
    data = DATA
    log_path = LOG_DIR / LOG_NAME
    force = "--force" in argv
    if "--host" in argv:
        host = Path(argv[argv.index("--host") + 1])
    if "--energy" in argv:
        energy = Path(argv[argv.index("--energy") + 1])
    if "--data" in argv:
        data = Path(argv[argv.index("--data") + 1])
    if "--log" in argv:
        log_path = Path(argv[argv.index("--log") + 1])
    run(host, energy, data, log_path, force=force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
