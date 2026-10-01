# ==============================================================================
# FILE: Communications/PublicHealth/scripts/public_health.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Check the five public radio and origin URLs. Writes a status file. Does not start port 8787.

Send stays off unless RR_PUBLIC_HEALTH_SEND=1. The job itself stays off unless RR_PUBLIC_HEALTH=1.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
OUT = Path(os.environ.get("RR_PUBLIC_HEALTH_OUT", str(DB / "Communications" / "PublicHealth" / "latest.json")))  # info: set OUT
CHECKS = [  # info: set CHECKS
    ("radio-page-origin", "https://origin.avaivy.cloud/radio"),  # info: ( "radio-page-origin" , "https://origin.avaivy.cloud/radio" ) ,
    ("radio-status-origin", "https://origin.avaivy.cloud/api/radio/status"),  # info: ( "radio-status-origin" , "https://origin.avaivy.cloud/api/radio/status" ) ,
    ("status-local", "http://127.0.0.1:8787/status"),  # info: ( "status-local" , "http://127.0.0.1:8787/status" ) ,
    ("radio-local", "http://127.0.0.1:8787/radio"),  # info: ( "radio-local" , "http://127.0.0.1:8787/radio" ) ,
    ("radio-status-local", "http://127.0.0.1:8787/api/radio/status"),  # info: ( "radio-status-local" , "http://127.0.0.1:8787/api/radio/status" ) ,
]  # info: ]


# ====================================================
# SECTION: function send_enabled
# What it does: True only when RR_PUBLIC_HEALTH_SEND=1. Default off.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def send_enabled() -> bool:  # info: def send_enabled
    return os.environ.get("RR_PUBLIC_HEALTH_SEND", "0").strip() == "1"  # info: return os . environ . get ( "RR_PUBLIC_HEALTH_SEND" , "0" ) . strip ( ) == "1"


# ====================================================
# SECTION: function probe
# What it does: One HTTP GET. Does not start a service.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def probe(url: str) -> dict:  # info: def probe
    req = urllib.request.Request(url, method="GET")  # info: set req
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=5) as response:  # info: with urllib . request . urlopen ( req , timeout = 5 ) as response :
            code = int(response.status)  # info: set code
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc :
        code = int(exc.code)  # info: set code
        return {"url": url, "up": 200 <= code < 400, "status": code}  # info: return { "url" : url , "up" : 200 <= code < 400 , "status" : code }
    except (urllib.error.URLError, TimeoutError, OSError):  # info: except ( urllib . error . URLError , TimeoutError , OSError ) :
        return {"url": url, "up": False, "status": None}  # info: return { "url" : url , "up" : False , "status" : None }
    return {"url": url, "up": 200 <= code < 400, "status": code}  # info: return { "url" : url , "up" : 200 <= code < 400 , "status" : code }


# ====================================================
# SECTION: function not_up
# What it does: Names that are down. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def not_up(rows: list[dict]) -> list[str]:  # info: def not_up
    return [row["name"] for row in rows if not row.get("up")]  # info: return [ row [ "name" ] for row in rows if not row . get ( "up" ) ]


# ====================================================
# SECTION: function maybe_send
# What it does: Ava posts the down list only when RR_PUBLIC_HEALTH_SEND=1. Default returns without a request.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def maybe_send(text: str) -> dict:  # info: def maybe_send
    if not send_enabled() or not text.strip():  # info: if not send_enabled ( ) or not text . strip ( ) :
        return {"ok": True, "sent": False, "detail": "send gate off"}  # info: return { "ok" : True , "sent" : False , "detail" : "send gate off" }
    import sys  # info: import sys
    voice = Path(__file__).resolve().parents[3] / "Media" / "Voice" / "scripts"  # info: set voice
    if str(voice) not in sys.path:  # info: if str ( voice ) not in sys . path :
        sys.path.insert(0, str(voice))  # info: sys . path . insert ( 0 , str ( voice ) )
    import voice_deliver  # info: import voice_deliver
    cfg = voice_deliver.load_kv(voice_deliver.RELAY)  # info: set cfg
    voice_deliver.load_secrets(cfg)  # info: call voice_deliver . load_secrets
    token = (os.environ.get("TELEGRAM_AVA_TOKEN") or "").strip()  # info: set token
    chat = voice_deliver.chat_id(cfg)  # info: set chat
    if not token or not chat:  # info: if not token or not chat :
        return {"ok": False, "sent": False, "detail": "missing token or chat"}  # info: return { "ok" : False , "sent" : False , "detail" : "missing token or chat" }
    body = json.dumps({"chat_id": chat, "text": text[:3500], "disable_web_page_preview": True}).encode()  # info: set body
    result = voice_deliver.post(token, "sendMessage", body, "application/json")  # info: set result
    return {"ok": bool(result.get("ok")), "sent": bool(result.get("ok")), "detail": "sendMessage"}  # info: return { "ok" : bool ( result . get ( "ok" ) ) , "sent" : bool ( result . get ( "ok" ) ) , "detail" : "sendMessage" }


# ====================================================
# SECTION: function main
# What it does: Write the status file. Send stays off unless the send flag is on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    rows = []  # info: set rows
    for name, url in CHECKS:  # info: for name , url in CHECKS :
        row = probe(url)  # info: set row
        row["name"] = name  # info: row [ "name" ] = name
        rows.append(row)  # info: rows . append ( row )
    down = not_up(rows)  # info: set down
    payload = {  # info: set payload
        "at": datetime.now().astimezone().isoformat(timespec="seconds"),  # info: "at" : datetime . now ( ) . astimezone ( ) . isoformat ( timespec = "seconds" ) ,
        "checks": rows,  # info: "checks" : rows ,
        "not_fully_up": down,  # info: "not_fully_up" : down ,
        "sent": False,  # info: "sent" : False ,
    }  # info: }
    if down:  # info: if down :
        said = "Not fully up: " + ", ".join(down)  # info: set said
        payload["would_say"] = said  # info: payload [ "would_say" ] = said
        delivery = maybe_send(said)  # info: set delivery
        payload["sent"] = bool(delivery.get("sent"))  # info: payload [ "sent" ] = bool ( delivery . get ( "sent" ) )
    OUT.parent.mkdir(parents=True, exist_ok=True)  # info: OUT . parent . mkdir ( parents = True , exist_ok = True )
    tmp = OUT.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps ( payload , indent = 2 ) + "\n" , encoding = "utf-8" )
    os.replace(tmp, OUT)  # info: os . replace ( tmp , OUT )
    print(json.dumps({"ok": True, "sent": False, "not_fully_up": down, "path": str(OUT)}))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
