# ==============================================================================
# FILE: Website/scripts/analytics_pull.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Mirror Mainland Two site analytics JSON onto the desk bank for reports.

  python3 analytics_pull.py              # today (HST)
  python3 analytics_pull.py 2026-10-01   # one day
  python3 analytics_pull.py --force      # ignore freshness window

Prefers Database Logs/Website/analytics/pull-from-api.sh. Falls back to a
stdlib HTTPS GET of https://api.rootrecord.cloud/api/analytics/daily. Writes
daily/YYYY-MM-DD.json plus analytics-last.json. Does not invent pageviews.
Does not send, spend, or publish.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
BANK = DB / "Logs" / "Website" / "analytics"  # info: set BANK
DAILY = BANK / "daily"  # info: set DAILY
LAST = BANK / "analytics-last.json"  # info: set LAST
WEBSITE_LAST = DB / "Website" / "analytics" / "daily-last.json"  # info: set WEBSITE_LAST
PULL_SH = BANK / "pull-from-api.sh"  # info: set PULL_SH
API = "https://api.rootrecord.cloud/api/analytics/daily"  # info: set API
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
FRESH_S = 900  # info: set FRESH_S (15 min, matches ML2 analytics timer)
TIMEOUT_S = 20  # info: set TIMEOUT_S


# ====================================================
# SECTION: function today_hst
# What it does: Return today's YYYY-MM-DD in Pacific/Honolulu. Does not call the network.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def today_hst() -> str:  # info: def today_hst
    return datetime.now(HST).date().isoformat()  # info: return datetime . now ( HST ) . date ( ) . isoformat ( )


# ====================================================
# SECTION: function day_path
# What it does: Path for one day's mirrored JSON under Logs/Website/analytics/daily/.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def day_path(day: str) -> Path:  # info: def day_path
    return DAILY / f"{day}.json"  # info: return DAILY / f"{day}.json"


# ====================================================
# SECTION: function _age_s
# What it does: File age in seconds, or None when missing. Does not read contents.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _age_s(path: Path) -> float | None:  # info: def _age_s
    if not path.is_file():  # info: if not path . is_file ( ) :
        return None  # info: return None
    return max(0.0, datetime.now().timestamp() - path.stat().st_mtime)  # info: return max ( 0.0 , datetime . now ( ) . timestamp ( ) - path . stat ( ) . st_mtime )


# ====================================================
# SECTION: function _write_doc
# What it does: Write measured daily JSON to daily/<day>.json, analytics-last.json, and Website/analytics/daily-last.json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_doc(day: str, raw: bytes) -> Path:  # info: def _write_doc
    DAILY.mkdir(parents=True, exist_ok=True)  # info: DAILY . mkdir ( parents = True , exist_ok = True )
    WEBSITE_LAST.parent.mkdir(parents=True, exist_ok=True)  # info: WEBSITE_LAST . parent . mkdir ( parents = True , exist_ok = True )
    target = day_path(day)  # info: set target
    tmp = target.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_bytes(raw)  # info: tmp . write_bytes ( raw )
    tmp.replace(target)  # info: tmp . replace ( target )
    LAST.write_bytes(raw)  # info: LAST . write_bytes ( raw )
    WEBSITE_LAST.write_bytes(raw)  # info: WEBSITE_LAST . write_bytes ( raw )
    return target  # info: return target


# ====================================================
# SECTION: function _pull_via_shell
# What it does: Run pull-from-api.sh for one day when the bank script exists. Returns True on success.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pull_via_shell(day: str) -> bool:  # info: def _pull_via_shell
    if not PULL_SH.is_file():  # info: if not PULL_SH . is_file ( ) :
        return False  # info: return False
    try:  # info: try :
        proc = subprocess.run(  # info: set proc
            ["bash", str(PULL_SH), day],  # info: [ "bash" , str ( PULL_SH ) , day ] ,
            cwd=str(BANK),  # info: cwd = str ( BANK ) ,
            capture_output=True,  # info: capture_output = True ,
            text=True,  # info: text = True ,
            timeout=TIMEOUT_S + 5,  # info: timeout = TIMEOUT_S + 5 ,
            check=False,  # info: check = False ,
        )  # info: )
    except (OSError, subprocess.TimeoutExpired):  # info: except ( OSError , subprocess . TimeoutExpired ) :
        return False  # info: return False
    if proc.returncode != 0:  # info: if proc . returncode != 0 :
        return False  # info: return False
    path = day_path(day)  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return False  # info: return False
    raw = path.read_bytes()  # info: set raw
    LAST.write_bytes(raw)  # info: LAST . write_bytes ( raw )
    WEBSITE_LAST.parent.mkdir(parents=True, exist_ok=True)  # info: WEBSITE_LAST . parent . mkdir ( parents = True , exist_ok = True )
    WEBSITE_LAST.write_bytes(raw)  # info: WEBSITE_LAST . write_bytes ( raw )
    return True  # info: return True


# ====================================================
# SECTION: function _pull_via_http
# What it does: Stdlib GET of the public analytics daily API into the desk bank. No auth.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pull_via_http(day: str) -> bool:  # info: def _pull_via_http
    url = f"{API}?date={day}"  # info: set url
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")  # info: set req
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # info: with urllib . request . urlopen ( req , timeout = TIMEOUT_S ) as resp :
            raw = resp.read()  # info: set raw
    except (urllib.error.URLError, TimeoutError, OSError):  # info: except ( urllib . error . URLError , TimeoutError , OSError ) :
        return False  # info: return False
    try:  # info: try :
        doc = json.loads(raw.decode("utf-8"))  # info: set doc
    except (UnicodeDecodeError, json.JSONDecodeError):  # info: except ( UnicodeDecodeError , json . JSONDecodeError ) :
        return False  # info: return False
    if not isinstance(doc, dict) or not doc.get("ok"):  # info: if not isinstance ( doc , dict ) or not doc . get ( "ok" ) :
        return False  # info: return False
    _write_doc(day, raw if raw.endswith(b"\n") else raw + b"\n")  # info: call _write_doc
    return True  # info: return True


# ====================================================
# SECTION: function pull
# What it does: Refresh one day's analytics mirror when missing or older than FRESH_S. Prefer pull-from-api.sh.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pull(day: str | None = None, *, force: bool = False) -> dict[str, Any]:  # info: def pull
    day = day or today_hst()  # info: set day
    path = day_path(day)  # info: set path
    age = _age_s(path)  # info: set age
    if path.is_file() and age is not None and age < FRESH_S and not force:  # info: if path . is_file ( ) and age is not None and age < FRESH_S and not force :
        try:  # info: try :
            doc = json.loads(path.read_text(encoding="utf-8"))  # info: set doc
        except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError ) :
            doc = {}  # info: set doc
        return {"ok": bool(isinstance(doc, dict) and doc.get("ok")), "day": day, "path": str(path), "refreshed": False, "age_s": age}  # info: return fresh-enough result
    refreshed = _pull_via_shell(day) or _pull_via_http(day)  # info: set refreshed
    if not refreshed:  # info: if not refreshed :
        return {"ok": False, "day": day, "path": str(path), "refreshed": False, "detail": "pull_failed"}  # info: return pull_failed
    return {"ok": True, "day": day, "path": str(path), "refreshed": True, "age_s": _age_s(path)}  # info: return success


# ====================================================
# SECTION: function load_daily
# What it does: Load one day's analytics dict from the desk bank; optionally refresh first. Returns {} when missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_daily(day: str | None = None, *, refresh: bool = True) -> dict[str, Any]:  # info: def load_daily
    day = day or today_hst()  # info: set day
    if refresh:  # info: if refresh :
        pull(day, force=False)  # info: call pull
    path = day_path(day)  # info: set path
    if not path.is_file() and LAST.is_file():  # info: if not path . is_file ( ) and LAST . is_file ( ) :
        path = LAST  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return {}  # info: return {}
    try:  # info: try :
        doc = json.loads(path.read_text(encoding="utf-8"))  # info: set doc
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError ) :
        return {}  # info: return {}
    return doc if isinstance(doc, dict) else {}  # info: return doc if isinstance ( doc , dict ) else {}


# ====================================================
# SECTION: function main
# What it does: CLI entry: pull today's (or argv day) analytics mirror and print a one-line status. Exit 0/1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(sys.argv[1:] if argv is None else argv)  # info: set args
    force = False  # info: set force
    if "--force" in args:  # info: if "--force" in args :
        force = True  # info: set force
        args = [a for a in args if a != "--force"]  # info: set args
    day = args[0] if args else today_hst()  # info: set day
    result = pull(day, force=force)  # info: set result
    if result.get("ok"):  # info: if result . get ( "ok" ) :
        flag = "refreshed" if result.get("refreshed") else "fresh"  # info: set flag
        print(f"analytics {day} {flag} -> {result.get('path')}")  # info: call print
        return 0  # info: return 0
    print(f"analytics {day} {result.get('detail') or 'fail'}", file=sys.stderr)  # info: call print on stderr
    return 1  # info: return 1


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
