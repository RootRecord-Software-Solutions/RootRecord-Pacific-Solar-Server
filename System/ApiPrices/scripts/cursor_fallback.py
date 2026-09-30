#!/usr/bin/env python3
"""Cursor ask-mode fallback. Package ApiPrices.

One job at a time. Caps: 2 per HST day, 6 hours between jobs.
Runs only when RR_API_SPEND=1 and may_spend('cursor') is true.
Stores text under Database System/ApiPrices/fallback/. Does not write reports.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import api_ledger
import envload

HST = ZoneInfo("Pacific/Honolulu")
MAX_PER_DAY = 2
MIN_HOURS = 6


def _queue_path() -> Path:
    return api_ledger.data_dir() / "cursor-fallback-queue.json"


def _budget_path() -> Path:
    return api_ledger.data_dir() / "cursor-fallback.json"


def _fallback_dir() -> Path:
    return api_ledger.data_dir() / "fallback"


def _load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _save(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def enqueue(kind: str, system: str, user: str, *, source_hash: str) -> None:
    q = _load(_queue_path(), {"jobs": []})
    jobs = [j for j in q.get("jobs") or [] if not (j.get("kind") == kind and j.get("hash") == source_hash)]
    jobs.append(
        {
            "kind": kind,
            "hash": source_hash,
            "system": system[:1500],
            "user": user[:6000],
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    q["jobs"] = jobs[-8:]
    _save(_queue_path(), q)


def pending() -> list[dict[str, Any]]:
    return list(_load(_queue_path(), {"jobs": []}).get("jobs") or [])


def _budget_ok() -> bool:
    st = _load(_budget_path(), {})
    today = datetime.now(HST).strftime("%Y-%m-%d")
    if st.get("date") != today:
        return True
    if int(st.get("count") or 0) >= MAX_PER_DAY:
        return False
    last = st.get("last_at")
    if last:
        try:
            last_dt = datetime.fromisoformat(str(last))
            if datetime.now(timezone.utc) - last_dt < timedelta(hours=MIN_HOURS):
                return False
        except ValueError:
            pass
    return True


def _note_run() -> None:
    today = datetime.now(HST).strftime("%Y-%m-%d")
    st = _load(_budget_path(), {})
    count = int(st.get("count") or 0) + 1 if st.get("date") == today else 1
    _save(
        _budget_path(),
        {"date": today, "count": count, "last_at": datetime.now(timezone.utc).isoformat()},
    )


def _pop(kind: str, source_hash: str) -> None:
    q = _load(_queue_path(), {"jobs": []})
    q["jobs"] = [j for j in q.get("jobs") or [] if not (j.get("kind") == kind and j.get("hash") == source_hash)]
    _save(_queue_path(), q)


def _blocked() -> str | None:
    if not api_ledger.spend_gate_open():
        return "rr_api_spend_off"
    ok, why = api_ledger.may_spend("cursor")
    if not ok:
        return why
    if not envload.key_set("CURSOR_API_KEY"):
        return "no_key"
    if not _budget_ok():
        return "budget"
    return None


def ask(system: str, user: str) -> str | None:
    why = _blocked()
    if why:
        return None
    prompt = (
        f"{system.strip()}\n\n"
        "Use only the source text below. Do not search the repository. "
        "Do not call tools. Reply with the report text only.\n\n"
        f"{user.strip()}"
    )
    model = api_ledger.DEFAULT_CURSOR_MODEL
    if "[" not in model:
        model = f"{model}[fast=false]"
    envload.load_env()
    key = (os.environ.get("CURSOR_API_KEY") or "").strip()
    cmd = [
        "cursor",
        "agent",
        "-p",
        "--mode",
        "ask",
        "--output-format",
        "text",
        "--model",
        model,
        prompt,
    ]
    env = os.environ.copy()
    env["CURSOR_API_KEY"] = key
    api_ledger.note_spend()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(api_ledger.data_dir()),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    _note_run()
    text = (proc.stdout or "").strip()
    if proc.returncode != 0 or not text:
        return None
    lines = [ln for ln in text.splitlines() if not ln.startswith("Cursor ") or len(ln) > 40]
    out = "\n".join(lines).strip()
    return out[:4000] if out else None


def drain_one() -> dict[str, Any] | None:
    """Run at most one queued job. Text stays in the Database fallback folder."""
    if _blocked():
        return None
    jobs = pending()
    if not jobs:
        return None
    order = {"kilauea": 0, "summary": 1, "morning": 2}
    jobs.sort(key=lambda j: order.get(j.get("kind") or "", 9))
    job = jobs[0]
    text = ask(job.get("system") or "", job.get("user") or "")
    if not text:
        return None
    kind = str(job.get("kind") or "summary")
    _pop(kind, job.get("hash") or "")
    stamp = datetime.now(HST).strftime("%Y-%m-%dT%H%M")
    dest = _fallback_dir() / f"{kind}-cursor-{stamp}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    api_ledger.record_usage("cursor", model=api_ledger.DEFAULT_CURSOR_MODEL, surface="cursor.ask", note=kind)
    return {"kind": kind, "path": str(dest), "text": text}
