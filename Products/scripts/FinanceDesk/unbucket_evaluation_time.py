# ==============================================================================
# FILE: Products/scripts/FinanceDesk/unbucket_evaluation_time.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""
Undo blanket category_id=Evaluation for [evaluation] time rows: pick a work category
from the description text (keyword rules). Keeps the description string unchanged.

Reads wrangler JSON exports (categories + time_entries), writes SQL UPDATEs.

Usage:
  python unbucket_evaluation_time.py --categories _c.json --time _t.json --out fix-eval-cats.sql
"""

from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import re  # info: import re
from typing import Dict, List, Tuple  # info: from typing import Dict , List , Tuple

EVAL_MARKER = re.compile(r"\[evaluation\]\s*", re.I)  # info: set EVAL_MARKER


# ====================================================
# SECTION: function load_cats
# What it does: load cats.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_cats(path: str) -> Dict[str, str]:  # info: def load_cats
    raw = json.load(open(path, encoding="utf-8-sig"))  # info: set raw
    name_to_id: Dict[str, str] = {}  # info: set name_to_id
    for r in raw[0]["results"]:  # info: for r in raw [ 0 ] [
        d = json.loads(r["doc"])  # info: set d
        name_to_id[str(d["name"]).strip()] = r["id"]  # info: name_to_id [ str ( d [ "name" ]
    return name_to_id  # info: return name_to_id


# ====================================================
# SECTION: function norm
# What it does: norm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def norm(s: str) -> str:  # info: def norm
    return " ".join(s.lower().split())  # info: return " " . join ( s . lower


# ====================================================
# SECTION: function pick_category
# What it does: Return category id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pick_category(desc: str, name_to_id: Dict[str, str]) -> str:  # info: def pick_category
    """Return category id."""  # info: """Return category id."""
    m = EVAL_MARKER.sub("", desc)  # info: set m
    t = norm(m)  # info: set t

    def cid(name: str) -> str:  # info: def cid
        return name_to_id[name]  # info: return name_to_id [ name ]

    # Order: more specific first
    if "break" in t or t.strip() == "cooking":  # info: if "break" in t or t . strip
        return cid("Break")  # info: return cid ( "Break" )
    if "billing" in t or "finance" in t or "taxation" in t or "tax " in t or "tax registration" in t:  # info: if "billing" in t or "finance" in t
        return cid("Finance")  # info: return cid ( "Finance" )
    if "marketing" in t or "discord" in t or "github" in t:  # info: if "marketing" in t or "discord" in t
        return cid("Marketing")  # info: return cid ( "Marketing" )
    if "analytics" in t:  # info: if "analytics" in t :
        return cid("Analytics")  # info: return cid ( "Analytics" )
    if "database" in t:  # info: if "database" in t :
        return cid("Analytics")  # info: return cid ( "Analytics" )
    if "design" in t or "theme" in t or "layout" in t or " ui" in t or t.startswith("ui"):  # info: if "design" in t or "theme" in t
        return cid("Design")  # info: return cid ( "Design" )
    if "operations audit" in t:  # info: if "operations audit" in t :
        return cid("Operations")  # info: return cid ( "Operations" )
    if "planning" in t or ("audit" in t and "operations" not in t):  # info: if "planning" in t or ( "audit" in
        return cid("Planning")  # info: return cid ( "Planning" )
    if "documentation" in t or "finalizing" in t or "configuring" in t or "encoding" in t or "signing" in t:  # info: if "documentation" in t or "finalizing" in t
        return cid("Documentation")  # info: return cid ( "Documentation" )
    if "microsoft" in t or "store" in t or "install" in t or "allowance" in t:  # info: if "microsoft" in t or "store" in t
        return cid("Documentation")  # info: return cid ( "Documentation" )
    if "testing" in t or t.strip() == "test" or " test " in f" {t} ":  # info: if "testing" in t or t . strip
        return cid("Testing")  # info: return cid ( "Testing" )
    if "weather" in t:  # info: if "weather" in t :
        return cid("Coding")  # info: return cid ( "Coding" )
    if "homestead" in t or "power manager" in t:  # info: if "homestead" in t or "power manager" in t
        return cid("Product")  # info: return cid ( "Product" )
    if "evaluation" == t.strip():  # info: if "evaluation" == t . strip ( )
        return cid("Evaluation")  # info: return cid ( "Evaluation" )
    if "cloud" in t:  # info: if "cloud" in t :
        return cid("Analytics")  # info: return cid ( "Analytics" )
    if "developer panel" in t or "javascript" in t or "python" in t or "upgrading" in t:  # info: if "developer panel" in t or "javascript" in t
        return cid("Development")  # info: return cid ( "Development" )
    if "building" in t or "development" in t or "version" in t or "working on" in t:  # info: if "building" in t or "development" in t
        return cid("Development")  # info: return cid ( "Development" )
    if "api key" in t or "firebase" in t or "features" in t:  # info: if "api key" in t or "firebase" in t
        return cid("Development")  # info: return cid ( "Development" )
    if "code review" in t:  # info: if "code review" in t :
        return cid("Coding")  # info: return cid ( "Coding" )
    if "accounts" in t:  # info: if "accounts" in t :
        return cid("Documentation")  # info: return cid ( "Documentation" )
    # default: general product/engineering work during eval period
    return cid("Development")  # info: return cid ( "Development" )


# ====================================================
# SECTION: function sql_escape
# What it does: sql escape.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sql_escape(s: str) -> str:  # info: def sql_escape
    return "'" + s.replace("'", "''") + "'"  # info: return "'" + s . replace ( "'"


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--categories", required=True)  # info: ap . add_argument ( "--categories" , required =
    ap.add_argument("--time", required=True)  # info: ap . add_argument ( "--time" , required =
    ap.add_argument("--user-key", default="user:rootrecord@outlook.com")  # info: ap . add_argument ( "--user-key" , default =
    ap.add_argument("--out", required=True)  # info: ap . add_argument ( "--out" , required =
    args = ap.parse_args()  # info: set args

    n2id = load_cats(args.categories)  # info: set n2id
    eval_id = n2id.get("Evaluation")  # info: set eval_id
    if not eval_id:  # info: if not eval_id :
        raise SystemExit("Evaluation category missing")  # info: raise SystemExit ( "Evaluation category missing" )

    raw = json.load(open(args.time, encoding="utf-8-sig"))  # info: set raw
    lines: List[str] = []  # info: set lines
    lines.append("-- unbucket_evaluation_time.py: restore varied categories for [evaluation] rows")  # info: lines . append ( "-- unbucket_evaluation_time.py: restore varied categories for [evaluation] rows" )
    n = 0  # info: set n
    for r in raw[0]["results"]:  # info: for r in raw [ 0 ] [
        d = json.loads(r["doc"])  # info: set d
        desc = str(d.get("description") or "")  # info: set desc
        if "[evaluation]" not in desc.lower():  # info: if "[evaluation]" not in desc . lower (
            continue  # info: continue
        if str(d.get("category_id")) != str(eval_id):  # info: if str ( d . get ( "category_id"
            continue  # info: continue
        new_cat = pick_category(desc, n2id)  # info: set new_cat
        if new_cat == str(d.get("category_id")):  # info: if new_cat == str ( d . get
            continue  # info: continue
        rid = r["id"]  # info: set rid
        lines.append(  # info: lines . append (
            f"UPDATE bm_owned_row SET doc = json_set(json_set(doc, '$.category_id', {sql_escape(new_cat)}), "  # info: f" UPDATE bm_owned_row SET doc = json_set(json_set(doc, '$.category_id', { sql_escape ( new_cat ) }
            f"'$.updated_at', strftime('%Y-%m-%dT%H:%M:%fZ','now')), "  # info: f" '$.updated_at', strftime('%Y-%m-%dT%H:%M:%fZ','now')), "
            f"updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "  # info: f" updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            f"WHERE user_key = {sql_escape(args.user_key)} AND coll = 'time_entries' AND id = {sql_escape(rid)};"  # info: f" WHERE user_key = { sql_escape ( args . user_key
        )  # info: )
        n += 1  # info: set n

    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + ("\n" if lines else ""))  # info: call open
    print(f"Wrote {args.out}: {n} UPDATEs")  # info: call print


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
