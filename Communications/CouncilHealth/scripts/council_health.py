#!/usr/bin/env python3
"""Council health check for the live relay.

Reports one council-relay.py process, Telegram getMe for Ava/Bruce/Carly, and
409 lines in the relay log. Does not call getUpdates, start or stop the relay,
or load a model unless RR_COUNCIL_HEALTH_PROBE=1 and --probe are both set.
Sends only when --alert and RR_RELAY_REPLIES=1, after a 30-minute cooldown.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "lib"
sys.path.insert(0, str(LIB))
from envload import load_env  # noqa: E402

PACIFIC = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server")
DATA = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Communications/CouncilHealth")
LOG_DIR = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/CouncilHealth")
RELAY_LOG = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/council-relay.log")
RELAY_CONF = PACIFIC / "Communications" / "telegram" / "config" / "relay.conf"
RUN_INFER = PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"
ALERT_COOLDOWN_S = 30 * 60
BOTS = ("ava", "bruce", "carly")
TOKEN_KEYS = {
    "ava": "TELEGRAM_AVA_TOKEN",
    "bruce": "TELEGRAM_BRUCE_TOKEN",
    "carly": "TELEGRAM_CARLY_TOKEN",
}


def _load_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _relay_pids() -> list[int]:
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", r"^python3 .+/council-relay\.py"],
            text=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return []
    pids: list[int] = []
    for line in out.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def _get_me(token: str) -> dict[str, Any]:
    if not token:
        return {"ok": False, "detail": "no_token"}
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"{type(e).__name__}"}
    if isinstance(body, dict) and body.get("ok"):
        user = body.get("result") or {}
        return {"ok": True, "username": user.get("username")}
    return {"ok": False, "detail": "getMe_false"}


def _tail_409(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": True, "detail": "no_log", "conflict_409": 0}
    try:
        text = path.read_bytes()[-120_000:].decode("utf-8", errors="replace")
    except OSError as e:
        return {"ok": False, "detail": f"log_read:{type(e).__name__}", "conflict_409": 0}
    lines = text.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        if "[ok] relay chat=" in ln:
            start = i
    recent = lines[start:]
    conflict = sum(1 for ln in recent if "409" in ln)
    return {"ok": conflict < 1, "conflict_409": conflict, "since_listen": True}


def _probe() -> dict[str, Any]:
    if os.environ.get("RR_COUNCIL_HEALTH_PROBE", "0").strip() != "1":
        return {"ok": None, "detail": "skipped"}
    if not RUN_INFER.is_file():
        return {"ok": False, "detail": "no_run_infer"}
    try:
        completed = subprocess.run(
            [str(RUN_INFER), "ava", "Reply with OK only."],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return {"ok": False, "detail": type(e).__name__}
    text = (completed.stdout or "").strip()
    return {"ok": bool(text) and completed.returncode == 0, "preview": text[:40]}


def _alert(text: str, chat_id: str) -> dict[str, Any]:
    if os.environ.get("RR_RELAY_REPLIES", "0").strip() != "1":
        return {"ok": False, "detail": "replies_off"}
    load_env()
    token = (os.environ.get("TELEGRAM_AVA_TOKEN") or "").strip()
    if not token or not chat_id:
        return {"ok": False, "detail": "no_token_or_chat"}
    payload = json.dumps({"chat_id": chat_id, "text": text[:3500], "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": type(e).__name__}
    return {"ok": bool(isinstance(body, dict) and body.get("ok"))}


def check(*, alert: bool, probe_chat: bool, network: bool) -> dict[str, Any]:
    load_env()
    pids = _relay_pids()
    problems: list[str] = []
    if len(pids) == 0:
        problems.append("council relay process missing")
    elif len(pids) > 1:
        problems.append(f"duplicate council relay pids={pids}")

    if network:
        bots = {name: _get_me(os.environ.get(TOKEN_KEYS[name], "")) for name in BOTS}
        for name, row in bots.items():
            if not row.get("ok"):
                problems.append(f"{name} getMe failed ({row.get('detail')})")
    else:
        bots = {name: {"ok": None, "detail": "skipped"} for name in BOTS}

    log_issues = _tail_409(RELAY_LOG)
    if not log_issues.get("ok"):
        problems.append(f"getUpdates 409×{log_issues.get('conflict_409')} since last relay listen")

    if probe_chat:
        chat_probe = _probe()
        if chat_probe.get("ok") is False:
            problems.append(f"model probe failed ({chat_probe.get('detail')})")
    else:
        chat_probe = {"ok": None, "detail": "skipped"}

    ok = not problems
    report: dict[str, Any] = {
        "ok": ok,
        "ts": time.time(),
        "relay_pids": pids,
        "bots": bots,
        "log": log_issues,
        "chat_probe": chat_probe,
        "problems": problems,
        "alerted": False,
    }

    state_path = DATA / "state.json"
    state: dict[str, Any] = {}
    if state_path.is_file():
        try:
            raw = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                state = raw
        except (OSError, json.JSONDecodeError):
            state = {}
    state["last"] = {k: report[k] for k in ("ok", "ts", "problems", "alerted")}
    state["last_ok"] = time.time() if ok else state.get("last_ok")
    state["last_fail"] = None if ok else time.time()

    if alert and problems:
        last_alert = float(state.get("last_alert_ts") or 0)
        if time.time() - last_alert >= ALERT_COOLDOWN_S:
            chat_id = _load_kv(RELAY_CONF).get("COUNCIL_CHAT_ID", "")
            msg = (
                "Council health check — systems not fully functional:\n"
                + "\n".join(f"• {p}" for p in problems[:8])
            )
            sent = _alert(msg, chat_id)
            if sent.get("ok"):
                state["last_alert_ts"] = time.time()
                report["alerted"] = True
                state["last"]["alerted"] = True

    DATA.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (DATA / "latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    line = {
        "ts": report["ts"],
        "ok": ok,
        "problems": problems,
        "alerted": report["alerted"],
        "pids": pids,
    }
    with (LOG_DIR / "council-health.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Council relay health check")
    parser.add_argument("--no-alert", action="store_true")
    parser.add_argument("--alert", action="store_true")
    parser.add_argument("--no-probe", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    alert = bool(args.alert) and not args.no_alert
    probe = bool(args.probe) and not args.no_probe
    report = check(alert=alert, probe_chat=probe, network=not args.no_network)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status = "OK" if report.get("ok") else "FAIL"
        print(f"council-health {status}")
        for prob in report.get("problems") or []:
            print(f"  - {prob}")
        print(f"  alerted={report.get('alerted')}")
    if args.no_network:
        return 0
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
