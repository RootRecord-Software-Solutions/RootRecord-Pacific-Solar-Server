#!/usr/bin/env python3
"""Queue a Kilauea public draft from Database Geology/Volcanoes/kilauea-last.json.

WO-MIG-24. Stdlib only. No HTTP, no Grok, no Discord, Slack, or Telegram.

Fingerprint is status_notice_id plus alert_level.
No notice id does not overwrite the last hash.
The first seen notice seeds publish-last.json and does not queue.
An unchanged fingerprint does not queue.

  python3 queue_draft.py
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
VOLCANO = DB / "Geology" / "Volcanoes" / "kilauea-last.json"
QUAKES = DB / "Geology" / "Earthquakes" / "hawaii-last.json"
OUT = DB / "Geology" / "PublicDraftQueue"
QUEUE = OUT / "queue"
PUBLISH = OUT / "publish-last.json"
LOG_DIR = DB / "Logs" / "Geology" / "PublicDraftQueue"
LOG_FILE = LOG_DIR / "queue-draft.log"
MAX_CHARS = 1900


def now_hst() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def fingerprint(notice_id: str, alert_level: str) -> str:
    core = f"{notice_id.strip()}\n{alert_level.strip().lower()}\n"
    return hashlib.sha256(core.encode("utf-8")).hexdigest()


def load_publish() -> dict:
    data = load_json(PUBLISH)
    return data or {}


def decide(notice_id: str, alert_level: str) -> tuple[str, str]:
    """Return (reason, fingerprint). Reasons: no-notice, seed, unchanged, queued."""
    fp = fingerprint(notice_id, alert_level)
    prev = str(load_publish().get("hash") or "")
    if not notice_id.strip():
        return "no-notice", fp
    if not prev:
        return "seed", fp
    if prev == fp:
        return "unchanged", fp
    return "queued", fp


def remember(fp: str, notice_id: str, alert_level: str, at: datetime) -> None:
    payload = {
        "hash": fp,
        "notice_id": notice_id,
        "alert_level": alert_level,
        "updated_at": at.isoformat(),
    }
    write_text(PUBLISH, json.dumps(payload, indent=2) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def log_line(at: datetime, reason: str, notice_id: str, name: str = "") -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    extra = f" file={name}" if name else ""
    line = f"{at.isoformat()} {reason} notice={notice_id or '-'}{extra}\n"
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line)


def draft_body(kilauea: dict, at: datetime) -> str:
    stamp = at.strftime("%Y-%m-%d %H:%M HST")
    notice = kilauea.get("latest_notice") if isinstance(kilauea.get("latest_notice"), dict) else {}
    url = notice.get("url") or kilauea.get("status_notice_url") or ""
    lines = [
        f"**Ava kilauea report** — {stamp}",
        "",
        f"Alert level: {kilauea.get('alert_level') or 'n/a'}",
        f"Aviation color: {kilauea.get('color_code') or 'n/a'}",
        f"Headline: {kilauea.get('headline') or 'n/a'}",
        f"Erupting: {kilauea.get('erupting')}",
    ]
    if notice:
        lines.append(
            f"Latest notice: {notice.get('type') or 'n/a'} ({notice.get('sent_utc') or 'n/a'} UTC)"
        )
        synopsis = " ".join(str(notice.get("synopsis") or "").split())
        if synopsis:
            lines.append(synopsis)
    if url:
        lines.append(str(url))
    quakes = load_json(QUAKES)
    if quakes and quakes.get("kilauea_150km_count") is not None:
        window = quakes.get("window_h", 24)
        lines.append(
            f"USGS: {quakes['kilauea_150km_count']} earthquakes magnitude 1 or greater "
            f"within 150 km of Kilauea in the last {window} hours."
        )
    text = "\n".join(lines).strip() + "\n"
    if len(text) > MAX_CHARS:
        text = text[: MAX_CHARS - 1].rstrip() + "\n"
    return text


def main() -> int:
    at = now_hst()
    kilauea = load_json(VOLCANO) or {}
    notice_id = str(kilauea.get("status_notice_id") or "").strip()
    alert_level = str(kilauea.get("alert_level") or "").strip()
    reason, fp = decide(notice_id, alert_level)
    name = ""
    if reason == "queued":
        name = f"{at.strftime('%Y-%m-%dT%H%M%S')}-kilauea-cron.md"
        write_text(QUEUE / name, draft_body(kilauea, at))
        remember(fp, notice_id, alert_level, at)
    elif reason != "no-notice":
        remember(fp, notice_id, alert_level, at)
    log_line(at, reason, notice_id, name)
    print(reason + (f" {name}" if name else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
