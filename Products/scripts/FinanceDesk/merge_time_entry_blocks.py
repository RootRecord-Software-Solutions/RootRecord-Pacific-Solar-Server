# ==============================================================================
# FILE: Products/scripts/FinanceDesk/merge_time_entry_blocks.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""
Merge consecutive time_entries that share category, project, description, and source
into a single row (earliest start, latest end). Reads wrangler JSON export.

Gap tolerance: entries chain if next.start <= prev.end + 2 seconds.

Usage:
  python merge_time_entry_blocks.py --export _all_time.json --out merge-time-blocks.sql
"""

from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from typing import Any, Dict, List, Tuple  # info: from typing import Any , Dict , List

GAP = timedelta(seconds=2)  # info: set GAP


# ====================================================
# SECTION: function parse_iso
# What it does: parse iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_iso(s: str) -> datetime:  # info: def parse_iso
    return datetime.fromisoformat(s.replace("Z", "+00:00"))  # info: return datetime . fromisoformat ( s . replace


# ====================================================
# SECTION: function fmt_z
# What it does: fmt z.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fmt_z(dt: datetime) -> str:  # info: def fmt_z
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")  # info: return dt . astimezone ( timezone . utc


# ====================================================
# SECTION: function key
# What it does: key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def key(e: Dict[str, Any]) -> Tuple[str, str, str, str]:  # info: def key
    return (  # info: return (
        str(e.get("category_id") or ""),  # info: call str
        str(e.get("project_id") or ""),  # info: call str
        str(e.get("description") or ""),  # info: call str
        str(e.get("source") or "manual"),  # info: call str
    )  # info: )


# ====================================================
# SECTION: function sql_escape
# What it does: sql escape.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sql_escape(s: str) -> str:  # info: def sql_escape
    return "'" + s.replace("'", "''") + "'"  # info: return "'" + s . replace ( "'"


# ====================================================
# SECTION: function sql_json
# What it does: sql json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sql_json(obj: Dict[str, Any]) -> str:  # info: def sql_json
    return sql_escape(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))  # info: return sql_escape ( json . dumps ( obj


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--export", required=True)  # info: ap . add_argument ( "--export" , required =
    ap.add_argument("--user-key", default="user:rootrecord@outlook.com")  # info: ap . add_argument ( "--user-key" , default =
    ap.add_argument("--out", required=True)  # info: ap . add_argument ( "--out" , required =
    args = ap.parse_args()  # info: set args

    raw = json.load(open(args.export, encoding="utf-8-sig"))  # info: set raw
    rows = raw[0]["results"]  # info: set rows
    entries: List[Dict[str, Any]] = []  # info: set entries
    for r in rows:  # info: for r in rows :
        d = json.loads(r["doc"])  # info: set d
        d["_rowid"] = r["id"]  # info: d [ "_rowid" ] = r [ "id"
        entries.append(d)  # info: entries . append ( d )

    entries.sort(key=lambda x: parse_iso(x["start_utc"]))  # info: entries . sort ( key = lambda x

    groups: List[List[Dict[str, Any]]] = []  # info: set groups
    g = [entries[0]]  # info: set g
    for e in entries[1:]:  # info: for e in entries [ 1 : ]
        prev = g[-1]  # info: set prev
        ke = parse_iso(prev["end_utc"])  # info: set ke
        s = parse_iso(e["start_utc"])  # info: set s
        if key(e) == key(prev) and s <= ke + GAP:  # info: if key ( e ) == key (
            g.append(e)  # info: g . append ( e )
        else:  # info: else :
            groups.append(g)  # info: groups . append ( g )
            g = [e]  # info: set g
    groups.append(g)  # info: groups . append ( g )

    lines: List[str] = []  # info: set lines
    lines.append(f"-- merge_time_entry_blocks.py user_key={args.user_key}")  # info: lines . append ( f" -- merge_time_entry_blocks.py user_key= { args
    n_del = 0  # info: set n_del
    n_upd = 0  # info: set n_upd

    for gr in groups:  # info: for gr in groups :
        if len(gr) < 2:  # info: if len ( gr ) < 2 :
            continue  # info: continue
        keep = gr[0]  # info: set keep
        rid = str(keep["_rowid"])  # info: set rid
        start = parse_iso(keep["start_utc"])  # info: set start
        end = max(parse_iso(x["end_utc"]) for x in gr)  # info: set end
        created = min(parse_iso(x["created_at"]) for x in gr if x.get("created_at"))  # info: set created
        merged = {k: v for k, v in keep.items() if not k.startswith("_")}  # info: set merged
        merged["id"] = rid  # info: merged [ "id" ] = rid
        merged["user_id"] = args.user_key  # info: merged [ "user_id" ] = args . user_key
        merged["start_utc"] = fmt_z(start)  # info: merged [ "start_utc" ] = fmt_z ( start
        merged["end_utc"] = fmt_z(end)  # info: merged [ "end_utc" ] = fmt_z ( end
        merged["created_at"] = fmt_z(created) if created.tzinfo else created.isoformat() + "Z"  # info: merged [ "created_at" ] = fmt_z ( created
        merged["updated_at"] = fmt_z(end)  # info: merged [ "updated_at" ] = fmt_z ( end

        doc_sql = sql_json(merged)  # info: set doc_sql
        lines.append(  # info: lines . append (
            f"UPDATE bm_owned_row SET doc = {doc_sql}, updated_at = {sql_escape(fmt_z(end))} "  # info: f" UPDATE bm_owned_row SET doc = { doc_sql } , updated_at = { sql_escape
            f"WHERE user_key = {sql_escape(args.user_key)} AND coll = 'time_entries' AND id = {sql_escape(rid)};"  # info: f" WHERE user_key = { sql_escape ( args . user_key
        )  # info: )
        n_upd += 1  # info: set n_upd
        for x in gr[1:]:  # info: for x in gr [ 1 : ]
            oid = str(x["_rowid"])  # info: set oid
            lines.append(  # info: lines . append (
                f"DELETE FROM bm_owned_row WHERE user_key = {sql_escape(args.user_key)} "  # info: f" DELETE FROM bm_owned_row WHERE user_key = { sql_escape ( args . user_key
                f"AND coll = 'time_entries' AND id = {sql_escape(oid)};"  # info: f" AND coll = 'time_entries' AND id = { sql_escape ( oid ) }
            )  # info: )
            n_del += 1  # info: set n_del

    lines.insert(1, f"-- updates={n_upd} deletes={n_del}")  # info: lines . insert ( 1 , f" -- updates=
    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")  # info: call open
    print(f"Wrote {args.out}: {n_upd} merges, {n_del} deletes ({len(lines)-2} SQL lines)")  # info: call print


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
