#!/usr/bin/env python3
"""Save redacted Vercel failed-build records. Stdlib only. Never prints the token.

  python3 vercel_builds.py

With no token, prints missing_vercel_token and writes nothing.
Successful deploys do not delete stored records. Prune waits for sign-off.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.envload import vercel_team_id, vercel_token  # noqa: E402

LOG_DIR = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Website")
API = "https://api.vercel.com"
MAX_LOG_CHARS = 120_000
TIMEOUT_S = 30
_REDACT = re.compile(
    r"(?i)(bearer\s+|token[=:]\s*|sk_(?:live|test)_|xai-|xox[baprs]-|"
    r"VERCEL_TOKEN=|POSTGRES_URL=)(\S+)"
)


def _redact(text: str) -> str:
    return _REDACT.sub(r"\1[redacted]", text)


def _slug(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip())[:80]
    return token.strip("-") or "project"


def _get(path: str, params: dict[str, str], token: str) -> Any:
    query = dict(params)
    team = vercel_team_id()
    if team:
        query["teamId"] = team
    url = API + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(
        url,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def _write_error(dep: dict[str, Any], log_text: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    uid = str(dep.get("uid") or dep.get("id") or "unknown")
    name = str(dep.get("name") or "project")
    target = str(dep.get("target") or "preview")
    stem = f"{_slug(name)}--{_slug(target)}--{_slug(uid)}"
    created = dep.get("createdAt") or dep.get("created")
    if isinstance(created, (int, float)):
        created_at = datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat()
    else:
        created_at = datetime.now(timezone.utc).isoformat()
    body = _redact(log_text or "(no log text returned)")[:MAX_LOG_CHARS]
    path = LOG_DIR / f"{stem}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({
        "uid": uid,
        "name": name,
        "target": target,
        "created_at": created_at,
        "url": str(dep.get("url") or ""),
        "log": body,
        "prune": "gated",
    }, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def sync_recent(*, limit: int = 40) -> dict[str, Any]:
    token = vercel_token()
    if not token:
        return {"ok": False, "detail": "missing_vercel_token", "saved": 0, "cleared": 0}
    data = _get("/v6/deployments", {"limit": str(limit)}, token)
    deployments = data.get("deployments") if isinstance(data, dict) else None
    if not isinstance(deployments, list):
        return {"ok": False, "detail": "list_failed", "saved": 0, "cleared": 0}
    saved = 0
    for dep in deployments:
        if not isinstance(dep, dict):
            continue
        state = str(dep.get("readyState") or dep.get("state") or "").upper()
        if state not in {"ERROR", "FAILED"}:
            continue
        uid = str(dep.get("uid") or dep.get("id") or "")
        events = _get(
            f"/v3/deployments/{uid}/events",
            {"limit": "1000", "builds": "1", "direction": "forward"},
            token,
        ) if uid else None
        lines: list[str] = []
        rows = events if isinstance(events, list) else (events or {}).get("events") if isinstance(events, dict) else []
        if isinstance(events, dict) and not rows and events.get("text"):
            lines.append(str(events.get("text")))
        elif isinstance(rows, list):
            for ev in rows:
                if not isinstance(ev, dict):
                    continue
                payload = ev.get("payload") if isinstance(ev.get("payload"), dict) else {}
                text = ev.get("text") or payload.get("text") or payload.get("message") or ""
                if text:
                    lines.append(str(text).rstrip())
        _write_error(dep, "\n".join(lines))
        saved += 1
    return {"ok": True, "detail": "saved", "saved": saved, "cleared": 0, "prune": "gated"}


def main() -> int:
    result = sync_recent()
    print(f"vercel {result.get('detail')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
