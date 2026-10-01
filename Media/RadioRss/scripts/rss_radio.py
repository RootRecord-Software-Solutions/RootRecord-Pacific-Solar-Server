# ==============================================================================
# FILE: Media/RadioRss/scripts/rss_radio.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""External RSS for RootRecord Radio. This does not change the broadcaster.

  python3 rss_radio.py check
  python3 rss_radio.py poll [--feed ID]
  python3 rss_radio.py health
  python3 rss_radio.py queue
  python3 rss_radio.py handoff [--speak]
  python3 rss_radio.py trace STORY_ID
  python3 rss_radio.py enable ID
  python3 rss_radio.py disable ID

poll returns success even when a feed fails. handoff without --speak does not render audio.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 , str ( HERE ) )

from common import log_line  # info: from common import log_line
from pipeline import export_queue, handoff, health_report, health_text, poll, set_runtime, trace, write_health  # info: from pipeline import export_queue , handoff , health_report , health_text , poll , set_runtime , trace , write_health
from registry import load_registry  # info: from registry import load_registry
from store import connect  # info: from store import connect


# ====================================================
# SECTION: function _print
# What it does: Print one JSON object for the poller log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _print(payload: dict) -> None:  # info: def _print
    print(json.dumps(payload, ensure_ascii=False))  # info: print ( json . dumps ( payload , ensure_ascii = False ) )


# ====================================================
# SECTION: function main
# What it does: Run one RSS command. A poll error is logged and still exits 0.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    command = argv[1] if len(argv) > 1 else "health"  # info: set command
    try:  # info: try
        registry = load_registry()  # info: set registry
        if command == "check":  # info: if command == "check" :
            on = [feed["id"] for feed in registry["feeds"] if feed.get("enabled") and feed.get("url")]  # info: set on
            _print({"ok": True, "feeds": len(registry["feeds"]), "enabled": len(on), "categories": sorted(registry["categories"])})  # info: _print ( { "ok" : True , "feeds" : len ( registry [ "feeds" ] ) , "enabled" : len ( on ) , "categories" : sorted ( registry [ "categories" ] ) } )
            return 0  # info: return 0
        conn = connect()  # info: set conn
        if command == "poll":  # info: if command == "poll" :
            only = ""  # info: set only
            if "--feed" in argv:  # info: if "--feed" in argv :
                only = argv[argv.index("--feed") + 1]  # info: set only
            _print(poll(registry, conn, only=only))  # info: _print ( poll ( registry , conn , only = only ) )
            return 0  # info: return 0
        if command == "health":  # info: if command == "health" :
            report = write_health(registry, conn)  # info: set report
            print(health_text(report), end="")  # info: print ( health_text ( report ) , end = "" )
            return 0  # info: return 0
        if command == "queue":  # info: if command == "queue" :
            path = export_queue(conn)  # info: set path
            _print({"ok": True, "queue": str(path)})  # info: _print ( { "ok" : True , "queue" : str ( path ) } )
            return 0  # info: return 0
        if command == "handoff":  # info: if command == "handoff" :
            _print(handoff(registry, conn, speak="--speak" in argv))  # info: _print ( handoff ( registry , conn , speak = "--speak" in argv ) )
            return 0  # info: return 0
        if command == "trace" and len(argv) > 2:  # info: if command == "trace" and len ( argv ) > 2 :
            _print(trace(conn, argv[2]))  # info: _print ( trace ( conn , argv [ 2 ] ) )
            return 0  # info: return 0
        if command in {"enable", "disable"} and len(argv) > 2:  # info: if command in { "enable" , "disable" } and len ( argv ) > 2 :
            _print(set_runtime(conn, argv[2], command == "enable"))  # info: _print ( set_runtime ( conn , argv [ 2 ] , command == "enable" ) )
            write_health(registry, conn)  # info: write_health ( registry , conn )
            return 0  # info: return 0
    except Exception as exc:  # info: except Exception as exc
        log_line(f"command_failed {command} {type(exc).__name__} {exc}")  # info: log_line ( f"command_failed { command } { type ( exc ) . __name__ } { exc }" )
        _print({"ok": command == "poll", "detail": type(exc).__name__})  # info: _print ( { "ok" : command == "poll" , "detail" : type ( exc ) . __name__ } )
        return 0 if command == "poll" else 1  # info: return 0 if command == "poll" else 1
    _print({"ok": False, "detail": "usage"})  # info: _print ( { "ok" : False , "detail" : "usage" } )
    return 1  # info: return 1


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main(sys.argv))  # info: raise SystemExit ( main ( sys . argv ) )
