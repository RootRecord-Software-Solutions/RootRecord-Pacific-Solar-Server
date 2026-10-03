# ==============================================================================
# FILE: Reports/pipeline/run.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""One poller tick for report profiles. It records windows. It does not start a second scheduler."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
if str(HERE) not in sys.path:  # info: if str ( HERE ) not in sys . path
    sys.path.insert(0, str(HERE))  # info: sys . path . insert

from context import build_context  # noqa: E402
from generate import deterministic  # noqa: E402
from store import profiles, record_generated, recover, write_queue  # noqa: E402
from windows import due, window_for  # noqa: E402


# ====================================================
# SECTION: function tick
# What it does: Record an empty deterministic report for a due news-select profile that has no observations. It does not render audio.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tick(when: datetime | None = None) -> dict:  # info: def tick
    clock = when or datetime.now()  # info: set clock
    made = []  # info: set made
    for profile in profiles():  # info: for profile in profiles
        if not due(profile, clock):  # info: if not due
            continue  # info: continue
        if profile.get("generator") != "news_select":  # info: if generator is not news_select
            continue  # info: continue
        context = build_context(profile, clock)  # info: set context
        generated = deterministic(context)  # info: set generated
        report = record_generated(profile, context, generated)  # info: set report
        made.append(report["report_id"])  # info: made . append
    write_queue()  # info: call write_queue
    state = recover(clock)  # info: set state
    return {"ok": True, "made": made, "current": len(state["current"]), "next": len(state["next"])}  # info: return tick


# ====================================================
# SECTION: function main
# What it does: tick, recover, or index. index needs a voice directory argument and does not delete files.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    command = sys.argv[1] if len(sys.argv) > 1 else "tick"  # info: set command
    if command == "recover":  # info: if command == "recover"
        print(json.dumps(recover(datetime.now()), default=str))  # info: call print
        return 0  # info: return 0
    if command == "index":  # info: if command == "index"
        from store import index_legacy  # info: from store import index_legacy
        voice = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Audio/Voice/Reports")  # info: set voice
        audio = Path(sys.argv[3]) if len(sys.argv) > 3 else None  # info: set audio
        print(json.dumps(index_legacy(voice, audio)))  # info: call print
        return 0  # info: return 0
    if command == "window":  # info: if command == "window"
        cadence = sys.argv[2] if len(sys.argv) > 2 else "5m"  # info: set cadence
        print(json.dumps(window_for(datetime.now(), cadence)))  # info: call print
        return 0  # info: return 0
    print(json.dumps(tick()))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
