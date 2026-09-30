#!/usr/bin/env python3
"""Public Fern Forest lot facts. No owner names, mailing addresses, or watts."""
from __future__ import annotations

import json
from pathlib import Path

FACTS = Path(
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/FernForest/facts.json"
)


def load() -> dict:
    data = json.loads(FACTS.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("facts file is not an object")
    return data


def lines(data: dict) -> list[str]:
    out = [
        f"{data.get('place')} — {data.get('acres')} acres, {data.get('class')}",
    ]
    for lot in data.get("lots") or []:
        if not isinstance(lot, dict):
            continue
        out.append(
            f"- TMK {lot.get('tmk')} lot {lot.get('lot')} {lot.get('qpublic')}"
        )
    return out


def main() -> int:
    for line in lines(load()):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
