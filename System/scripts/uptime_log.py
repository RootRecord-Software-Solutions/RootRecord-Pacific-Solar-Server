# ==============================================================================
# FILE: System/scripts/uptime_log.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import time  # info: import time
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
DIR = DB / "System" / "uptime"  # info: set DIR
PATH, MARKER = DIR / "uptime-events.jsonl", DIR / "uptime-last.json"  # info: PATH , MARKER = DIR / "uptime-events.jsonl" ,
KEEP, GAP_S = 400, 180  # info: KEEP , GAP_S = 400 , 180


# ====================================================
# SECTION: function _now_iso
# What it does:  now iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now_iso() -> str:  # info: def _now_iso
    return datetime.now(timezone.utc).isoformat()  # info: return datetime . now ( timezone . utc


# ====================================================
# SECTION: function _boot_uptime_s
# What it does:  boot uptime s.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _boot_uptime_s() -> int:  # info: def _boot_uptime_s
    with open("/proc/uptime") as f:  # info: with open ( "/proc/uptime" ) as f :
        return int(float(f.read().split()[0]))  # info: return int ( float ( f . read


# ====================================================
# SECTION: function _boot_id
# What it does:  boot id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _boot_id() -> str:  # info: def _boot_id
    try:  # info: try :
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()  # info: return Path ( "/proc/sys/kernel/random/boot_id" ) . read_text (
    except OSError:  # info: except OSError :
        return ""  # info: return ""


# ====================================================
# SECTION: function _append
# What it does:  append.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _append(kind: str, **extra) -> None:  # info: def _append
    PATH.parent.mkdir(parents=True, exist_ok=True)  # info: PATH . parent . mkdir ( parents =
    with PATH.open("a", encoding="utf-8") as fh:  # info: with PATH . open ( "a" , encoding
        fh.write(json.dumps({"at": _now_iso(), "kind": kind, **extra}, default=str) + "\n")  # info: fh . write ( json . dumps (
    lines = PATH.read_text(encoding="utf-8", errors="replace").splitlines()  # info: set lines
    if len(lines) > KEEP:  # info: if len ( lines ) > KEEP :
        tmp = PATH.with_name(PATH.name + ".tmp")  # info: set tmp
        tmp.write_text("\n".join(lines[-KEEP:]) + "\n", encoding="utf-8")  # info: tmp . write_text ( "\n" . join (
        os.replace(tmp, PATH)  # info: os . replace ( tmp , PATH )


# ====================================================
# SECTION: function _marker
# What it does:  marker.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _marker() -> dict:  # info: def _marker
    try:  # info: try :
        raw = json.loads(MARKER.read_text(encoding="utf-8"))  # info: set raw
        return raw if isinstance(raw, dict) else {}  # info: return raw if isinstance ( raw , dict
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return {}  # info: return { }


# ====================================================
# SECTION: function _write_marker
# What it does:  write marker.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_marker(payload: dict) -> None:  # info: def _write_marker
    MARKER.parent.mkdir(parents=True, exist_ok=True)  # info: MARKER . parent . mkdir ( parents =
    tmp = MARKER.with_name(MARKER.name + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, MARKER)  # info: os . replace ( tmp , MARKER )


# ====================================================
# SECTION: function tick
# What it does: Heartbeat: stamp presence; log a gap if the desk was gone long enough.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tick() -> dict:  # info: def tick
    """Heartbeat: stamp presence; log a gap if the desk was gone long enough."""  # info: """Heartbeat: stamp presence; log a gap if the desk was gone long enough."""
    now, m, bid = time.time(), _marker(), _boot_id()  # info: now , m , bid = time .
    last = float(m.get("last_tick_epoch") or 0)  # info: set last
    if m.get("boot_id") and bid and bid != m["boot_id"]:  # info: if m . get ( "boot_id" ) and
        _append("boot", boot_uptime_s=_boot_uptime_s())  # info: call _append
    if last and now - last >= GAP_S:  # info: if last and now - last >= GAP_S
        _append("heartbeat_gap", gap_s=int(now - last))  # info: call _append
        _append("desk_up", after_gap_s=int(now - last))  # info: call _append
    m.update(last_tick_at=_now_iso(), last_tick_epoch=now, boot_id=bid)  # info: m . update ( last_tick_at = _now_iso (
    if not m.get("origin_started_at"):  # info: if not m . get ( "origin_started_at" )
        m["origin_started_at"] = _now_iso()  # info: m [ "origin_started_at" ] = _now_iso ( )
        _append("origin_start", inferred=True, boot_uptime_s=_boot_uptime_s())  # info: call _append
    _write_marker(m)  # info: call _write_marker
    return m  # info: return m


# ====================================================
# SECTION: function recent
# What it does: recent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def recent(limit: int = 24) -> list[dict]:  # info: def recent
    try:  # info: try :
        lines = PATH.read_text(encoding="utf-8", errors="replace").splitlines()  # info: set lines
    except OSError:  # info: except OSError :
        return []  # info: return [ ]
    out = []  # info: set out
    for line in lines[-limit:]:  # info: for line in lines [ - limit :
        try:  # info: try :
            row = json.loads(line)  # info: set row
        except ValueError:  # info: except ValueError :
            continue  # info: continue
        if isinstance(row, dict):  # info: if isinstance ( row , dict ) :
            out.append(row)  # info: out . append ( row )
    return out  # info: return out


# ====================================================
# SECTION: function last_return
# What it does: last return.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def last_return() -> dict | None:  # info: def last_return
    return next((r for r in reversed(recent(80)) if r.get("kind") in {"origin_start", "desk_up"}), None)  # info: return next ( ( r for r in


# ====================================================
# SECTION: function facts
# What it does: facts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def facts(*, process_uptime_s: int | None = None) -> dict:  # info: def facts
    m, desk_s = _marker(), None  # info: m , desk_s = _marker ( ) ,
    if m.get("origin_started_at"):  # info: if m . get ( "origin_started_at" ) :
        try:  # info: try :
            desk_s = int((datetime.now(timezone.utc) - datetime.fromisoformat(m["origin_started_at"])).total_seconds())  # info: set desk_s
        except ValueError:  # info: except ValueError :
            desk_s = None  # info: set desk_s
    ret = last_return() or {}  # info: set ret
    return {"process_uptime_s": process_uptime_s, "boot_uptime_s": _boot_uptime_s(),  # info: return { "process_uptime_s" : process_uptime_s , "boot_uptime_s" :
            "desk_uptime_s": desk_s if desk_s is not None else process_uptime_s,  # info: "desk_uptime_s" : desk_s if desk_s is not None
            "origin_started_at": m.get("origin_started_at"), "last_return_at": ret.get("at"),  # info: "origin_started_at" : m . get ( "origin_started_at" )
            "last_return_kind": ret.get("kind"), "recent": recent(12)}  # info: "last_return_kind" : ret . get ( "kind" )


# ====================================================
# SECTION: block if
# What it does: __name__ == '__main__'
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
if __name__ == "__main__":  # info: if __name__ == "__main__" :
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tick"  # info: set cmd
    if cmd == "tick":  # info: if cmd == "tick" :
        tick()  # info: call tick
        print(json.dumps({"ok": True, "facts": {k: v for k, v in facts().items() if k != "recent"}}))  # info: call print
    elif cmd == "recent":  # info: elif cmd == "recent" :
        print(json.dumps(recent(), indent=2))  # info: call print
    else:  # info: else :
        print(json.dumps(facts(), indent=2))  # info: call print
