#!/usr/bin/env python3
# ==============================================================================
# voice_timing_report.py — documentation of how long voice desks take (stdlib).
# In : Database/Logs/Automations/automations_current.log + Archive/
#      jobs.py for the live minute list
# Out: Library Documentation/01-Operations/voice-timing.md
# No model. Sections follow Documenter HANDOFF-TEMPLATE.md.
# ==============================================================================
from __future__ import annotations

import os
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
ECO = Path(os.environ.get("RR_ECOSYSTEM_ROOT", "/home/rootrecord/RootRecord-Ecosystem"))
DB = Path(os.environ.get("RR_DATABASE_ROOT", str(ECO / "2 - RootRecord-Database")))
PACIFIC = Path(os.environ.get(
    "RR_PACIFIC_ROOT",
    str(ECO / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server"),
))
LOG_DIR = Path(os.environ.get("RR_AUTOMATIONS_LOG_DIR", str(DB / "Logs" / "Automations")))
JOBS = Path(os.environ.get("RR_JOBS_FILE", str(PACIFIC / "Automations" / "scripts" / "jobs.py")))
OUT = Path(os.environ.get(
    "RR_VOICE_TIMING_OUT",
    str(ECO / "5 - RootRecord-Library" / "Documentation" / "01-Operations" / "voice-timing.md"),
))
TEMPLATE = ECO / "5 - RootRecord-Library" / "Agent Context" / "Documenter-Agent-Context" / "HANDOFF-TEMPLATE.md"

# Desks that render together before each radio snapshot.
STACK = (
    "voice_system_perf",
    "voice_nws_weather",
    "voice_energy_report",
    "voice_remaining_tasks",
    "voice_earthquake_report",
    "voice_kilauea_report",
    "voice_solar_desk",
    "voice_security_desk",
    "voice_bandwidth_desk",
    "voice_current_report",
)
LABELS = {
    "voice_system_perf": "System",
    "voice_nws_weather": "NWS",
    "voice_energy_report": "Energy",
    "voice_remaining_tasks": "Remaining tasks",
    "voice_earthquake_report": "Earthquakes",
    "voice_kilauea_report": "Kīlauea",
    "voice_solar_desk": "Solar",
    "voice_security_desk": "Security",
    "voice_bandwidth_desk": "Bandwidth",
    "voice_current_report": "Current",
    "voice_hurricane_desk": "Hurricane",
    "voice_morning_report": "Morning roll-up",
    "voice_midday_report": "Midday roll-up",
    "voice_late_report": "Late roll-up",
    "voice_late_final_report": "Late final",
    "radio_news_update": "News",
    "voice_hourly_chime": "Chime",
}
LINE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})job:(\S+) (RUN|\|)"
)
SCHED = re.compile(
    r'"id": "(voice_[a-z0-9_]+|radio_news_update)".{0,2500}?'
    r'(?:"only_at_minutes": (\[[0-9, ]+\])|"at_times": (\[[^\]]+\]))',
    re.S,
)
LEAD_SEC = (29 * 60 + 59) - (12 * 60)


def log_files(root: Path) -> list[Path]:
    files = []
    current = root / "automations_current.log"
    archive = root / "Archive"
    if archive.is_dir():
        files.extend(sorted(archive.glob("automations_*.log")))
    if current.is_file():
        files.append(current)
    return files


def durations(files: list[Path]) -> dict[str, list[float]]:
    """Wall seconds from a RUN line to the next result line for that job."""
    open_runs: dict[str, datetime] = {}
    out: dict[str, list[float]] = {}
    for path in files:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = LINE.match(line)
            if not match:
                continue
            stamp = datetime.fromisoformat(match.group(1))
            job = match.group(2)
            if job not in LABELS:
                continue
            if match.group(3) == "RUN":
                open_runs[job] = stamp
                continue
            start = open_runs.pop(job, None)
            if start is None:
                continue
            wall = (stamp - start).total_seconds()
            if wall < 0:
                continue
            out.setdefault(job, []).append(wall)
    return out


def schedule(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for match in SCHED.finditer(text):
        job = match.group(1)
        found[job] = match.group(2) or match.group(3) or ""
    return found


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((p / 100) * (len(ordered) - 1))))
    return ordered[index]


def seconds(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.0f}s"


def stack_sum(rows: dict[str, list[float]], pick) -> float | None:
    parts = []
    for job in STACK:
        values = rows.get(job) or []
        if not values:
            return None
        parts.append(pick(values))
    return sum(parts)


def render(rows: dict[str, list[float]], when: datetime, files: list[Path], sched: dict[str, str]) -> str:
    total = sum(len(v) for v in rows.values())
    med = stack_sum(rows, statistics.median)
    avg = stack_sum(rows, statistics.mean)
    p90 = stack_sum(rows, lambda values: percentile(values, 90))
    clock = when.astimezone(HST).strftime("%Y-%m-%d %H:%M HST")
    facts = [
        "The station locks the playlist at HH:29:59 and HH:59:59, then chimes on the hour and the half hour.",
        "A file that arrives after that lock waits for the next cycle.",
        "The measured desks share one poller thread and one voice lock, so a set runs one after another.",
        "The lead from :12:00 to the :29:59 lock is 17 minutes 59 seconds. :42 has the same lead before :59:59.",
    ]
    if med is not None and avg is not None and p90 is not None:
        facts.append(
            f"The ten-desk set sums to median {seconds(med)}, average {seconds(avg)}, and p90 {seconds(p90)}."
        )
        if p90 <= LEAD_SEC:
            facts.append("That p90 sum fits inside the lead.")
        else:
            facts.append("That p90 sum is longer than the lead.")
    else:
        facts.append("The ten-desk set is incomplete in this log, so no stack sum is stated.")
    facts.append("The schedule table is copied from jobs.py.")
    order = list(STACK) + [job for job in LABELS if job not in STACK]

    lines = [
        "# Voice timing",
        "",
        f"**Generated:** {clock}  ",
        "**Source:** automations log, job wall time from RUN to the result line  ",
        "**Model:** none  ",
        f"**Template:** `{TEMPLATE.relative_to(ECO) if TEMPLATE.is_file() else 'HANDOFF-TEMPLATE.md'}`  ",
        "",
        f"## Handoff — {clock} — voice_timing_report → Library",
        "",
        "### Confirmed facts",
    ]
    lines.extend(f"- {fact}" for fact in facts)
    lines += [
        "",
        "### Pages updated",
        "",
        "- `Documentation/01-Operations/voice-timing.md` (this page)",
        "",
        "### Evidence",
        "",
        f"{total} finished runs in {len(files)} log files.",
        "",
        "| Job | Scheduled |",
        "| --- | --- |",
    ]
    for job in order:
        lines.append(f"| `{job}` | {sched.get(job) or '—'} |")
    lines += [
        "",
        "| Report | Job | Runs | Median | Average | p90 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for job in order:
        values = rows.get(job) or []
        if not values:
            lines.append(f"| {LABELS[job]} | `{job}` | 0 | — | — | — |")
            continue
        lines.append(
            f"| {LABELS[job]} | `{job}` | {len(values)} | {seconds(statistics.median(values))} | "
            f"{seconds(statistics.mean(values))} | {seconds(percentile(values, 90))} |"
        )
    lines += [
        "",
        "p90 is the nearest rank in that desk's own runs. The stack p90 is the sum of those ranks, not one measured batch.",
        "",
        "### Still open / unresolved",
        "",
        "- A slow energy camera look and a slow current report do not always land in the same pass. The summed p90 is the cautious figure.",
        "- Daypart roll-ups are written only inside their Hawaii window, so the 09:00, 12:00, and 21:00 cycles still play the previous roll-up.",
        "",
        "### Explicitly historical (do not treat as current)",
        "",
        "- Any earlier sentence that quotes one log pass, including the 299-run note from 2026-10-01 23:48 HST, is that pass. This page is the current measurement.",
        "",
        "### Next recommended action",
        "",
    ]
    if p90 is not None and p90 > LEAD_SEC:
        lines.append("- Move the :12 and :42 start earlier. The summed p90 no longer fits the lead.")
    else:
        lines.append("- Keep the :12 and :42 start while the summed p90 still fits the lead.")
    lines.append("")
    return "\n".join(lines)


def body(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("**Generated:**"))


def main() -> int:
    files = log_files(LOG_DIR)
    rows = durations(files)
    sched = schedule(JOBS.read_text(encoding="utf-8")) if JOBS.is_file() else {}
    text = render(rows, datetime.now(HST), files, sched)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.is_file() and body(OUT.read_text(encoding="utf-8", errors="replace")) == body(text):
        print(f"[ok] voice-timing unchanged ({sum(len(v) for v in rows.values())} runs)")
        return 0
    tmp = OUT.with_suffix(".md.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, OUT)
    print(f"[ok] voice-timing written ({sum(len(v) for v in rows.values())} runs): {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
