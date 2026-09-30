# ==============================================================================
# FILE: Products/scripts/FinanceDesk/import_windows_bm_sqlite.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""
Emit SQL for Cloudflare D1 `bm_owned_row` from the legacy Windows / Electron
RootRecord Business Manager SQLite (`business_data/rootrecord.db`).

Stable row ids (uuid5 hex, 32 chars) so re-running the same import updates rows
instead of duplicating.

Usage:
  python import_windows_bm_sqlite.py \\
    --db "C:/Users/you/RootRecord/Business Manager/business_data/rootrecord.db" \\
    --email rootrecord@outlook.com \\
    --out import-bm.sql

Apply to remote D1 (with credentials in env, same as deploy.ps1):
  cd Web/cloudflare/rootrecord-primary
  npx wrangler d1 execute root-record --remote --file=scripts/import-bm.sql

Before first import, optionally wipe existing BM rows for that user:
  npx wrangler d1 execute root-record --remote --command=\\
    "DELETE FROM bm_owned_row WHERE user_key = 'user:rootrecord@outlook.com';"

Note: Do not wrap statements in BEGIN/COMMIT; remote D1 rejects explicit SQL transactions.
"""

from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import sqlite3  # info: import sqlite3
import uuid  # info: import uuid
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from typing import Any, Dict, List, Optional  # info: from typing import Any , Dict , List


NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # UUID URL namespace


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
    # SQLite "2026-04-09T00:53:11.000" etc.
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
# SECTION: function map_kind
# What it does: map kind.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def map_kind(k: Optional[str]) -> str:  # info: def map_kind
    k = (k or "time").strip().lower()  # info: set k
    if k in ("time", "expense", "both"):  # info: if k in ( "time" , "expense" ,
        if k == "both":  # info: if k == "both" :
            return "time"  # info: return "time"
        return k  # info: return k
    return "time"  # info: return "time"


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
    ap.add_argument("--email", required=True, help="Portal email (e.g. rootrecord@outlook.com)")  # info: ap . add_argument ( "--email" , required =
    ap.add_argument("--user-id", type=int, default=1, help="rr_users.telegram_user_id / local user id (default 1)")  # info: ap . add_argument ( "--user-id" , type =
    ap.add_argument("--out", default="-", help="Output SQL path, or - for stdout")  # info: ap . add_argument ( "--out" , default =
    args = ap.parse_args()  # info: set args

    email = args.email.strip().lower()  # info: set email
    user_key = f"user:{email}"  # info: set user_key
    uid = int(args.user_id)  # info: set uid

    con = sqlite3.connect(args.db)  # info: set con
    con.row_factory = sqlite3.Row  # info: con . row_factory = sqlite3 . Row
    cur = con.cursor()  # info: set cur

    lines: List[str] = []  # info: set lines
    lines.append("-- Generated by import_windows_bm_sqlite.py")  # info: lines . append ( "-- Generated by import_windows_bm_sqlite.py" )
    lines.append(f"-- user_key = {user_key}")  # info: lines . append ( f" -- user_key = { user_key
    # Remote D1 rejects SQL BEGIN TRANSACTION / COMMIT (use separate statements only).

    # --- business_profiles -> businesses
    cur.execute(  # info: cur . execute (
        "SELECT * FROM business_profiles WHERE user_id = ? ORDER BY archived ASC, id ASC",  # info: "SELECT * FROM business_profiles WHERE user_id = ? ORDER BY archived ASC, id ASC" ,
        (uid,),  # info: call (
    )  # info: )
    profiles = cur.fetchall()  # info: set profiles
    default_set = False  # info: set default_set
    for p in profiles:  # info: for p in profiles :
        pid = stable_id("businesses", int(p["id"]))  # info: set pid
        now = iso_z(p["updated_at"] if p["updated_at"] else p["created_at"])  # info: set now
        created = iso_z(p["created_at"])  # info: set created
        archived = int(p["archived"] or 0)  # info: set archived
        is_def = not archived and not default_set  # info: set is_def
        if is_def:  # info: if is_def :
            default_set = True  # info: set default_set
        doc = {  # info: set doc
            "id": pid,  # info: "id" : pid ,
            "user_id": user_key,  # info: "user_id" : user_key ,
            "name": p["name"] or "Business",  # info: "name" : p [ "name" ] or "Business"
            "legal_name": p["legal_name"] or "",  # info: "legal_name" : p [ "legal_name" ] or ""
            "owner": p["owner"] or "",  # info: "owner" : p [ "owner" ] or ""
            "tax_id": p["tax_id"] or "",  # info: "tax_id" : p [ "tax_id" ] or ""
            "email": p["email"] or "",  # info: "email" : p [ "email" ] or ""
            "phone": p["phone"] or "",  # info: "phone" : p [ "phone" ] or ""
            "website": p["website"] or "",  # info: "website" : p [ "website" ] or ""
            "address": p["address"] or "",  # info: "address" : p [ "address" ] or ""
            "timezone": p["timezone"] or "system",  # info: "timezone" : p [ "timezone" ] or "system"
            "invoice_notes": p["invoice_notes"] or "",  # info: "invoice_notes" : p [ "invoice_notes" ] or ""
            "is_default": bool(is_def),  # info: "is_default" : bool ( is_def ) ,
            "created_at": created,  # info: "created_at" : created ,
            "updated_at": now,  # info: "updated_at" : now ,
        }  # info: }
        emit_insert(lines, user_key, "businesses", pid, doc, created, now)  # info: call emit_insert

    # --- work_categories -> categories (preserve sort_order)
    cur.execute(  # info: cur . execute (
        "SELECT * FROM work_categories WHERE user_id = ? ORDER BY sort_order ASC, id ASC",  # info: "SELECT * FROM work_categories WHERE user_id = ? ORDER BY sort_order ASC, id ASC" ,
        (uid,),  # info: call (
    )  # info: )
    cats = cur.fetchall()  # info: set cats
    cat_old_to_new: Dict[int, str] = {}  # info: set cat_old_to_new
    for c in cats:  # info: for c in cats :
        oid = int(c["id"])  # info: set oid
        nid = stable_id("categories", oid)  # info: set nid
        cat_old_to_new[oid] = nid  # info: cat_old_to_new [ oid ] = nid
        # Legacy `work_categories` has no created_at column.
        created = now_iso()  # info: set created
        updated = created  # info: set updated
        so = int(c["sort_order"] or 0)  # info: set so
        # Preserve legacy ordering when many rows share the same sort_order (Windows used id as tie-break).
        cloud_sort = so * 100_000 + oid  # info: set cloud_sort
        doc = {  # info: set doc
            "id": nid,  # info: "id" : nid ,
            "user_id": user_key,  # info: "user_id" : user_key ,
            "name": c["name"] or "Unnamed",  # info: "name" : c [ "name" ] or "Unnamed"
            "color": c["color"] or "#2B8A8F",
            "icon": c["icon"] or "",  # info: "icon" : c [ "icon" ] or ""
            "kind": map_kind(c["kind"]),  # info: "kind" : map_kind ( c [ "kind" ]
            "billable": int(c["billable"] if c["billable"] is not None else 1),  # info: "billable" : int ( c [ "billable" ]
            "archived": int(c["archived"] or 0),  # info: "archived" : int ( c [ "archived" ]
            "sort_order": cloud_sort,  # info: "sort_order" : cloud_sort ,
            "default_hourly_cents": c["default_hourly_cents"],  # info: "default_hourly_cents" : c [ "default_hourly_cents" ] ,
            "created_at": created,  # info: "created_at" : created ,
            "updated_at": updated,  # info: "updated_at" : updated ,
        }  # info: }
        emit_insert(lines, user_key, "categories", nid, doc, created, updated)  # info: call emit_insert

    # --- projects
    cur.execute(  # info: cur . execute (
        "SELECT * FROM projects WHERE user_id = ? ORDER BY sort_order ASC, id ASC",  # info: "SELECT * FROM projects WHERE user_id = ? ORDER BY sort_order ASC, id ASC" ,
        (uid,),  # info: call (
    )  # info: )
    projs = cur.fetchall()  # info: set projs
    proj_old_to_new: Dict[int, str] = {}  # info: set proj_old_to_new
    for p in projs:  # info: for p in projs :
        oid = int(p["id"])  # info: set oid
        nid = stable_id("projects", oid)  # info: set nid
        proj_old_to_new[oid] = nid  # info: proj_old_to_new [ oid ] = nid
        # Legacy `projects` has no timestamps.
        created = now_iso()  # info: set created
        updated = created  # info: set updated
        so = int(p["sort_order"] or 0)  # info: set so
        cloud_sort = so * 100_000 + oid  # info: set cloud_sort
        doc = {  # info: set doc
            "id": nid,  # info: "id" : nid ,
            "user_id": user_key,  # info: "user_id" : user_key ,
            "name": p["name"] or "Project",  # info: "name" : p [ "name" ] or "Project"
            "client_name": p["client_name"] or "",  # info: "client_name" : p [ "client_name" ] or ""
            "color": p["color"] or "#5C4D7D",
            "default_hourly_cents": p["default_hourly_cents"],  # info: "default_hourly_cents" : p [ "default_hourly_cents" ] ,
            "currency": p["currency"] or "USD",  # info: "currency" : p [ "currency" ] or "USD"
            "notes": p["notes"] or "",  # info: "notes" : p [ "notes" ] or ""
            "archived": int(p["archived"] or 0),  # info: "archived" : int ( p [ "archived" ]
            "sort_order": cloud_sort,  # info: "sort_order" : cloud_sort ,
            "created_at": created,  # info: "created_at" : created ,
            "updated_at": updated,  # info: "updated_at" : updated ,
        }  # info: }
        emit_insert(lines, user_key, "projects", nid, doc, created, updated)  # info: call emit_insert

    # --- quick_actions -> quick_actions (D1 coll name)
    cur.execute(  # info: cur . execute (
        "SELECT * FROM quick_actions WHERE user_id = ? ORDER BY sort_order ASC, id ASC",  # info: "SELECT * FROM quick_actions WHERE user_id = ? ORDER BY sort_order ASC, id ASC" ,
        (uid,),  # info: call (
    )  # info: )
    for q in cur.fetchall():  # info: for q in cur . fetchall ( )
        oid = int(q["id"])  # info: set oid
        nid = stable_id("quick_actions", oid)  # info: set nid
        wcid = q["work_category_id"]  # info: set wcid
        pid = q["project_id"]  # info: set pid
        so = int(q["sort_order"] or 0)  # info: set so
        cloud_sort = so * 100_000 + oid  # info: set cloud_sort
        doc = {  # info: set doc
            "id": nid,  # info: "id" : nid ,
            "user_id": user_key,  # info: "user_id" : user_key ,
            "label": q["label"] or "Quick",  # info: "label" : q [ "label" ] or "Quick"
            "category_id": cat_old_to_new.get(int(wcid)) if wcid is not None else None,  # info: "category_id" : cat_old_to_new . get ( int (
            "project_id": proj_old_to_new.get(int(pid)) if pid is not None else None,  # info: "project_id" : proj_old_to_new . get ( int (
            "default_description": q["default_description"] or "",  # info: "default_description" : q [ "default_description" ] or ""
            "sort_order": cloud_sort,  # info: "sort_order" : cloud_sort ,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),  # info: "created_at" : datetime . now ( timezone .
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),  # info: "updated_at" : datetime . now ( timezone .
        }  # info: }
        emit_insert(  # info: call emit_insert
            lines,  # info: lines ,
            user_key,  # info: user_key ,
            "quick_actions",  # info: "quick_actions" ,
            nid,  # info: nid ,
            doc,  # info: doc ,
            doc["created_at"],  # info: doc [ "created_at" ] ,
            doc["updated_at"],  # info: doc [ "updated_at" ] ,
        )  # info: )

    # --- time entries
    cur.execute(  # info: cur . execute (
        "SELECT * FROM rr_time_entries WHERE user_id = ? ORDER BY start_utc ASC",  # info: "SELECT * FROM rr_time_entries WHERE user_id = ? ORDER BY start_utc ASC" ,
        (uid,),  # info: call (
    )  # info: )
    for te in cur.fetchall():  # info: for te in cur . fetchall ( )
        oid = int(te["id"])  # info: set oid
        nid = stable_id("time_entries", oid)  # info: set nid
        desc = te["description"] or ""  # info: set desc
        notes = te["notes"] or ""  # info: set notes
        if notes:  # info: if notes :
            desc = f"{desc}\n{notes}".strip() if desc else str(notes)  # info: set desc
        cat_col = (te["category"] or "work").strip().lower()  # info: set cat_col
        if cat_col == "evaluation" and desc:  # info: if cat_col == "evaluation" and desc :
            desc = f"[evaluation] {desc}"  # info: set desc
        wcid = te["work_category_id"]  # info: set wcid
        pid = te["project_id"]  # info: set pid
        created = iso_z(te["created_at"])  # info: set created
        end = iso_z(te["end_utc"])  # info: set end
        start = iso_z(te["start_utc"])  # info: set start
        doc = {  # info: set doc
            "id": nid,  # info: "id" : nid ,
            "user_id": user_key,  # info: "user_id" : user_key ,
            "start_utc": start,  # info: "start_utc" : start ,
            "end_utc": end,  # info: "end_utc" : end ,
            "category_id": cat_old_to_new.get(int(wcid)) if wcid is not None else None,  # info: "category_id" : cat_old_to_new . get ( int (
            "project_id": proj_old_to_new.get(int(pid)) if pid is not None else None,  # info: "project_id" : proj_old_to_new . get ( int (
            "description": desc,  # info: "description" : desc ,
            "source": "manual",  # info: "source" : "manual" ,
            "created_at": created,  # info: "created_at" : created ,
            "updated_at": end,  # info: "updated_at" : end ,
        }  # info: }
        emit_insert(lines, user_key, "time_entries", nid, doc, created, end)  # info: call emit_insert

    # --- income
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
        doc = {  # info: set doc
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

    # --- expenses
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

    out = "\n".join(lines) + "\n"  # info: set out
    if args.out == "-":  # info: if args . out == "-" :
        print(out, end="")  # info: call print
    else:  # info: else :
        with open(args.out, "w", encoding="utf-8") as f:  # info: with open ( args . out , "w"
            f.write(out)  # info: f . write ( out )
        print(f"Wrote {args.out} ({len(lines)} statements)")  # info: call print


# ====================================================
# SECTION: function now_iso
# What it does: now iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_iso() -> str:  # info: def now_iso
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  # info: return datetime . now ( timezone . utc


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
