#!/usr/bin/env python3
"""ApiPrices commands. Package ApiPrices.

refresh — seed locally. Public-doc GET only when RR_API_PRICES=1.
cursor-drain — one Cursor ask only when RR_API_SPEND=1.
proof — offline seed on a temp RR_DATABASE_ROOT. Refuses the live Database.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import api_ledger  # noqa: E402

LIVE_DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database").resolve()


def _root_is_live(root: Path) -> bool:
    root = root.resolve()
    return root == LIVE_DB or LIVE_DB in root.parents or root in LIVE_DB.parents


def proof() -> int:
    raw = os.environ.get("RR_DATABASE_ROOT", "").strip()
    if not raw:
        print("proof requires RR_DATABASE_ROOT outside the live Database")
        return 2
    root = Path(raw)
    if _root_is_live(root):
        print("proof refuses the live Database tree")
        return 2
    os.environ.pop("RR_API_PRICES", None)
    os.environ.pop("RR_API_SPEND", None)
    seeded = api_ledger.seed(source="proof")
    prices = api_ledger.latest_catalog()
    xai_ok, xai_why = api_ledger.may_spend("xai")
    cur_ok, cur_why = api_ledger.may_spend("cursor")
    http_n = api_ledger.STATS["http_attempts"]
    spend_n = api_ledger.STATS["spend_attempts"]
    if seeded < 1 or not prices or xai_ok or cur_ok or http_n or spend_n:
        print(
            f"proof failed seeded={seeded} prices={len(prices)} "
            f"may_spend_xai={xai_ok}:{xai_why} may_spend_cursor={cur_ok}:{cur_why} "
            f"http_attempts={http_n} spend_attempts={spend_n}"
        )
        return 1
    if api_ledger.prices_gate_open() or api_ledger.spend_gate_open():
        print("proof failed gates open")
        return 1
    print(
        f"proof ok seeded={seeded} prices={len(prices)} "
        f"may_spend_xai={xai_ok} ({xai_why}) may_spend_cursor={cur_ok} ({cur_why}) "
        f"http_attempts={http_n} spend_attempts={spend_n}"
    )
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "refresh"
    if cmd == "proof":
        return proof()
    if cmd == "seed":
        n = api_ledger.seed(source="cli")
        print(f"seeded={n}")
        return 0
    if cmd == "refresh":
        out = api_ledger.refresh(source="daily")
        print(f"refresh detail={out.get('detail', 'ok')} http={out.get('http')} seeded={out.get('seeded_rows')}")
        return 0
    if cmd == "cursor-drain":
        import cursor_fallback

        job = cursor_fallback.drain_one()
        print("cursor-drain empty" if not job else "cursor-drain stored")
        return 0
    print("usage: job.py proof|seed|refresh|cursor-drain")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
