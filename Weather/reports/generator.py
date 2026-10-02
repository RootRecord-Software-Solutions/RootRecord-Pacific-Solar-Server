# ==============================================================================
# FILE: Weather/reports/generator.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Generate human-readable Markdown reports from collected HFO data.

Raw fetched data remains authoritative. This module only writes derived files
under Database/WEATHER/Hawai'i/reports.
"""
from __future__ import annotations  # info: from __future__ import annotations

import html  # info: import html
import json  # info: import json
import re  # info: import re
from html.parser import HTMLParser  # info: from html . parser import HTMLParser
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import quote  # info: from urllib . parse import quote
from typing import Any  # info: from typing import Any

import yaml  # info: import yaml

from core import hst_time  # info: from core import hst_time
from core.manifest import Manifest  # info: from core . manifest import Manifest

from reports.banner import OUTPUT_RELATIVE, generate_readme_banner  # info: from reports . banner import OUTPUT_RELATIVE , generate_readme_banner

REPORTS_DIRNAME = "reports"  # info: set REPORTS_DIRNAME
LEVEL0_DIRNAME = "0 Level Processing"  # info: set LEVEL0_DIRNAME
ARCHIVE_DIRNAME = "archived"  # info: set ARCHIVE_DIRNAME
README_TEMPLATE = Path(__file__).resolve().parent / "README_TEMPLATE.md"  # info: set README_TEMPLATE
DATABASE_README_TEMPLATE = Path(__file__).resolve().parent / "WEATHER_DATABASE_README_TEMPLATE.md"  # info: set DATABASE_README_TEMPLATE
AGGREGATE_FILENAME = "Hawaii_State_Weather_Report_current.md"  # info: set AGGREGATE_FILENAME
_EXCLUDED_PREFIXES = ("alerts_", "wwamap_", "nhc_current_storms", "ndfd_", "obhistory_")  # info: set _EXCLUDED_PREFIXES
# ====================================================
# SECTION: _EXCLUDED_IDS
# What it does: Set _EXCLUDED_IDS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_EXCLUDED_IDS = {  # info: set _EXCLUDED_IDS
    "rain_summary_graphical",  # info: "rain_summary_graphical" ,
    "nhc_source_index",  # info: "nhc_source_index" ,
    "nws_cwa_boundaries_catalog",  # info: "nws_cwa_boundaries_catalog" ,
    "nws_fire_zones_catalog",  # info: "nws_fire_zones_catalog" ,
    "nws_marine_zones_catalog",  # info: "nws_marine_zones_catalog" ,
    "nws_public_counties_catalog",  # info: "nws_public_counties_catalog" ,
    "nws_public_zones_catalog",  # info: "nws_public_zones_catalog" ,
    "nws_zone_county_catalog",  # info: "nws_zone_county_catalog" ,
}  # info: }
# ====================================================
# SECTION: _README_PLACEHOLDERS
# What it does: Set _README_PLACEHOLDERS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_README_PLACEHOLDERS = (  # info: set _README_PLACEHOLDERS
    "{{CURRENT_CONDITIONS}}",  # info: "{{CURRENT_CONDITIONS}}" ,
    "{{README_BANNER_URL}}",  # info: "{{README_BANNER_URL}}" ,
    "{{REPORT_UPDATED}}",  # info: "{{REPORT_UPDATED}}" ,
    "{{REPORT_SECTION_COUNT}}",  # info: "{{REPORT_SECTION_COUNT}}" ,
    "{{REPORT_SECTIONS}}",  # info: "{{REPORT_SECTIONS}}" ,
)  # info: )

# Site chrome phrases that must never appear inside a product body.
# ====================================================
# SECTION: _CHROME_MARKERS
# What it does: Set _CHROME_MARKERS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_CHROME_MARKERS = (  # info: set _CHROME_MARKERS
    "Privacy Policy",  # info: "Privacy Policy" ,
    "Freedom of Information Act",  # info: "Freedom of Information Act" ,
    "USA.gov",  # info: "USA.gov" ,
    "About Us",  # info: "About Us" ,
    "Career Opportunities",  # info: "Career Opportunities" ,
    "National Weather Service Home",  # info: "National Weather Service Home" ,
)  # info: )


# ====================================================
# SECTION: function _load_resource_names
# What it does:  load resource names.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_resource_names() -> dict[str, str]:  # info: def _load_resource_names
    path = Path(__file__).resolve().parent.parent / "config" / "resources.yaml"  # info: set path
    with path.open(encoding="utf-8") as f:  # info: with path . open ( encoding = "utf-8"
        config = yaml.safe_load(f) or {}  # info: set config
    names: dict[str, str] = {}  # info: set names

    def walk(node: Any) -> None:  # info: def walk
        if isinstance(node, dict):  # info: if isinstance ( node , dict ) :
            if "id" in node and "name" in node:  # info: if "id" in node and "name" in node
                names[str(node["id"])] = str(node["name"])  # info: names [ str ( node [ "id" ]
            for value in node.values():  # info: for value in node . values ( )
                walk(value)  # info: call walk
        elif isinstance(node, list):  # info: elif isinstance ( node , list ) :
            for value in node:  # info: for value in node :
                walk(value)  # info: call walk

    walk(config)  # info: call walk
    return names  # info: return names


# ====================================================
# SECTION: function _display_name
# What it does:  display name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _display_name(resource_id: str, names: dict[str, str]) -> str:  # info: def _display_name
    if resource_id in names:  # info: if resource_id in names :
        return names[resource_id]  # info: return names [ resource_id ]
    for base_id, name in names.items():  # info: for base_id , name in names . items
        if resource_id.startswith(base_id + "_"):  # info: if resource_id . startswith ( base_id + "_"
            return "{} — {}".format(name, resource_id[len(base_id) + 1:])  # info: return "{} — {}" . format ( name , resource_id
    return resource_id.replace("_", " ").title()  # info: return resource_id . replace ( "_" , " "


# ====================================================
# SECTION: function _is_reportable
# What it does:  is reportable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _is_reportable(resource_id: str, state_url: str, path: Path) -> bool:  # info: def _is_reportable
    if resource_id in _EXCLUDED_IDS:  # info: if resource_id in _EXCLUDED_IDS :
        return False  # info: return False
    if any(resource_id.startswith(prefix) for prefix in _EXCLUDED_PREFIXES):  # info: if any ( resource_id . startswith ( prefix
        return False  # info: return False
    if path.suffix.lower() not in {".txt", ".html", ".json"}:  # info: if path . suffix . lower ( )
        return False  # info: return False
    if path.suffix.lower() == ".json":  # info: if path . suffix . lower ( )
        return "api.weather.gov/products/" in state_url  # info: return "api.weather.gov/products/" in state_url
    return True  # info: return True


# ====================================================
# SECTION: class _VisibleTextParser
# What it does: Extract visible HTML text while preserving useful line structure.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class _VisibleTextParser(HTMLParser):  # info: class _VisibleTextParser
    """Extract visible HTML text while preserving useful line structure."""  # info: """Extract visible HTML text while preserving useful line structure."""

    _BLOCK_TAGS = {  # info: set _BLOCK_TAGS
        "address", "article", "aside", "blockquote", "br", "dd", "div", "dl",  # info: "address" , "article" , "aside" , "blockquote" ,
        "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2",  # info: "dt" , "fieldset" , "figcaption" , "figure" ,
        "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol",  # info: "h3" , "h4" , "h5" , "h6" ,
        "p", "pre", "section", "table", "td", "th", "tr", "ul",  # info: "p" , "pre" , "section" , "table" ,
    }  # info: }

    def __init__(self) -> None:  # info: def __init__
        super().__init__(convert_charrefs=True)  # info: call super
        self.parts: list[str] = []  # info: self . parts : list [ str ]
        self._skip_depth = 0  # info: self . _skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # info: def handle_starttag
        tag = tag.lower()  # info: set tag
        if tag in {"script", "style", "noscript", "template"}:  # info: if tag in { "script" , "style" ,
            self._skip_depth += 1  # info: self . _skip_depth += 1
            return  # info: return
        if not self._skip_depth and tag in self._BLOCK_TAGS:  # info: if not self . _skip_depth and tag in
            self.parts.append("\n")  # info: self . parts . append ( "\n" )

    def handle_endtag(self, tag: str) -> None:  # info: def handle_endtag
        tag = tag.lower()  # info: set tag
        if tag in {"script", "style", "noscript", "template"}:  # info: if tag in { "script" , "style" ,
            self._skip_depth = max(0, self._skip_depth - 1)  # info: self . _skip_depth = max ( 0 ,
            return  # info: return
        if not self._skip_depth and tag in self._BLOCK_TAGS:  # info: if not self . _skip_depth and tag in
            self.parts.append("\n")  # info: self . parts . append ( "\n" )

    def handle_data(self, data: str) -> None:  # info: def handle_data
        if not self._skip_depth:  # info: if not self . _skip_depth :
            self.parts.append(data)  # info: self . parts . append ( data )


# ====================================================
# SECTION: function _normalize_inline_whitespace
# What it does: Collapse runs of spaces/tabs to a single space without destroying letters. IMPORTANT: never put the letter t into a character class. Use an explicit tab character via chr(9) so the
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _normalize_inline_whitespace(text: str) -> str:  # info: def _normalize_inline_whitespace
    """Collapse runs of spaces/tabs to a single space without destroying letters.

    IMPORTANT: never put the letter t into a character class. Use an explicit
    tab character via chr(9) so the source cannot be corrupted by escape
    double-processing.
    """
    tab = chr(9)  # info: set tab
    text = text.replace(tab, " ")  # info: set text
    return re.sub(r" +", " ", text).strip()  # info: return re . sub ( r" +" , " "


# ====================================================
# SECTION: function _strip_chrome
# What it does: Drop trailing NWS website chrome if it leaked into extracted body text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _strip_chrome(text: str) -> str:  # info: def _strip_chrome
    """Drop trailing NWS website chrome if it leaked into extracted body text."""  # info: """Drop trailing NWS website chrome if it leaked into extracted body text."""
    cut = len(text)  # info: set cut
    for marker in _CHROME_MARKERS:  # info: for marker in _CHROME_MARKERS :
        idx = text.find(marker)  # info: set idx
        if idx != -1:  # info: if idx != - 1 :
            cut = min(cut, idx)  # info: set cut
    return text[:cut].rstrip()  # info: return text [ : cut ] . rstrip


# ====================================================
# SECTION: function _pre_product_text
# What it does: Prefer the last <pre> block — that is the official NWS product body.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pre_product_text(raw: str) -> str | None:  # info: def _pre_product_text
    """Prefer the last <pre> block — that is the official NWS product body."""  # info: """Prefer the last <pre> block — that is the official NWS product body."""
    pre_matches = re.findall(r"<pre\b[^>]*>(.*?)</pre\s*>", raw, flags=re.I | re.S)  # info: set pre_matches
    if not pre_matches:  # info: if not pre_matches :
        return None  # info: return None
    body = html.unescape(re.sub(r"<[^>]+>", "", pre_matches[-1]))  # info: set body
    # Preserve fixed-width spacing inside the product. Only normalize newlines.
    body = body.replace("\r\n", "\n").replace("\r", "\n")  # info: set body
    body = _strip_chrome(body)  # info: set body
    # Trim trailing blank lines only; keep internal column alignment intact.
    return body.rstrip() + ("\n" if body.strip() else "")  # info: return body . rstrip ( ) + (


# ====================================================
# SECTION: function _html_to_text
# What it does: Extract visible text from HTML. When a <pre> product block exists, return it verbatim (fixed-width safe). Otherwise parse visible text and normalize inline whitespace carefully.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _html_to_text(raw: str, *, preserve_pre: bool = True) -> str:  # info: def _html_to_text
    """Extract visible text from HTML.

    When a <pre> product block exists, return it verbatim (fixed-width safe).
    Otherwise parse visible text and normalize inline whitespace carefully.
    """
    if preserve_pre:  # info: if preserve_pre :
        pre = _pre_product_text(raw)  # info: set pre
        if pre and pre.strip():  # info: if pre and pre . strip ( )
            return pre.strip("\n")  # info: return pre . strip ( "\n" )

    parser = _VisibleTextParser()  # info: set parser
    try:  # info: try :
        parser.feed(raw)  # info: parser . feed ( raw )
        parser.close()  # info: parser . close ( )
        text = html.unescape("".join(parser.parts))  # info: set text
    except Exception:  # info: except Exception :
        text = html.unescape(re.sub(r"<[^>]+>", "", raw))  # info: set text

    text = text.replace("\r\n", "\n").replace("\r", "\n")  # info: set text
    lines = [_normalize_inline_whitespace(line) for line in text.splitlines()]  # info: set lines
    # Collapse excessive blank lines but keep paragraph breaks.
    cleaned: list[str] = []  # info: set cleaned
    blank_run = 0  # info: set blank_run
    for line in lines:  # info: for line in lines :
        if not line:  # info: if not line :
            blank_run += 1  # info: set blank_run
            if blank_run <= 1:  # info: if blank_run <= 1 :
                cleaned.append("")  # info: cleaned . append ( "" )
            continue  # info: continue
        blank_run = 0  # info: set blank_run
        cleaned.append(line)  # info: cleaned . append ( line )
    return _strip_chrome("\n".join(cleaned)).strip()  # info: return _strip_chrome ( "\n" . join ( cleaned


# ====================================================
# SECTION: function _extract_report_text
# What it does:  extract report text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _extract_report_text(path: Path) -> str | None:  # info: def _extract_report_text
    try:  # info: try :
        raw = path.read_text(encoding="utf-8", errors="replace")  # info: set raw
    except OSError:  # info: except OSError :
        return None  # info: return None

    if not raw.strip():  # info: if not raw . strip ( ) :
        return None  # info: return None

    if path.suffix.lower() == ".html":  # info: if path . suffix . lower ( )
        text = _html_to_text(raw, preserve_pre=True)  # info: set text
        return text or None  # info: return text or None

    if path.suffix.lower() != ".json":  # info: if path . suffix . lower ( )
        # Plain text / .txt product bodies: preserve exact spacing.
        body = raw.replace("\r\n", "\n").replace("\r", "\n")  # info: set body
        body = _strip_chrome(body)  # info: set body
        return body.rstrip() or None  # info: return body . rstrip ( ) or None

    try:  # info: try :
        obj = json.loads(raw)  # info: set obj
    except json.JSONDecodeError:  # info: except json . JSONDecodeError :
        return None  # info: return None

    def find_product_text(node: Any) -> str | None:  # info: def find_product_text
        if isinstance(node, dict):  # info: if isinstance ( node , dict ) :
            value = node.get("productText")  # info: set value
            if isinstance(value, str) and value.strip():  # info: if isinstance ( value , str ) and
                return value.strip()  # info: return value . strip ( )
            for child in node.values():  # info: for child in node . values ( )
                found = find_product_text(child)  # info: set found
                if found:  # info: if found :
                    return found  # info: return found
        elif isinstance(node, list):  # info: elif isinstance ( node , list ) :
            for child in node:  # info: for child in node :
                found = find_product_text(child)  # info: set found
                if found:  # info: if found :
                    return found  # info: return found
        return None  # info: return None

    product_text = find_product_text(obj)  # info: set product_text
    if product_text:  # info: if product_text :
        return _strip_chrome(product_text.replace("\r\n", "\n").replace("\r", "\n")).rstrip()  # info: return _strip_chrome ( product_text . replace ( "\r\n"

    # Metadata-only capture (e.g. products list without a second-hop body).
    if isinstance(obj, dict):  # info: if isinstance ( obj , dict ) :
        keys = (  # info: set keys
            "productName", "productCode", "issuingOffice", "issuanceTime",  # info: "productName" , "productCode" , "issuingOffice" , "issuanceTime" ,
            "wmoCollectiveId", "id", "@id",  # info: "wmoCollectiveId" , "id" , "@id" ,
        )  # info: )
        lines = []  # info: set lines
        for key in keys:  # info: for key in keys :
            value = obj.get(key)  # info: set value
            if value is not None and str(value).strip():  # info: if value is not None and str (
                lines.append("{}: {}".format(key, value))  # info: lines . append ( "{}: {}" . format (
        if lines:  # info: if lines :
            return "\n".join(lines)  # info: return "\n" . join ( lines )

    return None  # info: return None


# ====================================================
# SECTION: function _header
# What it does:  header.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _header(title: str, source_url: str, fetched_at: str | None, created_at: str) -> str:  # info: def _header
    return "\n".join([  # info: return "\n" . join ( [
        "# {}".format(title),
        "",  # info: "" ,
        "> **Official NWS Hawaii/HFO report — derived locally from collected source data.**",  # info: "> **Official NWS Hawaii/HFO report — derived locally from collected source data.**" ,
        "",  # info: "" ,
        "- **Source:** {}".format(source_url),  # info: "- **Source:** {}" . format ( source_url ) ,
        "- **Collected:** {} HST".format(fetched_at or "Unknown"),  # info: "- **Collected:** {} HST" . format ( fetched_at or "Unknown" )
        "- **Report created:** {} HST".format(created_at),  # info: "- **Report created:** {} HST" . format ( created_at ) ,
        "- **Raw source:** retained separately in the weather data tree.",  # info: "- **Raw source:** retained separately in the weather data tree." ,
        "",  # info: "" ,
        "---",  # info: "---" ,
        "",  # info: "" ,
    ])  # info: ] )


# ====================================================
# SECTION: function _as_markdown_report
# What it does: Preserve fixed-width NWS formatting without Markdown mangling it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _as_markdown_report(body: str) -> str:  # info: def _as_markdown_report
    """Preserve fixed-width NWS formatting without Markdown mangling it."""  # info: """Preserve fixed-width NWS formatting without Markdown mangling it."""
    fence = "`" * 3  # info: set fence
    body = body.replace(fence, "[NWS-FENCE]")  # info: set body
    return fence + "text\n" + body.rstrip() + "\n" + fence  # info: return fence + "text\n" + body . rstrip


# ====================================================
# SECTION: function _cell_text
# What it does: Plain text for one table cell — never destroy letter characters.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _cell_text(raw_cell: str) -> str:  # info: def _cell_text
    """Plain text for one table cell — never destroy letter characters."""  # info: """Plain text for one table cell — never destroy letter characters."""
    text = re.sub(r"<[^>]+>", " ", raw_cell)  # info: set text
    text = html.unescape(text)  # info: set text
    return _normalize_inline_whitespace(text).replace("|", "\\|")  # info: return _normalize_inline_whitespace ( text ) . replace (


# ====================================================
# SECTION: function _parse_rwr_stations
# What it does: Map ICAO station id -> observation fields from the HFO RWR HTML table.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _parse_rwr_stations(raw: str) -> dict[str, dict[str, str]]:  # info: def _parse_rwr_stations
    """Map ICAO station id -> observation fields from the HFO RWR HTML table."""  # info: """Map ICAO station id -> observation fields from the HFO RWR HTML table."""
    stations: dict[str, dict[str, str]] = {}  # info: set stations
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", raw, flags=re.I | re.S):  # info: for row in re . findall ( r"<tr\b[^>]*>(.*?)</tr>"
        icao_match = re.search(  # info: set icao_match
            r"href=[\"'][^\"']*/([A-Z0-9]{4})\.html[\"']",  # info: r"href=[\"'][^\"']*/([A-Z0-9]{4})\.html[\"']" ,
            row,  # info: row ,
            flags=re.I,  # info: set flags
        )  # info: )
        if not icao_match:  # info: if not icao_match :
            continue  # info: continue
        icao = icao_match.group(1).upper()  # info: set icao
        # First table wins (Fahrenheit). Never overwrite with the Celsius twin.
        if icao in stations:  # info: if icao in stations :
            continue  # info: continue
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.I | re.S)  # info: set cells
        if len(cells) < 7:  # info: if len ( cells ) < 7 :
            continue  # info: continue
        values = [_cell_text(cell) for cell in cells]  # info: set values
        stations[icao] = {  # info: stations [ icao ] = {
            "conditions": values[1] or "—",  # info: "conditions" : values [ 1 ] or "—"
            "temp": values[2] or "—",  # info: "temp" : values [ 2 ] or "—"
            "dewpoint": values[3] or "—",  # info: "dewpoint" : values [ 3 ] or "—"
            "rh": values[4] or "—",  # info: "rh" : values [ 4 ] or "—"
            "wind": values[5] or "—",  # info: "wind" : values [ 5 ] or "—"
            "pressure": values[6] or "—",  # info: "pressure" : values [ 6 ] or "—"
        }  # info: }
    return stations  # info: return stations



# ====================================================
# SECTION: function _format_temp_f
# What it does: Render a temperature cell as °F, rejecting obvious Celsius twins.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _format_temp_f(value: str) -> str:  # info: def _format_temp_f
    """Render a temperature cell as °F, rejecting obvious Celsius twins."""  # info: """Render a temperature cell as °F, rejecting obvious Celsius twins."""
    text = (value or "").strip()  # info: set text
    if not text or text == "—":  # info: if not text or text == "—" :
        return "—"  # info: return "—"
    match = re.search(r"-?\d+", text)  # info: set match
    if not match:  # info: if not match :
        return text  # info: return text
    number = int(match.group(0))  # info: set number
    if number < 40:  # info: if number < 40 :
        number = int(round(number * 9 / 5 + 32))  # info: set number
    return "{}°F".format(number)  # info: return "{}°F" . format ( number )


# ====================================================
# SECTION: function _current_conditions
# What it does: Build a compact current-conditions table from the collected HFO RWR page.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _current_conditions(base: Path) -> str:  # info: def _current_conditions
    """Build a compact current-conditions table from the collected HFO RWR page."""  # info: """Build a compact current-conditions table from the collected HFO RWR page."""
    source = base / "weather.gov" / "hfo" / "RWR" / "raw" / "RWR_raw_current.html"  # info: set source
    if not source.is_file():  # info: if not source . is_file ( ) :
        return "Current conditions are unavailable from the latest collected HFO observations."  # info: return "Current conditions are unavailable from the latest collected HFO observations."

    try:  # info: try :
        raw = source.read_text(encoding="utf-8", errors="replace")  # info: set raw
    except OSError:  # info: except OSError :
        return "Current conditions are unavailable from the latest collected HFO observations."  # info: return "Current conditions are unavailable from the latest collected HFO observations."

    parsed = _parse_rwr_stations(raw)  # info: set parsed
    stations = [  # info: set stations
        ("PHNL", "Honolulu"),  # info: call (
        ("PHLI", "Lihue"),  # info: call (
        ("PHOG", "Kahului"),  # info: call (
        ("PHTO", "Hilo"),  # info: call (
        ("PHKO", "Kailua-Kona"),  # info: Kailua-Kona ASOS (PHKO); Mountain View/Volcano have no RWR ICAO row
    ]  # info: ]
    rows: list[str] = []  # info: set rows
    for icao, label in stations:  # info: for icao , label in stations :
        obs = parsed.get(icao)  # info: set obs
        if not obs:  # info: if not obs :
            continue  # info: continue
        rows.append(  # info: rows . append (
            "| {} | {} | {} | {} | {}% | {} | {} |".format(  # info: "| {} | {} | {} | {} | {}% | {} | {} |" . format (
                label,  # info: label ,
                obs["conditions"],  # info: obs [ "conditions" ] ,
                _format_temp_f(obs["temp"]),  # info: call _format_temp_f
                _format_temp_f(obs["dewpoint"]),  # info: call _format_temp_f
                obs["rh"],  # info: obs [ "rh" ] ,
                obs["wind"],  # info: obs [ "wind" ] ,
                obs["pressure"],  # info: obs [ "pressure" ] ,
            )  # info: )
        )  # info: )

    if not rows:  # info: if not rows :
        return "Current conditions are unavailable from the latest collected HFO observations."  # info: return "Current conditions are unavailable from the latest collected HFO observations."

    return "\n".join([  # info: return "\n" . join ( [
        "| Location | Conditions | Temp | Dew point | RH | Wind | Pressure |",  # info: "| Location | Conditions | Temp | Dew point | RH | Wind | Pressure |" ,
        "|---|---|---:|---:|---:|---|---:|",  # info: "|---|---|---:|---:|---:|---|---:|" ,
        *rows,  # info: * rows ,
        "",  # info: "" ,
        "_Source: locally collected NWS-HFO Regional Weather Roundup (RWR). Values are °F._",  # info: "_Source: locally collected NWS-HFO Regional Weather Roundup (RWR). Values are °F._" ,
    ])  # info: ] )


# ====================================================
# SECTION: function _existing_created_at
# What it does: Read the report creation timestamp before it is replaced.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _existing_created_at(path: Path) -> str | None:  # info: def _existing_created_at
    """Read the report creation timestamp before it is replaced."""  # info: """Read the report creation timestamp before it is replaced."""
    try:  # info: try :
        raw = path.read_text(encoding="utf-8", errors="replace")  # info: set raw
    except OSError:  # info: except OSError :
        return None  # info: return None
    match = re.search(r"^- \*\*Report created:\*\* (.+?) HST$", raw, flags=re.M)  # info: set match
    return match.group(1).strip() if match else None  # info: return match . group ( 1 ) .


# ====================================================
# SECTION: function _archive_current
# What it does: Archive an existing current report using its original creation timestamp.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _archive_current(current_path: Path, archive_dir: Path, fallback_created_at: str) -> None:  # info: def _archive_current
    """Archive an existing current report using its original creation timestamp."""  # info: """Archive an existing current report using its original creation timestamp."""
    if not current_path.is_file():  # info: if not current_path . is_file ( ) :
        return  # info: return
    created_at = _existing_created_at(current_path) or fallback_created_at  # info: set created_at
    safe_timestamp = re.sub(r"[^0-9A-Za-z:+-]", "-", created_at).strip("-")  # info: set safe_timestamp
    stem = current_path.name.removesuffix("_current.md")  # info: set stem
    archive_path = archive_dir / (stem + "_" + safe_timestamp + ".md")  # info: set archive_path
    if archive_path.exists():  # info: if archive_path . exists ( ) :
        index = 2  # info: set index
        while True:  # info: while True :
            candidate = archive_dir / (stem + "_" + safe_timestamp + "_" + str(index) + ".md")  # info: set candidate
            if not candidate.exists():  # info: if not candidate . exists ( ) :
                archive_path = candidate  # info: set archive_path
                break  # info: break
            index += 1  # info: set index
    archive_dir.mkdir(parents=True, exist_ok=True)  # info: archive_dir . mkdir ( parents = True ,
    current_path.replace(archive_path)  # info: current_path . replace ( archive_path )


# ====================================================
# SECTION: function _write_current
# What it does: Write current, archiving the previous version only when content changed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_current(current_path: Path, content: str, archive_dir: Path, created_at: str) -> None:  # info: def _write_current
    """Write current, archiving the previous version only when content changed."""  # info: """Write current, archiving the previous version only when content changed."""
    if current_path.is_file():  # info: if current_path . is_file ( ) :
        try:  # info: try :
            existing = current_path.read_text(encoding="utf-8", errors="replace")  # info: set existing
            comparable_existing = re.sub(  # info: set comparable_existing
                r"^- \*\*Generated:\*\* .+? HST$",  # info: r"^- \*\*Generated:\*\* .+? HST$" ,
                "- **Generated:** <timestamp> HST",  # info: "- **Generated:** <timestamp> HST" ,
                existing,  # info: existing ,
                flags=re.M,  # info: set flags
            )  # info: )
            comparable_content = re.sub(  # info: set comparable_content
                r"^- \*\*Generated:\*\* .+? HST$",  # info: r"^- \*\*Generated:\*\* .+? HST$" ,
                "- **Generated:** <timestamp> HST",  # info: "- **Generated:** <timestamp> HST" ,
                content,  # info: content ,
                flags=re.M,  # info: set flags
            )  # info: )
            if comparable_existing == comparable_content:  # info: if comparable_existing == comparable_content :
                return  # info: return
        except OSError:  # info: except OSError :
            pass  # info: pass
        _archive_current(current_path, archive_dir, created_at)  # info: call _archive_current
    current_path.parent.mkdir(parents=True, exist_ok=True)  # info: current_path . parent . mkdir ( parents =
    current_path.write_text(content, encoding="utf-8")  # info: current_path . write_text ( content , encoding =


# ====================================================
# SECTION: function _build_readme_sections
# What it does: Build the human-readable statewide section body used by README templates.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _build_readme_sections(  # info: def _build_readme_sections
    sections: list[tuple[str, str, str, str | None, str]],  # info: set sections
) -> str:  # info: ) -> str :
    """Build the human-readable statewide section body used by README templates."""  # info: """Build the human-readable statewide section body used by README templates."""
    parts: list[str] = []  # info: set parts
    for index, (resource_id, title, source_url, fetched_at, body) in enumerate(sections, 1):  # info: for index , ( resource_id , title ,
        parts.extend([  # info: parts . extend ( [
            "### {}. {}".format(index, title),
            "",  # info: "" ,
            "| Field | Value |",  # info: "| Field | Value |" ,
            "|---|---|",  # info: "|---|---|" ,
            "| **Resource ID** | {} |".format(resource_id),  # info: "| **Resource ID** | {} |" . format ( resource_id ) ,
            "| **Official source** | {} |".format(source_url),  # info: "| **Official source** | {} |" . format ( source_url ) ,
            "| **Collected** | {} HST |".format(fetched_at or "Unknown"),  # info: "| **Collected** | {} HST |" . format ( fetched_at or "Unknown" )
            "",  # info: "" ,
            _as_markdown_report(body),  # info: call _as_markdown_report
            "",  # info: "" ,
            "---",  # info: "---" ,
            "",  # info: "" ,
        ])  # info: ] )
    return "\n".join(parts).rstrip()  # info: return "\n" . join ( parts ) .


# ====================================================
# SECTION: function _render_readme
# What it does:  render readme.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _render_readme(template: str, replacements: dict[str, str]) -> str:  # info: def _render_readme
    content = template  # info: set content
    for key, value in replacements.items():  # info: for key , value in replacements . items
        content = content.replace(key, value)  # info: set content
    missing = [key for key in _README_PLACEHOLDERS if key in content]  # info: set missing
    if missing:  # info: if missing :
        raise RuntimeError(  # info: raise RuntimeError (
            "README placeholder(s) were not rendered: {}".format(", ".join(missing))  # info: "README placeholder(s) were not rendered: {}" . format ( ", " . join (
        )  # info: )
    return content.rstrip() + "\n"  # info: return content . rstrip ( ) + "\n"


# ====================================================
# SECTION: function generate
# What it does: Generate level-0 per-product Markdown reports and one statewide aggregate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def generate(base_dir: str) -> list[Path]:  # info: def generate
    """Generate level-0 per-product Markdown reports and one statewide aggregate."""  # info: """Generate level-0 per-product Markdown reports and one statewide aggregate."""
    base = Path(base_dir)  # info: set base
    reports_root = base.parent / REPORTS_DIRNAME  # info: set reports_root
    reports_dir = reports_root / LEVEL0_DIRNAME  # info: set reports_dir
    archive_dir = reports_dir / ARCHIVE_DIRNAME  # info: set archive_dir
    reports_dir.mkdir(parents=True, exist_ok=True)  # info: reports_dir . mkdir ( parents = True ,

    manifest = Manifest(base_dir).load()  # info: set manifest
    names = _load_resource_names()  # info: set names

    expected = {AGGREGATE_FILENAME}  # info: set expected
    for resource_id in manifest.all_states():  # info: for resource_id in manifest . all_states ( )
        expected.add("{}_current.md".format(resource_id))  # info: expected . add ( "{}_current.md" . format (
    for old in reports_dir.glob("*_current.md"):  # info: for old in reports_dir . glob ( "*_current.md"
        if old.name not in expected:  # info: if old . name not in expected :
            old.unlink()  # info: old . unlink ( )
    sections: list[tuple[str, str, str, str | None, str]] = []  # info: set sections
    now = hst_time.hst_now().isoformat(timespec="seconds")  # info: set now

    for resource_id, state in manifest.all_states().items():  # info: for resource_id , state in manifest . all_states
        local_dir = base / state.local_resource_dir  # info: set local_dir
        if not local_dir.is_dir():  # info: if not local_dir . is_dir ( ) :
            continue  # info: continue

        candidates = sorted(p for p in local_dir.glob("*_current.*") if p.is_file())  # info: set candidates
        if not candidates:  # info: if not candidates :
            continue  # info: continue
        current_path = candidates[0]  # info: set current_path

        if not _is_reportable(resource_id, state.url, current_path):  # info: if not _is_reportable ( resource_id , state .
            continue  # info: continue

        body = _extract_report_text(current_path)  # info: set body
        if not body:  # info: if not body :
            continue  # info: continue

        title = _display_name(resource_id, names)  # info: set title
        report_path = reports_dir / "{}_current.md".format(resource_id)  # info: set report_path
        created_at = now  # info: set created_at
        report = (  # info: set report
            _header(title, state.url, state.current_fetch_timestamp_hst, created_at)  # info: call _header
            + _as_markdown_report(body)  # info: call +
            + "\n"  # info: + "\n"
        )  # info: )
        _write_current(report_path, report, archive_dir, now)  # info: call _write_current
        sections.append((resource_id, title, state.url, state.current_fetch_timestamp_hst, body))  # info: sections . append ( ( resource_id , title

    sections.sort(key=lambda item: (item[1].lower(), item[0].lower()))  # info: sections . sort ( key = lambda item

    aggregate_created_at = now  # info: set aggregate_created_at
    aggregate: list[str] = [  # info: set aggregate
        "# Hawaii State Weather Report",
        "",  # info: "" ,
        "> **Official NWS Hawaii/HFO statewide collection — generated automatically from locally collected current reports.**",  # info: "> **Official NWS Hawaii/HFO statewide collection — generated automatically from locally collected current rep
        "",  # info: "" ,
        "- **Generated:** {} HST".format(now),  # info: "- **Generated:** {} HST" . format ( now ) ,
        "- **Report created:** {} HST".format(aggregate_created_at),  # info: "- **Report created:** {} HST" . format ( aggregate_created_at ) ,
        "- **Current report sections:** {}".format(len(sections)),  # info: "- **Current report sections:** {}" . format ( len ( sections )
        "- **Raw source data:** retained separately; this document is derived and may be regenerated at any time.",  # info: "- **Raw source data:** retained separately; this document is derived and may be regenerated at any time." ,
        "",  # info: "" ,
        "---",  # info: "---" ,
        "",  # info: "" ,
    ]  # info: ]

    for index, (resource_id, title, source_url, fetched_at, body) in enumerate(sections, 1):  # info: for index , ( resource_id , title ,
        aggregate.extend([  # info: aggregate . extend ( [
            "## {}. {}".format(index, title),
            "",  # info: "" ,
            "- **Resource ID:** {}".format(resource_id),  # info: "- **Resource ID:** {}" . format ( resource_id ) ,
            "- **Source:** {}".format(source_url),  # info: "- **Source:** {}" . format ( source_url ) ,
            "- **Collected:** {} HST".format(fetched_at or "Unknown"),  # info: "- **Collected:** {} HST" . format ( fetched_at or "Unknown" )
            "",  # info: "" ,
            _as_markdown_report(body),  # info: call _as_markdown_report
            "",  # info: "" ,
            "---",  # info: "---" ,
            "",  # info: "" ,
        ])  # info: ] )

    aggregate_path = reports_dir / AGGREGATE_FILENAME  # info: set aggregate_path
    aggregate_content = "\n".join(aggregate)  # info: set aggregate_content
    _write_current(aggregate_path, aggregate_content, archive_dir, now)  # info: call _write_current

    try:  # info: try :
        generate_readme_banner(base)  # info: call generate_readme_banner
        banner_url = (  # info: set banner_url
            "https://raw.githubusercontent.com/rootrecordsoftwaresolutions/"  # info: "https://raw.githubusercontent.com/rootrecordsoftwaresolutions/"
            "RootRecord-Weather-Database/main/"  # info: "RootRecord-Weather-Database/main/"
            + quote(base.parent.name)  # info: call +
            + "/"  # info: + "/"
            + OUTPUT_RELATIVE.as_posix()  # info: + OUTPUT_RELATIVE . as_posix ( )
        )  # info: )
    except (FileNotFoundError, ValueError, RuntimeError):  # info: except ( FileNotFoundError , ValueError , RuntimeError )
        banner_url = (  # info: set banner_url
            "https://raw.githubusercontent.com/rootrecordsoftwaresolutions/"  # info: "https://raw.githubusercontent.com/rootrecordsoftwaresolutions/"
            "RootRecord-Weather-Database/main/"  # info: "RootRecord-Weather-Database/main/"
            + quote(base.parent.name + "/hfo/")  # info: call +
            + quote(  # info: call +
                "cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/"  # info: "cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/"
                "GOES18-HI-GEOCOLOR-600x600/GOES18-HI-GEOCOLOR-600x600_current.gif",  # info: "GOES18-HI-GEOCOLOR-600x600/GOES18-HI-GEOCOLOR-600x600_current.gif" ,
                safe="/",  # info: set safe
            )  # info: )
        )  # info: )

    current_conditions = _current_conditions(base)  # info: set current_conditions
    report_sections = _build_readme_sections(sections)  # info: set report_sections
    replacements = {  # info: set replacements
        "{{CURRENT_CONDITIONS}}": current_conditions,  # info: "{{CURRENT_CONDITIONS}}" : current_conditions ,
        "{{README_BANNER_URL}}": banner_url,  # info: "{{README_BANNER_URL}}" : banner_url ,
        "{{REPORT_UPDATED}}": "{} HST".format(now),  # info: "{{REPORT_UPDATED}}" : "{} HST" . format ( now )
        "{{REPORT_SECTION_COUNT}}": str(len(sections)),  # info: "{{REPORT_SECTION_COUNT}}" : str ( len ( sections )
        "{{REPORT_SECTIONS}}": report_sections,  # info: "{{REPORT_SECTIONS}}" : report_sections ,
    }  # info: }

    template_path = README_TEMPLATE  # info: set template_path
    if template_path.is_file():  # info: if template_path . is_file ( ) :
        template = template_path.read_text(encoding="utf-8")  # info: set template
    else:  # info: else :
        template = (  # info: set template
            "# Hawai'i State Weather Database\n\n"
            "{{CURRENT_CONDITIONS}}\n\n{{REPORT_SECTIONS}}\n"  # info: "{{CURRENT_CONDITIONS}}\n\n{{REPORT_SECTIONS}}\n"
        )  # info: )
    reports_readme = reports_root / "README.md"  # info: set reports_readme
    reports_readme.write_text(_render_readme(template, replacements), encoding="utf-8")  # info: reports_readme . write_text

    database_root = base.parent.parent  # info: set database_root
    database_readme = database_root / "README.md"  # info: set database_readme
    if DATABASE_README_TEMPLATE.is_file():  # info: if DATABASE_README_TEMPLATE . is_file ( ) :
        database_template = DATABASE_README_TEMPLATE.read_text(encoding="utf-8")  # info: set database_template
    else:  # info: else :
        database_template = (  # info: set database_template
            "# RootRecord Weather Database\n\n"
            "{{CURRENT_CONDITIONS}}\n\n{{REPORT_SECTIONS}}\n"  # info: "{{CURRENT_CONDITIONS}}\n\n{{REPORT_SECTIONS}}\n"
        )  # info: )
    database_readme.write_text(  # info: database_readme . write_text (
        _render_readme(database_template, replacements),  # info: call _render_readme
        encoding="utf-8",  # info: set encoding
    )  # info: )

    return [  # info: return [
        reports_dir / "{}_current.md".format(resource_id)  # info: reports_dir / "{}_current.md" . format ( resource_id )
        for resource_id, *_ in sections  # info: for resource_id , * _ in sections
    ] + [aggregate_path, reports_readme, database_readme]  # info: return the database report paths
