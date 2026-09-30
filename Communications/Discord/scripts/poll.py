#!/usr/bin/env python3
"""Discord poller. No token or an empty channel list: exit 0, no Discord HTTP.

Does not post. post_message stays in lib/api.py and returns without HTTP
unless RR_DISCORD_POST=1. That gate stays unset.

  python3 poll.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from lib.envload import bot_token  # noqa: E402

CHANNELS = HERE / "config" / "channels.json"
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
OUT = DB / "Communications" / "Discord"
LOG_DIR = DB / "Logs" / "Communications" / "Discord"
LOG_PATH = LOG_DIR / "poll.log"
STATUS_PATH = OUT / "status-last.json"
API = "https://discord.com/api/v10"
TIMEOUT = 15


def load_channels(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("channels must be a JSON list")
    out: list[str] = []
    for item in data:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            cid = item.get("id")
            if isinstance(cid, str) and cid.strip():
                out.append(cid.strip())
    return out


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def fetch_messages(token: str, channel_id: str) -> list:
    req = urllib.request.Request(
        f"{API}/channels/{channel_id}/messages?limit=1",
        headers={
            "Authorization": f"Bot {token}",
            "User-Agent": "RootRecord-Pacific (rootrecord, 1.0)",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        payload = json.load(response)
    return payload if isinstance(payload, list) else []


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    channels = load_channels(CHANNELS)
    token = bot_token()
    http_calls = 0
    polled: list[str] = []
    if token and channels:
        for channel_id in channels:
            fetch_messages(token, channel_id)
            http_calls += 1
            polled.append(channel_id)
    payload = {
        "ok": True,
        "token": "present" if token else "absent",
        "channels": len(channels),
        "http_calls": http_calls,
        "polled": polled,
        "posted": False,
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),
    }
    write_json(STATUS_PATH, payload)
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(
            f"{payload['updated_at']} token={payload['token']} channels={payload['channels']} http_calls={payload['http_calls']}\n"
        )
    return payload


def main() -> int:
    payload = run()
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
