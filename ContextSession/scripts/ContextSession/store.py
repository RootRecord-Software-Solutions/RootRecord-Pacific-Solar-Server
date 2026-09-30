# ==============================================================================
# FILE: ContextSession/scripts/ContextSession/store.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Context sessions compiled into one sqlite file. No per-event files."""  # info: """Context sessions compiled into one sqlite file. No per-event files."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
import sqlite3  # info: import sqlite3
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

SAFE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")  # info: set SAFE
DEFAULT_ROOT = Path(  # info: set DEFAULT_ROOT
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/ContextSession"  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/ContextSession"
)  # info: )
DB_NAME = "sessions.db"  # info: set DB_NAME
COMPILE_NAME = "compile-last.json"  # info: set COMPILE_NAME


# ====================================================
# SECTION: class SessionStore
# What it does: SessionStore.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class SessionStore:  # info: class SessionStore
    def __init__(self, root: str | Path | None = None):  # info: def __init__
        self.root = Path(root) if root else DEFAULT_ROOT  # info: self . root = Path ( root )
        self.root.mkdir(parents=True, exist_ok=True)  # info: self . root . mkdir ( parents =
        self.db_path = self.root / DB_NAME  # info: self . db_path = self . root /
        self.compile_path = self.root / COMPILE_NAME  # info: self . compile_path = self . root /

    def _check(self, label: str, value: str) -> str:  # info: def _check
        if not SAFE.fullmatch(value or ""):  # info: if not SAFE . fullmatch ( value or
            raise ValueError(f"invalid {label}")  # info: raise ValueError ( f" invalid { label }
        return value  # info: return value

    def _connect(self) -> sqlite3.Connection:  # info: def _connect
        conn = sqlite3.connect(self.db_path)  # info: set conn
        conn.execute("PRAGMA journal_mode=DELETE")  # info: conn . execute ( "PRAGMA journal_mode=DELETE" )
        conn.execute(  # info: conn . execute (
            """CREATE TABLE IF NOT EXISTS sessions(
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                provider TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                title TEXT,
                PRIMARY KEY (user_id, session_id)
            )"""
        )  # info: )
        conn.execute(  # info: conn . execute (
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
        )  # info: )
        return conn  # info: return conn

    def create_session(  # info: def create_session
        self,  # info: self ,
        user_id: str,  # info: set user_id
        session_id: str,  # info: set session_id
        provider: str = "",  # info: set provider
        title: str = "",  # info: set title
    ) -> dict:  # info: ) -> dict :
        self._check("user_id", user_id)  # info: self . _check ( "user_id" , user_id )
        self._check("session_id", session_id)  # info: self . _check ( "session_id" , session_id )
        now = datetime.now(timezone.utc).isoformat()  # info: set now
        with self._connect() as conn:  # info: with self . _connect ( ) as conn
            conn.execute(  # info: conn . execute (
                "INSERT INTO sessions VALUES(?,?,?,?,?,?)",  # info: "INSERT INTO sessions VALUES(?,?,?,?,?,?)" ,
                (user_id, session_id, provider, now, now, title),  # info: call (
            )  # info: )
        self.append_event(  # info: self . append_event (
            user_id,  # info: user_id ,
            session_id,  # info: session_id ,
            "system",  # info: "system" ,
            "session_created",  # info: "session_created" ,
            "Session created",  # info: "Session created" ,
            {"provider": provider, "title": title},  # info: { "provider" : provider , "title" : title
        )  # info: )
        return self.current(user_id, session_id)  # info: return self . current ( user_id , session_id

    def append_event(  # info: def append_event
        self,  # info: self ,
        user_id: str,  # info: set user_id
        session_id: str,  # info: set session_id
        role: str,  # info: set role
        event_type: str,  # info: set event_type
        content: str,  # info: set content
        metadata: dict | None = None,  # info: set metadata
    ) -> dict:  # info: ) -> dict :
        self._check("user_id", user_id)  # info: self . _check ( "user_id" , user_id )
        self._check("session_id", session_id)  # info: self . _check ( "session_id" , session_id )
        now = datetime.now(timezone.utc).isoformat()  # info: set now
        with self._connect() as conn:  # info: with self . _connect ( ) as conn
            conn.execute(  # info: conn . execute (
                """INSERT INTO events(user_id,session_id,ts,role,event_type,content,metadata)
                   VALUES(?,?,?,?,?,?,?)""",
                (  # info: call (
                    user_id,  # info: user_id ,
                    session_id,  # info: session_id ,
                    now,  # info: now ,
                    role,  # info: role ,
                    event_type,  # info: event_type ,
                    content,  # info: content ,
                    json.dumps(metadata or {}, ensure_ascii=False),  # info: json . dumps ( metadata or { }
                ),  # info: ) ,
            )  # info: )
            conn.execute(  # info: conn . execute (
                "UPDATE sessions SET updated_at=? WHERE user_id=? AND session_id=?",  # info: "UPDATE sessions SET updated_at=? WHERE user_id=? AND session_id=?" ,
                (now, user_id, session_id),  # info: call (
            )  # info: )
        self.compile()  # info: self . compile ( )
        return self.current(user_id, session_id)  # info: return self . current ( user_id , session_id

    def current(self, user_id: str, session_id: str) -> dict:  # info: def current
        self._check("user_id", user_id)  # info: self . _check ( "user_id" , user_id )
        self._check("session_id", session_id)  # info: self . _check ( "session_id" , session_id )
        with self._connect() as conn:  # info: with self . _connect ( ) as conn
            rows = conn.execute(  # info: set rows
                """SELECT ts,role,event_type,content,metadata
                   FROM events WHERE user_id=? AND session_id=? ORDER BY id""",
                (user_id, session_id),  # info: call (
            ).fetchall()  # info: ) . fetchall ( )
        events = [  # info: set events
            {  # info: {
                "ts": row[0],  # info: "ts" : row [ 0 ] ,
                "role": row[1],  # info: "role" : row [ 1 ] ,
                "event_type": row[2],  # info: "event_type" : row [ 2 ] ,
                "content": row[3],  # info: "content" : row [ 3 ] ,
                "metadata": json.loads(row[4] or "{}"),  # info: "metadata" : json . loads ( row [
            }  # info: }
            for row in rows  # info: for row in rows
        ]  # info: ]
        return {  # info: return {
            "user_id": user_id,  # info: "user_id" : user_id ,
            "session_id": session_id,  # info: "session_id" : session_id ,
            "events": events,  # info: "events" : events ,
            "event_count": len(events),  # info: "event_count" : len ( events ) ,
            "latest": events[-1] if events else None,  # info: "latest" : events [ - 1 ] if
        }  # info: }

    def list_sessions(self, user_id: str) -> list[dict]:  # info: def list_sessions
        self._check("user_id", user_id)  # info: self . _check ( "user_id" , user_id )
        with self._connect() as conn:  # info: with self . _connect ( ) as conn
            rows = conn.execute(  # info: set rows
                """SELECT session_id,provider,created_at,updated_at,title
                   FROM sessions WHERE user_id=? ORDER BY updated_at DESC""",
                (user_id,),  # info: call (
            ).fetchall()  # info: ) . fetchall ( )
        return [  # info: return [
            {  # info: {
                "session_id": row[0],  # info: "session_id" : row [ 0 ] ,
                "provider": row[1],  # info: "provider" : row [ 1 ] ,
                "created_at": row[2],  # info: "created_at" : row [ 2 ] ,
                "updated_at": row[3],  # info: "updated_at" : row [ 3 ] ,
                "title": row[4],  # info: "title" : row [ 4 ] ,
            }  # info: }
            for row in rows  # info: for row in rows
        ]  # info: ]

    def compile(self) -> dict:  # info: def compile
        """Rewrite one summary file from the sqlite store. Never adds another file."""  # info: """Rewrite one summary file from the sqlite store. Never adds another file."""
        with self._connect() as conn:  # info: with self . _connect ( ) as conn
            users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM sessions").fetchone()[0]  # info: set users
            sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]  # info: set sessions
            events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]  # info: set events
            latest_rows = conn.execute(  # info: set latest_rows
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
            ).fetchall()  # info: ) . fetchall ( )
        summary = {  # info: set summary
            "compiled_at": datetime.now(timezone.utc).isoformat(),  # info: "compiled_at" : datetime . now ( timezone .
            "store": DB_NAME,  # info: "store" : DB_NAME ,
            "users": users,  # info: "users" : users ,
            "sessions": sessions,  # info: "sessions" : sessions ,
            "events": events,  # info: "events" : events ,
            "latest": [  # info: "latest" : [
                {  # info: {
                    "user_id": row[0],  # info: "user_id" : row [ 0 ] ,
                    "session_id": row[1],  # info: "session_id" : row [ 1 ] ,
                    "updated_at": row[2],  # info: "updated_at" : row [ 2 ] ,
                    "title": row[3],  # info: "title" : row [ 3 ] ,
                    "event_count": row[4],  # info: "event_count" : row [ 4 ] ,
                    "latest_role": row[5],  # info: "latest_role" : row [ 5 ] ,
                    "latest_type": row[6],  # info: "latest_type" : row [ 6 ] ,
                }  # info: }
                for row in latest_rows  # info: for row in latest_rows
            ],  # info: ] ,
        }  # info: }
        tmp = self.compile_path.with_suffix(".json.tmp")  # info: set tmp
        tmp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
        tmp.replace(self.compile_path)  # info: tmp . replace ( self . compile_path )
        return summary  # info: return summary
