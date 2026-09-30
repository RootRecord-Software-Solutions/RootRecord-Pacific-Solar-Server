#!/usr/bin/env python3
"""Store shelf prices from vision. JSON for agents; JSONL history for audits.

Same product seen again → amend current price; keep prior prices in history
with the image path + timestamp. Never wipe the item on a price change.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

STORE_DIR = Path(
    os.environ.get(
        "PRODUCT_PRICES_DIR",
        str(Path.home() / ".ollama" / "skills" / "product-prices" / "store"),
    )
)
PRICES_PATH = STORE_DIR / "prices.json"
HISTORY_PATH = STORE_DIR / "sightings.jsonl"
MAX_ITEMS = 800
MAX_HISTORY_PER = 24

_PRICE_RE = re.compile(
    r"\$\s*(\d+(?:\.\d{1,2})?)",
    re.I,
)
_SAVE_RE = re.compile(
    r"(?:save|savings?|off)\s*\$?\s*(\d+(?:\.\d{1,2})?)",
    re.I,
)
# VLM often concatenates: "A | $1 | SAVE none B | $2 | SAVE none"
_PIPE_ROW_RE = re.compile(
    r"(?:^|(?<=\s)|(?<=none))"
    r"((?!save\b)[A-Za-z][A-Za-z0-9&'.\-]*(?:\s+[A-Za-z0-9&'.\-]+){0,6})"
    r"\s*\|\s*(\$\s*\d+(?:\.\d{1,2})?|\d+\.\d{2})"
    r"(?:\s*\|\s*((?:save|SAVE)\s*\$?\s*[\d.]+|SAVE\s*none|Save\s*\$?none|none))?",
    re.I,
)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()) + "-10:00"


def _now_ts() -> int:
    return int(time.time())


def slug(name: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return (raw or "item")[:56]


def _load() -> dict[str, Any]:
    if not PRICES_PATH.is_file():
        return {"updated": _now(), "items": []}
    try:
        data = json.loads(PRICES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"updated": _now(), "items": []}
    if not isinstance(data, dict):
        return {"updated": _now(), "items": []}
    items = data.get("items")
    if not isinstance(items, list):
        items = []
    data["items"] = items
    return data


def _save(data: dict[str, Any]) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["updated"] = _now()
    items = data.get("items") if isinstance(data.get("items"), list) else []
    data["items"] = items[-MAX_ITEMS:]
    tmp = PRICES_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(PRICES_PATH)


def _append_history(row: dict[str, Any]) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def parse_money(text: str) -> float | None:
    m = _PRICE_RE.search(text or "")
    if not m:
        # bare 7.99
        m2 = re.search(r"\b(\d+\.\d{2})\b", text or "")
        if not m2:
            return None
        try:
            return float(m2.group(1))
        except ValueError:
            return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def parse_save(text: str) -> float | None:
    m = _SAVE_RE.search(text or "")
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


_NAME_BAN = frozenset(
    {
        "the",
        "a",
        "an",
        "verified",
        "price",
        "prices",
        "tag",
        "tags",
        "image",
        "shelf",
        "store",
        "box",
        "boxes",
        "bag",
        "bags",
        "snack",
        "snacks",
        "product",
        "products",
        "item",
        "items",
        "each",
        "none",
        "save",
        "savings",
        "sale",
        "off",
        "unclear",
        "unknown",
        "advertised",
        "as advertised",
        "stand up bag",
        "family size",
        "oh so good",
        "energy guide",
        "per oz",
        "per lb",
    }
)


def _clean_product_name(name: str) -> str:
    name = re.sub(r"\s+", " ", (name or "")).strip(" -:|,.")
    name = re.sub(
        r"^(as advertised|verified text/?prices?:?|the image shows|it features|"
        r"oh so good!?|product)\s+",
        "",
        name,
        flags=re.I,
    ).strip()
    # Drop trailing size/price crumbs left in the name field.
    name = re.sub(
        r"\s+(?:\d+(?:\.\d+)?\s*(?:oz|lb|ct|cu\.?\s*ft)|\$\d+(?:\.\d{2})?)\s*$",
        "",
        name,
        flags=re.I,
    )
    if len(name) > 60:
        name = name[:60].rsplit(" ", 1)[0]
    return name


def _looks_like_size(name: str) -> bool:
    low = (name or "").lower().strip()
    if re.fullmatch(r"\d+[\"']?\s*(?:oz|lb|ct|cu\.?\s*ft|tabs?)?", low):
        return True
    if re.fullmatch(r"\d+[\"'].*", low) and "tab" in low:
        return True
    return False


def _name_ok(name: str) -> bool:
    name = _clean_product_name(name)
    if len(name) < 3 or not re.search(r"[A-Za-z]{3,}", name):
        return False
    if _looks_like_size(name):
        return False
    low = name.lower()
    if low in _NAME_BAN or slug(name) in _NAME_BAN:
        return False
    if re.fullmatch(r"(save|savings?|off|sale|deal)(\s+\d+(?:\.\d+)?)?", low):
        return False
    if re.search(r"\bsave\s*\$?none\b|\bor save\b", low):
        return False
    if re.match(r"^(or|and)\s+", low):
        return False
    stripped = _SAVE_RE.sub(" ", name)
    stripped = _PRICE_RE.sub(" ", stripped)
    stripped = re.sub(r"\b\d+(?:\.\d+)?\b", " ", stripped)
    stripped = re.sub(
        r"\b(save|savings?|off|sale|deal|as advertised|product)\b",
        " ",
        stripped,
        flags=re.I,
    )
    stripped = re.sub(r"\s+", " ", stripped).strip(" -:|,.")
    if len(stripped) < 3 or not re.search(r"[A-Za-z]{3,}", stripped):
        return False
    if stripped.lower() in _NAME_BAN or _looks_like_size(stripped):
        return False
    return True


def _unique_prices(*texts: str) -> set[float]:
    found: set[float] = set()
    for t in texts:
        for m in re.finditer(r"\$\s*(\d+(?:\.\d{1,2})?)", t or ""):
            try:
                found.add(float(m.group(1)))
            except ValueError:
                pass
    return found


def _prefer_name(a: str, b: str) -> str:
    """Keep the more specific product name (Doritos Cheese Balls > Doritos)."""
    a = _clean_product_name(a)
    b = _clean_product_name(b)
    if not a:
        return b
    if not b:
        return a
    if a.lower() in b.lower() and len(b) > len(a):
        return b
    if b.lower() in a.lower() and len(a) > len(b):
        return a
    return a if len(a) >= len(b) else b


def _dedupe_products(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per product family. Nested names merge (Cheese Balls ⊂ Doritos Cheese Balls)."""
    cleaned: list[dict[str, Any]] = []
    for row in rows:
        name = _clean_product_name(str(row.get("name") or ""))
        if not _name_ok(name) or re.match(r"^save\b", name, re.I):
            continue
        try:
            price = float(row.get("price"))
        except (TypeError, ValueError):
            continue
        save = row.get("save")
        try:
            save_f = float(save) if save is not None else None
        except (TypeError, ValueError):
            save_f = None
        size = str(row.get("size") or "")[:40]
        if size.lower() == name.lower():
            size = ""
        cleaned.append(
            {
                "name": name[:80],
                "price": price,
                "save": save_f,
                "size": size,
                "raw": str(row.get("raw") or "")[:200],
            }
        )

    merged: list[dict[str, Any]] = []
    for row in cleaned:
        absorbed = False
        for prev in merged:
            if float(prev["price"]) != float(row["price"]):
                continue
            a = str(prev["name"]).lower()
            b = str(row["name"]).lower()
            if a == b or a in b or b in a:
                prev["name"] = _prefer_name(str(prev["name"]), str(row["name"]))
                if row.get("save") is not None and prev.get("save") is None:
                    prev["save"] = row["save"]
                if row.get("size") and not prev.get("size"):
                    prev["size"] = row["size"]
                absorbed = True
                break
        if not absorbed:
            merged.append(dict(row))

    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for cand in merged:
        sid = slug(str(cand["name"]))
        if sid in _NAME_BAN:
            continue
        prev = by_id.get(sid)
        if prev is None:
            by_id[sid] = cand
            order.append(sid)
            continue
        if float(prev["price"]) == float(cand["price"]):
            prev["name"] = _prefer_name(str(prev["name"]), str(cand["name"]))
            if cand.get("save") is not None and prev.get("save") is None:
                prev["save"] = cand["save"]
            if cand.get("size") and not prev.get("size"):
                prev["size"] = cand["size"]
            continue
        # Same id, different price in one extract → keep later.
        by_id[sid] = cand
    return [by_id[i] for i in order][:12]


def _iter_pipe_chunks(text: str) -> list[str]:
    """Split verified spam into one chunk per PRODUCT | $PRICE row."""
    text = (text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"[\n;/]+", text) if p.strip()]
    out: list[str] = []
    for part in parts:
        matches = list(_PIPE_ROW_RE.finditer(part))
        if matches:
            for m in matches:
                name = m.group(1).strip()
                price = m.group(2).strip()
                save = (m.group(3) or "SAVE none").strip()
                if not name or re.match(r"^save\b", name, re.I):
                    continue
                if not price.startswith("$"):
                    price = f"${price}"
                out.append(f"{name} | {price} | {save}")
        elif "|" in part:
            out.append(part)
        else:
            out.append(part)
    return out


def extract_from_text(description: str, verified: str = "") -> list[dict[str, Any]]:
    """Best-effort product lines from vision text (no extra model call)."""
    verified = (verified or "").strip()
    description = (description or "").strip()
    out: list[dict[str, Any]] = []

    def _add(name: str, price: float, save: float | None, raw: str, *, size: str = "") -> None:
        name = _clean_product_name(name)
        if not _name_ok(name):
            return
        if size and (size.lower() == name.lower() or _looks_like_size(name)):
            return
        out.append(
            {
                "name": name[:80],
                "price": price,
                "save": save,
                "size": (size or "")[:40],
                "raw": raw[:200],
            }
        )

    def _parse_pipe_line(line: str) -> None:
        bits = [b.strip() for b in line.split("|") if b.strip()]
        if len(bits) < 2:
            return
        name, price_bit = bits[0], bits[1]
        save_bit = bits[2] if len(bits) > 2 else ""
        size_bit = bits[3] if len(bits) > 3 else ""
        money_bits = sum(1 for b in bits if parse_money(b) is not None)
        if money_bits >= 2 and not _name_ok(name):
            return
        if re.search(r"unclear|unknown|\?|^product$", name, re.I):
            return
        price = parse_money(price_bit)
        if price is None:
            return
        save = None
        if save_bit and "none" not in save_bit.lower():
            save = parse_money(save_bit) or parse_save(save_bit)
        # Sometimes size lands in save slot: "42 CT"
        size = ""
        for bit in (size_bit, save_bit):
            if bit and re.search(r"\b(\d+\s*(?:oz|lb|ct|cu\.?\s*ft))\b", bit, re.I):
                size = re.search(r"\b(\d+\s*(?:oz|lb|ct|cu\.?\s*ft))\b", bit, re.I).group(1)
                if bit == save_bit and save is None:
                    pass
                break
        if size_bit and "none" not in size_bit.lower() and not size:
            if parse_money(size_bit) is None and not re.search(r"save", size_bit, re.I):
                size = size_bit[:40]
        _add(name, price, save, line, size=size)

    if verified and ("$" in verified or re.search(r"\d+\.\d{2}", verified) or "|" in verified):
        for chunk in _iter_pipe_chunks(verified):
            if "|" in chunk:
                _parse_pipe_line(chunk)
                continue
            nums = re.findall(r"(\d+(?:\.\d{1,2})?)", chunk)
            if not nums:
                continue
            price = float(nums[-1])
            save = None
            sm = _SAVE_RE.search(chunk)
            if sm:
                try:
                    save = float(sm.group(1))
                except ValueError:
                    save = None
            name = chunk
            name = _PRICE_RE.sub(" ", name)
            name = _SAVE_RE.sub(" ", name)
            name = re.sub(r"\b\d+(?:\.\d+)?\b", " ", name)
            name = re.sub(
                r"\b(as advertised|stand up bag|per lb|per oz|lb|oz|ct|family size|save|off|sale)\b",
                " ",
                name,
                flags=re.I,
            )
            name = re.sub(r"\s+", " ", name).strip(" -:|,.")
            if not name or not _name_ok(name):
                continue
            _add(name.title() if name.isupper() else name, price, save, chunk)

    blob = description
    if "$" in blob or "|" in blob:
        chunks = [ln.strip() for ln in blob.replace(";", "\n").splitlines() if ln.strip()]
        if len(chunks) == 1 and ". " in chunks[0]:
            chunks = [p.strip() for p in chunks[0].split(". ") if p.strip()]
        for chunk in chunks:
            if "|" in chunk and "$" in chunk:
                for sub in _iter_pipe_chunks(chunk):
                    _parse_pipe_line(sub) if "|" in sub else None
                continue
            if "$" not in chunk:
                continue
            # Prefer explicit tag copy in quotes / ALL CAPS product lines.
            tag = re.search(
                r'["“]?([A-Z][A-Z0-9][A-Z0-9 \'&\-]{2,50})\s+(\d+(?:\.\d+)?\s*OZ)?\s*\$?\s*(\d+\.\d{2})',
                chunk,
            )
            if tag:
                nm = tag.group(1).title()
                size = (tag.group(2) or "").strip()
                _add(nm, float(tag.group(3)), parse_save(chunk), chunk, size=size)
                continue
            pairs = list(
                re.finditer(
                    r"([A-Z][A-Za-z0-9&'\-]+(?:\s+[A-Z][A-Za-z0-9&'\-]+){0,5})"
                    r"[^$\n]{0,48}"
                    r"\$\s*(\d+(?:\.\d{1,2})?)",
                    chunk,
                )
            )
            if len(pairs) >= 2:
                for m in pairs:
                    _add(m.group(1), float(m.group(2)), parse_save(chunk), chunk)
                continue
            price = parse_money(chunk)
            if price is None:
                continue
            # Cheese Balls / Doritos Cheese Balls patterns
            m = re.search(
                r"((?:Doritos\s+)?Cheese Balls|Sour Patch Kids|Hawaiian Island Pack|"
                r"Hawaiian Snack Pack|BouleBag|Camp Chef|Pringles|"
                r"[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){0,4})",
                chunk,
            )
            name = m.group(1).strip() if m else ""
            if not name or len(name) < 3:
                continue
            size_m = re.search(r"(\d+(?:\.\d+)?\s*(?:oz|lb|ct))", chunk, re.I)
            _add(name, price, parse_save(chunk), chunk, size=(size_m.group(1) if size_m else ""))

    return _dedupe_products(out)


def extract_with_vision(path: Path) -> list[dict[str, Any]]:
    """Structured product lines from the image (one short VLM call)."""
    try:
        from apps.core.services import ollama as oc
    except Exception:
        return []
    prompt = (
        "Shelf price list. One line per DISTINCT price tag — never repeat a line. "
        "Format: NAME | $PRICE | SAVE $X or SAVE none | SIZE or none. "
        "NAME = brand on the package above/beside that tag "
        "(use the package even if the tag has no product name). "
        "If unreadable, skip — do not invent. Numbers exactly as printed. No intro."
    )
    raw = oc.look_sync(prompt, [path], timeout=90) or ""
    raw = re.sub(r"[ \t]+", " ", (raw or "")).strip()
    if not raw or raw.lower().startswith("ids:"):
        return []
    out: list[dict[str, Any]] = []
    for part in _iter_pipe_chunks(raw.replace("\n", "\n")):
        # also split plain newlines
        for line in re.split(r"[\n;]+", part):
            line = line.strip()
            if not line:
                continue
            line = re.sub(r"^\d+[\.\)]\s*", "", line)
            if "|" not in line and "$" not in line:
                continue
            bits = [b.strip() for b in line.split("|")]
            name = bits[0] if bits else ""
            price_bit = bits[1] if len(bits) > 1 else line
            save_bit = bits[2] if len(bits) > 2 else ""
            size_bit = bits[3] if len(bits) > 3 else ""
            if re.search(r"unclear|unknown|\?|^product$", name, re.I):
                continue
            price = parse_money(price_bit) or parse_money(line)
            if price is None or not _name_ok(name):
                continue
            save = None
            if save_bit and "none" not in save_bit.lower():
                save = parse_money(save_bit) or parse_save(save_bit)
            out.append(
                {
                    "name": _clean_product_name(name)[:80],
                    "price": price,
                    "save": save,
                    "size": size_bit if size_bit and "none" not in size_bit.lower() else "",
                    "raw": line[:200],
                }
            )
    return _dedupe_products(out)


def _history_has(hist: list[Any], *, image: str, price: float, ts: str) -> bool:
    """True if this image+price already logged (same photo re-process)."""
    img = (image or "")[:300]
    for h in hist:
        if not isinstance(h, dict):
            continue
        try:
            hp = float(h.get("price"))
        except (TypeError, ValueError):
            continue
        if hp != price:
            continue
        himg = str(h.get("image") or "")[:300]
        if img and himg == img:
            return True
        # same second stamp + same price
        if ts and str(h.get("ts") or "") == ts and hp == price:
            return True
    return False


def record_sightings(
    products: list[dict[str, Any]],
    *,
    image: str = "",
    folder: str = "",
    source: str = "vision",
    caption: str = "",
) -> list[dict[str, Any]]:
    """Amend prices.json + append sightings.jsonl.

    Same product + new price → update current price, keep prior in history
    (with that sighting's image + timestamp). Same photo+price → no-op.
    """
    products = _dedupe_products(products)
    if not products:
        return []
    data = _load()
    items = data.get("items") if isinstance(data.get("items"), list) else []
    by_id = {
        str(it.get("id") or ""): it
        for it in items
        if isinstance(it, dict) and it.get("id")
    }
    recorded: list[dict[str, Any]] = []
    ts = _now()
    img = (image or "")[:300]
    for prod in products:
        name = _clean_product_name(str(prod.get("name") or ""))
        if not _name_ok(name):
            continue
        try:
            price_f = float(prod.get("price"))
        except (TypeError, ValueError):
            continue
        sid = slug(name)
        # Merge into an existing longer/shorter id when names nest (doritos ↔ doritos-cheese-balls).
        prev = by_id.get(sid) if isinstance(by_id.get(sid), dict) else None
        if prev is None:
            for oid, oit in list(by_id.items()):
                oname = str(oit.get("name") or "").lower()
                if not oname:
                    continue
                if name.lower() in oname or oname in name.lower():
                    # Prefer the more specific id going forward.
                    better = _prefer_name(str(oit.get("name") or ""), name)
                    if slug(better) != oid:
                        # Retarget: move under better slug.
                        sid = slug(better)
                        name = better
                        prev = dict(oit)
                        prev["id"] = sid
                        prev["name"] = name[:80]
                        by_id.pop(oid, None)
                        by_id[sid] = prev
                    else:
                        sid = oid
                        name = better
                        prev = oit
                    break
        if prev is None:
            prev = {}
        hist = list(prev.get("history") if isinstance(prev.get("history"), list) else [])
        prev_price = prev.get("price")
        try:
            prev_f = float(prev_price) if prev_price is not None else None
        except (TypeError, ValueError):
            prev_f = None
        # Same photo + same price already current → skip (no sighting inflation).
        if (
            img
            and prev_f is not None
            and prev_f == price_f
            and _history_has(hist, image=img, price=price_f, ts="")
        ):
            row = dict(prev)
            row["id"] = sid
            row["name"] = _prefer_name(str(prev.get("name") or ""), name)[:80]
            by_id[sid] = row
            recorded.append(row)
            continue
        entry = {
            "ts": ts,
            "price": price_f,
            "save": prod.get("save"),
            "size": str(prod.get("size") or "")[:40],
            "image": img,
            "folder": folder[:40],
            "caption": caption[:120],
            "source": source,
        }
        hist = (hist + [entry])[-MAX_HISTORY_PER:]
        changed = prev_f is not None and prev_f != price_f
        save_val = prod.get("save")
        if save_val is None:
            save_val = prev.get("save")
        row = {
            "id": sid,
            "name": _prefer_name(str(prev.get("name") or ""), name)[:80],
            "price": price_f,
            "save": save_val,
            "size": str(prod.get("size") or prev.get("size") or "")[:40],
            "last_seen": ts,
            "last_image": img or str(prev.get("last_image") or ""),
            "folder": folder[:40] or str(prev.get("folder") or ""),
            "sightings": int(prev.get("sightings") or 0) + 1,
            "prev_price": prev_f if changed else prev.get("prev_price"),
            "history": hist,
        }
        by_id[sid] = row
        recorded.append(row)
        _append_history(
            {
                "ts": ts,
                "id": sid,
                "name": row["name"],
                "price": price_f,
                "save": save_val,
                "size": row.get("size"),
                "image": img,
                "folder": folder[:40],
                "source": source,
                "changed": changed,
                "prev_price": prev_f if changed else None,
            }
        )
    data["items"] = sorted(
        by_id.values(),
        key=lambda r: str(r.get("last_seen") or ""),
        reverse=True,
    )[:MAX_ITEMS]
    _save(data)
    return recorded


def from_vision_row(row: dict[str, Any], *, path: Path | None = None) -> list[dict[str, Any]]:
    """Extract + record products from a vision analyze row."""
    desc = str(row.get("description") or "")
    verified = str(row.get("verified") or "")
    products = extract_from_text(desc, verified)
    uniq_prices = _unique_prices(desc, verified)
    # Weak only when we have almost nothing — do not treat VLM spam dollar-counts as "many products".
    weak = not products
    img_path = path
    if img_path is None:
        for key in ("src", "sorted"):
            cand = Path(str(row.get(key) or ""))
            if cand.is_file():
                img_path = cand
                break
    wants_prices = bool(uniq_prices) or "price" in desc.lower()
    if wants_prices and weak and img_path and img_path.is_file():
        print(
            f"product-prices extract pass path={img_path} "
            f"text_n={len(products)} unique_dollars={len(uniq_prices)}",
            flush=True,
        )
        vis = extract_with_vision(img_path)
        if vis:
            products = vis
    if not products:
        return []
    return record_sightings(
        products,
        image=str(row.get("sorted") or row.get("src") or ""),
        folder=str(row.get("folder") or ""),
        caption=str(row.get("caption") or ""),
        source="vision",
    )


def lookup(name: str) -> dict[str, Any] | None:
    sid = slug(name)
    data = _load()
    for it in data.get("items") or []:
        if isinstance(it, dict) and it.get("id") == sid:
            return dict(it)
    low = (name or "").lower()
    for it in data.get("items") or []:
        if not isinstance(it, dict):
            continue
        if low and low in str(it.get("name") or "").lower():
            return dict(it)
    return None


def recent(limit: int = 12) -> list[dict[str, Any]]:
    data = _load()
    items = [it for it in (data.get("items") or []) if isinstance(it, dict)]
    return items[: max(1, min(limit, 40))]


def remove_ids(ids: list[str]) -> int:
    """Drop junk items by id. History jsonl is left as audit trail."""
    want = {slug(i) for i in ids}
    data = _load()
    before = len(data.get("items") or [])
    data["items"] = [
        it
        for it in (data.get("items") or [])
        if isinstance(it, dict) and str(it.get("id") or "") not in want
    ]
    _save(data)
    return before - len(data["items"])


def prompt_block(*, cap: int = 500, ask: str = "") -> str:
    """Lines for desk / vision recall."""
    q = (ask or "").strip().lower()
    items = recent(16)
    if not items:
        return ""
    if q:
        hit = lookup(q)
        focused = [hit] if hit else []
        if not focused:
            focused = [
                it
                for it in items
                if any(
                    tok in str(it.get("name") or "").lower()
                    for tok in re.findall(r"[a-z0-9]{3,}", q)
                )
            ][:8]
        if focused:
            items = focused
    lines = ["Store prices (from shelf photos — quote; do not invent):"]
    for it in items[:10]:
        name = str(it.get("name") or it.get("id") or "?")
        price = it.get("price")
        save = it.get("save")
        seen = str(it.get("last_seen") or "")[:16]
        bit = f"- {name}: ${price:.2f}" if isinstance(price, (int, float)) else f"- {name}: {price}"
        if isinstance(save, (int, float)) and save > 0:
            bit += f" (save ${save:.2f})"
        size = str(it.get("size") or "").strip()
        if size:
            bit += f" · {size}"
        prev = it.get("prev_price")
        if isinstance(prev, (int, float)) and isinstance(price, (int, float)) and prev != price:
            bit += f" (was ${prev:.2f})"
        if seen:
            bit += f" · {seen}"
        lines.append(bit)
    blob = "\n".join(lines)
    return blob if len(blob) <= cap else blob[: cap - 1] + "…"


def _ask_wants_prices(ask: str) -> bool:
    low = (ask or "").lower()
    return any(
        k in low
        for k in (
            "price",
            "prices",
            "cost",
            "how much",
            "store",
            "shopping",
            "shelf",
            "product",
            "grocery",
            "deal",
            "sale",
            "pringles",
            "sour patch",
            "doritos",
            "cheese balls",
            "hawaiian",
            "walmart",
            "safeway",
            "target",
        )
    )


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"recent", "list"}:
        for it in recent(20):
            print(
                f"{it.get('name')}\t${it.get('price')}\t"
                f"save={it.get('save')}\tseen={it.get('last_seen')}"
            )
        return 0
    if args[0] == "lookup" and len(args) > 1:
        hit = lookup(" ".join(args[1:]))
        print(json.dumps(hit or {}, indent=2))
        return 0 if hit else 1
    if args[0] == "prompt":
        print(prompt_block(ask=" ".join(args[1:])))
        return 0
    if args[0] == "remove" and len(args) > 1:
        n = remove_ids(args[1:])
        print(f"removed {n}")
        return 0
    print(
        "usage: product_prices.py [recent|lookup NAME|prompt …|remove ID…]",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
