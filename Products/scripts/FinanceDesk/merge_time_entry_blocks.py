#!/usr/bin/env python3
"""
Merge consecutive time_entries that share category, project, description, and source
into a single row (earliest start, latest end). Reads wrangler JSON export.

Gap tolerance: entries chain if next.start <= prev.end + 2 seconds.

Usage:
  python merge_time_entry_blocks.py --export _all_time.json --out merge-time-blocks.sql
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

GAP = timedelta(seconds=2)


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def fmt_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def key(e: Dict[str, Any]) -> Tuple[str, str, str, str]:
    return (
        str(e.get("category_id") or ""),
        str(e.get("project_id") or ""),
        str(e.get("description") or ""),
        str(e.get("source") or "manual"),
    )


def sql_escape(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def sql_json(obj: Dict[str, Any]) -> str:
    return sql_escape(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--user-key", default="user:rootrecord@outlook.com")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    raw = json.load(open(args.export, encoding="utf-8-sig"))
    rows = raw[0]["results"]
    entries: List[Dict[str, Any]] = []
    for r in rows:
        d = json.loads(r["doc"])
        d["_rowid"] = r["id"]
        entries.append(d)

    entries.sort(key=lambda x: parse_iso(x["start_utc"]))

    groups: List[List[Dict[str, Any]]] = []
    g = [entries[0]]
    for e in entries[1:]:
        prev = g[-1]
        ke = parse_iso(prev["end_utc"])
        s = parse_iso(e["start_utc"])
        if key(e) == key(prev) and s <= ke + GAP:
            g.append(e)
        else:
            groups.append(g)
            g = [e]
    groups.append(g)

    lines: List[str] = []
    lines.append(f"-- merge_time_entry_blocks.py user_key={args.user_key}")
    n_del = 0
    n_upd = 0

    for gr in groups:
        if len(gr) < 2:
            continue
        keep = gr[0]
        rid = str(keep["_rowid"])
        start = parse_iso(keep["start_utc"])
        end = max(parse_iso(x["end_utc"]) for x in gr)
        created = min(parse_iso(x["created_at"]) for x in gr if x.get("created_at"))
        merged = {k: v for k, v in keep.items() if not k.startswith("_")}
        merged["id"] = rid
        merged["user_id"] = args.user_key
        merged["start_utc"] = fmt_z(start)
        merged["end_utc"] = fmt_z(end)
        merged["created_at"] = fmt_z(created) if created.tzinfo else created.isoformat() + "Z"
        merged["updated_at"] = fmt_z(end)

        doc_sql = sql_json(merged)
        lines.append(
            f"UPDATE bm_owned_row SET doc = {doc_sql}, updated_at = {sql_escape(fmt_z(end))} "
            f"WHERE user_key = {sql_escape(args.user_key)} AND coll = 'time_entries' AND id = {sql_escape(rid)};"
        )
        n_upd += 1
        for x in gr[1:]:
            oid = str(x["_rowid"])
            lines.append(
                f"DELETE FROM bm_owned_row WHERE user_key = {sql_escape(args.user_key)} "
                f"AND coll = 'time_entries' AND id = {sql_escape(oid)};"
            )
            n_del += 1

    lines.insert(1, f"-- updates={n_upd} deletes={n_del}")
    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"Wrote {args.out}: {n_upd} merges, {n_del} deletes ({len(lines)-2} SQL lines)")


if __name__ == "__main__":
    main()
