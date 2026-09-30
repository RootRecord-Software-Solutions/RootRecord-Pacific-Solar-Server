#!/usr/bin/env python3
"""Load ApiPrices key names from master-key.env. Never print values."""
from __future__ import annotations

import os
from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")
ALLOW = frozenset({
    "XAI_API_KEY",
    "XAI_MGMT_KEY",
    "XAI_TEAM_ID",
    "CURSOR_API_KEY",
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


def key_set(name: str) -> bool:
    """True when an allowlisted name is non-empty. Does not return the value."""
    if name not in ALLOW:
        return False
    load_env()
    return bool((os.environ.get(name) or "").strip())
