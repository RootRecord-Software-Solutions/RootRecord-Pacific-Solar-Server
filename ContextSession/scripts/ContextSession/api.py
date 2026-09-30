"""Optional FastAPI factory. Importing this module does not bind a port.

Nothing in this package calls create_app. A listener needs Alexander's sign-off.
"""
from __future__ import annotations

from .store import DEFAULT_ROOT, SessionStore


def create_app(root=None):
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("FastAPI is required by the optional API adapter") from exc

    app = FastAPI(title="Ava Ivy Context Session API")
    store = SessionStore(root or DEFAULT_ROOT)

    @app.get("/health")
    def health():
        return {"ok": True, "service": "context-session-builder"}

    @app.post("/users/{user_id}/sessions/{session_id}")
    def create(user_id, session_id, provider="", title=""):
        store.create_session(user_id, session_id, provider, title)
        return store.current(user_id, session_id)

    @app.post("/users/{user_id}/sessions/{session_id}/events")
    def event(user_id, session_id, role, event_type, content, metadata=None):
        try:
            return store.append_event(
                user_id, session_id, role, event_type, content, metadata
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/users/{user_id}/sessions")
    def sessions(user_id):
        return {"user_id": user_id, "sessions": store.list_sessions(user_id)}

    @app.get("/users/{user_id}/sessions/{session_id}")
    def current(user_id, session_id):
        return store.current(user_id, session_id)

    return app
