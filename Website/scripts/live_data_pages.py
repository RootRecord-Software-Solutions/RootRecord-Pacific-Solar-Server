#!/usr/bin/env python3
"""Build live-data page JSON from files this system already writes.

  python3 live_data_pages.py

Power reads Energy watts and soc last files. Weather reads the Hawaiʻi state
report header. Kīlauea reads Geology Volcanoes/kilauea-last.json.
Missing numbers are omitted. Chat, packs, day board, Minecraft, and context
are not built here.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
OUT = DATABASE / "Website" / "pages"
ENERGY = DATABASE / "Energy"
WEATHER_REPORT = DATABASE / "Weather" / "Hawai'i" / "reports" / "0 Level Processing" / "Hawaii_State_Weather_Report_current.md"
KILAUEA = DATABASE / "Geology" / "Volcanoes" / "kilauea-last.json"
HST = ZoneInfo("Pacific/Honolulu")
POWER_FIELDS = (
    "solar_input_power",
    "ac_output_power",
    "ac_input_power",
    "usbc_output_power",
    "at",
    "source",
    "charge_source",
)


def _now_line() -> str:
    now = datetime.now(HST)
    return now.strftime("%A, %B ") + str(now.day) + now.strftime(", %Y · %H:%M Hawaiian Standard Time")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _pick(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in fields:
        if key in row and row[key] is not None:
            out[key] = row[key]
    return out


def build_power() -> dict[str, Any]:
    devices: dict[str, Any] = {}
    for name in ("delta2", "river2pro"):
        watts = _pick(_read_json(ENERGY / "watts" / f"{name}-last.json"), POWER_FIELDS)
        soc = _pick(_read_json(ENERGY / "soc" / f"{name}-last.json"), ("soc", "at", "source"))
        device: dict[str, Any] = {}
        if watts:
            device["watts"] = watts
        if soc:
            device["soc"] = soc
        if device:
            devices[name] = device
    page: dict[str, Any] = {
        "resource": "power",
        "title": "Power / solar",
        "as_of": _now_line(),
    }
    if devices:
        page["devices"] = devices
    return page


def build_weather() -> dict[str, Any]:
    page: dict[str, Any] = {
        "resource": "weather",
        "title": "Weather",
        "as_of": _now_line(),
    }
    if not WEATHER_REPORT.is_file():
        return page
    text = WEATHER_REPORT.read_text(encoding="utf-8", errors="replace")
    generated = re.search(r"^\- \*\*Generated:\*\* (.+)$", text, re.M)
    sections = re.search(r"^\- \*\*Current report sections:\*\* (\d+)$", text, re.M)
    report: dict[str, Any] = {"file": WEATHER_REPORT.name}
    if generated:
        report["generated"] = generated.group(1).strip()
    if sections:
        report["sections"] = int(sections.group(1))
    page["report"] = report
    return page


def build_kilauea() -> dict[str, Any]:
    raw = _read_json(KILAUEA)
    page: dict[str, Any] = {
        "resource": "kilauea",
        "title": "Kīlauea",
        "as_of": _now_line(),
    }
    if not raw:
        return page
    kept = _pick(raw, ("at", "alert_level", "color_code", "headline", "erupting", "status_sent_utc"))
    if kept:
        page["status"] = kept
    return page


def build_all() -> dict[str, Any]:
    return {
        "power": build_power(),
        "weather": build_weather(),
        "kilauea": build_kilauea(),
    }


def write_all() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, page in build_all().items():
        path = OUT / f"{name}.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(page, indent=2), encoding="utf-8")
        tmp.replace(path)
        written.append(path)
    return written


def main() -> int:
    paths = write_all()
    print(f"live-data {len(paths)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
