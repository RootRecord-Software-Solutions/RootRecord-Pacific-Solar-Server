#!/usr/bin/env python3
"""Local AI usage ledger. Estimated token cost only. No network. No API keys."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

DEFAULT_DB_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
PRICING_PATH = Path(__file__).resolve().parent.parent / "config" / "pricing.json"

_lock = threading.Lock()

# Fallback if pricing.json is missing (USD per 1M tokens). pricing.json is the source.
DEFAULT_PRICING = {
    "openai": {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4.1": {"input": 2.00, "output": 8.00},
        "o3-mini": {"input": 1.10, "output": 4.40},
        "default": {"input": 1.00, "output": 3.00},
    },
    "anthropic": {
        "claude-sonnet-4": {"input": 3.00, "output": 15.00},
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
        "default": {"input": 3.00, "output": 15.00},
    },
    "xai": {
        "grok-3": {"input": 3.00, "output": 15.00},
        "grok-2": {"input": 2.00, "output": 10.00},
        "default": {"input": 2.00, "output": 10.00},
    },
    "google": {
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "default": {"input": 0.50, "output": 1.50},
    },
    "local": {
        "default": {"input": 0.0, "output": 0.0},
    },
}


def db_root() -> Path:
    return Path(os.environ.get("RR_DATABASE_ROOT", str(DEFAULT_DB_ROOT)))


def data_dir() -> Path:
    return db_root() / "Reports" / "AI-Usage"


def logs_dir() -> Path:
    return db_root() / "Logs" / "Reports" / "AI-Usage"


def db_path() -> Path:
    return data_dir() / "ai_usage.db"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(line: str) -> None:
    try:
        logs_dir().mkdir(parents=True, exist_ok=True)
        with (logs_dir() / "ai_usage_current.log").open("a", encoding="utf-8") as fh:
            fh.write(line.rstrip() + "\n")
    except OSError:
        pass


def _connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def ensure_schema() -> None:
    with _lock:
        con = _connect()
        try:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS ai_calls (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts_utc TEXT NOT NULL,
                  account_id TEXT,
                  provider TEXT NOT NULL,
                  model TEXT NOT NULL,
                  source TEXT,
                  action TEXT,
                  input_tokens INTEGER NOT NULL DEFAULT 0,
                  output_tokens INTEGER NOT NULL DEFAULT 0,
                  total_tokens INTEGER NOT NULL DEFAULT 0,
                  cost_usd REAL NOT NULL DEFAULT 0,
                  request_id TEXT,
                  ok INTEGER NOT NULL DEFAULT 1,
                  meta_json TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_ai_calls_ts ON ai_calls(ts_utc);
                CREATE INDEX IF NOT EXISTS idx_ai_calls_account ON ai_calls(account_id);
                CREATE INDEX IF NOT EXISTS idx_ai_calls_provider ON ai_calls(provider, model);

                CREATE TABLE IF NOT EXISTS ai_daily (
                  day TEXT NOT NULL,
                  account_id TEXT NOT NULL DEFAULT '',
                  provider TEXT NOT NULL DEFAULT '',
                  model TEXT NOT NULL DEFAULT '',
                  calls INTEGER NOT NULL DEFAULT 0,
                  input_tokens INTEGER NOT NULL DEFAULT 0,
                  output_tokens INTEGER NOT NULL DEFAULT 0,
                  total_tokens INTEGER NOT NULL DEFAULT 0,
                  cost_usd REAL NOT NULL DEFAULT 0,
                  PRIMARY KEY (day, account_id, provider, model)
                );
                """
            )
            con.commit()
        finally:
            con.close()


def load_pricing() -> dict:
    if PRICING_PATH.is_file():
        try:
            return json.loads(PRICING_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return DEFAULT_PRICING


def estimate_cost_usd(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    pricing: Optional[dict] = None,
) -> float:
    """Cost from published $/1M token rates. No provider call."""
    pricing = pricing or load_pricing()
    p = (provider or "unknown").lower().strip()
    m = (model or "default").lower().strip()
    block = pricing.get(p) or pricing.get("default") or {}
    rates = block.get(m) or block.get("default") or {"input": 0.0, "output": 0.0}
    inp = float(rates.get("input") or 0.0)
    out = float(rates.get("output") or 0.0)
    return (input_tokens / 1_000_000.0) * inp + (output_tokens / 1_000_000.0) * out


def _bump_daily(
    con: sqlite3.Connection,
    day: str,
    account_id: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    cost_usd: float,
) -> None:
    con.execute(
        """
        INSERT INTO ai_daily (day, account_id, provider, model, calls, input_tokens, output_tokens, total_tokens, cost_usd)
        VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)
        ON CONFLICT(day, account_id, provider, model) DO UPDATE SET
          calls = calls + 1,
          input_tokens = input_tokens + excluded.input_tokens,
          output_tokens = output_tokens + excluded.output_tokens,
          total_tokens = total_tokens + excluded.total_tokens,
          cost_usd = cost_usd + excluded.cost_usd
        """,
        (
            day,
            account_id or "",
            provider or "",
            model or "",
            int(input_tokens),
            int(output_tokens),
            int(total_tokens),
            float(cost_usd),
        ),
    )


def record_usage(
    *,
    provider: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_tokens: Optional[int] = None,
    account_id: Optional[str] = None,
    source: str = "",
    action: str = "",
    request_id: str = "",
    cost_usd: Optional[float] = None,
    ok: bool = True,
    meta: Optional[dict] = None,
) -> dict[str, Any]:
    """Record one metered call. Tokens and an estimated USD cost. No request text. No network."""
    ensure_schema()
    inp = max(0, int(input_tokens or 0))
    out = max(0, int(output_tokens or 0))
    total = int(total_tokens) if total_tokens is not None else inp + out
    if cost_usd is None:
        cost_usd = estimate_cost_usd(provider, model, inp, out)
    cost_usd = float(cost_usd or 0.0)
    ts = _utc_now()
    day = ts[:10]
    prov = (provider or "unknown").lower()
    with _lock:
        con = _connect()
        try:
            cur = con.execute(
                """
                INSERT INTO ai_calls (
                  ts_utc, account_id, provider, model, source, action,
                  input_tokens, output_tokens, total_tokens, cost_usd,
                  request_id, ok, meta_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    account_id,
                    prov,
                    model or "unknown",
                    source or "",
                    action or "",
                    inp,
                    out,
                    total,
                    cost_usd,
                    request_id or "",
                    1 if ok else 0,
                    json.dumps(meta or {}, ensure_ascii=False),
                ),
            )
            _bump_daily(con, day, account_id or "", prov, model or "", inp, out, total, cost_usd)
            con.commit()
            row_id = cur.lastrowid
        finally:
            con.close()
    _log(f"{ts} provider={prov} model={model or 'unknown'} tokens={total} cost_usd={cost_usd:.6f}")
    return {
        "ok": True,
        "id": row_id,
        "ts_utc": ts,
        "account_id": account_id,
        "provider": prov,
        "model": model,
        "input_tokens": inp,
        "output_tokens": out,
        "total_tokens": total,
        "cost_usd": round(cost_usd, 8),
    }


def summary(days: int = 30, account_id: Optional[str] = None) -> dict[str, Any]:
    """Totals, per-account share of cost, per-provider breakdown."""
    ensure_schema()
    since = (datetime.now(timezone.utc) - timedelta(days=max(1, days))).strftime("%Y-%m-%d")
    con = _connect()
    try:
        params: list[Any] = [since]
        where = "day >= ?"
        if account_id:
            where += " AND account_id = ?"
            params.append(account_id)
        rows = con.execute(
            f"""
            SELECT account_id, provider, model,
                   SUM(calls) AS calls,
                   SUM(input_tokens) AS input_tokens,
                   SUM(output_tokens) AS output_tokens,
                   SUM(total_tokens) AS total_tokens,
                   SUM(cost_usd) AS cost_usd
            FROM ai_daily
            WHERE {where}
            GROUP BY account_id, provider, model
            ORDER BY cost_usd DESC
            """,
            params,
        ).fetchall()

        by_account: dict[str, dict] = {}
        by_provider: dict[str, dict] = {}
        total_cost = 0.0
        total_tokens = 0
        total_calls = 0
        detail = []
        for r in rows:
            cost = float(r["cost_usd"] or 0)
            toks = int(r["total_tokens"] or 0)
            calls = int(r["calls"] or 0)
            total_cost += cost
            total_tokens += toks
            total_calls += calls
            aid = r["account_id"] or "(unattributed)"
            prov = r["provider"] or "unknown"
            acc = by_account.setdefault(aid, {"account_id": aid, "calls": 0, "total_tokens": 0, "cost_usd": 0.0})
            acc["calls"] += calls
            acc["total_tokens"] += toks
            acc["cost_usd"] += cost
            bp = by_provider.setdefault(prov, {"provider": prov, "calls": 0, "total_tokens": 0, "cost_usd": 0.0})
            bp["calls"] += calls
            bp["total_tokens"] += toks
            bp["cost_usd"] += cost
            detail.append(
                {
                    "account_id": aid,
                    "provider": prov,
                    "model": r["model"],
                    "calls": calls,
                    "input_tokens": int(r["input_tokens"] or 0),
                    "output_tokens": int(r["output_tokens"] or 0),
                    "total_tokens": toks,
                    "cost_usd": round(cost, 6),
                }
            )

        accounts = []
        for acc in sorted(by_account.values(), key=lambda x: -x["cost_usd"]):
            share = (acc["cost_usd"] / total_cost * 100.0) if total_cost > 0 else 0.0
            accounts.append(
                {
                    **acc,
                    "cost_usd": round(acc["cost_usd"], 6),
                    "cost_share_pct": round(share, 2),
                    "token_share_pct": round(
                        (acc["total_tokens"] / total_tokens * 100.0) if total_tokens else 0.0, 2
                    ),
                }
            )
        providers = [
            {
                **p,
                "cost_usd": round(p["cost_usd"], 6),
                "cost_share_pct": round((p["cost_usd"] / total_cost * 100.0) if total_cost else 0.0, 2),
            }
            for p in sorted(by_provider.values(), key=lambda x: -x["cost_usd"])
        ]
        return {
            "ok": True,
            "days": days,
            "since": since,
            "totals": {
                "calls": total_calls,
                "total_tokens": total_tokens,
                "cost_usd": round(total_cost, 6),
            },
            "accounts": accounts,
            "providers": providers,
            "detail": detail,
        }
    finally:
        con.close()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Local AI usage ledger (no network)")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("schema")
    sm = sub.add_parser("summary")
    sm.add_argument("--days", type=int, default=30)
    sm.add_argument("--account", default=None)
    rec = sub.add_parser("record")
    rec.add_argument("--provider", required=True)
    rec.add_argument("--model", required=True)
    rec.add_argument("--input-tokens", type=int, default=0)
    rec.add_argument("--output-tokens", type=int, default=0)
    rec.add_argument("--account", default=None)
    rec.add_argument("--source", default="")
    rec.add_argument("--action", default="")
    args = ap.parse_args()
    if args.command == "schema":
        ensure_schema()
        print(json.dumps({"ok": True, "db": str(db_path())}, indent=2))
    elif args.command == "record":
        print(
            json.dumps(
                record_usage(
                    provider=args.provider,
                    model=args.model,
                    input_tokens=args.input_tokens,
                    output_tokens=args.output_tokens,
                    account_id=args.account,
                    source=args.source,
                    action=args.action,
                ),
                indent=2,
            )
        )
    else:
        print(json.dumps(summary(days=args.days, account_id=args.account), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
