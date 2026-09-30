# ==============================================================================
# FILE: Communications/MetaAI/scripts/meta.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""On-demand Meta AI chat. Never installs packages. Never prompts meta.ai unless --send."""  # info: """On-demand Meta AI chat. Never installs packages. Never prompts meta.ai unless --send."""

from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import importlib.util  # info: import importlib . util
import json  # info: import json
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

PACKAGE = "meta-ai-api"  # info: set PACKAGE
IMPORT_NAME = "meta_ai_api"  # info: set IMPORT_NAME
DATA = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Communications/MetaAI")  # info: set DATA
LOG_DIR = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/MetaAI")  # info: set LOG_DIR


# ====================================================
# SECTION: function import_available
# What it does: import available.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def import_available() -> bool:  # info: def import_available
    return importlib.util.find_spec(IMPORT_NAME) is not None  # info: return importlib . util . find_spec ( IMPORT_NAME


# ====================================================
# SECTION: function check_report
# What it does: check report.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def check_report() -> dict:  # info: def check_report
    present = import_available()  # info: set present
    report = {"ok": present, "package": PACKAGE, "import": IMPORT_NAME, "send": False}  # info: set report
    if not present:  # info: if not present :
        report["error"] = "missing"  # info: report [ "error" ] = "missing"
        report["hint"] = f"{PACKAGE} is not installed; this script does not install it"  # info: report [ "hint" ] = f" { PACKAGE
    return report  # info: return report


# ====================================================
# SECTION: function write_last
# What it does: write last.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_last(user: str, message: str) -> None:  # info: def write_last
    DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
    payload = {  # info: set payload
        "at": datetime.now(timezone.utc).isoformat(),  # info: "at" : datetime . now ( timezone .
        "user": user,  # info: "user" : user ,
        "message": message,  # info: "message" : message ,
    }  # info: }
    (DATA / "last.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: call (


# ====================================================
# SECTION: function log_line
# What it does: log line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_line(text: str) -> None:  # info: def log_line
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    line = json.dumps({"at": datetime.now(timezone.utc).isoformat(), "text": text})  # info: set line
    with (LOG_DIR / "meta-ai.jsonl").open("a", encoding="utf-8") as handle:  # info: with ( LOG_DIR / "meta-ai.jsonl" ) . open
        handle.write(line + "\n")  # info: handle . write ( line + "\n" )


# ====================================================
# SECTION: function stream_prompt
# What it does: stream prompt.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stream_prompt(message: str) -> str:  # info: def stream_prompt
    from meta_ai_api import MetaAI  # info: from meta_ai_api import MetaAI

    response = MetaAI().prompt(message=message, stream=True)  # info: set response
    full = ""  # info: set full
    for chunk in response:  # info: for chunk in response :
        msg = chunk.get("message", "") if isinstance(chunk, dict) else ""  # info: set msg
        if msg.startswith(full):  # info: if msg . startswith ( full ) :
            print(msg[len(full) :], end="", flush=True)  # info: call print
            full = msg  # info: set full
        else:  # info: else :
            print(msg, end="", flush=True)  # info: call print
            full = msg  # info: set full
    print()  # info: call print
    return full  # info: return full


# ====================================================
# SECTION: function one_send
# What it does: one send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def one_send(message: str) -> int:  # info: def one_send
    if not import_available():  # info: if not import_available ( ) :
        print(json.dumps(check_report()))  # info: call print
        return 2  # info: return 2
    print("Meta AI: ", end="", flush=True)  # info: call print
    try:  # info: try :
        full = stream_prompt(message)  # info: set full
    except Exception as exc:  # info: except Exception as exc :
        log_line(f"error {type(exc).__name__}")  # info: call log_line
        print(f"\n[!] Error: {exc}\n")  # info: call print
        return 1  # info: return 1
    write_last(message, full)  # info: call write_last
    log_line("sent")  # info: call log_line
    return 0  # info: return 0


# ====================================================
# SECTION: function interactive
# What it does: interactive.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def interactive() -> int:  # info: def interactive
    print("Meta AI Chat  (type 'exit', 'quit' or Ctrl+C to leave)")  # info: call print
    while True:  # info: while True :
        try:  # info: try :
            user_input = input("You: ").strip()  # info: set user_input
        except (KeyboardInterrupt, EOFError):  # info: except ( KeyboardInterrupt , EOFError ) :
            print("\nGoodbye!")  # info: call print
            return 0  # info: return 0
        if not user_input:  # info: if not user_input :
            continue  # info: continue
        if user_input.lower() in {"exit", "quit", "q"}:  # info: if user_input . lower ( ) in {
            print("Goodbye!")  # info: call print
            return 0  # info: return 0
        code = one_send(user_input)  # info: set code
        if code == 2:  # info: if code == 2 :
            return 2  # info: return 2


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    parser = argparse.ArgumentParser(description="On-demand Meta AI chat. Does not install packages.")  # info: set parser
    parser.add_argument("--check", action="store_true", help="Report whether meta-ai-api imports. No send.")  # info: parser . add_argument ( "--check" , action =
    parser.add_argument("--send", action="store_true", help="Send to meta.ai. Requires sign-off.")  # info: parser . add_argument ( "--send" , action =
    parser.add_argument("message", nargs="?", help="One message with --send. Without --send this is ignored.")  # info: parser . add_argument ( "message" , nargs =
    args = parser.parse_args(argv)  # info: set args
    if args.send:  # info: if args . send :
        if args.message:  # info: if args . message :
            return one_send(args.message)  # info: return one_send ( args . message )
        return interactive()  # info: return interactive ( )
    print(json.dumps(check_report()))  # info: call print
    return 0 if import_available() else 2  # info: return 0 if import_available ( ) else 2


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
