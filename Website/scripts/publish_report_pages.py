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
"""Write the public /reports pages from measured report files.

Pages live in Website/Home/reports. The address is https://www.rootrecord.cloud/reports/<slug>.
Measured fields and sections only. Spoken transcripts and persona names stay off the page.
Source paths stay off the page. A file is left untouched when the bytes match.
"""
from __future__ import annotations  # info: from __future__ import annotations

import html  # info: import html
import json  # info: import json
import re  # info: import re
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

PACIFIC = Path(__file__).resolve().parents[2]  # info: set PACIFIC
HOME = PACIFIC / "Website" / "Home"  # info: set HOME
ROUTES = PACIFIC / "Communications" / "Discord" / "config" / "report-channels.json"  # info: set ROUTES
sys.path.insert(0, str(PACIFIC / "Communications" / "Discord"))  # info: sys . path . insert
from lib.public_report import TITLES  # noqa: E402

SITE = "https://www.rootrecord.cloud/reports"  # info: set SITE
VOICE = Path("/home/rootrecord/RootRecord-Ecosystem/test-reports/Voice")  # info: set VOICE
AREAS = (  # info: set AREAS
    ("Field", ("nws_weather", "official_weather", "hurricane_desk", "kilauea_report", "earthquake_report")),  # info: field
    ("Energy", ("energy_report", "solar_desk")),  # info: energy
    ("Operations", ("system_perf", "security_desk", "bandwidth_desk", "remaining_tasks", "boot_brief", "morning_report", "midday_report", "late_report")),  # info: operations
)  # info: )


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
# SECTION: function area_for
# What it does: Field, Energy, or Operations for a report key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def area_for(key: str) -> str:  # info: def area_for
    for name, keys in AREAS:  # info: for name , keys in AREAS
        if key in keys:  # info: if key in keys
            return name  # info: return name
    return "Operations"  # info: return Operations


# ====================================================
# SECTION: function report_markdown
# What it does: Read one current report. Empty when the file is missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def report_markdown(key: str) -> str:  # info: def report_markdown
    path = VOICE / f"{key}_current.md"  # info: set path
    if not path.is_file():  # info: if not path . is_file
        return ""  # info: return empty
    return path.read_text(encoding="utf-8", errors="replace")  # info: return markdown


# ====================================================
# SECTION: function as_of
# What it does: Clock from the report heading, shown as Hawaiian time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def as_of(md: str) -> str:  # info: def as_of
    found = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", md)  # info: set found
    if not found:  # info: if not found
        return ""  # info: return empty
    year, month, day, hour, minute = found.groups()  # info: unpack stamp
    names = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")  # info: set names
    return f"{int(day)} {names[int(month) - 1]} {year} · {hour}:{minute} HST"  # info: return stamp


# ====================================================
# SECTION: function clean_line
# What it does: Drop markup, file names, and provenance. Empty when the line is not public.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clean_line(raw: str) -> str:  # info: def clean_line
    item = raw[2:].strip() if raw.startswith("- ") else raw  # info: set item
    item = re.sub(r"`[^`]*`", "", item)  # info: drop code spans
    item = item.replace("**", "")  # info: drop bold marks
    item = re.sub(r"\(\s*\)", "", item)  # info: drop empty parens
    item = " ".join(item.split()).strip(" -")  # info: collapse space
    low = item.lower()  # info: set low
    if not item or low.startswith(("alerts source", "forecast source", "collected", "source:", "llm summary")):  # info: if provenance
        return ""  # info: return empty
    if low.startswith("off (") or "rr_voice" in low:  # info: if gate note
        return ""  # info: return empty
    if any(token in low for token in ("database ", ".json", ".py", ".jpg", "/proc", "host_desks", "spoken")):  # info: if internal
        return ""  # info: return empty
    return item  # info: return item


# ====================================================
# SECTION: function sections
# What it does: Measured sections as a heading plus lines. Spoken text is omitted.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sections(md: str) -> list[tuple[str, list[str]]]:  # info: def sections
    body = md.split("\n## Spoken", 1)[0]  # info: set body
    heading = "Readings"  # info: set heading
    bucket: list[str] = []  # info: set bucket
    found: list[tuple[str, list[str]]] = []  # info: set found

    def flush() -> None:  # info: def flush
        if bucket:  # info: if bucket
            found.append((heading, list(bucket)))  # info: append section
        bucket.clear()  # info: clear bucket

    for line in body.splitlines():  # info: for line in body
        raw = line.strip()  # info: set raw
        if raw.startswith("## "):  # info: if heading
            flush()  # info: call flush
            heading = raw[3:].strip()  # info: set heading
            if heading.lower() in {"spoken", "llm summary"}:  # info: if spoken or llm
                heading = ""  # info: clear heading
            continue  # info: continue
        if not heading or not raw or raw.startswith("#") or raw.startswith("_") or raw.startswith("|---") or raw.startswith("| Metric") or raw.startswith("| Device"):  # info: if skip
            continue  # info: continue
        if raw.startswith("|"):  # info: if table row
            cells = [cell.strip() for cell in raw.strip("|").split("|")]  # info: set cells
            item = clean_line(f"{cells[0]}: {cells[1]}") if len(cells) >= 2 else ""  # info: set item
        else:  # info: else
            item = clean_line(raw)  # info: set item
        if item and item not in bucket:  # info: if new
            bucket.append(item)  # info: append
    flush()  # info: call flush
    return [(name, rows) for name, rows in found if name and rows]  # info: return sections


# ====================================================
# SECTION: function pair
# What it does: Split a short label from its value. None when the line is a sentence.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pair(line: str) -> tuple[str, str] | None:  # info: def pair
    if ": " not in line:  # info: if no colon
        return None  # info: return None
    label, value = line.split(": ", 1)  # info: split label
    if not label or len(label) > 42 or len(value) > 180:  # info: if not a field
        return None  # info: return None
    return label, value  # info: return pair


# ====================================================
# SECTION: function render_section
# What it does: One report section as a field table or a reading list.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_section(heading: str, rows: list[str]) -> str:  # info: def render_section
    pairs = [pair(row) for row in rows]  # info: set pairs
    title = html.escape(heading)  # info: set title
    if pairs and all(item is not None for item in pairs):  # info: if every row is a field
        body = "\n".join(f"      <tr><th scope=\"row\">{html.escape(label)}</th><td>{html.escape(value)}</td></tr>" for label, value in pairs)  # info: set body
        inner = f'    <table class="report-table">\n{body}\n    </table>'  # info: set inner
    else:  # info: else
        body = "\n".join(f"      <li>{html.escape(row)}</li>" for row in rows)  # info: set body
        inner = f'    <ul class="facts">\n{body}\n    </ul>'  # info: set inner
    return f'  <section class="sec">\n    <h2>{title}</h2>\n{inner}\n  </section>'  # info: return section


# ====================================================
# SECTION: function highlights
# What it does: Up to three field pairs for an index card.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def highlights(parts: list[tuple[str, list[str]]]) -> list[tuple[str, str]]:  # info: def highlights
    picked = []  # info: set picked
    for _heading, rows in parts:  # info: for heading , rows
        for row in rows:  # info: for row in rows
            found = pair(row)  # info: set found
            if found:  # info: if found
                picked.append(found)  # info: append
            if len(picked) >= 3:  # info: if three
                return picked  # info: return picked
    return picked  # info: return picked


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
# What it does: Shared page head, nav, and footer. No starfield. Reports is the current nav item.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chrome(title: str, description: str, canonical: str, main: str, wide: bool = False) -> str:  # info: def chrome
    desc = html.escape(description, quote=True)  # info: set desc
    page_title = html.escape(title, quote=True)  # info: set page_title
    width = "page page-wide" if wide else "page"  # info: set width
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
<body class="desk">
<a class="skip" href="#content">Skip to content</a>
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
<main class="{width}" id="content">
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
<script src="/assets/shell.js"></script>
</body>
</html>
"""  # info: return page


# ====================================================
# SECTION: function index_page
# What it does: Build the /reports index as cards with the latest public text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def index_page(rows: list[dict]) -> str:  # info: def index_page
    groups = {"Ava": [], "Bruce": [], "Carly": []}  # info: set groups
    for row in rows:  # info: for row in rows
        key = str(row["key"])  # info: set key
        who = persona_name(key)  # info: set who
        slug = html.escape(str(row["name"]), quote=True)  # info: set slug
        title = html.escape(TITLES.get(key, key.replace("_", " ")))  # info: set title
        role = html.escape(str(row.get("function") or ""))  # info: set role
        md = report_markdown(key)  # info: set md
        preview = excerpt(public_body(key) or "")  # info: set preview
        if not preview:  # info: if not preview
            facts = measured(md)  # info: set facts
            preview = excerpt(facts[0]) if facts else "No public report is on file."  # info: set preview
        when = as_of(md)  # info: set when
        stamp = f'<p class="fine">{html.escape(when)}</p>' if when else ""  # info: set stamp
        groups.setdefault(who, []).append(  # info: append card
            f'    <a class="card report-card" href="/reports/{slug}">\n'
            f"      <h3>{title}</h3>\n"
            f'      <p class="tax-items">{role}</p>\n'
            f'      <p class="excerpt">{html.escape(preview)}</p>\n'
            f"      {stamp}\n"
            f"    </a>"
        )  # info: card
    blocks = []  # info: set blocks
    for who in ("Ava", "Bruce", "Carly"):  # info: for who in personas
        cards = "\n".join(groups.get(who) or [])  # info: set cards
        if cards:  # info: if cards
            blocks.append(f'  <section class="sec" aria-label="{who}">\n    <h2>{who}</h2>\n    <div class="report-board">\n{cards}\n    </div>\n  </section>')  # info: append section
    main = """  <p class="eyebrow">Public reports</p>
  <h1>Reports</h1>
  <p class="prose">Ava, Bruce, and Carly. Each card is the latest public report. Open it for the spoken text and the measured lines.</p>
""" + "\n".join(blocks)  # info: set main
    return chrome("Reports — Root Record", "Public reports from Ava, Bruce, and Carly.", f"{SITE}", main, wide=True)  # info: return chrome


# ====================================================
# SECTION: function report_page
# What it does: Build one /reports/<slug> page with the spoken text and measured lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def report_page(row: dict) -> str:  # info: def report_page
    key = str(row["key"])  # info: set key
    slug = str(row["name"])  # info: set slug
    title = TITLES.get(key, key.replace("_", " "))  # info: set title
    who = persona_name(key)  # info: set who
    md = report_markdown(key)  # info: set md
    body = public_body(key)  # info: set body
    text = html.escape(body) if body else "No public report is on file."  # info: set text
    blurb = str(row.get("function") or title)  # info: set blurb
    when = as_of(md)  # info: set when
    stamp = f'  <p class="meta">{html.escape(when)}</p>\n' if when else ""  # info: set stamp
    facts = "\n".join(f"    <li>{html.escape(item)}</li>" for item in measured(md))  # info: set facts
    measured_block = f'  <section class="sec" aria-label="Measured">\n    <h2>Measured</h2>\n    <ul class="facts">\n{facts}\n    </ul>\n  </section>\n' if facts else ""  # info: set measured_block
    main = f"""  <p class="eyebrow">{html.escape(who)}</p>
  <h1>{html.escape(title)}</h1>
{stamp}  <p class="prose">{html.escape(blurb)}</p>
  <section class="sec" aria-label="Spoken">
    <h2>Spoken</h2>
    <p class="prose">{text}</p>
  </section>
{measured_block}  <p class="fine"><a href="/reports">All reports</a></p>"""  # info: set main
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
