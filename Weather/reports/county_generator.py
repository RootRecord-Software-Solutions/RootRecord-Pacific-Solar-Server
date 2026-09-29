"""Deterministic Level-1 county report generator. Level 0 is never modified."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any
import yaml
from core import hst_time

ROOT = "reports"
LEVEL0 = "0 Level Processing"
LEVEL1 = "1 County Processing"
LEVEL1_DIRNAME = LEVEL1
OFFICIAL = "Official Sources"
ARCHIVE = "archived"
CONFIG = "report_counties.yaml"

def _config() -> dict[str, Any]:
    path = Path(__file__).resolve().parent.parent / "config" / CONFIG
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

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

def _write(path: Path, content: str, archive_dir: Path, created: str) -> None:
    if path.is_file():
        try:
            old = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            old = ""
        normalize = lambda s: re.sub(r"^- \*\*Generated:\*\* .+? HST$", "- **Generated:** <timestamp> HST", s, flags=re.M)
        if normalize(old) == normalize(content):
            return
        _archive(path, archive_dir, created)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def _body(text: str) -> str:
    fence = chr(96) * 3
    m = re.search(re.escape(fence) + r"text\n(.*?)\n" + re.escape(fence), text, re.S)
    return m.group(1).strip() if m else text.strip()

def _matches(text: str, counties: dict[str, Any]) -> set[str]:
    found = set()
    for key, cfg in counties.items():
        for alias in cfg.get("aliases", []):
            if re.search(r"(?<![A-Za-z])" + re.escape(str(alias)) + r"(?![A-Za-z])", text, re.I):
                found.add(key)
                break
    return found

def _load_ugc_map(base_dir: Path) -> dict[str, str]:
    """Read the newest locally archived NWS Zone/County DBX without GIS libraries."""
    rows = []
    for path in base_dir.rglob("*.dbx"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 7:
                continue
            # NWS ZoneCounty records: STATE|ZONE|CWA|NAME|STATE_ZONE|COUNTY|FIPS|...
            if parts[0].upper() != "HI":
                continue
            zone, county, fips = parts[1], parts[5], parts[6]
            if zone and county:
                rows.append((path.stat().st_mtime, f"HIZ{zone}", county, fips))
    rows.sort(key=lambda x: x[0])
    mapping = {}
    for _, ugc, county, fips in rows:
        if fips:
            mapping[ugc] = fips[-3:]
    return mapping

def _targets(resource_id: str, body: str, cfg: dict[str, Any], ugc_map: dict[str, str] | None = None) -> tuple[set[str], str]:
    counties = {str(c["key"]): c for c in cfg.get("counties", [])}
    same_to_key = {str(c.get("same", ""))[-3:]: str(c["key"]) for c in cfg.get("counties", [])}
    if ugc_map:
        found = {same_to_key.get(ugc_map.get(code.upper(), "")[-3:]) for code in re.findall(r"\bHIZ\d{3}\b", body, re.I)}
        found.discard(None)
        if found:
            return set(found), "NWS-zone-county-correlation"
    found_county_ugc = {same_to_key.get(code[-3:]) for code in re.findall(r"\bHIC\d{3}\b", body, re.I)}
    found_county_ugc.discard(None)
    if found_county_ugc:
        return set(found_county_ugc), "NWS-county-UGC"
    statewide = set(cfg.get("statewide_resource_ids", []))
    if resource_id in statewide:
        return set(counties), "statewide"
    for county, patterns in cfg.get("resource_routing", {}).get("county_patterns", {}).items():
        if any(re.search(p, resource_id, re.I) for p in patterns):
            return {county}, "explicit-resource"
    found = _matches(body, counties)
    if found:
        return found, "explicit-text"
    return set(), "unresolved/no-geographic-assignment"

def generate(base_dir: str) -> list[Path]:
    base = Path(base_dir)
    root = base.parent / ROOT
    level0 = root / LEVEL0
    level1 = root / LEVEL1
    archive = level1 / ARCHIVE
    level1.mkdir(parents=True, exist_ok=True)
    cfg = _config()
    ugc_map = _load_ugc_map(base)
    counties = {str(c["key"]): c for c in cfg.get("counties", [])}
    buckets = {key: [] for key in counties}
    unresolved = []
    source_candidates: dict[str, list[Path]] = {}
    official_root = root / OFFICIAL
    for official_path in sorted(official_root.glob("*/*_current.md")):
        rid = official_path.name.removesuffix("_current.md")
        source_candidates.setdefault(rid, []).append(official_path)
    now = hst_time.hst_now().isoformat(timespec="seconds")

    for path in sorted(level0.glob("*_current.md")):
        if path.name == "Hawaii_State_Weather_Report_current.md":
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        resource_id = path.name.removesuffix("_current.md")
        source_m = re.search(r"^- \*\*Source:\*\* (.+)$", raw, re.M)
        title_m = re.search(r"^# (.+)$", raw, re.M)
        source = source_m.group(1).strip() if source_m else ""
        official_path = None
        for candidate in source_candidates.get(resource_id, []):
            try:
                candidate_text = candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            official_source_m = re.search(r"^- \*\*Official source:\*\* (.+)$", candidate_text, re.M)
            if official_source_m and source and official_source_m.group(1).strip() == source:
                official_path = candidate
                raw = candidate_text
                break
        source_layer = "Official Sources" if official_path is not None else LEVEL0
        title = title_m.group(1).strip() if title_m else resource_id.replace("_", " ").title()
        body = _body(raw)
        targets, scope = _targets(resource_id, body, cfg, ugc_map)
        if not targets:
            unresolved.append((resource_id, title, source, scope, source_layer, body))
            continue
        for county in targets:
            buckets[county].append((resource_id, title, source, scope, source_layer, body))

    outputs = []
    fence = chr(96) * 3
    for key, county_cfg in counties.items():
        name = str(county_cfg.get("display_name") or county_cfg.get("speech") or key.title())
        sections = sorted(buckets[key], key=lambda x: (x[1].lower(), x[0].lower()))
        county_dir = level1 / key
        county_dir.mkdir(parents=True, exist_ok=True)

        # Every Level-1 source gets its own current/archived lifecycle.
        # This prevents the county layer from collapsing distinct products
        # into one irreversible file.
        for rid, title, source, scope, source_layer, body in sections:
            lines = [
                f"# {title} — {name}", "",
                "> **Level 1 county report — deterministically routed from preserved official-source data.**", "",
                f"- **Generated:** {now} HST",
                f"- **Report created:** {now} HST",
                f"- **County:** {name}",
                f"- **Resource ID:** {rid}",
                f"- **Source:** {source or 'Report metadata'}",
                f"- **Source layer:** {source_layer}",
                f"- **County assignment:** {scope}",
                f"- **Source level:** {source_layer}",
                "- **Processing:** deterministic rules only; no AI/LLM classification.",
                "- **Level 0:** untouched; its current and archived reports remain intact.",
                "", "---", "", fence + "text", body, fence, ""
            ]
            path = county_dir / f"{rid}_current.md"
            _write(path, "\n".join(lines), archive, now)
            outputs.append(path)

        # County aggregate is also its own Level-1 report with the same
        # archive lifecycle.
        lines = [
            f"# {name} Weather Report", "",
            "> **Level 1 county aggregate — deterministically assembled from preserved source-layer records.**", "",
            f"- **Generated:** {now} HST",
            f"- **Report created:** {now} HST",
            f"- **County:** {name}",
            f"- **Source level:** {LEVEL0}",
            f"- **Current report sections:** {len(sections)}",
            "- **Processing:** deterministic rules only; no AI/LLM classification.",
            "- **Level 0:** untouched; its current and archived reports remain intact.",
            "", "---", ""
        ]
        for i, (rid, title, source, scope, source_layer, body) in enumerate(sections, 1):
            lines += [
                f"## {i}. {title}", "",
                f"- **Resource ID:** {rid}",
                f"- **Source:** {source or 'Report metadata'}",
                f"- **Source layer:** {source_layer}",
                f"- **County assignment:** {scope}", "",
                fence + "text", body, fence, "", "---", ""
            ]
        aggregate_path = level1 / f"{key}_County_Weather_Report_current.md"
        _write(aggregate_path, "\n".join(lines), archive, now)
        outputs.append(aggregate_path)
    if unresolved:
        unresolved_dir = level1 / "unresolved"
        unresolved_dir.mkdir(parents=True, exist_ok=True)
        for rid, title, source, scope, source_layer, body in unresolved:
            lines = [
                f"# {title} — Geographic Scope Unresolved", "",
                "> **Level 1 unresolved-source record.** This product was not assigned to a county by an authoritative geographic rule and is intentionally excluded from county reports.",
                "",
                f"- **Generated:** {now} HST",
                f"- **Report created:** {now} HST",
                f"- **Resource ID:** {rid}",
                f"- **Source:** {source or 'Level 0 report metadata'}",
                f"- **County assignment:** {scope}",
                "- **Processing:** deterministic rules only; no AI/LLM classification.",
                "- **Safety boundary:** not copied into any county report.",
                "", "---", "", fence + "text", body, fence, ""
            ]
            path = unresolved_dir / f"{rid}_current.md"
            _write(path, "\n".join(lines), archive, now)
            outputs.append(path)
    return outputs
