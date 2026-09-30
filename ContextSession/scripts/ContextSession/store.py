"""Per-user context sessions. One sqlite file per user id. No network."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SAFE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
DEFAULT_ROOT = Path(
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/ContextSession"
)


class SessionStore:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def _check(self, label: str, value: str) -> str:
        if not SAFE.fullmatch(value or ""):
            raise ValueError(f"invalid {label}")
        return value

    def _db(self, user_id: str) -> Path:
        self._check("user_id", user_id)
        return self.root / f"{user_id}.db"

    def init_user(self, user_id: str) -> Path:
        db = self._db(user_id)
        with sqlite3.connect(db) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS sessions(
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    title TEXT
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    role TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    content TEXT,
                    metadata TEXT
                )"""
            )
        return db

    def create_session(
        self,
        user_id: str,
        session_id: str,
        provider: str = "",
        title: str = "",
    ) -> dict:
        self._check("session_id", session_id)
        self.init_user(user_id)
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db(user_id)) as conn:
            conn.execute(
                "INSERT INTO sessions VALUES(?,?,?,?,?,?)",
                (session_id, user_id, provider, now, now, title),
            )
        self.append_event(
            user_id,
            session_id,
            "system",
            "session_created",
            "Session created",
            {"provider": provider, "title": title},
        )
        return self.current(user_id, session_id)

    def append_event(
        self,
        user_id: str,
        session_id: str,
        role: str,
        event_type: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        self._check("session_id", session_id)
        self.init_user(user_id)
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db(user_id)) as conn:
            conn.execute(
                """INSERT INTO events(session_id,ts,role,event_type,content,metadata)
                   VALUES(?,?,?,?,?,?)""",
                (
                    session_id,
                    now,
                    role,
                    event_type,
                    content,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            conn.execute(
                "UPDATE sessions SET updated_at=? WHERE session_id=?",
                (now, session_id),
            )
        return self.current(user_id, session_id)

    def current(self, user_id: str, session_id: str) -> dict:
        self._check("session_id", session_id)
        self.init_user(user_id)
        with sqlite3.connect(self._db(user_id)) as conn:
            rows = conn.execute(
                """SELECT ts,role,event_type,content,metadata
                   FROM events WHERE session_id=? ORDER BY id""",
                (session_id,),
            ).fetchall()
        events = [
            {
                "ts": row[0],
                "role": row[1],
                "event_type": row[2],
                "content": row[3],
                "metadata": json.loads(row[4] or "{}"),
            }
            for row in rows
        ]
        return {
            "user_id": user_id,
            "session_id": session_id,
            "events": events,
            "event_count": len(events),
            "latest": events[-1] if events else None,
        }

    def list_sessions(self, user_id: str) -> list[dict]:
        self.init_user(user_id)
        with sqlite3.connect(self._db(user_id)) as conn:
            rows = conn.execute(
                """SELECT session_id,provider,created_at,updated_at,title
                   FROM sessions ORDER BY updated_at DESC"""
            ).fetchall()
        return [
            {
                "session_id": row[0],
                "provider": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "title": row[4],
            }
            for row in rows
        ]
