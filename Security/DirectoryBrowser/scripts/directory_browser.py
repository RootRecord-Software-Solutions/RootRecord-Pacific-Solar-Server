# ==============================================================================
# FILE: Security/DirectoryBrowser/scripts/directory_browser.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""List one directory level. Does not read file bytes and does not open a port.

  python3 directory_browser.py --root DIR [--rel REL]
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent  # info: set _SCRIPTS
if str(_SCRIPTS) not in sys.path:  # info: if str ( _SCRIPTS ) not in sys
    sys.path.insert(0, str(_SCRIPTS))  # info: sys . path . insert ( 0 ,

from DirectoryBrowser.list_dir import list_dir  # noqa: E402


# ====================================================
# SECTION: function _parser
# What it does:  parser.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _parser() -> argparse.ArgumentParser:  # info: def _parser
    parser = argparse.ArgumentParser(  # info: set parser
        description="List one directory level under --root. Does not open a port."  # info: set description
    )  # info: )
    parser.add_argument("--root", required=True, help="Directory to list. Required.")  # info: parser . add_argument ( "--root" , required =
    parser.add_argument("--rel", default="", help="Relative path under --root. One level.")  # info: parser . add_argument ( "--rel" , default =
    return parser  # info: return parser


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = _parser().parse_args(argv)  # info: set args
    try:  # info: try :
        payload = list_dir(args.root, args.rel)  # info: set payload
    except ValueError as exc:  # info: except ValueError as exc :
        print(str(exc), file=sys.stderr)  # info: call print
        return 1  # info: return 1
    json.dump(payload, sys.stdout, indent=2)  # info: json . dump ( payload , sys .
    sys.stdout.write("\n")  # info: sys . stdout . write ( "\n" )
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
