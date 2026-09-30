#!/usr/bin/env python3
"""Slack poller. No token: exit 0, status not_configured, no Slack HTTP.

A present token still does not call Slack and does not post. Posting needs
Alexander's sign-off. RR_SLACK stays unset, so the jobs.py block stays off.

  python3 poll.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from lib.envload import bot_token  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
OUT = DB / "Communications" / "Slack"
LOG_DIR = DB / "Logs" / "Communications" / "Slack"
LOG_PATH = LOG_DIR / "poll.log"
STATUS_PATH = OUT / "slack-last.json"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    token = bot_token()
    if token:
        status = "token_present"
    else:
        status = "not_configured"
    payload = {
        "ok": True,
        "status": status,
        "token": "present" if token else "absent",
        "http_calls": 0,
        "posted": False,
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),
    }
    write_json(STATUS_PATH, payload)
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(
            f"{payload['updated_at']} status={payload['status']} token={payload['token']} http_calls=0 posted=false\n"
        )
    return payload


def main() -> int:
    payload = run()
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
