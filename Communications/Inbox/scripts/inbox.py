#!/usr/bin/env python3
"""Local inbox on the quiet-mode relay hold. No network. No send.

Reads Relay-Inbox JSONL (or --inbox). Does not call getUpdates, Discord, Slack, or Cloudflare.

  inbox.py subscribe [--inbox DIR] [--database DIR]
  inbox.py drain     [--inbox DIR] [--database DIR]
  inbox.py overnight [--database DIR] [--solar-line TEXT]
  inbox.py feedback  [--database DIR] --note TEXT
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
DEFAULT_INBOX = Path(
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/Relay-Inbox"
)
DEFAULT_DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
CURRENT = "relay-inbox_current.jsonl"


def database_root(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    env = os.environ.get("RR_DATABASE_ROOT", "").strip()
    return Path(env) if env else DEFAULT_DATABASE


def data_dir(root: Path) -> Path:
    return root / "Communications" / "Inbox"


def log_dir(root: Path) -> Path:
    return root / "Logs" / "Communications" / "Inbox"


def parse_cmd(text: str) -> str | None:
    raw = str(text or "").strip().lower()
    if not raw:
        return None
    first = raw.split()[0].split("@", 1)[0]
    if first in {"/start", "/help", "!help"}:
        return "help" if first != "/start" else "start"
    if first in {"/subscribe", "!subscribe", "subscribe"}:
        return "subscribe"
    if first in {"/unsubscribe", "!unsubscribe", "unsubscribe"}:
        return "unsubscribe"
    return None


def load_records(inbox: Path) -> list[dict]:
    files = sorted((inbox / "Archive").glob("*/relay-inbox_*.jsonl"))
    files.append(inbox / CURRENT)
    recs: list[dict] = []
    for path in files:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    recs.sort(key=lambda r: (r.get("ts") or "", r.get("update_id") or 0))
    return recs


def record_key(rec: dict) -> str:
    return f"{rec.get('chat_id')}:{rec.get('message_id')}"


def write_private(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(text, encoding="utf-8")
    os.chmod(path, 0o600)


def log_line(root: Path, command: str, detail: str) -> None:
    folder = log_dir(root)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = folder / "inbox.log"
    stamp = datetime.now(HST).isoformat(timespec="seconds")
    line = f"{stamp} {command} {detail}\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    os.chmod(path, 0o600)


def cmd_subscribe(inbox: Path, root: Path) -> int:
    subs_path = data_dir(root) / "subscribers.json"
    state = {"subscribers": {}}
    if subs_path.is_file():
        try:
            loaded = json.loads(subs_path.read_text(encoding="utf-8"))
            if isinstance(loaded.get("subscribers"), dict):
                state = loaded
        except json.JSONDecodeError:
            state = {"subscribers": {}}
    subscribers: dict = state.setdefault("subscribers", {})
    seen = 0
    for rec in load_records(inbox):
        if rec.get("chat_type") != "private":
            continue
        cmd = parse_cmd(str(rec.get("text") or ""))
        if cmd not in {"subscribe", "unsubscribe", "start", "help"}:
            continue
        seen += 1
        cid = str(rec.get("chat_id"))
        frm = rec.get("from") if isinstance(rec.get("from"), dict) else {}
        label = str(frm.get("username") or frm.get("name") or "")
        if cmd == "subscribe":
            subscribers[cid] = {
                "surface": "telegram",
                "label": label,
                "since": rec.get("ts") or "",
            }
        elif cmd == "unsubscribe":
            subscribers.pop(cid, None)
    write_private(subs_path, json.dumps(state, indent=2) + "\n")
    log_line(root, "subscribe", f"commands={seen} subscribers={len(subscribers)}")
    print(f"[inbox] subscribe commands={seen} subscribers={len(subscribers)}")
    return 0


def load_ledger(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    done: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            done.add(json.loads(line)["key"])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return done


def cmd_drain(inbox: Path, root: Path) -> int:
    folder = data_dir(root)
    feedback = folder / "feedback.jsonl"
    ledger_path = folder / "drain-ledger.jsonl"
    done = load_ledger(ledger_path)
    copied = 0
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with feedback.open("a", encoding="utf-8") as out, ledger_path.open("a", encoding="utf-8") as ledger:
        for rec in load_records(inbox):
            key = record_key(rec)
            if not key or key in done:
                continue
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            ledger.write(json.dumps({"key": key, "ts": datetime.now(HST).isoformat(timespec="seconds")}) + "\n")
            done.add(key)
            copied += 1
    if feedback.is_file():
        os.chmod(feedback, 0o600)
    if ledger_path.is_file():
        os.chmod(ledger_path, 0o600)
    log_line(root, "drain", f"copied={copied}")
    print(f"[inbox] drain copied={copied}")
    return 0


def cmd_overnight(root: Path, solar_line: str) -> int:
    stamp = datetime.now(HST).strftime("%Y-%m-%d %H:%M %Z")
    solar = solar_line.strip() if solar_line else ""
    body = f"Late-night status — {stamp}\n"
    if solar:
        body += solar + "\n"
    else:
        body += "Solar line absent.\n"
    path = data_dir(root) / "overnight-last.txt"
    write_private(path, body)
    log_line(root, "overnight", "solar=yes" if solar else "solar=absent")
    print(f"[inbox] overnight wrote {path.name}")
    return 0


def cmd_feedback(root: Path, note: str) -> int:
    text = note.strip()
    if not text:
        print("[inbox] feedback needs --note", flush=True)
        return 2
    row = {
        "ts": datetime.now(HST).isoformat(timespec="seconds"),
        "kind": "note",
        "note": text[:4000],
    }
    path = data_dir(root) / "reply-feedback.jsonl"
    folder = path.parent
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.chmod(path, 0o600)
    log_line(root, "feedback", "appended=1")
    print("[inbox] feedback appended=1")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("subscribe", "drain", "overnight", "feedback"))
    ap.add_argument("--inbox", default="")
    ap.add_argument("--database", default="")
    ap.add_argument("--solar-line", default="")
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    root = database_root(args.database or None)
    inbox = Path(args.inbox) if args.inbox else DEFAULT_INBOX
    if args.command == "subscribe":
        return cmd_subscribe(inbox, root)
    if args.command == "drain":
        return cmd_drain(inbox, root)
    if args.command == "overnight":
        return cmd_overnight(root, args.solar_line)
    return cmd_feedback(root, args.note)


if __name__ == "__main__":
    raise SystemExit(main())
