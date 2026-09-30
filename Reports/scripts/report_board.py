#!/usr/bin/env python3
"""HST daily report due ledger + catch-up (G3 port of G1 reports/sort/daily-report-board + daily-reports-catchup, 2026-09-29).

  python3 report_board.py status              seed today's slots, mark past-due ones, print the board (no report run)
  python3 report_board.py run-due [--voice]   run the oldest mandatory due/failed slot still in its window (text only by
                                              default: voice_reports.py <slot>_report --no-voice; --voice also renders WAV)

Ported unchanged: slot policy (mandatory + catch-up only for morning / midday), catchup_window_open (morning only before
12:00, midday before 17:00), prior-day expiry (unfinished mandatory -> missed, optional -> skipped_optional), 14-day
history cap, oldest-first next_catchup_slot, late never caught up. Changed: G1 generated through report_generation
(Grok/local engine + MP3) and then PLAYED the report; G3 runs the existing template roll-ups and never plays
(playback BLOCKED). Slot times follow the G3 roll-up jobs (09:02 / 12:02 / 21:02), not G1's 10:00 / 11:55 / 22:00;
G1's evening slot was already removed there. A slot counts as done when <slot>_report_current.md was written today
after its scheduled time. State: Database Reports/board/daily-reports-due.json (small; rewritten in place).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parents[1]
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
STATE = DB / "Reports" / "board" / "daily-reports-due.json"
REPORTS = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))
VOICE = PACIFIC / "Media" / "Voice" / "scripts" / "voice_reports.py"
SLOTS = ("morning", "midday", "late")
META = {"morning": {"hour": 9, "minute": 2, "mandatory": True, "catch_up_allowed": True},
        "midday": {"hour": 12, "minute": 2, "mandatory": True, "catch_up_allowed": True},
        "late": {"hour": 21, "minute": 2, "mandatory": False, "catch_up_allowed": False}}
DONEISH = frozenset({"done", "missed", "skipped_optional"})
RETRYABLE = frozenset({"due", "failed"})


def now() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def catchup_window_open(kind: str, t: datetime) -> bool:  # G1 rule
    return t.hour < 12 if kind == "morning" else t.hour < 17 if kind == "midday" else False


def _read() -> dict:
    try:
        d = json.loads(STATE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(d: dict) -> dict:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    d = dict(d, updated_at=now().isoformat())
    tmp = STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATE)
    return d


def _seed(kind: str, day: str) -> dict:
    m = META[kind]
    return {"status": "pending", "scheduled_at": f"{day}T{m['hour']:02d}:{m['minute']:02d}:00", **m,
            "completed_at": None, "error": None, "started_at": None}


def _expire(prior: dict) -> dict:  # G1 _expire_prior_day
    for kind, row in (prior.get("slots") or {}).items():
        if not isinstance(row, dict) or row.get("status") in DONEISH:
            continue
        if row.get("mandatory"):
            row.update(status="missed", error=row.get("error") or "unfinished_after_midnight", completed_at=now().isoformat())
        else:
            row.update(status="skipped_optional", completed_at=now().isoformat())
    return prior


def _written_today(kind: str, t: datetime) -> str | None:
    f = REPORTS / f"{kind}_report_current.md"
    if not f.is_file():
        return None
    mt = datetime.fromtimestamp(f.stat().st_mtime, HST)
    due = t.replace(hour=META[kind]["hour"], minute=META[kind]["minute"], second=0)
    return mt.isoformat(timespec="seconds") if mt.date() == t.date() and mt >= due else None


def ensure_today(t: datetime) -> dict:
    day = t.strftime("%Y-%m-%d")
    d = _read()
    if d.get("day") and d["day"] != day:
        hist = d.get("history") if isinstance(d.get("history"), dict) else {}
        hist[d["day"]] = {"day": d["day"], "slots": _expire(deepcopy(d)).get("slots") or {}}
        for old in sorted(hist)[:-14]:
            hist.pop(old, None)
        d = {"day": day, "slots": {}, "history": hist}
    d.setdefault("day", day)
    d.setdefault("history", {})
    slots = d.setdefault("slots", {})
    for kind in SLOTS:
        if not isinstance(slots.get(kind), dict):
            slots[kind] = _seed(kind, day)
    return d


def mark_due(t: datetime) -> dict:
    d = ensure_today(t)
    for kind in SLOTS:
        row = d["slots"][kind]
        seen = _written_today(kind, t)
        if seen and row["status"] != "done":
            row.update(status="done", completed_at=seen, error=None)
            continue
        if row["status"] == "pending" and t >= t.replace(hour=row["hour"], minute=row["minute"], second=0):
            row.update(status="due", marked_due_at=t.isoformat())
    return _write(d)


def next_catchup_slot(d: dict, t: datetime) -> str | None:
    c = [(r["scheduled_at"], k) for k, r in d["slots"].items() if r.get("mandatory") and r.get("catch_up_allowed")
         and catchup_window_open(k, t) and r.get("status") in RETRYABLE]
    return sorted(c)[0][1] if c else None


def run_due(t: datetime, voice: bool) -> dict:
    d = mark_due(t)
    kind = next_catchup_slot(d, t)
    if not kind:
        return {"ok": True, "skipped": True, "detail": "nothing_due", "slots": {k: r["status"] for k, r in d["slots"].items()}}
    d["slots"][kind].update(status="running", started_at=now().isoformat())
    _write(d)
    cmd = ["nice", "-n", "10", sys.executable, str(VOICE), f"{kind}_report"] + ([] if voice else ["--no-voice"])
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    ok = p.returncode == 0
    d["slots"][kind].update(status="done" if ok else "failed", completed_at=now().isoformat() if ok else None,
                            error=None if ok else (p.stderr or p.stdout)[-400:], catch_up=True)
    _write(d)
    return {"ok": ok, "kind": kind, "rc": p.returncode, "voice": voice, "out": (p.stdout or "").strip()[-400:]}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("status", "run-due"):
        print(json.dumps({"ok": False, "detail": "usage: report_board.py status | run-due [--voice]"}))
        return 2
    t = now()
    if sys.argv[1] == "status":
        d = mark_due(t)
        print(json.dumps({"ok": True, "day": d["day"], "path": str(STATE),
                          "slots": {k: {"status": r["status"], "scheduled_at": r["scheduled_at"]} for k, r in d["slots"].items()},
                          "next_catchup": next_catchup_slot(d, t)}))
        return 0
    res = run_due(t, "--voice" in sys.argv)
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
