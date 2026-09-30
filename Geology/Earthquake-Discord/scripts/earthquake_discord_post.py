#!/usr/bin/env python3
"""Format Database Geology earthquake files for Discord. Dry-run by default.

Reads hawaii-last.json and global-last.json written by geology_collect.py.
Does not fetch USGS, attach audio, or play the speaker.

  python3 earthquake_discord_post.py           # print the message; write nothing
  python3 earthquake_discord_post.py --send    # hand the text to Communications/Discord

--send still does not call Discord unless the pipe's RR_DISCORD_POST=1 gate is set.
That gate is not set here.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from lib.envload import channel_id  # noqa: E402

PACIFIC = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server")
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
QUAKES = DB / "Geology" / "Earthquakes"
OUT = DB / "Geology" / "Earthquake-Discord"
LOG_DIR = DB / "Logs" / "Geology" / "Earthquake-Discord"
POSTED = OUT / "posted-last.json"
PIPE = PACIFIC / "Communications" / "Discord"
MAX_LINES = 6


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def events(bundle: dict | None) -> list[dict]:
    if not bundle:
        return []
    raw = bundle.get("events") or []
    return [e for e in raw if isinstance(e, dict) and e.get("id")]


def seen_ids(posted: dict | None) -> set[str]:
    if not posted:
        return set()
    raw = posted.get("seen_ids") or []
    return {str(i) for i in raw if i}


def section(label: str, bundle: dict | None, seen: set[str]) -> list[str]:
    if bundle is None:
        return [f"{label}: data is not on file."]
    ev = events(bundle)
    fresh = [e for e in ev if str(e.get("id")) not in seen]
    count = bundle.get("count")
    m25 = bundle.get("count_m25")
    lines = [
        f"{label} 24 h: {count if count is not None else len(ev)} (M2.5+ {m25 if m25 is not None else 'n/a'}). New since last post: {len(fresh)}."
    ]
    for e in fresh[:MAX_LINES]:
        lines.append(f"- M{e.get('mag')} {e.get('place')}")
    extra = len(fresh) - MAX_LINES
    if extra > 0:
        lines.append(f"- and {extra} more.")
    return lines


def build_message(hawaii: dict | None, global_: dict | None, seen: set[str]) -> str:
    collected = (hawaii or global_ or {}).get("at") or "n/a"
    lines = [f"Earthquake report. Collected {collected}.", ""]
    lines.extend(section("Hawaii", hawaii, seen))
    lines.append("")
    lines.extend(section("Global", global_, seen))
    return "\n".join(lines).strip() + "\n"


def source_digest(hawaii: dict | None, global_: dict | None) -> str:
    """Digest the collector snapshot, not the rendered 'new since last post' lines."""
    payload = {
        "hawaii_ids": [str(e["id"]) for e in events(hawaii)],
        "global_ids": [str(e["id"]) for e in events(global_)],
        "hawaii_count": None if not hawaii else hawaii.get("count"),
        "global_count": None if not global_ else global_.get("count"),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def remember(hawaii: dict | None, global_: dict | None, snap: str) -> dict:
    ids = [str(e["id"]) for e in events(hawaii) + events(global_)]
    prev = seen_ids(load_json(POSTED))
    merged = list(prev)
    for i in ids:
        if i not in prev:
            merged.append(i)
    return {
        "digest": snap,
        "seen_ids": merged[-400:],
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),
        "posted": False,
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def handoff(text: str) -> str:
    """Hand text to the Discord send pipe in a child process so package names do not collide.

    The pipe returns without HTTP unless its own gate is set.
    """
    if not (PIPE / "lib" / "api.py").is_file():
        return "pipe-missing"
    if not channel_id():
        return "channel-absent"
    code = (
        "import os, sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from lib.api import post_message\n"
        "cid = (os.environ.get('DISCORD_EARTHQUAKE_CHANNEL_ID') or '').strip()\n"
        "result = post_message(cid, sys.stdin.read().strip())\n"
        "print('handed' if isinstance(result, dict) else 'pipe-held')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code, str(PIPE)],
        input=text,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        timeout=20,
    )
    line = (proc.stdout or "").strip().splitlines()
    return line[-1] if line else "pipe-held"


def main() -> int:
    send = "--send" in sys.argv
    hawaii = load_json(QUAKES / "hawaii-last.json")
    global_ = load_json(QUAKES / "global-last.json")
    posted = load_json(POSTED)
    snap = source_digest(hawaii, global_)
    text = build_message(hawaii, global_, seen_ids(posted))
    if posted and posted.get("digest") == snap:
        print("unchanged")
        return 0
    if not send:
        print(text, end="")
        return 0
    outcome = handoff(text)
    print(outcome)
    if outcome == "handed":
        payload = remember(hawaii, global_, snap)
        payload["posted"] = True
        write_json(POSTED, payload)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with (LOG_DIR / "post.log").open("a", encoding="utf-8") as log:
            log.write(f"{payload['updated_at']} outcome={outcome}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
