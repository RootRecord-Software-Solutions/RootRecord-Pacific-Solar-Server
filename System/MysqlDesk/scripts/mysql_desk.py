# ==============================================================================
# FILE: System/MysqlDesk/scripts/mysql_desk.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Read-only MySQL desk facts (package MysqlDesk).

  python3 mysql_desk.py facts

Missing credentials return before any driver import or socket.
A live read runs only when ROOTMC_CORE_MYSQL_* (preferred) or AVA_MYSQL_*
(fallback) is complete in master-key.env. No pool, no INSERT/UPDATE/DELETE,
no cron log. Does not post, play audio, or edit jobs.py.
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
DATA = DB / "System" / "MysqlDesk"  # info: set DATA
LAST = DATA / "facts-last.json"  # info: set LAST
LOG_DIR = DB / "Logs" / "System" / "MysqlDesk"  # info: set LOG_DIR
LOG_FILE = LOG_DIR / "mysql-desk.log"  # info: set LOG_FILE

# ====================================================
# SECTION: _AGG
# What it does: Set _AGG.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_AGG = """
SELECT
  COUNT(*) AS wallets,
  COALESCE(SUM(balance), 0) AS total_gold,
  COALESCE(SUM(CASE WHEN balance > 0 THEN balance ELSE 0 END), 0) AS positive_gold,
  COALESCE(AVG(balance), 0) AS avg_gold,
  COALESCE(MAX(balance), 0) AS max_gold
FROM root_economy_balances
"""
# ====================================================
# SECTION: _TOP
# What it does: Set _TOP.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
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
# ====================================================
# SECTION: _TOP_THIN
# What it does: Set _TOP_THIN.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_TOP_THIN = """
SELECT minecraft_username AS name, balance
FROM root_economy_balances
WHERE balance IS NOT NULL
ORDER BY balance DESC
LIMIT 5
"""
# ====================================================
# SECTION: _BONDS
# What it does: Set _BONDS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_BONDS = """
SELECT COUNT(*) AS c,
       COALESCE(SUM(CASE WHEN redeemed_at IS NULL THEN principal ELSE 0 END), 0) AS principal
FROM root_bonds
"""
# ====================================================
# SECTION: _POOLS
# What it does: Set _POOLS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_POOLS = """
SELECT category, label, amount_g
FROM root_list_totals
WHERE scope = 'claims' AND group_key = 'pools'
ORDER BY category
"""


# ====================================================
# SECTION: function _envload
# What it does:  envload.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _envload():  # info: def _envload
    path = Path(__file__).resolve().parents[1] / "lib" / "envload.py"  # info: set path
    spec = importlib.util.spec_from_file_location("MysqlDesk.envload", path)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader
        raise ImportError(f"MysqlDesk envload missing: {path}")  # info: raise ImportError ( f" MysqlDesk envload missing: { path }
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    return mod  # info: return mod


# ====================================================
# SECTION: function _empty
# What it does:  empty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _empty() -> dict:  # info: def _empty
    return {  # info: return {
        "ok": False,  # info: "ok" : False ,
        "local_3306": False,  # info: "local_3306" : False ,
        "shockbyte": False,  # info: "shockbyte" : False ,
        "source": None,  # info: "source" : None ,
        "error": None,  # info: "error" : None ,
        "updated_at": datetime.now(timezone.utc).isoformat(),  # info: "updated_at" : datetime . now ( timezone .
        "wallets": 0,  # info: "wallets" : 0 ,
        "total_gold": 0.0,  # info: "total_gold" : 0.0 ,
        "positive_gold": 0.0,  # info: "positive_gold" : 0.0 ,
        "avg_gold": 0.0,  # info: "avg_gold" : 0.0 ,
        "max_gold": 0.0,  # info: "max_gold" : 0.0 ,
        "bonds_count": 0,  # info: "bonds_count" : 0 ,
        "bonds_principal": 0.0,  # info: "bonds_principal" : 0.0 ,
        "pools": {},  # info: "pools" : { } ,
        "top": [],  # info: "top" : [ ] ,
    }  # info: }


# ====================================================
# SECTION: function _num
# What it does:  num.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _num(value, *, whole: bool = False):  # info: def _num
    if whole:  # info: if whole :
        return int(value or 0)  # info: return int ( value or 0 )
    return float(value or 0)  # info: return float ( value or 0 )


# ====================================================
# SECTION: function _apply
# What it does:  apply.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _apply(conn, out: dict, *, shock: bool) -> None:  # info: def _apply
    with conn.cursor() as cur:  # info: with conn . cursor ( ) as cur
        cur.execute("SET SESSION TRANSACTION READ ONLY")  # info: cur . execute ( "SET SESSION TRANSACTION READ ONLY" )
        cur.execute("SELECT 1")  # info: cur . execute ( "SELECT 1" )
        cur.fetchone()  # info: cur . fetchone ( )
    if shock:  # info: if shock :
        out["shockbyte"] = True  # info: out [ "shockbyte" ] = True
    else:  # info: else :
        out["local_3306"] = True  # info: out [ "local_3306" ] = True
    with conn.cursor() as cur:  # info: with conn . cursor ( ) as cur
        cur.execute(_AGG)  # info: cur . execute ( _AGG )
        agg_rows = list(cur.fetchall())  # info: set agg_rows
    if not agg_rows:  # info: if not agg_rows :
        out["error"] = "no-rows"  # info: out [ "error" ] = "no-rows"
        return  # info: return
    agg = agg_rows[0]  # info: set agg
    out["ok"] = True  # info: out [ "ok" ] = True
    out["source"] = "root_economy_balances"  # info: out [ "source" ] = "root_economy_balances"
    out["error"] = None  # info: out [ "error" ] = None
    out["wallets"] = _num(agg.get("wallets"), whole=True)  # info: out [ "wallets" ] = _num ( agg
    out["total_gold"] = _num(agg.get("total_gold"))  # info: out [ "total_gold" ] = _num ( agg
    out["positive_gold"] = _num(agg.get("positive_gold"))  # info: out [ "positive_gold" ] = _num ( agg
    out["avg_gold"] = _num(agg.get("avg_gold"))  # info: out [ "avg_gold" ] = _num ( agg
    out["max_gold"] = _num(agg.get("max_gold"))  # info: out [ "max_gold" ] = _num ( agg
    with conn.cursor() as cur:  # info: with conn . cursor ( ) as cur
        cur.execute(_TOP)  # info: cur . execute ( _TOP )
        top = list(cur.fetchall())  # info: set top
        if len(top) < 3:  # info: if len ( top ) < 3 :
            cur.execute(_TOP_THIN)  # info: cur . execute ( _TOP_THIN )
            top = list(cur.fetchall())  # info: set top
        cur.execute(_BONDS)  # info: cur . execute ( _BONDS )
        bonds = list(cur.fetchall())  # info: set bonds
        cur.execute(_POOLS)  # info: cur . execute ( _POOLS )
        pools = list(cur.fetchall())  # info: set pools
    out["top"] = [  # info: out [ "top" ] = [
        {"name": str(row.get("name") or "?"), "balance": _num(row.get("balance"))}  # info: { "name" : str ( row . get
        for row in top  # info: for row in top
    ]  # info: ]
    if bonds:  # info: if bonds :
        out["bonds_count"] = _num(bonds[0].get("c"), whole=True)  # info: out [ "bonds_count" ] = _num ( bonds
        out["bonds_principal"] = _num(bonds[0].get("principal"))  # info: out [ "bonds_principal" ] = _num ( bonds
    out["pools"] = {  # info: out [ "pools" ] = {
        str(row.get("category") or ""): {  # info: call str
            "label": str(row.get("label") or row.get("category") or ""),  # info: "label" : str ( row . get (
            "amount_g": _num(row.get("amount_g")),  # info: "amount_g" : _num ( row . get (
        }  # info: }
        for row in pools  # info: for row in pools
        if row.get("category")  # info: if row . get ( "category" )
    }  # info: }


# ====================================================
# SECTION: function _connect
# What it does:  connect.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _connect(cfg: dict):  # info: def _connect
    import pymysql  # info: import pymysql
    from pymysql.cursors import DictCursor  # info: from pymysql . cursors import DictCursor

    return pymysql.connect(  # info: return pymysql . connect (
        host=cfg["host"],  # info: set host
        port=int(cfg["port"]),  # info: set port
        user=cfg["user"],  # info: set user
        password=cfg["password"],  # info: set password
        database=cfg["database"],  # info: set database
        charset="utf8mb4",  # info: set charset
        connect_timeout=8,  # info: set connect_timeout
        cursorclass=DictCursor,  # info: set cursorclass
        autocommit=True,  # info: set autocommit
    )  # info: )


# ====================================================
# SECTION: function facts
# What it does: Aggregates only. Returns before importing PyMySQL when no target is set.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def facts() -> dict:  # info: def facts
    """Aggregates only. Returns before importing PyMySQL when no target is set."""  # info: """Aggregates only. Returns before importing PyMySQL when no target is set."""
    envload = _envload()  # info: set envload
    shock = envload.configured("ROOTMC_CORE_MYSQL")  # info: set shock
    local = envload.configured("AVA_MYSQL")  # info: set local
    out = _empty()  # info: set out
    if not shock and not local:  # info: if not shock and not local :
        out["error"] = "missing-credentials"  # info: out [ "error" ] = "missing-credentials"
        return out  # info: return out
    last = "unavailable"  # info: set last
    for is_shock, cfg in ((True, shock), (False, local)):  # info: for is_shock , cfg in ( ( True
        if not cfg:  # info: if not cfg :
            continue  # info: continue
        conn = None  # info: set conn
        try:  # info: try :
            conn = _connect(cfg)  # info: set conn
            _apply(conn, out, shock=is_shock)  # info: call _apply
            if out["ok"]:  # info: if out [ "ok" ] :
                return out  # info: return out
            if out["error"] == "no-rows":  # info: if out [ "error" ] == "no-rows" :
                return out  # info: return out
        except Exception as exc:  # info: except Exception as exc :
            last = type(exc).__name__  # info: set last
            out["error"] = last  # info: out [ "error" ] = last
            out["ok"] = False  # info: out [ "ok" ] = False
        finally:  # info: finally :
            if conn is not None:  # info: if conn is not None :
                conn.close()  # info: conn . close ( )
    if not out["error"]:  # info: if not out [ "error" ] :
        out["error"] = last  # info: out [ "error" ] = last
    return out  # info: return out


# ====================================================
# SECTION: function _write
# What it does:  write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(snap: dict) -> None:  # info: def _write
    DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
    LAST.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")  # info: LAST . write_text ( json . dumps (
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    err = snap.get("error") or ""  # info: set err
    src = snap.get("source") or ""  # info: set src
    stamp = datetime.now().isoformat(timespec="seconds")  # info: set stamp
    line = f"{stamp}\tfacts\tok={bool(snap.get('ok'))}\tsource={src}\terror={err}\n"  # info: set line
    with LOG_FILE.open("a", encoding="utf-8") as fh:  # info: with LOG_FILE . open ( "a" , encoding
        fh.write(line)  # info: fh . write ( line )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(sys.argv if argv is None else argv)  # info: set args
    if args[1:] != ["facts"]:  # info: if args [ 1 : ] != [
        print("usage: mysql_desk.py facts", file=sys.stderr)  # info: call print
        return 2  # info: return 2
    snap = facts()  # info: set snap
    _write(snap)  # info: call _write
    print(json.dumps(snap))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
