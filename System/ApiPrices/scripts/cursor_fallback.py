# ==============================================================================
# FILE: System/ApiPrices/scripts/cursor_fallback.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Cursor ask-mode fallback. Package ApiPrices.

One job at a time. Caps: 2 per HST day, 6 hours between jobs.
Runs only when RR_API_SPEND=1 and may_spend('cursor') is true.
Stores text under Database System/ApiPrices/fallback/. Does not write reports.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

import api_ledger  # info: import api_ledger
import envload  # info: import envload

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
MAX_PER_DAY = 2  # info: set MAX_PER_DAY
MIN_HOURS = 6  # info: set MIN_HOURS


# ====================================================
# SECTION: function _queue_path
# What it does:  queue path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _queue_path() -> Path:  # info: def _queue_path
    return api_ledger.data_dir() / "cursor-fallback-queue.json"  # info: return api_ledger . data_dir ( ) / "cursor-fallback-queue.json"


# ====================================================
# SECTION: function _budget_path
# What it does:  budget path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _budget_path() -> Path:  # info: def _budget_path
    return api_ledger.data_dir() / "cursor-fallback.json"  # info: return api_ledger . data_dir ( ) / "cursor-fallback.json"


# ====================================================
# SECTION: function _fallback_dir
# What it does:  fallback dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fallback_dir() -> Path:  # info: def _fallback_dir
    return api_ledger.data_dir() / "fallback"  # info: return api_ledger . data_dir ( ) / "fallback"


# ====================================================
# SECTION: function _load
# What it does:  load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load(path: Path, default: Any) -> Any:  # info: def _load
    if not path.is_file():  # info: if not path . is_file ( ) :
        return default  # info: return default
    try:  # info: try :
        return json.loads(path.read_text(encoding="utf-8"))  # info: return json . loads ( path . read_text
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return default  # info: return default


# ====================================================
# SECTION: function _save
# What it does:  save.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _save(path: Path, data: Any) -> None:  # info: def _save
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps (


# ====================================================
# SECTION: function enqueue
# What it does: enqueue.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def enqueue(kind: str, system: str, user: str, *, source_hash: str) -> None:  # info: def enqueue
    q = _load(_queue_path(), {"jobs": []})  # info: set q
    jobs = [j for j in q.get("jobs") or [] if not (j.get("kind") == kind and j.get("hash") == source_hash)]  # info: set jobs
    jobs.append(  # info: jobs . append (
        {  # info: {
            "kind": kind,  # info: "kind" : kind ,
            "hash": source_hash,  # info: "hash" : source_hash ,
            "system": system[:1500],  # info: "system" : system [ : 1500 ] ,
            "user": user[:6000],  # info: "user" : user [ : 6000 ] ,
            "queued_at": datetime.now(timezone.utc).isoformat(),  # info: "queued_at" : datetime . now ( timezone .
        }  # info: }
    )  # info: )
    q["jobs"] = jobs[-8:]  # info: q [ "jobs" ] = jobs [ -
    _save(_queue_path(), q)  # info: call _save


# ====================================================
# SECTION: function pending
# What it does: pending.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pending() -> list[dict[str, Any]]:  # info: def pending
    return list(_load(_queue_path(), {"jobs": []}).get("jobs") or [])  # info: return list ( _load ( _queue_path ( )


# ====================================================
# SECTION: function _budget_ok
# What it does:  budget ok.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _budget_ok() -> bool:  # info: def _budget_ok
    st = _load(_budget_path(), {})  # info: set st
    today = datetime.now(HST).strftime("%Y-%m-%d")  # info: set today
    if st.get("date") != today:  # info: if st . get ( "date" ) !=
        return True  # info: return True
    if int(st.get("count") or 0) >= MAX_PER_DAY:  # info: if int ( st . get ( "count"
        return False  # info: return False
    last = st.get("last_at")  # info: set last
    if last:  # info: if last :
        try:  # info: try :
            last_dt = datetime.fromisoformat(str(last))  # info: set last_dt
            if datetime.now(timezone.utc) - last_dt < timedelta(hours=MIN_HOURS):  # info: if datetime . now ( timezone . utc
                return False  # info: return False
        except ValueError:  # info: except ValueError :
            pass  # info: pass
    return True  # info: return True


# ====================================================
# SECTION: function _note_run
# What it does:  note run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _note_run() -> None:  # info: def _note_run
    today = datetime.now(HST).strftime("%Y-%m-%d")  # info: set today
    st = _load(_budget_path(), {})  # info: set st
    count = int(st.get("count") or 0) + 1 if st.get("date") == today else 1  # info: set count
    _save(  # info: call _save
        _budget_path(),  # info: call _budget_path
        {"date": today, "count": count, "last_at": datetime.now(timezone.utc).isoformat()},  # info: { "date" : today , "count" : count
    )  # info: )


# ====================================================
# SECTION: function _pop
# What it does:  pop.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pop(kind: str, source_hash: str) -> None:  # info: def _pop
    q = _load(_queue_path(), {"jobs": []})  # info: set q
    q["jobs"] = [j for j in q.get("jobs") or [] if not (j.get("kind") == kind and j.get("hash") == source_hash)]  # info: q [ "jobs" ] = [ j for
    _save(_queue_path(), q)  # info: call _save


# ====================================================
# SECTION: function _blocked
# What it does:  blocked.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _blocked() -> str | None:  # info: def _blocked
    if not api_ledger.spend_gate_open():  # info: if not api_ledger . spend_gate_open ( ) :
        return "rr_api_spend_off"  # info: return "rr_api_spend_off"
    ok, why = api_ledger.may_spend("cursor")  # info: ok , why = api_ledger . may_spend (
    if not ok:  # info: if not ok :
        return why  # info: return why
    if not envload.key_set("CURSOR_API_KEY"):  # info: if not envload . key_set ( "CURSOR_API_KEY" )
        return "no_key"  # info: return "no_key"
    if not _budget_ok():  # info: if not _budget_ok ( ) :
        return "budget"  # info: return "budget"
    return None  # info: return None


# ====================================================
# SECTION: function ask
# What it does: ask.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ask(system: str, user: str) -> str | None:  # info: def ask
    why = _blocked()  # info: set why
    if why:  # info: if why :
        return None  # info: return None
    prompt = (  # info: set prompt
        f"{system.strip()}\n\n"  # info: f" { system . strip ( ) }
        "Use only the source text below. Do not search the repository. "  # info: "Use only the source text below. Do not search the repository. "
        "Do not call tools. Reply with the report text only.\n\n"  # info: "Do not call tools. Reply with the report text only.\n\n"
        f"{user.strip()}"  # info: f" { user . strip ( ) }
    )  # info: )
    model = api_ledger.DEFAULT_CURSOR_MODEL  # info: set model
    if "[" not in model:  # info: if "[" not in model :
        model = f"{model}[fast=false]"  # info: set model
    envload.load_env()  # info: envload . load_env ( )
    key = (os.environ.get("CURSOR_API_KEY") or "").strip()  # info: set key
    cmd = [  # info: set cmd
        "cursor",  # info: "cursor" ,
        "agent",  # info: "agent" ,
        "-p",  # info: "-p" ,
        "--mode",  # info: "--mode" ,
        "ask",  # info: "ask" ,
        "--output-format",  # info: "--output-format" ,
        "text",  # info: "text" ,
        "--model",  # info: "--model" ,
        model,  # info: model ,
        prompt,  # info: prompt ,
    ]  # info: ]
    env = os.environ.copy()  # info: set env
    env["CURSOR_API_KEY"] = key  # info: env [ "CURSOR_API_KEY" ] = key
    api_ledger.note_spend()  # info: api_ledger . note_spend ( )
    try:  # info: try :
        proc = subprocess.run(  # info: set proc
            cmd,  # info: cmd ,
            cwd=str(api_ledger.data_dir()),  # info: set cwd
            env=env,  # info: set env
            capture_output=True,  # info: set capture_output
            text=True,  # info: set text
            timeout=180,  # info: set timeout
        )  # info: )
    except (FileNotFoundError, subprocess.TimeoutExpired):  # info: except ( FileNotFoundError , subprocess . TimeoutExpired )
        return None  # info: return None
    _note_run()  # info: call _note_run
    text = (proc.stdout or "").strip()  # info: set text
    if proc.returncode != 0 or not text:  # info: if proc . returncode != 0 or not
        return None  # info: return None
    lines = [ln for ln in text.splitlines() if not ln.startswith("Cursor ") or len(ln) > 40]  # info: set lines
    out = "\n".join(lines).strip()  # info: set out
    return out[:4000] if out else None  # info: return out [ : 4000 ] if out


# ====================================================
# SECTION: function drain_one
# What it does: Run at most one queued job. Text stays in the Database fallback folder.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def drain_one() -> dict[str, Any] | None:  # info: def drain_one
    """Run at most one queued job. Text stays in the Database fallback folder."""  # info: """Run at most one queued job. Text stays in the Database fallback folder."""
    if _blocked():  # info: if _blocked ( ) :
        return None  # info: return None
    jobs = pending()  # info: set jobs
    if not jobs:  # info: if not jobs :
        return None  # info: return None
    order = {"kilauea": 0, "summary": 1, "morning": 2}  # info: set order
    jobs.sort(key=lambda j: order.get(j.get("kind") or "", 9))  # info: jobs . sort ( key = lambda j
    job = jobs[0]  # info: set job
    text = ask(job.get("system") or "", job.get("user") or "")  # info: set text
    if not text:  # info: if not text :
        return None  # info: return None
    kind = str(job.get("kind") or "summary")  # info: set kind
    _pop(kind, job.get("hash") or "")  # info: call _pop
    stamp = datetime.now(HST).strftime("%Y-%m-%dT%H%M")  # info: set stamp
    dest = _fallback_dir() / f"{kind}-cursor-{stamp}.md"  # info: set dest
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir ( parents =
    dest.write_text(text, encoding="utf-8")  # info: dest . write_text ( text , encoding =
    api_ledger.record_usage("cursor", model=api_ledger.DEFAULT_CURSOR_MODEL, surface="cursor.ask", note=kind)  # info: api_ledger . record_usage ( "cursor" , model =
    return {"kind": kind, "path": str(dest), "text": text}  # info: return { "kind" : kind , "path" :
