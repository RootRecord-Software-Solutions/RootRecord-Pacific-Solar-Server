# ==============================================================================
# FILE: Communications/Inbox/scripts/inbox.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Local inbox on the quiet-mode relay hold. No network. No send.

Reads Relay-Inbox JSONL (or --inbox). Does not call getUpdates, Discord, Slack, or Cloudflare.

  inbox.py subscribe [--inbox DIR] [--database DIR]
  inbox.py drain     [--inbox DIR] [--database DIR]
  inbox.py overnight [--database DIR] [--solar-line TEXT]
  inbox.py feedback  [--database DIR] --note TEXT
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import os  # info: import os
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DEFAULT_INBOX = Path(  # info: set DEFAULT_INBOX
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/Relay-Inbox"  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/Relay-Inbox"
)  # info: )
DEFAULT_DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DEFAULT_DATABASE
CURRENT = "relay-inbox_current.jsonl"  # info: set CURRENT


# ====================================================
# SECTION: function database_root
# What it does: database root.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def database_root(arg: str | None) -> Path:  # info: def database_root
    if arg:  # info: if arg :
        return Path(arg)  # info: return Path ( arg )
    env = os.environ.get("RR_DATABASE_ROOT", "").strip()  # info: set env
    return Path(env) if env else DEFAULT_DATABASE  # info: return Path ( env ) if env else


# ====================================================
# SECTION: function data_dir
# What it does: data dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def data_dir(root: Path) -> Path:  # info: def data_dir
    return root / "Communications" / "Inbox"  # info: return root / "Communications" / "Inbox"


# ====================================================
# SECTION: function log_dir
# What it does: log dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_dir(root: Path) -> Path:  # info: def log_dir
    return root / "Logs" / "Communications" / "Inbox"  # info: return root / "Logs" / "Communications" / "Inbox"


# ====================================================
# SECTION: function parse_cmd
# What it does: parse cmd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_cmd(text: str) -> str | None:  # info: def parse_cmd
    raw = str(text or "").strip().lower()  # info: set raw
    if not raw:  # info: if not raw :
        return None  # info: return None
    first = raw.split()[0].split("@", 1)[0]  # info: set first
    if first in {"/start", "/help", "!help"}:  # info: if first in { "/start" , "/help" ,
        return "help" if first != "/start" else "start"  # info: return "help" if first != "/start" else "start"
    if first in {"/subscribe", "!subscribe", "subscribe"}:  # info: if first in { "/subscribe" , "!subscribe" ,
        return "subscribe"  # info: return "subscribe"
    if first in {"/unsubscribe", "!unsubscribe", "unsubscribe"}:  # info: if first in { "/unsubscribe" , "!unsubscribe" ,
        return "unsubscribe"  # info: return "unsubscribe"
    return None  # info: return None


# ====================================================
# SECTION: function load_records
# What it does: load records.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_records(inbox: Path) -> list[dict]:  # info: def load_records
    files = sorted((inbox / "Archive").glob("*/relay-inbox_*.jsonl"))  # info: set files
    files.append(inbox / CURRENT)  # info: files . append ( inbox / CURRENT )
    recs: list[dict] = []  # info: set recs
    for path in files:  # info: for path in files :
        if not path.is_file():  # info: if not path . is_file ( ) :
            continue  # info: continue
        for line in path.read_text(encoding="utf-8").splitlines():  # info: for line in path . read_text ( encoding
            if not line.strip():  # info: if not line . strip ( ) :
                continue  # info: continue
            try:  # info: try :
                recs.append(json.loads(line))  # info: recs . append ( json . loads (
            except json.JSONDecodeError:  # info: except json . JSONDecodeError :
                continue  # info: continue
    recs.sort(key=lambda r: (r.get("ts") or "", r.get("update_id") or 0))  # info: recs . sort ( key = lambda r
    return recs  # info: return recs


# ====================================================
# SECTION: function record_key
# What it does: record key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def record_key(rec: dict) -> str:  # info: def record_key
    return f"{rec.get('chat_id')}:{rec.get('message_id')}"  # info: return f" { rec . get ( 'chat_id'


# ====================================================
# SECTION: function write_private
# What it does: write private.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_private(path: Path, text: str) -> None:  # info: def write_private
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)  # info: path . parent . mkdir ( parents =
    path.write_text(text, encoding="utf-8")  # info: path . write_text ( text , encoding =
    os.chmod(path, 0o600)  # info: os . chmod ( path , 0o600 )


# ====================================================
# SECTION: function log_line
# What it does: log line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_line(root: Path, command: str, detail: str) -> None:  # info: def log_line
    folder = log_dir(root)  # info: set folder
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)  # info: folder . mkdir ( parents = True ,
    path = folder / "inbox.log"  # info: set path
    stamp = datetime.now(HST).isoformat(timespec="seconds")  # info: set stamp
    line = f"{stamp} {command} {detail}\n"  # info: set line
    with path.open("a", encoding="utf-8") as fh:  # info: with path . open ( "a" , encoding
        fh.write(line)  # info: fh . write ( line )
    os.chmod(path, 0o600)  # info: os . chmod ( path , 0o600 )


# ====================================================
# SECTION: function cmd_subscribe
# What it does: cmd subscribe.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cmd_subscribe(inbox: Path, root: Path) -> int:  # info: def cmd_subscribe
    subs_path = data_dir(root) / "subscribers.json"  # info: set subs_path
    state = {"subscribers": {}}  # info: set state
    if subs_path.is_file():  # info: if subs_path . is_file ( ) :
        try:  # info: try :
            loaded = json.loads(subs_path.read_text(encoding="utf-8"))  # info: set loaded
            if isinstance(loaded.get("subscribers"), dict):  # info: if isinstance ( loaded . get ( "subscribers"
                state = loaded  # info: set state
        except json.JSONDecodeError:  # info: except json . JSONDecodeError :
            state = {"subscribers": {}}  # info: set state
    subscribers: dict = state.setdefault("subscribers", {})  # info: set subscribers
    seen = 0  # info: set seen
    for rec in load_records(inbox):  # info: for rec in load_records ( inbox ) :
        if rec.get("chat_type") != "private":  # info: if rec . get ( "chat_type" ) !=
            continue  # info: continue
        cmd = parse_cmd(str(rec.get("text") or ""))  # info: set cmd
        if cmd not in {"subscribe", "unsubscribe", "start", "help"}:  # info: if cmd not in { "subscribe" , "unsubscribe"
            continue  # info: continue
        seen += 1  # info: set seen
        cid = str(rec.get("chat_id"))  # info: set cid
        frm = rec.get("from") if isinstance(rec.get("from"), dict) else {}  # info: set frm
        label = str(frm.get("username") or frm.get("name") or "")  # info: set label
        if cmd == "subscribe":  # info: if cmd == "subscribe" :
            subscribers[cid] = {  # info: subscribers [ cid ] = {
                "surface": "telegram",  # info: "surface" : "telegram" ,
                "label": label,  # info: "label" : label ,
                "since": rec.get("ts") or "",  # info: "since" : rec . get ( "ts" )
            }  # info: }
        elif cmd == "unsubscribe":  # info: elif cmd == "unsubscribe" :
            subscribers.pop(cid, None)  # info: subscribers . pop ( cid , None )
    write_private(subs_path, json.dumps(state, indent=2) + "\n")  # info: call write_private
    log_line(root, "subscribe", f"commands={seen} subscribers={len(subscribers)}")  # info: call log_line
    print(f"[inbox] subscribe commands={seen} subscribers={len(subscribers)}")  # info: call print
    return 0  # info: return 0


# ====================================================
# SECTION: function load_ledger
# What it does: load ledger.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_ledger(path: Path) -> set[str]:  # info: def load_ledger
    if not path.is_file():  # info: if not path . is_file ( ) :
        return set()  # info: return set ( )
    done: set[str] = set()  # info: set done
    for line in path.read_text(encoding="utf-8").splitlines():  # info: for line in path . read_text ( encoding
        try:  # info: try :
            done.add(json.loads(line)["key"])  # info: done . add ( json . loads (
        except (json.JSONDecodeError, KeyError, TypeError):  # info: except ( json . JSONDecodeError , KeyError ,
            continue  # info: continue
    return done  # info: return done


# ====================================================
# SECTION: function cmd_drain
# What it does: cmd drain.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cmd_drain(inbox: Path, root: Path) -> int:  # info: def cmd_drain
    folder = data_dir(root)  # info: set folder
    feedback = folder / "feedback.jsonl"  # info: set feedback
    ledger_path = folder / "drain-ledger.jsonl"  # info: set ledger_path
    done = load_ledger(ledger_path)  # info: set done
    copied = 0  # info: set copied
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)  # info: folder . mkdir ( parents = True ,
    with feedback.open("a", encoding="utf-8") as out, ledger_path.open("a", encoding="utf-8") as ledger:  # info: with feedback . open ( "a" , encoding
        for rec in load_records(inbox):  # info: for rec in load_records ( inbox ) :
            key = record_key(rec)  # info: set key
            if not key or key in done:  # info: if not key or key in done :
                continue  # info: continue
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")  # info: out . write ( json . dumps (
            ledger.write(json.dumps({"key": key, "ts": datetime.now(HST).isoformat(timespec="seconds")}) + "\n")  # info: ledger . write ( json . dumps (
            done.add(key)  # info: done . add ( key )
            copied += 1  # info: set copied
    if feedback.is_file():  # info: if feedback . is_file ( ) :
        os.chmod(feedback, 0o600)  # info: os . chmod ( feedback , 0o600 )
    if ledger_path.is_file():  # info: if ledger_path . is_file ( ) :
        os.chmod(ledger_path, 0o600)  # info: os . chmod ( ledger_path , 0o600 )
    log_line(root, "drain", f"copied={copied}")  # info: call log_line
    print(f"[inbox] drain copied={copied}")  # info: call print
    return 0  # info: return 0


# ====================================================
# SECTION: function cmd_overnight
# What it does: cmd overnight.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cmd_overnight(root: Path, solar_line: str) -> int:  # info: def cmd_overnight
    stamp = datetime.now(HST).strftime("%Y-%m-%d %H:%M %Z")  # info: set stamp
    solar = solar_line.strip() if solar_line else ""  # info: set solar
    body = f"Late-night status — {stamp}\n"  # info: set body
    if solar:  # info: if solar :
        body += solar + "\n"  # info: set body
    else:  # info: else :
        body += "Solar line absent.\n"  # info: set body
    path = data_dir(root) / "overnight-last.txt"  # info: set path
    write_private(path, body)  # info: call write_private
    log_line(root, "overnight", "solar=yes" if solar else "solar=absent")  # info: call log_line
    print(f"[inbox] overnight wrote {path.name}")  # info: call print
    return 0  # info: return 0


# ====================================================
# SECTION: function cmd_feedback
# What it does: cmd feedback.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cmd_feedback(root: Path, note: str) -> int:  # info: def cmd_feedback
    text = note.strip()  # info: set text
    if not text:  # info: if not text :
        print("[inbox] feedback needs --note", flush=True)  # info: call print
        return 2  # info: return 2
    row = {  # info: set row
        "ts": datetime.now(HST).isoformat(timespec="seconds"),  # info: "ts" : datetime . now ( HST )
        "kind": "note",  # info: "kind" : "note" ,
        "note": text[:4000],  # info: "note" : text [ : 4000 ] ,
    }  # info: }
    path = data_dir(root) / "reply-feedback.jsonl"  # info: set path
    folder = path.parent  # info: set folder
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)  # info: folder . mkdir ( parents = True ,
    with path.open("a", encoding="utf-8") as fh:  # info: with path . open ( "a" , encoding
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")  # info: fh . write ( json . dumps (
    os.chmod(path, 0o600)  # info: os . chmod ( path , 0o600 )
    log_line(root, "feedback", "appended=1")  # info: call log_line
    print("[inbox] feedback appended=1")  # info: call print
    return 0  # info: return 0


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])  # info: set ap
    ap.add_argument("command", choices=("subscribe", "drain", "overnight", "feedback"))  # info: ap . add_argument ( "command" , choices =
    ap.add_argument("--inbox", default="")  # info: ap . add_argument ( "--inbox" , default =
    ap.add_argument("--database", default="")  # info: ap . add_argument ( "--database" , default =
    ap.add_argument("--solar-line", default="")  # info: ap . add_argument ( "--solar-line" , default =
    ap.add_argument("--note", default="")  # info: ap . add_argument ( "--note" , default =
    args = ap.parse_args()  # info: set args
    root = database_root(args.database or None)  # info: set root
    inbox = Path(args.inbox) if args.inbox else DEFAULT_INBOX  # info: set inbox
    if args.command == "subscribe":  # info: if args . command == "subscribe" :
        return cmd_subscribe(inbox, root)  # info: return cmd_subscribe ( inbox , root )
    if args.command == "drain":  # info: if args . command == "drain" :
        return cmd_drain(inbox, root)  # info: return cmd_drain ( inbox , root )
    if args.command == "overnight":  # info: if args . command == "overnight" :
        return cmd_overnight(root, args.solar_line)  # info: return cmd_overnight ( root , args . solar_line
    return cmd_feedback(root, args.note)  # info: return cmd_feedback ( root , args . note


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
