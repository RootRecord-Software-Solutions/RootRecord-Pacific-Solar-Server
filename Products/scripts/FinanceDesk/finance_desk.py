"""Desk finance payload from the live ledger + Stripe snapshot."""
from __future__ import annotations

import time
from typing import Any

from apps.core.services import public_finance as pub
from apps.core.services import stripe_poll


def _ops_from_ledger(ledger: dict) -> dict[str, Any]:
    expenses, income, _ = pub._collect_lines(ledger)
    exp_mo = round(sum(float(e.get("monthlyUsd") or 0) for e in expenses), 2)
    inc_mo = round(sum(float(i.get("monthlyUsd") or 0) for i in income), 2)
    projects = []
    for p in ledger.get("projects") or []:
        if not isinstance(p, dict):
            continue
        projects.append(
            {
                "id": p.get("id"),
                "name": p.get("name") or p.get("label") or p.get("id"),
            }
        )
    lines = []
    for e in expenses:
        lines.append(
            {
                "id": e.get("id"),
                "kind": "expense",
                "label": e.get("label"),
                "amountUsd": e.get("amountUsd"),
                "monthlyUsd": e.get("monthlyUsd"),
                "period": e.get("period"),
                "category": e.get("category"),
                "project": e.get("project"),
            }
        )
    for i in income:
        lines.append(
            {
                "id": i.get("id"),
                "kind": "income",
                "label": i.get("label"),
                "amountUsd": i.get("amountUsd"),
                "monthlyUsd": i.get("monthlyUsd"),
                "period": i.get("period"),
            }
        )
    return {
        "summary": {
            "projectCount": len(projects),
            "accountCount": len(ledger.get("accounts") or []),
            "expensesMonthlyUsd": exp_mo,
            "expenseCount": len(expenses),
            "otherIncomeMonthlyUsd": inc_mo,
            "incomeCount": len(income),
            "netOtherMonthlyUsd": round(inc_mo - exp_mo, 2),
            "staleIds": [],
        },
        "expenseCategories": [
            "hosting", "domains", "cloudflare", "software", "hardware",
            "utilities", "ads", "travel", "ops", "other",
        ],
        "projects": projects,
        "accounts": ledger.get("accounts") or [],
        "lines": lines,
    }


def _stripe_block(snap: dict[str, Any]) -> dict[str, Any]:
    configured = stripe_poll.configured()
    age = stripe_poll.snapshot_age_s(snap)
    age_ms = int(age * 1000) if age is not None else None
    avail = float(snap.get("usdAvailable") or 0)
    pending = float(snap.get("usdPending") or 0)
    expl = snap.get("explain") if isinstance(snap.get("explain"), dict) else {
        "avail": avail,
        "pending": pending,
        "pendingCoversDeficit": avail < 0 and (pending + avail) >= -0.05,
        "healthyTiming": -1.0 < avail < 0 and (pending + avail) >= -0.05,
    }
    ok = bool(snap.get("ok"))
    plain = None
    if ok:
        plain = f"Stripe snapshot {int(age)}s ago." if age is not None else "Stripe snapshot on disk."
        if age is not None and age > 3600:
            plain = f"Stripe snapshot is {int(age / 3600)}h old — refresh if you need now."
    elif configured:
        plain = snap.get("detail") or snap.get("error") or "Stripe poll failed."
    else:
        plain = "Stripe key not set."
    return {
        "configured": configured,
        "ok": ok,
        "reason": None if ok else (snap.get("detail") or snap.get("error") or "not_configured"),
        "usdAvailable": avail if ok else None,
        "usdPending": pending if ok else None,
        "income30dUsd": snap.get("income30dUsd") if ok else None,
        "fees30dUsd": snap.get("fees30dUsd") if ok else None,
        "payouts30dUsd": snap.get("payouts30dUsd") if ok else None,
        "ageMs": age_ms,
        "fetchedAt": snap.get("fetchedAt"),
        "source": snap.get("source"),
        "explain": expl if ok else None,
        "plain": plain,
        "recent": snap.get("recent") or [],
    }


def desk_payload(snap: dict[str, Any] | None = None) -> dict[str, Any]:
    snap = snap if snap is not None else stripe_poll.read_snapshot()
    ledger_path = pub._finance_file("ops-ledger.json")
    ledger = pub._read_json(ledger_path) if ledger_path else {}
    ops = _ops_from_ledger(ledger)
    stripe = _stripe_block(snap)
    exp = float(ops["summary"]["expensesMonthlyUsd"] or 0)
    inc30 = float(stripe.get("income30dUsd") or 0)
    rev = inc30
    costs = exp
    profit = round(rev - costs, 2)
    return {
        "ok": True,
        "stripe": stripe,
        "ops": ops,
        "wishlists": {
            "summary": {"listCount": 0, "itemCount": 0, "wantedUsd": 0},
            "lists": [],
        },
        "review": {},
        "optimal": {
            "summary": {"monthlyUsd": exp, "lineCount": ops["summary"]["expenseCount"]},
            "deltaMonthlyUsd": 0,
            "note": "Target spend is the current ledger until you set optimal lines.",
            "lines": ops["lines"],
        },
        "venmo": {"configured": False, "ytd": {}, "contextYtd": {}},
        "pnl": {
            "plain": stripe.get("plain") or "",
            "totals": {
                "profitUsd": profit,
                "revenueUsd": rev,
                "costsUsd": costs,
                "runRateMonthly": {
                    "profitUsd": round((inc30 / 30.0) * 30 - exp, 2),
                    "costsUsd": exp,
                },
            },
            "stripe": {
                "rr": {"incomeUsd": inc30},
                "availableUsd": stripe.get("usdAvailable"),
                "pendingUsd": stripe.get("usdPending"),
            },
        },
        "updatedAt": int(time.time() * 1000),
        "sources": {
            "ledger": str(ledger_path) if ledger_path else None,
            "stripe": str(stripe_poll.snapshot_path()) if stripe_poll.snapshot_path().is_file() else None,
        },
    }
