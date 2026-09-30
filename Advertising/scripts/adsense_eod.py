#!/usr/bin/env python3
"""AdSense end-of-day snapshot. Stdlib only. Never prints secrets.

  python3 adsense_eod.py

With no client id, secret, or refresh token, writes ok=false detail=not_configured
and exits 0. It does not call Google. A failed live pull keeps the previous ok file.
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

from lib.envload import adsense_account_name, adsense_credentials, adsense_currency  # noqa: E402

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
SNAPSHOT = DATABASE / "Advertising" / "adsense-last.json"
HST = ZoneInfo("Pacific/Honolulu")
TOKEN_URI = "https://oauth2.googleapis.com/token"
API = "https://adsense.googleapis.com/v2"
DAYS = 7
TIMEOUT_S = 30
METRICS = (
    "PAGE_VIEWS",
    "CLICKS",
    "ESTIMATED_EARNINGS",
    "PAGE_VIEWS_RPM",
    "IMPRESSIONS",
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
        raise RuntimeError(f"adsense token {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("adsense token failed") from None
    access = tok.get("access_token") if isinstance(tok, dict) else None
    if not isinstance(access, str) or not access:
        raise RuntimeError("adsense token missing")
    return access


def _get(url: str, access: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + access})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"adsense {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("adsense request failed") from None
    if not isinstance(body, dict):
        raise RuntimeError("adsense bad body")
    return body


def _resolve_account(access: str) -> str:
    named = _account(adsense_account_name())
    if named:
        return named
    payload = _get(f"{API}/accounts", access)
    rows = payload.get("accounts") or []
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("adsense no account")
    first = rows[0] if isinstance(rows[0], dict) else {}
    name = _account(str(first.get("name") or ""))
    if not name:
        raise RuntimeError("adsense account missing name")
    return name


def _cell_map(headers: list[Any], row: dict[str, Any]) -> dict[str, str]:
    cells = row.get("cells") or []
    out: dict[str, str] = {}
    for i, header in enumerate(headers):
        if not isinstance(header, dict):
            continue
        key = str(header.get("name") or header.get("type") or f"c{i}")
        val = ""
        if isinstance(cells, list) and i < len(cells):
            cell = cells[i]
            val = str(cell.get("value") if isinstance(cell, dict) else cell or "")
        out[key] = val
    return out


def _parse(report: dict[str, Any]) -> dict[str, Any]:
    headers = report.get("headers") or []
    if not isinstance(headers, list):
        headers = []
    rows_out = []
    for row in report.get("rows") or []:
        if isinstance(row, dict):
            rows_out.append(_cell_map(headers, row))
    totals: dict[str, str] = {}
    if isinstance(report.get("totals"), dict):
        totals = _cell_map(headers, report["totals"])
    names = [h.get("name") for h in headers if isinstance(h, dict)]
    return {"headers": names, "rows": rows_out, "totals": totals}


def _live(client_id: str, client_secret: str, refresh_token: str) -> dict[str, Any]:
    access = _refresh(client_id, client_secret, refresh_token)
    end = datetime.now(HST).date()
    start = end - timedelta(days=DAYS - 1)
    account = _resolve_account(access)
    query = urllib.parse.urlencode(
        [
            ("dateRange", "CUSTOM"),
            ("startDate.year", str(start.year)),
            ("startDate.month", str(start.month)),
            ("startDate.day", str(start.day)),
            ("endDate.year", str(end.year)),
            ("endDate.month", str(end.month)),
            ("endDate.day", str(end.day)),
            *[("metrics", metric) for metric in METRICS],
            ("dimensions", "DATE"),
            ("orderBy", "+DATE"),
            ("currencyCode", adsense_currency()),
        ]
    )
    raw = _get(f"{API}/{account}/reports:generate?{query}", access)
    return {
        "ok": True,
        "kind": "eod",
        "generated": _stamp(),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "account": account,
        "report": _parse(raw),
    }


def run() -> dict[str, Any]:
    client_id, client_secret, refresh_token = adsense_credentials()
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
    print(f"adsense {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
