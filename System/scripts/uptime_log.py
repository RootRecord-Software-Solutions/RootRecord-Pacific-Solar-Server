#!/usr/bin/env python3
"""Desk-up / desk-down event log (G3 port of G1 uptime-log/scripts/uptime_log.py). Live stamps only — never invent hours.

  python3 uptime_log.py [tick|facts|recent]

Same event kinds (origin_start, heartbeat_gap, desk_up), same KEEP=400 rolling JSONL and GAP_S=180 gap rule.
G3 changes (documented): stdlib only (psutil.boot_time -> /proc/uptime); the "origin" is the Pacific poller (tick runs
from jobs.py); gap timing uses wall clock + kernel boot_id instead of time.monotonic() (monotonic resets on reboot,
so G1 could not see a reboot gap) and a boot_id change logs a `boot` event. G1 origin_start/stop hooks were called
by Ava-Core origin; G3 has no such hook, so the first tick after a start logs origin_start(inferred=True) as G1 did.
Files: Database System/uptime/uptime-events.jsonl + uptime-last.json (marker). Gated RR_UPTIME_LOG=1 (every 60 s).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
DIR = DB / "System" / "uptime"
PATH, MARKER = DIR / "uptime-events.jsonl", DIR / "uptime-last.json"
KEEP, GAP_S = 400, 180


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _boot_uptime_s() -> int:
    with open("/proc/uptime") as f:
        return int(float(f.read().split()[0]))


def _boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return ""


def _append(kind: str, **extra) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    with PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": _now_iso(), "kind": kind, **extra}, default=str) + "\n")
    lines = PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) > KEEP:
        tmp = PATH.with_name(PATH.name + ".tmp")
        tmp.write_text("\n".join(lines[-KEEP:]) + "\n", encoding="utf-8")
        os.replace(tmp, PATH)


def _marker() -> dict:
    try:
        raw = json.loads(MARKER.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_marker(payload: dict) -> None:
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    tmp = MARKER.with_name(MARKER.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, MARKER)


def tick() -> dict:
    """Heartbeat: stamp presence; log a gap if the desk was gone long enough."""
    now, m, bid = time.time(), _marker(), _boot_id()
    last = float(m.get("last_tick_epoch") or 0)
    if m.get("boot_id") and bid and bid != m["boot_id"]:
        _append("boot", boot_uptime_s=_boot_uptime_s())
    if last and now - last >= GAP_S:
        _append("heartbeat_gap", gap_s=int(now - last))
        _append("desk_up", after_gap_s=int(now - last))
    m.update(last_tick_at=_now_iso(), last_tick_epoch=now, boot_id=bid)
    if not m.get("origin_started_at"):
        m["origin_started_at"] = _now_iso()
        _append("origin_start", inferred=True, boot_uptime_s=_boot_uptime_s())
    _write_marker(m)
    return m


def recent(limit: int = 24) -> list[dict]:
    try:
        lines = PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out = []
    for line in lines[-limit:]:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def last_return() -> dict | None:
    return next((r for r in reversed(recent(80)) if r.get("kind") in {"origin_start", "desk_up"}), None)


def facts(*, process_uptime_s: int | None = None) -> dict:
    m, desk_s = _marker(), None
    if m.get("origin_started_at"):
        try:
            desk_s = int((datetime.now(timezone.utc) - datetime.fromisoformat(m["origin_started_at"])).total_seconds())
        except ValueError:
            desk_s = None
    ret = last_return() or {}
    return {"process_uptime_s": process_uptime_s, "boot_uptime_s": _boot_uptime_s(),
            "desk_uptime_s": desk_s if desk_s is not None else process_uptime_s,
            "origin_started_at": m.get("origin_started_at"), "last_return_at": ret.get("at"),
            "last_return_kind": ret.get("kind"), "recent": recent(12)}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tick"
    if cmd == "tick":
        tick()
        print(json.dumps({"ok": True, "facts": {k: v for k, v in facts().items() if k != "recent"}}))
    elif cmd == "recent":
        print(json.dumps(recent(), indent=2))
    else:
        print(json.dumps(facts(), indent=2))
