# ==============================================================================
# FILE: Reports/AI-Usage/scripts/ai_usage.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Local AI usage ledger. Estimated token cost only. No network. No API keys."""  # info: """Local AI usage ledger. Estimated token cost only. No network. No API keys."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sqlite3  # info: import sqlite3
import threading  # info: import threading
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from pathlib import Path  # info: from pathlib import Path
from typing import Any, Optional  # info: from typing import Any , Optional

DEFAULT_DB_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DEFAULT_DB_ROOT
PRICING_PATH = Path(__file__).resolve().parent.parent / "config" / "pricing.json"  # info: set PRICING_PATH

_lock = threading.Lock()  # info: set _lock

# Fallback if pricing.json is missing (USD per 1M tokens). pricing.json is the source.
# ====================================================
# SECTION: DEFAULT_PRICING
# What it does: Set DEFAULT_PRICING.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
DEFAULT_PRICING = {  # info: set DEFAULT_PRICING
    "openai": {  # info: "openai" : {
        "gpt-4o": {"input": 2.50, "output": 10.00},  # info: "gpt-4o" : { "input" : 2.50 , "output"
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},  # info: "gpt-4o-mini" : { "input" : 0.15 , "output"
        "gpt-4.1": {"input": 2.00, "output": 8.00},  # info: "gpt-4.1" : { "input" : 2.00 , "output"
        "o3-mini": {"input": 1.10, "output": 4.40},  # info: "o3-mini" : { "input" : 1.10 , "output"
        "default": {"input": 1.00, "output": 3.00},  # info: "default" : { "input" : 1.00 , "output"
    },  # info: } ,
    "anthropic": {  # info: "anthropic" : {
        "claude-sonnet-4": {"input": 3.00, "output": 15.00},  # info: "claude-sonnet-4" : { "input" : 3.00 , "output"
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},  # info: "claude-3-5-sonnet" : { "input" : 3.00 , "output"
        "claude-3-5-haiku": {"input": 0.80, "output": 4.00},  # info: "claude-3-5-haiku" : { "input" : 0.80 , "output"
        "default": {"input": 3.00, "output": 15.00},  # info: "default" : { "input" : 3.00 , "output"
    },  # info: } ,
    "xai": {  # info: "xai" : {
        "grok-3": {"input": 3.00, "output": 15.00},  # info: "grok-3" : { "input" : 3.00 , "output"
        "grok-2": {"input": 2.00, "output": 10.00},  # info: "grok-2" : { "input" : 2.00 , "output"
        "default": {"input": 2.00, "output": 10.00},  # info: "default" : { "input" : 2.00 , "output"
    },  # info: } ,
    "google": {  # info: "google" : {
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},  # info: "gemini-2.0-flash" : { "input" : 0.10 , "output"
        "default": {"input": 0.50, "output": 1.50},  # info: "default" : { "input" : 0.50 , "output"
    },  # info: } ,
    "local": {  # info: "local" : {
        "default": {"input": 0.0, "output": 0.0},  # info: "default" : { "input" : 0.0 , "output"
    },  # info: } ,
}  # info: }


# ====================================================
# SECTION: function db_root
# What it does: db root.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def db_root() -> Path:  # info: def db_root
    return Path(os.environ.get("RR_DATABASE_ROOT", str(DEFAULT_DB_ROOT)))  # info: return Path ( os . environ . get


# ====================================================
# SECTION: function data_dir
# What it does: data dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def data_dir() -> Path:  # info: def data_dir
    return db_root() / "Reports" / "AI-Usage"  # info: return db_root ( ) / "Reports" / "AI-Usage"


# ====================================================
# SECTION: function logs_dir
# What it does: logs dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def logs_dir() -> Path:  # info: def logs_dir
    return db_root() / "Logs" / "Reports" / "AI-Usage"  # info: return db_root ( ) / "Logs" / "Reports"


# ====================================================
# SECTION: function db_path
# What it does: db path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def db_path() -> Path:  # info: def db_path
    return data_dir() / "ai_usage.db"  # info: return data_dir ( ) / "ai_usage.db"


# ====================================================
# SECTION: function _utc_now
# What it does:  utc now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _utc_now() -> str:  # info: def _utc_now
    return datetime.now(timezone.utc).isoformat()  # info: return datetime . now ( timezone . utc


# ====================================================
# SECTION: function _log
# What it does:  log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _log(line: str) -> None:  # info: def _log
    try:  # info: try :
        logs_dir().mkdir(parents=True, exist_ok=True)  # info: call logs_dir
        with (logs_dir() / "ai_usage_current.log").open("a", encoding="utf-8") as fh:  # info: with ( logs_dir ( ) / "ai_usage_current.log" )
            fh.write(line.rstrip() + "\n")  # info: fh . write ( line . rstrip (
    except OSError:  # info: except OSError :
        pass  # info: pass


# ====================================================
# SECTION: function _connect
# What it does:  connect.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _connect() -> sqlite3.Connection:  # info: def _connect
    path = db_path()  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    con = sqlite3.connect(str(path), timeout=30)  # info: set con
    con.row_factory = sqlite3.Row  # info: con . row_factory = sqlite3 . Row
    con.execute("PRAGMA journal_mode=WAL")  # info: con . execute ( "PRAGMA journal_mode=WAL" )
    return con  # info: return con


# ====================================================
# SECTION: function ensure_schema
# What it does: ensure schema.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_schema() -> None:  # info: def ensure_schema
    with _lock:  # info: with _lock :
        con = _connect()  # info: set con
        try:  # info: try :
            con.executescript(  # info: con . executescript (
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
            )  # info: )
            con.commit()  # info: con . commit ( )
        finally:  # info: finally :
            con.close()  # info: con . close ( )


# ====================================================
# SECTION: function load_pricing
# What it does: load pricing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_pricing() -> dict:  # info: def load_pricing
    if PRICING_PATH.is_file():  # info: if PRICING_PATH . is_file ( ) :
        try:  # info: try :
            return json.loads(PRICING_PATH.read_text(encoding="utf-8"))  # info: return json . loads ( PRICING_PATH . read_text
        except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
            pass  # info: pass
    return DEFAULT_PRICING  # info: return DEFAULT_PRICING


# ====================================================
# SECTION: function estimate_cost_usd
# What it does: Cost from published $/1M token rates. No provider call.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def estimate_cost_usd(  # info: def estimate_cost_usd
    provider: str,  # info: set provider
    model: str,  # info: set model
    input_tokens: int,  # info: set input_tokens
    output_tokens: int,  # info: set output_tokens
    pricing: Optional[dict] = None,  # info: set pricing
) -> float:  # info: ) -> float :
    """Cost from published $/1M token rates. No provider call."""  # info: """Cost from published $/1M token rates. No provider call."""
    pricing = pricing or load_pricing()  # info: set pricing
    p = (provider or "unknown").lower().strip()  # info: set p
    m = (model or "default").lower().strip()  # info: set m
    block = pricing.get(p) or pricing.get("default") or {}  # info: set block
    rates = block.get(m) or block.get("default") or {"input": 0.0, "output": 0.0}  # info: set rates
    inp = float(rates.get("input") or 0.0)  # info: set inp
    out = float(rates.get("output") or 0.0)  # info: set out
    return (input_tokens / 1_000_000.0) * inp + (output_tokens / 1_000_000.0) * out  # info: return ( input_tokens / 1_000_000.0 ) * inp


# ====================================================
# SECTION: function _bump_daily
# What it does:  bump daily.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _bump_daily(  # info: def _bump_daily
    con: sqlite3.Connection,  # info: set con
    day: str,  # info: set day
    account_id: str,  # info: set account_id
    provider: str,  # info: set provider
    model: str,  # info: set model
    input_tokens: int,  # info: set input_tokens
    output_tokens: int,  # info: set output_tokens
    total_tokens: int,  # info: set total_tokens
    cost_usd: float,  # info: set cost_usd
) -> None:  # info: ) -> None :
    con.execute(  # info: con . execute (
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
        (  # info: call (
            day,  # info: day ,
            account_id or "",  # info: account_id or "" ,
            provider or "",  # info: provider or "" ,
            model or "",  # info: model or "" ,
            int(input_tokens),  # info: call int
            int(output_tokens),  # info: call int
            int(total_tokens),  # info: call int
            float(cost_usd),  # info: call float
        ),  # info: ) ,
    )  # info: )


# ====================================================
# SECTION: function record_usage
# What it does: Record one metered call. Tokens and an estimated USD cost. No request text. No network.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def record_usage(  # info: def record_usage
    *,  # info: * ,
    provider: str,  # info: set provider
    model: str,  # info: set model
    input_tokens: int = 0,  # info: set input_tokens
    output_tokens: int = 0,  # info: set output_tokens
    total_tokens: Optional[int] = None,  # info: set total_tokens
    account_id: Optional[str] = None,  # info: set account_id
    source: str = "",  # info: set source
    action: str = "",  # info: set action
    request_id: str = "",  # info: set request_id
    cost_usd: Optional[float] = None,  # info: set cost_usd
    ok: bool = True,  # info: set ok
    meta: Optional[dict] = None,  # info: set meta
) -> dict[str, Any]:  # info: ) -> dict [ str , Any ]
    """Record one metered call. Tokens and an estimated USD cost. No request text. No network."""  # info: """Record one metered call. Tokens and an estimated USD cost. No request text. No network."""
    ensure_schema()  # info: call ensure_schema
    inp = max(0, int(input_tokens or 0))  # info: set inp
    out = max(0, int(output_tokens or 0))  # info: set out
    total = int(total_tokens) if total_tokens is not None else inp + out  # info: set total
    if cost_usd is None:  # info: if cost_usd is None :
        cost_usd = estimate_cost_usd(provider, model, inp, out)  # info: set cost_usd
    cost_usd = float(cost_usd or 0.0)  # info: set cost_usd
    ts = _utc_now()  # info: set ts
    day = ts[:10]  # info: set day
    prov = (provider or "unknown").lower()  # info: set prov
    with _lock:  # info: with _lock :
        con = _connect()  # info: set con
        try:  # info: try :
            cur = con.execute(  # info: set cur
                """
                INSERT INTO ai_calls (
                  ts_utc, account_id, provider, model, source, action,
                  input_tokens, output_tokens, total_tokens, cost_usd,
                  request_id, ok, meta_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (  # info: call (
                    ts,  # info: ts ,
                    account_id,  # info: account_id ,
                    prov,  # info: prov ,
                    model or "unknown",  # info: model or "unknown" ,
                    source or "",  # info: source or "" ,
                    action or "",  # info: action or "" ,
                    inp,  # info: inp ,
                    out,  # info: out ,
                    total,  # info: total ,
                    cost_usd,  # info: cost_usd ,
                    request_id or "",  # info: request_id or "" ,
                    1 if ok else 0,  # info: 1 if ok else 0 ,
                    json.dumps(meta or {}, ensure_ascii=False),  # info: json . dumps ( meta or { }
                ),  # info: ) ,
            )  # info: )
            _bump_daily(con, day, account_id or "", prov, model or "", inp, out, total, cost_usd)  # info: call _bump_daily
            con.commit()  # info: con . commit ( )
            row_id = cur.lastrowid  # info: set row_id
        finally:  # info: finally :
            con.close()  # info: con . close ( )
    _log(f"{ts} provider={prov} model={model or 'unknown'} tokens={total} cost_usd={cost_usd:.6f}")  # info: call _log
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "id": row_id,  # info: "id" : row_id ,
        "ts_utc": ts,  # info: "ts_utc" : ts ,
        "account_id": account_id,  # info: "account_id" : account_id ,
        "provider": prov,  # info: "provider" : prov ,
        "model": model,  # info: "model" : model ,
        "input_tokens": inp,  # info: "input_tokens" : inp ,
        "output_tokens": out,  # info: "output_tokens" : out ,
        "total_tokens": total,  # info: "total_tokens" : total ,
        "cost_usd": round(cost_usd, 8),  # info: "cost_usd" : round ( cost_usd , 8 )
    }  # info: }


# ====================================================
# SECTION: function summary
# What it does: Totals, per-account share of cost, per-provider breakdown.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def summary(days: int = 30, account_id: Optional[str] = None) -> dict[str, Any]:  # info: def summary
    """Totals, per-account share of cost, per-provider breakdown."""  # info: """Totals, per-account share of cost, per-provider breakdown."""
    ensure_schema()  # info: call ensure_schema
    since = (datetime.now(timezone.utc) - timedelta(days=max(1, days))).strftime("%Y-%m-%d")  # info: set since
    con = _connect()  # info: set con
    try:  # info: try :
        params: list[Any] = [since]  # info: set params
        where = "day >= ?"  # info: set where
        if account_id:  # info: if account_id :
            where += " AND account_id = ?"  # info: set where
            params.append(account_id)  # info: params . append ( account_id )
        rows = con.execute(  # info: set rows
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
            params,  # info: params ,
        ).fetchall()  # info: ) . fetchall ( )

        by_account: dict[str, dict] = {}  # info: set by_account
        by_provider: dict[str, dict] = {}  # info: set by_provider
        total_cost = 0.0  # info: set total_cost
        total_tokens = 0  # info: set total_tokens
        total_calls = 0  # info: set total_calls
        detail = []  # info: set detail
        for r in rows:  # info: for r in rows :
            cost = float(r["cost_usd"] or 0)  # info: set cost
            toks = int(r["total_tokens"] or 0)  # info: set toks
            calls = int(r["calls"] or 0)  # info: set calls
            total_cost += cost  # info: set total_cost
            total_tokens += toks  # info: set total_tokens
            total_calls += calls  # info: set total_calls
            aid = r["account_id"] or "(unattributed)"  # info: set aid
            prov = r["provider"] or "unknown"  # info: set prov
            acc = by_account.setdefault(aid, {"account_id": aid, "calls": 0, "total_tokens": 0, "cost_usd": 0.0})  # info: set acc
            acc["calls"] += calls  # info: acc [ "calls" ] += calls
            acc["total_tokens"] += toks  # info: acc [ "total_tokens" ] += toks
            acc["cost_usd"] += cost  # info: acc [ "cost_usd" ] += cost
            bp = by_provider.setdefault(prov, {"provider": prov, "calls": 0, "total_tokens": 0, "cost_usd": 0.0})  # info: set bp
            bp["calls"] += calls  # info: bp [ "calls" ] += calls
            bp["total_tokens"] += toks  # info: bp [ "total_tokens" ] += toks
            bp["cost_usd"] += cost  # info: bp [ "cost_usd" ] += cost
            detail.append(  # info: detail . append (
                {  # info: {
                    "account_id": aid,  # info: "account_id" : aid ,
                    "provider": prov,  # info: "provider" : prov ,
                    "model": r["model"],  # info: "model" : r [ "model" ] ,
                    "calls": calls,  # info: "calls" : calls ,
                    "input_tokens": int(r["input_tokens"] or 0),  # info: "input_tokens" : int ( r [ "input_tokens" ]
                    "output_tokens": int(r["output_tokens"] or 0),  # info: "output_tokens" : int ( r [ "output_tokens" ]
                    "total_tokens": toks,  # info: "total_tokens" : toks ,
                    "cost_usd": round(cost, 6),  # info: "cost_usd" : round ( cost , 6 )
                }  # info: }
            )  # info: )

        accounts = []  # info: set accounts
        for acc in sorted(by_account.values(), key=lambda x: -x["cost_usd"]):  # info: for acc in sorted ( by_account . values
            share = (acc["cost_usd"] / total_cost * 100.0) if total_cost > 0 else 0.0  # info: set share
            accounts.append(  # info: accounts . append (
                {  # info: {
                    **acc,  # info: ** acc ,
                    "cost_usd": round(acc["cost_usd"], 6),  # info: "cost_usd" : round ( acc [ "cost_usd" ]
                    "cost_share_pct": round(share, 2),  # info: "cost_share_pct" : round ( share , 2 )
                    "token_share_pct": round(  # info: "token_share_pct" : round (
                        (acc["total_tokens"] / total_tokens * 100.0) if total_tokens else 0.0, 2  # info: call (
                    ),  # info: ) ,
                }  # info: }
            )  # info: )
        providers = [  # info: set providers
            {  # info: {
                **p,  # info: ** p ,
                "cost_usd": round(p["cost_usd"], 6),  # info: "cost_usd" : round ( p [ "cost_usd" ]
                "cost_share_pct": round((p["cost_usd"] / total_cost * 100.0) if total_cost else 0.0, 2),  # info: "cost_share_pct" : round ( ( p [ "cost_usd"
            }  # info: }
            for p in sorted(by_provider.values(), key=lambda x: -x["cost_usd"])  # info: for p in sorted ( by_provider . values
        ]  # info: ]
        return {  # info: return {
            "ok": True,  # info: "ok" : True ,
            "days": days,  # info: "days" : days ,
            "since": since,  # info: "since" : since ,
            "totals": {  # info: "totals" : {
                "calls": total_calls,  # info: "calls" : total_calls ,
                "total_tokens": total_tokens,  # info: "total_tokens" : total_tokens ,
                "cost_usd": round(total_cost, 6),  # info: "cost_usd" : round ( total_cost , 6 )
            },  # info: } ,
            "accounts": accounts,  # info: "accounts" : accounts ,
            "providers": providers,  # info: "providers" : providers ,
            "detail": detail,  # info: "detail" : detail ,
        }  # info: }
    finally:  # info: finally :
        con.close()  # info: con . close ( )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    import argparse  # info: import argparse

    ap = argparse.ArgumentParser(description="Local AI usage ledger (no network)")  # info: set ap
    sub = ap.add_subparsers(dest="command", required=True)  # info: set sub
    sub.add_parser("schema")  # info: sub . add_parser ( "schema" )
    sm = sub.add_parser("summary")  # info: set sm
    sm.add_argument("--days", type=int, default=30)  # info: sm . add_argument ( "--days" , type =
    sm.add_argument("--account", default=None)  # info: sm . add_argument ( "--account" , default =
    rec = sub.add_parser("record")  # info: set rec
    rec.add_argument("--provider", required=True)  # info: rec . add_argument ( "--provider" , required =
    rec.add_argument("--model", required=True)  # info: rec . add_argument ( "--model" , required =
    rec.add_argument("--input-tokens", type=int, default=0)  # info: rec . add_argument ( "--input-tokens" , type =
    rec.add_argument("--output-tokens", type=int, default=0)  # info: rec . add_argument ( "--output-tokens" , type =
    rec.add_argument("--account", default=None)  # info: rec . add_argument ( "--account" , default =
    rec.add_argument("--source", default="")  # info: rec . add_argument ( "--source" , default =
    rec.add_argument("--action", default="")  # info: rec . add_argument ( "--action" , default =
    args = ap.parse_args()  # info: set args
    if args.command == "schema":  # info: if args . command == "schema" :
        ensure_schema()  # info: call ensure_schema
        print(json.dumps({"ok": True, "db": str(db_path())}, indent=2))  # info: call print
    elif args.command == "record":  # info: elif args . command == "record" :
        print(  # info: call print
            json.dumps(  # info: json . dumps (
                record_usage(  # info: call record_usage
                    provider=args.provider,  # info: set provider
                    model=args.model,  # info: set model
                    input_tokens=args.input_tokens,  # info: set input_tokens
                    output_tokens=args.output_tokens,  # info: set output_tokens
                    account_id=args.account,  # info: set account_id
                    source=args.source,  # info: set source
                    action=args.action,  # info: set action
                ),  # info: ) ,
                indent=2,  # info: set indent
            )  # info: )
        )  # info: )
    else:  # info: else :
        print(json.dumps(summary(days=args.days, account_id=args.account), indent=2))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
