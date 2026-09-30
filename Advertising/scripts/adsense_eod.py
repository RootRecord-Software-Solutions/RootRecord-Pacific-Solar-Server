# ==============================================================================
# FILE: Advertising/scripts/adsense_eod.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""AdSense end-of-day snapshot. Stdlib only. Never prints secrets.

  python3 adsense_eod.py

With no client id, secret, or refresh token, writes ok=false detail=not_configured
and exits 0. It does not call Google. A failed live pull keeps the previous ok file.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
import urllib.error  # info: import urllib . error
import urllib.parse  # info: import urllib . parse
import urllib.request  # info: import urllib . request
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
if str(ROOT) not in sys.path:  # info: if str ( ROOT ) not in sys
    sys.path.insert(0, str(ROOT))  # info: sys . path . insert ( 0 ,

from lib.envload import adsense_account_name, adsense_credentials, adsense_currency  # noqa: E402

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE
SNAPSHOT = DATABASE / "Advertising" / "adsense-last.json"  # info: set SNAPSHOT
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
TOKEN_URI = "https://oauth2.googleapis.com/token"  # info: set TOKEN_URI
API = "https://adsense.googleapis.com/v2"  # info: set API
DAYS = 7  # info: set DAYS
TIMEOUT_S = 30  # info: set TIMEOUT_S
# ====================================================
# SECTION: METRICS
# What it does: Set METRICS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
METRICS = (  # info: set METRICS
    "PAGE_VIEWS",  # info: "PAGE_VIEWS" ,
    "CLICKS",  # info: "CLICKS" ,
    "ESTIMATED_EARNINGS",  # info: "ESTIMATED_EARNINGS" ,
    "PAGE_VIEWS_RPM",  # info: "PAGE_VIEWS_RPM" ,
    "IMPRESSIONS",  # info: "IMPRESSIONS" ,
)  # info: )


# ====================================================
# SECTION: function _write
# What it does:  write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(snap: dict[str, Any]) -> None:  # info: def _write
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)  # info: SNAPSHOT . parent . mkdir ( parents =
    tmp = SNAPSHOT.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(SNAPSHOT)  # info: tmp . replace ( SNAPSHOT )


# ====================================================
# SECTION: function _read
# What it does:  read.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read() -> dict[str, Any]:  # info: def _read
    if not SNAPSHOT.is_file():  # info: if not SNAPSHOT . is_file ( ) :
        return {}  # info: return { }
    try:  # info: try :
        raw = json.loads(SNAPSHOT.read_text(encoding="utf-8"))  # info: set raw
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {}  # info: return { }
    return raw if isinstance(raw, dict) else {}  # info: return raw if isinstance ( raw , dict


# ====================================================
# SECTION: function _stamp
# What it does:  stamp.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _stamp() -> str:  # info: def _stamp
    return datetime.now(HST).isoformat(timespec="seconds")  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function _not_configured
# What it does:  not configured.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _not_configured() -> dict[str, Any]:  # info: def _not_configured
    out = {"ok": False, "detail": "not_configured", "kind": "eod", "generated": _stamp()}  # info: set out
    _write(out)  # info: call _write
    return out  # info: return out


# ====================================================
# SECTION: function _account
# What it does:  account.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _account(name: str) -> str:  # info: def _account
    name = name.strip()  # info: set name
    if not name:  # info: if not name :
        return ""  # info: return ""
    return name if name.startswith("accounts/") else f"accounts/{name}"  # info: return name if name . startswith ( "accounts/"


# ====================================================
# SECTION: function _refresh
# What it does:  refresh.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _refresh(client_id: str, client_secret: str, refresh_token: str) -> str:  # info: def _refresh
    body = urllib.parse.urlencode(  # info: set body
        {  # info: {
            "client_id": client_id,  # info: "client_id" : client_id ,
            "client_secret": client_secret,  # info: "client_secret" : client_secret ,
            "refresh_token": refresh_token,  # info: "refresh_token" : refresh_token ,
            "grant_type": "refresh_token",  # info: "grant_type" : "refresh_token" ,
        }  # info: }
    ).encode()  # info: ) . encode ( )
    req = urllib.request.Request(  # info: set req
        TOKEN_URI,  # info: TOKEN_URI ,
        data=body,  # info: set data
        method="POST",  # info: set method
        headers={"Content-Type": "application/x-www-form-urlencoded"},  # info: set headers
    )  # info: )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # info: with urllib . request . urlopen ( req
            tok = json.loads(resp.read().decode("utf-8"))  # info: set tok
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        raise RuntimeError(f"adsense token {exc.code}") from None  # info: raise RuntimeError ( f" adsense token { exc .
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):  # info: except ( urllib . error . URLError ,
        raise RuntimeError("adsense token failed") from None  # info: raise RuntimeError ( "adsense token failed" ) from None
    access = tok.get("access_token") if isinstance(tok, dict) else None  # info: set access
    if not isinstance(access, str) or not access:  # info: if not isinstance ( access , str )
        raise RuntimeError("adsense token missing")  # info: raise RuntimeError ( "adsense token missing" )
    return access  # info: return access


# ====================================================
# SECTION: function _get
# What it does:  get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(url: str, access: str) -> dict[str, Any]:  # info: def _get
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + access})  # info: set req
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # info: with urllib . request . urlopen ( req
            body = json.loads(resp.read().decode("utf-8"))  # info: set body
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        raise RuntimeError(f"adsense {exc.code}") from None  # info: raise RuntimeError ( f" adsense { exc .
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):  # info: except ( urllib . error . URLError ,
        raise RuntimeError("adsense request failed") from None  # info: raise RuntimeError ( "adsense request failed" ) from None
    if not isinstance(body, dict):  # info: if not isinstance ( body , dict )
        raise RuntimeError("adsense bad body")  # info: raise RuntimeError ( "adsense bad body" )
    return body  # info: return body


# ====================================================
# SECTION: function _resolve_account
# What it does:  resolve account.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _resolve_account(access: str) -> str:  # info: def _resolve_account
    named = _account(adsense_account_name())  # info: set named
    if named:  # info: if named :
        return named  # info: return named
    payload = _get(f"{API}/accounts", access)  # info: set payload
    rows = payload.get("accounts") or []  # info: set rows
    if not isinstance(rows, list) or not rows:  # info: if not isinstance ( rows , list )
        raise RuntimeError("adsense no account")  # info: raise RuntimeError ( "adsense no account" )
    first = rows[0] if isinstance(rows[0], dict) else {}  # info: set first
    name = _account(str(first.get("name") or ""))  # info: set name
    if not name:  # info: if not name :
        raise RuntimeError("adsense account missing name")  # info: raise RuntimeError ( "adsense account missing name" )
    return name  # info: return name


# ====================================================
# SECTION: function _cell_map
# What it does:  cell map.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _cell_map(headers: list[Any], row: dict[str, Any]) -> dict[str, str]:  # info: def _cell_map
    cells = row.get("cells") or []  # info: set cells
    out: dict[str, str] = {}  # info: set out
    for i, header in enumerate(headers):  # info: for i , header in enumerate ( headers
        if not isinstance(header, dict):  # info: if not isinstance ( header , dict )
            continue  # info: continue
        key = str(header.get("name") or header.get("type") or f"c{i}")  # info: set key
        val = ""  # info: set val
        if isinstance(cells, list) and i < len(cells):  # info: if isinstance ( cells , list ) and
            cell = cells[i]  # info: set cell
            val = str(cell.get("value") if isinstance(cell, dict) else cell or "")  # info: set val
        out[key] = val  # info: out [ key ] = val
    return out  # info: return out


# ====================================================
# SECTION: function _parse
# What it does:  parse.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _parse(report: dict[str, Any]) -> dict[str, Any]:  # info: def _parse
    headers = report.get("headers") or []  # info: set headers
    if not isinstance(headers, list):  # info: if not isinstance ( headers , list )
        headers = []  # info: set headers
    rows_out = []  # info: set rows_out
    for row in report.get("rows") or []:  # info: for row in report . get ( "rows"
        if isinstance(row, dict):  # info: if isinstance ( row , dict ) :
            rows_out.append(_cell_map(headers, row))  # info: rows_out . append ( _cell_map ( headers ,
    totals: dict[str, str] = {}  # info: set totals
    if isinstance(report.get("totals"), dict):  # info: if isinstance ( report . get ( "totals"
        totals = _cell_map(headers, report["totals"])  # info: set totals
    names = [h.get("name") for h in headers if isinstance(h, dict)]  # info: set names
    return {"headers": names, "rows": rows_out, "totals": totals}  # info: return { "headers" : names , "rows" :


# ====================================================
# SECTION: function _live
# What it does:  live.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _live(client_id: str, client_secret: str, refresh_token: str) -> dict[str, Any]:  # info: def _live
    access = _refresh(client_id, client_secret, refresh_token)  # info: set access
    end = datetime.now(HST).date()  # info: set end
    start = end - timedelta(days=DAYS - 1)  # info: set start
    account = _resolve_account(access)  # info: set account
    query = urllib.parse.urlencode(  # info: set query
        [  # info: [
            ("dateRange", "CUSTOM"),  # info: call (
            ("startDate.year", str(start.year)),  # info: call (
            ("startDate.month", str(start.month)),  # info: call (
            ("startDate.day", str(start.day)),  # info: call (
            ("endDate.year", str(end.year)),  # info: call (
            ("endDate.month", str(end.month)),  # info: call (
            ("endDate.day", str(end.day)),  # info: call (
            *[("metrics", metric) for metric in METRICS],  # info: call *
            ("dimensions", "DATE"),  # info: call (
            ("orderBy", "+DATE"),  # info: call (
            ("currencyCode", adsense_currency()),  # info: call (
        ]  # info: ]
    )  # info: )
    raw = _get(f"{API}/{account}/reports:generate?{query}", access)  # info: set raw
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "kind": "eod",  # info: "kind" : "eod" ,
        "generated": _stamp(),  # info: "generated" : _stamp ( ) ,
        "start": start.isoformat(),  # info: "start" : start . isoformat ( ) ,
        "end": end.isoformat(),  # info: "end" : end . isoformat ( ) ,
        "account": account,  # info: "account" : account ,
        "report": _parse(raw),  # info: "report" : _parse ( raw ) ,
    }  # info: }


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run() -> dict[str, Any]:  # info: def run
    client_id, client_secret, refresh_token = adsense_credentials()  # info: client_id , client_secret , refresh_token = adsense_credentials (
    if not client_id or not client_secret or not refresh_token:  # info: if not client_id or not client_secret or not
        return _not_configured()  # info: return _not_configured ( )
    existing = _read()  # info: set existing
    try:  # info: try :
        snap = _live(client_id, client_secret, refresh_token)  # info: set snap
    except RuntimeError:  # info: except RuntimeError :
        if existing.get("ok"):  # info: if existing . get ( "ok" ) :
            return existing  # info: return existing
        out = {"ok": False, "detail": "poll_failed", "kind": "eod", "generated": _stamp()}  # info: set out
        _write(out)  # info: call _write
        return out  # info: return out
    _write(snap)  # info: call _write
    return snap  # info: return snap


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    snap = run()  # info: set snap
    detail = "ok" if snap.get("ok") else snap.get("detail") or "fail"  # info: set detail
    print(f"adsense {detail}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
