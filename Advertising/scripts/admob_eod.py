# ==============================================================================
# FILE: Advertising/scripts/admob_eod.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""AdMob end-of-day snapshot. Stdlib only. Never prints secrets.

  python3 admob_eod.py

With no client id, secret, or refresh token, writes ok=false detail=not_configured
and exits 0. It does not call Google. The AdMob refresh token does not fall back
to the AdSense token. A failed live pull keeps the previous ok file.
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

from lib.envload import admob_account_name, admob_credentials  # noqa: E402

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE
SNAPSHOT = DATABASE / "Advertising" / "admob-last.json"  # info: set SNAPSHOT
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
TOKEN_URI = "https://oauth2.googleapis.com/token"  # info: set TOKEN_URI
API = "https://admob.googleapis.com/v1"  # info: set API
DAYS = 7  # info: set DAYS
TIMEOUT_S = 45  # info: set TIMEOUT_S
# ====================================================
# SECTION: METRICS
# What it does: Set METRICS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
METRICS = (  # info: set METRICS
    "ESTIMATED_EARNINGS",  # info: "ESTIMATED_EARNINGS" ,
    "IMPRESSIONS",  # info: "IMPRESSIONS" ,
    "CLICKS",  # info: "CLICKS" ,
    "AD_REQUESTS",  # info: "AD_REQUESTS" ,
    "MATCHED_REQUESTS",  # info: "MATCHED_REQUESTS" ,
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
        raise RuntimeError(f"admob token {exc.code}") from None  # info: raise RuntimeError ( f" admob token { exc .
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):  # info: except ( urllib . error . URLError ,
        raise RuntimeError("admob token failed") from None  # info: raise RuntimeError ( "admob token failed" ) from None
    access = tok.get("access_token") if isinstance(tok, dict) else None  # info: set access
    if not isinstance(access, str) or not access:  # info: if not isinstance ( access , str )
        raise RuntimeError("admob token missing")  # info: raise RuntimeError ( "admob token missing" )
    return access  # info: return access


# ====================================================
# SECTION: function _request
# What it does:  request.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _request(url: str, access: str, payload: dict[str, Any] | None = None) -> Any:  # info: def _request
    data = None if payload is None else json.dumps(payload).encode()  # info: set data
    headers = {"Authorization": "Bearer " + access}  # info: set headers
    if payload is not None:  # info: if payload is not None :
        headers["Content-Type"] = "application/json"  # info: headers [ "Content-Type" ] = "application/json"
    req = urllib.request.Request(url, data=data, method="POST" if payload is not None else "GET", headers=headers)  # info: set req
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # info: with urllib . request . urlopen ( req
            return json.loads(resp.read().decode("utf-8"))  # info: return json . loads ( resp . read
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        raise RuntimeError(f"admob {exc.code}") from None  # info: raise RuntimeError ( f" admob { exc .
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):  # info: except ( urllib . error . URLError ,
        raise RuntimeError("admob request failed") from None  # info: raise RuntimeError ( "admob request failed" ) from None


# ====================================================
# SECTION: function _resolve_account
# What it does:  resolve account.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _resolve_account(access: str) -> str:  # info: def _resolve_account
    named = _account(admob_account_name())  # info: set named
    if named:  # info: if named :
        return named  # info: return named
    payload = _request(f"{API}/accounts", access)  # info: set payload
    if not isinstance(payload, dict):  # info: if not isinstance ( payload , dict )
        raise RuntimeError("admob no account")  # info: raise RuntimeError ( "admob no account" )
    rows = payload.get("account") or payload.get("accounts") or []  # info: set rows
    if isinstance(rows, dict):  # info: if isinstance ( rows , dict ) :
        rows = [rows]  # info: set rows
    if not isinstance(rows, list) or not rows:  # info: if not isinstance ( rows , list )
        raise RuntimeError("admob no account")  # info: raise RuntimeError ( "admob no account" )
    first = rows[0] if isinstance(rows[0], dict) else {}  # info: set first
    name = _account(str(first.get("name") or ""))  # info: set name
    if not name:  # info: if not name :
        raise RuntimeError("admob account missing name")  # info: raise RuntimeError ( "admob account missing name" )
    return name  # info: return name


# ====================================================
# SECTION: function _metric
# What it does:  metric.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _metric(row: dict[str, Any], key: str) -> str:  # info: def _metric
    cell = (row.get("metricValues") or {}).get(key) or {}  # info: set cell
    if not isinstance(cell, dict):  # info: if not isinstance ( cell , dict )
        return ""  # info: return ""
    if "microsValue" in cell:  # info: if "microsValue" in cell :
        try:  # info: try :
            return f"{int(cell['microsValue']) / 1_000_000:.4f}"  # info: return f" { int ( cell [ 'microsValue'
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            return ""  # info: return ""
    if "integerValue" in cell:  # info: if "integerValue" in cell :
        return str(cell["integerValue"])  # info: return str ( cell [ "integerValue" ] )
    if "doubleValue" in cell:  # info: if "doubleValue" in cell :
        return str(cell["doubleValue"])  # info: return str ( cell [ "doubleValue" ] )
    return ""  # info: return ""


# ====================================================
# SECTION: function _parse
# What it does:  parse.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _parse(stream: list[Any]) -> dict[str, Any]:  # info: def _parse
    rows_out: list[dict[str, str]] = []  # info: set rows_out
    totals: dict[str, str] = {}  # info: set totals
    for item in stream:  # info: for item in stream :
        if not isinstance(item, dict):  # info: if not isinstance ( item , dict )
            continue  # info: continue
        if isinstance(item.get("row"), dict):  # info: if isinstance ( item . get ( "row"
            row = item["row"]  # info: set row
            dims = row.get("dimensionValues") or {}  # info: set dims
            date = ""  # info: set date
            if isinstance(dims, dict) and isinstance(dims.get("DATE"), dict):  # info: if isinstance ( dims , dict ) and
                date = str(dims["DATE"].get("value") or "")  # info: set date
            rows_out.append({"DATE": date, **{key: _metric(row, key) for key in METRICS}})  # info: rows_out . append ( { "DATE" : date
        if isinstance(item.get("total"), dict):  # info: if isinstance ( item . get ( "total"
            tot = item["total"]  # info: set tot
            totals = {key: _metric(tot, key) for key in METRICS}  # info: set totals
    return {"rows": rows_out, "totals": totals}  # info: return { "rows" : rows_out , "totals" :


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
    body = {  # info: set body
        "reportSpec": {  # info: "reportSpec" : {
            "dateRange": {  # info: "dateRange" : {
                "startDate": {"year": start.year, "month": start.month, "day": start.day},  # info: "startDate" : { "year" : start . year
                "endDate": {"year": end.year, "month": end.month, "day": end.day},  # info: "endDate" : { "year" : end . year
            },  # info: } ,
            "dimensions": ["DATE"],  # info: "dimensions" : [ "DATE" ] ,
            "metrics": list(METRICS),  # info: "metrics" : list ( METRICS ) ,
            "sortConditions": [{"dimension": "DATE", "order": "ASCENDING"}],  # info: "sortConditions" : [ { "dimension" : "DATE" ,
        }  # info: }
    }  # info: }
    result = _request(f"{API}/{account}/networkReport:generate", access, body)  # info: set result
    if isinstance(result, list):  # info: if isinstance ( result , list ) :
        stream = result  # info: set stream
    elif isinstance(result, dict):  # info: elif isinstance ( result , dict ) :
        stream = [result]  # info: set stream
    else:  # info: else :
        raise RuntimeError("admob bad body")  # info: raise RuntimeError ( "admob bad body" )
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "kind": "eod",  # info: "kind" : "eod" ,
        "generated": _stamp(),  # info: "generated" : _stamp ( ) ,
        "start": start.isoformat(),  # info: "start" : start . isoformat ( ) ,
        "end": end.isoformat(),  # info: "end" : end . isoformat ( ) ,
        "account": account,  # info: "account" : account ,
        "report": _parse(stream),  # info: "report" : _parse ( stream ) ,
    }  # info: }


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run() -> dict[str, Any]:  # info: def run
    client_id, client_secret, refresh_token = admob_credentials()  # info: client_id , client_secret , refresh_token = admob_credentials (
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
    print(f"admob {detail}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
