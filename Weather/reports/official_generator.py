# ==============================================================================
# FILE: Weather/reports/official_generator.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Build source-isolated mirrors of official report products.

This is NOT a processing level. It is a preservation/organization layer that
keeps official-source reports grouped by issuing source while Level 0 and
Level 1 remain processing layers.

The exact fetched source bytes remain in the URL-mirrored raw data tree.
These Markdown files are the readable official-product representation.
"""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import urlsplit  # info: from urllib . parse import urlsplit

from core import hst_time  # info: from core import hst_time
from core.manifest import Manifest  # info: from core . manifest import Manifest
from reports.generator import _extract_report_text, _is_reportable, _display_name, _load_resource_names  # info: from reports . generator import _extract_report_text , _is_reportable

ROOT = "reports"  # info: set ROOT
OFFICIAL = "Official Sources"  # info: set OFFICIAL
LEVEL0 = "0 Level Processing"  # info: set LEVEL0
ARCHIVE = "archived"  # info: set ARCHIVE


# ====================================================
# SECTION: function _source_name
# What it does:  source name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _source_name(url: str) -> str:  # info: def _source_name
    normalized = str(url or "").strip()  # info: set normalized
    if normalized.startswith("/"):  # info: if normalized . startswith ( "/" ) :
        normalized = "https://www.weather.gov" + normalized  # info: set normalized
    parsed = urlsplit(normalized)  # info: set parsed
    host = parsed.netloc.lower()  # info: set host
    if host in {"api.weather.gov", "www.weather.gov", "forecast.weather.gov"}:  # info: if host in { "api.weather.gov" , "www.weather.gov" ,
        return "NWS-HFO"  # info: return "NWS-HFO"
    if host in {"www.nhc.noaa.gov", "nhc.noaa.gov"}:  # info: if host in { "www.nhc.noaa.gov" , "nhc.noaa.gov" }
        return "NHC"  # info: return "NHC"
    if host in {"www.noaa.gov", "noaa.gov"}:  # info: if host in { "www.noaa.gov" , "noaa.gov" }
        return "NOAA"  # info: return "NOAA"
    if "gml.noaa.gov" in host:  # info: if "gml.noaa.gov" in host :
        return "NOAA-GML"  # info: return "NOAA-GML"
    if "nesdis.noaa.gov" in host:  # info: if "nesdis.noaa.gov" in host :
        return "NOAA-NESDIS"  # info: return "NOAA-NESDIS"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", host or "unknown-source")  # info: return re . sub ( r"[^A-Za-z0-9._-]+" , "_"


# ====================================================
# SECTION: function _created
# What it does:  created.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _created(path: Path) -> str | None:  # info: def _created
    try:  # info: try :
        text = path.read_text(encoding="utf-8", errors="replace")  # info: set text
    except OSError:  # info: except OSError :
        return None  # info: return None
    m = re.search(r"^- \*\*Report created:\*\* (.+?) HST$", text, re.M)  # info: set m
    return m.group(1).strip() if m else None  # info: return m . group ( 1 ) .


# ====================================================
# SECTION: function _archive
# What it does:  archive.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _archive(path: Path, archive_dir: Path, fallback: str) -> None:  # info: def _archive
    if not path.is_file():  # info: if not path . is_file ( ) :
        return  # info: return
    stamp = re.sub(r"[^0-9A-Za-z:+-]", "-", _created(path) or fallback).strip("-")  # info: set stamp
    stem = path.name.removesuffix("_current.md")  # info: set stem
    target = archive_dir / f"{stem}_{stamp}.md"  # info: set target
    n = 2  # info: set n
    while target.exists():  # info: while target . exists ( ) :
        target = archive_dir / f"{stem}_{stamp}_{n}.md"  # info: set target
        n += 1  # info: set n
    archive_dir.mkdir(parents=True, exist_ok=True)  # info: archive_dir . mkdir ( parents = True ,
    path.replace(target)  # info: path . replace ( target )


# ====================================================
# SECTION: function _normalize_for_compare
# What it does:  normalize for compare.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _normalize_for_compare(text: str) -> str:  # info: def _normalize_for_compare
    return re.sub(  # info: return re . sub (
        r"^- \*\*Generated:\*\* .+? HST$",  # info: r"^- \*\*Generated:\*\* .+? HST$" ,
        "- **Generated:** <timestamp> HST",  # info: "- **Generated:** <timestamp> HST" ,
        text,  # info: text ,
        flags=re.M,  # info: set flags
    )  # info: )


# ====================================================
# SECTION: function _write
# What it does:  write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(path: Path, content: str, archive_dir: Path, created: str) -> bool:  # info: def _write
    if path.is_file():  # info: if path . is_file ( ) :
        try:  # info: try :
            old = path.read_text(encoding="utf-8", errors="replace")  # info: set old
        except OSError:  # info: except OSError :
            old = ""  # info: set old
        if _normalize_for_compare(old) == _normalize_for_compare(content):  # info: if _normalize_for_compare ( old ) == _normalize_for_compare (
            return False  # info: return False
        _archive(path, archive_dir, created)  # info: call _archive
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    path.write_text(content, encoding="utf-8")  # info: path . write_text ( content , encoding =
    return True  # info: return True


# ====================================================
# SECTION: function _body
# What it does:  body.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _body(text: str) -> str:  # info: def _body
    fence = chr(96) * 3  # info: set fence
    m = re.search(re.escape(fence) + r"text\n(.*?)\n" + re.escape(fence), text, re.S)  # info: set m
    return m.group(1).strip() if m else text.strip()  # info: return m . group ( 1 ) .


# ====================================================
# SECTION: function generate
# What it does: Generate source-isolated official reports directly from collected sources. This layer deliberately does not read Level 0. That prevents a processed report from becoming the suppose
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def generate(base_dir: str) -> list[Path]:  # info: def generate
    """Generate source-isolated official reports directly from collected sources.

    This layer deliberately does not read Level 0. That prevents a processed
    report from becoming the supposed source of an official-source record.
    """
    base = Path(base_dir)  # info: set base
    reports_root = base.parent / ROOT  # info: set reports_root
    official_root = reports_root / OFFICIAL  # info: set official_root
    now = hst_time.hst_now().isoformat(timespec="seconds")  # info: set now
    manifest = Manifest(base_dir).load()  # info: set manifest
    names = _load_resource_names()  # info: set names
    outputs: list[Path] = []  # info: set outputs

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

        source = _source_name(state.url)  # info: set source
        title = _display_name(resource_id, names)  # info: set title
        source_dir = official_root / source  # info: set source_dir
        archive_dir = source_dir / ARCHIVE  # info: set archive_dir
        target = source_dir / f"{resource_id}_current.md"  # info: set target
        fence = chr(96) * 3  # info: set fence
        content = "\n".join([  # info: set content
            f"# {title}",
            "",  # info: "" ,
            "> **Official-source report mirror.** This record is derived directly from the collected official source, not from Level 0 or another processing layer.",  # info: "> **Official-source report mirror.** This record is derived directly from the collected official source, not 
            "",  # info: "" ,
            f"- **Generated:** {now} HST",  # info: f" - **Generated:** { now } HST " ,
            f"- **Report created:** {now} HST",  # info: f" - **Report created:** { now } HST " ,
            f"- **Source authority:** {source}",  # info: f" - **Source authority:** { source } " ,
            f"- **Resource ID:** {resource_id}",  # info: f" - **Resource ID:** { resource_id } " ,
            f"- **Official source:** {state.url}",  # info: f" - **Official source:** { state . url } "
            f"- **Collected:** {state.current_fetch_timestamp_hst or 'Unknown'} HST",  # info: f" - **Collected:** { state . current_fetch_timestamp_hst or 'Unknown'
            "- **Processing:** none; this layer preserves the readable official-product representation.",  # info: "- **Processing:** none; this layer preserves the readable official-product representation." ,
            "- **Raw source:** retained separately in the URL-mirrored weather data tree.",  # info: "- **Raw source:** retained separately in the URL-mirrored weather data tree." ,
            "- **Level 0:** not used as an input.",  # info: "- **Level 0:** not used as an input." ,
            "",  # info: "" ,
            "---",  # info: "---" ,
            "",  # info: "" ,
            fence + "text",  # info: fence + "text" ,
            body,  # info: body ,
            fence,  # info: fence ,
            "",  # info: "" ,
        ])  # info: ] )
        if _write(target, content, archive_dir, now):  # info: if _write ( target , content , archive_dir
            outputs.append(target)  # info: outputs . append ( target )
        else:  # info: else :
            outputs.append(target)  # info: outputs . append ( target )

    return outputs  # info: return outputs
