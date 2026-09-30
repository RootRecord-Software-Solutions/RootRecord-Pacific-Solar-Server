"""Discord send entry point. Refuses HTTP unless RR_DISCORD_POST=1 and a token exist."""
from __future__ import annotations

import json
import os
import urllib.request

from lib.envload import bot_token

API = "https://discord.com/api/v10"
TIMEOUT = 15


def post_message(channel_id: str, content: str) -> dict | None:
    """Return None and do not call Discord unless the post gate and token are both set."""
    if os.environ.get("RR_DISCORD_POST", "0").strip() != "1":
        return None
    token = bot_token()
    if not token or not str(channel_id or "").strip() or not str(content or "").strip():
        return None
    body = json.dumps(
        {
            "content": str(content)[:2000],
            "allowed_mentions": {"parse": []},
        }
    ).encode()
    req = urllib.request.Request(
        f"{API}/channels/{channel_id}/messages",
        data=body,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "RootRecord-Pacific (rootrecord, 1.0)",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        payload = json.load(response)
    return payload if isinstance(payload, dict) else None
