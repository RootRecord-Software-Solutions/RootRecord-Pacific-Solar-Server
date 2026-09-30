#!/usr/bin/env python3
"""Context session CLI. Does not import FastAPI and does not open a port.

  python3 context_session.py --root DIR create USER SESSION [--provider P] [--title T]
  python3 context_session.py --root DIR append USER SESSION ROLE TYPE CONTENT
  python3 context_session.py --root DIR list USER
  python3 context_session.py --root DIR current USER SESSION
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from ContextSession.store import SessionStore  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Context session store. Does not open a port."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Directory for per-user sqlite files. Default is Database ContextSession/.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    create = sub.add_parser("create")
    create.add_argument("user_id")
    create.add_argument("session_id")
    create.add_argument("--provider", default="")
    create.add_argument("--title", default="")

    append = sub.add_parser("append")
    append.add_argument("user_id")
    append.add_argument("session_id")
    append.add_argument("role")
    append.add_argument("event_type")
    append.add_argument("content")

    listing = sub.add_parser("list")
    listing.add_argument("user_id")

    current = sub.add_parser("current")
    current.add_argument("user_id")
    current.add_argument("session_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    store = SessionStore(args.root)
    try:
        if args.cmd == "create":
            payload = store.create_session(
                args.user_id, args.session_id, args.provider, args.title
            )
        elif args.cmd == "append":
            payload = store.append_event(
                args.user_id,
                args.session_id,
                args.role,
                args.event_type,
                args.content,
            )
        elif args.cmd == "list":
            payload = {
                "user_id": args.user_id,
                "sessions": store.list_sessions(args.user_id),
            }
        else:
            payload = store.current(args.user_id, args.session_id)
    except (ValueError, sqlite3.IntegrityError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
