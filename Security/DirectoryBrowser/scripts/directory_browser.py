#!/usr/bin/env python3
"""List one directory level. Does not read file bytes and does not open a port.

  python3 directory_browser.py --root DIR [--rel REL]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from DirectoryBrowser.list_dir import list_dir  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List one directory level under --root. Does not open a port."
    )
    parser.add_argument("--root", required=True, help="Directory to list. Required.")
    parser.add_argument("--rel", default="", help="Relative path under --root. One level.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = list_dir(args.root, args.rel)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
