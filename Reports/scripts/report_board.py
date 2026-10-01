# ==============================================================================
# FILE: Reports/scripts/report_board.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""HST daily report due ledger + catch-up (G3 port of G1 reports/sort/daily-report-board + daily-reports-catchup, 2026-09-29).

  python3 report_board.py status              seed today's slots, mark past-due ones, print the board (no report run)
  python3 report_board.py run-due [--voice]   run the oldest mandatory due/failed slot still in its window (text only by
                                              default: voice_reports.py <slot>_report --no-voice; --voice also renders WAV)

Ported unchanged: slot policy (mandatory + catch-up only for morning / midday), catchup_window_open (morning only before
12:00, midday before 17:00), prior-day expiry (unfinished mandatory -> missed, optional -> skipped_optional), 14-day
history cap, oldest-first next_catchup_slot, late never caught up. Changed: G1 generated through report_generation
(Grok/local engine + MP3) and then PLAYED the report; G3 runs the existing template roll-ups and never plays
(playback BLOCKED). Slot times follow the G3 roll-up jobs (09:00 / 12:00 / 21:00), not G1's 10:00 / 11:55 / 22:00;
G1's evening slot was already removed there. A slot counts as done when <slot>_report_current.md was written today
after its scheduled time. State: Database Reports/board/daily-reports-due.json (small; rewritten in place).
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
from copy import deepcopy  # info: from copy import deepcopy
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parents[1]  # info: set PACIFIC
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
STATE = DB / "Reports" / "board" / "daily-reports-due.json"  # info: set STATE
REPORTS = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))  # info: set REPORTS
VOICE = PACIFIC / "Media" / "Voice" / "scripts" / "voice_reports.py"  # info: set VOICE
SLOTS = ("morning", "midday", "late")  # info: set SLOTS
META = {"morning": {"hour": 9, "minute": 0, "mandatory": True, "catch_up_allowed": True},  # info: set META
        "midday": {"hour": 12, "minute": 0, "mandatory": True, "catch_up_allowed": True},  # info: "midday" : { "hour" : 12 , "minute"
        "late": {"hour": 21, "minute": 0, "mandatory": False, "catch_up_allowed": False}}  # info: "late" : { "hour" : 21 , "minute"
DONEISH = frozenset({"done", "missed", "skipped_optional"})  # info: set DONEISH
RETRYABLE = frozenset({"due", "failed"})  # info: set RETRYABLE


# ====================================================
# SECTION: function now
# What it does: now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> datetime:  # info: def now
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function catchup_window_open
# What it does: catchup window open.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def catchup_window_open(kind: str, t: datetime) -> bool:  # G1 rule
    return t.hour < 12 if kind == "morning" else t.hour < 17 if kind == "midday" else False  # info: return t . hour < 12 if kind


# ====================================================
# SECTION: function _read
# What it does:  read.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read() -> dict:  # info: def _read
    try:  # info: try :
        d = json.loads(STATE.read_text(encoding="utf-8"))  # info: set d
        return d if isinstance(d, dict) else {}  # info: return d if isinstance ( d , dict
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return {}  # info: return { }


# ====================================================
# SECTION: function _write
# What it does:  write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(d: dict) -> dict:  # info: def _write
    STATE.parent.mkdir(parents=True, exist_ok=True)  # info: STATE . parent . mkdir ( parents =
    d = dict(d, updated_at=now().isoformat())  # info: set d
    tmp = STATE.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, STATE)  # info: os . replace ( tmp , STATE )
    return d  # info: return d


# ====================================================
# SECTION: function _seed
# What it does:  seed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _seed(kind: str, day: str) -> dict:  # info: def _seed
    m = META[kind]  # info: set m
    return {"status": "pending", "scheduled_at": f"{day}T{m['hour']:02d}:{m['minute']:02d}:00", **m,  # info: return { "status" : "pending" , "scheduled_at" :
            "completed_at": None, "error": None, "started_at": None}  # info: "completed_at" : None , "error" : None ,


# ====================================================
# SECTION: function _expire
# What it does:  expire.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _expire(prior: dict) -> dict:  # G1 _expire_prior_day
    for kind, row in (prior.get("slots") or {}).items():  # info: for kind , row in ( prior .
        if not isinstance(row, dict) or row.get("status") in DONEISH:  # info: if not isinstance ( row , dict )
            continue  # info: continue
        if row.get("mandatory"):  # info: if row . get ( "mandatory" ) :
            row.update(status="missed", error=row.get("error") or "unfinished_after_midnight", completed_at=now().isoformat())  # info: row . update ( status = "missed" ,
        else:  # info: else :
            row.update(status="skipped_optional", completed_at=now().isoformat())  # info: row . update ( status = "skipped_optional" ,
    return prior  # info: return prior


# ====================================================
# SECTION: function _written_today
# What it does:  written today.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _written_today(kind: str, t: datetime) -> str | None:  # info: def _written_today
    f = REPORTS / f"{kind}_report_current.md"  # info: set f
    if not f.is_file():  # info: if not f . is_file ( ) :
        return None  # info: return None
    mt = datetime.fromtimestamp(f.stat().st_mtime, HST)  # info: set mt
    due = t.replace(hour=META[kind]["hour"], minute=META[kind]["minute"], second=0)  # info: set due
    return mt.isoformat(timespec="seconds") if mt.date() == t.date() and mt >= due else None  # info: return mt . isoformat ( timespec = "seconds"


# ====================================================
# SECTION: function ensure_today
# What it does: ensure today.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_today(t: datetime) -> dict:  # info: def ensure_today
    day = t.strftime("%Y-%m-%d")  # info: set day
    d = _read()  # info: set d
    if d.get("day") and d["day"] != day:  # info: if d . get ( "day" ) and
        hist = d.get("history") if isinstance(d.get("history"), dict) else {}  # info: set hist
        hist[d["day"]] = {"day": d["day"], "slots": _expire(deepcopy(d)).get("slots") or {}}  # info: hist [ d [ "day" ] ] =
        for old in sorted(hist)[:-14]:  # info: for old in sorted ( hist ) [
            hist.pop(old, None)  # info: hist . pop ( old , None )
        d = {"day": day, "slots": {}, "history": hist}  # info: set d
    d.setdefault("day", day)  # info: d . setdefault ( "day" , day )
    d.setdefault("history", {})  # info: d . setdefault ( "history" , { }
    slots = d.setdefault("slots", {})  # info: set slots
    for kind in SLOTS:  # info: for kind in SLOTS :
        if not isinstance(slots.get(kind), dict):  # info: if not isinstance ( slots . get (
            slots[kind] = _seed(kind, day)  # info: slots [ kind ] = _seed ( kind
    return d  # info: return d


# ====================================================
# SECTION: function mark_due
# What it does: mark due.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mark_due(t: datetime) -> dict:  # info: def mark_due
    d = ensure_today(t)  # info: set d
    for kind in SLOTS:  # info: for kind in SLOTS :
        row = d["slots"][kind]  # info: set row
        seen = _written_today(kind, t)  # info: set seen
        if seen and row["status"] != "done":  # info: if seen and row [ "status" ] !=
            row.update(status="done", completed_at=seen, error=None)  # info: row . update ( status = "done" ,
            continue  # info: continue
        if row["status"] == "pending" and t >= t.replace(hour=row["hour"], minute=row["minute"], second=0):  # info: if row [ "status" ] == "pending" and
            row.update(status="due", marked_due_at=t.isoformat())  # info: row . update ( status = "due" ,
    return _write(d)  # info: return _write ( d )


# ====================================================
# SECTION: function next_catchup_slot
# What it does: next catchup slot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def next_catchup_slot(d: dict, t: datetime) -> str | None:  # info: def next_catchup_slot
    c = [(r["scheduled_at"], k) for k, r in d["slots"].items() if r.get("mandatory") and r.get("catch_up_allowed")  # info: set c
         and catchup_window_open(k, t) and r.get("status") in RETRYABLE]  # info: call and
    return sorted(c)[0][1] if c else None  # info: return sorted ( c ) [ 0 ]


# ====================================================
# SECTION: function run_due
# What it does: run due.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_due(t: datetime, voice: bool) -> dict:  # info: def run_due
    d = mark_due(t)  # info: set d
    kind = next_catchup_slot(d, t)  # info: set kind
    if not kind:  # info: if not kind :
        return {"ok": True, "skipped": True, "detail": "nothing_due", "slots": {k: r["status"] for k, r in d["slots"].items()}}  # info: return { "ok" : True , "skipped" :
    d["slots"][kind].update(status="running", started_at=now().isoformat())  # info: d [ "slots" ] [ kind ] .
    _write(d)  # info: call _write
    cmd = ["nice", "-n", "10", sys.executable, str(VOICE), f"{kind}_report"] + ([] if voice else ["--no-voice"])  # info: set cmd
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)  # info: set p
    ok = p.returncode == 0  # info: set ok
    d["slots"][kind].update(status="done" if ok else "failed", completed_at=now().isoformat() if ok else None,  # info: d [ "slots" ] [ kind ] .
                            error=None if ok else (p.stderr or p.stdout)[-400:], catch_up=True)  # info: set error
    _write(d)  # info: call _write
    return {"ok": ok, "kind": kind, "rc": p.returncode, "voice": voice, "out": (p.stdout or "").strip()[-400:]}  # info: return { "ok" : ok , "kind" :


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if len(sys.argv) < 2 or sys.argv[1] not in ("status", "run-due"):  # info: if len ( sys . argv ) <
        print(json.dumps({"ok": False, "detail": "usage: report_board.py status | run-due [--voice]"}))  # info: call print
        return 2  # info: return 2
    t = now()  # info: set t
    if sys.argv[1] == "status":  # info: if sys . argv [ 1 ] ==
        d = mark_due(t)  # info: set d
        print(json.dumps({"ok": True, "day": d["day"], "path": str(STATE),  # info: call print
                          "slots": {k: {"status": r["status"], "scheduled_at": r["scheduled_at"]} for k, r in d["slots"].items()},  # info: "slots" : { k : { "status" :
                          "next_catchup": next_catchup_slot(d, t)}))  # info: "next_catchup" : next_catchup_slot ( d , t )
        return 0  # info: return 0
    res = run_due(t, "--voice" in sys.argv)  # info: set res
    print(json.dumps(res, ensure_ascii=False))  # info: call print
    return 0 if res.get("ok") else 1  # info: return 0 if res . get ( "ok"


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
