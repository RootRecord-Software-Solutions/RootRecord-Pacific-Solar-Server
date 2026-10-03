# ==============================================================================
# FILE: Reports/pipeline/context.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Report context from a profile and already stored rows. This module does not fetch the web."""
from __future__ import annotations  # info: from __future__ import annotations

import sqlite3  # info: import sqlite3
from pathlib import Path  # info: from pathlib import Path

from windows import window_for  # info: from windows import window_for


# ====================================================
# SECTION: function build_context
# What it does: Assemble the generator input. Observations are passed in or read from an existing news database.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_context(profile: dict, when, observations: list | None = None, news_db: Path | None = None) -> dict:  # info: def build_context
    window = window_for(when, str(profile.get("cadence") or "hourly"))  # info: set window
    rows = list(observations or [])  # info: set rows
    if profile.get("generator") == "news_select" and news_db is not None:  # info: if profile generator is news_select
        rows = select_news(news_db, window, str(profile.get("topic") or ""), str(profile.get("scope") or ""))  # info: set rows
    return {  # info: return {
        "profile": profile,  # info: "profile" : profile
        "window": window,  # info: "window" : window
        "topic": profile.get("topic") or "",  # info: "topic"
        "scope": profile.get("scope") or "",  # info: "scope"
        "observations": rows,  # info: "observations" : rows
        "sources": [{"id": row.get("id"), "url": row.get("url")} for row in rows if isinstance(row, dict)],  # info: "sources"
    }  # info: }


# ====================================================
# SECTION: function select_news
# What it does: Read posts already in a news sqlite file for the topic and scope. It does not download feeds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def select_news(db_path: Path, window: dict, topic: str, scope: str) -> list:  # info: def select_news
    if not db_path.is_file():  # info: if not db_path . is_file
        return []  # info: return []
    try:  # info: try
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)  # info: set conn
        conn.row_factory = sqlite3.Row  # info: set row_factory
    except sqlite3.Error:  # info: except sqlite3 . Error
        return []  # info: return []
    try:  # info: try
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}  # info: set tables
        if "posts" not in tables:  # info: if "posts" not in tables
            return []  # info: return []
        found = []  # info: set found
        for row in conn.execute("SELECT * FROM posts ORDER BY rowid DESC LIMIT 200"):  # info: for row in posts
            item = dict(row)  # info: set item
            blob = " ".join(str(item.get(key) or "") for key in ("title", "summary", "topic", "scope", "region")).lower()  # info: set blob
            if topic and topic not in ("news", "configured") and topic.lower() not in blob:  # info: if topic filter misses
                continue  # info: continue
            if scope and scope not in ("configured", "") and scope.lower() not in blob and scope.lower() not in str(db_path).lower():  # info: if scope filter misses
                continue  # info: continue
            found.append({"id": str(item.get("id") or item.get("url") or ""), "url": item.get("url") or "", "title": item.get("title") or "", "summary": item.get("summary") or ""})  # info: found . append
            if len(found) >= 8:  # info: if len ( found ) >= 8
                break  # info: break
        return found  # info: return found
    except sqlite3.Error:  # info: except sqlite3 . Error
        return []  # info: return []
    finally:  # info: finally
        conn.close()  # info: conn . close
