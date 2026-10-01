# ==============================================================================
# FILE: Automations/scripts/test_automation_control.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Tests for automation overrides and power schedules. Uses temp files only. Does not touch BLE."""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 , str ( HERE ) )
import automation_control as actl  # noqa: E402

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
# What it does: Run the override and schedule checks against temp files. Does not call flock or BLE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    missing = [row[3] for row in actl.POWER_FUNCTIONS if not (actl.actions_dir() / row[3]).is_file()]  # info: set missing
    rec("catalog scripts exist", not missing, ", ".join(missing))  # info: call rec
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        root = Path(tmp)  # info: set root
        actions = root / "actions"  # info: set actions
        actions.mkdir()  # info: actions . mkdir ( )
        for _dev, _fn, _label, script in actl.POWER_FUNCTIONS:  # info: for _dev , _fn , _label , script in actl . POWER_FUNCTIONS
            (actions / script).write_text("#!/bin/sh\necho ok\n", encoding="utf-8")  # info: call write_text
        os.environ["RR_AUTOMATION_OVERRIDES"] = str(root / "overrides.json")  # info: os . environ [ "RR_AUTOMATION_OVERRIDES" ] =
        os.environ["RR_POWER_AUTOMATIONS"] = str(root / "power.json")  # info: os . environ [ "RR_POWER_AUTOMATIONS" ] =
        os.environ["RR_ECOFLOW_ACTIONS"] = str(actions)  # info: os . environ [ "RR_ECOFLOW_ACTIONS" ] =
        exercise()  # info: call exercise
    failed = [name for name, ok, _note in RESULTS if not ok]  # info: set failed
    print(f"{len(RESULTS) - len(failed)} passed, {len(failed)} failed")  # info: call print
    return 1 if failed else 0  # info: return 1 if failed else 0


# ====================================================
# SECTION: function exercise
# What it does: Assertions for overrides, due times, and a fake runner. Does not start the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def exercise() -> None:  # info: def exercise
    job = {"id": "heartbeat", "enabled": True}  # info: set job
    rec("default on", actl.job_enabled(job) is True)  # info: call rec
    actl.set_job_override("heartbeat", False, True)  # info: call actl . set_job_override
    rec("override off", actl.job_enabled(job) is False)  # info: call rec
    actl.set_job_override("heartbeat", True, True)  # info: call actl . set_job_override
    rec("override cleared", "heartbeat" not in actl.load_overrides()["jobs"])  # info: call rec
    try:  # info: try
        actl.set_job_override("bad id", False, True)  # info: call actl . set_job_override
        rec("reject bad id", False)  # info: call rec
    except ValueError:  # info: except ValueError
        rec("reject bad id", True)  # info: call rec
    now = datetime(2026, 10, 2, 22, 0, 30, tzinfo=actl.HST)  # info: set now
    item = {"enabled": True, "hour": 22, "minute": 0, "repeat": "daily", "last_status": "", "last_fired": "", "last_attempt": ""}  # info: set item
    rec("before clock", actl.item_due(item, now.replace(hour=21, minute=59), True) is False)  # info: call rec
    rec("on the minute", actl.item_due(item, now, True) is True)  # info: call rec
    rec("inside retry", actl.item_due(item, now.replace(minute=14), True) is True)  # info: call rec
    rec("retry closed", actl.item_due(item, now.replace(minute=15), True) is False)  # info: call rec
    done = dict(item, last_status="ok", last_fired="2026-10-02T22:00:05-10:00")  # info: set done
    rec("success blocks today", actl.item_due(done, now, True) is False)  # info: call rec
    rec("success allows tomorrow", actl.item_due(done, now + timedelta(days=1), True) is True)  # info: call rec
    tried = dict(item, last_attempt="2026-10-02T22:00:10-10:00")  # info: set tried
    rec("same minute once", actl.item_due(tried, now, True) is False)  # info: call rec
    rec("master pauses", actl.item_due(item, now, False) is False)  # info: call rec
    once = dict(item, repeat="once", date="2026-10-02")  # info: set once
    rec("once today", actl.item_due(once, now, True) is True)  # info: call rec
    rec("once other day", actl.item_due(dict(once, date="2026-10-03"), now, True) is False)  # info: call rec
    past = {"device": "delta2", "function": "ac-off", "hour": 1, "minute": 0, "repeat": "once", "date": "2020-01-01"}  # info: set past
    rec("once in the past", "already past" in actl.validate_spec(past, now))  # info: call rec
    rec("opposite", actl.opposite_function("delta2", "ac-off") == "ac-on")  # info: call rec
    rec("script stays in catalog", actl.script_for("delta2", "ac-off") is not None)  # info: call rec
    rec("unknown script refused", actl.script_for("delta2", "nope") is None)  # info: call rec
    specs = [  # info: set specs
        {"name": "Night", "device": "delta2", "function": "ac-off", "hour": 22, "minute": 0, "repeat": "daily"},  # info: call {
        {"name": "Night (return)", "device": "delta2", "function": "ac-on", "hour": 6, "minute": 0, "repeat": "daily"},  # info: call {
    ]  # info: ]
    made = actl.add_items(specs, now)  # info: set made
    rec("pair stored", len(made) == 2 and made[0]["group"] and made[0]["group"] == made[1]["group"])  # info: call rec
    calls = []  # info: set calls

    def runner(spec, script):  # info: def runner
        calls.append((spec["function"], script.name))  # info: calls . append
        return 0, "STATUS=OK"  # info: return 0 , "STATUS=OK"

    notes = actl.run_due(now, runner=runner)  # info: set notes
    rec("runner saw ac-off only", calls == [("ac-off", "delta2-ac-off.sh")], str(calls))  # info: call rec
    rec("log line", len(notes) == 1 and notes[0].startswith("power:delta2.ac-off OK"))  # info: call rec
    saved = {it["function"]: it for it in actl.load_power()["items"]}  # info: set saved
    rec("off marked ran", saved["ac-off"]["last_status"] == "ok")  # info: call rec
    rec("on still armed", saved["ac-on"]["enabled"] is True and saved["ac-on"]["last_status"] == "")  # info: call rec
    actl.set_master(False)  # info: call actl . set_master
    rec("master off skips", actl.run_due(now.replace(hour=6), runner=runner) == [])  # info: call rec
    rec("runner not called again", len(calls) == 1)  # info: call rec


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
