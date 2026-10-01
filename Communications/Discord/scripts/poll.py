# ==============================================================================
# FILE: Communications/Discord/scripts/poll.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Discord poller. No token or an empty channel list: exit 0, no Discord HTTP.

Does not post. post_message stays in lib/api.py and returns without HTTP
unless RR_DISCORD_POST=1. That gate stays unset.

The Ava review pipeline stays off unless RR_DISCORD_REVIEW_PIPELINE=1.
It does not run for traffic that does not name Ava.

  python3 poll.py
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import urllib.request  # info: import urllib . request
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent.parent  # info: set HERE
SCRIPTS = HERE / "scripts"  # info: set SCRIPTS
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
sys.path.insert(0, str(SCRIPTS))  # info: sys . path . insert ( 0 , str ( SCRIPTS ) )

from lib.api import post_message  # noqa: E402
from lib.envload import bot_token  # noqa: E402
import review  # noqa: E402

CHANNELS = HERE / "config" / "channels.json"  # info: set CHANNELS
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
OUT = DB / "Communications" / "Discord"  # info: set OUT
LOG_DIR = DB / "Logs" / "Communications" / "Discord"  # info: set LOG_DIR
LOG_PATH = LOG_DIR / "poll.log"  # info: set LOG_PATH
STATUS_PATH = OUT / "status-last.json"  # info: set STATUS_PATH
API = "https://discord.com/api/v10"  # info: set API
TIMEOUT = 15  # info: set TIMEOUT


# ====================================================
# SECTION: function load_channels
# What it does: load channels.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_channels(path: Path) -> list[str]:  # info: def load_channels
    data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    if not isinstance(data, list):  # info: if not isinstance ( data , list )
        raise ValueError("channels must be a JSON list")  # info: raise ValueError ( "channels must be a JSON list" )
    out: list[str] = []  # info: set out
    for item in data:  # info: for item in data :
        if isinstance(item, str) and item.strip():  # info: if isinstance ( item , str ) and
            out.append(item.strip())  # info: out . append ( item . strip (
        elif isinstance(item, dict):  # info: elif isinstance ( item , dict ) :
            cid = item.get("id")  # info: set cid
            if isinstance(cid, str) and cid.strip():  # info: if isinstance ( cid , str ) and
                out.append(cid.strip())  # info: out . append ( cid . strip (
    return out  # info: return out


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
# SECTION: function fetch_messages
# What it does: fetch messages.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_messages(token: str, channel_id: str) -> list:  # info: def fetch_messages
    req = urllib.request.Request(  # info: set req
        f"{API}/channels/{channel_id}/messages?limit=1",  # info: f" { API } /channels/ { channel_id }
        headers={  # info: set headers
            "Authorization": f"Bot {token}",  # info: "Authorization" : f" Bot { token } "
            "User-Agent": "RootRecord-Pacific (rootrecord, 1.0)",  # info: "User-Agent" : "RootRecord-Pacific (rootrecord, 1.0)" ,
        },  # info: } ,
    )  # info: )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:  # info: with urllib . request . urlopen ( req
        payload = json.load(response)  # info: set payload
    return payload if isinstance(payload, list) else []  # info: return payload if isinstance ( payload , list


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run() -> dict:  # info: def run
    OUT.mkdir(parents=True, exist_ok=True)  # info: OUT . mkdir ( parents = True ,
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    channels = load_channels(CHANNELS)  # info: set channels
    token = bot_token()  # info: set token
    http_calls = 0  # info: set http_calls
    polled: list[str] = []  # info: set polled
    review_handled = 0  # info: set review_handled
    review_posted = 0  # info: set review_posted
    review_on = review.pipeline_enabled()  # info: set review_on
    if token and channels:  # info: if token and channels :
        for channel_id in channels:  # info: for channel_id in channels :
            messages = fetch_messages(token, channel_id)  # info: set messages
            http_calls += 1  # info: set http_calls
            polled.append(channel_id)  # info: polled . append ( channel_id )
            outcome = review.apply_review(  # info: set outcome
                channel_id,  # info: channel_id
                messages,  # info: messages
                enabled=review_on,  # info: enabled = review_on
                respond_fn=lambda cid, msgs: review.respond(cid, msgs, post=post_message, log=review.stage_log),  # info: respond_fn = lambda cid , msgs : review . respond
            )  # info: )
            review_handled += int(outcome.get("handled") or 0)  # info: set review_handled
            review_posted += int(outcome.get("posted") or 0)  # info: set review_posted
    payload = {  # info: set payload
        "ok": True,  # info: "ok" : True ,
        "token": "present" if token else "absent",  # info: "token" : "present" if token else "absent" ,
        "channels": len(channels),  # info: "channels" : len ( channels ) ,
        "http_calls": http_calls,  # info: "http_calls" : http_calls ,
        "polled": polled,  # info: "polled" : polled ,
        "posted": review_posted > 0,  # info: "posted" : review_posted > 0 ,
        "review_pipeline": "on" if review_on else "off",  # info: "review_pipeline" : "on" if review_on else "off" ,
        "review_handled": review_handled,  # info: "review_handled" : review_handled ,
        "review_posted": review_posted,  # info: "review_posted" : review_posted ,
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),  # info: "updated_at" : datetime . now ( HST )
    }  # info: }
    write_json(STATUS_PATH, payload)  # info: call write_json
    with LOG_PATH.open("a", encoding="utf-8") as log:  # info: with LOG_PATH . open ( "a" , encoding
        log.write(  # info: log . write (
            f"{payload['updated_at']} token={payload['token']} channels={payload['channels']} http_calls={payload['http_calls']} review={payload['review_pipeline']}\n"  # info: f" { payload [ 'updated_at' ] } token=
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
