# ==============================================================================
# FILE: Products/scripts/Pantry/pantry.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Household food stock. Counts are logged, never invented."""  # info: """Household food stock. Counts are logged, never invented."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
import sys  # info: import sys
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

STORE = Path(  # info: set STORE
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/Pantry/stock.json"  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/Pantry/stock.json"
)  # info: )
NAME_CAP = 80  # info: set NAME_CAP
MAX_ITEMS = 400  # info: set MAX_ITEMS
PANTRY_TAG = re.compile(r"<<<PANTRY\s+(add|use|set)\s+([^>]*?)>>>", re.I)  # info: set PANTRY_TAG


# ====================================================
# SECTION: function _now
# What it does:  now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now() -> str:  # info: def _now
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()) + "-10:00"  # info: return time . strftime ( "%Y-%m-%dT%H:%M:%S" , time


# ====================================================
# SECTION: function slug
# What it does: slug.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def slug(name: str) -> str:  # info: def slug
    raw = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")  # info: set raw
    return (raw or "item")[:48]  # info: return ( raw or "item" ) [ :


# ====================================================
# SECTION: function _load
# What it does:  load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load() -> dict[str, Any]:  # info: def _load
    if not STORE.is_file():  # info: if not STORE . is_file ( ) :
        return {"updated": _now(), "items": [], "aliases": {}}  # info: return { "updated" : _now ( ) ,
    try:  # info: try :
        data = json.loads(STORE.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {"updated": _now(), "items": [], "aliases": {}}  # info: return { "updated" : _now ( ) ,
    return data if isinstance(data, dict) else {"updated": _now(), "items": [], "aliases": {}}  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function _save
# What it does:  save.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _save(data: dict[str, Any]) -> None:  # info: def _save
    STORE.parent.mkdir(parents=True, exist_ok=True)  # info: STORE . parent . mkdir ( parents =
    data = dict(data)  # info: set data
    data["updated"] = _now()  # info: data [ "updated" ] = _now ( )
    tmp = STORE.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(STORE)  # info: tmp . replace ( STORE )


# ====================================================
# SECTION: function _qty
# What it does:  qty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _qty(raw: Any) -> float | str:  # info: def _qty
    if raw is None or raw == "":  # info: if raw is None or raw == ""
        return "some"  # info: return "some"
    if isinstance(raw, (int, float)):  # info: if isinstance ( raw , ( int ,
        return float(raw)  # info: return float ( raw )
    text = str(raw).strip().lower()  # info: set text
    if text in {"some", "a", "an", "few", "leftover", "leftovers"}:  # info: if text in { "some" , "a" ,
        return "some"  # info: return "some"
    try:  # info: try :
        return float(text)  # info: return float ( text )
    except ValueError:  # info: except ValueError :
        return "some"  # info: return "some"


# ====================================================
# SECTION: function _aliases
# What it does:  aliases.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _aliases(data: dict[str, Any]) -> dict[str, str]:  # info: def _aliases
    raw = data.get("aliases") or {}  # info: set raw
    if not isinstance(raw, dict):  # info: if not isinstance ( raw , dict )
        return {}  # info: return { }
    return {slug(str(k)): slug(str(v)) for k, v in raw.items() if k and v}  # info: return { slug ( str ( k )


# ====================================================
# SECTION: function resolve_id
# What it does: resolve id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def resolve_id(name: str, data: dict[str, Any] | None = None) -> str:  # info: def resolve_id
    sid = slug(name)  # info: set sid
    data = data if data is not None else _load()  # info: set data
    aliases = _aliases(data)  # info: set aliases
    return aliases.get(sid, sid)  # info: return aliases . get ( sid , sid


# ====================================================
# SECTION: function items
# What it does: items.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def items() -> list[dict[str, Any]]:  # info: def items
    rows = _load().get("items") or []  # info: set rows
    return [i for i in rows if isinstance(i, dict) and i.get("id")]  # info: return [ i for i in rows if


# ====================================================
# SECTION: function have_ids
# What it does: have ids.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def have_ids() -> set[str]:  # info: def have_ids
    out: set[str] = set()  # info: set out
    data = _load()  # info: set data
    aliases = _aliases(data)  # info: set aliases
    reverse: dict[str, list[str]] = {}  # info: set reverse
    for src, dst in aliases.items():  # info: for src , dst in aliases . items
        reverse.setdefault(dst, []).append(src)  # info: reverse . setdefault ( dst , [ ]
    for row in items():  # info: for row in items ( ) :
        qty = row.get("qty")  # info: set qty
        if qty == 0 or qty == 0.0:  # info: if qty == 0 or qty == 0.0
            continue  # info: continue
        iid = str(row.get("id") or "")  # info: set iid
        if not iid:  # info: if not iid :
            continue  # info: continue
        out.add(iid)  # info: out . add ( iid )
        out.update(reverse.get(iid) or [])  # info: out . update ( reverse . get (
        for a in row.get("aliases") or []:  # info: for a in row . get ( "aliases"
            out.add(slug(str(a)))  # info: out . add ( slug ( str (
    return out  # info: return out


# ====================================================
# SECTION: function get
# What it does: get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def get(name: str) -> dict[str, Any] | None:  # info: def get
    data = _load()  # info: set data
    want = resolve_id(name, data)  # info: set want
    for row in data.get("items") or []:  # info: for row in data . get ( "items"
        if isinstance(row, dict) and row.get("id") == want:  # info: if isinstance ( row , dict ) and
            return row  # info: return row
    return None  # info: return None


# ====================================================
# SECTION: function _bump
# What it does:  bump.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _bump(name: str, delta: float | str, *, unit: str, voice: str, mode: str) -> dict[str, Any]:  # info: def _bump
    name = (name or "").strip()[:NAME_CAP]  # info: set name
    if not name:  # info: if not name :
        return {"ok": False, "error": "empty_name"}  # info: return { "ok" : False , "error" :
    data = _load()  # info: set data
    rows = [i for i in (data.get("items") or []) if isinstance(i, dict)]  # info: set rows
    iid = resolve_id(name, data)  # info: set iid
    row = next((i for i in rows if i.get("id") == iid), None)  # info: set row
    if row is None:  # info: if row is None :
        if mode == "use":  # info: if mode == "use" :
            return {"ok": False, "error": "missing", "id": iid}  # info: return { "ok" : False , "error" :
        if len(rows) >= MAX_ITEMS:  # info: if len ( rows ) >= MAX_ITEMS :
            return {"ok": False, "error": "cap"}  # info: return { "ok" : False , "error" :
        row = {  # info: set row
            "id": iid,  # info: "id" : iid ,
            "name": name,  # info: "name" : name ,
            "qty": 0,  # info: "qty" : 0 ,
            "unit": (unit or "ea")[:16],  # info: call "unit"
            "created": _now(),  # info: "created" : _now ( ) ,
        }  # info: }
        rows.append(row)  # info: rows . append ( row )
    if unit:  # info: if unit :
        row["unit"] = unit[:16]  # info: row [ "unit" ] = unit [ :
    cur = row.get("qty")  # info: set cur
    if mode == "set":  # info: if mode == "set" :
        row["qty"] = delta  # info: row [ "qty" ] = delta
    elif delta == "some" or cur == "some":  # info: elif delta == "some" or cur == "some"
        row["qty"] = "some" if mode == "add" else (0 if mode == "use" else delta)  # info: row [ "qty" ] = "some" if mode
        if mode == "use" and cur == "some":  # info: if mode == "use" and cur == "some"
            row["qty"] = "some"  # info: row [ "qty" ] = "some"
            row["note"] = "used some; count still unknown"  # info: row [ "note" ] = "used some; count still unknown"
    else:  # info: else :
        try:  # info: try :
            base = float(cur or 0)  # info: set base
            change = float(delta)  # info: set change
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            row["qty"] = "some"  # info: row [ "qty" ] = "some"
        else:  # info: else :
            nxt = base + change if mode == "add" else base - change  # info: set nxt
            row["qty"] = nxt if nxt > 0 else 0  # info: row [ "qty" ] = nxt if nxt
    row["updated"] = _now()  # info: row [ "updated" ] = _now ( )
    row["updated_by"] = voice  # info: row [ "updated_by" ] = voice
    data["items"] = rows  # info: data [ "items" ] = rows
    _save(data)  # info: call _save
    return {"ok": True, "id": iid, "qty": row.get("qty"), "unit": row.get("unit"), "action": mode}  # info: return { "ok" : True , "id" :


# ====================================================
# SECTION: function add_item
# What it does: add item.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add_item(name: str, qty: Any = 1, *, unit: str = "ea", voice: str = "cli") -> dict[str, Any]:  # info: def add_item
    return _bump(name, _qty(qty), unit=unit, voice=voice, mode="add")  # info: return _bump ( name , _qty ( qty


# ====================================================
# SECTION: function use_item
# What it does: use item.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def use_item(name: str, qty: Any = 1, *, voice: str = "cli") -> dict[str, Any]:  # info: def use_item
    return _bump(name, _qty(qty), unit="", voice=voice, mode="use")  # info: return _bump ( name , _qty ( qty


# ====================================================
# SECTION: function set_item
# What it does: set item.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_item(name: str, qty: Any, *, unit: str = "ea", voice: str = "cli") -> dict[str, Any]:  # info: def set_item
    return _bump(name, _qty(qty), unit=unit, voice=voice, mode="set")  # info: return _bump ( name , _qty ( qty


# ====================================================
# SECTION: function prompt_lines
# What it does: prompt lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def prompt_lines(*, cap: int = 3500) -> str:  # info: def prompt_lines
    rows = [i for i in items() if i.get("qty") not in (0, 0.0)]  # info: set rows
    lines = ["Pantry stock (logged only):"]  # info: set lines
    if not rows:  # info: if not rows :
        lines.append("- empty on file")  # info: lines . append ( "- empty on file" )
    for row in sorted(rows, key=lambda r: str(r.get("name") or "")):  # info: for row in sorted ( rows , key
        lines.append(f"- {row.get('id')}: {row.get('qty')} {row.get('unit') or 'ea'} ({row.get('name')})")  # info: lines . append ( f" - { row
    blob = "\n".join(lines)  # info: set blob
    if len(blob) > cap:  # info: if len ( blob ) > cap :
        return blob[: cap - 1] + "…"  # info: return blob [ : cap - 1 ]
    return blob  # info: return blob


# ====================================================
# SECTION: function apply_pantry_tags
# What it does: apply pantry tags.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_pantry_tags(raw: str, *, voice: str) -> None:  # info: def apply_pantry_tags
    for kind, body in PANTRY_TAG.findall(raw or ""):  # info: for kind , body in PANTRY_TAG . findall
        parts = [p.strip() for p in (body or "").split("|")]  # info: set parts
        name = parts[0] if parts else ""  # info: set name
        qty = parts[1] if len(parts) > 1 else 1  # info: set qty
        unit = parts[2] if len(parts) > 2 else "ea"  # info: set unit
        k = kind.lower()  # info: set k
        if k == "add":  # info: if k == "add" :
            add_item(name, qty, unit=unit, voice=voice)  # info: call add_item
        elif k == "use":  # info: elif k == "use" :
            use_item(name, qty, voice=voice)  # info: call use_item
        elif k == "set":  # info: elif k == "set" :
            set_item(name, qty, unit=unit, voice=voice)  # info: call set_item


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(argv if argv is not None else sys.argv[1:])  # info: set args
    if not args or args[0] in {"list", "show"}:  # info: if not args or args [ 0 ]
        print(prompt_lines())  # info: call print
        return 0  # info: return 0
    if args[0] == "add" and len(args) > 1:  # info: if args [ 0 ] == "add" and
        name = args[1]  # info: set name
        qty = args[2] if len(args) > 2 else 1  # info: set qty
        unit = args[3] if len(args) > 3 else "ea"  # info: set unit
        if len(args) == 3 and not _looks_qty(args[2]):  # info: if len ( args ) == 3 and
            name = " ".join(args[1:])  # info: set name
            qty = 1  # info: set qty
            unit = "ea"  # info: set unit
        elif len(args) > 4:  # info: elif len ( args ) > 4 :
            name = " ".join(args[1:-2])  # info: set name
            qty = args[-2]  # info: set qty
            unit = args[-1]  # info: set unit
        print(json.dumps(add_item(name, qty, unit=unit, voice="cli")))  # info: call print
        return 0  # info: return 0
    if args[0] == "use" and len(args) > 1:  # info: if args [ 0 ] == "use" and
        qty = args[-1] if len(args) > 2 and _looks_qty(args[-1]) else 1  # info: set qty
        name = " ".join(args[1:-1] if len(args) > 2 and _looks_qty(args[-1]) else args[1:])  # info: set name
        print(json.dumps(use_item(name, qty, voice="cli")))  # info: call print
        return 0  # info: return 0
    if args[0] == "set" and len(args) > 1:  # info: if args [ 0 ] == "set" and
        unit = args[-1] if len(args) > 3 else "ea"  # info: set unit
        qty = args[-2] if len(args) > 3 else (args[-1] if len(args) > 2 else "some")  # info: set qty
        name = " ".join(args[1:-2] if len(args) > 3 else args[1:-1] if len(args) > 2 else args[1:])  # info: set name
        print(json.dumps(set_item(name, qty, unit=unit, voice="cli")))  # info: call print
        return 0  # info: return 0
    print(json.dumps({"ok": False, "error": "usage"}))  # info: call print
    return 2  # info: return 2


# ====================================================
# SECTION: function _looks_qty
# What it does:  looks qty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _looks_qty(text: str) -> bool:  # info: def _looks_qty
    t = (text or "").strip().lower()  # info: set t
    if t in {"some", "a", "an"}:  # info: if t in { "some" , "a" ,
        return True  # info: return True
    try:  # info: try :
        float(t)  # info: call float
        return True  # info: return True
    except ValueError:  # info: except ValueError :
        return False  # info: return False


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
