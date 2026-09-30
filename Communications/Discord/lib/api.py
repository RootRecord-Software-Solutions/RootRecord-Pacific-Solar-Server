# ==============================================================================
# FILE: Communications/Discord/lib/api.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Discord send entry point. Refuses HTTP unless RR_DISCORD_POST=1 and a token exist."""  # info: """Discord send entry point. Refuses HTTP unless RR_DISCORD_POST=1 and a token exist."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import urllib.request  # info: import urllib . request

from lib.envload import bot_token  # info: from lib . envload import bot_token

API = "https://discord.com/api/v10"  # info: set API
TIMEOUT = 15  # info: set TIMEOUT


# ====================================================
# SECTION: function post_message
# What it does: Return None and do not call Discord unless the post gate and token are both set.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def post_message(channel_id: str, content: str) -> dict | None:  # info: def post_message
    """Return None and do not call Discord unless the post gate and token are both set."""  # info: """Return None and do not call Discord unless the post gate and token are both set."""
    if os.environ.get("RR_DISCORD_POST", "0").strip() != "1":  # info: if os . environ . get ( "RR_DISCORD_POST"
        return None  # info: return None
    token = bot_token()  # info: set token
    if not token or not str(channel_id or "").strip() or not str(content or "").strip():  # info: if not token or not str ( channel_id
        return None  # info: return None
    body = json.dumps(  # info: set body
        {  # info: {
            "content": str(content)[:2000],  # info: "content" : str ( content ) [ :
            "allowed_mentions": {"parse": []},  # info: "allowed_mentions" : { "parse" : [ ] }
        }  # info: }
    ).encode()  # info: ) . encode ( )
    req = urllib.request.Request(  # info: set req
        f"{API}/channels/{channel_id}/messages",  # info: f" { API } /channels/ { channel_id }
        data=body,  # info: set data
        headers={  # info: set headers
            "Authorization": f"Bot {token}",  # info: "Authorization" : f" Bot { token } "
            "Content-Type": "application/json; charset=utf-8",  # info: "Content-Type" : "application/json; charset=utf-8" ,
            "User-Agent": "RootRecord-Pacific (rootrecord, 1.0)",  # info: "User-Agent" : "RootRecord-Pacific (rootrecord, 1.0)" ,
        },  # info: } ,
        method="POST",  # info: set method
    )  # info: )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:  # info: with urllib . request . urlopen ( req
        payload = json.load(response)  # info: set payload
    return payload if isinstance(payload, dict) else None  # info: return payload if isinstance ( payload , dict
