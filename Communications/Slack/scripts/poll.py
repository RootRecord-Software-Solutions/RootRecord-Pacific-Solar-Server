# ==============================================================================
# FILE: Communications/Slack/scripts/poll.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Slack poller. No token: exit 0, status not_configured, no Slack HTTP.

A present token still does not call Slack and does not post. Posting needs
Alexander's sign-off. RR_SLACK stays unset, so the jobs.py block stays off.

  python3 poll.py
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent.parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,

from lib.envload import bot_token  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
OUT = DB / "Communications" / "Slack"  # info: set OUT
LOG_DIR = DB / "Logs" / "Communications" / "Slack"  # info: set LOG_DIR
LOG_PATH = LOG_DIR / "poll.log"  # info: set LOG_PATH
STATUS_PATH = OUT / "slack-last.json"  # info: set STATUS_PATH


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
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run() -> dict:  # info: def run
    OUT.mkdir(parents=True, exist_ok=True)  # info: OUT . mkdir ( parents = True ,
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    token = bot_token()  # info: set token
    if token:  # info: if token :
        status = "token_present"  # info: set status
    else:  # info: else :
        status = "not_configured"  # info: set status
    payload = {  # info: set payload
        "ok": True,  # info: "ok" : True ,
        "status": status,  # info: "status" : status ,
        "token": "present" if token else "absent",  # info: "token" : "present" if token else "absent" ,
        "http_calls": 0,  # info: "http_calls" : 0 ,
        "posted": False,  # info: "posted" : False ,
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),  # info: "updated_at" : datetime . now ( HST )
    }  # info: }
    write_json(STATUS_PATH, payload)  # info: call write_json
    with LOG_PATH.open("a", encoding="utf-8") as log:  # info: with LOG_PATH . open ( "a" , encoding
        log.write(  # info: log . write (
            f"{payload['updated_at']} status={payload['status']} token={payload['token']} http_calls=0 posted=false\n"  # info: f" { payload [ 'updated_at' ] } status=
        )  # info: )
    return payload  # info: return payload


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    payload = run()  # info: set payload
    print(json.dumps(payload))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
