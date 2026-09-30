#!/usr/bin/env python3
"""Refresh the Stripe balance snapshot. Stdlib only. Never prints the secret.

  python3 stripe_poll.py

With no key, writes ok=false detail=not_configured and exits 0.
On a failed live poll, keeps the previous ok snapshot and does not replace it.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.envload import stripe_secret  # noqa: E402

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
SNAPSHOT = DATABASE / "Website" / "stripe-snapshot.json"
STRIPE_API = "https://api.stripe.com/v1"
FRESH_S = 25 * 60
TIMEOUT_S = 25


def _usd(cents: Any) -> float:
    try:
        return round(int(cents) / 100.0, 2)
    except (TypeError, ValueError):
        return 0.0


def read_snapshot() -> dict[str, Any]:
    if not SNAPSHOT.is_file():
        return {}
    try:
        raw = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def snapshot_age_s(snap: dict[str, Any]) -> float | None:
    try:
        v = float(snap.get("fetchedAt"))
    except (TypeError, ValueError):
        return None
    if v > 10_000_000_000:
        v = v / 1000.0
    if v <= 0:
        return None
    return time.time() - v


def _write(snap: dict[str, Any]) -> None:
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    tmp = SNAPSHOT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    tmp.replace(SNAPSHOT)


def _get(path: str, params: dict[str, str], secret: str) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    url = STRIPE_API + path + ("?" + query if query else "")
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + secret,
            "Stripe-Version": "2024-06-20",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"stripe {path} {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"stripe {path} failed") from None
    if not isinstance(body, dict):
        raise RuntimeError(f"stripe {path} bad body")
    return body


def _explain(avail: float, pending: float) -> dict[str, Any]:
    covers = pending + avail >= -0.05
    healthy = -1.0 < avail < 0 and covers
    return {
        "avail": avail,
        "pending": pending,
        "pendingCoversDeficit": bool(avail < 0 and covers),
        "healthyTiming": bool(healthy),
    }


def _live(secret: str) -> dict[str, Any]:
    since = str(int(time.time()) - 30 * 24 * 3600)
    bal = _get("/balance", {}, secret)
    tx = _get("/balance_transactions", {"limit": "100", "created[gte]": since}, secret)
    pays = _get("/payouts", {"limit": "100", "created[gte]": since, "status": "paid"}, secret)
    available = [
        {"currency": r.get("currency"), "amount": _usd(r.get("amount"))}
        for r in (bal.get("available") or [])
        if isinstance(r, dict)
    ]
    pending = [
        {"currency": r.get("currency"), "amount": _usd(r.get("amount"))}
        for r in (bal.get("pending") or [])
        if isinstance(r, dict)
    ]
    usd_avail = round(sum(float(r.get("amount") or 0) for r in available if r.get("currency") == "usd"), 2)
    usd_pend = round(sum(float(r.get("amount") or 0) for r in pending if r.get("currency") == "usd"), 2)
    income = 0.0
    fees = 0.0
    recent: list[dict[str, Any]] = []
    for row in tx.get("data") or []:
        if not isinstance(row, dict) or str(row.get("currency") or "").lower() != "usd":
            continue
        amt = _usd(row.get("amount"))
        fee = _usd(row.get("fee"))
        kind = str(row.get("type") or "other")
        if amt > 0:
            income += amt
        fees += abs(fee)
        created = row.get("created")
        created_iso: Any = created
        if isinstance(created, (int, float)):
            created_iso = datetime.fromtimestamp(int(created), tz=timezone.utc).isoformat()
        recent.append({
            "id": row.get("id"),
            "type": kind,
            "amount": amt,
            "fee": fee,
            "net": _usd(row.get("net")),
            "description": row.get("description") or kind,
            "created": created_iso,
            "currency": "usd",
        })
        if len(recent) >= 40:
            break
    payouts = 0.0
    for row in pays.get("data") or []:
        if isinstance(row, dict) and str(row.get("currency") or "").lower() == "usd":
            payouts += _usd(row.get("amount"))
    return {
        "ok": True,
        "source": "stripe_balance_api",
        "fetchedAt": int(time.time() * 1000),
        "available": available,
        "pending": pending,
        "usdAvailable": usd_avail,
        "usdPending": usd_pend,
        "income30dUsd": round(income, 2),
        "fees30dUsd": round(fees, 2),
        "payouts30dUsd": round(payouts, 2),
        "recent": recent,
        "explain": _explain(usd_avail, usd_pend),
    }


def poll(*, force: bool = False) -> dict[str, Any]:
    existing = read_snapshot()
    age = snapshot_age_s(existing)
    if existing.get("ok") and age is not None and age < FRESH_S and not force:
        return existing
    secret = stripe_secret()
    if not secret.startswith("sk_"):
        out = {
            "ok": False,
            "source": "stripe_balance_api",
            "fetchedAt": int(time.time() * 1000),
            "detail": "not_configured",
        }
        _write(out)
        return out
    try:
        snap = _live(secret)
    except RuntimeError as exc:
        if existing.get("ok"):
            existing["stale"] = True
            existing["pollError"] = str(exc)[:180]
            return existing
        out = {
            "ok": False,
            "source": "stripe_balance_api",
            "fetchedAt": int(time.time() * 1000),
            "detail": "poll_failed",
            "error": str(exc)[:180],
        }
        _write(out)
        return out
    _write(snap)
    return snap


def main() -> int:
    snap = poll(force=False)
    detail = "ok" if snap.get("ok") else snap.get("detail") or "fail"
    print(f"stripe {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
