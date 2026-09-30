# ==============================================================================
# FILE: Weather/discovery/hazard_catalog.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Deterministic discovery of NWS/NOAA hazard product catalogs.

This is intentionally a crawler/parser, not an AI classifier. It follows
explicit seed URLs, extracts links and AWIPS-like product identifiers, and
writes a reviewable inventory so new hazard products can be added without
manually clicking through pages.
"""
from __future__ import annotations  # info: from __future__ import annotations
import json  # info: import json
import re  # info: import re
from html.parser import HTMLParser  # info: from html . parser import HTMLParser
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import urljoin, urlparse  # info: from urllib . parse import urljoin , urlparse
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen

AWIPS_RE = re.compile(r"\b[A-Z0-9]{3,8}(?:HFO|HI|PHFO)?\b")  # info: set AWIPS_RE
# ====================================================
# SECTION: HAZARD_WORDS
# What it does: Set HAZARD_WORDS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
HAZARD_WORDS = re.compile(  # info: set HAZARD_WORDS
    r"\b(warning|watch|advisory|statement|outlook|emergency|hazard|"  # info: r"\b(warning|watch|advisory|statement|outlook|emergency|hazard|"
    r"tsunami|flood|fire|wind|surf|storm|volcano|earthquake|marine|"  # info: r"tsunami|flood|fire|wind|surf|storm|volcano|earthquake|marine|"
    r"tropical|avalanche|civil|non-precipitation|severe)\b", re.I  # info: r"tropical|avalanche|civil|non-precipitation|severe)\b" , re . I
)  # info: )

# ====================================================
# SECTION: class _Links
# What it does:  Links.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class _Links(HTMLParser):  # info: class _Links
    def __init__(self):  # info: def __init__
        super().__init__()  # info: call super
        self.links = []  # info: self . links = [ ]
        self.text = []  # info: self . text = [ ]
    def handle_starttag(self, tag, attrs):  # info: def handle_starttag
        if tag.lower() != "a":  # info: if tag . lower ( ) != "a"
            return  # info: return
        for k, v in attrs:  # info: for k , v in attrs :
            if k.lower() == "href" and v:  # info: if k . lower ( ) == "href"
                self.links.append(v)  # info: self . links . append ( v )
    def handle_data(self, data):  # info: def handle_data
        self.text.append(data)  # info: self . text . append ( data )

# ====================================================
# SECTION: function fetch_html
# What it does: fetch html.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_html(url: str, timeout: float = 20.0) -> str:  # info: def fetch_html
    req = Request(url, headers={"User-Agent": "RootRecord-Weather-Inventory/1.0"})  # info: set req
    with urlopen(req, timeout=timeout) as response:  # info: with urlopen ( req , timeout = timeout
        return response.read().decode("utf-8", errors="replace")  # info: return response . read ( ) . decode

# ====================================================
# SECTION: function discover
# What it does: discover.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def discover(seeds: list[str], max_depth: int = 1) -> dict:  # info: def discover
    seen = set()  # info: set seen
    queue = [(u, 0) for u in seeds]  # info: set queue
    products = {}  # info: set products
    links = []  # info: set links
    while queue:  # info: while queue :
        url, depth = queue.pop(0)  # info: url , depth = queue . pop (
        if url in seen or depth > max_depth:  # info: if url in seen or depth > max_depth
            continue  # info: continue
        seen.add(url)  # info: seen . add ( url )
        try:  # info: try :
            html = fetch_html(url)  # info: set html
        except Exception as exc:  # info: except Exception as exc :
            links.append({"url": url, "error": str(exc)})  # info: links . append ( { "url" : url
            continue  # info: continue
        parser = _Links()  # info: set parser
        parser.feed(html)  # info: parser . feed ( html )
        text = "\n".join(parser.text)  # info: set text
        ids = sorted(set(m.group(0) for m in AWIPS_RE.finditer(text) if HAZARD_WORDS.search(text[max(0, m.start()-120):m.end()+120])))  # info: set ids
        for product_id in ids:  # info: for product_id in ids :
            products.setdefault(product_id, {"sources": []})  # info: products . setdefault ( product_id , { "sources"
            products[product_id]["sources"].append(url)  # info: products [ product_id ] [ "sources" ] .
        for href in parser.links:  # info: for href in parser . links :
            target = urljoin(url, href)  # info: set target
            if urlparse(target).scheme not in {"http", "https"}:  # info: if urlparse ( target ) . scheme not
                continue  # info: continue
            if urlparse(target).netloc != urlparse(url).netloc:  # info: if urlparse ( target ) . netloc !=
                continue  # info: continue
            links.append({"from": url, "url": target})  # info: links . append ( { "from" : url
            if depth < max_depth and HAZARD_WORDS.search(target):  # info: if depth < max_depth and HAZARD_WORDS . search
                queue.append((target, depth + 1))  # info: queue . append ( ( target , depth
    return {"seeds": seeds, "products": products, "links": links}  # info: return { "seeds" : seeds , "products" :

# ====================================================
# SECTION: function write_inventory
# What it does: write inventory.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_inventory(output: str, seeds: list[str], max_depth: int = 1) -> Path:  # info: def write_inventory
    path = Path(output)  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    path.write_text(json.dumps(discover(seeds, max_depth), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps (
    return path  # info: return path

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    import argparse  # info: import argparse
    p = argparse.ArgumentParser()  # info: set p
    p.add_argument("--output", required=True)  # info: p . add_argument ( "--output" , required =
    p.add_argument("--depth", type=int, default=1)  # info: p . add_argument ( "--depth" , type =
    p.add_argument("seed", nargs="+")  # info: p . add_argument ( "seed" , nargs =
    args = p.parse_args()  # info: set args
    print(write_inventory(args.output, args.seed, args.depth))  # info: call print
