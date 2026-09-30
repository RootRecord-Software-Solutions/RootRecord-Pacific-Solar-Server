#!/usr/bin/env python3
"""On-demand Meta AI chat. Never installs packages. Never prompts meta.ai unless --send."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = "meta-ai-api"
IMPORT_NAME = "meta_ai_api"
DATA = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Communications/MetaAI")
LOG_DIR = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/MetaAI")


def import_available() -> bool:
    return importlib.util.find_spec(IMPORT_NAME) is not None


def check_report() -> dict:
    present = import_available()
    report = {"ok": present, "package": PACKAGE, "import": IMPORT_NAME, "send": False}
    if not present:
        report["error"] = "missing"
        report["hint"] = f"{PACKAGE} is not installed; this script does not install it"
    return report


def write_last(user: str, message: str) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "at": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "message": message,
    }
    (DATA / "last.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def log_line(text: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"at": datetime.now(timezone.utc).isoformat(), "text": text})
    with (LOG_DIR / "meta-ai.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def stream_prompt(message: str) -> str:
    from meta_ai_api import MetaAI

    response = MetaAI().prompt(message=message, stream=True)
    full = ""
    for chunk in response:
        msg = chunk.get("message", "") if isinstance(chunk, dict) else ""
        if msg.startswith(full):
            print(msg[len(full) :], end="", flush=True)
            full = msg
        else:
            print(msg, end="", flush=True)
            full = msg
    print()
    return full


def one_send(message: str) -> int:
    if not import_available():
        print(json.dumps(check_report()))
        return 2
    print("Meta AI: ", end="", flush=True)
    try:
        full = stream_prompt(message)
    except Exception as exc:
        log_line(f"error {type(exc).__name__}")
        print(f"\n[!] Error: {exc}\n")
        return 1
    write_last(message, full)
    log_line("sent")
    return 0


def interactive() -> int:
    print("Meta AI Chat  (type 'exit', 'quit' or Ctrl+C to leave)")
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return 0
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            return 0
        code = one_send(user_input)
        if code == 2:
            return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="On-demand Meta AI chat. Does not install packages.")
    parser.add_argument("--check", action="store_true", help="Report whether meta-ai-api imports. No send.")
    parser.add_argument("--send", action="store_true", help="Send to meta.ai. Requires sign-off.")
    parser.add_argument("message", nargs="?", help="One message with --send. Without --send this is ignored.")
    args = parser.parse_args(argv)
    if args.send:
        if args.message:
            return one_send(args.message)
        return interactive()
    print(json.dumps(check_report()))
    return 0 if import_available() else 2


if __name__ == "__main__":
    raise SystemExit(main())
