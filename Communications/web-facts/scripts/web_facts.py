# ==============================================================================
# FILE: Communications/web-facts/scripts/web_facts.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Allowlisted HTTPS GET for council facts. No cookies, no JS, no skill auto-install.

G3 port (2026-09-29, old-repo migration) of G1 websites/web-facts/scripts/web_facts.py, logic unchanged.
On demand only (CLI / import); not wired to the council relay (council chat replies are BLOCKED).
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
from urllib.parse import urlparse  # info: from urllib . parse import urlparse

# ====================================================
# SECTION: HOSTS
# What it does: Set HOSTS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
HOSTS = frozenset(  # info: set HOSTS
    {  # info: {
        "api.weather.gov",  # info: "api.weather.gov" ,
        "earthquake.usgs.gov",  # info: "earthquake.usgs.gov" ,
        "en.wikipedia.org",  # info: "en.wikipedia.org" ,
        "lite.wikipedia.org",  # info: "lite.wikipedia.org" ,
        "docs.litecoin.org",  # info: "docs.litecoin.org" ,
        "download.litecoin.org",  # info: "download.litecoin.org" ,
    }  # info: }
)  # info: )
CAP = 8_000  # info: set CAP
TIMEOUT = 8  # info: set TIMEOUT


# ====================================================
# SECTION: function allowed
# What it does: allowed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def allowed(url: str) -> bool:  # info: def allowed
    try:  # info: try :
        p = urlparse(url)  # info: set p
    except Exception:  # info: except Exception :
        return False  # info: return False
    if p.scheme != "https":  # info: if p . scheme != "https" :
        return False  # info: return False
    host = (p.hostname or "").lower()  # info: set host
    return host in HOSTS  # info: return host in HOSTS


# ====================================================
# SECTION: function fetch
# What it does: fetch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch(url: str) -> dict[str, str | bool]:  # info: def fetch
    target = (url or "").strip()  # info: set target
    if not allowed(target):  # info: if not allowed ( target ) :
        return {"ok": False, "error": "host_not_allowlisted"}  # info: return { "ok" : False , "error" :
    req = urllib.request.Request(  # info: set req
        target,  # info: target ,
        headers={"User-Agent": "RootRecord-council-facts/1.0", "Accept": "text/plain, text/html, application/json"},  # info: set headers
        method="GET",  # info: set method
    )  # info: )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # info: with urllib . request . urlopen ( req
            raw = resp.read(CAP + 1)  # info: set raw
    except urllib.error.HTTPError as e:  # info: except urllib . error . HTTPError as e
        return {"ok": False, "error": f"http_{e.code}"}  # info: return { "ok" : False , "error" :
    except Exception as e:  # info: except Exception as e :
        return {"ok": False, "error": type(e).__name__}  # info: return { "ok" : False , "error" :
    text = raw[:CAP].decode("utf-8", errors="replace")  # info: set text
    return {"ok": True, "url": target, "text": text, "truncated": len(raw) > CAP}  # info: return { "ok" : True , "url" :


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    import sys  # info: import sys

    args = list(argv if argv is not None else sys.argv[1:])  # info: set args
    if not args:  # info: if not args :
        print(json.dumps({"ok": False, "error": "usage", "hosts": sorted(HOSTS)}))  # info: call print
        return 2  # info: return 2
    print(json.dumps(fetch(args[0]), indent=2)[:9000])  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
