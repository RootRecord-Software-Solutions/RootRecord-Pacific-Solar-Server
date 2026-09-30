# ==============================================================================
# FILE: Products/scripts/FinanceDesk/finance_desk.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Desk finance payload from the live ledger + Stripe snapshot."""  # info: """Desk finance payload from the live ledger + Stripe snapshot."""
from __future__ import annotations  # info: from __future__ import annotations

import time  # info: import time
from typing import Any  # info: from typing import Any

from apps.core.services import public_finance as pub  # info: from apps . core . services import public_finance
from apps.core.services import stripe_poll  # info: from apps . core . services import stripe_poll


# ====================================================
# SECTION: function _ops_from_ledger
# What it does:  ops from ledger.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ops_from_ledger(ledger: dict) -> dict[str, Any]:  # info: def _ops_from_ledger
    expenses, income, _ = pub._collect_lines(ledger)  # info: expenses , income , _ = pub .
    exp_mo = round(sum(float(e.get("monthlyUsd") or 0) for e in expenses), 2)  # info: set exp_mo
    inc_mo = round(sum(float(i.get("monthlyUsd") or 0) for i in income), 2)  # info: set inc_mo
    projects = []  # info: set projects
    for p in ledger.get("projects") or []:  # info: for p in ledger . get ( "projects"
        if not isinstance(p, dict):  # info: if not isinstance ( p , dict )
            continue  # info: continue
        projects.append(  # info: projects . append (
            {  # info: {
                "id": p.get("id"),  # info: "id" : p . get ( "id" )
                "name": p.get("name") or p.get("label") or p.get("id"),  # info: "name" : p . get ( "name" )
            }  # info: }
        )  # info: )
    lines = []  # info: set lines
    for e in expenses:  # info: for e in expenses :
        lines.append(  # info: lines . append (
            {  # info: {
                "id": e.get("id"),  # info: "id" : e . get ( "id" )
                "kind": "expense",  # info: "kind" : "expense" ,
                "label": e.get("label"),  # info: "label" : e . get ( "label" )
                "amountUsd": e.get("amountUsd"),  # info: "amountUsd" : e . get ( "amountUsd" )
                "monthlyUsd": e.get("monthlyUsd"),  # info: "monthlyUsd" : e . get ( "monthlyUsd" )
                "period": e.get("period"),  # info: "period" : e . get ( "period" )
                "category": e.get("category"),  # info: "category" : e . get ( "category" )
                "project": e.get("project"),  # info: "project" : e . get ( "project" )
            }  # info: }
        )  # info: )
    for i in income:  # info: for i in income :
        lines.append(  # info: lines . append (
            {  # info: {
                "id": i.get("id"),  # info: "id" : i . get ( "id" )
                "kind": "income",  # info: "kind" : "income" ,
                "label": i.get("label"),  # info: "label" : i . get ( "label" )
                "amountUsd": i.get("amountUsd"),  # info: "amountUsd" : i . get ( "amountUsd" )
                "monthlyUsd": i.get("monthlyUsd"),  # info: "monthlyUsd" : i . get ( "monthlyUsd" )
                "period": i.get("period"),  # info: "period" : i . get ( "period" )
            }  # info: }
        )  # info: )
    return {  # info: return {
        "summary": {  # info: "summary" : {
            "projectCount": len(projects),  # info: "projectCount" : len ( projects ) ,
            "accountCount": len(ledger.get("accounts") or []),  # info: "accountCount" : len ( ledger . get (
            "expensesMonthlyUsd": exp_mo,  # info: "expensesMonthlyUsd" : exp_mo ,
            "expenseCount": len(expenses),  # info: "expenseCount" : len ( expenses ) ,
            "otherIncomeMonthlyUsd": inc_mo,  # info: "otherIncomeMonthlyUsd" : inc_mo ,
            "incomeCount": len(income),  # info: "incomeCount" : len ( income ) ,
            "netOtherMonthlyUsd": round(inc_mo - exp_mo, 2),  # info: "netOtherMonthlyUsd" : round ( inc_mo - exp_mo ,
            "staleIds": [],  # info: "staleIds" : [ ] ,
        },  # info: } ,
        "expenseCategories": [  # info: "expenseCategories" : [
            "hosting", "domains", "cloudflare", "software", "hardware",  # info: "hosting" , "domains" , "cloudflare" , "software" ,
            "utilities", "ads", "travel", "ops", "other",  # info: "utilities" , "ads" , "travel" , "ops" ,
        ],  # info: ] ,
        "projects": projects,  # info: "projects" : projects ,
        "accounts": ledger.get("accounts") or [],  # info: "accounts" : ledger . get ( "accounts" )
        "lines": lines,  # info: "lines" : lines ,
    }  # info: }


# ====================================================
# SECTION: function _stripe_block
# What it does:  stripe block.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _stripe_block(snap: dict[str, Any]) -> dict[str, Any]:  # info: def _stripe_block
    configured = stripe_poll.configured()  # info: set configured
    age = stripe_poll.snapshot_age_s(snap)  # info: set age
    age_ms = int(age * 1000) if age is not None else None  # info: set age_ms
    avail = float(snap.get("usdAvailable") or 0)  # info: set avail
    pending = float(snap.get("usdPending") or 0)  # info: set pending
    expl = snap.get("explain") if isinstance(snap.get("explain"), dict) else {  # info: set expl
        "avail": avail,  # info: "avail" : avail ,
        "pending": pending,  # info: "pending" : pending ,
        "pendingCoversDeficit": avail < 0 and (pending + avail) >= -0.05,  # info: "pendingCoversDeficit" : avail < 0 and ( pending
        "healthyTiming": -1.0 < avail < 0 and (pending + avail) >= -0.05,  # info: "healthyTiming" : - 1.0 < avail < 0
    }  # info: }
    ok = bool(snap.get("ok"))  # info: set ok
    plain = None  # info: set plain
    if ok:  # info: if ok :
        plain = f"Stripe snapshot {int(age)}s ago." if age is not None else "Stripe snapshot on disk."  # info: set plain
        if age is not None and age > 3600:  # info: if age is not None and age >
            plain = f"Stripe snapshot is {int(age / 3600)}h old — refresh if you need now."  # info: set plain
    elif configured:  # info: elif configured :
        plain = snap.get("detail") or snap.get("error") or "Stripe poll failed."  # info: set plain
    else:  # info: else :
        plain = "Stripe key not set."  # info: set plain
    return {  # info: return {
        "configured": configured,  # info: "configured" : configured ,
        "ok": ok,  # info: "ok" : ok ,
        "reason": None if ok else (snap.get("detail") or snap.get("error") or "not_configured"),  # info: "reason" : None if ok else ( snap
        "usdAvailable": avail if ok else None,  # info: "usdAvailable" : avail if ok else None ,
        "usdPending": pending if ok else None,  # info: "usdPending" : pending if ok else None ,
        "income30dUsd": snap.get("income30dUsd") if ok else None,  # info: "income30dUsd" : snap . get ( "income30dUsd" )
        "fees30dUsd": snap.get("fees30dUsd") if ok else None,  # info: "fees30dUsd" : snap . get ( "fees30dUsd" )
        "payouts30dUsd": snap.get("payouts30dUsd") if ok else None,  # info: "payouts30dUsd" : snap . get ( "payouts30dUsd" )
        "ageMs": age_ms,  # info: "ageMs" : age_ms ,
        "fetchedAt": snap.get("fetchedAt"),  # info: "fetchedAt" : snap . get ( "fetchedAt" )
        "source": snap.get("source"),  # info: "source" : snap . get ( "source" )
        "explain": expl if ok else None,  # info: "explain" : expl if ok else None ,
        "plain": plain,  # info: "plain" : plain ,
        "recent": snap.get("recent") or [],  # info: "recent" : snap . get ( "recent" )
    }  # info: }


# ====================================================
# SECTION: function desk_payload
# What it does: desk payload.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def desk_payload(snap: dict[str, Any] | None = None) -> dict[str, Any]:  # info: def desk_payload
    snap = snap if snap is not None else stripe_poll.read_snapshot()  # info: set snap
    ledger_path = pub._finance_file("ops-ledger.json")  # info: set ledger_path
    ledger = pub._read_json(ledger_path) if ledger_path else {}  # info: set ledger
    ops = _ops_from_ledger(ledger)  # info: set ops
    stripe = _stripe_block(snap)  # info: set stripe
    exp = float(ops["summary"]["expensesMonthlyUsd"] or 0)  # info: set exp
    inc30 = float(stripe.get("income30dUsd") or 0)  # info: set inc30
    rev = inc30  # info: set rev
    costs = exp  # info: set costs
    profit = round(rev - costs, 2)  # info: set profit
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "stripe": stripe,  # info: "stripe" : stripe ,
        "ops": ops,  # info: "ops" : ops ,
        "wishlists": {  # info: "wishlists" : {
            "summary": {"listCount": 0, "itemCount": 0, "wantedUsd": 0},  # info: "summary" : { "listCount" : 0 , "itemCount"
            "lists": [],  # info: "lists" : [ ] ,
        },  # info: } ,
        "review": {},  # info: "review" : { } ,
        "optimal": {  # info: "optimal" : {
            "summary": {"monthlyUsd": exp, "lineCount": ops["summary"]["expenseCount"]},  # info: "summary" : { "monthlyUsd" : exp , "lineCount"
            "deltaMonthlyUsd": 0,  # info: "deltaMonthlyUsd" : 0 ,
            "note": "Target spend is the current ledger until you set optimal lines.",  # info: "note" : "Target spend is the current ledger until you set optimal lines." ,
            "lines": ops["lines"],  # info: "lines" : ops [ "lines" ] ,
        },  # info: } ,
        "venmo": {"configured": False, "ytd": {}, "contextYtd": {}},  # info: "venmo" : { "configured" : False , "ytd"
        "pnl": {  # info: "pnl" : {
            "plain": stripe.get("plain") or "",  # info: "plain" : stripe . get ( "plain" )
            "totals": {  # info: "totals" : {
                "profitUsd": profit,  # info: "profitUsd" : profit ,
                "revenueUsd": rev,  # info: "revenueUsd" : rev ,
                "costsUsd": costs,  # info: "costsUsd" : costs ,
                "runRateMonthly": {  # info: "runRateMonthly" : {
                    "profitUsd": round((inc30 / 30.0) * 30 - exp, 2),  # info: "profitUsd" : round ( ( inc30 / 30.0
                    "costsUsd": exp,  # info: "costsUsd" : exp ,
                },  # info: } ,
            },  # info: } ,
            "stripe": {  # info: "stripe" : {
                "rr": {"incomeUsd": inc30},  # info: "rr" : { "incomeUsd" : inc30 } ,
                "availableUsd": stripe.get("usdAvailable"),  # info: "availableUsd" : stripe . get ( "usdAvailable" )
                "pendingUsd": stripe.get("usdPending"),  # info: "pendingUsd" : stripe . get ( "usdPending" )
            },  # info: } ,
        },  # info: } ,
        "updatedAt": int(time.time() * 1000),  # info: "updatedAt" : int ( time . time (
        "sources": {  # info: "sources" : {
            "ledger": str(ledger_path) if ledger_path else None,  # info: "ledger" : str ( ledger_path ) if ledger_path
            "stripe": str(stripe_poll.snapshot_path()) if stripe_poll.snapshot_path().is_file() else None,  # info: "stripe" : str ( stripe_poll . snapshot_path (
        },  # info: } ,
    }  # info: }
