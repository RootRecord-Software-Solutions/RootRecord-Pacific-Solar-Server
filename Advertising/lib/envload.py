# ==============================================================================
# FILE: Advertising/lib/envload.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Load AdSense and AdMob key names from central master-key.env only. Never print secrets."""  # info: """Load AdSense and AdMob key names from central master-key.env only. Never print secrets."""
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
    "GOOGLE_ADSENSE_CLIENT_ID",  # info: "GOOGLE_ADSENSE_CLIENT_ID" ,
    "GOOGLE_ADSENSE_CLIENT_SECRET",  # info: "GOOGLE_ADSENSE_CLIENT_SECRET" ,
    "GOOGLE_ADSENSE_REFRESH_TOKEN",  # info: "GOOGLE_ADSENSE_REFRESH_TOKEN" ,
    "GOOGLE_ADSENSE_ACCOUNT_NAME",  # info: "GOOGLE_ADSENSE_ACCOUNT_NAME" ,
    "GOOGLE_ADSENSE_CURRENCY",  # info: "GOOGLE_ADSENSE_CURRENCY" ,
    "GOOGLE_ADMOB_CLIENT_ID",  # info: "GOOGLE_ADMOB_CLIENT_ID" ,
    "GOOGLE_ADMOB_CLIENT_SECRET",  # info: "GOOGLE_ADMOB_CLIENT_SECRET" ,
    "GOOGLE_ADMOB_REFRESH_TOKEN",  # info: "GOOGLE_ADMOB_REFRESH_TOKEN" ,
    "GOOGLE_ADMOB_ACCOUNT_NAME",  # info: "GOOGLE_ADMOB_ACCOUNT_NAME" ,
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
# SECTION: function _value
# What it does:  value.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _value(name: str) -> str:  # info: def _value
    load_env()  # info: call load_env
    return (os.environ.get(name) or "").strip()  # info: return ( os . environ . get (


# ====================================================
# SECTION: function adsense_credentials
# What it does: Client id, client secret, refresh token. Empty strings when absent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def adsense_credentials() -> tuple[str, str, str]:  # info: def adsense_credentials
    """Client id, client secret, refresh token. Empty strings when absent."""  # info: """Client id, client secret, refresh token. Empty strings when absent."""
    return (  # info: return (
        _value("GOOGLE_ADSENSE_CLIENT_ID"),  # info: call _value
        _value("GOOGLE_ADSENSE_CLIENT_SECRET"),  # info: call _value
        _value("GOOGLE_ADSENSE_REFRESH_TOKEN"),  # info: call _value
    )  # info: )


# ====================================================
# SECTION: function admob_credentials
# What it does: AdMob client id and secret fall back to the AdSense client. The refresh token does not.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def admob_credentials() -> tuple[str, str, str]:  # info: def admob_credentials
    """AdMob client id and secret fall back to the AdSense client. The refresh token does not."""  # info: """AdMob client id and secret fall back to the AdSense client. The refresh token does not."""
    client_id = _value("GOOGLE_ADMOB_CLIENT_ID") or _value("GOOGLE_ADSENSE_CLIENT_ID")  # info: set client_id
    client_secret = _value("GOOGLE_ADMOB_CLIENT_SECRET") or _value("GOOGLE_ADSENSE_CLIENT_SECRET")  # info: set client_secret
    refresh = _value("GOOGLE_ADMOB_REFRESH_TOKEN")  # info: set refresh
    return client_id, client_secret, refresh  # info: return client_id , client_secret , refresh


# ====================================================
# SECTION: function adsense_account_name
# What it does: adsense account name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def adsense_account_name() -> str:  # info: def adsense_account_name
    return _value("GOOGLE_ADSENSE_ACCOUNT_NAME")  # info: return _value ( "GOOGLE_ADSENSE_ACCOUNT_NAME" )


# ====================================================
# SECTION: function admob_account_name
# What it does: admob account name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def admob_account_name() -> str:  # info: def admob_account_name
    return _value("GOOGLE_ADMOB_ACCOUNT_NAME")  # info: return _value ( "GOOGLE_ADMOB_ACCOUNT_NAME" )


# ====================================================
# SECTION: function adsense_currency
# What it does: adsense currency.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def adsense_currency() -> str:  # info: def adsense_currency
    return _value("GOOGLE_ADSENSE_CURRENCY") or "USD"  # info: return _value ( "GOOGLE_ADSENSE_CURRENCY" ) or "USD"
