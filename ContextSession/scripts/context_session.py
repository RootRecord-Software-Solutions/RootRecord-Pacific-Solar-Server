# ==============================================================================
# FILE: ContextSession/scripts/context_session.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Context session CLI. Does not import FastAPI and does not open a port.

  python3 context_session.py --root DIR create USER SESSION [--provider P] [--title T]
  python3 context_session.py --root DIR append USER SESSION ROLE TYPE CONTENT
  python3 context_session.py --root DIR list USER
  python3 context_session.py --root DIR current USER SESSION
  python3 context_session.py --root DIR compile
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import sqlite3  # info: import sqlite3
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent  # info: set _SCRIPTS
if str(_SCRIPTS) not in sys.path:  # info: if str ( _SCRIPTS ) not in sys
    sys.path.insert(0, str(_SCRIPTS))  # info: sys . path . insert ( 0 ,

from ContextSession.store import SessionStore  # noqa: E402


# ====================================================
# SECTION: function _parser
# What it does:  parser.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _parser() -> argparse.ArgumentParser:  # info: def _parser
    parser = argparse.ArgumentParser(  # info: set parser
        description="Context session store. Does not open a port."  # info: set description
    )  # info: )
    parser.add_argument(  # info: parser . add_argument (
        "--root",  # info: "--root" ,
        default=None,  # info: set default
        help="Directory for sessions.db. Default is Database ContextSession/.",  # info: set help
    )  # info: )
    sub = parser.add_subparsers(dest="cmd", required=True)  # info: set sub

    create = sub.add_parser("create")  # info: set create
    create.add_argument("user_id")  # info: create . add_argument ( "user_id" )
    create.add_argument("session_id")  # info: create . add_argument ( "session_id" )
    create.add_argument("--provider", default="")  # info: create . add_argument ( "--provider" , default =
    create.add_argument("--title", default="")  # info: create . add_argument ( "--title" , default =

    append = sub.add_parser("append")  # info: set append
    append.add_argument("user_id")  # info: append . add_argument ( "user_id" )
    append.add_argument("session_id")  # info: append . add_argument ( "session_id" )
    append.add_argument("role")  # info: append . add_argument ( "role" )
    append.add_argument("event_type")  # info: append . add_argument ( "event_type" )
    append.add_argument("content")  # info: append . add_argument ( "content" )

    listing = sub.add_parser("list")  # info: set listing
    listing.add_argument("user_id")  # info: listing . add_argument ( "user_id" )

    current = sub.add_parser("current")  # info: set current
    current.add_argument("user_id")  # info: current . add_argument ( "user_id" )
    current.add_argument("session_id")  # info: current . add_argument ( "session_id" )

    sub.add_parser("compile")  # info: sub . add_parser ( "compile" )
    return parser  # info: return parser


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = _parser().parse_args(argv)  # info: set args
    store = SessionStore(args.root)  # info: set store
    try:  # info: try :
        if args.cmd == "create":  # info: if args . cmd == "create" :
            payload = store.create_session(  # info: set payload
                args.user_id, args.session_id, args.provider, args.title  # info: args . user_id , args . session_id ,
            )  # info: )
        elif args.cmd == "append":  # info: elif args . cmd == "append" :
            payload = store.append_event(  # info: set payload
                args.user_id,  # info: args . user_id ,
                args.session_id,  # info: args . session_id ,
                args.role,  # info: args . role ,
                args.event_type,  # info: args . event_type ,
                args.content,  # info: args . content ,
            )  # info: )
        elif args.cmd == "list":  # info: elif args . cmd == "list" :
            payload = {  # info: set payload
                "user_id": args.user_id,  # info: "user_id" : args . user_id ,
                "sessions": store.list_sessions(args.user_id),  # info: "sessions" : store . list_sessions ( args .
            }  # info: }
        elif args.cmd == "compile":  # info: elif args . cmd == "compile" :
            payload = store.compile()  # info: set payload
        else:  # info: else :
            payload = store.current(args.user_id, args.session_id)  # info: set payload
    except (ValueError, sqlite3.IntegrityError) as exc:  # info: except ( ValueError , sqlite3 . IntegrityError )
        print(str(exc), file=sys.stderr)  # info: call print
        return 1  # info: return 1
    print(json.dumps(payload, ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
