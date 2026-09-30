#!/usr/bin/env python3
"""Official NWS Honolulu hurricane local statement (HLS) fetch — G3 port of the HLS part of
G1 weather/official-weather-media/scripts/official_weather_media.py (2026-09-29 old-repo migration).

Standalone and additive: the weather poller already stores AFD / SFP / ZFP / CWF / NOW / HWO (fetch/text_products.py)
and the wwamap / IR satellite imagery; it defines but never fetches HLS (hurricanes/scripts/sources.py
CPHC_PRODUCT_TYPES). This script fills only that gap and does not touch the poller.

  python3 official_statement.py      -> Database Weather/Hawai'i/official/HLS_current.txt + official-last.json

Ported unchanged: _clean_hls, _looks_like_product, API-first (products/types/HLS/locations/HFO @graph[0] -> productText)
with the forecast.weather.gov product.php <pre> fallback. Not ported: NHC page / graphic downloads (poller has the
imagery; pages were OBS browser sources), the all-time zip archive, OBS scenes, WAV render (voice_reports.py
official_weather builds the spoken text). Current file overwritten in place; nothing dated, nothing deleted.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
OUT = DB / "Weather" / "Hawai'i" / "official"
UA = "RootRecord-Pacific/3 official-statement (NWS HFO HLS)"
HLS_PRODUCTS = "https://api.weather.gov/products/types/HLS/locations/HFO"
HLS_TXT = "https://forecast.weather.gov/product.php?site=HFO&issuedby=HFO&product=HLS&format=txt&version=1&glossary=0"
TIMEOUT = min(20.0, float(os.environ.get("RR_OFFICIAL_TIMEOUT", "15")))


def _get(url: str, accept: str = "application/ld+json") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(3_000_000)


def _clean_hls(text: str) -> str:  # G1, unchanged
    text = text.replace("&&", ". ").replace("$", "").replace("&", "and")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()[:14000] + "\n"


def _looks_like_product(text: str) -> bool:  # G1, unchanged
    t = (text or "").strip()
    if len(t) < 80:
        return False
    head = t[:500].lower()
    return not ("<html" in head or "googleanalytics" in head or "xml_logo.gif" in head)


def latest_hls() -> dict:
    """{text, issued, id, source} or {} when NWS HFO has no HLS on file."""
    try:
        items = json.loads(_get(HLS_PRODUCTS)).get("@graph") or []
        if items:
            pid = items[0].get("@id") or ""
            body = json.loads(_get(pid)) if pid else {}
            text = str(body.get("productText") or "").strip()
            if _looks_like_product(text):
                return {"text": _clean_hls(text), "issued": items[0].get("issuanceTime"), "id": pid, "source": "api"}
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"warn": f"HLS API failed: {type(exc).__name__}: {exc}"[:240]}), file=sys.stderr)
    try:
        raw = _get(HLS_TXT, accept="text/html").decode("utf-8", "replace")
        pre = re.search(r"<pre[^>]*>(.*?)</pre>", raw, re.I | re.S)
        text = pre.group(1) if pre else ("" if "<html" in raw.lower() else raw)
        if _looks_like_product(text):
            return {"text": _clean_hls(text), "issued": None, "id": HLS_TXT, "source": "product.php"}
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"warn": f"HLS text fallback failed: {type(exc).__name__}"}), file=sys.stderr)
    return {}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cur = OUT / "HLS_current.txt"
    hls = latest_hls()
    prior = cur.read_text(encoding="utf-8") if cur.is_file() else ""
    text = hls.get("text", "")
    changed = bool(text) and hashlib.sha256(prior.encode()).hexdigest() != hashlib.sha256(text.encode()).hexdigest()
    if changed:
        tmp = cur.with_suffix(".txt.tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, cur)
    state = {"ok": bool(text), "at": datetime.now(HST).isoformat(timespec="seconds"),
             "hls": {"issued": hls.get("issued"), "id": hls.get("id"), "source": hls.get("source"),
                     "chars": len(text), "changed": changed, "file": str(cur.relative_to(DB)) if text else None}}
    tmp = OUT / "official-last.json.tmp"
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, OUT / "official-last.json")
    print(json.dumps(state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
