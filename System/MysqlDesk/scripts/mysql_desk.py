#!/usr/bin/env python3
"""Read-only MySQL desk facts (package MysqlDesk).

  python3 mysql_desk.py facts

Missing credentials return before any driver import or socket.
A live read runs only when ROOTMC_CORE_MYSQL_* (preferred) or AVA_MYSQL_*
(fallback) is complete in master-key.env. No pool, no INSERT/UPDATE/DELETE,
no cron log. Does not post, play audio, or edit jobs.py.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
DATA = DB / "System" / "MysqlDesk"
LAST = DATA / "facts-last.json"
LOG_DIR = DB / "Logs" / "System" / "MysqlDesk"
LOG_FILE = LOG_DIR / "mysql-desk.log"

_AGG = """
SELECT
  COUNT(*) AS wallets,
  COALESCE(SUM(balance), 0) AS total_gold,
  COALESCE(SUM(CASE WHEN balance > 0 THEN balance ELSE 0 END), 0) AS positive_gold,
  COALESCE(AVG(balance), 0) AS avg_gold,
  COALESCE(MAX(balance), 0) AS max_gold
FROM root_economy_balances
"""
_TOP = """
SELECT minecraft_username AS name, balance
FROM root_economy_balances
WHERE balance IS NOT NULL
  AND minecraft_username IS NOT NULL
  AND minecraft_username <> ''
  AND LOWER(minecraft_username) NOT IN ('player', 'unknown', 'null')
ORDER BY balance DESC
LIMIT 5
"""
_TOP_THIN = """
SELECT minecraft_username AS name, balance
FROM root_economy_balances
WHERE balance IS NOT NULL
ORDER BY balance DESC
LIMIT 5
"""
_BONDS = """
SELECT COUNT(*) AS c,
       COALESCE(SUM(CASE WHEN redeemed_at IS NULL THEN principal ELSE 0 END), 0) AS principal
FROM root_bonds
"""
_POOLS = """
SELECT category, label, amount_g
FROM root_list_totals
WHERE scope = 'claims' AND group_key = 'pools'
ORDER BY category
"""


def _envload():
    path = Path(__file__).resolve().parents[1] / "lib" / "envload.py"
    spec = importlib.util.spec_from_file_location("MysqlDesk.envload", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"MysqlDesk envload missing: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _empty() -> dict:
    return {
        "ok": False,
        "local_3306": False,
        "shockbyte": False,
        "source": None,
        "error": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "wallets": 0,
        "total_gold": 0.0,
        "positive_gold": 0.0,
        "avg_gold": 0.0,
        "max_gold": 0.0,
        "bonds_count": 0,
        "bonds_principal": 0.0,
        "pools": {},
        "top": [],
    }


def _num(value, *, whole: bool = False):
    if whole:
        return int(value or 0)
    return float(value or 0)


def _apply(conn, out: dict, *, shock: bool) -> None:
    with conn.cursor() as cur:
        cur.execute("SET SESSION TRANSACTION READ ONLY")
        cur.execute("SELECT 1")
        cur.fetchone()
    if shock:
        out["shockbyte"] = True
    else:
        out["local_3306"] = True
    with conn.cursor() as cur:
        cur.execute(_AGG)
        agg_rows = list(cur.fetchall())
    if not agg_rows:
        out["error"] = "no-rows"
        return
    agg = agg_rows[0]
    out["ok"] = True
    out["source"] = "root_economy_balances"
    out["error"] = None
    out["wallets"] = _num(agg.get("wallets"), whole=True)
    out["total_gold"] = _num(agg.get("total_gold"))
    out["positive_gold"] = _num(agg.get("positive_gold"))
    out["avg_gold"] = _num(agg.get("avg_gold"))
    out["max_gold"] = _num(agg.get("max_gold"))
    with conn.cursor() as cur:
        cur.execute(_TOP)
        top = list(cur.fetchall())
        if len(top) < 3:
            cur.execute(_TOP_THIN)
            top = list(cur.fetchall())
        cur.execute(_BONDS)
        bonds = list(cur.fetchall())
        cur.execute(_POOLS)
        pools = list(cur.fetchall())
    out["top"] = [
        {"name": str(row.get("name") or "?"), "balance": _num(row.get("balance"))}
        for row in top
    ]
    if bonds:
        out["bonds_count"] = _num(bonds[0].get("c"), whole=True)
        out["bonds_principal"] = _num(bonds[0].get("principal"))
    out["pools"] = {
        str(row.get("category") or ""): {
            "label": str(row.get("label") or row.get("category") or ""),
            "amount_g": _num(row.get("amount_g")),
        }
        for row in pools
        if row.get("category")
    }


def _connect(cfg: dict):
    import pymysql
    from pymysql.cursors import DictCursor

    return pymysql.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        connect_timeout=8,
        cursorclass=DictCursor,
        autocommit=True,
    )


def facts() -> dict:
    """Aggregates only. Returns before importing PyMySQL when no target is set."""
    envload = _envload()
    shock = envload.configured("ROOTMC_CORE_MYSQL")
    local = envload.configured("AVA_MYSQL")
    out = _empty()
    if not shock and not local:
        out["error"] = "missing-credentials"
        return out
    last = "unavailable"
    for is_shock, cfg in ((True, shock), (False, local)):
        if not cfg:
            continue
        conn = None
        try:
            conn = _connect(cfg)
            _apply(conn, out, shock=is_shock)
            if out["ok"]:
                return out
            if out["error"] == "no-rows":
                return out
        except Exception as exc:
            last = type(exc).__name__
            out["error"] = last
            out["ok"] = False
        finally:
            if conn is not None:
                conn.close()
    if not out["error"]:
        out["error"] = last
    return out


def _write(snap: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    LAST.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    err = snap.get("error") or ""
    src = snap.get("source") or ""
    stamp = datetime.now().isoformat(timespec="seconds")
    line = f"{stamp}\tfacts\tok={bool(snap.get('ok'))}\tsource={src}\terror={err}\n"
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    if args[1:] != ["facts"]:
        print("usage: mysql_desk.py facts", file=sys.stderr)
        return 2
    snap = facts()
    _write(snap)
    print(json.dumps(snap))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
