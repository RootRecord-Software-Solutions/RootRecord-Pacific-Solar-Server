# ==============================================================================
# FILE: Website/scripts/publish_report_pages.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Write the public /reports pages from the same text Discord posts.

Pages live in Website/Home/reports. The address is https://www.rootrecord.cloud/reports/<slug>.
Spoken text only. Source paths stay off the page. A file is left untouched when the bytes match.
"""
from __future__ import annotations  # info: from __future__ import annotations

import html  # info: import html
import json  # info: import json
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

PACIFIC = Path(__file__).resolve().parents[2]  # info: set PACIFIC
HOME = PACIFIC / "Website" / "Home"  # info: set HOME
ROUTES = PACIFIC / "Communications" / "Discord" / "config" / "report-channels.json"  # info: set ROUTES
sys.path.insert(0, str(PACIFIC / "Communications" / "Discord"))  # info: sys . path . insert
from lib.public_report import TITLES, persona_name, spoken_text  # noqa: E402

SITE = "https://www.rootrecord.cloud/reports"  # info: set SITE
VOICE = Path("/home/rootrecord/RootRecord-Ecosystem/test-reports/Voice")  # info: set VOICE


# ====================================================
# SECTION: function load_routes
# What it does: Read the Discord report list. Does not post.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_routes() -> list[dict]:  # info: def load_routes
    data = json.loads(ROUTES.read_text(encoding="utf-8"))  # info: set data
    rows = data.get("reports") if isinstance(data, dict) else None  # info: set rows
    return [row for row in rows or [] if isinstance(row, dict) and row.get("name") and row.get("key")]  # info: return rows


# ====================================================
# SECTION: function public_body
# What it does: Spoken public text for one report key. Empty when the file is missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def public_body(key: str) -> str:  # info: def public_body
    path = VOICE / f"{key}_current.md"  # info: set path
    if not path.is_file():  # info: if not path . is_file
        return ""  # info: return empty
    read_path = path.with_name(path.name.replace(".md", ".read.txt"))  # info: set read_path
    read = read_path.read_text(encoding="utf-8", errors="replace") if read_path.is_file() else ""  # info: set read
    return spoken_text(path.read_text(encoding="utf-8", errors="replace"), read)  # info: return spoken_text


# ====================================================
# SECTION: function write_if_changed
# What it does: Write HTML only when the new text differs. Does not post.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_if_changed(path: Path, text: str) -> bool:  # info: def write_if_changed
    if path.is_file() and path.read_text(encoding="utf-8") == text:  # info: if path . is_file and text matches
        return False  # info: return False
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    path.write_text(text, encoding="utf-8")  # info: path . write_text
    return True  # info: return True


# ====================================================
# SECTION: function chrome
# What it does: Shared page head, nav, and footer. Reports is the current nav item.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chrome(title: str, description: str, canonical: str, main: str) -> str:  # info: def chrome
    desc = html.escape(description, quote=True)  # info: set desc
    page_title = html.escape(title, quote=True)  # info: set page_title
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{page_title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="Root Record">
<meta name="theme-color" content="#000011">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<canvas id="starfield" aria-hidden="true"></canvas>
<header class="top">
  <a class="brand" href="/">Root Record</a>
  <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
  <nav id="site-nav" aria-label="Primary">
    <a href="/">Home</a>
    <a href="/ecosystem">Ecosystem</a>
    <a href="/operations">Systems</a>
    <a href="/intelligence">Intelligence</a>
    <a href="/knowledge">Knowledge</a>
    <a href="/security">Security</a>
    <a href="/reports" aria-current="page">Reports</a>
    <a href="/status">Status</a>
  </nav>
</header>
<main class="page" id="content">
{main}
</main>
<footer class="site-foot">
  <a href="/ecosystem">Ecosystem</a>
  <a href="/operations">Systems</a>
  <a href="/intelligence">Intelligence</a>
  <a href="/reports">Reports</a>
  <a href="/status">Status</a>
  <a href="/about">About</a>
</footer>
<script src="/assets/starfield.js"></script>
<script src="/assets/shell.js"></script>
</body>
</html>
"""  # info: return page


# ====================================================
# SECTION: function index_page
# What it does: Build the /reports index. One link per Discord slug.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def index_page(rows: list[dict]) -> str:  # info: def index_page
    groups = {"Ava": [], "Bruce": [], "Carly": []}  # info: set groups
    for row in rows:  # info: for row in rows
        key = str(row["key"])  # info: set key
        who = persona_name(key)  # info: set who
        slug = str(row["name"])  # info: set slug
        title = TITLES.get(key, key.replace("_", " "))  # info: set title
        groups.setdefault(who, []).append(f'    <li><a href="/reports/{html.escape(slug, quote=True)}">{html.escape(title)}</a></li>')  # info: append link
    blocks = []  # info: set blocks
    for who in ("Ava", "Bruce", "Carly"):  # info: for who in personas
        items = "\n".join(groups.get(who) or [])  # info: set items
        if items:  # info: if items
            blocks.append(f"  <h2>{who}</h2>\n  <ul>\n{items}\n  </ul>")  # info: append block
    main = """  <p class="eyebrow">Public reports</p>
  <h1>Reports</h1>
  <p class="prose">Ava, Bruce, and Carly. Each page is the latest public report. The same address is the link posted with that report.</p>
  <section class="tree" aria-label="Reports">
""" + "\n".join(blocks) + "\n  </section>\n  <p class=\"fine\"><a href=\"/operations#reporting\">Systems</a></p>"  # info: set main
    return chrome("Reports — Root Record", "Public reports from Ava, Bruce, and Carly.", f"{SITE}", main)  # info: return chrome


# ====================================================
# SECTION: function report_page
# What it does: Build one /reports/<slug> page. Spoken text only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def report_page(row: dict) -> str:  # info: def report_page
    key = str(row["key"])  # info: set key
    slug = str(row["name"])  # info: set slug
    title = TITLES.get(key, key.replace("_", " "))  # info: set title
    who = persona_name(key)  # info: set who
    body = public_body(key)  # info: set body
    text = html.escape(body) if body else "No public report is on file."  # info: set text
    blurb = str(row.get("function") or title)  # info: set blurb
    main = f"""  <p class="eyebrow">{html.escape(who)}</p>
  <h1>{html.escape(title)}</h1>
  <p class="prose">{text}</p>
  <p class="fine"><a href="/reports">All reports</a></p>"""  # info: set main
    return chrome(f"{title} — Root Record", blurb, f"{SITE}/{slug}", main)  # info: return chrome


# ====================================================
# SECTION: function publish
# What it does: Write the index and one page per report slug. Does not post to Discord.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def publish() -> list[str]:  # info: def publish
    rows = load_routes()  # info: set rows
    written = []  # info: set written
    if write_if_changed(HOME / "reports" / "index.html", index_page(rows)):  # info: if write_if_changed index
        written.append("/reports")  # info: append index
    for row in rows:  # info: for row in rows
        slug = str(row["name"])  # info: set slug
        if write_if_changed(HOME / "reports" / slug / "index.html", report_page(row)):  # info: if write_if_changed page
            written.append(f"/reports/{slug}")  # info: append slug
    return written  # info: return written


# ====================================================
# SECTION: function main
# What it does: Publish the pages and print the paths that changed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    written = publish()  # info: set written
    if not written:  # info: if not written
        print("same")  # info: print same
        return 0  # info: return 0
    print("\n".join(written))  # info: print written
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__
    raise SystemExit(main())  # info: raise SystemExit
