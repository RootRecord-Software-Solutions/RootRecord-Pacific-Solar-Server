#!/usr/bin/env python3
"""AdMob end-of-day snapshot. Stdlib only. Never prints secrets.

  python3 admob_eod.py

With no client id, secret, or refresh token, writes ok=false detail=not_configured
and exits 0. It does not call Google. The AdMob refresh token does not fall back
to the AdSense token. A failed live pull keeps the previous ok file.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.envload import admob_account_name, admob_credentials  # noqa: E402

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
SNAPSHOT = DATABASE / "Advertising" / "admob-last.json"
HST = ZoneInfo("Pacific/Honolulu")
TOKEN_URI = "https://oauth2.googleapis.com/token"
API = "https://admob.googleapis.com/v1"
DAYS = 7
TIMEOUT_S = 45
METRICS = (
    "ESTIMATED_EARNINGS",
    "IMPRESSIONS",
    "CLICKS",
    "AD_REQUESTS",
    "MATCHED_REQUESTS",
)


def _write(snap: dict[str, Any]) -> None:
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    tmp = SNAPSHOT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    tmp.replace(SNAPSHOT)


def _read() -> dict[str, Any]:
    if not SNAPSHOT.is_file():
        return {}
    try:
        raw = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _stamp() -> str:
    return datetime.now(HST).isoformat(timespec="seconds")


def _not_configured() -> dict[str, Any]:
    out = {"ok": False, "detail": "not_configured", "kind": "eod", "generated": _stamp()}
    _write(out)
    return out


def _account(name: str) -> str:
    name = name.strip()
    if not name:
        return ""
    return name if name.startswith("accounts/") else f"accounts/{name}"


def _refresh(client_id: str, client_secret: str, refresh_token: str) -> str:
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_URI,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            tok = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"admob token {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("admob token failed") from None
    access = tok.get("access_token") if isinstance(tok, dict) else None
    if not isinstance(access, str) or not access:
        raise RuntimeError("admob token missing")
    return access


def _request(url: str, access: str, payload: dict[str, Any] | None = None) -> Any:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Authorization": "Bearer " + access}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method="POST" if payload is not None else "GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"admob {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("admob request failed") from None


def _resolve_account(access: str) -> str:
    named = _account(admob_account_name())
    if named:
        return named
    payload = _request(f"{API}/accounts", access)
    if not isinstance(payload, dict):
        raise RuntimeError("admob no account")
    rows = payload.get("account") or payload.get("accounts") or []
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("admob no account")
    first = rows[0] if isinstance(rows[0], dict) else {}
    name = _account(str(first.get("name") or ""))
    if not name:
        raise RuntimeError("admob account missing name")
    return name


def _metric(row: dict[str, Any], key: str) -> str:
    cell = (row.get("metricValues") or {}).get(key) or {}
    if not isinstance(cell, dict):
        return ""
    if "microsValue" in cell:
        try:
            return f"{int(cell['microsValue']) / 1_000_000:.4f}"
        except (TypeError, ValueError):
            return ""
    if "integerValue" in cell:
        return str(cell["integerValue"])
    if "doubleValue" in cell:
        return str(cell["doubleValue"])
    return ""


def _parse(stream: list[Any]) -> dict[str, Any]:
    rows_out: list[dict[str, str]] = []
    totals: dict[str, str] = {}
    for item in stream:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("row"), dict):
            row = item["row"]
            dims = row.get("dimensionValues") or {}
            date = ""
            if isinstance(dims, dict) and isinstance(dims.get("DATE"), dict):
                date = str(dims["DATE"].get("value") or "")
            rows_out.append({"DATE": date, **{key: _metric(row, key) for key in METRICS}})
        if isinstance(item.get("total"), dict):
            tot = item["total"]
            totals = {key: _metric(tot, key) for key in METRICS}
    return {"rows": rows_out, "totals": totals}


def _live(client_id: str, client_secret: str, refresh_token: str) -> dict[str, Any]:
    access = _refresh(client_id, client_secret, refresh_token)
    end = datetime.now(HST).date()
    start = end - timedelta(days=DAYS - 1)
    account = _resolve_account(access)
    body = {
        "reportSpec": {
            "dateRange": {
                "startDate": {"year": start.year, "month": start.month, "day": start.day},
                "endDate": {"year": end.year, "month": end.month, "day": end.day},
            },
            "dimensions": ["DATE"],
            "metrics": list(METRICS),
            "sortConditions": [{"dimension": "DATE", "order": "ASCENDING"}],
        }
    }
    result = _request(f"{API}/{account}/networkReport:generate", access, body)
    if isinstance(result, list):
        stream = result
    elif isinstance(result, dict):
        stream = [result]
    else:
        raise RuntimeError("admob bad body")
    return {
        "ok": True,
        "kind": "eod",
        "generated": _stamp(),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "account": account,
        "report": _parse(stream),
    }


def run() -> dict[str, Any]:
    client_id, client_secret, refresh_token = admob_credentials()
    if not client_id or not client_secret or not refresh_token:
        return _not_configured()
    existing = _read()
    try:
        snap = _live(client_id, client_secret, refresh_token)
    except RuntimeError:
        if existing.get("ok"):
            return existing
        out = {"ok": False, "detail": "poll_failed", "kind": "eod", "generated": _stamp()}
        _write(out)
        return out
    _write(snap)
    return snap


def main() -> int:
    snap = run()
    detail = "ok" if snap.get("ok") else snap.get("detail") or "fail"
    print(f"admob {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
