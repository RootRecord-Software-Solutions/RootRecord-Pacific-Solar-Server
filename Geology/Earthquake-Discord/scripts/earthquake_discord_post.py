# ==============================================================================
# FILE: Geology/Earthquake-Discord/scripts/earthquake_discord_post.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Format Database Geology earthquake files for Discord. Dry-run by default.

Reads hawaii-last.json and global-last.json written by geology_collect.py.
Does not fetch USGS, attach audio, or play the speaker.

  python3 earthquake_discord_post.py           # print the message; write nothing
  python3 earthquake_discord_post.py --send    # hand the text to Communications/Discord

--send still does not call Discord unless the pipe's RR_DISCORD_POST=1 gate is set.
That gate is not set here.
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent.parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,

from lib.envload import channel_id  # noqa: E402

PACIFIC = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server")  # info: set PACIFIC
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
QUAKES = DB / "Geology" / "Earthquakes"  # info: set QUAKES
OUT = DB / "Geology" / "Earthquake-Discord"  # info: set OUT
LOG_DIR = DB / "Logs" / "Geology" / "Earthquake-Discord"  # info: set LOG_DIR
POSTED = OUT / "posted-last.json"  # info: set POSTED
PIPE = PACIFIC / "Communications" / "Discord"  # info: set PIPE
MAX_LINES = 6  # info: set MAX_LINES


# ====================================================
# SECTION: function load_json
# What it does: load json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_json(path: Path) -> dict | None:  # info: def load_json
    if not path.is_file():  # info: if not path . is_file ( ) :
        return None  # info: return None
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return None  # info: return None
    return data if isinstance(data, dict) else None  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function events
# What it does: events.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def events(bundle: dict | None) -> list[dict]:  # info: def events
    if not bundle:  # info: if not bundle :
        return []  # info: return [ ]
    raw = bundle.get("events") or []  # info: set raw
    return [e for e in raw if isinstance(e, dict) and e.get("id")]  # info: return [ e for e in raw if


# ====================================================
# SECTION: function seen_ids
# What it does: seen ids.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def seen_ids(posted: dict | None) -> set[str]:  # info: def seen_ids
    if not posted:  # info: if not posted :
        return set()  # info: return set ( )
    raw = posted.get("seen_ids") or []  # info: set raw
    return {str(i) for i in raw if i}  # info: return { str ( i ) for i


# ====================================================
# SECTION: function section
# What it does: section.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def section(label: str, bundle: dict | None, seen: set[str]) -> list[str]:  # info: def section
    if bundle is None:  # info: if bundle is None :
        return [f"{label}: data is not on file."]  # info: return [ f" { label } : data is not on file. "
    ev = events(bundle)  # info: set ev
    fresh = [e for e in ev if str(e.get("id")) not in seen]  # info: set fresh
    count = bundle.get("count")  # info: set count
    m25 = bundle.get("count_m25")  # info: set m25
    lines = [  # info: set lines
        f"{label} 24 h: {count if count is not None else len(ev)} (M2.5+ {m25 if m25 is not None else 'n/a'}). New since last post: {len(fresh)}."  # info: f" { label } 24 h: { count if
    ]  # info: ]
    for e in fresh[:MAX_LINES]:  # info: for e in fresh [ : MAX_LINES ]
        lines.append(f"- M{e.get('mag')} {e.get('place')}")  # info: lines . append ( f" - M { e
    extra = len(fresh) - MAX_LINES  # info: set extra
    if extra > 0:  # info: if extra > 0 :
        lines.append(f"- and {extra} more.")  # info: lines . append ( f" - and { extra
    return lines  # info: return lines


# ====================================================
# SECTION: function build_message
# What it does: build message.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_message(hawaii: dict | None, global_: dict | None, seen: set[str]) -> str:  # info: def build_message
    collected = (hawaii or global_ or {}).get("at") or "n/a"  # info: set collected
    lines = [f"Earthquake report. Collected {collected}.", ""]  # info: set lines
    lines.extend(section("Hawaii", hawaii, seen))  # info: lines . extend ( section ( "Hawaii" ,
    lines.append("")  # info: lines . append ( "" )
    lines.extend(section("Global", global_, seen))  # info: lines . extend ( section ( "Global" ,
    return "\n".join(lines).strip() + "\n"  # info: return "\n" . join ( lines ) .


# ====================================================
# SECTION: function source_digest
# What it does: Digest the collector snapshot, not the rendered 'new since last post' lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def source_digest(hawaii: dict | None, global_: dict | None) -> str:  # info: def source_digest
    """Digest the collector snapshot, not the rendered 'new since last post' lines."""  # info: """Digest the collector snapshot, not the rendered 'new since last post' lines."""
    payload = {  # info: set payload
        "hawaii_ids": [str(e["id"]) for e in events(hawaii)],  # info: "hawaii_ids" : [ str ( e [ "id"
        "global_ids": [str(e["id"]) for e in events(global_)],  # info: "global_ids" : [ str ( e [ "id"
        "hawaii_count": None if not hawaii else hawaii.get("count"),  # info: "hawaii_count" : None if not hawaii else hawaii
        "global_count": None if not global_ else global_.get("count"),  # info: "global_count" : None if not global_ else global_
    }  # info: }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)  # info: set raw
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()  # info: return hashlib . sha256 ( raw . encode


# ====================================================
# SECTION: function remember
# What it does: remember.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def remember(hawaii: dict | None, global_: dict | None, snap: str) -> dict:  # info: def remember
    ids = [str(e["id"]) for e in events(hawaii) + events(global_)]  # info: set ids
    prev = seen_ids(load_json(POSTED))  # info: set prev
    merged = list(prev)  # info: set merged
    for i in ids:  # info: for i in ids :
        if i not in prev:  # info: if i not in prev :
            merged.append(i)  # info: merged . append ( i )
    return {  # info: return {
        "digest": snap,  # info: "digest" : snap ,
        "seen_ids": merged[-400:],  # info: "seen_ids" : merged [ - 400 : ]
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),  # info: "updated_at" : datetime . now ( HST )
        "posted": False,  # info: "posted" : False ,
    }  # info: }


# ====================================================
# SECTION: function write_json
# What it does: write json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_json(path: Path, payload: dict) -> None:  # info: def write_json
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function handoff
# What it does: Hand text to the Discord send pipe in a child process so package names do not collide. The pipe returns without HTTP unless its own gate is set.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def handoff(text: str) -> str:  # info: def handoff
    """Hand text to the Discord send pipe in a child process so package names do not collide.

    The pipe returns without HTTP unless its own gate is set.
    """
    if not (PIPE / "lib" / "api.py").is_file():  # info: if not ( PIPE / "lib" / "api.py"
        return "pipe-missing"  # info: return "pipe-missing"
    if not channel_id():  # info: if not channel_id ( ) :
        return "channel-absent"  # info: return "channel-absent"
    code = (  # info: set code
        "import os, sys\n"  # info: "import os, sys\n"
        "sys.path.insert(0, sys.argv[1])\n"  # info: "sys.path.insert(0, sys.argv[1])\n"
        "from lib.api import post_message\n"  # info: "from lib.api import post_message\n"
        "cid = (os.environ.get('DISCORD_EARTHQUAKE_CHANNEL_ID') or '').strip()\n"  # info: "cid = (os.environ.get('DISCORD_EARTHQUAKE_CHANNEL_ID') or '').strip()\n"
        "result = post_message(cid, sys.stdin.read().strip())\n"  # info: "result = post_message(cid, sys.stdin.read().strip())\n"
        "print('handed' if isinstance(result, dict) else 'pipe-held')\n"  # info: "print('handed' if isinstance(result, dict) else 'pipe-held')\n"
    )  # info: )
    proc = subprocess.run(  # info: set proc
        [sys.executable, "-c", code, str(PIPE)],  # info: [ sys . executable , "-c" , code
        input=text,  # info: set input
        capture_output=True,  # info: set capture_output
        text=True,  # info: set text
        env=os.environ.copy(),  # info: set env
        timeout=20,  # info: set timeout
    )  # info: )
    line = (proc.stdout or "").strip().splitlines()  # info: set line
    return line[-1] if line else "pipe-held"  # info: return line [ - 1 ] if line


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    send = "--send" in sys.argv  # info: set send
    hawaii = load_json(QUAKES / "hawaii-last.json")  # info: set hawaii
    global_ = load_json(QUAKES / "global-last.json")  # info: set global_
    posted = load_json(POSTED)  # info: set posted
    snap = source_digest(hawaii, global_)  # info: set snap
    text = build_message(hawaii, global_, seen_ids(posted))  # info: set text
    if posted and posted.get("digest") == snap:  # info: if posted and posted . get ( "digest"
        print("unchanged")  # info: call print
        return 0  # info: return 0
    if not send:  # info: if not send :
        print(text, end="")  # info: call print
        return 0  # info: return 0
    outcome = handoff(text)  # info: set outcome
    print(outcome)  # info: call print
    if outcome == "handed":  # info: if outcome == "handed" :
        payload = remember(hawaii, global_, snap)  # info: set payload
        payload["posted"] = True  # info: payload [ "posted" ] = True
        write_json(POSTED, payload)  # info: call write_json
        LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
        with (LOG_DIR / "post.log").open("a", encoding="utf-8") as log:  # info: with ( LOG_DIR / "post.log" ) . open
            log.write(f"{payload['updated_at']} outcome={outcome}\n")  # info: log . write ( f" { payload [
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
