# ==============================================================================
# FILE: Geology/PublicDraftQueue/scripts/announce_count.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Count queued Kilauea drafts. Does not publish them and does not send unless RR_KILAUEA_DRAFT_SEND=1.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
QUEUE = Path(os.environ.get("RR_KILAUEA_QUEUE", str(DB / "Geology" / "PublicDraftQueue" / "queue")))  # info: set QUEUE
OUT = Path(os.environ.get("RR_KILAUEA_ANNOUNCE_OUT", str(DB / "Geology" / "PublicDraftQueue" / "announce-last.json")))  # info: set OUT


# ====================================================
# SECTION: function send_enabled
# What it does: True only when RR_KILAUEA_DRAFT_SEND=1. Default off.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def send_enabled() -> bool:  # info: def send_enabled
    return os.environ.get("RR_KILAUEA_DRAFT_SEND", "0").strip() == "1"  # info: return os . environ . get ( "RR_KILAUEA_DRAFT_SEND" , "0" ) . strip ( ) == "1"


# ====================================================
# SECTION: function count_drafts
# What it does: How many markdown drafts are queued. Does not publish or delete them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def count_drafts(queue: Path) -> int:  # info: def count_drafts
    if not queue.is_dir():  # info: if not queue . is_dir ( ) :
        return 0  # info: return 0
    return sum(1 for path in queue.glob("*.md") if path.is_file())  # info: return sum ( 1 for path in queue . glob ( "*.md" ) if path . is_file ( ) )


# ====================================================
# SECTION: function sentence
# What it does: The queued-count sentence. Does not say published.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sentence(count: int) -> str:  # info: def sentence
    word = "draft" if count == 1 else "drafts"  # info: set word
    return f"Queued {count} public report {word}."  # info: return f" Queued { count } public report { word } . "


# ====================================================
# SECTION: function maybe_send
# What it does: Posts the count only when RR_KILAUEA_DRAFT_SEND=1. Does not publish the drafts.
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
# What it does: Write the count file. Send stays off unless the send flag is on, and this script still does not post.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    count = count_drafts(QUEUE)  # info: set count
    text = sentence(count)  # info: set text
    payload = {  # info: set payload
        "at": datetime.now().astimezone().isoformat(timespec="seconds"),  # info: "at" : datetime . now ( ) . astimezone ( ) . isoformat ( timespec = "seconds" ) ,
        "count": count,  # info: "count" : count ,
        "text": text,  # info: "text" : text ,
        "sent": bool(maybe_send(text).get("sent")),  # info: "sent" : bool ( maybe_send ( text ) . get ( "sent" ) ) ,
        "send_gate": send_enabled(),  # info: "send_gate" : send_enabled ( ) ,
    }  # info: }
    OUT.parent.mkdir(parents=True, exist_ok=True)  # info: OUT . parent . mkdir ( parents = True , exist_ok = True )
    tmp = OUT.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps ( payload , indent = 2 ) + "\n" , encoding = "utf-8" )
    os.replace(tmp, OUT)  # info: os . replace ( tmp , OUT )
    print(json.dumps({"ok": True, "sent": False, "count": count, "text": text}))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
