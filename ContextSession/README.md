# ContextSession

Per-user context session store. On demand. No poller and no listening port.

---

## Status (2026-09-30 HST — WO-MIG-43)

| Item | State |
| --- | --- |
| Domain folder | **`ContextSession/` only** (no lowercase twin) |
| Package | `scripts/ContextSession` |
| CLI | `scripts/context_session.py` — create, append, list, current |
| Listener | FastAPI factory is in `api.py` and is not called. No `serve` command. |
| Data | Database `2 - RootRecord-Database/ContextSession/` — one `{user_id}.db` per user (git-ignored) |
| Logs | Database `Logs/ContextSession/` — reserved. The CLI prints JSON and does not write a log file. |
| jobs.py | Not edited. No periodic job. |
| Secrets | None |

### Command

```text
python3 context_session.py --root DIR create USER SESSION [--provider P] [--title T]
python3 context_session.py --root DIR append USER SESSION ROLE TYPE CONTENT
python3 context_session.py --root DIR list USER
python3 context_session.py --root DIR current USER SESSION
```

`--root` defaults to the Database folder above. User ids and session ids must match `[A-Za-z0-9._-]{1,128}`.

Ported from `old/operations/context_session_builder`. Placeholder READMEs under `scripts/ContextSession/placeholders/` are not implemented. EcoFlow BLE, the poller, Hawaiʻi weather, the globe collector, camera grabs, Kokoro, and `geology_collect.py` are untouched.
