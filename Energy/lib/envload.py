#!/usr/bin/env python3
"""Load EcoFlow keys from central master-key.env only. Never print secrets."""
from __future__ import annotations

import os
from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")
ALLOW = frozenset({
    "AVA_ECOFLOW_USER_ID",
    "ECOFLOW_ACCOUNT_ID",
    "ECOFLOW_DELTA_2",
    "ECOFLOW_RIVER_2_PRO",
    "ECOFLOW_DELTA_2_SECONDARY",
    "ECOFLOW_DELTA_2_NAME",
    "ECOFLOW_DELTA_2_SECONDARY_NAME",
    "ECOFLOW_RIVER_2_PRO_NAME",
    "ECOFLOW_ACCESS",
    "ECOFLOW_SECRET",
    "ECOFLOW_REGION",
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


def user_id() -> str:
    load_env()
    uid = (os.environ.get("AVA_ECOFLOW_USER_ID") or "").strip()
    if not uid:
        uid = (os.environ.get("ECOFLOW_ACCOUNT_ID") or "").strip()
    return uid


def api_keys() -> tuple[str, str]:
    load_env()
    access = (os.environ.get("ECOFLOW_ACCESS") or "").strip()
    secret = (os.environ.get("ECOFLOW_SECRET") or "").strip()
    return access, secret


def env_sn(alias: str) -> str:
    """Resolve SN from env the same way BLE inventory names are set."""
    load_env()
    key = {
        "delta2": "ECOFLOW_DELTA_2",
        "river2pro": "ECOFLOW_RIVER_2_PRO",
        "security": "ECOFLOW_DELTA_2_SECONDARY",
        "b3": "ECOFLOW_DELTA_2_SECONDARY",
    }.get(alias, "")
    return (os.environ.get(key) or "").strip() if key else ""


def env_name(alias: str) -> str:
    load_env()
    key = {
        "delta2": "ECOFLOW_DELTA_2_NAME",
        "river2pro": "ECOFLOW_RIVER_2_PRO_NAME",
        "security": "ECOFLOW_DELTA_2_SECONDARY_NAME",
        "b3": "ECOFLOW_DELTA_2_SECONDARY_NAME",
    }.get(alias, "")
    return (os.environ.get(key) or "").strip() if key else ""
