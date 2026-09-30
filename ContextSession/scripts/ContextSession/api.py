# ==============================================================================
# FILE: ContextSession/scripts/ContextSession/api.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Optional FastAPI factory. Importing this module does not bind a port.

Nothing in this package calls create_app. A listener needs Alexander's sign-off.
"""
from __future__ import annotations  # info: from __future__ import annotations

from .store import DEFAULT_ROOT, SessionStore  # info: from . store import DEFAULT_ROOT , SessionStore


# ====================================================
# SECTION: function create_app
# What it does: create app.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def create_app(root=None):  # info: def create_app
    try:  # info: try :
        from fastapi import FastAPI, HTTPException  # info: from fastapi import FastAPI , HTTPException
    except ImportError as exc:  # info: except ImportError as exc :
        raise RuntimeError("FastAPI is required by the optional API adapter") from exc  # info: raise RuntimeError ( "FastAPI is required by the optional API adapter" ) from exc

    app = FastAPI(title="Ava Ivy Context Session API")  # info: set app
    store = SessionStore(root or DEFAULT_ROOT)  # info: set store

    @app.get("/health")  # info: decorator app . get
    def health():  # info: def health
        return {"ok": True, "service": "context-session-builder"}  # info: return { "ok" : True , "service" :

    @app.post("/users/{user_id}/sessions/{session_id}")  # info: decorator app . post
    def create(user_id, session_id, provider="", title=""):  # info: def create
        store.create_session(user_id, session_id, provider, title)  # info: store . create_session ( user_id , session_id ,
        return store.current(user_id, session_id)  # info: return store . current ( user_id , session_id

    @app.post("/users/{user_id}/sessions/{session_id}/events")  # info: decorator app . post
    def event(user_id, session_id, role, event_type, content, metadata=None):  # info: def event
        try:  # info: try :
            return store.append_event(  # info: return store . append_event (
                user_id, session_id, role, event_type, content, metadata  # info: user_id , session_id , role , event_type ,
            )  # info: )
        except ValueError as exc:  # info: except ValueError as exc :
            raise HTTPException(400, str(exc)) from exc  # info: raise HTTPException ( 400 , str ( exc

    @app.get("/users/{user_id}/sessions")  # info: decorator app . get
    def sessions(user_id):  # info: def sessions
        return {"user_id": user_id, "sessions": store.list_sessions(user_id)}  # info: return { "user_id" : user_id , "sessions" :

    @app.get("/users/{user_id}/sessions/{session_id}")  # info: decorator app . get
    def current(user_id, session_id):  # info: def current
        return store.current(user_id, session_id)  # info: return store . current ( user_id , session_id

    return app  # info: return app
