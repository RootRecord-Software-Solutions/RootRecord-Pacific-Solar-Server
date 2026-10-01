# ==============================================================================
# FILE: Communications/Discord/scripts/report_rollups.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Post one 8-hour or noon 24-hour public summary per report channel.

  python3 report_rollups.py 8h
  python3 report_rollups.py 24h

Uses the reports already on disk. Does not invent a missing average.
Discord HTTP still requires RR_DISCORD_POST=1, set only on this job.
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert
from lib.api import post_message  # noqa: E402
from lib.public_report import HST, consolidation, samples, window_for  # noqa: E402

ECOSYSTEM = HERE.parents[3]  # info: set ECOSYSTEM
ROUTES = HERE / "config" / "report-channels.json"  # info: set ROUTES
DB = Path(os.environ.get("RR_DATABASE_ROOT", str(ECOSYSTEM / "2 - RootRecord-Database")))  # info: set DB
LEDGER = DB / "Communications" / "Discord" / "report-rollup-last.json"  # info: set LEDGER


# ====================================================
# SECTION: function load_routes
# What it does: Return report routes that have a channel id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_routes(path: Path | None = None) -> list[dict]:  # info: def load_routes
    """Return report routes that have a channel id."""  # info: docstring
    try:  # info: try
        data = json.loads((path or ROUTES).read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except
        return []  # info: return [ ]
    rows = data.get("reports") if isinstance(data, dict) else None  # info: set rows
    return [row for row in rows or [] if isinstance(row, dict) and row.get("key") and row.get("channel_id")]  # info: return rows


# ====================================================
# SECTION: function load_ledger
# What it does: Return posted window digests.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_ledger(path: Path | None = None) -> dict:  # info: def load_ledger
    """Return posted window digests."""  # info: docstring
    try:  # info: try
        data = json.loads((path or LEDGER).read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except
        return {}  # info: return { }
    posted = data.get("posted") if isinstance(data, dict) else None  # info: set posted
    return posted if isinstance(posted, dict) else {}  # info: return posted


# ====================================================
# SECTION: function save_ledger
# What it does: Write the rollup ledger.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_ledger(posted: dict, path: Path | None = None) -> None:  # info: def save_ledger
    """Write the rollup ledger."""  # info: docstring
    raw = path or LEDGER  # info: set raw
    raw.parent.mkdir(parents=True, exist_ok=True)  # info: mkdir
    payload = {"updated_at": datetime.now(HST).isoformat(timespec="seconds"), "posted": posted}  # info: set payload
    tmp = raw.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: write
    os.replace(tmp, raw)  # info: replace


# ====================================================
# SECTION: function build
# What it does: Build one summary per topic for the previous 8 or 24 hours.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build(hours: int, routes: list[dict], root: Path, now: datetime | None = None) -> list[dict]:  # info: def build
    """Build one summary per topic for the previous 8 or 24 hours."""  # info: docstring
    start, end = window_for(hours, now)  # info: set start , end
    ready = []  # info: set ready
    for row in routes:  # info: for row in routes
        key = str(row["key"])  # info: set key
        slug = str(row.get("name") or key)  # info: set slug
        text = consolidation(key, slug, samples(root, key, start, end), hours, start, end)  # info: set text
        snap = hashlib.sha256(text.encode("utf-8")).hexdigest()  # info: set snap
        ready.append({"key": f"{key}:{hours}:{end.strftime('%Y%m%dT%H')}", "channel_id": str(row["channel_id"]), "digest": snap, "body": text})  # info: append
    return ready  # info: return ready


# ====================================================
# SECTION: function publish
# What it does: Post summaries whose window has not already been sent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def publish(hours: int, routes: list[dict] | None = None, root: Path | None = None, post=post_message, now: datetime | None = None) -> list[str]:  # info: def publish
    """Post summaries whose window has not already been sent."""  # info: docstring
    ledger = load_ledger()  # info: set ledger
    lines = []  # info: set lines
    changed = False  # info: set changed
    for item in build(hours, routes if routes is not None else load_routes(), root or ECOSYSTEM, now):  # info: for item in build
        if ledger.get(item["key"]) == item["digest"]:  # info: if already posted
            continue  # info: continue
        if lines:  # info: if lines
            time.sleep(0.4)  # info: sleep
        result = post(item["channel_id"], item["body"])  # info: set result
        label = item["key"].split(":", 1)[0]  # info: set label
        if not isinstance(result, dict):  # info: if held
            lines.append(f"held {label}")  # info: append
            continue  # info: continue
        ledger[item["key"]] = item["digest"]  # info: remember
        changed = True  # info: set changed
        lines.append(f"posted {label}")  # info: append
    if changed:  # info: if changed
        save_ledger(ledger)  # info: save
    return lines  # info: return lines


# ====================================================
# SECTION: function main
# What it does: Post the 8-hour or 24-hour summaries.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    """Post the 8-hour or 24-hour summaries."""  # info: docstring
    arg = (sys.argv[1] if len(sys.argv) > 1 else "").strip()  # info: set arg
    hours = 8 if arg == "8h" else 24 if arg == "24h" else 0  # info: set hours
    if not hours:  # info: if not hours
        print("usage: report_rollups.py 8h|24h")  # info: print usage
        return 2  # info: return 2
    lines = publish(hours)  # info: set lines
    print("\n".join(lines) if lines else "same")  # info: print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if main
    raise SystemExit(main())  # info: exit
