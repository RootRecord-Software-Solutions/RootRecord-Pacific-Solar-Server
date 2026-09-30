# ==============================================================================
# FILE: System/ApiPrices/scripts/job.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""ApiPrices commands. Package ApiPrices.

refresh — seed locally. Public-doc GET only when RR_API_PRICES=1.
cursor-drain — one Cursor ask only when RR_API_SPEND=1.
proof — offline seed on a temp RR_DATABASE_ROOT. Refuses the live Database.
"""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

_HERE = Path(__file__).resolve().parent  # info: set _HERE
if str(_HERE) not in sys.path:  # info: if str ( _HERE ) not in sys
    sys.path.insert(0, str(_HERE))  # info: sys . path . insert ( 0 ,

import api_ledger  # noqa: E402

LIVE_DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database").resolve()  # info: set LIVE_DB


# ====================================================
# SECTION: function _root_is_live
# What it does:  root is live.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _root_is_live(root: Path) -> bool:  # info: def _root_is_live
    root = root.resolve()  # info: set root
    return root == LIVE_DB or LIVE_DB in root.parents or root in LIVE_DB.parents  # info: return root == LIVE_DB or LIVE_DB in root


# ====================================================
# SECTION: function proof
# What it does: proof.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def proof() -> int:  # info: def proof
    raw = os.environ.get("RR_DATABASE_ROOT", "").strip()  # info: set raw
    if not raw:  # info: if not raw :
        print("proof requires RR_DATABASE_ROOT outside the live Database")  # info: call print
        return 2  # info: return 2
    root = Path(raw)  # info: set root
    if _root_is_live(root):  # info: if _root_is_live ( root ) :
        print("proof refuses the live Database tree")  # info: call print
        return 2  # info: return 2
    os.environ.pop("RR_API_PRICES", None)  # info: os . environ . pop ( "RR_API_PRICES" ,
    os.environ.pop("RR_API_SPEND", None)  # info: os . environ . pop ( "RR_API_SPEND" ,
    seeded = api_ledger.seed(source="proof")  # info: set seeded
    prices = api_ledger.latest_catalog()  # info: set prices
    xai_ok, xai_why = api_ledger.may_spend("xai")  # info: xai_ok , xai_why = api_ledger . may_spend (
    cur_ok, cur_why = api_ledger.may_spend("cursor")  # info: cur_ok , cur_why = api_ledger . may_spend (
    http_n = api_ledger.STATS["http_attempts"]  # info: set http_n
    spend_n = api_ledger.STATS["spend_attempts"]  # info: set spend_n
    if seeded < 1 or not prices or xai_ok or cur_ok or http_n or spend_n:  # info: if seeded < 1 or not prices or
        print(  # info: call print
            f"proof failed seeded={seeded} prices={len(prices)} "  # info: f" proof failed seeded= { seeded } prices= { len
            f"may_spend_xai={xai_ok}:{xai_why} may_spend_cursor={cur_ok}:{cur_why} "  # info: f" may_spend_xai= { xai_ok } : { xai_why
            f"http_attempts={http_n} spend_attempts={spend_n}"  # info: f" http_attempts= { http_n } spend_attempts= { spend_n
        )  # info: )
        return 1  # info: return 1
    if api_ledger.prices_gate_open() or api_ledger.spend_gate_open():  # info: if api_ledger . prices_gate_open ( ) or api_ledger
        print("proof failed gates open")  # info: call print
        return 1  # info: return 1
    print(  # info: call print
        f"proof ok seeded={seeded} prices={len(prices)} "  # info: f" proof ok seeded= { seeded } prices= { len
        f"may_spend_xai={xai_ok} ({xai_why}) may_spend_cursor={cur_ok} ({cur_why}) "  # info: f" may_spend_xai= { xai_ok } ( { xai_why
        f"http_attempts={http_n} spend_attempts={spend_n}"  # info: f" http_attempts= { http_n } spend_attempts= { spend_n
    )  # info: )
    return 0  # info: return 0


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    cmd = argv[1] if len(argv) > 1 else "refresh"  # info: set cmd
    if cmd == "proof":  # info: if cmd == "proof" :
        return proof()  # info: return proof ( )
    if cmd == "seed":  # info: if cmd == "seed" :
        n = api_ledger.seed(source="cli")  # info: set n
        print(f"seeded={n}")  # info: call print
        return 0  # info: return 0
    if cmd == "refresh":  # info: if cmd == "refresh" :
        out = api_ledger.refresh(source="daily")  # info: set out
        print(f"refresh detail={out.get('detail', 'ok')} http={out.get('http')} seeded={out.get('seeded_rows')}")  # info: call print
        return 0  # info: return 0
    if cmd == "cursor-drain":  # info: if cmd == "cursor-drain" :
        import cursor_fallback  # info: import cursor_fallback

        job = cursor_fallback.drain_one()  # info: set job
        print("cursor-drain empty" if not job else "cursor-drain stored")  # info: call print
        return 0  # info: return 0
    print("usage: job.py proof|seed|refresh|cursor-drain")  # info: call print
    return 2  # info: return 2


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv))  # info: raise SystemExit ( main ( sys . argv
