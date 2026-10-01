# ==============================================================================
# FILE: Communications/Discord/scripts/report_relay.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Post each automated report to its own Discord channel when the file changes.

Reads config/report-channels.json. Skips a missing file and a digest already
posted. Does not call Discord unless RR_DISCORD_POST=1, which the poller sets
only on this job. Does not fetch chat and does not run inference.
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent.parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 , str ( HERE ) )
from lib.api import post_message  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
ECOSYSTEM = HERE.parents[3]  # info: set ECOSYSTEM
ROUTES = HERE / "config" / "report-channels.json"  # info: set ROUTES
DB = Path(os.environ.get("RR_DATABASE_ROOT", str(ECOSYSTEM / "2 - RootRecord-Database")))  # info: set DB
LEDGER = DB / "Communications" / "Discord" / "report-relay-last.json"  # info: set LEDGER
LIMIT = 1900  # info: set LIMIT


# ====================================================
# SECTION: function load_routes
# What it does: Return the report list from config, or an empty list.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_routes(path: Path | None = None) -> list[dict]:  # info: def load_routes
    """Return the report list from config, or an empty list."""  # info: docstring
    raw = path or ROUTES  # info: set raw
    try:  # info: try
        data = json.loads(raw.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except
        return []  # info: return [ ]
    rows = data.get("reports") if isinstance(data, dict) else None  # info: set rows
    return [row for row in rows or [] if isinstance(row, dict) and row.get("channel_id") and row.get("source")]  # info: return rows


# ====================================================
# SECTION: function digest
# What it does: Hash the file bytes so an unchanged report is not posted again.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def digest(text: str) -> str:  # info: def digest
    """Hash the file bytes so an unchanged report is not posted again."""  # info: docstring
    return hashlib.sha256(text.encode("utf-8")).hexdigest()  # info: return hashlib


# ====================================================
# SECTION: function clip
# What it does: Keep the measured report and drop the spoken section before the Discord length cap.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clip(text: str, limit: int = LIMIT) -> str:  # info: def clip
    """Keep the measured report and drop the spoken section before the Discord length cap."""  # info: docstring
    body = text  # info: set body
    mark = body.find("\n## Spoken")  # info: set mark
    if mark > 0:  # info: if mark > 0
        body = body[:mark]  # info: set body
    body = body.strip()  # info: set body
    if len(body) <= limit:  # info: if len ( body ) <= limit
        return body  # info: return body
    return body[: limit - 20].rstrip() + "\n… truncated."  # info: return truncated


# ====================================================
# SECTION: function load_ledger
# What it does: Return the last posted digest for each report key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_ledger(path: Path | None = None) -> dict:  # info: def load_ledger
    """Return the last posted digest for each report key."""  # info: docstring
    raw = path or LEDGER  # info: set raw
    try:  # info: try
        data = json.loads(raw.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except
        return {}  # info: return { }
    posted = data.get("posted") if isinstance(data, dict) else None  # info: set posted
    return posted if isinstance(posted, dict) else {}  # info: return posted


# ====================================================
# SECTION: function save_ledger
# What it does: Write the digest ledger without leaving a partial file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_ledger(posted: dict, path: Path | None = None) -> None:  # info: def save_ledger
    """Write the digest ledger without leaving a partial file."""  # info: docstring
    raw = path or LEDGER  # info: set raw
    raw.parent.mkdir(parents=True, exist_ok=True)  # info: mkdir
    payload = {  # info: set payload
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),  # info: updated_at
        "posted": posted,  # info: posted
    }  # info: }
    tmp = raw.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: write tmp
    os.replace(tmp, raw)  # info: os . replace


# ====================================================
# SECTION: function plan
# What it does: Decide which reports are new. Does not call Discord.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def plan(routes: list[dict], posted: dict, root: Path) -> list[dict]:  # info: def plan
    """Decide which reports are new. Does not call Discord."""  # info: docstring
    ready = []  # info: set ready
    for row in routes:  # info: for row in routes
        key = str(row.get("key") or row.get("name") or "")  # info: set key
        path = root / str(row.get("source") or "")  # info: set path
        if not key or not path.is_file():  # info: if not key or not path
            continue  # info: continue
        text = path.read_text(encoding="utf-8", errors="replace")  # info: set text
        snap = digest(text)  # info: set snap
        if posted.get(key) == snap:  # info: if already posted
            continue  # info: continue
        body = clip(text)  # info: set body
        if not body:  # info: if not body
            continue  # info: continue
        ready.append({"key": key, "channel_id": str(row["channel_id"]), "digest": snap, "body": body})  # info: append
    return ready  # info: return ready


# ====================================================
# SECTION: function relay
# What it does: Post planned reports and remember the digests that Discord accepted.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def relay(routes: list[dict] | None = None, posted: dict | None = None, root: Path | None = None, post=post_message) -> list[str]:  # info: def relay
    """Post planned reports and remember the digests that Discord accepted."""  # info: docstring
    rows = routes if routes is not None else load_routes()  # info: set rows
    ledger = dict(posted if posted is not None else load_ledger())  # info: set ledger
    base = root or ECOSYSTEM  # info: set base
    lines = []  # info: set lines
    for item in plan(rows, ledger, base):  # info: for item in plan
        if lines:  # info: if lines
            time.sleep(0.4)  # info: time . sleep ( 0.4 )
        result = post(item["channel_id"], item["body"])  # info: set result
        if not isinstance(result, dict):  # info: if the pipe held the post
            lines.append(f"held {item['key']}")  # info: append held
            continue  # info: continue
        ledger[item["key"]] = item["digest"]  # info: remember digest
        lines.append(f"posted {item['key']}")  # info: append posted
    if any(line.startswith("posted ") for line in lines):  # info: if any posted
        save_ledger(ledger)  # info: save ledger
    return lines  # info: return lines


# ====================================================
# SECTION: function main
# What it does: Relay current reports and print one status line per change.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    """Relay current reports and print one status line per change."""  # info: docstring
    lines = relay()  # info: set lines
    if not lines:  # info: if not lines
        print("same")  # info: print same
        return 0  # info: return 0
    print("\n".join(lines))  # info: print lines
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__
    raise SystemExit(main())  # info: raise SystemExit
