# ==============================================================================
# FILE: Automations/scripts/test_polling_rest.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Polling-rest checks on temp files. Does not call systemctl or stop the poller."""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert
import polling_rest as rest  # noqa: E402

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
# What it does: Run the rest checks against a fake systemctl.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory
        root = Path(tmp)  # info: set root
        os.environ["RR_POLLING_REST"] = str(root / "polling-rest.json")  # info: os . environ
        os.environ["RR_SYSTEMD_USER_DIR"] = str(root / "systemd")  # info: os . environ
        os.environ["RR_POLLING_REST_STOP"] = "/bin/true"  # info: os . environ
        exercise()  # info: call exercise
    failed = [name for name, ok, _note in RESULTS if not ok]  # info: set failed
    print(f"{len(RESULTS) - len(failed)} passed, {len(failed)} failed")  # info: call print
    return 1 if failed else 0  # info: return 1 if failed else 0


# ====================================================
# SECTION: function exercise
# What it does: Arm, fire, and delete. The runner records commands and does not execute them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def exercise() -> None:  # info: def exercise
    now = datetime(2026, 10, 2, 12, 0, tzinfo=rest.HST)  # info: set now
    off = now + timedelta(hours=2)  # info: set off
    on = now + timedelta(hours=8)  # info: set on
    rec("boot after off", rest.validate("once", on, off, now) != "")  # info: call rec
    calls: list[list[str]] = []  # info: set calls

    def runner(argv):  # info: def runner
        calls.append(list(argv))  # info: calls . append
        return 0  # info: return 0

    item = rest.add_rest("once", off, on, now=now, runner=runner)  # info: set item
    rec("armed", item["enabled"] is True and rest.ID_RE.match(item["id"]) is not None)  # info: call rec
    timers = [row for row in calls if row[:3] == ["systemctl", "--user", "enable"]]  # info: set timers
    rec("two timers", len(timers) == 2)  # info: call rec
    unit = (rest.unit_dir() / f"rr-polling-rest-off-{item['id']}.timer").read_text(encoding="utf-8")  # info: set unit
    rec("calendar", "Pacific/Honolulu" in unit and "Persistent=true" in unit)  # info: call rec
    rec("not stopped yet", not any(row[0] == "bash" for row in calls))  # info: call rec
    code = rest.fire("off", item["id"], runner=runner)  # info: set code
    saved = rest.load()["items"][0]  # info: set saved
    rec("stopped", code == 0 and saved["off_done_at"] != "" and "stopped, waiting to boot" in rest.describe(saved))  # info: call rec
    rec("poller still down", not any(row[-1:] == [rest.POLLER_UNIT] and "start" in row for row in calls))  # info: call rec
    code = rest.fire("on", item["id"], runner=runner)  # info: set code
    saved = rest.load()["items"][0]  # info: set saved
    rec("booted", code == 0 and saved["enabled"] is False and any(rest.POLLER_UNIT in row for row in calls))  # info: call rec
    rec("delete", rest.delete_rest(item["id"], runner=runner) is True and rest.load()["items"] == [])  # info: call rec
    daily_off = now.replace(hour=22, minute=0)  # info: set daily_off
    daily_on = daily_off + timedelta(hours=8)  # info: set daily_on
    daily = rest.add_rest("daily", daily_off, daily_on, now=now, runner=runner)  # info: set daily
    text = (rest.unit_dir() / f"rr-polling-rest-on-{daily['id']}.timer").read_text(encoding="utf-8")  # info: set text
    rec("daily clock", "*-*-* 06:00:00 Pacific/Honolulu" in text)  # info: call rec
    rest.delete_rest(daily["id"], runner=runner)  # info: call rest . delete_rest


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
