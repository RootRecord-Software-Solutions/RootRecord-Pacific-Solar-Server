# ==============================================================================
# FILE: Weather/scripts/official_statement.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import re  # info: import re
import sys  # info: import sys
import urllib.request  # info: import urllib . request
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
OUT = DB / "Weather" / "Hawai'i" / "official"  # info: set OUT
UA = "RootRecord-Pacific/3 official-statement (NWS HFO HLS)"  # info: set UA
HLS_PRODUCTS = "https://api.weather.gov/products/types/HLS/locations/HFO"  # info: set HLS_PRODUCTS
HLS_TXT = "https://forecast.weather.gov/product.php?site=HFO&issuedby=HFO&product=HLS&format=txt&version=1&glossary=0"  # info: set HLS_TXT
TIMEOUT = min(20.0, float(os.environ.get("RR_OFFICIAL_TIMEOUT", "15")))  # info: set TIMEOUT


# ====================================================
# SECTION: function _get
# What it does:  get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(url: str, accept: str = "application/ld+json") -> bytes:  # info: def _get
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})  # info: set req
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # info: with urllib . request . urlopen ( req
        return r.read(3_000_000)  # info: return r . read ( 3_000_000 )


# ====================================================
# SECTION: function _clean_hls
# What it does:  clean hls.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clean_hls(text: str) -> str:  # G1, unchanged
    text = text.replace("&&", ". ").replace("$", "").replace("&", "and")  # info: set text
    text = re.sub(r"\s+", " ", text)  # info: set text
    text = re.sub(r"\n\s*\n+", "\n\n", text)  # info: set text
    return text.strip()[:14000] + "\n"  # info: return text . strip ( ) [ :


# ====================================================
# SECTION: function _looks_like_product
# What it does:  looks like product.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _looks_like_product(text: str) -> bool:  # G1, unchanged
    t = (text or "").strip()  # info: set t
    if len(t) < 80:  # info: if len ( t ) < 80 :
        return False  # info: return False
    head = t[:500].lower()  # info: set head
    return not ("<html" in head or "googleanalytics" in head or "xml_logo.gif" in head)  # info: return not ( "<html" in head or "googleanalytics"


# ====================================================
# SECTION: function latest_hls
# What it does: {text, issued, id, source} or {} when NWS HFO has no HLS on file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def latest_hls() -> dict:  # info: def latest_hls
    """{text, issued, id, source} or {} when NWS HFO has no HLS on file."""  # info: """{text, issued, id, source} or {} when NWS HFO has no HLS on file."""
    try:  # info: try :
        items = json.loads(_get(HLS_PRODUCTS)).get("@graph") or []  # info: set items
        if items:  # info: if items :
            pid = items[0].get("@id") or ""  # info: set pid
            body = json.loads(_get(pid)) if pid else {}  # info: set body
            text = str(body.get("productText") or "").strip()  # info: set text
            if _looks_like_product(text):  # info: if _looks_like_product ( text ) :
                return {"text": _clean_hls(text), "issued": items[0].get("issuanceTime"), "id": pid, "source": "api"}  # info: return { "text" : _clean_hls ( text )
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"warn": f"HLS API failed: {type(exc).__name__}: {exc}"[:240]}), file=sys.stderr)  # info: call print
    try:  # info: try :
        raw = _get(HLS_TXT, accept="text/html").decode("utf-8", "replace")  # info: set raw
        pre = re.search(r"<pre[^>]*>(.*?)</pre>", raw, re.I | re.S)  # info: set pre
        text = pre.group(1) if pre else ("" if "<html" in raw.lower() else raw)  # info: set text
        if _looks_like_product(text):  # info: if _looks_like_product ( text ) :
            return {"text": _clean_hls(text), "issued": None, "id": HLS_TXT, "source": "product.php"}  # info: return { "text" : _clean_hls ( text )
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"warn": f"HLS text fallback failed: {type(exc).__name__}"}), file=sys.stderr)  # info: call print
    return {}  # info: return { }


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    OUT.mkdir(parents=True, exist_ok=True)  # info: OUT . mkdir ( parents = True ,
    cur = OUT / "HLS_current.txt"  # info: set cur
    hls = latest_hls()  # info: set hls
    prior = cur.read_text(encoding="utf-8") if cur.is_file() else ""  # info: set prior
    text = hls.get("text", "")  # info: set text
    changed = bool(text) and hashlib.sha256(prior.encode()).hexdigest() != hashlib.sha256(text.encode()).hexdigest()  # info: set changed
    if changed:  # info: if changed :
        tmp = cur.with_suffix(".txt.tmp")  # info: set tmp
        tmp.write_text(text, encoding="utf-8")  # info: tmp . write_text ( text , encoding =
        os.replace(tmp, cur)  # info: os . replace ( tmp , cur )
    state = {"ok": bool(text), "at": datetime.now(HST).isoformat(timespec="seconds"),  # info: set state
             "hls": {"issued": hls.get("issued"), "id": hls.get("id"), "source": hls.get("source"),  # info: "hls" : { "issued" : hls . get
                     "chars": len(text), "changed": changed, "file": str(cur.relative_to(DB)) if text else None}}  # info: "chars" : len ( text ) , "changed"
    tmp = OUT / "official-last.json.tmp"  # info: set tmp
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, OUT / "official-last.json")  # info: os . replace ( tmp , OUT /
    print(json.dumps(state))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
