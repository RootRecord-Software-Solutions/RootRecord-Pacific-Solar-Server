# ==============================================================================
# FILE: Automations/scripts/test_service_notice.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Service-window checks on a temp file. Does not call the public API or publish the site."""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert
import service_notice as notice  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []  # info: set RESULTS


# ====================================================
# SECTION: function rec
# What it does: Record one test result.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def rec(name: str, ok: bool, note: str = "") -> None:  # info: def rec
    RESULTS.append((name, bool(ok), note))  # info: RESULTS . append
    print(("PASS " if ok else "FAIL ") + name + (f" — {note}" if note else ""))  # info: call print


# ====================================================
# SECTION: function main
# What it does: Run the window checks. Does not read api.rootrecord.cloud.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory
        os.environ["RR_SERVICE_NOTICE"] = str(Path(tmp) / "service-notice.json")  # info: os . environ
        exercise()  # info: call exercise
    failed = [name for name, ok, _note in RESULTS if not ok]  # info: set failed
    print(f"{len(RESULTS) - len(failed)} passed, {len(failed)} failed")  # info: call print
    return 1 if failed else 0  # info: return 1 if failed else 0


# ====================================================
# SECTION: function exercise
# What it does: Phases, publish, freeze, and delete. The fetch function is local.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def exercise() -> None:  # info: def exercise
    now = datetime(2026, 10, 2, 12, 0, tzinfo=notice.HST)  # info: set now
    down = now + timedelta(hours=2)  # info: set down
    up = now + timedelta(hours=8)  # info: set up
    rec("return after down", notice.validate_window(up, down, now) != "")  # info: call rec
    rec("already ended", "already ended" in notice.validate_window(now - timedelta(hours=3), now - timedelta(hours=1), now))  # info: call rec

    def fetch():  # info: def fetch
        return {"stats": {"hawaiiActiveFlows": 4, "localActiveFlows": 2, "activeFlows": 6, "endpoints": 9}}  # info: return

    item = notice.add_window(down, up, "  Solar\nwork  ", fetch=fetch, now=now)  # info: set item
    rec("note cleaned", item["note"] == "Solar work")  # info: call rec
    rec("snapshot", item["last_known"]["hawaii"] == 4 and item["last_known"]["endpoints"] == 9)  # info: call rec
    rec("upcoming", notice.phase(item, now) == "upcoming")  # info: call rec
    rec("shown inside a day", (notice.current_window(now=now) or {}).get("id") == item["id"])  # info: call rec
    rec("hidden beyond a day", notice.current_window(now=now - timedelta(hours=30)) is None)  # info: call rec
    rec("down phase", notice.phase(item, down + timedelta(minutes=1)) == "down")  # info: call rec
    rec("not frozen yet", notice.needs_freeze(down + timedelta(minutes=1)) is True)  # info: call rec
    frozen = notice.freeze_due(down + timedelta(minutes=1), fetch=fetch)  # info: set frozen
    rec("freeze once", frozen == [item["id"]] and notice.needs_freeze(down + timedelta(minutes=2)) is False)  # info: call rec
    saved = notice.load()["windows"][0]  # info: set saved
    rec("counts kept", saved["last_known"]["flows"] == 6 and saved["frozen"] is True)  # info: call rec
    rec("delete", notice.delete_window(item["id"]) is True and notice.load()["windows"] == [])  # info: call rec
    try:  # info: try
        notice.add_window(down, up, "x" * 161, fetch=fetch, now=now)  # info: call notice . add_window
        rec("long note rejected", False)  # info: call rec
    except ValueError:  # info: except ValueError
        rec("long note rejected", True)  # info: call rec


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
