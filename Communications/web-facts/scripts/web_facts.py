"""Allowlisted HTTPS GET for council facts. No cookies, no JS, no skill auto-install.

G3 port (2026-09-29, old-repo migration) of G1 websites/web-facts/scripts/web_facts.py, logic unchanged.
On demand only (CLI / import); not wired to the council relay (council chat replies are BLOCKED).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from urllib.parse import urlparse

HOSTS = frozenset(
    {
        "api.weather.gov",
        "earthquake.usgs.gov",
        "en.wikipedia.org",
        "lite.wikipedia.org",
        "docs.litecoin.org",
        "download.litecoin.org",
    }
)
CAP = 8_000
TIMEOUT = 8


def allowed(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme != "https":
        return False
    host = (p.hostname or "").lower()
    return host in HOSTS


def fetch(url: str) -> dict[str, str | bool]:
    target = (url or "").strip()
    if not allowed(target):
        return {"ok": False, "error": "host_not_allowlisted"}
    req = urllib.request.Request(
        target,
        headers={"User-Agent": "RootRecord-council-facts/1.0", "Accept": "text/plain, text/html, application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read(CAP + 1)
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"http_{e.code}"}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}
    text = raw[:CAP].decode("utf-8", errors="replace")
    return {"ok": True, "url": target, "text": text, "truncated": len(raw) > CAP}


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        print(json.dumps({"ok": False, "error": "usage", "hosts": sorted(HOSTS)}))
        return 2
    print(json.dumps(fetch(args[0]), indent=2)[:9000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
