#!/usr/bin/env python3
"""
Undo blanket category_id=Evaluation for [evaluation] time rows: pick a work category
from the description text (keyword rules). Keeps the description string unchanged.

Reads wrangler JSON exports (categories + time_entries), writes SQL UPDATEs.

Usage:
  python unbucket_evaluation_time.py --categories _c.json --time _t.json --out fix-eval-cats.sql
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Dict, List, Tuple

EVAL_MARKER = re.compile(r"\[evaluation\]\s*", re.I)


def load_cats(path: str) -> Dict[str, str]:
    raw = json.load(open(path, encoding="utf-8-sig"))
    name_to_id: Dict[str, str] = {}
    for r in raw[0]["results"]:
        d = json.loads(r["doc"])
        name_to_id[str(d["name"]).strip()] = r["id"]
    return name_to_id


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def pick_category(desc: str, name_to_id: Dict[str, str]) -> str:
    """Return category id."""
    m = EVAL_MARKER.sub("", desc)
    t = norm(m)

    def cid(name: str) -> str:
        return name_to_id[name]

    # Order: more specific first
    if "break" in t or t.strip() == "cooking":
        return cid("Break")
    if "billing" in t or "finance" in t or "taxation" in t or "tax " in t or "tax registration" in t:
        return cid("Finance")
    if "marketing" in t or "discord" in t or "github" in t:
        return cid("Marketing")
    if "analytics" in t:
        return cid("Analytics")
    if "database" in t:
        return cid("Analytics")
    if "design" in t or "theme" in t or "layout" in t or " ui" in t or t.startswith("ui"):
        return cid("Design")
    if "operations audit" in t:
        return cid("Operations")
    if "planning" in t or ("audit" in t and "operations" not in t):
        return cid("Planning")
    if "documentation" in t or "finalizing" in t or "configuring" in t or "encoding" in t or "signing" in t:
        return cid("Documentation")
    if "microsoft" in t or "store" in t or "install" in t or "allowance" in t:
        return cid("Documentation")
    if "testing" in t or t.strip() == "test" or " test " in f" {t} ":
        return cid("Testing")
    if "weather" in t:
        return cid("Coding")
    if "homestead" in t or "power manager" in t:
        return cid("Product")
    if "evaluation" == t.strip():
        return cid("Evaluation")
    if "cloud" in t:
        return cid("Analytics")
    if "developer panel" in t or "javascript" in t or "python" in t or "upgrading" in t:
        return cid("Development")
    if "building" in t or "development" in t or "version" in t or "working on" in t:
        return cid("Development")
    if "api key" in t or "firebase" in t or "features" in t:
        return cid("Development")
    if "code review" in t:
        return cid("Coding")
    if "accounts" in t:
        return cid("Documentation")
    # default: general product/engineering work during eval period
    return cid("Development")


def sql_escape(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", required=True)
    ap.add_argument("--time", required=True)
    ap.add_argument("--user-key", default="user:rootrecord@outlook.com")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    n2id = load_cats(args.categories)
    eval_id = n2id.get("Evaluation")
    if not eval_id:
        raise SystemExit("Evaluation category missing")

    raw = json.load(open(args.time, encoding="utf-8-sig"))
    lines: List[str] = []
    lines.append("-- unbucket_evaluation_time.py: restore varied categories for [evaluation] rows")
    n = 0
    for r in raw[0]["results"]:
        d = json.loads(r["doc"])
        desc = str(d.get("description") or "")
        if "[evaluation]" not in desc.lower():
            continue
        if str(d.get("category_id")) != str(eval_id):
            continue
        new_cat = pick_category(desc, n2id)
        if new_cat == str(d.get("category_id")):
            continue
        rid = r["id"]
        lines.append(
            f"UPDATE bm_owned_row SET doc = json_set(json_set(doc, '$.category_id', {sql_escape(new_cat)}), "
            f"'$.updated_at', strftime('%Y-%m-%dT%H:%M:%fZ','now')), "
            f"updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            f"WHERE user_key = {sql_escape(args.user_key)} AND coll = 'time_entries' AND id = {sql_escape(rid)};"
        )
        n += 1

    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + ("\n" if lines else ""))
    print(f"Wrote {args.out}: {n} UPDATEs")


if __name__ == "__main__":
    main()
