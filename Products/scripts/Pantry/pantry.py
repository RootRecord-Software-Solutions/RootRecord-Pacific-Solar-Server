#!/usr/bin/env python3
"""Household food stock. Counts are logged, never invented."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

STORE = Path(
    os.environ.get(
        "PANTRY_STORE",
        str(Path.home() / ".ollama" / "skills" / "pantry" / "store" / "stock.json"),
    )
)
NAME_CAP = 80
MAX_ITEMS = 400
PANTRY_TAG = re.compile(r"<<<PANTRY\s+(add|use|set)\s+([^>]*?)>>>", re.I)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()) + "-10:00"


def slug(name: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return (raw or "item")[:48]


def _load() -> dict[str, Any]:
    if not STORE.is_file():
        return {"updated": _now(), "items": [], "aliases": {}}
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"updated": _now(), "items": [], "aliases": {}}
    return data if isinstance(data, dict) else {"updated": _now(), "items": [], "aliases": {}}


def _save(data: dict[str, Any]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["updated"] = _now()
    tmp = STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STORE)


def _qty(raw: Any) -> float | str:
    if raw is None or raw == "":
        return "some"
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip().lower()
    if text in {"some", "a", "an", "few", "leftover", "leftovers"}:
        return "some"
    try:
        return float(text)
    except ValueError:
        return "some"


def _aliases(data: dict[str, Any]) -> dict[str, str]:
    raw = data.get("aliases") or {}
    if not isinstance(raw, dict):
        return {}
    return {slug(str(k)): slug(str(v)) for k, v in raw.items() if k and v}


def resolve_id(name: str, data: dict[str, Any] | None = None) -> str:
    sid = slug(name)
    data = data if data is not None else _load()
    aliases = _aliases(data)
    return aliases.get(sid, sid)


def items() -> list[dict[str, Any]]:
    rows = _load().get("items") or []
    return [i for i in rows if isinstance(i, dict) and i.get("id")]


def have_ids() -> set[str]:
    out: set[str] = set()
    data = _load()
    aliases = _aliases(data)
    reverse: dict[str, list[str]] = {}
    for src, dst in aliases.items():
        reverse.setdefault(dst, []).append(src)
    for row in items():
        qty = row.get("qty")
        if qty == 0 or qty == 0.0:
            continue
        iid = str(row.get("id") or "")
        if not iid:
            continue
        out.add(iid)
        out.update(reverse.get(iid) or [])
        for a in row.get("aliases") or []:
            out.add(slug(str(a)))
    return out


def get(name: str) -> dict[str, Any] | None:
    data = _load()
    want = resolve_id(name, data)
    for row in data.get("items") or []:
        if isinstance(row, dict) and row.get("id") == want:
            return row
    return None


def _bump(name: str, delta: float | str, *, unit: str, voice: str, mode: str) -> dict[str, Any]:
    name = (name or "").strip()[:NAME_CAP]
    if not name:
        return {"ok": False, "error": "empty_name"}
    data = _load()
    rows = [i for i in (data.get("items") or []) if isinstance(i, dict)]
    iid = resolve_id(name, data)
    row = next((i for i in rows if i.get("id") == iid), None)
    if row is None:
        if mode == "use":
            return {"ok": False, "error": "missing", "id": iid}
        if len(rows) >= MAX_ITEMS:
            return {"ok": False, "error": "cap"}
        row = {
            "id": iid,
            "name": name,
            "qty": 0,
            "unit": (unit or "ea")[:16],
            "created": _now(),
        }
        rows.append(row)
    if unit:
        row["unit"] = unit[:16]
    cur = row.get("qty")
    if mode == "set":
        row["qty"] = delta
    elif delta == "some" or cur == "some":
        row["qty"] = "some" if mode == "add" else (0 if mode == "use" else delta)
        if mode == "use" and cur == "some":
            row["qty"] = "some"
            row["note"] = "used some; count still unknown"
    else:
        try:
            base = float(cur or 0)
            change = float(delta)
        except (TypeError, ValueError):
            row["qty"] = "some"
        else:
            nxt = base + change if mode == "add" else base - change
            row["qty"] = nxt if nxt > 0 else 0
    row["updated"] = _now()
    row["updated_by"] = voice
    data["items"] = rows
    _save(data)
    return {"ok": True, "id": iid, "qty": row.get("qty"), "unit": row.get("unit"), "action": mode}


def add_item(name: str, qty: Any = 1, *, unit: str = "ea", voice: str = "cli") -> dict[str, Any]:
    return _bump(name, _qty(qty), unit=unit, voice=voice, mode="add")


def use_item(name: str, qty: Any = 1, *, voice: str = "cli") -> dict[str, Any]:
    return _bump(name, _qty(qty), unit="", voice=voice, mode="use")


def set_item(name: str, qty: Any, *, unit: str = "ea", voice: str = "cli") -> dict[str, Any]:
    return _bump(name, _qty(qty), unit=unit, voice=voice, mode="set")


def prompt_lines(*, cap: int = 3500) -> str:
    rows = [i for i in items() if i.get("qty") not in (0, 0.0)]
    lines = ["Pantry stock (logged only):"]
    if not rows:
        lines.append("- empty on file")
    for row in sorted(rows, key=lambda r: str(r.get("name") or "")):
        lines.append(f"- {row.get('id')}: {row.get('qty')} {row.get('unit') or 'ea'} ({row.get('name')})")
    blob = "\n".join(lines)
    if len(blob) > cap:
        return blob[: cap - 1] + "…"
    return blob


def apply_pantry_tags(raw: str, *, voice: str) -> None:
    for kind, body in PANTRY_TAG.findall(raw or ""):
        parts = [p.strip() for p in (body or "").split("|")]
        name = parts[0] if parts else ""
        qty = parts[1] if len(parts) > 1 else 1
        unit = parts[2] if len(parts) > 2 else "ea"
        k = kind.lower()
        if k == "add":
            add_item(name, qty, unit=unit, voice=voice)
        elif k == "use":
            use_item(name, qty, voice=voice)
        elif k == "set":
            set_item(name, qty, unit=unit, voice=voice)


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"list", "show"}:
        print(prompt_lines())
        return 0
    if args[0] == "add" and len(args) > 1:
        name = args[1]
        qty = args[2] if len(args) > 2 else 1
        unit = args[3] if len(args) > 3 else "ea"
        if len(args) == 3 and not _looks_qty(args[2]):
            name = " ".join(args[1:])
            qty = 1
            unit = "ea"
        elif len(args) > 4:
            name = " ".join(args[1:-2])
            qty = args[-2]
            unit = args[-1]
        print(json.dumps(add_item(name, qty, unit=unit, voice="cli")))
        return 0
    if args[0] == "use" and len(args) > 1:
        qty = args[-1] if len(args) > 2 and _looks_qty(args[-1]) else 1
        name = " ".join(args[1:-1] if len(args) > 2 and _looks_qty(args[-1]) else args[1:])
        print(json.dumps(use_item(name, qty, voice="cli")))
        return 0
    if args[0] == "set" and len(args) > 1:
        unit = args[-1] if len(args) > 3 else "ea"
        qty = args[-2] if len(args) > 3 else (args[-1] if len(args) > 2 else "some")
        name = " ".join(args[1:-2] if len(args) > 3 else args[1:-1] if len(args) > 2 else args[1:])
        print(json.dumps(set_item(name, qty, unit=unit, voice="cli")))
        return 0
    print(json.dumps({"ok": False, "error": "usage"}))
    return 2


def _looks_qty(text: str) -> bool:
    t = (text or "").strip().lower()
    if t in {"some", "a", "an"}:
        return True
    try:
        float(t)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
