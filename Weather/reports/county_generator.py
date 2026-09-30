# ==============================================================================
# FILE: Weather/reports/county_generator.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Deterministic Level-1 county report generator. Level 0 is never modified."""  # info: """Deterministic Level-1 county report generator. Level 0 is never modified."""
from __future__ import annotations  # info: from __future__ import annotations
import re  # info: import re
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
import yaml  # info: import yaml
from core import hst_time  # info: from core import hst_time

ROOT = "reports"  # info: set ROOT
LEVEL0 = "0 Level Processing"  # info: set LEVEL0
LEVEL1 = "1 County Processing"  # info: set LEVEL1
LEVEL1_DIRNAME = LEVEL1  # info: set LEVEL1_DIRNAME
OFFICIAL = "Official Sources"  # info: set OFFICIAL
ARCHIVE = "archived"  # info: set ARCHIVE
CONFIG = "report_counties.yaml"  # info: set CONFIG

# ====================================================
# SECTION: function _config
# What it does:  config.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _config() -> dict[str, Any]:  # info: def _config
    path = Path(__file__).resolve().parent.parent / "config" / CONFIG  # info: set path
    with path.open(encoding="utf-8") as f:  # info: with path . open ( encoding = "utf-8"
        return yaml.safe_load(f) or {}  # info: return yaml . safe_load ( f ) or

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
# SECTION: function _write
# What it does:  write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(path: Path, content: str, archive_dir: Path, created: str) -> None:  # info: def _write
    if path.is_file():  # info: if path . is_file ( ) :
        try:  # info: try :
            old = path.read_text(encoding="utf-8", errors="replace")  # info: set old
        except OSError:  # info: except OSError :
            old = ""  # info: set old
        normalize = lambda s: re.sub(r"^- \*\*Generated:\*\* .+? HST$", "- **Generated:** <timestamp> HST", s, flags=re.M)  # info: set normalize
        if normalize(old) == normalize(content):  # info: if normalize ( old ) == normalize (
            return  # info: return
        _archive(path, archive_dir, created)  # info: call _archive
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    path.write_text(content, encoding="utf-8")  # info: path . write_text ( content , encoding =

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
# SECTION: function _matches
# What it does:  matches.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _matches(text: str, counties: dict[str, Any]) -> set[str]:  # info: def _matches
    found = set()  # info: set found
    for key, cfg in counties.items():  # info: for key , cfg in counties . items
        for alias in cfg.get("aliases", []):  # info: for alias in cfg . get ( "aliases"
            if re.search(r"(?<![A-Za-z])" + re.escape(str(alias)) + r"(?![A-Za-z])", text, re.I):  # info: if re . search ( r"(?<![A-Za-z])" + re
                found.add(key)  # info: found . add ( key )
                break  # info: break
    return found  # info: return found

# ====================================================
# SECTION: function _load_ugc_map
# What it does: Read the newest locally archived NWS Zone/County DBX without GIS libraries.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_ugc_map(base_dir: Path) -> dict[str, str]:  # info: def _load_ugc_map
    """Read the newest locally archived NWS Zone/County DBX without GIS libraries."""  # info: """Read the newest locally archived NWS Zone/County DBX without GIS libraries."""
    rows = []  # info: set rows
    for path in base_dir.rglob("*.dbx"):  # info: for path in base_dir . rglob ( "*.dbx"
        try:  # info: try :
            text = path.read_text(encoding="utf-8", errors="replace")  # info: set text
        except OSError:  # info: except OSError :
            continue  # info: continue
        for line in text.splitlines():  # info: for line in text . splitlines ( )
            parts = [p.strip() for p in line.split("|")]  # info: set parts
            if len(parts) < 7:  # info: if len ( parts ) < 7 :
                continue  # info: continue
            # NWS ZoneCounty records: STATE|ZONE|CWA|NAME|STATE_ZONE|COUNTY|FIPS|...
            if parts[0].upper() != "HI":  # info: if parts [ 0 ] . upper (
                continue  # info: continue
            zone, county, fips = parts[1], parts[5], parts[6]  # info: zone , county , fips = parts [
            if zone and county:  # info: if zone and county :
                rows.append((path.stat().st_mtime, f"HIZ{zone}", county, fips))  # info: rows . append ( ( path . stat
    rows.sort(key=lambda x: x[0])  # info: rows . sort ( key = lambda x
    mapping = {}  # info: set mapping
    for _, ugc, county, fips in rows:  # info: for _ , ugc , county , fips
        if fips:  # info: if fips :
            mapping[ugc] = fips[-3:]  # info: mapping [ ugc ] = fips [ -
    return mapping  # info: return mapping

# ====================================================
# SECTION: function _targets
# What it does:  targets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _targets(resource_id: str, body: str, cfg: dict[str, Any], ugc_map: dict[str, str] | None = None) -> tuple[set[str], str]:  # info: def _targets
    counties = {str(c["key"]): c for c in cfg.get("counties", [])}  # info: set counties
    same_to_key = {str(c.get("same", ""))[-3:]: str(c["key"]) for c in cfg.get("counties", [])}  # info: set same_to_key
    if ugc_map:  # info: if ugc_map :
        found = {same_to_key.get(ugc_map.get(code.upper(), "")[-3:]) for code in re.findall(r"\bHIZ\d{3}\b", body, re.I)}  # info: set found
        found.discard(None)  # info: found . discard ( None )
        if found:  # info: if found :
            return set(found), "NWS-zone-county-correlation"  # info: return set ( found ) , "NWS-zone-county-correlation"
    found_county_ugc = {same_to_key.get(code[-3:]) for code in re.findall(r"\bHIC\d{3}\b", body, re.I)}  # info: set found_county_ugc
    found_county_ugc.discard(None)  # info: found_county_ugc . discard ( None )
    if found_county_ugc:  # info: if found_county_ugc :
        return set(found_county_ugc), "NWS-county-UGC"  # info: return set ( found_county_ugc ) , "NWS-county-UGC"
    statewide = set(cfg.get("statewide_resource_ids", []))  # info: set statewide
    if resource_id in statewide:  # info: if resource_id in statewide :
        return set(counties), "statewide"  # info: return set ( counties ) , "statewide"
    for county, patterns in cfg.get("resource_routing", {}).get("county_patterns", {}).items():  # info: for county , patterns in cfg . get
        if any(re.search(p, resource_id, re.I) for p in patterns):  # info: if any ( re . search ( p
            return {county}, "explicit-resource"  # info: return { county } , "explicit-resource"
    found = _matches(body, counties)  # info: set found
    if found:  # info: if found :
        return found, "explicit-text"  # info: return found , "explicit-text"
    return set(), "unresolved/no-geographic-assignment"  # info: return set ( ) , "unresolved/no-geographic-assignment"

# ====================================================
# SECTION: function generate
# What it does: generate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def generate(base_dir: str) -> list[Path]:  # info: def generate
    base = Path(base_dir)  # info: set base
    root = base.parent / ROOT  # info: set root
    level0 = root / LEVEL0  # info: set level0
    level1 = root / LEVEL1  # info: set level1
    archive = level1 / ARCHIVE  # info: set archive
    level1.mkdir(parents=True, exist_ok=True)  # info: level1 . mkdir ( parents = True ,
    cfg = _config()  # info: set cfg
    ugc_map = _load_ugc_map(base)  # info: set ugc_map
    counties = {str(c["key"]): c for c in cfg.get("counties", [])}  # info: set counties
    buckets = {key: [] for key in counties}  # info: set buckets
    unresolved = []  # info: set unresolved
    source_candidates: dict[str, list[Path]] = {}  # info: set source_candidates
    official_root = root / OFFICIAL  # info: set official_root
    for official_path in sorted(official_root.glob("*/*_current.md")):  # info: for official_path in sorted ( official_root . glob
        rid = official_path.name.removesuffix("_current.md")  # info: set rid
        source_candidates.setdefault(rid, []).append(official_path)  # info: source_candidates . setdefault ( rid , [ ]
    now = hst_time.hst_now().isoformat(timespec="seconds")  # info: set now

    for path in sorted(level0.glob("*_current.md")):  # info: for path in sorted ( level0 . glob
        if path.name == "Hawaii_State_Weather_Report_current.md":  # info: if path . name == "Hawaii_State_Weather_Report_current.md" :
            continue  # info: continue
        try:  # info: try :
            raw = path.read_text(encoding="utf-8", errors="replace")  # info: set raw
        except OSError:  # info: except OSError :
            continue  # info: continue
        resource_id = path.name.removesuffix("_current.md")  # info: set resource_id
        source_m = re.search(r"^- \*\*Source:\*\* (.+)$", raw, re.M)  # info: set source_m
        title_m = re.search(r"^# (.+)$", raw, re.M)
        source = source_m.group(1).strip() if source_m else ""  # info: set source
        official_path = None  # info: set official_path
        for candidate in source_candidates.get(resource_id, []):  # info: for candidate in source_candidates . get ( resource_id
            try:  # info: try :
                candidate_text = candidate.read_text(encoding="utf-8", errors="replace")  # info: set candidate_text
            except OSError:  # info: except OSError :
                continue  # info: continue
            official_source_m = re.search(r"^- \*\*Official source:\*\* (.+)$", candidate_text, re.M)  # info: set official_source_m
            if official_source_m and source and official_source_m.group(1).strip() == source:  # info: if official_source_m and source and official_source_m . group
                official_path = candidate  # info: set official_path
                raw = candidate_text  # info: set raw
                break  # info: break
        source_layer = "Official Sources" if official_path is not None else LEVEL0  # info: set source_layer
        title = title_m.group(1).strip() if title_m else resource_id.replace("_", " ").title()  # info: set title
        body = _body(raw)  # info: set body
        targets, scope = _targets(resource_id, body, cfg, ugc_map)  # info: targets , scope = _targets ( resource_id ,
        if not targets:  # info: if not targets :
            unresolved.append((resource_id, title, source, scope, source_layer, body))  # info: unresolved . append ( ( resource_id , title
            continue  # info: continue
        for county in targets:  # info: for county in targets :
            buckets[county].append((resource_id, title, source, scope, source_layer, body))  # info: buckets [ county ] . append ( (

    outputs = []  # info: set outputs
    fence = chr(96) * 3  # info: set fence
    for key, county_cfg in counties.items():  # info: for key , county_cfg in counties . items
        name = str(county_cfg.get("display_name") or county_cfg.get("speech") or key.title())  # info: set name
        sections = sorted(buckets[key], key=lambda x: (x[1].lower(), x[0].lower()))  # info: set sections
        county_dir = level1 / key  # info: set county_dir
        county_dir.mkdir(parents=True, exist_ok=True)  # info: county_dir . mkdir ( parents = True ,

        # Every Level-1 source gets its own current/archived lifecycle.
        # This prevents the county layer from collapsing distinct products
        # into one irreversible file.
        for rid, title, source, scope, source_layer, body in sections:  # info: for rid , title , source , scope
            lines = [  # info: set lines
                f"# {title} — {name}", "",
                "> **Level 1 county report — deterministically routed from preserved official-source data.**", "",  # info: "> **Level 1 county report — deterministically routed from preserved official-source data.**" , "" ,
                f"- **Generated:** {now} HST",  # info: f" - **Generated:** { now } HST " ,
                f"- **Report created:** {now} HST",  # info: f" - **Report created:** { now } HST " ,
                f"- **County:** {name}",  # info: f" - **County:** { name } " ,
                f"- **Resource ID:** {rid}",  # info: f" - **Resource ID:** { rid } " ,
                f"- **Source:** {source or 'Report metadata'}",  # info: f" - **Source:** { source or 'Report metadata' } "
                f"- **Source layer:** {source_layer}",  # info: f" - **Source layer:** { source_layer } " ,
                f"- **County assignment:** {scope}",  # info: f" - **County assignment:** { scope } " ,
                f"- **Source level:** {source_layer}",  # info: f" - **Source level:** { source_layer } " ,
                "- **Processing:** deterministic rules only; no AI/LLM classification.",  # info: "- **Processing:** deterministic rules only; no AI/LLM classification." ,
                "- **Level 0:** untouched; its current and archived reports remain intact.",  # info: "- **Level 0:** untouched; its current and archived reports remain intact." ,
                "", "---", "", fence + "text", body, fence, ""  # info: "" , "---" , "" , fence +
            ]  # info: ]
            path = county_dir / f"{rid}_current.md"  # info: set path
            _write(path, "\n".join(lines), archive, now)  # info: call _write
            outputs.append(path)  # info: outputs . append ( path )

        # County aggregate is also its own Level-1 report with the same
        # archive lifecycle.
        lines = [  # info: set lines
            f"# {name} Weather Report", "",
            "> **Level 1 county aggregate — deterministically assembled from preserved source-layer records.**", "",  # info: "> **Level 1 county aggregate — deterministically assembled from preserved source-layer records.**" , "" ,
            f"- **Generated:** {now} HST",  # info: f" - **Generated:** { now } HST " ,
            f"- **Report created:** {now} HST",  # info: f" - **Report created:** { now } HST " ,
            f"- **County:** {name}",  # info: f" - **County:** { name } " ,
            f"- **Source level:** {LEVEL0}",  # info: f" - **Source level:** { LEVEL0 } " ,
            f"- **Current report sections:** {len(sections)}",  # info: f" - **Current report sections:** { len ( sections ) }
            "- **Processing:** deterministic rules only; no AI/LLM classification.",  # info: "- **Processing:** deterministic rules only; no AI/LLM classification." ,
            "- **Level 0:** untouched; its current and archived reports remain intact.",  # info: "- **Level 0:** untouched; its current and archived reports remain intact." ,
            "", "---", ""  # info: "" , "---" , ""
        ]  # info: ]
        for i, (rid, title, source, scope, source_layer, body) in enumerate(sections, 1):  # info: for i , ( rid , title ,
            lines += [  # info: set lines
                f"## {i}. {title}", "",
                f"- **Resource ID:** {rid}",  # info: f" - **Resource ID:** { rid } " ,
                f"- **Source:** {source or 'Report metadata'}",  # info: f" - **Source:** { source or 'Report metadata' } "
                f"- **Source layer:** {source_layer}",  # info: f" - **Source layer:** { source_layer } " ,
                f"- **County assignment:** {scope}", "",  # info: f" - **County assignment:** { scope } " , ""
                fence + "text", body, fence, "", "---", ""  # info: fence + "text" , body , fence ,
            ]  # info: ]
        aggregate_path = level1 / f"{key}_County_Weather_Report_current.md"  # info: set aggregate_path
        _write(aggregate_path, "\n".join(lines), archive, now)  # info: call _write
        outputs.append(aggregate_path)  # info: outputs . append ( aggregate_path )
    if unresolved:  # info: if unresolved :
        unresolved_dir = level1 / "unresolved"  # info: set unresolved_dir
        unresolved_dir.mkdir(parents=True, exist_ok=True)  # info: unresolved_dir . mkdir ( parents = True ,
        for rid, title, source, scope, source_layer, body in unresolved:  # info: for rid , title , source , scope
            lines = [  # info: set lines
                f"# {title} — Geographic Scope Unresolved", "",
                "> **Level 1 unresolved-source record.** This product was not assigned to a county by an authoritative geographic rule and is intentionally excluded from county reports.",  # info: "> **Level 1 unresolved-source record.** This product was not assigned to a county by an authoritative geograp
                "",  # info: "" ,
                f"- **Generated:** {now} HST",  # info: f" - **Generated:** { now } HST " ,
                f"- **Report created:** {now} HST",  # info: f" - **Report created:** { now } HST " ,
                f"- **Resource ID:** {rid}",  # info: f" - **Resource ID:** { rid } " ,
                f"- **Source:** {source or 'Level 0 report metadata'}",  # info: f" - **Source:** { source or 'Level 0 report metadata' } "
                f"- **County assignment:** {scope}",  # info: f" - **County assignment:** { scope } " ,
                "- **Processing:** deterministic rules only; no AI/LLM classification.",  # info: "- **Processing:** deterministic rules only; no AI/LLM classification." ,
                "- **Safety boundary:** not copied into any county report.",  # info: "- **Safety boundary:** not copied into any county report." ,
                "", "---", "", fence + "text", body, fence, ""  # info: "" , "---" , "" , fence +
            ]  # info: ]
            path = unresolved_dir / f"{rid}_current.md"  # info: set path
            _write(path, "\n".join(lines), archive, now)  # info: call _write
            outputs.append(path)  # info: outputs . append ( path )
    return outputs  # info: return outputs
