"""Deterministic discovery of NWS/NOAA hazard product catalogs.

This is intentionally a crawler/parser, not an AI classifier. It follows
explicit seed URLs, extracts links and AWIPS-like product identifiers, and
writes a reviewable inventory so new hazard products can be added without
manually clicking through pages.
"""
from __future__ import annotations
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

AWIPS_RE = re.compile(r"\b[A-Z0-9]{3,8}(?:HFO|HI|PHFO)?\b")
HAZARD_WORDS = re.compile(
    r"\b(warning|watch|advisory|statement|outlook|emergency|hazard|"
    r"tsunami|flood|fire|wind|surf|storm|volcano|earthquake|marine|"
    r"tropical|avalanche|civil|non-precipitation|severe)\b", re.I
)

class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.text = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for k, v in attrs:
            if k.lower() == "href" and v:
                self.links.append(v)
    def handle_data(self, data):
        self.text.append(data)

def fetch_html(url: str, timeout: float = 20.0) -> str:
    req = Request(url, headers={"User-Agent": "RootRecord-Weather-Inventory/1.0"})
    with urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")

def discover(seeds: list[str], max_depth: int = 1) -> dict:
    seen = set()
    queue = [(u, 0) for u in seeds]
    products = {}
    links = []
    while queue:
        url, depth = queue.pop(0)
        if url in seen or depth > max_depth:
            continue
        seen.add(url)
        try:
            html = fetch_html(url)
        except Exception as exc:
            links.append({"url": url, "error": str(exc)})
            continue
        parser = _Links()
        parser.feed(html)
        text = "\n".join(parser.text)
        ids = sorted(set(m.group(0) for m in AWIPS_RE.finditer(text) if HAZARD_WORDS.search(text[max(0, m.start()-120):m.end()+120])))
        for product_id in ids:
            products.setdefault(product_id, {"sources": []})
            products[product_id]["sources"].append(url)
        for href in parser.links:
            target = urljoin(url, href)
            if urlparse(target).scheme not in {"http", "https"}:
                continue
            if urlparse(target).netloc != urlparse(url).netloc:
                continue
            links.append({"from": url, "url": target})
            if depth < max_depth and HAZARD_WORDS.search(target):
                queue.append((target, depth + 1))
    return {"seeds": seeds, "products": products, "links": links}

def write_inventory(output: str, seeds: list[str], max_depth: int = 1) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(discover(seeds, max_depth), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("seed", nargs="+")
    args = p.parse_args()
    print(write_inventory(args.output, args.seed, args.depth))
