# ==============================================================================
# FILE: System/MysqlDesk/lib/envload.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Load MySQL desk-fact key names from master-key.env. Never print values."""  # info: """Load MySQL desk-fact key names from master-key.env. Never print values."""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
from pathlib import Path  # info: from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")  # info: set MASTER_KEY_ENV
# ====================================================
# SECTION: ALLOW
# What it does: Set ALLOW.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ALLOW = frozenset({  # info: set ALLOW
    "ROOTMC_CORE_MYSQL_HOST",  # info: "ROOTMC_CORE_MYSQL_HOST" ,
    "ROOTMC_CORE_MYSQL_PORT",  # info: "ROOTMC_CORE_MYSQL_PORT" ,
    "ROOTMC_CORE_MYSQL_USER",  # info: "ROOTMC_CORE_MYSQL_USER" ,
    "ROOTMC_CORE_MYSQL_PASSWORD",  # info: "ROOTMC_CORE_MYSQL_PASSWORD" ,
    "ROOTMC_CORE_MYSQL_DATABASE",  # info: "ROOTMC_CORE_MYSQL_DATABASE" ,
    "AVA_MYSQL_HOST",  # info: "AVA_MYSQL_HOST" ,
    "AVA_MYSQL_PORT",  # info: "AVA_MYSQL_PORT" ,
    "AVA_MYSQL_USER",  # info: "AVA_MYSQL_USER" ,
    "AVA_MYSQL_PASSWORD",  # info: "AVA_MYSQL_PASSWORD" ,
    "AVA_MYSQL_DATABASE",  # info: "AVA_MYSQL_DATABASE" ,
})  # info: } )


# ====================================================
# SECTION: function load_env
# What it does: load env.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_env(paths: list[Path] | None = None) -> None:  # info: def load_env
    for env in paths or [MASTER_KEY_ENV]:  # info: for env in paths or [ MASTER_KEY_ENV ]
        if not env.is_file():  # info: if not env . is_file ( ) :
            continue  # info: continue
        for line in env.read_text(encoding="utf-8", errors="replace").splitlines():  # info: for line in env . read_text ( encoding
            s = line.strip()  # info: set s
            if not s or s.startswith("#") or "=" not in s:
                continue  # info: continue
            k, _, v = s.partition("=")  # info: k , _ , v = s .
            k, v = k.strip(), v.strip().strip('"').strip("'")  # info: k , v = k . strip (
            if not k or k not in ALLOW:  # info: if not k or k not in ALLOW
                continue  # info: continue
            if k not in os.environ:  # info: if k not in os . environ :
                os.environ[k] = v  # info: os . environ [ k ] = v


# ====================================================
# SECTION: function _port
# What it does:  port.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _port(prefix: str) -> int | None:  # info: def _port
    raw = (os.environ.get(f"{prefix}_PORT") or "3306").split("#")[0].strip() or "3306"
    try:  # info: try :
        port = int(raw)  # info: set port
    except ValueError:  # info: except ValueError :
        return None  # info: return None
    if port < 1 or port > 65535:  # info: if port < 1 or port > 65535
        return None  # info: return None
    return port  # info: return port


# ====================================================
# SECTION: function configured
# What it does: Shockbyte is ROOTMC_CORE_MYSQL. Local fallback is AVA_MYSQL. All of host, user, password, and database must be set. An incomplete set is skipped. The returned dict is for the conne
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def configured(prefix: str) -> dict[str, object] | None:  # info: def configured
    """Shockbyte is ROOTMC_CORE_MYSQL. Local fallback is AVA_MYSQL.

    All of host, user, password, and database must be set. An incomplete set
    is skipped. The returned dict is for the connector only. Do not log it.
    """
    load_env()  # info: call load_env
    host = (os.environ.get(f"{prefix}_HOST") or "").strip()  # info: set host
    user = (os.environ.get(f"{prefix}_USER") or "").strip()  # info: set user
    password = os.environ.get(f"{prefix}_PASSWORD") or ""  # info: set password
    database = (os.environ.get(f"{prefix}_DATABASE") or "").strip()  # info: set database
    if not (host and user and password and database):  # info: if not ( host and user and password
        return None  # info: return None
    port = _port(prefix)  # info: set port
    if port is None:  # info: if port is None :
        return None  # info: return None
    return {  # info: return {
        "host": host,  # info: "host" : host ,
        "port": port,  # info: "port" : port ,
        "user": user,  # info: "user" : user ,
        "password": password,  # info: "password" : password ,
        "database": database,  # info: "database" : database ,
    }  # info: }
