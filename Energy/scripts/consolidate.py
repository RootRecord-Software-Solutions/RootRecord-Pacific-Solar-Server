# ==============================================================================
# FILE: Energy/scripts/consolidate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Consolidate EcoFlow layer buckets.

  python3 consolidate.py minutes   # :00 — 1sec into 1min, 5min, 15min
  python3 consolidate.py hours     # :30 — hour and above, plus periods.json
"""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import shutil  # info: import shutil
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

PACIFIC = Path(__file__).resolve().parents[2]  # info: set PACIFIC
if str(PACIFIC) not in sys.path:  # info: if str ( PACIFIC ) not in sys . path
    sys.path.insert(0, str(PACIFIC))  # info: sys . path . insert ( 0 , str ( PACIFIC ) )

from Energy.db.condense import consolidate_minutes, condense_hours  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
AUTOMATIONS_CURRENT = Path(  # info: set AUTOMATIONS_CURRENT
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log"  # info: live poller log
)  # info: end AUTOMATIONS_CURRENT
AUTOMATIONS_ARCHIVE = Path(  # info: set AUTOMATIONS_ARCHIVE
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/Archive"  # info: hourly archive folder
)  # info: end AUTOMATIONS_ARCHIVE


# ====================================================
# SECTION: function archive_automations_log
# What it does: Rename automations_current.log to automations_TIMESTAMP.log and put it in Archive.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def archive_automations_log() -> str | None:  # info: def archive_automations_log
    """Rename automations_current.log to automations_TIMESTAMP.log under Archive.

    The poller keeps an open systemd append FD on the current path, so the cut is
    copy-into-Archive then truncate-in-place (same inode). That is the rename the
    desk asked for without sending new lines into the archived file.
    """  # info: docstring
    if not AUTOMATIONS_CURRENT.is_file() or AUTOMATIONS_CURRENT.stat().st_size <= 0:  # info: nothing to archive
        return None  # info: return None
    AUTOMATIONS_ARCHIVE.mkdir(parents=True, exist_ok=True)  # info: AUTOMATIONS_ARCHIVE . mkdir
    stamp = datetime.now(HST).strftime("%Y%m%d-%H%M%S")  # info: set stamp
    dest = AUTOMATIONS_ARCHIVE / f"automations_{stamp}.log"  # info: set dest
    if dest.exists():  # info: if dest . exists
        stamp = datetime.now(HST).strftime("%Y%m%d-%H%M%S-%f")  # info: avoid clobbering a same-second archive
        dest = AUTOMATIONS_ARCHIVE / f"automations_{stamp}.log"  # info: set dest
    shutil.copy2(AUTOMATIONS_CURRENT, dest)  # info: land the renamed copy in Archive
    AUTOMATIONS_CURRENT.write_text("", encoding="utf-8")  # info: clear the live path for the open poller FD
    return dest.name  # info: return dest . name


# ====================================================
# SECTION: function main
# What it does: Run the minute roll-up or the hour roll-up from the first argument.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(argv if argv is not None else sys.argv[1:])  # info: set args
    mode = (args[0] if args else "").strip().lower()  # info: set mode
    if mode in ("minutes", "minute", "min"):  # info: if mode is the minute roll-up
        count = consolidate_minutes()  # info: set count
        print(f"SUMMARY=ecoflow_layers minutes={count}")  # info: call print
        return 0  # info: return 0
    if mode in ("hours", "hour"):  # info: if mode is the hour roll-up
        count = condense_hours()  # info: set count
        archived = None  # info: set archived
        if datetime.now(HST).minute == 30:  # info: once an hour on the :30 hours job
            archived = archive_automations_log()  # info: call archive_automations_log
        if archived:  # info: if archived
            print(f"SUMMARY=ecoflow_layers hours={count} json=periods.json automations_log={archived}")  # info: call print
        else:  # info: else
            print(f"SUMMARY=ecoflow_layers hours={count} json=periods.json")  # info: call print
        return 0  # info: return 0
    print("usage: consolidate.py minutes|hours", file=sys.stderr)  # info: call print
    return 2  # info: return 2


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
