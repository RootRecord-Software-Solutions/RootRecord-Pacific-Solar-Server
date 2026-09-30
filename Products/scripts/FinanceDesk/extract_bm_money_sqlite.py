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

from __future__ import annotations

import argparse
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def stable_id(coll: str, old_pk: int) -> str:
    return uuid.uuid5(NS, f"rr:bm-import:v1|{coll}|{old_pk}").hex


def iso_z(raw: Optional[str]) -> str:
    if not raw or not str(raw).strip():
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    s = str(raw).strip()
    if s.endswith("Z"):
        return s
    if "+" in s or s.count("-") > 2 and "T" in s and s.endswith(("+00:00",)):
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if "T" in s and not s.endswith("Z"):
        return s + "Z" if not s.endswith("+00:00") else s.replace("+00:00", "Z")
    return s


def sql_escape(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def sql_json(obj: Dict[str, Any]) -> str:
    return sql_escape(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def emit_insert(
    lines: List[str],
    user_key: str,
    coll: str,
    row_id: str,
    doc: Dict[str, Any],
    created_at: str,
    updated_at: str,
) -> None:
    lines.append(
        f"INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "
        f"VALUES ({sql_escape(user_key)}, {sql_escape(coll)}, {sql_escape(row_id)}, "
        f"{sql_json(doc)}, {sql_escape(created_at)}, {sql_escape(updated_at)}) "
        f"ON CONFLICT(user_key, coll, id) DO UPDATE SET "
        f"doc = excluded.doc, updated_at = excluded.updated_at;"
    )


def map_funding(fs: Optional[str]) -> str:
    fs = (fs or "cash").strip().lower()
    if fs in ("cash", "bank", "credit"):
        return fs
    return "cash"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to rootrecord.db")
    ap.add_argument("--email", required=True)
    ap.add_argument("--user-id", type=int, default=1, help="Legacy rr_users id (default 1)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    email = args.email.strip().lower()
    user_key = f"user:{email}"
    uid = int(args.user_id)

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM work_categories WHERE user_id = ? ORDER BY sort_order ASC, id ASC",
        (uid,),
    )
    cat_old_to_new: Dict[int, str] = {}
    for c in cur.fetchall():
        oid = int(c["id"])
        cat_old_to_new[oid] = stable_id("categories", oid)

    cur.execute(
        "SELECT * FROM projects WHERE user_id = ? ORDER BY sort_order ASC, id ASC",
        (uid,),
    )
    proj_old_to_new: Dict[int, str] = {}
    for p in cur.fetchall():
        oid = int(p["id"])
        proj_old_to_new[oid] = stable_id("projects", oid)

    lines: List[str] = []
    lines.append("-- extract_bm_money_sqlite.py (income + expense only; ids match import_windows_bm_sqlite.py)")
    lines.append(f"-- user_key={user_key} legacy user_id={uid}")

    cur.execute(
        "SELECT * FROM income_entries WHERE user_id = ? ORDER BY received_at_utc ASC",
        (uid,),
    )
    for inc in cur.fetchall():
        oid = int(inc["id"])
        nid = stable_id("income_entries", oid)
        created = iso_z(inc["created_at"])
        updated = iso_z(inc["updated_at"])
        recv = iso_z(inc["received_at_utc"])
        doc: Dict[str, Any] = {
            "id": nid,
            "user_id": user_key,
            "received_at_utc": recv,
            "amount_cents": int(inc["amount_cents"] or 0),
            "currency": inc["currency"] or "USD",
            "description": inc["description"] or "",
            "created_at": created,
            "updated_at": updated,
        }
        wcid = inc["work_category_id"]
        pid = inc["project_id"]
        if wcid is not None:
            doc["category_id"] = cat_old_to_new.get(int(wcid))
        if pid is not None:
            doc["project_id"] = proj_old_to_new.get(int(pid))
        emit_insert(lines, user_key, "income_entries", nid, doc, created, updated)

    cur.execute(
        "SELECT * FROM expense_entries WHERE user_id = ? ORDER BY spent_at_utc ASC",
        (uid,),
    )
    for ex in cur.fetchall():
        oid = int(ex["id"])
        nid = stable_id("expense_entries", oid)
        created = iso_z(ex["created_at"])
        spent = iso_z(ex["spent_at_utc"])
        doc = {
            "id": nid,
            "user_id": user_key,
            "spent_at_utc": spent,
            "amount_cents": int(ex["amount_cents"] or 0),
            "currency": ex["currency"] or "USD",
            "description": ex["description"] or "",
            "funding": map_funding(ex["funding_source"]),
            "created_at": created,
            "updated_at": created,
        }
        wcid = ex["work_category_id"]
        pid = ex["project_id"]
        if wcid is not None:
            doc["category_id"] = cat_old_to_new.get(int(wcid))
        if pid is not None:
            doc["project_id"] = proj_old_to_new.get(int(pid))
        emit_insert(lines, user_key, "expense_entries", nid, doc, created, created)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {args.out} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
