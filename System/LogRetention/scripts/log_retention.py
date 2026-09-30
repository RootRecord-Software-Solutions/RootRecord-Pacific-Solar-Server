# ==============================================================================
# FILE: System/LogRetention/scripts/log_retention.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""log_retention.py — log retention (WO-MIG-41).

Same shape as weather retention: --dry-run is the default and changes no log
file. --apply moves aged logs. This script never unlinks, rmdirs, or rmtrees.

Default root:  2 - RootRecord-Database/Logs/
Archive:       2 - RootRecord-Database/Archive/Previous-Datasets/Logs-<YYYYMM>/
Reports:       2 - RootRecord-Database/Logs/System/LogRetention/
State:         2 - RootRecord-Database/System/LogRetention/log-retention.json

--apply on the live Logs root refuses to run unless RR_LOG_RETENTION_APPLY=1.
The scheduled job stays --dry-run.
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import fcntl  # info: import fcntl
import json  # info: import json
import os  # info: import os
import re  # info: import re
import shutil  # info: import shutil
import sys  # info: import sys
from datetime import date, datetime  # info: from datetime import date , datetime
from pathlib import Path  # info: from pathlib import Path

DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DB
LIVE_LOGS = DB / "Logs"  # info: set LIVE_LOGS
LIVE_ARCHIVE = DB / "Archive" / "Previous-Datasets"  # info: set LIVE_ARCHIVE
LIVE_REPORT_DIR = LIVE_LOGS / "System" / "LogRetention"  # info: set LIVE_REPORT_DIR
LIVE_STATE = DB / "System" / "LogRetention" / "log-retention.json"  # info: set LIVE_STATE
KEEP_DAYS = 7  # info: set KEEP_DAYS
MAX_LIVE_BYTES = 10 * 1024 * 1024  # info: set MAX_LIVE_BYTES
LOG_KEEP = 5  # info: set LOG_KEEP
DATE_IN_NAME = re.compile(r"(?:^|[^0-9])(\d{4}-\d{2}-\d{2})(?:[^0-9]|$)")  # info: set DATE_IN_NAME
ROTATION = re.compile(r"\.log\.\d+$", re.I)  # info: set ROTATION
SKIP_DIRS = {"__pycache__", "leveldb", ".config"}  # info: set SKIP_DIRS


# ====================================================
# SECTION: function name_day
# What it does: name day.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def name_day(name: str) -> date | None:  # info: def name_day
    m = DATE_IN_NAME.search(name)  # info: set m
    if not m:  # info: if not m :
        return None  # info: return None
    try:  # info: try :
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()  # info: return datetime . strptime ( m . group
    except ValueError:  # info: except ValueError :
        return None  # info: return None


# ====================================================
# SECTION: function is_log_name
# What it does: is log name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_log_name(name: str) -> bool:  # info: def is_log_name
    n = name.lower()  # info: set n
    if n.endswith(".jsonl"):  # info: if n . endswith ( ".jsonl" ) :
        return False  # info: return False
    if n.endswith(".log") or n.endswith(".out") or n.endswith(".log.gz") or n.endswith(".log.old"):  # info: if n . endswith ( ".log" ) or
        return True  # info: return True
    return bool(ROTATION.search(n))  # info: return bool ( ROTATION . search ( n


# ====================================================
# SECTION: function is_rotation
# What it does: is rotation.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_rotation(name: str) -> bool:  # info: def is_rotation
    n = name.lower()  # info: set n
    return bool(ROTATION.search(n) or n.endswith(".log.gz") or n.endswith(".log.old"))  # info: return bool ( ROTATION . search ( n


# ====================================================
# SECTION: function is_live_writer
# What it does: is live writer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_live_writer(name: str) -> bool:  # info: def is_live_writer
    n = name.lower()  # info: set n
    if "_current.log" in n or n == "latest.log":  # info: if "_current.log" in n or n == "latest.log"
        return True  # info: return True
    if name_day(name) is not None or is_rotation(name):  # info: if name_day ( name ) is not None
        return False  # info: return False
    return n.endswith(".log") or n.endswith(".out")  # info: return n . endswith ( ".log" ) or


# ====================================================
# SECTION: function skip_dir
# What it does: skip dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def skip_dir(name: str) -> bool:  # info: def skip_dir
    return name.lower() in SKIP_DIRS or "local storage" in name.lower()  # info: return name . lower ( ) in SKIP_DIRS


# ====================================================
# SECTION: function file_day
# What it does: file day.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def file_day(path: Path) -> date | None:  # info: def file_day
    named = name_day(path.name)  # info: set named
    if named is not None:  # info: if named is not None :
        return named  # info: return named
    try:  # info: try :
        return datetime.fromtimestamp(path.stat().st_mtime).date()  # info: return datetime . fromtimestamp ( path . stat
    except OSError:  # info: except OSError :
        return None  # info: return None


# ====================================================
# SECTION: function age_days
# What it does: age days.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def age_days(path: Path, today: date) -> int | None:  # info: def age_days
    day = file_day(path)  # info: set day
    if day is None:  # info: if day is None :
        return None  # info: return None
    return (today - day).days  # info: return ( today - day ) . days


# ====================================================
# SECTION: function dest_for
# What it does: dest for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def dest_for(src: Path, root: Path, archive_root: Path, when: date) -> Path:  # info: def dest_for
    return archive_root / f"Logs-{when.strftime('%Y%m')}" / src.relative_to(root)  # info: return archive_root / f" Logs- { when .


# ====================================================
# SECTION: function move_file
# What it does: Move src to dest. Content stays on disk. Never unlinks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def move_file(src: Path, dest: Path) -> Path:  # info: def move_file
    """Move src to dest. Content stays on disk. Never unlinks."""  # info: """Move src to dest. Content stays on disk. Never unlinks."""
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir ( parents =
    if dest.exists():  # info: if dest . exists ( ) :
        dest = dest.with_name(dest.name + f".dup-{datetime.now():%Y%m%d%H%M%S}")  # info: set dest
    shutil.move(str(src), str(dest))  # info: shutil . move ( str ( src )
    return dest  # info: return dest


# ====================================================
# SECTION: function plan
# What it does: plan.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def plan(root: Path, archive_root: Path, today: date) -> dict:  # info: def plan
    would_move: list[dict] = []  # info: set would_move
    would_rotate: list[dict] = []  # info: set would_rotate
    seen: set[Path] = set()  # info: set seen
    scanned = 0  # info: set scanned
    if not root.is_dir():  # info: if not root . is_dir ( ) :
        return {"scanned": 0, "would_move": [], "would_rotate": [], "would_delete": 0}  # info: return { "scanned" : 0 , "would_move" :

    for dirpath, dirs, files in os.walk(root, followlinks=False):  # info: for dirpath , dirs , files in os
        dirs[:] = [d for d in dirs if not skip_dir(d)]  # info: dirs [ : ] = [ d for
        for fname in files:  # info: for fname in files :
            path = Path(dirpath) / fname  # info: set path
            if path.is_symlink() or not path.is_file():  # info: if path . is_symlink ( ) or not
                continue  # info: continue
            if skip_dir(path.name) or "local storage" in str(path).lower():  # info: if skip_dir ( path . name ) or
                continue  # info: continue
            if not is_log_name(path.name):  # info: if not is_log_name ( path . name )
                continue  # info: continue
            scanned += 1  # info: set scanned
            if is_live_writer(path.name):  # info: if is_live_writer ( path . name ) :
                try:  # info: try :
                    size = path.stat().st_size  # info: set size
                except OSError:  # info: except OSError :
                    continue  # info: continue
                if path.name.lower().endswith(".log") and size >= MAX_LIVE_BYTES:  # info: if path . name . lower ( )
                    oldest = path.with_name(f"{path.name}.{LOG_KEEP}")  # info: set oldest
                    oldest_move = None  # info: set oldest_move
                    if oldest.is_file() and not oldest.is_symlink():  # info: if oldest . is_file ( ) and not
                        when = file_day(oldest) or today  # info: set when
                        oldest_move = str(dest_for(oldest, root, archive_root, when))  # info: set oldest_move
                        if oldest not in seen:  # info: if oldest not in seen :
                            seen.add(oldest)  # info: seen . add ( oldest )
                            would_move.append({  # info: would_move . append ( {
                                "src": str(oldest),  # info: "src" : str ( oldest ) ,
                                "dest": oldest_move,  # info: "dest" : oldest_move ,
                                "bytes": oldest.stat().st_size,  # info: "bytes" : oldest . stat ( ) .
                                "age_days": age_days(oldest, today),  # info: "age_days" : age_days ( oldest , today )
                                "why": "oldest rotation (10 MB x 5)",  # info: "why" : "oldest rotation (10 MB x 5)" ,
                            })  # info: } )
                    would_rotate.append({  # info: would_rotate . append ( {
                        "src": str(path),  # info: "src" : str ( path ) ,
                        "bytes": size,  # info: "bytes" : size ,
                        "oldest": str(oldest) if oldest_move else None,  # info: "oldest" : str ( oldest ) if oldest_move
                    })  # info: } )
                continue  # info: continue
            aged = age_days(path, today)  # info: set aged
            if aged is None or aged < KEEP_DAYS:  # info: if aged is None or aged < KEEP_DAYS
                continue  # info: continue
            if not (name_day(path.name) is not None or is_rotation(path.name)):  # info: if not ( name_day ( path . name
                continue  # info: continue
            if path in seen:  # info: if path in seen :
                continue  # info: continue
            seen.add(path)  # info: seen . add ( path )
            when = file_day(path) or today  # info: set when
            try:  # info: try :
                size = path.stat().st_size  # info: set size
            except OSError:  # info: except OSError :
                size = 0  # info: set size
            would_move.append({  # info: would_move . append ( {
                "src": str(path),  # info: "src" : str ( path ) ,
                "dest": str(dest_for(path, root, archive_root, when)),  # info: "dest" : str ( dest_for ( path ,
                "bytes": size,  # info: "bytes" : size ,
                "age_days": aged,  # info: "age_days" : aged ,
                "why": "older than 7 days",  # info: "why" : "older than 7 days" ,
            })  # info: } )
    return {  # info: return {
        "scanned": scanned,  # info: "scanned" : scanned ,
        "would_move": would_move,  # info: "would_move" : would_move ,
        "would_rotate": would_rotate,  # info: "would_rotate" : would_rotate ,
        "would_delete": 0,  # info: "would_delete" : 0 ,
    }  # info: }


# ====================================================
# SECTION: function apply_plan
# What it does: apply plan.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_plan(root: Path, archive_root: Path, p: dict) -> list[str]:  # info: def apply_plan
    actions: list[str] = []  # info: set actions
    for item in p["would_move"]:  # info: for item in p [ "would_move" ] :
        src, dest = Path(item["src"]), Path(item["dest"])  # info: src , dest = Path ( item [
        if not src.is_file() or src.is_symlink():  # info: if not src . is_file ( ) or
            continue  # info: continue
        landed = move_file(src, dest)  # info: set landed
        actions.append(f"moved {src} -> {landed}")  # info: actions . append ( f" moved { src
    for item in p["would_rotate"]:  # info: for item in p [ "would_rotate" ] :
        live = Path(item["src"])  # info: set live
        if not live.is_file() or live.is_symlink():  # info: if not live . is_file ( ) or
            continue  # info: continue
        try:  # info: try :
            if live.stat().st_size < MAX_LIVE_BYTES:  # info: if live . stat ( ) . st_size
                continue  # info: continue
        except OSError:  # info: except OSError :
            continue  # info: continue
        oldest = live.with_name(f"{live.name}.{LOG_KEEP}")  # info: set oldest
        if oldest.is_file() and not oldest.is_symlink():  # info: if oldest . is_file ( ) and not
            when = file_day(oldest) or datetime.now().astimezone().date()  # info: set when
            landed = move_file(oldest, dest_for(oldest, root, archive_root, when))  # info: set landed
            actions.append(f"moved oldest rotation {oldest} -> {landed}")  # info: actions . append ( f" moved oldest rotation { oldest
        for i in range(LOG_KEEP - 1, 0, -1):  # info: for i in range ( LOG_KEEP - 1
            src = live.with_name(f"{live.name}.{i}")  # info: set src
            if src.is_file() and not src.is_symlink():  # info: if src . is_file ( ) and not
                os.replace(src, live.with_name(f"{live.name}.{i + 1}"))  # info: os . replace ( src , live .
        shutil.copy2(live, live.with_name(f"{live.name}.1"))  # info: shutil . copy2 ( live , live .
        with live.open("r+b") as fh:  # info: with live . open ( "r+b" ) as
            fh.truncate(0)  # info: fh . truncate ( 0 )
        actions.append(f"copytruncated {live.name} (kept the file)")  # info: actions . append ( f" copytruncated { live
    return actions  # info: return actions


# ====================================================
# SECTION: function render
# What it does: render.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render(p: dict, mode: str, root: Path, archive_root: Path, now: datetime, actions: list[str]) -> str:  # info: def render
    move_bytes = sum(m["bytes"] for m in p["would_move"])  # info: set move_bytes
    lines = [  # info: set lines
        f"# Log retention — {mode.upper()} — {now.isoformat(timespec='seconds')}",
        "",  # info: "" ,
        f"Root: `{root}`",  # info: f" Root: ` { root } ` " ,
        f"Archive: `{archive_root}/Logs-<YYYYMM>/` (move, never delete).",  # info: f" Archive: ` { archive_root } /Logs-<YYYYMM>/` (move, never delete). " ,
        f"Scanned log files: {p['scanned']}.",  # info: f" Scanned log files: { p [ 'scanned' ] }
        f"**Would move:** {len(p['would_move'])} files, {move_bytes} bytes.",  # info: f" **Would move:** { len ( p [ 'would_move'
        f"**Would copytruncate:** {len(p['would_rotate'])} live logs over 10 MB.",  # info: f" **Would copytruncate:** { len ( p [ 'would_rotate'
        "**Would delete:** 0.",  # info: "**Would delete:** 0." ,
        "",  # info: "" ,
    ]  # info: ]
    if p["would_move"]:  # info: if p [ "would_move" ] :
        lines.append("## Move candidates")
        lines.append("")  # info: lines . append ( "" )
        for m in p["would_move"][:200]:  # info: for m in p [ "would_move" ] [
            lines.append(f"- `{m['src']}` ({m['bytes']} B, age {m['age_days']} d, {m['why']}) → `{m['dest']}`")  # info: lines . append ( f" - ` { m
        if len(p["would_move"]) > 200:  # info: if len ( p [ "would_move" ] )
            lines.append(f"- … {len(p['would_move']) - 200} more")  # info: lines . append ( f" - … { len
        lines.append("")  # info: lines . append ( "" )
    if p["would_rotate"]:  # info: if p [ "would_rotate" ] :
        lines.append("## Copytruncate candidates")
        lines.append("")  # info: lines . append ( "" )
        for r in p["would_rotate"][:50]:  # info: for r in p [ "would_rotate" ] [
            lines.append(f"- `{r['src']}` ({r['bytes']} B)")  # info: lines . append ( f" - ` { r
        lines.append("")  # info: lines . append ( "" )
    if actions:  # info: if actions :
        lines.append("## Actions")
        lines.append("")  # info: lines . append ( "" )
        lines.extend(f"- {a}" for a in actions)  # info: lines . extend ( f" - { a
        lines.append("")  # info: lines . append ( "" )
    return "\n".join(lines)  # info: return "\n" . join ( lines )


# ====================================================
# SECTION: function write_state
# What it does: write state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_state(path: Path, payload: dict) -> None:  # info: def write_state
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps (


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser(description="Log retention (dry-run by default)")  # info: set ap
    g = ap.add_mutually_exclusive_group()  # info: set g
    g.add_argument("--dry-run", action="store_true", help="default: read-only report")  # info: g . add_argument ( "--dry-run" , action =
    g.add_argument("--apply", action="store_true", help="move logs past 7 days (live root needs RR_LOG_RETENTION_APPLY=1)")  # info: g . add_argument ( "--apply" , action =
    ap.add_argument("--root", default="", help="scan root (default: Database Logs)")  # info: ap . add_argument ( "--root" , default =
    ap.add_argument("--archive", default="", help="archive root (default: Archive/Previous-Datasets)")  # info: ap . add_argument ( "--archive" , default =
    ap.add_argument("--report", default="")  # info: ap . add_argument ( "--report" , default =
    ap.add_argument("--no-save", action="store_true")  # info: ap . add_argument ( "--no-save" , action =
    a = ap.parse_args()  # info: set a
    mode = "apply" if a.apply else "dry-run"  # info: set mode
    root = Path(a.root).expanduser() if a.root else LIVE_LOGS  # info: set root
    archive_root = Path(a.archive).expanduser() if a.archive else LIVE_ARCHIVE  # info: set archive_root
    root = root.resolve()  # info: set root
    archive_root = archive_root.resolve()  # info: set archive_root
    if mode == "apply" and root == LIVE_LOGS.resolve() and os.environ.get("RR_LOG_RETENTION_APPLY") != "1":  # info: if mode == "apply" and root == LIVE_LOGS
        print("refusing --apply on live Logs without RR_LOG_RETENTION_APPLY=1", file=sys.stderr)  # info: call print
        return 2  # info: return 2
    if not root.is_dir():  # info: if not root . is_dir ( ) :
        print(f"No log root: {root}", file=sys.stderr)  # info: call print
        return 1  # info: return 1
    lock = open("/tmp/log-retention.lock", "w")  # info: set lock
    try:  # info: try :
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # info: fcntl . flock ( lock , fcntl .
    except BlockingIOError:  # info: except BlockingIOError :
        print("[skip] another log-retention run holds the lock")  # info: call print
        return 0  # info: return 0
    now = datetime.now().astimezone()  # info: set now
    planned = plan(root, archive_root, now.date())  # info: set planned
    actions = apply_plan(root, archive_root, planned) if mode == "apply" else []  # info: set actions
    text = render(planned, mode, root, archive_root, now, actions)  # info: set text
    print(text)  # info: call print
    if not a.no_save:  # info: if not a . no_save :
        if a.report:  # info: if a . report :
            out = Path(a.report)  # info: set out
        elif root == LIVE_LOGS.resolve():  # info: elif root == LIVE_LOGS . resolve ( )
            out = LIVE_REPORT_DIR / f"log-retention_{mode}_{now:%Y-%m-%d_%H%M}.md"  # info: set out
        else:  # info: else :
            out = root / "System" / "LogRetention" / f"log-retention_{mode}_{now:%Y-%m-%d_%H%M}.md"  # info: set out
        out.parent.mkdir(parents=True, exist_ok=True)  # info: out . parent . mkdir ( parents =
        out.write_text(text + "\n", encoding="utf-8")  # info: out . write_text ( text + "\n" ,
        print(f"[saved] {out}")  # info: call print
        state_path = LIVE_STATE if root == LIVE_LOGS.resolve() else root / "log-retention.json"  # info: set state_path
        write_state(state_path, {  # info: call write_state
            "ok": True,  # info: "ok" : True ,
            "mode": mode,  # info: "mode" : mode ,
            "ts": now.isoformat(timespec="seconds"),  # info: "ts" : now . isoformat ( timespec =
            "root": str(root),  # info: "root" : str ( root ) ,
            "archive": str(archive_root),  # info: "archive" : str ( archive_root ) ,
            "scanned": planned["scanned"],  # info: "scanned" : planned [ "scanned" ] ,
            "would_delete": 0,  # info: "would_delete" : 0 ,
            "would_move_count": len(planned["would_move"]),  # info: "would_move_count" : len ( planned [ "would_move" ]
            "would_move": [m["src"] for m in planned["would_move"]],  # info: "would_move" : [ m [ "src" ] for
            "would_rotate": [r["src"] for r in planned["would_rotate"]],  # info: "would_rotate" : [ r [ "src" ] for
            "actions": actions,  # info: "actions" : actions ,
        })  # info: } )
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
