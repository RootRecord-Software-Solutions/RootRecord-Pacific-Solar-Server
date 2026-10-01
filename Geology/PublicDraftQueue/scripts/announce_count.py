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
        "sent": False,  # info: "sent" : False ,
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
