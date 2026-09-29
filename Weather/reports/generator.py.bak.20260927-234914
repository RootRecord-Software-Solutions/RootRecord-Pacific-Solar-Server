"""Generate human-readable Markdown reports from collected HFO data.

Raw fetched data remains authoritative. This module only writes derived files
under Database/WEATHER/Hawai'i/reports.
"""
from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
from typing import Any

import yaml

from core import hst_time
from core.manifest import Manifest

from reports.banner import OUTPUT_RELATIVE, generate_readme_banner

REPORTS_DIRNAME = "reports"
LEVEL0_DIRNAME = "0 Level Processing"
ARCHIVE_DIRNAME = "archived"
REPORTING_README = Path(__file__).resolve().parent / "README.md"
DATABASE_README_TEMPLATE = Path(__file__).resolve().parent / "WEATHER_DATABASE_README_TEMPLATE.md"
AGGREGATE_FILENAME = "Hawaii_State_Weather_Report_current.md"
_EXCLUDED_PREFIXES = ("alerts_", "wwamap_", "nhc_current_storms", "ndfd_", "obhistory_")
_EXCLUDED_IDS = {
    "rain_summary_graphical",
    "nhc_source_index",
    "noaa_solar_calculation_table",
    "nws_cwa_boundaries_catalog",
    "nws_fire_zones_catalog",
    "nws_marine_zones_catalog",
    "nws_public_counties_catalog",
    "nws_public_zones_catalog",
    "nws_zone_county_catalog",
}
_README_PLACEHOLDERS = (
    "{{CURRENT_CONDITIONS}}",
    "{{README_BANNER_URL}}",
    "{{REPORT_UPDATED}}",
    "{{REPORT_SECTION_COUNT}}",
    "{{REPORT_SECTIONS}}",
)

# Site chrome phrases that must never appear inside a product body.
_CHROME_MARKERS = (
    "Privacy Policy",
    "Freedom of Information Act",
    "USA.gov",
    "About Us",
    "Career Opportunities",
    "National Weather Service Home",
)


def _load_resource_names() -> dict[str, str]:
    path = Path(__file__).resolve().parent.parent / "config" / "resources.yaml"
    with path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    names: dict[str, str] = {}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "id" in node and "name" in node:
                names[str(node["id"])] = str(node["name"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(config)
    return names


def _display_name(resource_id: str, names: dict[str, str]) -> str:
    if resource_id in names:
        return names[resource_id]
    for base_id, name in names.items():
        if resource_id.startswith(base_id + "_"):
            return "{} — {}".format(name, resource_id[len(base_id) + 1:])
    return resource_id.replace("_", " ").title()


def _is_reportable(resource_id: str, state_url: str, path: Path) -> bool:
    if resource_id in _EXCLUDED_IDS:
        return False
    if any(resource_id.startswith(prefix) for prefix in _EXCLUDED_PREFIXES):
        return False
    if path.suffix.lower() not in {".txt", ".html", ".json"}:
        return False
    if path.suffix.lower() == ".json":
        return "api.weather.gov/products/" in state_url
    return True


class _VisibleTextParser(HTMLParser):
    """Extract visible HTML text while preserving useful line structure."""

    _BLOCK_TAGS = {
        "address", "article", "aside", "blockquote", "br", "dd", "div", "dl",
        "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2",
        "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol",
        "p", "pre", "section", "table", "td", "th", "tr", "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "template"}:
            self._skip_depth += 1
            return
        if not self._skip_depth and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "template"}:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if not self._skip_depth and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def _normalize_inline_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs to a single space without destroying letters.

    IMPORTANT: never put the letter t into a character class. Use an explicit
    tab character via chr(9) so the source cannot be corrupted by escape
    double-processing.
    """
    tab = chr(9)
    text = text.replace(tab, " ")
    return re.sub(r" +", " ", text).strip()


def _strip_chrome(text: str) -> str:
    """Drop trailing NWS website chrome if it leaked into extracted body text."""
    cut = len(text)
    for marker in _CHROME_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            cut = min(cut, idx)
    return text[:cut].rstrip()


def _pre_product_text(raw: str) -> str | None:
    """Prefer the last <pre> block — that is the official NWS product body."""
    pre_matches = re.findall(r"<pre\b[^>]*>(.*?)</pre\s*>", raw, flags=re.I | re.S)
    if not pre_matches:
        return None
    body = html.unescape(re.sub(r"<[^>]+>", "", pre_matches[-1]))
    # Preserve fixed-width spacing inside the product. Only normalize newlines.
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    body = _strip_chrome(body)
    # Trim trailing blank lines only; keep internal column alignment intact.
    return body.rstrip() + ("\n" if body.strip() else "")


def _html_to_text(raw: str, *, preserve_pre: bool = True) -> str:
    """Extract visible text from HTML.

    When a <pre> product block exists, return it verbatim (fixed-width safe).
    Otherwise parse visible text and normalize inline whitespace carefully.
    """
    if preserve_pre:
        pre = _pre_product_text(raw)
        if pre and pre.strip():
            return pre.strip("\n")

    parser = _VisibleTextParser()
    try:
        parser.feed(raw)
        parser.close()
        text = html.unescape("".join(parser.parts))
    except Exception:
        text = html.unescape(re.sub(r"<[^>]+>", "", raw))

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_normalize_inline_whitespace(line) for line in text.splitlines()]
    # Collapse excessive blank lines but keep paragraph breaks.
    cleaned: list[str] = []
    blank_run = 0
    for line in lines:
        if not line:
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
            continue
        blank_run = 0
        cleaned.append(line)
    return _strip_chrome("\n".join(cleaned)).strip()


def _extract_report_text(path: Path) -> str | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    if not raw.strip():
        return None

    if path.suffix.lower() == ".html":
        text = _html_to_text(raw, preserve_pre=True)
        return text or None

    if path.suffix.lower() != ".json":
        # Plain text / .txt product bodies: preserve exact spacing.
        body = raw.replace("\r\n", "\n").replace("\r", "\n")
        body = _strip_chrome(body)
        return body.rstrip() or None

    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None

    def find_product_text(node: Any) -> str | None:
        if isinstance(node, dict):
            value = node.get("productText")
            if isinstance(value, str) and value.strip():
                return value.strip()
            for child in node.values():
                found = find_product_text(child)
                if found:
                    return found
        elif isinstance(node, list):
            for child in node:
                found = find_product_text(child)
                if found:
                    return found
        return None

    product_text = find_product_text(obj)
    if product_text:
        return _strip_chrome(product_text.replace("\r\n", "\n").replace("\r", "\n")).rstrip()

    # Metadata-only capture (e.g. products list without a second-hop body).
    if isinstance(obj, dict):
        keys = (
            "productName", "productCode", "issuingOffice", "issuanceTime",
            "wmoCollectiveId", "id", "@id",
        )
        lines = []
        for key in keys:
            value = obj.get(key)
            if value is not None and str(value).strip():
                lines.append("{}: {}".format(key, value))
        if lines:
            return "\n".join(lines)

    return None


def _header(title: str, source_url: str, fetched_at: str | None, created_at: str) -> str:
    return "\n".join([
        "# {}".format(title),
        "",
        "> **Official NWS Hawaii/HFO report — derived locally from collected source data.**",
        "",
        "- **Source:** {}".format(source_url),
        "- **Collected:** {} HST".format(fetched_at or "Unknown"),
        "- **Report created:** {} HST".format(created_at),
        "- **Raw source:** retained separately in the weather data tree.",
        "",
        "---",
        "",
    ])


def _as_markdown_report(body: str) -> str:
    """Preserve fixed-width NWS formatting without Markdown mangling it."""
    fence = "`" * 3
    body = body.replace(fence, "[NWS-FENCE]")
    return fence + "text\n" + body.rstrip() + "\n" + fence


def _cell_text(raw_cell: str) -> str:
    """Plain text for one table cell — never destroy letter characters."""
    text = re.sub(r"<[^>]+>", " ", raw_cell)
    text = html.unescape(text)
    return _normalize_inline_whitespace(text).replace("|", "\\|")


def _parse_rwr_stations(raw: str) -> dict[str, dict[str, str]]:
    """Map ICAO station id -> observation fields from the HFO RWR HTML table."""
    stations: dict[str, dict[str, str]] = {}
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", raw, flags=re.I | re.S):
        icao_match = re.search(
            r"href=[\"'][^\"']*/([A-Z0-9]{4})\.html[\"']",
            row,
            flags=re.I,
        )
        if not icao_match:
            continue
        icao = icao_match.group(1).upper()
        # First table wins (Fahrenheit). Never overwrite with the Celsius twin.
        if icao in stations:
            continue
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.I | re.S)
        if len(cells) < 7:
            continue
        values = [_cell_text(cell) for cell in cells]
        stations[icao] = {
            "conditions": values[1] or "—",
            "temp": values[2] or "—",
            "dewpoint": values[3] or "—",
            "rh": values[4] or "—",
            "wind": values[5] or "—",
            "pressure": values[6] or "—",
        }
    return stations



def _format_temp_f(value: str) -> str:
    """Render a temperature cell as °F, rejecting obvious Celsius twins."""
    text = (value or "").strip()
    if not text or text == "—":
        return "—"
    match = re.search(r"-?\d+", text)
    if not match:
        return text
    number = int(match.group(0))
    if number < 40:
        number = int(round(number * 9 / 5 + 32))
    return "{}°F".format(number)


def _current_conditions(base: Path) -> str:
    """Build a compact current-conditions table from the collected HFO RWR page."""
    source = base / "weather.gov" / "hfo" / "RWR" / "raw" / "RWR_raw_current.html"
    if not source.is_file():
        return "Current conditions are unavailable from the latest collected HFO observations."

    try:
        raw = source.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "Current conditions are unavailable from the latest collected HFO observations."

    parsed = _parse_rwr_stations(raw)
    stations = [
        ("PHNL", "Honolulu"),
        ("PHLI", "Lihue"),
        ("PHOG", "Kahului"),
        ("PHTO", "Hilo"),
        ("PHKO", "Kona"),
    ]
    rows: list[str] = []
    for icao, label in stations:
        obs = parsed.get(icao)
        if not obs:
            continue
        rows.append(
            "| {} | {} | {} | {} | {}% | {} | {} |".format(
                label,
                obs["conditions"],
                _format_temp_f(obs["temp"]),
                _format_temp_f(obs["dewpoint"]),
                obs["rh"],
                obs["wind"],
                obs["pressure"],
            )
        )

    if not rows:
        return "Current conditions are unavailable from the latest collected HFO observations."

    return "\n".join([
        "| Location | Conditions | Temp | Dew point | RH | Wind | Pressure |",
        "|---|---|---:|---:|---:|---|---:|",
        *rows,
        "",
        "_Source: locally collected NWS-HFO Regional Weather Roundup (RWR). Values are °F._",
    ])


def _existing_created_at(path: Path) -> str | None:
    """Read the report creation timestamp before it is replaced."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = re.search(r"^- \*\*Report created:\*\* (.+?) HST$", raw, flags=re.M)
    return match.group(1).strip() if match else None


def _archive_current(current_path: Path, archive_dir: Path, fallback_created_at: str) -> None:
    """Archive an existing current report using its original creation timestamp."""
    if not current_path.is_file():
        return
    created_at = _existing_created_at(current_path) or fallback_created_at
    safe_timestamp = re.sub(r"[^0-9A-Za-z:+-]", "-", created_at).strip("-")
    stem = current_path.name.removesuffix("_current.md")
    archive_path = archive_dir / (stem + "_" + safe_timestamp + ".md")
    if archive_path.exists():
        index = 2
        while True:
            candidate = archive_dir / (stem + "_" + safe_timestamp + "_" + str(index) + ".md")
            if not candidate.exists():
                archive_path = candidate
                break
            index += 1
    archive_dir.mkdir(parents=True, exist_ok=True)
    current_path.replace(archive_path)


def _write_current(current_path: Path, content: str, archive_dir: Path, created_at: str) -> None:
    """Write current, archiving the previous version only when content changed."""
    if current_path.is_file():
        try:
            existing = current_path.read_text(encoding="utf-8", errors="replace")
            comparable_existing = re.sub(
                r"^- \*\*Generated:\*\* .+? HST$",
                "- **Generated:** <timestamp> HST",
                existing,
                flags=re.M,
            )
            comparable_content = re.sub(
                r"^- \*\*Generated:\*\* .+? HST$",
                "- **Generated:** <timestamp> HST",
                content,
                flags=re.M,
            )
            if comparable_existing == comparable_content:
                return
        except OSError:
            pass
        _archive_current(current_path, archive_dir, created_at)
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(content, encoding="utf-8")


def _build_readme_sections(
    sections: list[tuple[str, str, str, str | None, str]],
) -> str:
    """Build the human-readable statewide section body used by README templates."""
    parts: list[str] = []
    for index, (resource_id, title, source_url, fetched_at, body) in enumerate(sections, 1):
        parts.extend([
            "### {}. {}".format(index, title),
            "",
            "| Field | Value |",
            "|---|---|",
            "| **Resource ID** | {} |".format(resource_id),
            "| **Official source** | {} |".format(source_url),
            "| **Collected** | {} HST |".format(fetched_at or "Unknown"),
            "",
            _as_markdown_report(body),
            "",
            "---",
            "",
        ])
    return "\n".join(parts).rstrip()


def _render_readme(template: str, replacements: dict[str, str]) -> str:
    content = template
    for key, value in replacements.items():
        content = content.replace(key, value)
    missing = [key for key in _README_PLACEHOLDERS if key in content]
    if missing:
        raise RuntimeError(
            "README placeholder(s) were not rendered: {}".format(", ".join(missing))
        )
    return content.rstrip() + "\n"


def generate(base_dir: str) -> list[Path]:
    """Generate level-0 per-product Markdown reports and one statewide aggregate."""
    base = Path(base_dir)
    reports_root = base.parent / REPORTS_DIRNAME
    reports_dir = reports_root / LEVEL0_DIRNAME
    archive_dir = reports_dir / ARCHIVE_DIRNAME
    reports_dir.mkdir(parents=True, exist_ok=True)

    manifest = Manifest(base_dir).load()
    names = _load_resource_names()

    expected = {AGGREGATE_FILENAME}
    for resource_id in manifest.all_states():
        expected.add("{}_current.md".format(resource_id))
    for old in reports_dir.glob("*_current.md"):
        if old.name not in expected:
            old.unlink()
    sections: list[tuple[str, str, str, str | None, str]] = []
    now = hst_time.hst_now().isoformat(timespec="seconds")

    for resource_id, state in manifest.all_states().items():
        local_dir = base / state.local_resource_dir
        if not local_dir.is_dir():
            continue

        candidates = sorted(p for p in local_dir.glob("*_current.*") if p.is_file())
        if not candidates:
            continue
        current_path = candidates[0]

        if not _is_reportable(resource_id, state.url, current_path):
            continue

        body = _extract_report_text(current_path)
        if not body:
            continue

        title = _display_name(resource_id, names)
        report_path = reports_dir / "{}_current.md".format(resource_id)
        created_at = now
        report = (
            _header(title, state.url, state.current_fetch_timestamp_hst, created_at)
            + _as_markdown_report(body)
            + "\n"
        )
        _write_current(report_path, report, archive_dir, now)
        sections.append((resource_id, title, state.url, state.current_fetch_timestamp_hst, body))

    sections.sort(key=lambda item: (item[1].lower(), item[0].lower()))

    aggregate_created_at = now
    aggregate: list[str] = [
        "# Hawaii State Weather Report",
        "",
        "> **Official NWS Hawaii/HFO statewide collection — generated automatically from locally collected current reports.**",
        "",
        "- **Generated:** {} HST".format(now),
        "- **Report created:** {} HST".format(aggregate_created_at),
        "- **Current report sections:** {}".format(len(sections)),
        "- **Raw source data:** retained separately; this document is derived and may be regenerated at any time.",
        "",
        "---",
        "",
    ]

    for index, (resource_id, title, source_url, fetched_at, body) in enumerate(sections, 1):
        aggregate.extend([
            "## {}. {}".format(index, title),
            "",
            "- **Resource ID:** {}".format(resource_id),
            "- **Source:** {}".format(source_url),
            "- **Collected:** {} HST".format(fetched_at or "Unknown"),
            "",
            _as_markdown_report(body),
            "",
            "---",
            "",
        ])

    aggregate_path = reports_dir / AGGREGATE_FILENAME
    aggregate_content = "\n".join(aggregate)
    _write_current(aggregate_path, aggregate_content, archive_dir, now)

    try:
        generate_readme_banner(base)
        banner_url = (
            "https://raw.githubusercontent.com/rootrecordsoftwaresolutions/"
            "RootRecord-Weather-Database/main/"
            + quote(base.parent.name)
            + "/"
            + OUTPUT_RELATIVE.as_posix()
        )
    except (FileNotFoundError, ValueError, RuntimeError):
        banner_url = (
            "https://raw.githubusercontent.com/rootrecordsoftwaresolutions/"
            "RootRecord-Weather-Database/main/"
            + quote(base.parent.name + "/hfo/")
            + quote(
                "cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/"
                "GOES18-HI-GEOCOLOR-600x600/GOES18-HI-GEOCOLOR-600x600_current.gif",
                safe="/",
            )
        )

    current_conditions = _current_conditions(base)
    report_sections = _build_readme_sections(sections)
    replacements = {
        "{{CURRENT_CONDITIONS}}": current_conditions,
        "{{README_BANNER_URL}}": banner_url,
        "{{REPORT_UPDATED}}": "{} HST".format(now),
        "{{REPORT_SECTION_COUNT}}": str(len(sections)),
        "{{REPORT_SECTIONS}}": report_sections,
    }

    template_path = REPORTING_README.with_name("README_TEMPLATE.md")
    if template_path.is_file():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = (
            "# Hawai'i State Weather Database\n\n"
            "{{CURRENT_CONDITIONS}}\n\n{{REPORT_SECTIONS}}\n"
        )
    REPORTING_README.write_text(_render_readme(template, replacements), encoding="utf-8")

    database_root = base.parent.parent
    database_readme = database_root / "README.md"
    if DATABASE_README_TEMPLATE.is_file():
        database_template = DATABASE_README_TEMPLATE.read_text(encoding="utf-8")
    else:
        database_template = (
            "# RootRecord Weather Database\n\n"
            "{{CURRENT_CONDITIONS}}\n\n{{REPORT_SECTIONS}}\n"
        )
    database_readme.write_text(
        _render_readme(database_template, replacements),
        encoding="utf-8",
    )

    return [
        reports_dir / "{}_current.md".format(resource_id)
        for resource_id, *_ in sections
    ] + [aggregate_path, REPORTING_README, database_readme]
