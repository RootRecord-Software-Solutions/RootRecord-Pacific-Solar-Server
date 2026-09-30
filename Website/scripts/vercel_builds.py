# ==============================================================================
# FILE: Website/scripts/vercel_builds.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Save redacted Vercel failed-build records. Stdlib only. Never prints the token.

  python3 vercel_builds.py

With no token, prints missing_vercel_token and writes nothing.
Successful deploys do not delete stored records. Prune waits for sign-off.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
import sys  # info: import sys
import urllib.error  # info: import urllib . error
import urllib.parse  # info: import urllib . parse
import urllib.request  # info: import urllib . request
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
if str(ROOT) not in sys.path:  # info: if str ( ROOT ) not in sys
    sys.path.insert(0, str(ROOT))  # info: sys . path . insert ( 0 ,

from lib.envload import vercel_team_id, vercel_token  # noqa: E402

LOG_DIR = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Website")  # info: set LOG_DIR
API = "https://api.vercel.com"  # info: set API
MAX_LOG_CHARS = 120_000  # info: set MAX_LOG_CHARS
TIMEOUT_S = 30  # info: set TIMEOUT_S
_REDACT = re.compile(  # info: set _REDACT
    r"(?i)(bearer\s+|token[=:]\s*|sk_(?:live|test)_|xai-|xox[baprs]-|"  # info: r"(?i)(bearer\s+|token[=:]\s*|sk_(?:live|test)_|xai-|xox[baprs]-|"
    r"VERCEL_TOKEN=|POSTGRES_URL=)(\S+)"  # info: r"VERCEL_TOKEN=|POSTGRES_URL=)(\S+)"
)  # info: )


# ====================================================
# SECTION: function _redact
# What it does:  redact.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _redact(text: str) -> str:  # info: def _redact
    return _REDACT.sub(r"\1[redacted]", text)  # info: return _REDACT . sub ( r"\1[redacted]" , text


# ====================================================
# SECTION: function _slug
# What it does:  slug.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _slug(value: str) -> str:  # info: def _slug
    token = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip())[:80]  # info: set token
    return token.strip("-") or "project"  # info: return token . strip ( "-" ) or


# ====================================================
# SECTION: function _get
# What it does:  get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(path: str, params: dict[str, str], token: str) -> Any:  # info: def _get
    query = dict(params)  # info: set query
    team = vercel_team_id()  # info: set team
    if team:  # info: if team :
        query["teamId"] = team  # info: query [ "teamId" ] = team
    url = API + path  # info: set url
    if query:  # info: if query :
        url += "?" + urllib.parse.urlencode(query)  # info: set url
    req = urllib.request.Request(  # info: set req
        url,  # info: url ,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},  # info: set headers
        method="GET",  # info: set method
    )  # info: )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # info: with urllib . request . urlopen ( req
            return json.loads(resp.read().decode("utf-8"))  # info: return json . loads ( resp . read
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):  # info: except ( urllib . error . URLError ,
        return None  # info: return None


# ====================================================
# SECTION: function _write_error
# What it does:  write error.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_error(dep: dict[str, Any], log_text: str) -> Path:  # info: def _write_error
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    uid = str(dep.get("uid") or dep.get("id") or "unknown")  # info: set uid
    name = str(dep.get("name") or "project")  # info: set name
    target = str(dep.get("target") or "preview")  # info: set target
    stem = f"{_slug(name)}--{_slug(target)}--{_slug(uid)}"  # info: set stem
    created = dep.get("createdAt") or dep.get("created")  # info: set created
    if isinstance(created, (int, float)):  # info: if isinstance ( created , ( int ,
        created_at = datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat()  # info: set created_at
    else:  # info: else :
        created_at = datetime.now(timezone.utc).isoformat()  # info: set created_at
    body = _redact(log_text or "(no log text returned)")[:MAX_LOG_CHARS]  # info: set body
    path = LOG_DIR / f"{stem}.json"  # info: set path
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps({  # info: tmp . write_text ( json . dumps (
        "uid": uid,  # info: "uid" : uid ,
        "name": name,  # info: "name" : name ,
        "target": target,  # info: "target" : target ,
        "created_at": created_at,  # info: "created_at" : created_at ,
        "url": str(dep.get("url") or ""),  # info: "url" : str ( dep . get (
        "log": body,  # info: "log" : body ,
        "prune": "gated",  # info: "prune" : "gated" ,
    }, indent=2), encoding="utf-8")  # info: } , indent = 2 ) , encoding
    tmp.replace(path)  # info: tmp . replace ( path )
    return path  # info: return path


# ====================================================
# SECTION: function sync_recent
# What it does: sync recent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sync_recent(*, limit: int = 40) -> dict[str, Any]:  # info: def sync_recent
    token = vercel_token()  # info: set token
    if not token:  # info: if not token :
        return {"ok": False, "detail": "missing_vercel_token", "saved": 0, "cleared": 0}  # info: return { "ok" : False , "detail" :
    data = _get("/v6/deployments", {"limit": str(limit)}, token)  # info: set data
    deployments = data.get("deployments") if isinstance(data, dict) else None  # info: set deployments
    if not isinstance(deployments, list):  # info: if not isinstance ( deployments , list )
        return {"ok": False, "detail": "list_failed", "saved": 0, "cleared": 0}  # info: return { "ok" : False , "detail" :
    saved = 0  # info: set saved
    for dep in deployments:  # info: for dep in deployments :
        if not isinstance(dep, dict):  # info: if not isinstance ( dep , dict )
            continue  # info: continue
        state = str(dep.get("readyState") or dep.get("state") or "").upper()  # info: set state
        if state not in {"ERROR", "FAILED"}:  # info: if state not in { "ERROR" , "FAILED"
            continue  # info: continue
        uid = str(dep.get("uid") or dep.get("id") or "")  # info: set uid
        events = _get(  # info: set events
            f"/v3/deployments/{uid}/events",  # info: f" /v3/deployments/ { uid } /events " ,
            {"limit": "1000", "builds": "1", "direction": "forward"},  # info: { "limit" : "1000" , "builds" : "1"
            token,  # info: token ,
        ) if uid else None  # info: ) if uid else None
        lines: list[str] = []  # info: set lines
        rows = events if isinstance(events, list) else (events or {}).get("events") if isinstance(events, dict) else []  # info: set rows
        if isinstance(events, dict) and not rows and events.get("text"):  # info: if isinstance ( events , dict ) and
            lines.append(str(events.get("text")))  # info: lines . append ( str ( events .
        elif isinstance(rows, list):  # info: elif isinstance ( rows , list ) :
            for ev in rows:  # info: for ev in rows :
                if not isinstance(ev, dict):  # info: if not isinstance ( ev , dict )
                    continue  # info: continue
                payload = ev.get("payload") if isinstance(ev.get("payload"), dict) else {}  # info: set payload
                text = ev.get("text") or payload.get("text") or payload.get("message") or ""  # info: set text
                if text:  # info: if text :
                    lines.append(str(text).rstrip())  # info: lines . append ( str ( text )
        _write_error(dep, "\n".join(lines))  # info: call _write_error
        saved += 1  # info: set saved
    return {"ok": True, "detail": "saved", "saved": saved, "cleared": 0, "prune": "gated"}  # info: return { "ok" : True , "detail" :


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    result = sync_recent()  # info: set result
    print(f"vercel {result.get('detail')}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
