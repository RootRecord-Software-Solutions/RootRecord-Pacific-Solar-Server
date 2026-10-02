# ==============================================================================
# compare_span.py — percent change for a spoken number against yesterday,
# last week, and last month. A period with no earlier reading is omitted.
# Averages and raw numbers both use percent. A zero baseline is omitted.
# ==============================================================================
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
LEDGER = Path(os.environ.get("RR_COMPARE_LEDGER", str(DB / "Reports" / "Comparisons" / "metrics.jsonl")))
SAMPLES = Path(os.environ.get("RR_ENERGY_SAMPLES", str(DB / "Energy" / "samples")))
HST = ZoneInfo("Pacific/Honolulu")

# label, seconds back, slack seconds
PERIODS = (
    ("yesterday", 86400, 6 * 3600),
    ("last week", 7 * 86400, 36 * 3600),
    ("last month", 30 * 86400, 3 * 86400),
)

_NAME = re.compile(r"^read-(delta2|river2pro)-(\d{8})-(\d{6})\.json$")
_index: list[tuple[str, datetime, Path]] | None = None


def _stamp(text: str) -> datetime | None:
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=HST)
    return when


def load_rows(path: Path | None = None) -> list[dict]:
    src = path or LEDGER
    rows = []
    if not src.is_file():
        return rows
    for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
            when = _stamp(str(row.get("at")))
            value = float(row["value"])
        except (ValueError, KeyError, TypeError):
            continue
        if when is None:
            continue
        rows.append({"at": when, "key": str(row.get("key") or ""), "value": value})
    return rows


def record(key: str, value: float, when: datetime, path: Path | None = None) -> None:
    dest = path or LEDGER
    dest.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": when.isoformat(timespec="seconds"), "key": key, "value": value}
    with dest.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, separators=(",", ":")) + "\n")


def nearest(rows: list[dict], key: str, target: datetime, slack: int) -> float | None:
    best = None
    best_gap = None
    window = timedelta(seconds=slack)
    for row in rows:
        if row["key"] != key:
            continue
        gap = abs(row["at"] - target)
        if gap > window:
            continue
        if best_gap is None or gap < best_gap:
            best = row["value"]
            best_gap = gap
    return best


def _energy_index() -> list[tuple[str, datetime, Path]]:
    global _index
    if _index is not None:
        return _index
    found = []
    if SAMPLES.is_dir():
        for path in SAMPLES.glob("read-*.json"):
            hit = _NAME.match(path.name)
            if not hit:
                continue
            when = datetime.strptime(hit.group(2) + hit.group(3), "%Y%m%d%H%M%S").replace(tzinfo=HST)
            found.append((hit.group(1), when, path))
    _index = found
    return found


def _sample_number(fields: dict, field: str) -> float | None:
    if field == "soc":
        raw = fields.get("soc")
        if not isinstance(raw, (int, float)):
            return None
        return float(round(raw))
    if field == "solar_w":
        raw = fields.get("solar_input_power")
        return float(raw) if isinstance(raw, (int, float)) else None
    if field == "output_w":
        parts = [fields.get("ac_output_power"), fields.get("usbc_output_power")]
        nums = [float(v) for v in parts if isinstance(v, (int, float))]
        return sum(nums) if nums else None
    return None


def energy_prior(key: str, target: datetime, slack: int) -> float | None:
    parts = key.split(".")
    if len(parts) != 3 or parts[0] != "energy":
        return None
    alias, field = parts[1], parts[2]
    best = None
    best_gap = None
    window = timedelta(seconds=slack)
    for name, when, path in _energy_index():
        if name != alias:
            continue
        gap = abs(when - target)
        if gap > window or (best_gap is not None and gap >= best_gap):
            continue
        try:
            fields = json.loads(path.read_text(encoding="utf-8")).get("fields") or {}
        except (OSError, ValueError):
            continue
        value = _sample_number(fields, field)
        if value is None:
            continue
        best = value
        best_gap = gap
    return best


def _clause(value: float, prior: float, label: str) -> str | None:
    if prior == 0:
        return None
    pct = round(100 * (value - prior) / abs(prior))
    if pct > 0:
        return f"up {pct} percent from {label}"
    if pct < 0:
        return f"down {abs(pct)} percent from {label}"
    return f"unchanged from {label}"


def sentences(key: str, value, label: str, when: datetime, rows: list[dict] | None = None, path: Path | None = None) -> list[str]:
    """Record this reading. Speak only the periods that have an earlier number."""
    try:
        current = float(value)
    except (TypeError, ValueError):
        return []
    stored = rows if rows is not None else load_rows(path)
    parts = []
    for phrase, seconds, slack in PERIODS:
        target = when - timedelta(seconds=seconds)
        prior = nearest(stored, key, target, slack)
        if prior is None:
            prior = energy_prior(key, target, slack)
        if prior is None:
            continue
        clause = _clause(current, prior, phrase)
        if clause:
            parts.append(clause)
    if rows is None:
        record(key, current, when, path)
    if not parts or not label:
        return []
    return [f"{label} {parts[0]}" + (", " + ", ".join(parts[1:]) if len(parts) > 1 else "") + "."]
