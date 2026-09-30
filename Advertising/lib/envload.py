#!/usr/bin/env python3
"""Load AdSense and AdMob key names from central master-key.env only. Never print secrets."""
from __future__ import annotations

import os
from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")
ALLOW = frozenset({
    "GOOGLE_ADSENSE_CLIENT_ID",
    "GOOGLE_ADSENSE_CLIENT_SECRET",
    "GOOGLE_ADSENSE_REFRESH_TOKEN",
    "GOOGLE_ADSENSE_ACCOUNT_NAME",
    "GOOGLE_ADSENSE_CURRENCY",
    "GOOGLE_ADMOB_CLIENT_ID",
    "GOOGLE_ADMOB_CLIENT_SECRET",
    "GOOGLE_ADMOB_REFRESH_TOKEN",
    "GOOGLE_ADMOB_ACCOUNT_NAME",
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


def _value(name: str) -> str:
    load_env()
    return (os.environ.get(name) or "").strip()


def adsense_credentials() -> tuple[str, str, str]:
    """Client id, client secret, refresh token. Empty strings when absent."""
    return (
        _value("GOOGLE_ADSENSE_CLIENT_ID"),
        _value("GOOGLE_ADSENSE_CLIENT_SECRET"),
        _value("GOOGLE_ADSENSE_REFRESH_TOKEN"),
    )


def admob_credentials() -> tuple[str, str, str]:
    """AdMob client id and secret fall back to the AdSense client. The refresh token does not."""
    client_id = _value("GOOGLE_ADMOB_CLIENT_ID") or _value("GOOGLE_ADSENSE_CLIENT_ID")
    client_secret = _value("GOOGLE_ADMOB_CLIENT_SECRET") or _value("GOOGLE_ADSENSE_CLIENT_SECRET")
    refresh = _value("GOOGLE_ADMOB_REFRESH_TOKEN")
    return client_id, client_secret, refresh


def adsense_account_name() -> str:
    return _value("GOOGLE_ADSENSE_ACCOUNT_NAME")


def admob_account_name() -> str:
    return _value("GOOGLE_ADMOB_ACCOUNT_NAME")


def adsense_currency() -> str:
    return _value("GOOGLE_ADSENSE_CURRENCY") or "USD"
