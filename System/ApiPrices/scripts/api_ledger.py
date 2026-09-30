#!/usr/bin/env python3
"""Public API price catalog. Package ApiPrices.

Spend stays off. Public-doc GET and the xAI billing probe run only when
RR_API_PRICES=1. This module does not call chat, TTS, or Cursor.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import envload

HST = ZoneInfo("Pacific/Honolulu")
LIVE_DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
STATS = {"http_attempts": 0, "spend_attempts": 0}

DEFAULT_XAI_MODEL = "grok-4.6"
DEFAULT_CURSOR_MODEL = "composer-2.5"

# Operator notes from 2026-09-03. Not live meters.
CURSOR_SEED_USED_PCT = 73
XAI_SEED_USD = 5.00
REPORT_AUDIO_CLIP_USD = 0.10
REPORT_AUDIO_CLIP_ACTUAL_USD = 0.07

SOURCES = (
    {"vendor": "cursor", "url": "https://cursor.com/docs/models.md", "alt": "https://cursor.com/docs/models"},
    {"vendor": "xai", "url": "https://docs.x.ai/docs/models.md", "alt": "https://docs.x.ai/docs/models"},
    {"vendor": "openai", "url": "https://developers.openai.com/api/docs/pricing.md", "alt": "https://openai.com/api/pricing/"},
    {"vendor": "gemini", "url": "https://ai.google.dev/gemini-api/docs/pricing.md", "alt": "https://ai.google.dev/gemini-api/docs/pricing"},
)

# USD per million tokens unless unit says otherwise. Captured 2026-09-03.
SEED_ROWS: tuple[dict[str, Any], ...] = (
    {"vendor": "cursor", "model": "grok-4.6", "input": 2.0, "cached": 0.5, "output": 6.0, "notes": "Cursor Models pool; Auto list price when routed here"},
    {"vendor": "cursor", "model": "grok-4.6-fast", "input": 4.0, "cached": 1.0, "output": 12.0, "notes": "Cursor Models pool"},
    {"vendor": "cursor", "model": "grok-4.5", "input": 2.0, "cached": 0.5, "output": 6.0, "notes": "Cursor Models pool"},
    {"vendor": "cursor", "model": "composer-2.5", "input": 0.5, "cached": 0.2, "output": 2.5, "notes": "Cursor Models pool; cheapest first-party"},
    {"vendor": "cursor", "model": "composer-2.5-fast", "input": 3.0, "cached": 0.5, "output": 15.0, "notes": "Cursor Models pool"},
    {"vendor": "cursor", "model": "token-rate-third-party", "input": 0.25, "cached": 0.25, "output": 0.25, "notes": "Teams/Enterprise add-on per million tokens on third-party; first-party exempt"},
    {"vendor": "cursor", "model": "auto", "input": None, "cached": None, "output": None, "notes": "Bills at the routed model list price"},
    {"vendor": "xai", "model": "grok-4.6", "input": 2.0, "cached": 0.5, "output": 6.0, "notes": "<200k prompt; >=200k doubles all three"},
    {"vendor": "xai", "model": "grok-4.6-long", "input": 4.0, "cached": 1.0, "output": 12.0, "notes": "whole request once prompt >=200k"},
    {"vendor": "xai", "model": "grok-4.5", "input": 2.0, "cached": 0.3, "output": 6.0, "notes": "<200k prompt"},
    {"vendor": "xai", "model": "grok-4.3", "input": 1.25, "cached": 0.2, "output": 2.5, "notes": "<200k prompt"},
    {"vendor": "xai", "model": "grok-imagine-image-2.0", "input": None, "cached": None, "output": 0.04, "unit": "image", "notes": "from $0.04 / image"},
    {"vendor": "xai", "model": "grok-voice-tts", "input": None, "cached": None, "output": 15.0, "unit": "1M chars", "notes": "Text to Speech; report clip meter is $0.10"},
    {"vendor": "openai", "model": "gpt-5.6-sol", "input": 4.0, "cached": 0.4, "output": 20.0, "notes": "short context"},
    {"vendor": "openai", "model": "gpt-5.6-terra", "input": 2.0, "cached": 0.2, "output": 12.0, "notes": "short context"},
    {"vendor": "openai", "model": "gpt-5.6-luna", "input": 0.2, "cached": 0.02, "output": 1.2, "notes": "short context"},
    {"vendor": "openai", "model": "gpt-6-astra", "input": 10.0, "cached": 1.0, "output": 50.0, "notes": "Trusted Access; short context"},
    {"vendor": "openai", "model": "gpt-5.3-codex", "input": 1.75, "cached": 0.175, "output": 14.0, "notes": "Codex"},
    {"vendor": "gemini", "model": "gemini-3.6-flash", "input": 1.5, "cached": 0.15, "output": 7.5, "notes": "Google paid standard"},
    {"vendor": "gemini", "model": "gemini-3.1-pro", "input": 2.0, "cached": 0.2, "output": 12.0, "notes": "<=200k; >200k input $4 / output $18"},
    {"vendor": "gemini", "model": "gemini-2.5-flash-lite", "input": 0.1, "cached": 0.01, "output": 0.4, "notes": "cheapest Gemini paid text"},
    {"vendor": "gemini", "model": "gemini-2.5-pro", "input": 1.25, "cached": 0.125, "output": 10.0, "notes": "<=200k; >200k input $2.50 / output $15"},
    {"vendor": "gemini", "model": "gemini-3.8-flash", "input": 0.75, "cached": 0.075, "output": 3.5, "notes": "as billed inside Cursor Other Models"},
    {"vendor": "anthropic", "model": "claude-sonnet-5", "input": 2.0, "cached": 0.2, "output": 10.0, "notes": "Cursor Other Models list"},
    {"vendor": "anthropic", "model": "claude-opus-5", "input": 5.0, "cached": 0.5, "output": 25.0, "notes": "Cursor Other Models list"},
)

_DEFAULT_ACCOUNT = {"spend_allowed": False, "starting_usd": None, "used_pct": None, "note": ""}
_MONEY = re.compile(r"\$([0-9]+(?:\.[0-9]+)?)")
_UA = "RootRecord-ava-ledger/1.0 (price catalog; no inference)"


def prices_gate_open() -> bool:
    return os.environ.get("RR_API_PRICES", "0") == "1"


def spend_gate_open() -> bool:
    return os.environ.get("RR_API_SPEND", "0") == "1"


def note_http() -> None:
    STATS["http_attempts"] += 1


def note_spend() -> None:
    STATS["spend_attempts"] += 1


def data_dir() -> Path:
    root = Path(os.environ.get("RR_DATABASE_ROOT", str(LIVE_DB)))
    return root / "System" / "ApiPrices"


def log_dir() -> Path:
    root = Path(os.environ.get("RR_DATABASE_ROOT", str(LIVE_DB)))
    return root / "Logs" / "System" / "ApiPrices"


def _state_path() -> Path:
    return data_dir() / "api-ledger.json"


def _last_path() -> Path:
    return data_dir() / "api-ledger-last.json"


def _db_path() -> Path:
    return data_dir() / "api-ledger.sqlite"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_accounts() -> dict[str, dict]:
    return {
        "cursor": {
            **_DEFAULT_ACCOUNT,
            "kind": "percent_pool",
            "label": "Cursor",
            "used_pct": CURSOR_SEED_USED_PCT,
            "note": "Operator 2026-09-03: ~73% used. Self-update stays off.",
        },
        "xai": {
            **_DEFAULT_ACCOUNT,
            "kind": "usd_prepaid",
            "label": "xAI / Grok",
            "starting_usd": XAI_SEED_USD,
            "note": "Operator 2026-09-03: $5 prepaid. Spend off.",
        },
        "openai": {**_DEFAULT_ACCOUNT, "kind": "usd_prepaid", "label": "OpenAI"},
        "gemini": {**_DEFAULT_ACCOUNT, "kind": "usd_prepaid", "label": "Gemini"},
        "anthropic": {**_DEFAULT_ACCOUNT, "kind": "usd_prepaid", "label": "Anthropic"},
    }


def flags() -> dict:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    base = {
        "capture_enabled": True,
        "spend_master": False,
        "accounts": _empty_accounts(),
        "seeded_at": None,
    }
    if not path.is_file():
        base["seeded_at"] = _now()
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return base
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return base
    if not isinstance(data, dict):
        return base
    out = dict(base)
    out["capture_enabled"] = bool(data.get("capture_enabled", True))
    out["spend_master"] = bool(data.get("spend_master"))
    out["seeded_at"] = data.get("seeded_at") or base["seeded_at"]
    accounts = _empty_accounts()
    raw = data.get("accounts") if isinstance(data.get("accounts"), dict) else {}
    for key, acc in accounts.items():
        got = raw.get(key) if isinstance(raw.get(key), dict) else {}
        acc["spend_allowed"] = bool(got.get("spend_allowed"))
        if got.get("starting_usd") not in (None, ""):
            try:
                acc["starting_usd"] = max(0.0, float(got["starting_usd"]))
            except (TypeError, ValueError):
                pass
        if got.get("used_pct") not in (None, ""):
            try:
                acc["used_pct"] = max(0, min(100, int(got["used_pct"])))
            except (TypeError, ValueError):
                pass
        if got.get("note"):
            acc["note"] = str(got["note"])[:240]
        accounts[key] = acc
    out["accounts"] = accounts
    return out


def may_spend(vendor: str) -> tuple[bool, str]:
    st = flags()
    if not st.get("spend_master"):
        return False, "spend_master_off"
    acc = (st.get("accounts") or {}).get(vendor) or {}
    if not acc.get("spend_allowed"):
        return False, f"{vendor}_off"
    if not spend_gate_open():
        return False, "rr_api_spend_off"
    return True, "ok"


def connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
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
    )
    return conn


def _insert_price(conn: sqlite3.Connection, source: str, row: dict, live: int) -> None:
    conn.execute(
        """INSERT INTO prices (at, source, vendor, model, input_per_m, cached_per_m, output_per_m, unit, notes, live)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            _now(),
            source,
            row["vendor"],
            row["model"],
            row.get("input") if "input" in row else row.get("input_per_m"),
            row.get("cached") if "cached" in row else row.get("cached_per_m"),
            row.get("output") if "output" in row else row.get("output_per_m"),
            row.get("unit") or "1M tokens",
            row.get("notes") or "",
            int(live),
        ),
    )


def _seed_prices(source: str) -> int:
    conn = connect()
    try:
        n = conn.execute("SELECT COUNT(*) AS n FROM prices").fetchone()["n"]
        if n:
            return 0
        for row in SEED_ROWS:
            _insert_price(conn, source, row, live=0)
        conn.commit()
        return len(SEED_ROWS)
    finally:
        conn.close()


def seed(source: str = "seed") -> int:
    """Write the embedded catalog. No HTTP."""
    flags()
    return _seed_prices(source)


def latest_catalog(limit: int = 80) -> list[dict]:
    conn = connect()
    try:
        rows = conn.execute(
            """SELECT vendor, model, input_per_m, cached_per_m, output_per_m, unit, notes, at, live
               FROM prices ORDER BY id DESC LIMIT ?""",
            (max(20, int(limit)),),
        ).fetchall()
    finally:
        conn.close()
    seen: set[tuple[str, str]] = set()
    out = []
    for row in rows:
        key = (row["vendor"], row["model"])
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(row))
    out.sort(key=lambda r: (r["vendor"], r["model"]))
    return out


def latest_price(vendor: str, model: str) -> dict | None:
    for row in latest_catalog(limit=200):
        if row["vendor"] == vendor and row["model"] == model:
            return row
    for seed_row in SEED_ROWS:
        if seed_row["vendor"] == vendor and seed_row["model"] == model:
            return {
                "vendor": vendor,
                "model": model,
                "input_per_m": seed_row.get("input"),
                "cached_per_m": seed_row.get("cached"),
                "output_per_m": seed_row.get("output"),
                "unit": seed_row.get("unit") or "1M tokens",
                "notes": seed_row.get("notes"),
                "at": None,
                "live": 0,
            }
    return None


def estimate_usd(
    vendor: str,
    model: str,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_tokens: int = 0,
) -> float | None:
    row = latest_price(vendor, model)
    if not row:
        return None
    usd = 0.0
    known = False
    for key, tokens in (
        ("input_per_m", input_tokens),
        ("cached_per_m", cached_tokens),
        ("output_per_m", output_tokens),
    ):
        rate = row.get(key)
        if rate is None:
            continue
        usd += (max(0, int(tokens)) / 1_000_000) * float(rate)
        known = True
    return round(usd, 6) if known else None


def record_usage(
    vendor: str,
    *,
    model: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_tokens: int = 0,
    usd: float | None = None,
    surface: str = "",
    note: str = "",
) -> None:
    if usd is None:
        usd = estimate_usd(
            vendor,
            model or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )
    conn = connect()
    try:
        conn.execute(
            """INSERT INTO usage (at, vendor, model, input_tokens, output_tokens, cached_tokens, usd, surface, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                _now(),
                vendor,
                model,
                int(input_tokens or 0),
                int(output_tokens or 0),
                int(cached_tokens or 0),
                usd,
                surface[:40],
                note[:240],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _fetch(url: str, alt: str | None) -> tuple[str, str, bytes]:
    """GET a public docs page. Caller must already have passed the price gate."""
    note_http()
    last_err = ""
    for candidate in (url, alt):
        if not candidate:
            continue
        req = urllib.request.Request(candidate, headers={"User-Agent": _UA})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                status = getattr(resp, "status", 200)
                if status >= 400:
                    last_err = f"HTTP {status}"
                    continue
                return candidate, "", resp.read()
        except urllib.error.HTTPError as exc:
            last_err = f"HTTP {exc.code}"
        except Exception as exc:
            last_err = str(exc)[:200]
    return url, last_err or "fetch_failed", b""


def _parse_live(vendor: str, text: str) -> list[dict]:
    low = text.lower()
    found: list[dict] = []

    def grab(model: str, *needles: str) -> None:
        idx = -1
        hit = ""
        for needle in needles:
            i = low.find(needle.lower())
            if i >= 0:
                idx = i
                hit = needle
                break
        if idx < 0:
            return
        window = text[idx : idx + 900]
        money = [float(x) for x in _MONEY.findall(window)[:6]]
        if len(money) < 2:
            return
        inp = money[0]
        if len(money) >= 4:
            cached, out = money[2], money[3]
        elif len(money) >= 3:
            cached, out = money[1], money[2]
        else:
            cached, out = None, money[1]
        found.append(
            {
                "vendor": vendor,
                "model": model,
                "input": inp,
                "cached": cached,
                "output": out,
                "notes": f"live parse near {hit!r}",
            }
        )

    if vendor == "xai":
        grab("grok-4.6", "grok-4.6 (< 200k", "grok-4.6")
        grab("grok-4.5", "grok-4.5 (< 200k", "grok-4.5")
    elif vendor == "cursor":
        grab("grok-4.6", "Grok 4.6")
        grab("composer-2.5", "Composer 2.5")
    elif vendor == "openai":
        grab("gpt-5.6-sol", "gpt-5.6-sol", "GPT-5.6 Sol")
        grab("gpt-5.6-terra", "gpt-5.6-terra", "GPT-5.6 Terra")
    elif vendor == "gemini":
        grab("gemini-2.5-flash", "Gemini 2.5 Flash")
        grab("gemini-3.1-pro", "Gemini 3.1 Pro")
    return found


def _probe_xai_prepaid() -> dict:
    """Billing GET. Caller must already have passed the price gate and spend_master."""
    if not envload.key_set("XAI_MGMT_KEY") or not envload.key_set("XAI_TEAM_ID"):
        return {"ok": False, "detail": "no_mgmt_key"}
    envload.load_env()
    key = (os.environ.get("XAI_MGMT_KEY") or "").strip()
    team = (os.environ.get("XAI_TEAM_ID") or "").strip()
    url = f"https://management-api.x.ai/v1/billing/teams/{team}/prepaid/balance"
    note_http()
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": _UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        return {"ok": False, "detail": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)[:160]}
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return {"ok": False, "detail": "bad_json"}
    total = data.get("total") if isinstance(data, dict) else None
    raw = total.get("val") if isinstance(total, dict) else total
    try:
        usd = abs(int(str(raw).strip())) / 100.0
    except (TypeError, ValueError):
        return {"ok": False, "detail": "no_total"}
    return {"ok": True, "usd": usd, "detail": "mgmt_prepaid"}


def _key_present(vendor: str) -> bool:
    name = {
        "xai": "XAI_API_KEY",
        "cursor": "CURSOR_API_KEY",
    }.get(vendor, "")
    return envload.key_set(name) if name else False


def _balance_block(st: dict, *, probe: bool) -> dict:
    xai_live = {"ok": False, "detail": "spend_off"}
    if probe and st.get("spend_master"):
        xai_live = _probe_xai_prepaid()
    out = {}
    for key, acc in (st.get("accounts") or {}).items():
        starting = acc.get("starting_usd")
        used_pct = acc.get("used_pct")
        remaining_usd = None
        remaining_pct = None
        status = "needs_seed"
        live = None
        if key == "xai" and xai_live.get("ok"):
            live = xai_live.get("usd")
            remaining_usd = live
            status = "live"
        elif acc.get("kind") == "percent_pool" and used_pct is not None:
            remaining_pct = max(0, 100 - int(used_pct))
            status = "seeded"
        elif starting is not None:
            remaining_usd = round(float(starting), 4)
            status = "seeded"
        out[key] = {
            "label": acc.get("label") or key,
            "kind": acc.get("kind"),
            "spend_allowed": bool(acc.get("spend_allowed")),
            "key_present": _key_present(key),
            "starting_usd": starting,
            "used_pct": used_pct,
            "remaining_pct": remaining_pct,
            "remaining_usd": remaining_usd,
            "live_usd": live,
            "status": status,
        }
    return out


def _write_last(payload: dict) -> None:
    path = _last_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def refresh(*, source: str = "daily") -> dict:
    """Seed locally. HTTP only when RR_API_PRICES=1."""
    st = flags()
    seeded = _seed_prices(source)
    out: dict[str, Any] = {
        "ok": True,
        "source": source,
        "at": datetime.now(HST).isoformat(),
        "seeded_rows": seeded,
        "fetches": [],
        "live_rows": 0,
        "http": False,
    }
    if not prices_gate_open():
        out["detail"] = "rr_api_prices_off"
        out["balances"] = _balance_block(st, probe=False)
        _write_last(out)
        return out
    if not st.get("capture_enabled"):
        out["detail"] = "capture_off"
        _write_last(out)
        return out
    out["http"] = True
    conn = connect()
    live_n = 0
    try:
        for src in SOURCES:
            url, err, body = _fetch(src["url"], src.get("alt"))
            sha = hashlib.sha256(body).hexdigest()[:16] if body else ""
            ok = bool(body) and not err
            conn.execute(
                """INSERT INTO fetches (at, source, vendor, url, ok, bytes, sha, detail)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (_now(), source, src["vendor"], url, int(ok), len(body), sha, err[:200]),
            )
            parsed = _parse_live(src["vendor"], body.decode("utf-8", "replace")) if body else []
            for row in parsed:
                _insert_price(conn, source, row, live=1)
                live_n += 1
            out["fetches"].append(
                {"vendor": src["vendor"], "url": url, "ok": ok, "bytes": len(body), "parsed": len(parsed), "detail": err or "ok"}
            )
        conn.commit()
    finally:
        conn.close()
    out["live_rows"] = live_n
    out["balances"] = _balance_block(st, probe=bool(st.get("spend_master")))
    _write_last(out)
    return out
