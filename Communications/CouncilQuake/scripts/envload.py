#!/usr/bin/env python3
"""Load the Carly Telegram token from master-key.env. Never print the value."""
from __future__ import annotations

import os
from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")
ALLOW = frozenset({"TELEGRAM_CARLY_TOKEN"})


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


def carly_token() -> str:
    load_env()
    return (os.environ.get("TELEGRAM_CARLY_TOKEN") or "").strip()
