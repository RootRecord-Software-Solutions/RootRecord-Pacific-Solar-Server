#!/usr/bin/env python3
"""Gig index. Domain and page names only. The client site is not rehosted."""
from __future__ import annotations

import json
from pathlib import Path

GIGS = Path(
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/Clients/gigs.json"
)


def load() -> dict:
    data = json.loads(GIGS.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("gigs file is not an object")
    return data


def lines(data: dict) -> list[str]:
    out = ["Web-dev gigs (not memberships):"]
    rows = data.get("gigs") or []
    if not rows:
        out.append("- none on file")
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        pages = ", ".join(str(p) for p in (row.get("pages") or []))
        out.append(f"- {row.get('domain')}: {pages}")
        note = str(row.get("note") or "").strip()
        if note:
            out.append(f"  {note}")
    return out


def main() -> int:
    for line in lines(load()):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
