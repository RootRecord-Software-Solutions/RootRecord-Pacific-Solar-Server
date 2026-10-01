# ==============================================================================
# FILE: Media/Voice/scripts/note_draft.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Turn one notes.jsonl line into a work-order draft. Does not build and does not call development.execute_work_order.

Stays off unless RR_NOTE_DRAFT=1.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
LIB = Path(os.environ.get("RR_LIBRARY_ROOT", "/home/rootrecord/RootRecord-Ecosystem/5 - RootRecord-Library"))  # info: set LIB
NOTES = Path(os.environ.get("RR_VOICE_NOTES", str(DB / "Communications" / "VoiceDeliver" / "notes.jsonl")))  # info: set NOTES
CURSOR = Path(os.environ.get("RR_NOTE_DRAFT_CURSOR", str(DB / "Communications" / "VoiceDeliver" / "note-draft-cursor.json")))  # info: set CURSOR
DRAFTS = Path(os.environ.get("RR_NOTE_DRAFT_DIR", str(LIB / "Documentation" / "06-development" / "Work-Orders" / "drafts")))  # info: set DRAFTS


# ====================================================
# SECTION: function gate_on
# What it does: True only when RR_NOTE_DRAFT=1. Default off.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def gate_on() -> bool:  # info: def gate_on
    return os.environ.get("RR_NOTE_DRAFT", "0").strip() == "1"  # info: return os . environ . get ( "RR_NOTE_DRAFT" , "0" ) . strip ( ) == "1"


# ====================================================
# SECTION: function load_notes
# What it does: Read notes.jsonl lines. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_notes(path: Path) -> list[dict]:  # info: def load_notes
    if not path.is_file():  # info: if not path . is_file ( ) :
        return []  # info: return [ ]
    rows = []  # info: set rows
    for line in path.read_text(encoding="utf-8").splitlines():  # info: for line in path . read_text ( encoding = "utf-8" ) . splitlines ( ) :
        if not line.strip():  # info: if not line . strip ( ) :
            continue  # info: continue
        try:  # info: try :
            row = json.loads(line)  # info: set row
        except ValueError:  # info: except ValueError :
            continue  # info: continue
        if isinstance(row, dict):  # info: if isinstance ( row , dict ) :
            rows.append(row)  # info: rows . append ( row )
    return rows  # info: return rows


# ====================================================
# SECTION: function draft_body
# What it does: One work-order draft. It does not authorize a build.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def draft_body(note: dict) -> str:  # info: def draft_body
    report = str(note.get("report") or "report")  # info: set report
    text = str(note.get("text") or "").strip()  # info: set text
    reply_to = note.get("reply_to")  # info: set reply_to
    return (  # info: return (
        f"# Note draft — {report}\n\n"  # info: f" # Note draft — { report } \n\n "
        f"Source: VoiceDeliver/notes.jsonl\n"  # info: f" Source: VoiceDeliver/notes.jsonl \n "
        f"Reply to message {reply_to}\n\n"  # info: f" Reply to message { reply_to } \n\n "
        f"{text}\n\n"  # info: f" { text } \n\n "
        "This is a draft. It does not authorize a build.\n"  # info: "This is a draft. It does not authorize a build.\n"
    )  # info: )


# ====================================================
# SECTION: function write_one
# What it does: Write the next unprocessed note as a draft. Does not call a work-order executor.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_one(notes: list[dict], cursor: int, drafts: Path) -> dict:  # info: def write_one
    if cursor >= len(notes):  # info: if cursor >= len ( notes ) :
        return {"ok": True, "written": False, "cursor": cursor, "detail": "no new note"}  # info: return { "ok" : True , "written" : False , "cursor" : cursor , "detail" : "no new note" }
    note = notes[cursor]  # info: set note
    report = str(note.get("report") or "report").replace("/", "-")  # info: set report
    drafts.mkdir(parents=True, exist_ok=True)  # info: drafts . mkdir ( parents = True , exist_ok = True )
    path = drafts / f"note-{cursor + 1}-{report}.md"  # info: set path
    path.write_text(draft_body(note), encoding="utf-8")  # info: path . write_text ( draft_body ( note ) , encoding = "utf-8" )
    return {"ok": True, "written": True, "cursor": cursor + 1, "path": str(path)}  # info: return { "ok" : True , "written" : True , "cursor" : cursor + 1 , "path" : str ( path ) }


# ====================================================
# SECTION: function main
# What it does: Gate off by default. One draft when the gate is on. No build.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if not gate_on():  # info: if not gate_on ( ) :
        print(json.dumps({"ok": True, "written": False, "detail": "gate off"}))  # info: call print
        return 0  # info: return 0
    notes = load_notes(NOTES)  # info: set notes
    try:  # info: try :
        cursor = int(json.loads(CURSOR.read_text(encoding="utf-8")).get("cursor", 0)) if CURSOR.is_file() else 0  # info: set cursor
    except (OSError, ValueError, TypeError):  # info: except ( OSError , ValueError , TypeError ) :
        cursor = 0  # info: set cursor
    result = write_one(notes, cursor, DRAFTS)  # info: set result
    CURSOR.parent.mkdir(parents=True, exist_ok=True)  # info: CURSOR . parent . mkdir ( parents = True , exist_ok = True )
    CURSOR.write_text(json.dumps({"cursor": result["cursor"]}) + "\n", encoding="utf-8")  # info: CURSOR . write_text ( json . dumps ( { "cursor" : result [ "cursor" ] } ) + "\n" , encoding = "utf-8" )
    print(json.dumps(result))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
