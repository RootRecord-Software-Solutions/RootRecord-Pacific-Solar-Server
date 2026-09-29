"""Build source-isolated mirrors of official report products.

This is NOT a processing level. It is a preservation/organization layer that
keeps official-source reports grouped by issuing source while Level 0 and
Level 1 remain processing layers.

The exact fetched source bytes remain in the URL-mirrored raw data tree.
These Markdown files are the readable official-product representation.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from core import hst_time
from core.manifest import Manifest
from reports.generator import _extract_report_text, _is_reportable, _display_name, _load_resource_names

ROOT = "reports"
OFFICIAL = "Official Sources"
LEVEL0 = "0 Level Processing"
ARCHIVE = "archived"


def _source_name(url: str) -> str:
    normalized = str(url or "").strip()
    if normalized.startswith("/"):
        normalized = "https://www.weather.gov" + normalized
    parsed = urlsplit(normalized)
    host = parsed.netloc.lower()
    if host in {"api.weather.gov", "www.weather.gov", "forecast.weather.gov"}:
        return "NWS-HFO"
    if host in {"www.nhc.noaa.gov", "nhc.noaa.gov"}:
        return "NHC"
    if host in {"www.noaa.gov", "noaa.gov"}:
        return "NOAA"
    if "gml.noaa.gov" in host:
        return "NOAA-GML"
    if "nesdis.noaa.gov" in host:
        return "NOAA-NESDIS"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", host or "unknown-source")


def _created(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"^- \*\*Report created:\*\* (.+?) HST$", text, re.M)
    return m.group(1).strip() if m else None


def _archive(path: Path, archive_dir: Path, fallback: str) -> None:
    if not path.is_file():
        return
    stamp = re.sub(r"[^0-9A-Za-z:+-]", "-", _created(path) or fallback).strip("-")
    stem = path.name.removesuffix("_current.md")
    target = archive_dir / f"{stem}_{stamp}.md"
    n = 2
    while target.exists():
        target = archive_dir / f"{stem}_{stamp}_{n}.md"
        n += 1
    archive_dir.mkdir(parents=True, exist_ok=True)
    path.replace(target)


def _normalize_for_compare(text: str) -> str:
    return re.sub(
        r"^- \*\*Generated:\*\* .+? HST$",
        "- **Generated:** <timestamp> HST",
        text,
        flags=re.M,
    )


def _write(path: Path, content: str, archive_dir: Path, created: str) -> bool:
    if path.is_file():
        try:
            old = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            old = ""
        if _normalize_for_compare(old) == _normalize_for_compare(content):
            return False
        _archive(path, archive_dir, created)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _body(text: str) -> str:
    fence = chr(96) * 3
    m = re.search(re.escape(fence) + r"text\n(.*?)\n" + re.escape(fence), text, re.S)
    return m.group(1).strip() if m else text.strip()


def generate(base_dir: str) -> list[Path]:
    """Generate source-isolated official reports directly from collected sources.

    This layer deliberately does not read Level 0. That prevents a processed
    report from becoming the supposed source of an official-source record.
    """
    base = Path(base_dir)
    reports_root = base.parent / ROOT
    official_root = reports_root / OFFICIAL
    now = hst_time.hst_now().isoformat(timespec="seconds")
    manifest = Manifest(base_dir).load()
    names = _load_resource_names()
    outputs: list[Path] = []

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

        source = _source_name(state.url)
        title = _display_name(resource_id, names)
        source_dir = official_root / source
        archive_dir = source_dir / ARCHIVE
        target = source_dir / f"{resource_id}_current.md"
        fence = chr(96) * 3
        content = "\n".join([
            f"# {title}",
            "",
            "> **Official-source report mirror.** This record is derived directly from the collected official source, not from Level 0 or another processing layer.",
            "",
            f"- **Generated:** {now} HST",
            f"- **Report created:** {now} HST",
            f"- **Source authority:** {source}",
            f"- **Resource ID:** {resource_id}",
            f"- **Official source:** {state.url}",
            f"- **Collected:** {state.current_fetch_timestamp_hst or 'Unknown'} HST",
            "- **Processing:** none; this layer preserves the readable official-product representation.",
            "- **Raw source:** retained separately in the URL-mirrored weather data tree.",
            "- **Level 0:** not used as an input.",
            "",
            "---",
            "",
            fence + "text",
            body,
            fence,
            "",
        ])
        if _write(target, content, archive_dir, now):
            outputs.append(target)
        else:
            outputs.append(target)

    return outputs
