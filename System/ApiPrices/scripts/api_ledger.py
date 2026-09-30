# ==============================================================================
# FILE: System/ApiPrices/scripts/api_ledger.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Public API price catalog. Package ApiPrices.

Spend stays off. Public-doc GET and the xAI billing probe run only when
RR_API_PRICES=1. This module does not call chat, TTS, or Cursor.
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import re  # info: import re
import sqlite3  # info: import sqlite3
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

import envload  # info: import envload

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
LIVE_DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set LIVE_DB
STATS = {"http_attempts": 0, "spend_attempts": 0}  # info: set STATS

DEFAULT_XAI_MODEL = "grok-4.6"  # info: set DEFAULT_XAI_MODEL
DEFAULT_CURSOR_MODEL = "composer-2.5"  # info: set DEFAULT_CURSOR_MODEL

# Operator notes from 2026-09-03. Not live meters.
CURSOR_SEED_USED_PCT = 73  # info: set CURSOR_SEED_USED_PCT
XAI_SEED_USD = 5.00  # info: set XAI_SEED_USD
REPORT_AUDIO_CLIP_USD = 0.10  # info: set REPORT_AUDIO_CLIP_USD
REPORT_AUDIO_CLIP_ACTUAL_USD = 0.07  # info: set REPORT_AUDIO_CLIP_ACTUAL_USD

# ====================================================
# SECTION: SOURCES
# What it does: Set SOURCES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
SOURCES = (  # info: set SOURCES
    {"vendor": "cursor", "url": "https://cursor.com/docs/models.md", "alt": "https://cursor.com/docs/models"},  # info: { "vendor" : "cursor" , "url" : "https://cursor.com/docs/models.md"
    {"vendor": "xai", "url": "https://docs.x.ai/docs/models.md", "alt": "https://docs.x.ai/docs/models"},  # info: { "vendor" : "xai" , "url" : "https://docs.x.ai/docs/models.md"
    {"vendor": "openai", "url": "https://developers.openai.com/api/docs/pricing.md", "alt": "https://openai.com/api/pricing/"},  # info: { "vendor" : "openai" , "url" : "https://developers.openai.com/api/docs/pricing.md"
    {"vendor": "gemini", "url": "https://ai.google.dev/gemini-api/docs/pricing.md", "alt": "https://ai.google.dev/gemini-api/docs/pricing"},  # info: { "vendor" : "gemini" , "url" : "https://ai.google.dev/gemini-api/docs/pricing.md"
)  # info: )

# USD per million tokens unless unit says otherwise. Captured 2026-09-03.
# ====================================================
# SECTION: SEED_ROWS
# What it does: Set SEED_ROWS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
SEED_ROWS: tuple[dict[str, Any], ...] = (  # info: set SEED_ROWS
    {"vendor": "cursor", "model": "grok-4.6", "input": 2.0, "cached": 0.5, "output": 6.0, "notes": "Cursor Models pool; Auto list price when routed here"},  # info: { "vendor" : "cursor" , "model" : "grok-4.6"
    {"vendor": "cursor", "model": "grok-4.6-fast", "input": 4.0, "cached": 1.0, "output": 12.0, "notes": "Cursor Models pool"},  # info: { "vendor" : "cursor" , "model" : "grok-4.6-fast"
    {"vendor": "cursor", "model": "grok-4.5", "input": 2.0, "cached": 0.5, "output": 6.0, "notes": "Cursor Models pool"},  # info: { "vendor" : "cursor" , "model" : "grok-4.5"
    {"vendor": "cursor", "model": "composer-2.5", "input": 0.5, "cached": 0.2, "output": 2.5, "notes": "Cursor Models pool; cheapest first-party"},  # info: { "vendor" : "cursor" , "model" : "composer-2.5"
    {"vendor": "cursor", "model": "composer-2.5-fast", "input": 3.0, "cached": 0.5, "output": 15.0, "notes": "Cursor Models pool"},  # info: { "vendor" : "cursor" , "model" : "composer-2.5-fast"
    {"vendor": "cursor", "model": "token-rate-third-party", "input": 0.25, "cached": 0.25, "output": 0.25, "notes": "Teams/Enterprise add-on per million tokens on third-party; first-party exempt"},  # info: { "vendor" : "cursor" , "model" : "token-rate-third-party"
    {"vendor": "cursor", "model": "auto", "input": None, "cached": None, "output": None, "notes": "Bills at the routed model list price"},  # info: { "vendor" : "cursor" , "model" : "auto"
    {"vendor": "xai", "model": "grok-4.6", "input": 2.0, "cached": 0.5, "output": 6.0, "notes": "<200k prompt; >=200k doubles all three"},  # info: { "vendor" : "xai" , "model" : "grok-4.6"
    {"vendor": "xai", "model": "grok-4.6-long", "input": 4.0, "cached": 1.0, "output": 12.0, "notes": "whole request once prompt >=200k"},  # info: { "vendor" : "xai" , "model" : "grok-4.6-long"
    {"vendor": "xai", "model": "grok-4.5", "input": 2.0, "cached": 0.3, "output": 6.0, "notes": "<200k prompt"},  # info: { "vendor" : "xai" , "model" : "grok-4.5"
    {"vendor": "xai", "model": "grok-4.3", "input": 1.25, "cached": 0.2, "output": 2.5, "notes": "<200k prompt"},  # info: { "vendor" : "xai" , "model" : "grok-4.3"
    {"vendor": "xai", "model": "grok-imagine-image-2.0", "input": None, "cached": None, "output": 0.04, "unit": "image", "notes": "from $0.04 / image"},  # info: { "vendor" : "xai" , "model" : "grok-imagine-image-2.0"
    {"vendor": "xai", "model": "grok-voice-tts", "input": None, "cached": None, "output": 15.0, "unit": "1M chars", "notes": "Text to Speech; report clip meter is $0.10"},  # info: { "vendor" : "xai" , "model" : "grok-voice-tts"
    {"vendor": "openai", "model": "gpt-5.6-sol", "input": 4.0, "cached": 0.4, "output": 20.0, "notes": "short context"},  # info: { "vendor" : "openai" , "model" : "gpt-5.6-sol"
    {"vendor": "openai", "model": "gpt-5.6-terra", "input": 2.0, "cached": 0.2, "output": 12.0, "notes": "short context"},  # info: { "vendor" : "openai" , "model" : "gpt-5.6-terra"
    {"vendor": "openai", "model": "gpt-5.6-luna", "input": 0.2, "cached": 0.02, "output": 1.2, "notes": "short context"},  # info: { "vendor" : "openai" , "model" : "gpt-5.6-luna"
    {"vendor": "openai", "model": "gpt-6-astra", "input": 10.0, "cached": 1.0, "output": 50.0, "notes": "Trusted Access; short context"},  # info: { "vendor" : "openai" , "model" : "gpt-6-astra"
    {"vendor": "openai", "model": "gpt-5.3-codex", "input": 1.75, "cached": 0.175, "output": 14.0, "notes": "Codex"},  # info: { "vendor" : "openai" , "model" : "gpt-5.3-codex"
    {"vendor": "gemini", "model": "gemini-3.6-flash", "input": 1.5, "cached": 0.15, "output": 7.5, "notes": "Google paid standard"},  # info: { "vendor" : "gemini" , "model" : "gemini-3.6-flash"
    {"vendor": "gemini", "model": "gemini-3.1-pro", "input": 2.0, "cached": 0.2, "output": 12.0, "notes": "<=200k; >200k input $4 / output $18"},  # info: { "vendor" : "gemini" , "model" : "gemini-3.1-pro"
    {"vendor": "gemini", "model": "gemini-2.5-flash-lite", "input": 0.1, "cached": 0.01, "output": 0.4, "notes": "cheapest Gemini paid text"},  # info: { "vendor" : "gemini" , "model" : "gemini-2.5-flash-lite"
    {"vendor": "gemini", "model": "gemini-2.5-pro", "input": 1.25, "cached": 0.125, "output": 10.0, "notes": "<=200k; >200k input $2.50 / output $15"},  # info: { "vendor" : "gemini" , "model" : "gemini-2.5-pro"
    {"vendor": "gemini", "model": "gemini-3.8-flash", "input": 0.75, "cached": 0.075, "output": 3.5, "notes": "as billed inside Cursor Other Models"},  # info: { "vendor" : "gemini" , "model" : "gemini-3.8-flash"
    {"vendor": "anthropic", "model": "claude-sonnet-5", "input": 2.0, "cached": 0.2, "output": 10.0, "notes": "Cursor Other Models list"},  # info: { "vendor" : "anthropic" , "model" : "claude-sonnet-5"
    {"vendor": "anthropic", "model": "claude-opus-5", "input": 5.0, "cached": 0.5, "output": 25.0, "notes": "Cursor Other Models list"},  # info: { "vendor" : "anthropic" , "model" : "claude-opus-5"
)  # info: )

_DEFAULT_ACCOUNT = {"spend_allowed": False, "starting_usd": None, "used_pct": None, "note": ""}  # info: set _DEFAULT_ACCOUNT
_MONEY = re.compile(r"\$([0-9]+(?:\.[0-9]+)?)")  # info: set _MONEY
_UA = "RootRecord-ava-ledger/1.0 (price catalog; no inference)"  # info: set _UA


# ====================================================
# SECTION: function prices_gate_open
# What it does: prices gate open.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def prices_gate_open() -> bool:  # info: def prices_gate_open
    return os.environ.get("RR_API_PRICES", "0") == "1"  # info: return os . environ . get ( "RR_API_PRICES"


# ====================================================
# SECTION: function spend_gate_open
# What it does: spend gate open.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def spend_gate_open() -> bool:  # info: def spend_gate_open
    return os.environ.get("RR_API_SPEND", "0") == "1"  # info: return os . environ . get ( "RR_API_SPEND"


# ====================================================
# SECTION: function note_http
# What it does: note http.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def note_http() -> None:  # info: def note_http
    STATS["http_attempts"] += 1  # info: STATS [ "http_attempts" ] += 1


# ====================================================
# SECTION: function note_spend
# What it does: note spend.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def note_spend() -> None:  # info: def note_spend
    STATS["spend_attempts"] += 1  # info: STATS [ "spend_attempts" ] += 1


# ====================================================
# SECTION: function data_dir
# What it does: data dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def data_dir() -> Path:  # info: def data_dir
    root = Path(os.environ.get("RR_DATABASE_ROOT", str(LIVE_DB)))  # info: set root
    return root / "System" / "ApiPrices"  # info: return root / "System" / "ApiPrices"


# ====================================================
# SECTION: function log_dir
# What it does: log dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_dir() -> Path:  # info: def log_dir
    root = Path(os.environ.get("RR_DATABASE_ROOT", str(LIVE_DB)))  # info: set root
    return root / "Logs" / "System" / "ApiPrices"  # info: return root / "Logs" / "System" / "ApiPrices"


# ====================================================
# SECTION: function _state_path
# What it does:  state path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _state_path() -> Path:  # info: def _state_path
    return data_dir() / "api-ledger.json"  # info: return data_dir ( ) / "api-ledger.json"


# ====================================================
# SECTION: function _last_path
# What it does:  last path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _last_path() -> Path:  # info: def _last_path
    return data_dir() / "api-ledger-last.json"  # info: return data_dir ( ) / "api-ledger-last.json"


# ====================================================
# SECTION: function _db_path
# What it does:  db path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _db_path() -> Path:  # info: def _db_path
    return data_dir() / "api-ledger.sqlite"  # info: return data_dir ( ) / "api-ledger.sqlite"


# ====================================================
# SECTION: function _now
# What it does:  now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now() -> str:  # info: def _now
    return datetime.now(timezone.utc).isoformat()  # info: return datetime . now ( timezone . utc


# ====================================================
# SECTION: function _empty_accounts
# What it does:  empty accounts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _empty_accounts() -> dict[str, dict]:  # info: def _empty_accounts
    return {  # info: return {
        "cursor": {  # info: "cursor" : {
            **_DEFAULT_ACCOUNT,  # info: ** _DEFAULT_ACCOUNT ,
            "kind": "percent_pool",  # info: "kind" : "percent_pool" ,
            "label": "Cursor",  # info: "label" : "Cursor" ,
            "used_pct": CURSOR_SEED_USED_PCT,  # info: "used_pct" : CURSOR_SEED_USED_PCT ,
            "note": "Operator 2026-09-03: ~73% used. Self-update stays off.",  # info: "note" : "Operator 2026-09-03: ~73% used. Self-update stays off." ,
        },  # info: } ,
        "xai": {  # info: "xai" : {
            **_DEFAULT_ACCOUNT,  # info: ** _DEFAULT_ACCOUNT ,
            "kind": "usd_prepaid",  # info: "kind" : "usd_prepaid" ,
            "label": "xAI / Grok",  # info: "label" : "xAI / Grok" ,
            "starting_usd": XAI_SEED_USD,  # info: "starting_usd" : XAI_SEED_USD ,
            "note": "Operator 2026-09-03: $5 prepaid. Spend off.",  # info: "note" : "Operator 2026-09-03: $5 prepaid. Spend off." ,
        },  # info: } ,
        "openai": {**_DEFAULT_ACCOUNT, "kind": "usd_prepaid", "label": "OpenAI"},  # info: "openai" : { ** _DEFAULT_ACCOUNT , "kind" :
        "gemini": {**_DEFAULT_ACCOUNT, "kind": "usd_prepaid", "label": "Gemini"},  # info: "gemini" : { ** _DEFAULT_ACCOUNT , "kind" :
        "anthropic": {**_DEFAULT_ACCOUNT, "kind": "usd_prepaid", "label": "Anthropic"},  # info: "anthropic" : { ** _DEFAULT_ACCOUNT , "kind" :
    }  # info: }


# ====================================================
# SECTION: function flags
# What it does: flags.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def flags() -> dict:  # info: def flags
    path = _state_path()  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    base = {  # info: set base
        "capture_enabled": True,  # info: "capture_enabled" : True ,
        "spend_master": False,  # info: "spend_master" : False ,
        "accounts": _empty_accounts(),  # info: "accounts" : _empty_accounts ( ) ,
        "seeded_at": None,  # info: "seeded_at" : None ,
    }  # info: }
    if not path.is_file():  # info: if not path . is_file ( ) :
        base["seeded_at"] = _now()  # info: base [ "seeded_at" ] = _now ( )
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps (
        return base  # info: return base
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return base  # info: return base
    if not isinstance(data, dict):  # info: if not isinstance ( data , dict )
        return base  # info: return base
    out = dict(base)  # info: set out
    out["capture_enabled"] = bool(data.get("capture_enabled", True))  # info: out [ "capture_enabled" ] = bool ( data
    out["spend_master"] = bool(data.get("spend_master"))  # info: out [ "spend_master" ] = bool ( data
    out["seeded_at"] = data.get("seeded_at") or base["seeded_at"]  # info: out [ "seeded_at" ] = data . get
    accounts = _empty_accounts()  # info: set accounts
    raw = data.get("accounts") if isinstance(data.get("accounts"), dict) else {}  # info: set raw
    for key, acc in accounts.items():  # info: for key , acc in accounts . items
        got = raw.get(key) if isinstance(raw.get(key), dict) else {}  # info: set got
        acc["spend_allowed"] = bool(got.get("spend_allowed"))  # info: acc [ "spend_allowed" ] = bool ( got
        if got.get("starting_usd") not in (None, ""):  # info: if got . get ( "starting_usd" ) not
            try:  # info: try :
                acc["starting_usd"] = max(0.0, float(got["starting_usd"]))  # info: acc [ "starting_usd" ] = max ( 0.0
            except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
                pass  # info: pass
        if got.get("used_pct") not in (None, ""):  # info: if got . get ( "used_pct" ) not
            try:  # info: try :
                acc["used_pct"] = max(0, min(100, int(got["used_pct"])))  # info: acc [ "used_pct" ] = max ( 0
            except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
                pass  # info: pass
        if got.get("note"):  # info: if got . get ( "note" ) :
            acc["note"] = str(got["note"])[:240]  # info: acc [ "note" ] = str ( got
        accounts[key] = acc  # info: accounts [ key ] = acc
    out["accounts"] = accounts  # info: out [ "accounts" ] = accounts
    return out  # info: return out


# ====================================================
# SECTION: function may_spend
# What it does: may spend.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def may_spend(vendor: str) -> tuple[bool, str]:  # info: def may_spend
    st = flags()  # info: set st
    if not st.get("spend_master"):  # info: if not st . get ( "spend_master" )
        return False, "spend_master_off"  # info: return False , "spend_master_off"
    acc = (st.get("accounts") or {}).get(vendor) or {}  # info: set acc
    if not acc.get("spend_allowed"):  # info: if not acc . get ( "spend_allowed" )
        return False, f"{vendor}_off"  # info: return False , f" { vendor } _off
    if not spend_gate_open():  # info: if not spend_gate_open ( ) :
        return False, "rr_api_spend_off"  # info: return False , "rr_api_spend_off"
    return True, "ok"  # info: return True , "ok"


# ====================================================
# SECTION: function connect
# What it does: connect.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def connect() -> sqlite3.Connection:  # info: def connect
    path = _db_path()  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    conn = sqlite3.connect(str(path))  # info: set conn
    conn.row_factory = sqlite3.Row  # info: conn . row_factory = sqlite3 . Row
    conn.execute("PRAGMA journal_mode=WAL")  # info: conn . execute ( "PRAGMA journal_mode=WAL" )
    conn.executescript(  # info: conn . executescript (
        """
        CREATE TABLE IF NOT EXISTS prices (
          id INTEGER PRIMARY KEY,
          at TEXT NOT NULL,
          source TEXT NOT NULL,
          vendor TEXT NOT NULL,
          model TEXT NOT NULL,
          input_per_m REAL,
          cached_per_m REAL,
          output_per_m REAL,
          unit TEXT,
          notes TEXT,
          live INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_prices_vendor ON prices(vendor, at);
        CREATE TABLE IF NOT EXISTS fetches (
          id INTEGER PRIMARY KEY,
          at TEXT NOT NULL,
          source TEXT NOT NULL,
          vendor TEXT NOT NULL,
          url TEXT,
          ok INTEGER NOT NULL,
          bytes INTEGER,
          sha TEXT,
          detail TEXT
        );
        CREATE TABLE IF NOT EXISTS usage (
          id INTEGER PRIMARY KEY,
          at TEXT NOT NULL,
          vendor TEXT NOT NULL,
          model TEXT,
          input_tokens INTEGER,
          output_tokens INTEGER,
          cached_tokens INTEGER,
          usd REAL,
          surface TEXT,
          note TEXT
        );
        """
    )  # info: )
    return conn  # info: return conn


# ====================================================
# SECTION: function _insert_price
# What it does:  insert price.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _insert_price(conn: sqlite3.Connection, source: str, row: dict, live: int) -> None:  # info: def _insert_price
    conn.execute(  # info: conn . execute (
        """INSERT INTO prices (at, source, vendor, model, input_per_m, cached_per_m, output_per_m, unit, notes, live)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (  # info: call (
            _now(),  # info: call _now
            source,  # info: source ,
            row["vendor"],  # info: row [ "vendor" ] ,
            row["model"],  # info: row [ "model" ] ,
            row.get("input") if "input" in row else row.get("input_per_m"),  # info: row . get ( "input" ) if "input"
            row.get("cached") if "cached" in row else row.get("cached_per_m"),  # info: row . get ( "cached" ) if "cached"
            row.get("output") if "output" in row else row.get("output_per_m"),  # info: row . get ( "output" ) if "output"
            row.get("unit") or "1M tokens",  # info: row . get ( "unit" ) or "1M tokens"
            row.get("notes") or "",  # info: row . get ( "notes" ) or ""
            int(live),  # info: call int
        ),  # info: ) ,
    )  # info: )


# ====================================================
# SECTION: function _seed_prices
# What it does:  seed prices.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _seed_prices(source: str) -> int:  # info: def _seed_prices
    conn = connect()  # info: set conn
    try:  # info: try :
        n = conn.execute("SELECT COUNT(*) AS n FROM prices").fetchone()["n"]  # info: set n
        if n:  # info: if n :
            return 0  # info: return 0
        for row in SEED_ROWS:  # info: for row in SEED_ROWS :
            _insert_price(conn, source, row, live=0)  # info: call _insert_price
        conn.commit()  # info: conn . commit ( )
        return len(SEED_ROWS)  # info: return len ( SEED_ROWS )
    finally:  # info: finally :
        conn.close()  # info: conn . close ( )


# ====================================================
# SECTION: function seed
# What it does: Write the embedded catalog. No HTTP.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def seed(source: str = "seed") -> int:  # info: def seed
    """Write the embedded catalog. No HTTP."""  # info: """Write the embedded catalog. No HTTP."""
    flags()  # info: call flags
    return _seed_prices(source)  # info: return _seed_prices ( source )


# ====================================================
# SECTION: function latest_catalog
# What it does: latest catalog.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def latest_catalog(limit: int = 80) -> list[dict]:  # info: def latest_catalog
    conn = connect()  # info: set conn
    try:  # info: try :
        rows = conn.execute(  # info: set rows
            """SELECT vendor, model, input_per_m, cached_per_m, output_per_m, unit, notes, at, live
               FROM prices ORDER BY id DESC LIMIT ?""",
            (max(20, int(limit)),),  # info: call (
        ).fetchall()  # info: ) . fetchall ( )
    finally:  # info: finally :
        conn.close()  # info: conn . close ( )
    seen: set[tuple[str, str]] = set()  # info: set seen
    out = []  # info: set out
    for row in rows:  # info: for row in rows :
        key = (row["vendor"], row["model"])  # info: set key
        if key in seen:  # info: if key in seen :
            continue  # info: continue
        seen.add(key)  # info: seen . add ( key )
        out.append(dict(row))  # info: out . append ( dict ( row )
    out.sort(key=lambda r: (r["vendor"], r["model"]))  # info: out . sort ( key = lambda r
    return out  # info: return out


# ====================================================
# SECTION: function latest_price
# What it does: latest price.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def latest_price(vendor: str, model: str) -> dict | None:  # info: def latest_price
    for row in latest_catalog(limit=200):  # info: for row in latest_catalog ( limit = 200
        if row["vendor"] == vendor and row["model"] == model:  # info: if row [ "vendor" ] == vendor and
            return row  # info: return row
    for seed_row in SEED_ROWS:  # info: for seed_row in SEED_ROWS :
        if seed_row["vendor"] == vendor and seed_row["model"] == model:  # info: if seed_row [ "vendor" ] == vendor and
            return {  # info: return {
                "vendor": vendor,  # info: "vendor" : vendor ,
                "model": model,  # info: "model" : model ,
                "input_per_m": seed_row.get("input"),  # info: "input_per_m" : seed_row . get ( "input" )
                "cached_per_m": seed_row.get("cached"),  # info: "cached_per_m" : seed_row . get ( "cached" )
                "output_per_m": seed_row.get("output"),  # info: "output_per_m" : seed_row . get ( "output" )
                "unit": seed_row.get("unit") or "1M tokens",  # info: "unit" : seed_row . get ( "unit" )
                "notes": seed_row.get("notes"),  # info: "notes" : seed_row . get ( "notes" )
                "at": None,  # info: "at" : None ,
                "live": 0,  # info: "live" : 0 ,
            }  # info: }
    return None  # info: return None


# ====================================================
# SECTION: function estimate_usd
# What it does: estimate usd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def estimate_usd(  # info: def estimate_usd
    vendor: str,  # info: set vendor
    model: str,  # info: set model
    *,  # info: * ,
    input_tokens: int = 0,  # info: set input_tokens
    output_tokens: int = 0,  # info: set output_tokens
    cached_tokens: int = 0,  # info: set cached_tokens
) -> float | None:  # info: ) -> float | None :
    row = latest_price(vendor, model)  # info: set row
    if not row:  # info: if not row :
        return None  # info: return None
    usd = 0.0  # info: set usd
    known = False  # info: set known
    for key, tokens in (  # info: for key , tokens in (
        ("input_per_m", input_tokens),  # info: call (
        ("cached_per_m", cached_tokens),  # info: call (
        ("output_per_m", output_tokens),  # info: call (
    ):  # info: ) :
        rate = row.get(key)  # info: set rate
        if rate is None:  # info: if rate is None :
            continue  # info: continue
        usd += (max(0, int(tokens)) / 1_000_000) * float(rate)  # info: set usd
        known = True  # info: set known
    return round(usd, 6) if known else None  # info: return round ( usd , 6 ) if


# ====================================================
# SECTION: function record_usage
# What it does: record usage.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def record_usage(  # info: def record_usage
    vendor: str,  # info: set vendor
    *,  # info: * ,
    model: str | None = None,  # info: set model
    input_tokens: int = 0,  # info: set input_tokens
    output_tokens: int = 0,  # info: set output_tokens
    cached_tokens: int = 0,  # info: set cached_tokens
    usd: float | None = None,  # info: set usd
    surface: str = "",  # info: set surface
    note: str = "",  # info: set note
) -> None:  # info: ) -> None :
    if usd is None:  # info: if usd is None :
        usd = estimate_usd(  # info: set usd
            vendor,  # info: vendor ,
            model or "",  # info: model or "" ,
            input_tokens=input_tokens,  # info: set input_tokens
            output_tokens=output_tokens,  # info: set output_tokens
            cached_tokens=cached_tokens,  # info: set cached_tokens
        )  # info: )
    conn = connect()  # info: set conn
    try:  # info: try :
        conn.execute(  # info: conn . execute (
            """INSERT INTO usage (at, vendor, model, input_tokens, output_tokens, cached_tokens, usd, surface, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (  # info: call (
                _now(),  # info: call _now
                vendor,  # info: vendor ,
                model,  # info: model ,
                int(input_tokens or 0),  # info: call int
                int(output_tokens or 0),  # info: call int
                int(cached_tokens or 0),  # info: call int
                usd,  # info: usd ,
                surface[:40],  # info: surface [ : 40 ] ,
                note[:240],  # info: note [ : 240 ] ,
            ),  # info: ) ,
        )  # info: )
        conn.commit()  # info: conn . commit ( )
    finally:  # info: finally :
        conn.close()  # info: conn . close ( )


# ====================================================
# SECTION: function _fetch
# What it does: GET a public docs page. Caller must already have passed the price gate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fetch(url: str, alt: str | None) -> tuple[str, str, bytes]:  # info: def _fetch
    """GET a public docs page. Caller must already have passed the price gate."""  # info: """GET a public docs page. Caller must already have passed the price gate."""
    note_http()  # info: call note_http
    last_err = ""  # info: set last_err
    for candidate in (url, alt):  # info: for candidate in ( url , alt )
        if not candidate:  # info: if not candidate :
            continue  # info: continue
        req = urllib.request.Request(candidate, headers={"User-Agent": _UA})  # info: set req
        try:  # info: try :
            with urllib.request.urlopen(req, timeout=12) as resp:  # info: with urllib . request . urlopen ( req
                status = getattr(resp, "status", 200)  # info: set status
                if status >= 400:  # info: if status >= 400 :
                    last_err = f"HTTP {status}"  # info: set last_err
                    continue  # info: continue
                return candidate, "", resp.read()  # info: return candidate , "" , resp . read
        except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
            last_err = f"HTTP {exc.code}"  # info: set last_err
        except Exception as exc:  # info: except Exception as exc :
            last_err = str(exc)[:200]  # info: set last_err
    return url, last_err or "fetch_failed", b""  # info: return url , last_err or "fetch_failed" , b""


# ====================================================
# SECTION: function _parse_live
# What it does:  parse live.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _parse_live(vendor: str, text: str) -> list[dict]:  # info: def _parse_live
    low = text.lower()  # info: set low
    found: list[dict] = []  # info: set found

    def grab(model: str, *needles: str) -> None:  # info: def grab
        idx = -1  # info: set idx
        hit = ""  # info: set hit
        for needle in needles:  # info: for needle in needles :
            i = low.find(needle.lower())  # info: set i
            if i >= 0:  # info: if i >= 0 :
                idx = i  # info: set idx
                hit = needle  # info: set hit
                break  # info: break
        if idx < 0:  # info: if idx < 0 :
            return  # info: return
        window = text[idx : idx + 900]  # info: set window
        money = [float(x) for x in _MONEY.findall(window)[:6]]  # info: set money
        if len(money) < 2:  # info: if len ( money ) < 2 :
            return  # info: return
        inp = money[0]  # info: set inp
        if len(money) >= 4:  # info: if len ( money ) >= 4 :
            cached, out = money[2], money[3]  # info: cached , out = money [ 2 ]
        elif len(money) >= 3:  # info: elif len ( money ) >= 3 :
            cached, out = money[1], money[2]  # info: cached , out = money [ 1 ]
        else:  # info: else :
            cached, out = None, money[1]  # info: cached , out = None , money [
        found.append(  # info: found . append (
            {  # info: {
                "vendor": vendor,  # info: "vendor" : vendor ,
                "model": model,  # info: "model" : model ,
                "input": inp,  # info: "input" : inp ,
                "cached": cached,  # info: "cached" : cached ,
                "output": out,  # info: "output" : out ,
                "notes": f"live parse near {hit!r}",  # info: "notes" : f" live parse near { hit ! r
            }  # info: }
        )  # info: )

    if vendor == "xai":  # info: if vendor == "xai" :
        grab("grok-4.6", "grok-4.6 (< 200k", "grok-4.6")  # info: call grab
        grab("grok-4.5", "grok-4.5 (< 200k", "grok-4.5")  # info: call grab
    elif vendor == "cursor":  # info: elif vendor == "cursor" :
        grab("grok-4.6", "Grok 4.6")  # info: call grab
        grab("composer-2.5", "Composer 2.5")  # info: call grab
    elif vendor == "openai":  # info: elif vendor == "openai" :
        grab("gpt-5.6-sol", "gpt-5.6-sol", "GPT-5.6 Sol")  # info: call grab
        grab("gpt-5.6-terra", "gpt-5.6-terra", "GPT-5.6 Terra")  # info: call grab
    elif vendor == "gemini":  # info: elif vendor == "gemini" :
        grab("gemini-2.5-flash", "Gemini 2.5 Flash")  # info: call grab
        grab("gemini-3.1-pro", "Gemini 3.1 Pro")  # info: call grab
    return found  # info: return found


# ====================================================
# SECTION: function _probe_xai_prepaid
# What it does: Billing GET. Caller must already have passed the price gate and spend_master.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _probe_xai_prepaid() -> dict:  # info: def _probe_xai_prepaid
    """Billing GET. Caller must already have passed the price gate and spend_master."""  # info: """Billing GET. Caller must already have passed the price gate and spend_master."""
    if not envload.key_set("XAI_MGMT_KEY") or not envload.key_set("XAI_TEAM_ID"):  # info: if not envload . key_set ( "XAI_MGMT_KEY" )
        return {"ok": False, "detail": "no_mgmt_key"}  # info: return { "ok" : False , "detail" :
    envload.load_env()  # info: envload . load_env ( )
    key = (os.environ.get("XAI_MGMT_KEY") or "").strip()  # info: set key
    team = (os.environ.get("XAI_TEAM_ID") or "").strip()  # info: set team
    url = f"https://management-api.x.ai/v1/billing/teams/{team}/prepaid/balance"  # info: set url
    note_http()  # info: call note_http
    req = urllib.request.Request(  # info: set req
        url,  # info: url ,
        headers={"Authorization": f"Bearer {key}", "User-Agent": _UA},  # info: set headers
    )  # info: )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=15) as resp:  # info: with urllib . request . urlopen ( req
            body = resp.read()  # info: set body
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        return {"ok": False, "detail": f"HTTP {exc.code}"}  # info: return { "ok" : False , "detail" :
    except Exception as exc:  # info: except Exception as exc :
        return {"ok": False, "detail": str(exc)[:160]}  # info: return { "ok" : False , "detail" :
    try:  # info: try :
        data = json.loads(body.decode("utf-8", "replace"))  # info: set data
    except json.JSONDecodeError:  # info: except json . JSONDecodeError :
        return {"ok": False, "detail": "bad_json"}  # info: return { "ok" : False , "detail" :
    total = data.get("total") if isinstance(data, dict) else None  # info: set total
    raw = total.get("val") if isinstance(total, dict) else total  # info: set raw
    try:  # info: try :
        usd = abs(int(str(raw).strip())) / 100.0  # info: set usd
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return {"ok": False, "detail": "no_total"}  # info: return { "ok" : False , "detail" :
    return {"ok": True, "usd": usd, "detail": "mgmt_prepaid"}  # info: return { "ok" : True , "usd" :


# ====================================================
# SECTION: function _key_present
# What it does:  key present.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _key_present(vendor: str) -> bool:  # info: def _key_present
    name = {  # info: set name
        "xai": "XAI_API_KEY",  # info: "xai" : "XAI_API_KEY" ,
        "cursor": "CURSOR_API_KEY",  # info: "cursor" : "CURSOR_API_KEY" ,
    }.get(vendor, "")  # info: } . get ( vendor , "" )
    return envload.key_set(name) if name else False  # info: return envload . key_set ( name ) if


# ====================================================
# SECTION: function _balance_block
# What it does:  balance block.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _balance_block(st: dict, *, probe: bool) -> dict:  # info: def _balance_block
    xai_live = {"ok": False, "detail": "spend_off"}  # info: set xai_live
    if probe and st.get("spend_master"):  # info: if probe and st . get ( "spend_master"
        xai_live = _probe_xai_prepaid()  # info: set xai_live
    out = {}  # info: set out
    for key, acc in (st.get("accounts") or {}).items():  # info: for key , acc in ( st .
        starting = acc.get("starting_usd")  # info: set starting
        used_pct = acc.get("used_pct")  # info: set used_pct
        remaining_usd = None  # info: set remaining_usd
        remaining_pct = None  # info: set remaining_pct
        status = "needs_seed"  # info: set status
        live = None  # info: set live
        if key == "xai" and xai_live.get("ok"):  # info: if key == "xai" and xai_live . get
            live = xai_live.get("usd")  # info: set live
            remaining_usd = live  # info: set remaining_usd
            status = "live"  # info: set status
        elif acc.get("kind") == "percent_pool" and used_pct is not None:  # info: elif acc . get ( "kind" ) ==
            remaining_pct = max(0, 100 - int(used_pct))  # info: set remaining_pct
            status = "seeded"  # info: set status
        elif starting is not None:  # info: elif starting is not None :
            remaining_usd = round(float(starting), 4)  # info: set remaining_usd
            status = "seeded"  # info: set status
        out[key] = {  # info: out [ key ] = {
            "label": acc.get("label") or key,  # info: "label" : acc . get ( "label" )
            "kind": acc.get("kind"),  # info: "kind" : acc . get ( "kind" )
            "spend_allowed": bool(acc.get("spend_allowed")),  # info: "spend_allowed" : bool ( acc . get (
            "key_present": _key_present(key),  # info: "key_present" : _key_present ( key ) ,
            "starting_usd": starting,  # info: "starting_usd" : starting ,
            "used_pct": used_pct,  # info: "used_pct" : used_pct ,
            "remaining_pct": remaining_pct,  # info: "remaining_pct" : remaining_pct ,
            "remaining_usd": remaining_usd,  # info: "remaining_usd" : remaining_usd ,
            "live_usd": live,  # info: "live_usd" : live ,
            "status": status,  # info: "status" : status ,
        }  # info: }
    return out  # info: return out


# ====================================================
# SECTION: function _write_last
# What it does:  write last.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_last(payload: dict) -> None:  # info: def _write_last
    path = _last_path()  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps (


# ====================================================
# SECTION: function refresh
# What it does: Seed locally. HTTP only when RR_API_PRICES=1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def refresh(*, source: str = "daily") -> dict:  # info: def refresh
    """Seed locally. HTTP only when RR_API_PRICES=1."""  # info: """Seed locally. HTTP only when RR_API_PRICES=1."""
    st = flags()  # info: set st
    seeded = _seed_prices(source)  # info: set seeded
    out: dict[str, Any] = {  # info: set out
        "ok": True,  # info: "ok" : True ,
        "source": source,  # info: "source" : source ,
        "at": datetime.now(HST).isoformat(),  # info: "at" : datetime . now ( HST )
        "seeded_rows": seeded,  # info: "seeded_rows" : seeded ,
        "fetches": [],  # info: "fetches" : [ ] ,
        "live_rows": 0,  # info: "live_rows" : 0 ,
        "http": False,  # info: "http" : False ,
    }  # info: }
    if not prices_gate_open():  # info: if not prices_gate_open ( ) :
        out["detail"] = "rr_api_prices_off"  # info: out [ "detail" ] = "rr_api_prices_off"
        out["balances"] = _balance_block(st, probe=False)  # info: out [ "balances" ] = _balance_block ( st
        _write_last(out)  # info: call _write_last
        return out  # info: return out
    if not st.get("capture_enabled"):  # info: if not st . get ( "capture_enabled" )
        out["detail"] = "capture_off"  # info: out [ "detail" ] = "capture_off"
        _write_last(out)  # info: call _write_last
        return out  # info: return out
    out["http"] = True  # info: out [ "http" ] = True
    conn = connect()  # info: set conn
    live_n = 0  # info: set live_n
    try:  # info: try :
        for src in SOURCES:  # info: for src in SOURCES :
            url, err, body = _fetch(src["url"], src.get("alt"))  # info: url , err , body = _fetch (
            sha = hashlib.sha256(body).hexdigest()[:16] if body else ""  # info: set sha
            ok = bool(body) and not err  # info: set ok
            conn.execute(  # info: conn . execute (
                """INSERT INTO fetches (at, source, vendor, url, ok, bytes, sha, detail)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (_now(), source, src["vendor"], url, int(ok), len(body), sha, err[:200]),  # info: call (
            )  # info: )
            parsed = _parse_live(src["vendor"], body.decode("utf-8", "replace")) if body else []  # info: set parsed
            for row in parsed:  # info: for row in parsed :
                _insert_price(conn, source, row, live=1)  # info: call _insert_price
                live_n += 1  # info: set live_n
            out["fetches"].append(  # info: out [ "fetches" ] . append (
                {"vendor": src["vendor"], "url": url, "ok": ok, "bytes": len(body), "parsed": len(parsed), "detail": err or "ok"}  # info: { "vendor" : src [ "vendor" ] ,
            )  # info: )
        conn.commit()  # info: conn . commit ( )
    finally:  # info: finally :
        conn.close()  # info: conn . close ( )
    out["live_rows"] = live_n  # info: out [ "live_rows" ] = live_n
    out["balances"] = _balance_block(st, probe=bool(st.get("spend_master")))  # info: out [ "balances" ] = _balance_block ( st
    _write_last(out)  # info: call _write_last
    return out  # info: return out
