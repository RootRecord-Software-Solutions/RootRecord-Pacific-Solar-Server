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
VOICE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Audio/Voice/Reports")  # info: set VOICE
CURRENT_MD = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Audio/Voice/Reports/current_report_current.md")  # info: set CURRENT_MD
AREAS = (  # info: set AREAS
    ("Current", ("current_report",)),  # info: current
    ("Field", ("nws_weather", "official_weather", "hurricane_desk", "kilauea_report", "earthquake_report")),  # info: field
    ("Energy", ("solar_desk",)),  # info: energy (combined solar desk)
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
    path = CURRENT_MD if key == "current_report" else (VOICE / f"{key}_current.md")  # info: set path
    sidecar = path.with_name(path.stem + ".report.json")  # info: set sidecar
    if sidecar.is_file():  # info: if sidecar . is_file
        try:  # info: try
            report = json.loads(sidecar.read_text(encoding="utf-8"))  # info: set report
            parts = [str(section.get("text") or "") for section in report.get("sections") or [] if isinstance(section, dict)]  # info: set parts
            text = "\n\n".join(part for part in parts if part).strip()  # info: set text
            if text:  # info: if text
                return text + "\n"  # info: return text
        except (OSError, json.JSONDecodeError):  # info: except
            pass  # info: pass
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
def sections(md: str) -> list[dict]:  # info: def sections
    body = md.split("\n## Spoken", 1)[0]  # info: set body
    heading = "Readings"  # info: set heading
    lines: list[str] = []  # info: set lines
    columns: list[str] = []  # info: set columns
    table: list[list[str]] = []  # info: set table
    found: list[dict] = []  # info: set found

    def flush() -> None:  # info: def flush
        had_table = bool(table and columns)  # info: set had_table
        if had_table:  # info: if table
            found.append({"heading": heading, "kind": "table", "columns": list(columns), "rows": [list(row) for row in table]})  # info: append table
        if lines:  # info: if lines
            label = "Notes" if had_table else heading  # info: set label
            found.append({"heading": label, "kind": "list", "rows": list(lines)})  # info: append list
        lines.clear()  # info: clear lines
        columns.clear()  # info: clear columns
        table.clear()  # info: clear table

    for line in body.splitlines():  # info: for line in body
        raw = line.strip()  # info: set raw
        if raw.startswith("## "):  # info: if heading
            flush()  # info: call flush
            heading = raw[3:].strip()  # info: set heading
            if heading.lower() in {"spoken", "llm summary"}:  # info: if spoken or llm
                heading = ""  # info: clear heading
            continue  # info: continue
        if not heading or not raw or raw.startswith("#") or raw.startswith("_") or set(raw.replace("|", "").replace("-", "").replace(":", "").replace(" ", "")) == set():  # info: if skip
            continue  # info: continue
        if raw.startswith("|"):  # info: if table row
            cells = [clean_line(cell.strip()) for cell in raw.strip("|").split("|")]  # info: set cells
            if not cells:  # info: if empty cells
                continue  # info: continue
            if not columns:  # info: if header
                columns.extend(cells)  # info: store header
            elif len(cells) == len(columns):  # info: if data row
                table.append(cells)  # info: append row
            continue  # info: continue
        item = clean_line(raw)  # info: set item
        if item and len(item) > 180 and not raw.startswith("- "):  # info: if narrative
            continue  # info: continue
        if item and item not in lines:  # info: if new
            lines.append(item)  # info: append
    flush()  # info: call flush
    return [part for part in found if part.get("heading")]  # info: return sections


# ====================================================
# SECTION: function show_heading
# What it does: Public section title. Drops internal notes and title-case headings.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def show_heading(raw: str) -> str:  # info: def show_heading
    text = re.sub(r"\s*\([^)]*(?:poller|database|g\d)[^)]*\)", "", raw, flags=re.I)  # info: drop internal notes
    text = " ".join(text.split())  # info: collapse space
    letters = [ch for ch in text if ch.isalpha()]  # info: set letters
    uppers = sum(ch.isupper() for ch in letters)  # info: set uppers
    if letters and uppers > 1 and uppers >= max(2, len(letters) // 6):  # info: if title case
        text = text[:1].upper() + text[1:].lower()  # info: sentence case
    text = re.sub(r"\bhawaii\b", "Hawaiʻi", text, flags=re.I)  # info: restore Hawaiʻi
    text = re.sub(r"\bkīlauea\b", "Kīlauea", text, flags=re.I)  # info: restore Kīlauea
    for token, shown in (("nws", "NWS"), ("usgs", "USGS"), ("cpu", "CPU"), ("ram", "RAM"), ("soc", "SOC"), ("hst", "HST")):  # info: for token , shown
        text = re.sub(rf"\b{token}\b", shown, text, flags=re.I)  # info: restore token
    return text  # info: return heading


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
def render_section(part: dict) -> str:  # info: def render_section
    title = html.escape(show_heading(str(part.get("heading") or "Readings")))  # info: set title
    if part.get("kind") == "table":  # info: if table
        columns = [show_heading(name) if name == name.title() else name for name in (part.get("columns") or [])]  # info: set columns
        head = "".join(f"<th scope=\"col\">{html.escape(name)}</th>" for name in columns)  # info: set head
        body_rows = []  # info: set body_rows
        for row in part.get("rows") or []:  # info: for row in rows
            cells = "".join(f"<td>{html.escape(cell)}</td>" for cell in row)  # info: set cells
            body_rows.append(f"      <tr>{cells}</tr>")  # info: append row
        inner = f'    <table class="report-table">\n      <thead><tr>{head}</tr></thead>\n      <tbody>\n' + "\n".join(body_rows) + "\n      </tbody>\n    </table>"  # info: set inner
    else:  # info: else
        rows = part.get("rows") or []  # info: set rows
        pairs = [pair(row) for row in rows]  # info: set pairs
        if pairs and all(item is not None for item in pairs):  # info: if every row is a field
            body = "\n".join(f"      <tr><th scope=\"row\">{html.escape(label)}</th><td>{html.escape(value)}</td></tr>" for label, value in pairs)  # info: set body
            inner = f'    <table class="report-table">\n{body}\n    </table>'  # info: set inner
        else:  # info: else
            body = "\n".join(f"      <li>{html.escape(row)}</li>" for row in rows)  # info: set body
            inner = f'    <ul class="facts">\n{body}\n    </ul>'  # info: set inner
    return f'  <section class="sec">\n    <h2>{title}</h2>\n{inner}\n  </section>'  # info: return section


# ====================================================
# SECTION: function highlights
# What it does: Up to three short readings for an index card. Long lines are shortened. Source notes stay off the card.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def highlights(parts: list[dict]) -> list[tuple[str, str]]:  # info: def highlights
    short: list[tuple[str, str]] = []  # info: set short
    long: list[tuple[str, str]] = []  # info: set long

    def take(label: str, value: str) -> None:  # info: def take
        text = re.sub(r"https?://\S+", "", value)  # info: drop urls
        stamp = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?-10:00", text)  # info: set stamp
        if stamp:  # info: if hawaiian stamp
            year, month, day, hour, minute = stamp.groups()  # info: unpack stamp
            names = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")  # info: set names
            shown = f"{int(day)} {names[int(month) - 1]} {year} · {hour}:{minute} HST"  # info: set shown
            text = (text[:stamp.start()] + shown + text[stamp.end():]).strip()  # info: replace stamp
        if label.lower() == "age h":  # info: if age label
            label = "Age"  # info: set label
            text = text if text.endswith(" h") else f"{text} h"  # info: set text
        if label.lower() == "issued / fetched":  # info: if issued label
            label = "Issued"  # info: set label
        text = " ".join(text.split()).strip(" .,;")  # info: collapse space
        low = text.lower()  # info: set low
        if not label or not text:  # info: if empty
            return  # info: return
        if any(token in low for token in ("zone forecast", "state forecast", "forecast source", "alerts source")):  # info: if source note
            return  # info: return
        if len(text) <= 80:  # info: if short
            short.append((label, text))  # info: append short
            return  # info: return
        if len(text) > 96:  # info: if long
            text = text[:96].rsplit(" ", 1)[0].rstrip(".,;:") + "…"  # info: shorten text
        long.append((label, text))  # info: append long

    for part in parts:  # info: for part in parts
        if part.get("kind") == "table":  # info: if table
            columns = part.get("columns") or []  # info: set columns
            rows = part.get("rows") or []  # info: set rows
            if rows and columns:  # info: if row
                row = rows[0]  # info: set row
                for name, cell in list(zip(columns, row))[:3]:  # info: for name , cell
                    if name and cell:  # info: if field
                        take(name, cell)  # info: call take
            if short or long:  # info: if table fields
                return (short + long)[:3]  # info: return table fields
            continue  # info: continue
        for row in part.get("rows") or []:  # info: for row in rows
            found = pair(row)  # info: set found
            if not found and " — " in row:  # info: if em dash
                label, value = row.split(" — ", 1)  # info: split label
                if label and len(label) <= 42 and value and len(value) <= 180:  # info: if field
                    found = (label.strip(), value.strip())  # info: set found
            if found:  # info: if found
                take(found[0], found[1])  # info: call take
    chosen = (short + long)[:3]  # info: set chosen
    if chosen:  # info: if chosen
        return chosen  # info: return chosen
    for part in parts:  # info: for part in parts
        rows = part.get("rows") or []  # info: set rows
        if part.get("kind") == "list" and rows:  # info: if list
            take(show_heading(str(part.get("heading") or "Reading")), rows[0])  # info: call take
            if short or long:  # info: if lead
                return (short + long)[:1]  # info: return lead
    return []  # info: return empty


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
# What it does: Shared page head, nav, and footer. No starfield. Public primary nav with Reports as current (non-link); footer is Account/Terms/Privacy/Data deletion.
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
    <a href="/products">Products</a>
    <a href="/services">Services</a>
    <a href="/solutions">Solutions</a>
    <a href="/about">About</a>
    <a href="/security">Security</a>
    <a href="/status">Status</a>
    <span aria-current="page">Reports</span>
    <a href="/radio">Radio</a>
    <a href="/live">Live</a>
  </nav>
</header>
<main class="{width}" id="content">
{main}
</main>
<footer class="site-foot">
  <a href="/login">Account</a>
  <a href="/terms">Terms</a>
  <a href="/privacy">Privacy</a>
  <a href="/data-deletion">Data deletion</a>
</footer>
<script src="/assets/shell.js"></script>
</body>
</html>
"""  # info: return page


# ====================================================
# SECTION: function index_page
# What it does: Build the /reports index as field, energy, and operations cards.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def index_page(rows: list[dict]) -> str:  # info: def index_page
    by_key = {str(row["key"]): row for row in rows}  # info: set by_key
    blocks = []  # info: set blocks
    for area, keys in AREAS:  # info: for area , keys in AREAS
        cards = []  # info: set cards
        for key in keys:  # info: for key in keys
            row = by_key.get(key)  # info: set row
            if not row:  # info: if not row
                continue  # info: continue
            slug = html.escape(str(row["name"]), quote=True)  # info: set slug
            title = html.escape(TITLES.get(key, key.replace("_", " ")))  # info: set title
            md = report_markdown(key)  # info: set md
            parts = sections(md)  # info: set parts
            when = as_of(md)  # info: set when
            fields = highlights(parts)  # info: set fields
            if fields:  # info: if fields
                rows_html = []  # info: set rows_html
                for label, value in fields:  # info: for label , value in fields
                    wide = ' class="wide"' if len(value) > 40 else ""  # info: set wide
                    rows_html.append(f"        <div{wide}><dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd></div>")  # info: append row
                lines = "\n".join(rows_html)  # info: set lines
                body = f'      <dl class="report-facts">\n{lines}\n      </dl>'  # info: set body
            else:  # info: else
                body = '      <p class="excerpt">No reading is on file for this period.</p>'  # info: set body
            stamp = f'\n      <p class="fine">{html.escape(when)}</p>' if when else ""  # info: set stamp
            cards.append(  # info: append card
                f'    <a class="card report-card" href="/reports/{slug}">\n'
                f"      <h3>{title}</h3>\n"
                f"{body}{stamp}\n"
                f"    </a>"
            )  # info: card
        if cards:  # info: if cards
            board = "\n".join(cards)  # info: set board
            blocks.append(f'  <section class="sec" aria-label="{area}">\n    <h2>{area}</h2>\n    <div class="report-board">\n{board}\n    </div>\n  </section>')  # info: append section
    main = """  <p class="eyebrow">Field record</p>
  <h1>Reports</h1>
  <p class="prose">Latest published readings for weather, geology, energy, and operations. Each report is the measured record for that period.</p>
""" + "\n".join(blocks)  # info: set main
    return chrome("Reports — Root Record", "Latest field and operations readings from Root Record.", f"{SITE}", main, wide=True)  # info: return chrome


# ====================================================
# SECTION: function report_page
# What it does: Build one /reports/<slug> page as a measured report.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def report_page(row: dict) -> str:  # info: def report_page
    key = str(row["key"])  # info: set key
    slug = str(row["name"])  # info: set slug
    title = TITLES.get(key, key.replace("_", " "))  # info: set title
    md = report_markdown(key)  # info: set md
    parts = sections(md)  # info: set parts
    when = as_of(md)  # info: set when
    stamp = f'  <p class="meta">{html.escape(when)}</p>\n' if when else ""  # info: set stamp
    body = "\n".join(render_section(part) for part in parts)  # info: set body
    if not body:  # info: if not body
        body = '  <p class="empty-note">No reading is on file for this period.</p>'  # info: set body
    area = area_for(key)  # info: set area
    main = f"""  <p class="eyebrow">{html.escape(area)}</p>
  <h1>{html.escape(title)}</h1>
{stamp}{body}
  <p class="fine"><a href="/reports">All reports</a></p>"""  # info: set main
    return chrome(f"{title} — Root Record", f"Latest {title} reading.", f"{SITE}/{slug}", main)  # info: return chrome


# ====================================================
# SECTION: function publish
# What it does: Write the index and one page per report slug. Does not post to Discord.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def publish() -> list[str]:  # info: def publish
    rows = load_routes() + [{"key": "current_report", "name": "current"}]  # info: set rows
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
