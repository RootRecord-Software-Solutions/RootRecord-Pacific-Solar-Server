#!/usr/bin/env python3
"""Load Stripe and Vercel key names from central master-key.env only. Never print secrets."""
from __future__ import annotations

import os
from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")
ALLOW = frozenset({
    "STRIPE_SECRET_KEY",
    "AVA_STRIPE_SECRET_KEY",
    "VERCEL_TOKEN",
    "VERCEL_API_TOKEN",
    "VERCEL_TEAM_ID",
    "VERCEL_ORG_ID",
})


def load_env(paths: list[Path] | None = None) -> None:
    for env in paths or [MASTER_KEY_ENV]:
        if not env.is_file():
            return
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


def stripe_secret() -> str:
    load_env()
    return (os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("AVA_STRIPE_SECRET_KEY") or "").strip()


def vercel_token() -> str:
    load_env()
    return (os.environ.get("VERCEL_TOKEN") or os.environ.get("VERCEL_API_TOKEN") or "").strip()


def vercel_team_id() -> str:
    load_env()
    return (os.environ.get("VERCEL_TEAM_ID") or os.environ.get("VERCEL_ORG_ID") or "").strip()
