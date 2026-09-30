# ==============================================================================
# FILE: Products/scripts/FinanceDesk/extract_bm_money_sqlite.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""
Emit bm_owned_row INSERTs for income_entries + expense_entries only from legacy
Windows RootRecord SQLite (`business_data/rootrecord.db`).

Row ids and JSON fields match `import_windows_bm_sqlite.py` so restored rows are
identical to a full import’s money section (safe to re-apply: ON CONFLICT DO UPDATE).

Usage:
  python extract_bm_money_sqlite.py \\
    --db "C:/Users/you/RootRecord/Business Manager/business_data/rootrecord.db" \\
    --email rootrecord@outlook.com \\
    --out scripts/restore-money.sql

Apply:
  npx wrangler d1 execute root-record --remote --file=scripts/restore-money.sql
"""

from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import sqlite3  # info: import sqlite3
import uuid  # info: import uuid
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from typing import Any, Dict, List, Optional  # info: from typing import Any , Dict , List

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # info: set NS


# ====================================================
# SECTION: function stable_id
# What it does: stable id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stable_id(coll: str, old_pk: int) -> str:  # info: def stable_id
    return uuid.uuid5(NS, f"rr:bm-import:v1|{coll}|{old_pk}").hex  # info: return uuid . uuid5 ( NS , f"


# ====================================================
# SECTION: function iso_z
# What it does: iso z.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def iso_z(raw: Optional[str]) -> str:  # info: def iso_z
    if not raw or not str(raw).strip():  # info: if not raw or not str ( raw
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  # info: return datetime . now ( timezone . utc
    s = str(raw).strip()  # info: set s
    if s.endswith("Z"):  # info: if s . endswith ( "Z" ) :
        return s  # info: return s
    if "+" in s or s.count("-") > 2 and "T" in s and s.endswith(("+00:00",)):  # info: if "+" in s or s . count
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")  # info: return datetime . fromisoformat ( s . replace
    if "T" in s and not s.endswith("Z"):  # info: if "T" in s and not s .
        return s + "Z" if not s.endswith("+00:00") else s.replace("+00:00", "Z")  # info: return s + "Z" if not s .
    return s  # info: return s


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
# SECTION: function emit_insert
# What it does: emit insert.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def emit_insert(  # info: def emit_insert
    lines: List[str],  # info: set lines
    user_key: str,  # info: set user_key
    coll: str,  # info: set coll
    row_id: str,  # info: set row_id
    doc: Dict[str, Any],  # info: set doc
    created_at: str,  # info: set created_at
    updated_at: str,  # info: set updated_at
) -> None:  # info: ) -> None :
    lines.append(  # info: lines . append (
        f"INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "  # info: f" INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "
        f"VALUES ({sql_escape(user_key)}, {sql_escape(coll)}, {sql_escape(row_id)}, "  # info: f" VALUES ( { sql_escape ( user_key ) }
        f"{sql_json(doc)}, {sql_escape(created_at)}, {sql_escape(updated_at)}) "  # info: f" { sql_json ( doc ) } ,
        f"ON CONFLICT(user_key, coll, id) DO UPDATE SET "  # info: f" ON CONFLICT(user_key, coll, id) DO UPDATE SET "
        f"doc = excluded.doc, updated_at = excluded.updated_at;"  # info: f" doc = excluded.doc, updated_at = excluded.updated_at; "
    )  # info: )


# ====================================================
# SECTION: function map_funding
# What it does: map funding.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def map_funding(fs: Optional[str]) -> str:  # info: def map_funding
    fs = (fs or "cash").strip().lower()  # info: set fs
    if fs in ("cash", "bank", "credit"):  # info: if fs in ( "cash" , "bank" ,
        return fs  # info: return fs
    return "cash"  # info: return "cash"


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--db", required=True, help="Path to rootrecord.db")  # info: ap . add_argument ( "--db" , required =
    ap.add_argument("--email", required=True)  # info: ap . add_argument ( "--email" , required =
    ap.add_argument("--user-id", type=int, default=1, help="Legacy rr_users id (default 1)")  # info: ap . add_argument ( "--user-id" , type =
    ap.add_argument("--out", required=True)  # info: ap . add_argument ( "--out" , required =
    args = ap.parse_args()  # info: set args

    email = args.email.strip().lower()  # info: set email
    user_key = f"user:{email}"  # info: set user_key
    uid = int(args.user_id)  # info: set uid

    con = sqlite3.connect(args.db)  # info: set con
    con.row_factory = sqlite3.Row  # info: con . row_factory = sqlite3 . Row
    cur = con.cursor()  # info: set cur

    cur.execute(  # info: cur . execute (
        "SELECT * FROM work_categories WHERE user_id = ? ORDER BY sort_order ASC, id ASC",  # info: "SELECT * FROM work_categories WHERE user_id = ? ORDER BY sort_order ASC, id ASC" ,
        (uid,),  # info: call (
    )  # info: )
    cat_old_to_new: Dict[int, str] = {}  # info: set cat_old_to_new
    for c in cur.fetchall():  # info: for c in cur . fetchall ( )
        oid = int(c["id"])  # info: set oid
        cat_old_to_new[oid] = stable_id("categories", oid)  # info: cat_old_to_new [ oid ] = stable_id ( "categories"

    cur.execute(  # info: cur . execute (
        "SELECT * FROM projects WHERE user_id = ? ORDER BY sort_order ASC, id ASC",  # info: "SELECT * FROM projects WHERE user_id = ? ORDER BY sort_order ASC, id ASC" ,
        (uid,),  # info: call (
    )  # info: )
    proj_old_to_new: Dict[int, str] = {}  # info: set proj_old_to_new
    for p in cur.fetchall():  # info: for p in cur . fetchall ( )
        oid = int(p["id"])  # info: set oid
        proj_old_to_new[oid] = stable_id("projects", oid)  # info: proj_old_to_new [ oid ] = stable_id ( "projects"

    lines: List[str] = []  # info: set lines
    lines.append("-- extract_bm_money_sqlite.py (income + expense only; ids match import_windows_bm_sqlite.py)")  # info: lines . append ( "-- extract_bm_money_sqlite.py (income + expense only; ids match import_windows_bm_sqlite.py)
    lines.append(f"-- user_key={user_key} legacy user_id={uid}")  # info: lines . append ( f" -- user_key= { user_key

    cur.execute(  # info: cur . execute (
        "SELECT * FROM income_entries WHERE user_id = ? ORDER BY received_at_utc ASC",  # info: "SELECT * FROM income_entries WHERE user_id = ? ORDER BY received_at_utc ASC" ,
        (uid,),  # info: call (
    )  # info: )
    for inc in cur.fetchall():  # info: for inc in cur . fetchall ( )
        oid = int(inc["id"])  # info: set oid
        nid = stable_id("income_entries", oid)  # info: set nid
        created = iso_z(inc["created_at"])  # info: set created
        updated = iso_z(inc["updated_at"])  # info: set updated
        recv = iso_z(inc["received_at_utc"])  # info: set recv
        doc: Dict[str, Any] = {  # info: set doc
            "id": nid,  # info: "id" : nid ,
            "user_id": user_key,  # info: "user_id" : user_key ,
            "received_at_utc": recv,  # info: "received_at_utc" : recv ,
            "amount_cents": int(inc["amount_cents"] or 0),  # info: "amount_cents" : int ( inc [ "amount_cents" ]
            "currency": inc["currency"] or "USD",  # info: "currency" : inc [ "currency" ] or "USD"
            "description": inc["description"] or "",  # info: "description" : inc [ "description" ] or ""
            "created_at": created,  # info: "created_at" : created ,
            "updated_at": updated,  # info: "updated_at" : updated ,
        }  # info: }
        wcid = inc["work_category_id"]  # info: set wcid
        pid = inc["project_id"]  # info: set pid
        if wcid is not None:  # info: if wcid is not None :
            doc["category_id"] = cat_old_to_new.get(int(wcid))  # info: doc [ "category_id" ] = cat_old_to_new . get
        if pid is not None:  # info: if pid is not None :
            doc["project_id"] = proj_old_to_new.get(int(pid))  # info: doc [ "project_id" ] = proj_old_to_new . get
        emit_insert(lines, user_key, "income_entries", nid, doc, created, updated)  # info: call emit_insert

    cur.execute(  # info: cur . execute (
        "SELECT * FROM expense_entries WHERE user_id = ? ORDER BY spent_at_utc ASC",  # info: "SELECT * FROM expense_entries WHERE user_id = ? ORDER BY spent_at_utc ASC" ,
        (uid,),  # info: call (
    )  # info: )
    for ex in cur.fetchall():  # info: for ex in cur . fetchall ( )
        oid = int(ex["id"])  # info: set oid
        nid = stable_id("expense_entries", oid)  # info: set nid
        created = iso_z(ex["created_at"])  # info: set created
        spent = iso_z(ex["spent_at_utc"])  # info: set spent
        doc = {  # info: set doc
            "id": nid,  # info: "id" : nid ,
            "user_id": user_key,  # info: "user_id" : user_key ,
            "spent_at_utc": spent,  # info: "spent_at_utc" : spent ,
            "amount_cents": int(ex["amount_cents"] or 0),  # info: "amount_cents" : int ( ex [ "amount_cents" ]
            "currency": ex["currency"] or "USD",  # info: "currency" : ex [ "currency" ] or "USD"
            "description": ex["description"] or "",  # info: "description" : ex [ "description" ] or ""
            "funding": map_funding(ex["funding_source"]),  # info: "funding" : map_funding ( ex [ "funding_source" ]
            "created_at": created,  # info: "created_at" : created ,
            "updated_at": created,  # info: "updated_at" : created ,
        }  # info: }
        wcid = ex["work_category_id"]  # info: set wcid
        pid = ex["project_id"]  # info: set pid
        if wcid is not None:  # info: if wcid is not None :
            doc["category_id"] = cat_old_to_new.get(int(wcid))  # info: doc [ "category_id" ] = cat_old_to_new . get
        if pid is not None:  # info: if pid is not None :
            doc["project_id"] = proj_old_to_new.get(int(pid))  # info: doc [ "project_id" ] = proj_old_to_new . get
        emit_insert(lines, user_key, "expense_entries", nid, doc, created, created)  # info: call emit_insert

    with open(args.out, "w", encoding="utf-8") as f:  # info: with open ( args . out , "w"
        f.write("\n".join(lines) + "\n")  # info: f . write ( "\n" . join (
    print(f"Wrote {args.out} ({len(lines)} lines)")  # info: call print


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
