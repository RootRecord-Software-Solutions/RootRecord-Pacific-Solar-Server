"""Context sessions compiled into one sqlite file. No per-event files."""
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
DB_NAME = "sessions.db"
COMPILE_NAME = "compile-last.json"


class SessionStore:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / DB_NAME
        self.compile_path = self.root / COMPILE_NAME

    def _check(self, label: str, value: str) -> str:
        if not SAFE.fullmatch(value or ""):
            raise ValueError(f"invalid {label}")
        return value

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions(
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                provider TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                title TEXT,
                PRIMARY KEY (user_id, session_id)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                ts TEXT NOT NULL,
                role TEXT NOT NULL,
                event_type TEXT NOT NULL,
                content TEXT,
                metadata TEXT
            )"""
        )
        return conn

    def create_session(
        self,
        user_id: str,
        session_id: str,
        provider: str = "",
        title: str = "",
    ) -> dict:
        self._check("user_id", user_id)
        self._check("session_id", session_id)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions VALUES(?,?,?,?,?,?)",
                (user_id, session_id, provider, now, now, title),
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
        self._check("user_id", user_id)
        self._check("session_id", session_id)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO events(user_id,session_id,ts,role,event_type,content,metadata)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    user_id,
                    session_id,
                    now,
                    role,
                    event_type,
                    content,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            conn.execute(
                "UPDATE sessions SET updated_at=? WHERE user_id=? AND session_id=?",
                (now, user_id, session_id),
            )
        self.compile()
        return self.current(user_id, session_id)

    def current(self, user_id: str, session_id: str) -> dict:
        self._check("user_id", user_id)
        self._check("session_id", session_id)
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT ts,role,event_type,content,metadata
                   FROM events WHERE user_id=? AND session_id=? ORDER BY id""",
                (user_id, session_id),
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
        self._check("user_id", user_id)
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT session_id,provider,created_at,updated_at,title
                   FROM sessions WHERE user_id=? ORDER BY updated_at DESC""",
                (user_id,),
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

    def compile(self) -> dict:
        """Rewrite one summary file from the sqlite store. Never adds another file."""
        with self._connect() as conn:
            users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM sessions").fetchone()[0]
            sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            latest_rows = conn.execute(
                """SELECT s.user_id, s.session_id, s.updated_at, s.title,
                          (SELECT COUNT(*) FROM events e
                           WHERE e.user_id=s.user_id AND e.session_id=s.session_id),
                          (SELECT role FROM events e
                           WHERE e.user_id=s.user_id AND e.session_id=s.session_id
                           ORDER BY e.id DESC LIMIT 1),
                          (SELECT event_type FROM events e
                           WHERE e.user_id=s.user_id AND e.session_id=s.session_id
                           ORDER BY e.id DESC LIMIT 1)
                   FROM sessions s
                   ORDER BY s.updated_at DESC"""
            ).fetchall()
        summary = {
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "store": DB_NAME,
            "users": users,
            "sessions": sessions,
            "events": events,
            "latest": [
                {
                    "user_id": row[0],
                    "session_id": row[1],
                    "updated_at": row[2],
                    "title": row[3],
                    "event_count": row[4],
                    "latest_role": row[5],
                    "latest_type": row[6],
                }
                for row in latest_rows
            ],
        }
        tmp = self.compile_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.compile_path)
        return summary
