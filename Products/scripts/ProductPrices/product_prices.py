# ==============================================================================
# FILE: Products/scripts/ProductPrices/product_prices.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Store shelf prices from vision. JSON for agents; JSONL history for audits.

Same product seen again → amend current price; keep prior prices in history
with the image path + timestamp. Never wipe the item on a price change.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

STORE_DIR = Path(  # info: set STORE_DIR
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/ProductPrices"  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/ProductPrices"
)  # info: )
PRICES_PATH = STORE_DIR / "prices.json"  # info: set PRICES_PATH
HISTORY_PATH = STORE_DIR / "sightings.jsonl"  # info: set HISTORY_PATH
MAX_ITEMS = 800  # info: set MAX_ITEMS
MAX_HISTORY_PER = 24  # info: set MAX_HISTORY_PER

_PRICE_RE = re.compile(  # info: set _PRICE_RE
    r"\$\s*(\d+(?:\.\d{1,2})?)",  # info: r"\$\s*(\d+(?:\.\d{1,2})?)" ,
    re.I,  # info: re . I ,
)  # info: )
_SAVE_RE = re.compile(  # info: set _SAVE_RE
    r"(?:save|savings?|off)\s*\$?\s*(\d+(?:\.\d{1,2})?)",  # info: r"(?:save|savings?|off)\s*\$?\s*(\d+(?:\.\d{1,2})?)" ,
    re.I,  # info: re . I ,
)  # info: )
# VLM often concatenates: "A | $1 | SAVE none B | $2 | SAVE none"
# ====================================================
# SECTION: _PIPE_ROW_RE
# What it does: Set _PIPE_ROW_RE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_PIPE_ROW_RE = re.compile(  # info: set _PIPE_ROW_RE
    r"(?:^|(?<=\s)|(?<=none))"  # info: r"(?:^|(?<=\s)|(?<=none))"
    r"((?!save\b)[A-Za-z][A-Za-z0-9&'.\-]*(?:\s+[A-Za-z0-9&'.\-]+){0,6})"  # info: r"((?!save\b)[A-Za-z][A-Za-z0-9&'.\-]*(?:\s+[A-Za-z0-9&'.\-]+){0,6})"
    r"\s*\|\s*(\$\s*\d+(?:\.\d{1,2})?|\d+\.\d{2})"  # info: r"\s*\|\s*(\$\s*\d+(?:\.\d{1,2})?|\d+\.\d{2})"
    r"(?:\s*\|\s*((?:save|SAVE)\s*\$?\s*[\d.]+|SAVE\s*none|Save\s*\$?none|none))?",  # info: r"(?:\s*\|\s*((?:save|SAVE)\s*\$?\s*[\d.]+|SAVE\s*none|Save\s*\$?none|none))?" ,
    re.I,  # info: re . I ,
)  # info: )


# ====================================================
# SECTION: function _now
# What it does:  now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now() -> str:  # info: def _now
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()) + "-10:00"  # info: return time . strftime ( "%Y-%m-%dT%H:%M:%S" , time


# ====================================================
# SECTION: function _now_ts
# What it does:  now ts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now_ts() -> int:  # info: def _now_ts
    return int(time.time())  # info: return int ( time . time ( )


# ====================================================
# SECTION: function slug
# What it does: slug.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def slug(name: str) -> str:  # info: def slug
    raw = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")  # info: set raw
    return (raw or "item")[:56]  # info: return ( raw or "item" ) [ :


# ====================================================
# SECTION: function _load
# What it does:  load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load() -> dict[str, Any]:  # info: def _load
    if not PRICES_PATH.is_file():  # info: if not PRICES_PATH . is_file ( ) :
        return {"updated": _now(), "items": []}  # info: return { "updated" : _now ( ) ,
    try:  # info: try :
        data = json.loads(PRICES_PATH.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {"updated": _now(), "items": []}  # info: return { "updated" : _now ( ) ,
    if not isinstance(data, dict):  # info: if not isinstance ( data , dict )
        return {"updated": _now(), "items": []}  # info: return { "updated" : _now ( ) ,
    items = data.get("items")  # info: set items
    if not isinstance(items, list):  # info: if not isinstance ( items , list )
        items = []  # info: set items
    data["items"] = items  # info: data [ "items" ] = items
    return data  # info: return data


# ====================================================
# SECTION: function _save
# What it does:  save.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _save(data: dict[str, Any]) -> None:  # info: def _save
    STORE_DIR.mkdir(parents=True, exist_ok=True)  # info: STORE_DIR . mkdir ( parents = True ,
    data = dict(data)  # info: set data
    data["updated"] = _now()  # info: data [ "updated" ] = _now ( )
    items = data.get("items") if isinstance(data.get("items"), list) else []  # info: set items
    data["items"] = items[-MAX_ITEMS:]  # info: data [ "items" ] = items [ -
    tmp = PRICES_PATH.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(PRICES_PATH)  # info: tmp . replace ( PRICES_PATH )


# ====================================================
# SECTION: function _append_history
# What it does:  append history.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _append_history(row: dict[str, Any]) -> None:  # info: def _append_history
    STORE_DIR.mkdir(parents=True, exist_ok=True)  # info: STORE_DIR . mkdir ( parents = True ,
    with HISTORY_PATH.open("a", encoding="utf-8") as f:  # info: with HISTORY_PATH . open ( "a" , encoding
        f.write(json.dumps(row, sort_keys=True) + "\n")  # info: f . write ( json . dumps (


# ====================================================
# SECTION: function parse_money
# What it does: parse money.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_money(text: str) -> float | None:  # info: def parse_money
    m = _PRICE_RE.search(text or "")  # info: set m
    if not m:  # info: if not m :
        # bare 7.99
        m2 = re.search(r"\b(\d+\.\d{2})\b", text or "")  # info: set m2
        if not m2:  # info: if not m2 :
            return None  # info: return None
        try:  # info: try :
            return float(m2.group(1))  # info: return float ( m2 . group ( 1
        except ValueError:  # info: except ValueError :
            return None  # info: return None
    try:  # info: try :
        return float(m.group(1))  # info: return float ( m . group ( 1
    except ValueError:  # info: except ValueError :
        return None  # info: return None


# ====================================================
# SECTION: function parse_save
# What it does: parse save.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_save(text: str) -> float | None:  # info: def parse_save
    m = _SAVE_RE.search(text or "")  # info: set m
    if not m:  # info: if not m :
        return None  # info: return None
    try:  # info: try :
        return float(m.group(1))  # info: return float ( m . group ( 1
    except ValueError:  # info: except ValueError :
        return None  # info: return None


# ====================================================
# SECTION: _NAME_BAN
# What it does: Set _NAME_BAN.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_NAME_BAN = frozenset(  # info: set _NAME_BAN
    {  # info: {
        "the",  # info: "the" ,
        "a",  # info: "a" ,
        "an",  # info: "an" ,
        "verified",  # info: "verified" ,
        "price",  # info: "price" ,
        "prices",  # info: "prices" ,
        "tag",  # info: "tag" ,
        "tags",  # info: "tags" ,
        "image",  # info: "image" ,
        "shelf",  # info: "shelf" ,
        "store",  # info: "store" ,
        "box",  # info: "box" ,
        "boxes",  # info: "boxes" ,
        "bag",  # info: "bag" ,
        "bags",  # info: "bags" ,
        "snack",  # info: "snack" ,
        "snacks",  # info: "snacks" ,
        "product",  # info: "product" ,
        "products",  # info: "products" ,
        "item",  # info: "item" ,
        "items",  # info: "items" ,
        "each",  # info: "each" ,
        "none",  # info: "none" ,
        "save",  # info: "save" ,
        "savings",  # info: "savings" ,
        "sale",  # info: "sale" ,
        "off",  # info: "off" ,
        "unclear",  # info: "unclear" ,
        "unknown",  # info: "unknown" ,
        "advertised",  # info: "advertised" ,
        "as advertised",  # info: "as advertised" ,
        "stand up bag",  # info: "stand up bag" ,
        "family size",  # info: "family size" ,
        "oh so good",  # info: "oh so good" ,
        "energy guide",  # info: "energy guide" ,
        "per oz",  # info: "per oz" ,
        "per lb",  # info: "per lb" ,
    }  # info: }
)  # info: )


# ====================================================
# SECTION: function _clean_product_name
# What it does:  clean product name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clean_product_name(name: str) -> str:  # info: def _clean_product_name
    name = re.sub(r"\s+", " ", (name or "")).strip(" -:|,.")  # info: set name
    name = re.sub(  # info: set name
        r"^(as advertised|verified text/?prices?:?|the image shows|it features|"  # info: r"^(as advertised|verified text/?prices?:?|the image shows|it features|"
        r"oh so good!?|product)\s+",  # info: r"oh so good!?|product)\s+" ,
        "",  # info: "" ,
        name,  # info: name ,
        flags=re.I,  # info: set flags
    ).strip()  # info: ) . strip ( )
    # Drop trailing size/price crumbs left in the name field.
    name = re.sub(  # info: set name
        r"\s+(?:\d+(?:\.\d+)?\s*(?:oz|lb|ct|cu\.?\s*ft)|\$\d+(?:\.\d{2})?)\s*$",  # info: r"\s+(?:\d+(?:\.\d+)?\s*(?:oz|lb|ct|cu\.?\s*ft)|\$\d+(?:\.\d{2})?)\s*$" ,
        "",  # info: "" ,
        name,  # info: name ,
        flags=re.I,  # info: set flags
    )  # info: )
    if len(name) > 60:  # info: if len ( name ) > 60 :
        name = name[:60].rsplit(" ", 1)[0]  # info: set name
    return name  # info: return name


# ====================================================
# SECTION: function _looks_like_size
# What it does:  looks like size.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _looks_like_size(name: str) -> bool:  # info: def _looks_like_size
    low = (name or "").lower().strip()  # info: set low
    if re.fullmatch(r"\d+[\"']?\s*(?:oz|lb|ct|cu\.?\s*ft|tabs?)?", low):  # info: if re . fullmatch ( r"\d+[\"']?\s*(?:oz|lb|ct|cu\.?\s*ft|tabs?)?" , low
        return True  # info: return True
    if re.fullmatch(r"\d+[\"'].*", low) and "tab" in low:  # info: if re . fullmatch ( r"\d+[\"'].*" , low
        return True  # info: return True
    return False  # info: return False


# ====================================================
# SECTION: function _name_ok
# What it does:  name ok.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _name_ok(name: str) -> bool:  # info: def _name_ok
    name = _clean_product_name(name)  # info: set name
    if len(name) < 3 or not re.search(r"[A-Za-z]{3,}", name):  # info: if len ( name ) < 3 or
        return False  # info: return False
    if _looks_like_size(name):  # info: if _looks_like_size ( name ) :
        return False  # info: return False
    low = name.lower()  # info: set low
    if low in _NAME_BAN or slug(name) in _NAME_BAN:  # info: if low in _NAME_BAN or slug ( name
        return False  # info: return False
    if re.fullmatch(r"(save|savings?|off|sale|deal)(\s+\d+(?:\.\d+)?)?", low):  # info: if re . fullmatch ( r"(save|savings?|off|sale|deal)(\s+\d+(?:\.\d+)?)?" , low
        return False  # info: return False
    if re.search(r"\bsave\s*\$?none\b|\bor save\b", low):  # info: if re . search ( r"\bsave\s*\$?none\b|\bor save\b" , low
        return False  # info: return False
    if re.match(r"^(or|and)\s+", low):  # info: if re . match ( r"^(or|and)\s+" , low
        return False  # info: return False
    stripped = _SAVE_RE.sub(" ", name)  # info: set stripped
    stripped = _PRICE_RE.sub(" ", stripped)  # info: set stripped
    stripped = re.sub(r"\b\d+(?:\.\d+)?\b", " ", stripped)  # info: set stripped
    stripped = re.sub(  # info: set stripped
        r"\b(save|savings?|off|sale|deal|as advertised|product)\b",  # info: r"\b(save|savings?|off|sale|deal|as advertised|product)\b" ,
        " ",  # info: " " ,
        stripped,  # info: stripped ,
        flags=re.I,  # info: set flags
    )  # info: )
    stripped = re.sub(r"\s+", " ", stripped).strip(" -:|,.")  # info: set stripped
    if len(stripped) < 3 or not re.search(r"[A-Za-z]{3,}", stripped):  # info: if len ( stripped ) < 3 or
        return False  # info: return False
    if stripped.lower() in _NAME_BAN or _looks_like_size(stripped):  # info: if stripped . lower ( ) in _NAME_BAN
        return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function _unique_prices
# What it does:  unique prices.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _unique_prices(*texts: str) -> set[float]:  # info: def _unique_prices
    found: set[float] = set()  # info: set found
    for t in texts:  # info: for t in texts :
        for m in re.finditer(r"\$\s*(\d+(?:\.\d{1,2})?)", t or ""):  # info: for m in re . finditer ( r"\$\s*(\d+(?:\.\d{1,2})?)"
            try:  # info: try :
                found.add(float(m.group(1)))  # info: found . add ( float ( m .
            except ValueError:  # info: except ValueError :
                pass  # info: pass
    return found  # info: return found


# ====================================================
# SECTION: function _prefer_name
# What it does: Keep the more specific product name (Doritos Cheese Balls > Doritos).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _prefer_name(a: str, b: str) -> str:  # info: def _prefer_name
    """Keep the more specific product name (Doritos Cheese Balls > Doritos)."""  # info: """Keep the more specific product name (Doritos Cheese Balls > Doritos)."""
    a = _clean_product_name(a)  # info: set a
    b = _clean_product_name(b)  # info: set b
    if not a:  # info: if not a :
        return b  # info: return b
    if not b:  # info: if not b :
        return a  # info: return a
    if a.lower() in b.lower() and len(b) > len(a):  # info: if a . lower ( ) in b
        return b  # info: return b
    if b.lower() in a.lower() and len(a) > len(b):  # info: if b . lower ( ) in a
        return a  # info: return a
    return a if len(a) >= len(b) else b  # info: return a if len ( a ) >=


# ====================================================
# SECTION: function _dedupe_products
# What it does: One row per product family. Nested names merge (Cheese Balls ⊂ Doritos Cheese Balls).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _dedupe_products(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:  # info: def _dedupe_products
    """One row per product family. Nested names merge (Cheese Balls ⊂ Doritos Cheese Balls)."""  # info: """One row per product family. Nested names merge (Cheese Balls ⊂ Doritos Cheese Balls)."""
    cleaned: list[dict[str, Any]] = []  # info: set cleaned
    for row in rows:  # info: for row in rows :
        name = _clean_product_name(str(row.get("name") or ""))  # info: set name
        if not _name_ok(name) or re.match(r"^save\b", name, re.I):  # info: if not _name_ok ( name ) or re
            continue  # info: continue
        try:  # info: try :
            price = float(row.get("price"))  # info: set price
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            continue  # info: continue
        save = row.get("save")  # info: set save
        try:  # info: try :
            save_f = float(save) if save is not None else None  # info: set save_f
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            save_f = None  # info: set save_f
        size = str(row.get("size") or "")[:40]  # info: set size
        if size.lower() == name.lower():  # info: if size . lower ( ) == name
            size = ""  # info: set size
        cleaned.append(  # info: cleaned . append (
            {  # info: {
                "name": name[:80],  # info: "name" : name [ : 80 ] ,
                "price": price,  # info: "price" : price ,
                "save": save_f,  # info: "save" : save_f ,
                "size": size,  # info: "size" : size ,
                "raw": str(row.get("raw") or "")[:200],  # info: "raw" : str ( row . get (
            }  # info: }
        )  # info: )

    merged: list[dict[str, Any]] = []  # info: set merged
    for row in cleaned:  # info: for row in cleaned :
        absorbed = False  # info: set absorbed
        for prev in merged:  # info: for prev in merged :
            if float(prev["price"]) != float(row["price"]):  # info: if float ( prev [ "price" ] )
                continue  # info: continue
            a = str(prev["name"]).lower()  # info: set a
            b = str(row["name"]).lower()  # info: set b
            if a == b or a in b or b in a:  # info: if a == b or a in b
                prev["name"] = _prefer_name(str(prev["name"]), str(row["name"]))  # info: prev [ "name" ] = _prefer_name ( str
                if row.get("save") is not None and prev.get("save") is None:  # info: if row . get ( "save" ) is
                    prev["save"] = row["save"]  # info: prev [ "save" ] = row [ "save"
                if row.get("size") and not prev.get("size"):  # info: if row . get ( "size" ) and
                    prev["size"] = row["size"]  # info: prev [ "size" ] = row [ "size"
                absorbed = True  # info: set absorbed
                break  # info: break
        if not absorbed:  # info: if not absorbed :
            merged.append(dict(row))  # info: merged . append ( dict ( row )

    by_id: dict[str, dict[str, Any]] = {}  # info: set by_id
    order: list[str] = []  # info: set order
    for cand in merged:  # info: for cand in merged :
        sid = slug(str(cand["name"]))  # info: set sid
        if sid in _NAME_BAN:  # info: if sid in _NAME_BAN :
            continue  # info: continue
        prev = by_id.get(sid)  # info: set prev
        if prev is None:  # info: if prev is None :
            by_id[sid] = cand  # info: by_id [ sid ] = cand
            order.append(sid)  # info: order . append ( sid )
            continue  # info: continue
        if float(prev["price"]) == float(cand["price"]):  # info: if float ( prev [ "price" ] )
            prev["name"] = _prefer_name(str(prev["name"]), str(cand["name"]))  # info: prev [ "name" ] = _prefer_name ( str
            if cand.get("save") is not None and prev.get("save") is None:  # info: if cand . get ( "save" ) is
                prev["save"] = cand["save"]  # info: prev [ "save" ] = cand [ "save"
            if cand.get("size") and not prev.get("size"):  # info: if cand . get ( "size" ) and
                prev["size"] = cand["size"]  # info: prev [ "size" ] = cand [ "size"
            continue  # info: continue
        # Same id, different price in one extract → keep later.
        by_id[sid] = cand  # info: by_id [ sid ] = cand
    return [by_id[i] for i in order][:12]  # info: return [ by_id [ i ] for i


# ====================================================
# SECTION: function _iter_pipe_chunks
# What it does: Split verified spam into one chunk per PRODUCT | $PRICE row.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _iter_pipe_chunks(text: str) -> list[str]:  # info: def _iter_pipe_chunks
    """Split verified spam into one chunk per PRODUCT | $PRICE row."""  # info: """Split verified spam into one chunk per PRODUCT | $PRICE row."""
    text = (text or "").strip()  # info: set text
    if not text:  # info: if not text :
        return []  # info: return [ ]
    parts = [p.strip() for p in re.split(r"[\n;/]+", text) if p.strip()]  # info: set parts
    out: list[str] = []  # info: set out
    for part in parts:  # info: for part in parts :
        matches = list(_PIPE_ROW_RE.finditer(part))  # info: set matches
        if matches:  # info: if matches :
            for m in matches:  # info: for m in matches :
                name = m.group(1).strip()  # info: set name
                price = m.group(2).strip()  # info: set price
                save = (m.group(3) or "SAVE none").strip()  # info: set save
                if not name or re.match(r"^save\b", name, re.I):  # info: if not name or re . match (
                    continue  # info: continue
                if not price.startswith("$"):  # info: if not price . startswith ( "$" )
                    price = f"${price}"  # info: set price
                out.append(f"{name} | {price} | {save}")  # info: out . append ( f" { name }
        elif "|" in part:  # info: elif "|" in part :
            out.append(part)  # info: out . append ( part )
        else:  # info: else :
            out.append(part)  # info: out . append ( part )
    return out  # info: return out


# ====================================================
# SECTION: function extract_from_text
# What it does: Best-effort product lines from vision text (no extra model call).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def extract_from_text(description: str, verified: str = "") -> list[dict[str, Any]]:  # info: def extract_from_text
    """Best-effort product lines from vision text (no extra model call)."""  # info: """Best-effort product lines from vision text (no extra model call)."""
    verified = (verified or "").strip()  # info: set verified
    description = (description or "").strip()  # info: set description
    out: list[dict[str, Any]] = []  # info: set out

    def _add(name: str, price: float, save: float | None, raw: str, *, size: str = "") -> None:  # info: def _add
        name = _clean_product_name(name)  # info: set name
        if not _name_ok(name):  # info: if not _name_ok ( name ) :
            return  # info: return
        if size and (size.lower() == name.lower() or _looks_like_size(name)):  # info: if size and ( size . lower (
            return  # info: return
        out.append(  # info: out . append (
            {  # info: {
                "name": name[:80],  # info: "name" : name [ : 80 ] ,
                "price": price,  # info: "price" : price ,
                "save": save,  # info: "save" : save ,
                "size": (size or "")[:40],  # info: call "size"
                "raw": raw[:200],  # info: "raw" : raw [ : 200 ] ,
            }  # info: }
        )  # info: )

    def _parse_pipe_line(line: str) -> None:  # info: def _parse_pipe_line
        bits = [b.strip() for b in line.split("|") if b.strip()]  # info: set bits
        if len(bits) < 2:  # info: if len ( bits ) < 2 :
            return  # info: return
        name, price_bit = bits[0], bits[1]  # info: name , price_bit = bits [ 0 ]
        save_bit = bits[2] if len(bits) > 2 else ""  # info: set save_bit
        size_bit = bits[3] if len(bits) > 3 else ""  # info: set size_bit
        money_bits = sum(1 for b in bits if parse_money(b) is not None)  # info: set money_bits
        if money_bits >= 2 and not _name_ok(name):  # info: if money_bits >= 2 and not _name_ok (
            return  # info: return
        if re.search(r"unclear|unknown|\?|^product$", name, re.I):  # info: if re . search ( r"unclear|unknown|\?|^product$" , name
            return  # info: return
        price = parse_money(price_bit)  # info: set price
        if price is None:  # info: if price is None :
            return  # info: return
        save = None  # info: set save
        if save_bit and "none" not in save_bit.lower():  # info: if save_bit and "none" not in save_bit .
            save = parse_money(save_bit) or parse_save(save_bit)  # info: set save
        # Sometimes size lands in save slot: "42 CT"
        size = ""  # info: set size
        for bit in (size_bit, save_bit):  # info: for bit in ( size_bit , save_bit )
            if bit and re.search(r"\b(\d+\s*(?:oz|lb|ct|cu\.?\s*ft))\b", bit, re.I):  # info: if bit and re . search ( r"\b(\d+\s*(?:oz|lb|ct|cu\.?\s*ft))\b"
                size = re.search(r"\b(\d+\s*(?:oz|lb|ct|cu\.?\s*ft))\b", bit, re.I).group(1)  # info: set size
                if bit == save_bit and save is None:  # info: if bit == save_bit and save is None
                    pass  # info: pass
                break  # info: break
        if size_bit and "none" not in size_bit.lower() and not size:  # info: if size_bit and "none" not in size_bit .
            if parse_money(size_bit) is None and not re.search(r"save", size_bit, re.I):  # info: if parse_money ( size_bit ) is None and
                size = size_bit[:40]  # info: set size
        _add(name, price, save, line, size=size)  # info: call _add

    if verified and ("$" in verified or re.search(r"\d+\.\d{2}", verified) or "|" in verified):  # info: if verified and ( "$" in verified or
        for chunk in _iter_pipe_chunks(verified):  # info: for chunk in _iter_pipe_chunks ( verified ) :
            if "|" in chunk:  # info: if "|" in chunk :
                _parse_pipe_line(chunk)  # info: call _parse_pipe_line
                continue  # info: continue
            nums = re.findall(r"(\d+(?:\.\d{1,2})?)", chunk)  # info: set nums
            if not nums:  # info: if not nums :
                continue  # info: continue
            price = float(nums[-1])  # info: set price
            save = None  # info: set save
            sm = _SAVE_RE.search(chunk)  # info: set sm
            if sm:  # info: if sm :
                try:  # info: try :
                    save = float(sm.group(1))  # info: set save
                except ValueError:  # info: except ValueError :
                    save = None  # info: set save
            name = chunk  # info: set name
            name = _PRICE_RE.sub(" ", name)  # info: set name
            name = _SAVE_RE.sub(" ", name)  # info: set name
            name = re.sub(r"\b\d+(?:\.\d+)?\b", " ", name)  # info: set name
            name = re.sub(  # info: set name
                r"\b(as advertised|stand up bag|per lb|per oz|lb|oz|ct|family size|save|off|sale)\b",  # info: r"\b(as advertised|stand up bag|per lb|per oz|lb|oz|ct|family size|save|off|sale)\b" ,
                " ",  # info: " " ,
                name,  # info: name ,
                flags=re.I,  # info: set flags
            )  # info: )
            name = re.sub(r"\s+", " ", name).strip(" -:|,.")  # info: set name
            if not name or not _name_ok(name):  # info: if not name or not _name_ok ( name
                continue  # info: continue
            _add(name.title() if name.isupper() else name, price, save, chunk)  # info: call _add

    blob = description  # info: set blob
    if "$" in blob or "|" in blob:  # info: if "$" in blob or "|" in blob
        chunks = [ln.strip() for ln in blob.replace(";", "\n").splitlines() if ln.strip()]  # info: set chunks
        if len(chunks) == 1 and ". " in chunks[0]:  # info: if len ( chunks ) == 1 and
            chunks = [p.strip() for p in chunks[0].split(". ") if p.strip()]  # info: set chunks
        for chunk in chunks:  # info: for chunk in chunks :
            if "|" in chunk and "$" in chunk:  # info: if "|" in chunk and "$" in chunk
                for sub in _iter_pipe_chunks(chunk):  # info: for sub in _iter_pipe_chunks ( chunk ) :
                    _parse_pipe_line(sub) if "|" in sub else None  # info: call _parse_pipe_line
                continue  # info: continue
            if "$" not in chunk:  # info: if "$" not in chunk :
                continue  # info: continue
            # Prefer explicit tag copy in quotes / ALL CAPS product lines.
            tag = re.search(  # info: set tag
                r'["“]?([A-Z][A-Z0-9][A-Z0-9 \'&\-]{2,50})\s+(\d+(?:\.\d+)?\s*OZ)?\s*\$?\s*(\d+\.\d{2})',  # info: r'["“]?([A-Z][A-Z0-9][A-Z0-9 \'&\-]{2,50})\s+(\d+(?:\.\d+)?\s*OZ)?\s*\$?\s*(\d+\.\d{2})' ,
                chunk,  # info: chunk ,
            )  # info: )
            if tag:  # info: if tag :
                nm = tag.group(1).title()  # info: set nm
                size = (tag.group(2) or "").strip()  # info: set size
                _add(nm, float(tag.group(3)), parse_save(chunk), chunk, size=size)  # info: call _add
                continue  # info: continue
            pairs = list(  # info: set pairs
                re.finditer(  # info: re . finditer (
                    r"([A-Z][A-Za-z0-9&'\-]+(?:\s+[A-Z][A-Za-z0-9&'\-]+){0,5})"  # info: r"([A-Z][A-Za-z0-9&'\-]+(?:\s+[A-Z][A-Za-z0-9&'\-]+){0,5})"
                    r"[^$\n]{0,48}"  # info: r"[^$\n]{0,48}"
                    r"\$\s*(\d+(?:\.\d{1,2})?)",  # info: r"\$\s*(\d+(?:\.\d{1,2})?)" ,
                    chunk,  # info: chunk ,
                )  # info: )
            )  # info: )
            if len(pairs) >= 2:  # info: if len ( pairs ) >= 2 :
                for m in pairs:  # info: for m in pairs :
                    _add(m.group(1), float(m.group(2)), parse_save(chunk), chunk)  # info: call _add
                continue  # info: continue
            price = parse_money(chunk)  # info: set price
            if price is None:  # info: if price is None :
                continue  # info: continue
            # Cheese Balls / Doritos Cheese Balls patterns
            m = re.search(  # info: set m
                r"((?:Doritos\s+)?Cheese Balls|Sour Patch Kids|Hawaiian Island Pack|"  # info: r"((?:Doritos\s+)?Cheese Balls|Sour Patch Kids|Hawaiian Island Pack|"
                r"Hawaiian Snack Pack|BouleBag|Camp Chef|Pringles|"  # info: r"Hawaiian Snack Pack|BouleBag|Camp Chef|Pringles|"
                r"[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){0,4})",  # info: r"[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){0,4})" ,
                chunk,  # info: chunk ,
            )  # info: )
            name = m.group(1).strip() if m else ""  # info: set name
            if not name or len(name) < 3:  # info: if not name or len ( name )
                continue  # info: continue
            size_m = re.search(r"(\d+(?:\.\d+)?\s*(?:oz|lb|ct))", chunk, re.I)  # info: set size_m
            _add(name, price, parse_save(chunk), chunk, size=(size_m.group(1) if size_m else ""))  # info: call _add

    return _dedupe_products(out)  # info: return _dedupe_products ( out )


# ====================================================
# SECTION: function extract_with_vision
# What it does: Structured product lines from the image (one short VLM call).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def extract_with_vision(path: Path) -> list[dict[str, Any]]:  # info: def extract_with_vision
    """Structured product lines from the image (one short VLM call)."""  # info: """Structured product lines from the image (one short VLM call)."""
    try:  # info: try :
        from apps.core.services import ollama as oc  # info: from apps . core . services import ollama
    except Exception:  # info: except Exception :
        return []  # info: return [ ]
    prompt = (  # info: set prompt
        "Shelf price list. One line per DISTINCT price tag — never repeat a line. "  # info: "Shelf price list. One line per DISTINCT price tag — never repeat a line. "
        "Format: NAME | $PRICE | SAVE $X or SAVE none | SIZE or none. "  # info: "Format: NAME | $PRICE | SAVE $X or SAVE none | SIZE or none. "
        "NAME = brand on the package above/beside that tag "  # info: "NAME = brand on the package above/beside that tag "
        "(use the package even if the tag has no product name). "  # info: "(use the package even if the tag has no product name). "
        "If unreadable, skip — do not invent. Numbers exactly as printed. No intro."  # info: "If unreadable, skip — do not invent. Numbers exactly as printed. No intro."
    )  # info: )
    raw = oc.look_sync(prompt, [path], timeout=90) or ""  # info: set raw
    raw = re.sub(r"[ \t]+", " ", (raw or "")).strip()  # info: set raw
    if not raw or raw.lower().startswith("ids:"):  # info: if not raw or raw . lower (
        return []  # info: return [ ]
    out: list[dict[str, Any]] = []  # info: set out
    for part in _iter_pipe_chunks(raw.replace("\n", "\n")):  # info: for part in _iter_pipe_chunks ( raw . replace
        # also split plain newlines
        for line in re.split(r"[\n;]+", part):  # info: for line in re . split ( r"[\n;]+"
            line = line.strip()  # info: set line
            if not line:  # info: if not line :
                continue  # info: continue
            line = re.sub(r"^\d+[\.\)]\s*", "", line)  # info: set line
            if "|" not in line and "$" not in line:  # info: if "|" not in line and "$" not
                continue  # info: continue
            bits = [b.strip() for b in line.split("|")]  # info: set bits
            name = bits[0] if bits else ""  # info: set name
            price_bit = bits[1] if len(bits) > 1 else line  # info: set price_bit
            save_bit = bits[2] if len(bits) > 2 else ""  # info: set save_bit
            size_bit = bits[3] if len(bits) > 3 else ""  # info: set size_bit
            if re.search(r"unclear|unknown|\?|^product$", name, re.I):  # info: if re . search ( r"unclear|unknown|\?|^product$" , name
                continue  # info: continue
            price = parse_money(price_bit) or parse_money(line)  # info: set price
            if price is None or not _name_ok(name):  # info: if price is None or not _name_ok (
                continue  # info: continue
            save = None  # info: set save
            if save_bit and "none" not in save_bit.lower():  # info: if save_bit and "none" not in save_bit .
                save = parse_money(save_bit) or parse_save(save_bit)  # info: set save
            out.append(  # info: out . append (
                {  # info: {
                    "name": _clean_product_name(name)[:80],  # info: "name" : _clean_product_name ( name ) [ :
                    "price": price,  # info: "price" : price ,
                    "save": save,  # info: "save" : save ,
                    "size": size_bit if size_bit and "none" not in size_bit.lower() else "",  # info: "size" : size_bit if size_bit and "none" not
                    "raw": line[:200],  # info: "raw" : line [ : 200 ] ,
                }  # info: }
            )  # info: )
    return _dedupe_products(out)  # info: return _dedupe_products ( out )


# ====================================================
# SECTION: function _history_has
# What it does: True if this image+price already logged (same photo re-process).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _history_has(hist: list[Any], *, image: str, price: float, ts: str) -> bool:  # info: def _history_has
    """True if this image+price already logged (same photo re-process)."""  # info: """True if this image+price already logged (same photo re-process)."""
    img = (image or "")[:300]  # info: set img
    for h in hist:  # info: for h in hist :
        if not isinstance(h, dict):  # info: if not isinstance ( h , dict )
            continue  # info: continue
        try:  # info: try :
            hp = float(h.get("price"))  # info: set hp
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            continue  # info: continue
        if hp != price:  # info: if hp != price :
            continue  # info: continue
        himg = str(h.get("image") or "")[:300]  # info: set himg
        if img and himg == img:  # info: if img and himg == img :
            return True  # info: return True
        # same second stamp + same price
        if ts and str(h.get("ts") or "") == ts and hp == price:  # info: if ts and str ( h . get
            return True  # info: return True
    return False  # info: return False


# ====================================================
# SECTION: function record_sightings
# What it does: Amend prices.json + append sightings.jsonl. Same product + new price → update current price, keep prior in history (with that sighting's image + timestamp). Same photo+price → no-o
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def record_sightings(  # info: def record_sightings
    products: list[dict[str, Any]],  # info: set products
    *,  # info: * ,
    image: str = "",  # info: set image
    folder: str = "",  # info: set folder
    source: str = "vision",  # info: set source
    caption: str = "",  # info: set caption
) -> list[dict[str, Any]]:  # info: ) -> list [ dict [ str ,
    """Amend prices.json + append sightings.jsonl.

    Same product + new price → update current price, keep prior in history
    (with that sighting's image + timestamp). Same photo+price → no-op.
    """
    products = _dedupe_products(products)  # info: set products
    if not products:  # info: if not products :
        return []  # info: return [ ]
    data = _load()  # info: set data
    items = data.get("items") if isinstance(data.get("items"), list) else []  # info: set items
    by_id = {  # info: set by_id
        str(it.get("id") or ""): it  # info: call str
        for it in items  # info: for it in items
        if isinstance(it, dict) and it.get("id")  # info: if isinstance ( it , dict ) and
    }  # info: }
    recorded: list[dict[str, Any]] = []  # info: set recorded
    ts = _now()  # info: set ts
    img = (image or "")[:300]  # info: set img
    for prod in products:  # info: for prod in products :
        name = _clean_product_name(str(prod.get("name") or ""))  # info: set name
        if not _name_ok(name):  # info: if not _name_ok ( name ) :
            continue  # info: continue
        try:  # info: try :
            price_f = float(prod.get("price"))  # info: set price_f
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            continue  # info: continue
        sid = slug(name)  # info: set sid
        # Merge into an existing longer/shorter id when names nest (doritos ↔ doritos-cheese-balls).
        prev = by_id.get(sid) if isinstance(by_id.get(sid), dict) else None  # info: set prev
        if prev is None:  # info: if prev is None :
            for oid, oit in list(by_id.items()):  # info: for oid , oit in list ( by_id
                oname = str(oit.get("name") or "").lower()  # info: set oname
                if not oname:  # info: if not oname :
                    continue  # info: continue
                if name.lower() in oname or oname in name.lower():  # info: if name . lower ( ) in oname
                    # Prefer the more specific id going forward.
                    better = _prefer_name(str(oit.get("name") or ""), name)  # info: set better
                    if slug(better) != oid:  # info: if slug ( better ) != oid :
                        # Retarget: move under better slug.
                        sid = slug(better)  # info: set sid
                        name = better  # info: set name
                        prev = dict(oit)  # info: set prev
                        prev["id"] = sid  # info: prev [ "id" ] = sid
                        prev["name"] = name[:80]  # info: prev [ "name" ] = name [ :
                        by_id.pop(oid, None)  # info: by_id . pop ( oid , None )
                        by_id[sid] = prev  # info: by_id [ sid ] = prev
                    else:  # info: else :
                        sid = oid  # info: set sid
                        name = better  # info: set name
                        prev = oit  # info: set prev
                    break  # info: break
        if prev is None:  # info: if prev is None :
            prev = {}  # info: set prev
        hist = list(prev.get("history") if isinstance(prev.get("history"), list) else [])  # info: set hist
        prev_price = prev.get("price")  # info: set prev_price
        try:  # info: try :
            prev_f = float(prev_price) if prev_price is not None else None  # info: set prev_f
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            prev_f = None  # info: set prev_f
        # Same photo + same price already current → skip (no sighting inflation).
        if (  # info: if (
            img  # info: img
            and prev_f is not None  # info: and prev_f is not None
            and prev_f == price_f  # info: and prev_f == price_f
            and _history_has(hist, image=img, price=price_f, ts="")  # info: call and
        ):  # info: ) :
            row = dict(prev)  # info: set row
            row["id"] = sid  # info: row [ "id" ] = sid
            row["name"] = _prefer_name(str(prev.get("name") or ""), name)[:80]  # info: row [ "name" ] = _prefer_name ( str
            by_id[sid] = row  # info: by_id [ sid ] = row
            recorded.append(row)  # info: recorded . append ( row )
            continue  # info: continue
        entry = {  # info: set entry
            "ts": ts,  # info: "ts" : ts ,
            "price": price_f,  # info: "price" : price_f ,
            "save": prod.get("save"),  # info: "save" : prod . get ( "save" )
            "size": str(prod.get("size") or "")[:40],  # info: "size" : str ( prod . get (
            "image": img,  # info: "image" : img ,
            "folder": folder[:40],  # info: "folder" : folder [ : 40 ] ,
            "caption": caption[:120],  # info: "caption" : caption [ : 120 ] ,
            "source": source,  # info: "source" : source ,
        }  # info: }
        hist = (hist + [entry])[-MAX_HISTORY_PER:]  # info: set hist
        changed = prev_f is not None and prev_f != price_f  # info: set changed
        save_val = prod.get("save")  # info: set save_val
        if save_val is None:  # info: if save_val is None :
            save_val = prev.get("save")  # info: set save_val
        row = {  # info: set row
            "id": sid,  # info: "id" : sid ,
            "name": _prefer_name(str(prev.get("name") or ""), name)[:80],  # info: "name" : _prefer_name ( str ( prev .
            "price": price_f,  # info: "price" : price_f ,
            "save": save_val,  # info: "save" : save_val ,
            "size": str(prod.get("size") or prev.get("size") or "")[:40],  # info: "size" : str ( prod . get (
            "last_seen": ts,  # info: "last_seen" : ts ,
            "last_image": img or str(prev.get("last_image") or ""),  # info: "last_image" : img or str ( prev .
            "folder": folder[:40] or str(prev.get("folder") or ""),  # info: "folder" : folder [ : 40 ] or
            "sightings": int(prev.get("sightings") or 0) + 1,  # info: "sightings" : int ( prev . get (
            "prev_price": prev_f if changed else prev.get("prev_price"),  # info: "prev_price" : prev_f if changed else prev .
            "history": hist,  # info: "history" : hist ,
        }  # info: }
        by_id[sid] = row  # info: by_id [ sid ] = row
        recorded.append(row)  # info: recorded . append ( row )
        _append_history(  # info: call _append_history
            {  # info: {
                "ts": ts,  # info: "ts" : ts ,
                "id": sid,  # info: "id" : sid ,
                "name": row["name"],  # info: "name" : row [ "name" ] ,
                "price": price_f,  # info: "price" : price_f ,
                "save": save_val,  # info: "save" : save_val ,
                "size": row.get("size"),  # info: "size" : row . get ( "size" )
                "image": img,  # info: "image" : img ,
                "folder": folder[:40],  # info: "folder" : folder [ : 40 ] ,
                "source": source,  # info: "source" : source ,
                "changed": changed,  # info: "changed" : changed ,
                "prev_price": prev_f if changed else None,  # info: "prev_price" : prev_f if changed else None ,
            }  # info: }
        )  # info: )
    data["items"] = sorted(  # info: data [ "items" ] = sorted (
        by_id.values(),  # info: by_id . values ( ) ,
        key=lambda r: str(r.get("last_seen") or ""),  # info: set key
        reverse=True,  # info: set reverse
    )[:MAX_ITEMS]  # info: ) [ : MAX_ITEMS ]
    _save(data)  # info: call _save
    return recorded  # info: return recorded


# ====================================================
# SECTION: function from_vision_row
# What it does: Extract + record products from a vision analyze row.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def from_vision_row(row: dict[str, Any], *, path: Path | None = None) -> list[dict[str, Any]]:  # info: def from_vision_row
    """Extract + record products from a vision analyze row."""  # info: """Extract + record products from a vision analyze row."""
    desc = str(row.get("description") or "")  # info: set desc
    verified = str(row.get("verified") or "")  # info: set verified
    products = extract_from_text(desc, verified)  # info: set products
    uniq_prices = _unique_prices(desc, verified)  # info: set uniq_prices
    # Weak only when we have almost nothing — do not treat VLM spam dollar-counts as "many products".
    weak = not products  # info: set weak
    img_path = path  # info: set img_path
    if img_path is None:  # info: if img_path is None :
        for key in ("src", "sorted"):  # info: for key in ( "src" , "sorted" )
            cand = Path(str(row.get(key) or ""))  # info: set cand
            if cand.is_file():  # info: if cand . is_file ( ) :
                img_path = cand  # info: set img_path
                break  # info: break
    wants_prices = bool(uniq_prices) or "price" in desc.lower()  # info: set wants_prices
    if wants_prices and weak and img_path and img_path.is_file():  # info: if wants_prices and weak and img_path and img_path
        print(  # info: call print
            f"product-prices extract pass path={img_path} "  # info: f" product-prices extract pass path= { img_path } "
            f"text_n={len(products)} unique_dollars={len(uniq_prices)}",  # info: f" text_n= { len ( products ) }
            flush=True,  # info: set flush
        )  # info: )
        vis = extract_with_vision(img_path)  # info: set vis
        if vis:  # info: if vis :
            products = vis  # info: set products
    if not products:  # info: if not products :
        return []  # info: return [ ]
    return record_sightings(  # info: return record_sightings (
        products,  # info: products ,
        image=str(row.get("sorted") or row.get("src") or ""),  # info: set image
        folder=str(row.get("folder") or ""),  # info: set folder
        caption=str(row.get("caption") or ""),  # info: set caption
        source="vision",  # info: set source
    )  # info: )


# ====================================================
# SECTION: function lookup
# What it does: lookup.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lookup(name: str) -> dict[str, Any] | None:  # info: def lookup
    sid = slug(name)  # info: set sid
    data = _load()  # info: set data
    for it in data.get("items") or []:  # info: for it in data . get ( "items"
        if isinstance(it, dict) and it.get("id") == sid:  # info: if isinstance ( it , dict ) and
            return dict(it)  # info: return dict ( it )
    low = (name or "").lower()  # info: set low
    for it in data.get("items") or []:  # info: for it in data . get ( "items"
        if not isinstance(it, dict):  # info: if not isinstance ( it , dict )
            continue  # info: continue
        if low and low in str(it.get("name") or "").lower():  # info: if low and low in str ( it
            return dict(it)  # info: return dict ( it )
    return None  # info: return None


# ====================================================
# SECTION: function recent
# What it does: recent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def recent(limit: int = 12) -> list[dict[str, Any]]:  # info: def recent
    data = _load()  # info: set data
    items = [it for it in (data.get("items") or []) if isinstance(it, dict)]  # info: set items
    return items[: max(1, min(limit, 40))]  # info: return items [ : max ( 1 ,


# ====================================================
# SECTION: function remove_ids
# What it does: Drop junk items by id. History jsonl is left as audit trail.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def remove_ids(ids: list[str]) -> int:  # info: def remove_ids
    """Drop junk items by id. History jsonl is left as audit trail."""  # info: """Drop junk items by id. History jsonl is left as audit trail."""
    want = {slug(i) for i in ids}  # info: set want
    data = _load()  # info: set data
    before = len(data.get("items") or [])  # info: set before
    data["items"] = [  # info: data [ "items" ] = [
        it  # info: it
        for it in (data.get("items") or [])  # info: for it in ( data . get (
        if isinstance(it, dict) and str(it.get("id") or "") not in want  # info: if isinstance ( it , dict ) and
    ]  # info: ]
    _save(data)  # info: call _save
    return before - len(data["items"])  # info: return before - len ( data [ "items"


# ====================================================
# SECTION: function prompt_block
# What it does: Lines for desk / vision recall.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def prompt_block(*, cap: int = 500, ask: str = "") -> str:  # info: def prompt_block
    """Lines for desk / vision recall."""  # info: """Lines for desk / vision recall."""
    q = (ask or "").strip().lower()  # info: set q
    items = recent(16)  # info: set items
    if not items:  # info: if not items :
        return ""  # info: return ""
    if q:  # info: if q :
        hit = lookup(q)  # info: set hit
        focused = [hit] if hit else []  # info: set focused
        if not focused:  # info: if not focused :
            focused = [  # info: set focused
                it  # info: it
                for it in items  # info: for it in items
                if any(  # info: if any (
                    tok in str(it.get("name") or "").lower()  # info: tok in str ( it . get (
                    for tok in re.findall(r"[a-z0-9]{3,}", q)  # info: for tok in re . findall ( r"[a-z0-9]{3,}"
                )  # info: )
            ][:8]  # info: ] [ : 8 ]
        if focused:  # info: if focused :
            items = focused  # info: set items
    lines = ["Store prices (from shelf photos — quote; do not invent):"]  # info: set lines
    for it in items[:10]:  # info: for it in items [ : 10 ]
        name = str(it.get("name") or it.get("id") or "?")  # info: set name
        price = it.get("price")  # info: set price
        save = it.get("save")  # info: set save
        seen = str(it.get("last_seen") or "")[:16]  # info: set seen
        bit = f"- {name}: ${price:.2f}" if isinstance(price, (int, float)) else f"- {name}: {price}"  # info: set bit
        if isinstance(save, (int, float)) and save > 0:  # info: if isinstance ( save , ( int ,
            bit += f" (save ${save:.2f})"  # info: set bit
        size = str(it.get("size") or "").strip()  # info: set size
        if size:  # info: if size :
            bit += f" · {size}"  # info: set bit
        prev = it.get("prev_price")  # info: set prev
        if isinstance(prev, (int, float)) and isinstance(price, (int, float)) and prev != price:  # info: if isinstance ( prev , ( int ,
            bit += f" (was ${prev:.2f})"  # info: set bit
        if seen:  # info: if seen :
            bit += f" · {seen}"  # info: set bit
        lines.append(bit)  # info: lines . append ( bit )
    blob = "\n".join(lines)  # info: set blob
    return blob if len(blob) <= cap else blob[: cap - 1] + "…"  # info: return blob if len ( blob ) <=


# ====================================================
# SECTION: function _ask_wants_prices
# What it does:  ask wants prices.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ask_wants_prices(ask: str) -> bool:  # info: def _ask_wants_prices
    low = (ask or "").lower()  # info: set low
    return any(  # info: return any (
        k in low  # info: k in low
        for k in (  # info: for k in (
            "price",  # info: "price" ,
            "prices",  # info: "prices" ,
            "cost",  # info: "cost" ,
            "how much",  # info: "how much" ,
            "store",  # info: "store" ,
            "shopping",  # info: "shopping" ,
            "shelf",  # info: "shelf" ,
            "product",  # info: "product" ,
            "grocery",  # info: "grocery" ,
            "deal",  # info: "deal" ,
            "sale",  # info: "sale" ,
            "pringles",  # info: "pringles" ,
            "sour patch",  # info: "sour patch" ,
            "doritos",  # info: "doritos" ,
            "cheese balls",  # info: "cheese balls" ,
            "hawaiian",  # info: "hawaiian" ,
            "walmart",  # info: "walmart" ,
            "safeway",  # info: "safeway" ,
            "target",  # info: "target" ,
        )  # info: )
    )  # info: )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    import sys  # info: import sys

    args = list(argv if argv is not None else sys.argv[1:])  # info: set args
    if not args or args[0] in {"recent", "list"}:  # info: if not args or args [ 0 ]
        for it in recent(20):  # info: for it in recent ( 20 ) :
            print(  # info: call print
                f"{it.get('name')}\t${it.get('price')}\t"  # info: f" { it . get ( 'name' )
                f"save={it.get('save')}\tseen={it.get('last_seen')}"  # info: f" save= { it . get ( 'save'
            )  # info: )
        return 0  # info: return 0
    if args[0] == "lookup" and len(args) > 1:  # info: if args [ 0 ] == "lookup" and
        hit = lookup(" ".join(args[1:]))  # info: set hit
        print(json.dumps(hit or {}, indent=2))  # info: call print
        return 0 if hit else 1  # info: return 0 if hit else 1
    if args[0] == "prompt":  # info: if args [ 0 ] == "prompt" :
        print(prompt_block(ask=" ".join(args[1:])))  # info: call print
        return 0  # info: return 0
    if args[0] == "remove" and len(args) > 1:  # info: if args [ 0 ] == "remove" and
        n = remove_ids(args[1:])  # info: set n
        print(f"removed {n}")  # info: call print
        return 0  # info: return 0
    print(  # info: call print
        "usage: product_prices.py [recent|lookup NAME|prompt …|remove ID…]",  # info: "usage: product_prices.py [recent|lookup NAME|prompt …|remove ID…]" ,
        file=sys.stderr,  # info: set file
    )  # info: )
    return 2  # info: return 2


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
