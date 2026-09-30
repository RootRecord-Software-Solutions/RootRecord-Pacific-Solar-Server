#!/usr/bin/env python3
"""Load MySQL desk-fact key names from master-key.env. Never print values."""
from __future__ import annotations

import os
from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")
ALLOW = frozenset({
    "ROOTMC_CORE_MYSQL_HOST",
    "ROOTMC_CORE_MYSQL_PORT",
    "ROOTMC_CORE_MYSQL_USER",
    "ROOTMC_CORE_MYSQL_PASSWORD",
    "ROOTMC_CORE_MYSQL_DATABASE",
    "AVA_MYSQL_HOST",
    "AVA_MYSQL_PORT",
    "AVA_MYSQL_USER",
    "AVA_MYSQL_PASSWORD",
    "AVA_MYSQL_DATABASE",
})


def load_env(paths: list[Path] | None = None) -> None:
    for env in paths or [MASTER_KEY_ENV]:
        if not env.is_file():
            continue
        for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, _, v = s.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if not k or k not in ALLOW:
                continue
            if k not in os.environ:
                os.environ[k] = v


def _port(prefix: str) -> int | None:
    raw = (os.environ.get(f"{prefix}_PORT") or "3306").split("#")[0].strip() or "3306"
    try:
        port = int(raw)
    except ValueError:
        return None
    if port < 1 or port > 65535:
        return None
    return port


def configured(prefix: str) -> dict[str, object] | None:
    """Shockbyte is ROOTMC_CORE_MYSQL. Local fallback is AVA_MYSQL.

    All of host, user, password, and database must be set. An incomplete set
    is skipped. The returned dict is for the connector only. Do not log it.
    """
    load_env()
    host = (os.environ.get(f"{prefix}_HOST") or "").strip()
    user = (os.environ.get(f"{prefix}_USER") or "").strip()
    password = os.environ.get(f"{prefix}_PASSWORD") or ""
    database = (os.environ.get(f"{prefix}_DATABASE") or "").strip()
    if not (host and user and password and database):
        return None
    port = _port(prefix)
    if port is None:
        return None
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
    }
