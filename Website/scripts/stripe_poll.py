# ==============================================================================
# FILE: Website/scripts/stripe_poll.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Refresh the Stripe balance snapshot. Stdlib only. Never prints the secret.

  python3 stripe_poll.py

With no key, writes ok=false detail=not_configured and exits 0.
On a failed live poll, keeps the previous ok snapshot and does not replace it.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
import time  # info: import time
import urllib.error  # info: import urllib . error
import urllib.parse  # info: import urllib . parse
import urllib.request  # info: import urllib . request
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
if str(ROOT) not in sys.path:  # info: if str ( ROOT ) not in sys
    sys.path.insert(0, str(ROOT))  # info: sys . path . insert ( 0 ,

from lib.envload import stripe_secret  # noqa: E402

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE
SNAPSHOT = DATABASE / "Website" / "stripe-snapshot.json"  # info: set SNAPSHOT
STRIPE_API = "https://api.stripe.com/v1"  # info: set STRIPE_API
FRESH_S = 25 * 60  # info: set FRESH_S
TIMEOUT_S = 25  # info: set TIMEOUT_S


# ====================================================
# SECTION: function _usd
# What it does:  usd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _usd(cents: Any) -> float:  # info: def _usd
    try:  # info: try :
        return round(int(cents) / 100.0, 2)  # info: return round ( int ( cents ) /
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return 0.0  # info: return 0.0


# ====================================================
# SECTION: function read_snapshot
# What it does: read snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_snapshot() -> dict[str, Any]:  # info: def read_snapshot
    if not SNAPSHOT.is_file():  # info: if not SNAPSHOT . is_file ( ) :
        return {}  # info: return { }
    try:  # info: try :
        raw = json.loads(SNAPSHOT.read_text(encoding="utf-8"))  # info: set raw
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {}  # info: return { }
    return raw if isinstance(raw, dict) else {}  # info: return raw if isinstance ( raw , dict


# ====================================================
# SECTION: function snapshot_age_s
# What it does: snapshot age s.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def snapshot_age_s(snap: dict[str, Any]) -> float | None:  # info: def snapshot_age_s
    try:  # info: try :
        v = float(snap.get("fetchedAt"))  # info: set v
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return None  # info: return None
    if v > 10_000_000_000:  # info: if v > 10_000_000_000 :
        v = v / 1000.0  # info: set v
    if v <= 0:  # info: if v <= 0 :
        return None  # info: return None
    return time.time() - v  # info: return time . time ( ) - v


# ====================================================
# SECTION: function _write
# What it does:  write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(snap: dict[str, Any]) -> None:  # info: def _write
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)  # info: SNAPSHOT . parent . mkdir ( parents =
    tmp = SNAPSHOT.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(snap, indent=2), encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(SNAPSHOT)  # info: tmp . replace ( SNAPSHOT )


# ====================================================
# SECTION: function _get
# What it does:  get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(path: str, params: dict[str, str], secret: str) -> dict[str, Any]:  # info: def _get
    query = urllib.parse.urlencode(params)  # info: set query
    url = STRIPE_API + path + ("?" + query if query else "")  # info: set url
    req = urllib.request.Request(  # info: set req
        url,  # info: url ,
        headers={  # info: set headers
            "Authorization": "Bearer " + secret,  # info: "Authorization" : "Bearer " + secret ,
            "Stripe-Version": "2024-06-20",  # info: "Stripe-Version" : "2024-06-20" ,
            "Accept": "application/json",  # info: "Accept" : "application/json" ,
        },  # info: } ,
        method="GET",  # info: set method
    )  # info: )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # info: with urllib . request . urlopen ( req
            body = json.loads(resp.read().decode("utf-8"))  # info: set body
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        raise RuntimeError(f"stripe {path} {exc.code}") from None  # info: raise RuntimeError ( f" stripe { path }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:  # info: except ( urllib . error . URLError ,
        raise RuntimeError(f"stripe {path} failed") from None  # info: raise RuntimeError ( f" stripe { path }
    if not isinstance(body, dict):  # info: if not isinstance ( body , dict )
        raise RuntimeError(f"stripe {path} bad body")  # info: raise RuntimeError ( f" stripe { path }
    return body  # info: return body


# ====================================================
# SECTION: function _explain
# What it does:  explain.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _explain(avail: float, pending: float) -> dict[str, Any]:  # info: def _explain
    covers = pending + avail >= -0.05  # info: set covers
    healthy = -1.0 < avail < 0 and covers  # info: set healthy
    return {  # info: return {
        "avail": avail,  # info: "avail" : avail ,
        "pending": pending,  # info: "pending" : pending ,
        "pendingCoversDeficit": bool(avail < 0 and covers),  # info: "pendingCoversDeficit" : bool ( avail < 0 and
        "healthyTiming": bool(healthy),  # info: "healthyTiming" : bool ( healthy ) ,
    }  # info: }


# ====================================================
# SECTION: function _live
# What it does:  live.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _live(secret: str) -> dict[str, Any]:  # info: def _live
    since = str(int(time.time()) - 30 * 24 * 3600)  # info: set since
    bal = _get("/balance", {}, secret)  # info: set bal
    tx = _get("/balance_transactions", {"limit": "100", "created[gte]": since}, secret)  # info: set tx
    pays = _get("/payouts", {"limit": "100", "created[gte]": since, "status": "paid"}, secret)  # info: set pays
    available = [  # info: set available
        {"currency": r.get("currency"), "amount": _usd(r.get("amount"))}  # info: { "currency" : r . get ( "currency"
        for r in (bal.get("available") or [])  # info: for r in ( bal . get (
        if isinstance(r, dict)  # info: if isinstance ( r , dict )
    ]  # info: ]
    pending = [  # info: set pending
        {"currency": r.get("currency"), "amount": _usd(r.get("amount"))}  # info: { "currency" : r . get ( "currency"
        for r in (bal.get("pending") or [])  # info: for r in ( bal . get (
        if isinstance(r, dict)  # info: if isinstance ( r , dict )
    ]  # info: ]
    usd_avail = round(sum(float(r.get("amount") or 0) for r in available if r.get("currency") == "usd"), 2)  # info: set usd_avail
    usd_pend = round(sum(float(r.get("amount") or 0) for r in pending if r.get("currency") == "usd"), 2)  # info: set usd_pend
    income = 0.0  # info: set income
    fees = 0.0  # info: set fees
    recent: list[dict[str, Any]] = []  # info: set recent
    for row in tx.get("data") or []:  # info: for row in tx . get ( "data"
        if not isinstance(row, dict) or str(row.get("currency") or "").lower() != "usd":  # info: if not isinstance ( row , dict )
            continue  # info: continue
        amt = _usd(row.get("amount"))  # info: set amt
        fee = _usd(row.get("fee"))  # info: set fee
        kind = str(row.get("type") or "other")  # info: set kind
        if amt > 0:  # info: if amt > 0 :
            income += amt  # info: set income
        fees += abs(fee)  # info: set fees
        created = row.get("created")  # info: set created
        created_iso: Any = created  # info: set created_iso
        if isinstance(created, (int, float)):  # info: if isinstance ( created , ( int ,
            created_iso = datetime.fromtimestamp(int(created), tz=timezone.utc).isoformat()  # info: set created_iso
        recent.append({  # info: recent . append ( {
            "id": row.get("id"),  # info: "id" : row . get ( "id" )
            "type": kind,  # info: "type" : kind ,
            "amount": amt,  # info: "amount" : amt ,
            "fee": fee,  # info: "fee" : fee ,
            "net": _usd(row.get("net")),  # info: "net" : _usd ( row . get (
            "description": row.get("description") or kind,  # info: "description" : row . get ( "description" )
            "created": created_iso,  # info: "created" : created_iso ,
            "currency": "usd",  # info: "currency" : "usd" ,
        })  # info: } )
        if len(recent) >= 40:  # info: if len ( recent ) >= 40 :
            break  # info: break
    payouts = 0.0  # info: set payouts
    for row in pays.get("data") or []:  # info: for row in pays . get ( "data"
        if isinstance(row, dict) and str(row.get("currency") or "").lower() == "usd":  # info: if isinstance ( row , dict ) and
            payouts += _usd(row.get("amount"))  # info: set payouts
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "source": "stripe_balance_api",  # info: "source" : "stripe_balance_api" ,
        "fetchedAt": int(time.time() * 1000),  # info: "fetchedAt" : int ( time . time (
        "available": available,  # info: "available" : available ,
        "pending": pending,  # info: "pending" : pending ,
        "usdAvailable": usd_avail,  # info: "usdAvailable" : usd_avail ,
        "usdPending": usd_pend,  # info: "usdPending" : usd_pend ,
        "income30dUsd": round(income, 2),  # info: "income30dUsd" : round ( income , 2 )
        "fees30dUsd": round(fees, 2),  # info: "fees30dUsd" : round ( fees , 2 )
        "payouts30dUsd": round(payouts, 2),  # info: "payouts30dUsd" : round ( payouts , 2 )
        "recent": recent,  # info: "recent" : recent ,
        "explain": _explain(usd_avail, usd_pend),  # info: "explain" : _explain ( usd_avail , usd_pend )
    }  # info: }


# ====================================================
# SECTION: function poll
# What it does: poll.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poll(*, force: bool = False) -> dict[str, Any]:  # info: def poll
    existing = read_snapshot()  # info: set existing
    age = snapshot_age_s(existing)  # info: set age
    if existing.get("ok") and age is not None and age < FRESH_S and not force:  # info: if existing . get ( "ok" ) and
        return existing  # info: return existing
    secret = stripe_secret()  # info: set secret
    if not secret.startswith("sk_"):  # info: if not secret . startswith ( "sk_" )
        out = {  # info: set out
            "ok": False,  # info: "ok" : False ,
            "source": "stripe_balance_api",  # info: "source" : "stripe_balance_api" ,
            "fetchedAt": int(time.time() * 1000),  # info: "fetchedAt" : int ( time . time (
            "detail": "not_configured",  # info: "detail" : "not_configured" ,
        }  # info: }
        _write(out)  # info: call _write
        return out  # info: return out
    try:  # info: try :
        snap = _live(secret)  # info: set snap
    except RuntimeError as exc:  # info: except RuntimeError as exc :
        if existing.get("ok"):  # info: if existing . get ( "ok" ) :
            existing["stale"] = True  # info: existing [ "stale" ] = True
            existing["pollError"] = str(exc)[:180]  # info: existing [ "pollError" ] = str ( exc
            return existing  # info: return existing
        out = {  # info: set out
            "ok": False,  # info: "ok" : False ,
            "source": "stripe_balance_api",  # info: "source" : "stripe_balance_api" ,
            "fetchedAt": int(time.time() * 1000),  # info: "fetchedAt" : int ( time . time (
            "detail": "poll_failed",  # info: "detail" : "poll_failed" ,
            "error": str(exc)[:180],  # info: "error" : str ( exc ) [ :
        }  # info: }
        _write(out)  # info: call _write
        return out  # info: return out
    _write(snap)  # info: call _write
    return snap  # info: return snap


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    snap = poll(force=False)  # info: set snap
    detail = "ok" if snap.get("ok") else snap.get("detail") or "fail"  # info: set detail
    print(f"stripe {detail}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
