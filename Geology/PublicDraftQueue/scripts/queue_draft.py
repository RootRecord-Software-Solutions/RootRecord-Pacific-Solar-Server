# ==============================================================================
# FILE: Geology/PublicDraftQueue/scripts/queue_draft.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Queue a Kilauea public draft from Database Geology/Volcanoes/Hawaii/kilauea_current.json.

WO-MIG-24. Stdlib only. No HTTP, no Grok, no Discord, Slack, or Telegram.

Fingerprint is status_notice_id plus alert_level.
No notice id does not overwrite the last hash.
The first seen notice seeds publish-last.json and does not queue.
An unchanged fingerprint does not queue.

  python3 queue_draft.py
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
VOLCANO = DB / "Geology" / "Volcanoes" / "Hawaii" / "kilauea_current.json"  # info: Hawaiʻi volcano bank
QUAKES = DB / "Geology" / "Earthquakes" / "hawaii_current.json"  # info: set QUAKES
OUT = DB / "Geology" / "PublicDraftQueue"  # info: set OUT
QUEUE = OUT / "queue"  # info: set QUEUE
PUBLISH = OUT / "publish-last.json"  # info: set PUBLISH
LOG_DIR = DB / "Logs" / "Geology" / "PublicDraftQueue"  # info: set LOG_DIR
LOG_FILE = LOG_DIR / "queue-draft.log"  # info: set LOG_FILE
MAX_CHARS = 1900  # info: set MAX_CHARS


# ====================================================
# SECTION: function now_hst
# What it does: now hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_hst() -> datetime:  # info: def now_hst
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function load_json
# What it does: load json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_json(path: Path) -> dict | None:  # info: def load_json
    if not path.is_file():  # info: if not path . is_file ( ) :
        return None  # info: return None
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return None  # info: return None
    return data if isinstance(data, dict) else None  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function fingerprint
# What it does: fingerprint.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fingerprint(notice_id: str, alert_level: str) -> str:  # info: def fingerprint
    core = f"{notice_id.strip()}\n{alert_level.strip().lower()}\n"  # info: set core
    return hashlib.sha256(core.encode("utf-8")).hexdigest()  # info: return hashlib . sha256 ( core . encode


# ====================================================
# SECTION: function load_publish
# What it does: load publish.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_publish() -> dict:  # info: def load_publish
    data = load_json(PUBLISH)  # info: set data
    return data or {}  # info: return data or { }


# ====================================================
# SECTION: function decide
# What it does: Return (reason, fingerprint). Reasons: no-notice, seed, unchanged, queued.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def decide(notice_id: str, alert_level: str) -> tuple[str, str]:  # info: def decide
    """Return (reason, fingerprint). Reasons: no-notice, seed, unchanged, queued."""  # info: """Return (reason, fingerprint). Reasons: no-notice, seed, unchanged, queued."""
    fp = fingerprint(notice_id, alert_level)  # info: set fp
    prev = str(load_publish().get("hash") or "")  # info: set prev
    if not notice_id.strip():  # info: if not notice_id . strip ( ) :
        return "no-notice", fp  # info: return "no-notice" , fp
    if not prev:  # info: if not prev :
        return "seed", fp  # info: return "seed" , fp
    if prev == fp:  # info: if prev == fp :
        return "unchanged", fp  # info: return "unchanged" , fp
    return "queued", fp  # info: return "queued" , fp


# ====================================================
# SECTION: function remember
# What it does: remember.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def remember(fp: str, notice_id: str, alert_level: str, at: datetime) -> None:  # info: def remember
    payload = {  # info: set payload
        "hash": fp,  # info: "hash" : fp ,
        "notice_id": notice_id,  # info: "notice_id" : notice_id ,
        "alert_level": alert_level,  # info: "alert_level" : alert_level ,
        "updated_at": at.isoformat(),  # info: "updated_at" : at . isoformat ( ) ,
    }  # info: }
    write_text(PUBLISH, json.dumps(payload, indent=2) + "\n")  # info: call write_text


# ====================================================
# SECTION: function write_text
# What it does: write text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_text(path: Path, text: str) -> None:  # info: def write_text
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_name(path.name + ".tmp")  # info: set tmp
    tmp.write_text(text, encoding="utf-8")  # info: tmp . write_text ( text , encoding =
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function log_line
# What it does: log line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_line(at: datetime, reason: str, notice_id: str, name: str = "") -> None:  # info: def log_line
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    extra = f" file={name}" if name else ""  # info: set extra
    line = f"{at.isoformat()} {reason} notice={notice_id or '-'}{extra}\n"  # info: set line
    with LOG_FILE.open("a", encoding="utf-8") as handle:  # info: with LOG_FILE . open ( "a" , encoding
        handle.write(line)  # info: handle . write ( line )


# ====================================================
# SECTION: function draft_body
# What it does: draft body.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def draft_body(kilauea: dict, at: datetime) -> str:  # info: def draft_body
    stamp = at.strftime("%Y-%m-%d %H:%M HST")  # info: set stamp
    notice = kilauea.get("latest_notice") if isinstance(kilauea.get("latest_notice"), dict) else {}  # info: set notice
    url = notice.get("url") or kilauea.get("status_notice_url") or ""  # info: set url
    lines = [  # info: set lines
        f"**Ava kilauea report** — {stamp}",  # info: f" **Ava kilauea report** — { stamp } " ,
        "",  # info: "" ,
        f"Alert level: {kilauea.get('alert_level') or 'n/a'}",  # info: f" Alert level: { kilauea . get ( 'alert_level'
        f"Aviation color: {kilauea.get('color_code') or 'n/a'}",  # info: f" Aviation color: { kilauea . get ( 'color_code'
        f"Headline: {kilauea.get('headline') or 'n/a'}",  # info: f" Headline: { kilauea . get ( 'headline'
        f"Erupting: {kilauea.get('erupting')}",  # info: f" Erupting: { kilauea . get ( 'erupting'
    ]  # info: ]
    if notice:  # info: if notice :
        lines.append(  # info: lines . append (
            f"Latest notice: {notice.get('type') or 'n/a'} ({notice.get('sent_utc') or 'n/a'} UTC)"  # info: f" Latest notice: { notice . get ( 'type'
        )  # info: )
        synopsis = " ".join(str(notice.get("synopsis") or "").split())  # info: set synopsis
        if synopsis:  # info: if synopsis :
            lines.append(synopsis)  # info: lines . append ( synopsis )
    if url:  # info: if url :
        lines.append(str(url))  # info: lines . append ( str ( url )
    quakes = load_json(QUAKES)  # info: set quakes
    if quakes and quakes.get("kilauea_150km_count") is not None:  # info: if quakes and quakes . get ( "kilauea_150km_count"
        window = quakes.get("window_h", 24)  # info: set window
        lines.append(  # info: lines . append (
            f"USGS: {quakes['kilauea_150km_count']} earthquakes magnitude 1 or greater "  # info: f" USGS: { quakes [ 'kilauea_150km_count' ] }
            f"within 150 km of Kilauea in the last {window} hours."  # info: f" within 150 km of Kilauea in the last { window } hours. "
        )  # info: )
    text = "\n".join(lines).strip() + "\n"  # info: set text
    if len(text) > MAX_CHARS:  # info: if len ( text ) > MAX_CHARS :
        text = text[: MAX_CHARS - 1].rstrip() + "\n"  # info: set text
    return text  # info: return text


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    at = now_hst()  # info: set at
    kilauea = load_json(VOLCANO) or {}  # info: set kilauea
    notice_id = str(kilauea.get("status_notice_id") or "").strip()  # info: set notice_id
    alert_level = str(kilauea.get("alert_level") or "").strip()  # info: set alert_level
    reason, fp = decide(notice_id, alert_level)  # info: reason , fp = decide ( notice_id ,
    name = ""  # info: set name
    if reason == "queued":  # info: if reason == "queued" :
        name = f"{at.strftime('%Y-%m-%dT%H%M%S')}-kilauea-cron.md"  # info: set name
        write_text(QUEUE / name, draft_body(kilauea, at))  # info: call write_text
        remember(fp, notice_id, alert_level, at)  # info: call remember
    elif reason != "no-notice":  # info: elif reason != "no-notice" :
        remember(fp, notice_id, alert_level, at)  # info: call remember
    log_line(at, reason, notice_id, name)  # info: call log_line
    print(reason + (f" {name}" if name else ""))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
