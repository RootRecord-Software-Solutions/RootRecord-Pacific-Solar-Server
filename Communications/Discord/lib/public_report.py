# ==============================================================================
# FILE: Communications/Discord/lib/public_report.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Public Discord text for Root Record reports.

Measured lines and the public page link. Spoken transcripts stay off the post.
Internal source paths and file names stay off the message.
"""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
SITE = "https://www.rootrecord.cloud/reports"  # info: set SITE
KIND = {  # info: set KIND
    "nws_weather": "nws", "energy_report": "energy", "remaining_tasks": "remaining",  # info: kinds
    "morning_report": "morning", "midday_report": "midday", "late_report": "late",  # info: kinds
    "earthquake_report": "earthquake", "hurricane_desk": "hurricane", "kilauea_report": "kilauea",  # info: kinds
    "solar_desk": "solar", "security_desk": "security", "bandwidth_desk": "bandwidth",  # info: kinds
    "official_weather": "official", "boot_brief": "boot", "system_perf": "system",  # info: kinds
}  # info: }
AGENT = {  # info: set AGENT
    "morning": "ava", "midday": "ava", "late": "ava", "nws": "ava", "official": "ava", "boot": "ava",  # info: ava
    "solar": "bruce", "system": "bruce", "remaining": "bruce",  # info: bruce
    "energy": "carly", "earthquake": "carly", "kilauea": "carly", "hurricane": "carly",  # info: carly
    "security": "carly", "bandwidth": "carly",  # info: carly
}  # info: }
NAMES = {"ava": "Ava", "bruce": "Bruce", "carly": "Carly"}  # info: set NAMES
TITLES = {  # info: set TITLES
    "nws_weather": "NWS Hawaiʻi", "kilauea_report": "Kīlauea", "security_desk": "Security",  # info: titles
    "bandwidth_desk": "Bandwidth", "energy_report": "Energy", "remaining_tasks": "Remaining tasks",  # info: titles
    "system_perf": "System performance", "solar_desk": "Solar", "earthquake_report": "Earthquake",  # info: titles
    "hurricane_desk": "Hurricane", "morning_report": "Morning report", "midday_report": "Midday report",  # info: titles
    "late_report": "Late report", "official_weather": "Official weather", "boot_brief": "Boot brief",  # info: titles
}  # info: }
STAMP = re.compile(r"_(\d{8}T\d{4})")  # info: set STAMP
ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d+(?:\.\d+)?)%\s*\|\s*(\d+(?:\.\d+)?)\s*W\s*\|\s*(\d+(?:\.\d+)?)\s*W\s*\|")  # info: set ROW
CPU = re.compile(r"^\|\s*CPU\s*\|\s*(\d+(?:\.\d+)?)%")  # info: set CPU
RAM = re.compile(r"^\|\s*RAM\s*\|\s*(\d+(?:\.\d+)?)%")  # info: set RAM


# ====================================================
# SECTION: function persona_name
# What it does: Return Ava, Bruce, or Carly for a report key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona_name(key: str) -> str:  # info: def persona_name
    """Return Ava, Bruce, or Carly for a report key."""  # info: docstring
    return NAMES.get(AGENT.get(KIND.get(key, ""), ""), "Ava")  # info: return name


# ====================================================
# SECTION: function page_link
# What it does: Public page on www.rootrecord.cloud for this report.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def page_link(slug: str) -> str:  # info: def page_link
    """Public page on www.rootrecord.cloud for this report."""  # info: docstring
    return f"{SITE}/{slug}"  # info: return link


# ====================================================
# SECTION: function spoken_text
# What it does: Prefer the spoken transcript. Otherwise keep measured lines and drop source paths.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def spoken_text(md: str, read: str = "") -> str:  # info: def spoken_text
    """Prefer the spoken transcript. Otherwise keep measured lines and drop source paths."""  # info: docstring
    if read.strip():  # info: if read . strip
        return " ".join(read.split())  # info: return spoken
    if "\n## Spoken" in md:  # info: if spoken section
        tail = md.split("\n## Spoken", 1)[1]  # info: set tail
        lines = []  # info: set lines
        for line in tail.splitlines():  # info: for line in tail
            s = line.strip()  # info: set s
            if not s or s.startswith("_") or s.startswith("#"):  # info: if footer
                continue  # info: continue
            lines.append(s)  # info: append
        if lines:  # info: if lines
            return " ".join(" ".join(lines).split())  # info: return spoken
    kept = []  # info: set kept
    for line in md.splitlines():  # info: for line in md
        s = line.strip()  # info: set s
        if not s or s.startswith("#") or s.startswith("_") or s.startswith("|---") or s.startswith("| Device") or s.startswith("| Metric"):  # info: if skip
            continue  # info: continue
        if len(s) > 220 and not s.startswith(("-", "|")):  # info: if narrative
            continue  # info: continue
        if s.startswith("## ") or "`" in s or "Source:" in s:  # info: if internal
            continue  # info: continue
        if s.startswith("|"):  # info: if table row
            cells = [c.strip() for c in s.strip("|").split("|")]  # info: set cells
            if len(cells) >= 4 and cells[1].endswith("%"):  # info: if energy row
                kept.append(f"{cells[0]} battery {cells[1]}, solar {cells[2]}, AC out {cells[3]}.")  # info: append
            elif len(cells) >= 2:  # info: elif metric
                kept.append(f"{cells[0]}: {cells[1]}.")  # info: append
            continue  # info: continue
        kept.append(s.lstrip("- ").strip())  # info: append bullet
    return " ".join(" ".join(kept).split())  # info: return text


# ====================================================
# SECTION: function measured_text
# What it does: Public measured lines. Spoken transcripts stay out of the post.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def measured_text(md: str) -> str:  # info: def measured_text
    """Public measured lines. Spoken transcripts stay out of the post."""  # info: docstring
    clipped = md.split("\n## Spoken", 1)[0]  # info: set clipped
    return spoken_text(clipped, "")  # info: return measured


# ====================================================
# SECTION: function public_message
# What it does: Report title, measured lines, and the public page link.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def public_message(key: str, slug: str, md: str, read: str = "") -> str:  # info: def public_message
    """Report title, measured lines, and the public page link."""  # info: docstring
    del read  # info: ignore transcript
    body = measured_text(md)  # info: set body
    if not body:  # info: if not body
        return ""  # info: return empty
    title = TITLES.get(key, key.replace("_", " "))  # info: set title
    return f"{title}\n\n{body}\n\n{page_link(slug)}"  # info: return message


# ====================================================
# SECTION: function file_time
# What it does: Read the archive stamp, or the file mtime, as HST.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def file_time(path: Path) -> datetime | None:  # info: def file_time
    """Read the archive stamp, or the file mtime, as HST."""  # info: docstring
    found = STAMP.search(path.name)  # info: set found
    if found:  # info: if found
        return datetime.strptime(found.group(1), "%Y%m%dT%H%M").replace(tzinfo=HST)  # info: return stamp
    if not path.is_file():  # info: if missing
        return None  # info: return None
    return datetime.fromtimestamp(path.stat().st_mtime, HST)  # info: return mtime


# ====================================================
# SECTION: function samples
# What it does: Load report files whose time falls in the window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def samples(root: Path, key: str, start: datetime, end: datetime) -> list[tuple[datetime, str]]:  # info: def samples
    """Load report files whose time falls in the window."""  # info: docstring
    folder = root / "test-reports" / "Voice"  # info: set folder
    paths = list(folder.glob(f"{key}_*.md")) + list((folder / "Archive").glob(f"{key}_*.md"))  # info: set paths
    found = []  # info: set found
    for path in paths:  # info: for path in paths
        if path.suffix != ".md" or ".read." in path.name:  # info: if not markdown
            continue  # info: continue
        when = file_time(path)  # info: set when
        if when is None or when < start or when >= end:  # info: if outside window
            continue  # info: continue
        found.append((when, path.read_text(encoding="utf-8", errors="replace")))  # info: append
    found.sort(key=lambda row: row[0])  # info: sort
    return found  # info: return found


# ====================================================
# SECTION: function _mean
# What it does: Average a list of numbers. Return None when fewer than two exist.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _mean(values: list[float]) -> float | None:  # info: def _mean
    """Average a list of numbers. Return None when fewer than two exist."""  # info: docstring
    if len(values) < 2:  # info: if fewer than two
        return None  # info: return None
    return sum(values) / len(values)  # info: return mean


# ====================================================
# SECTION: function averages
# What it does: Average repeated measured fields. Skip a field that was sampled once.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def averages(texts: list[str]) -> list[str]:  # info: def averages
    """Average repeated measured fields. Skip a field that was sampled once."""  # info: docstring
    packs: dict[str, dict[str, list[float]]] = {}  # info: set packs
    cpu, ram = [], []  # info: set cpu , ram
    for text in texts:  # info: for text in texts
        for line in text.splitlines():  # info: for line in text
            row = ROW.match(line.strip())  # info: set row
            if row:  # info: if row
                name = row.group(1)  # info: set name
                bucket = packs.setdefault(name, {"soc": [], "solar": [], "ac": []})  # info: set bucket
                bucket["soc"].append(float(row.group(2)))  # info: append soc
                bucket["solar"].append(float(row.group(3)))  # info: append solar
                bucket["ac"].append(float(row.group(4)))  # info: append ac
            cpu_m = CPU.match(line.strip())  # info: set cpu_m
            ram_m = RAM.match(line.strip())  # info: set ram_m
            if cpu_m:  # info: if cpu
                cpu.append(float(cpu_m.group(1)))  # info: append
            if ram_m:  # info: if ram
                ram.append(float(ram_m.group(1)))  # info: append
    lines = []  # info: set lines
    for name, bucket in packs.items():  # info: for name , bucket
        parts = []  # info: set parts
        soc, solar, ac = _mean(bucket["soc"]), _mean(bucket["solar"]), _mean(bucket["ac"])  # info: set means
        if soc is not None:  # info: if soc
            parts.append(f"average charge {soc:.0f}%")  # info: append
        if solar is not None:  # info: if solar
            parts.append(f"average solar {solar:.0f} W")  # info: append
        if ac is not None:  # info: if ac
            parts.append(f"average AC out {ac:.0f} W")  # info: append
        if parts:  # info: if parts
            lines.append(f"{name}: {', '.join(parts)}.")  # info: append
    if _mean(cpu) is not None:  # info: if cpu mean
        lines.append(f"Average CPU { _mean(cpu):.0f}%.")  # info: append
    if _mean(ram) is not None:  # info: if ram mean
        lines.append(f"Average memory {_mean(ram):.0f}% used.")  # info: append
    return lines  # info: return lines


# ====================================================
# SECTION: function window_for
# What it does: Previous 8 or 24 hours ending on the current HST hour.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def window_for(hours: int, now: datetime | None = None) -> tuple[datetime, datetime]:  # info: def window_for
    """Previous 8 or 24 hours ending on the current HST hour."""  # info: docstring
    clock = (now or datetime.now(HST)).astimezone(HST).replace(minute=0, second=0, microsecond=0)  # info: set clock
    return clock - timedelta(hours=hours), clock  # info: return window


# ====================================================
# SECTION: function consolidation
# What it does: Public 8-hour or 24-hour summary for one topic. Numbers come only from reports in the window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def consolidation(key: str, slug: str, rows: list[tuple[datetime, str]], hours: int, start: datetime, end: datetime) -> str:  # info: def consolidation
    """Public 8-hour or 24-hour summary for one topic. Numbers come only from reports in the window."""  # info: docstring
    title = TITLES.get(key, key.replace("_", " "))  # info: set title
    label = "8-hour summary" if hours == 8 else "24-hour summary"  # info: set label
    span = f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')} HST"  # info: set span
    if not rows:  # info: if not rows
        body = f"{label}, {span}. No reports on file for this window."  # info: set body
    else:  # info: else
        first, last = rows[0][0], rows[-1][0]  # info: set first , last
        bits = [f"{label}, {span}.", f"{len(rows)} report{'s' if len(rows) != 1 else ''} on file, {first.strftime('%H:%M')} to {last.strftime('%H:%M')} HST."]  # info: set bits
        bits.extend(averages([text for _, text in rows]))  # info: extend averages
        latest = measured_text(rows[-1][1])  # info: set latest
        if latest:  # info: if latest
            bits.append(f"Latest: {latest}")  # info: append latest
        body = " ".join(bits)  # info: set body
    return f"{title}\n\n{body}\n\n{page_link(slug)}"  # info: return message
