#!/usr/bin/env python3
"""weather-retention.py — Weather data retention (policy signed off by Alexander 2026-09-29).

Policy source: Pacific Weather/README.md §Retention; Library 08-ideas/2026-09-29-weather-retention-and-repo.md
(the separate Weather repo is NOT approved and is not used here).

| Class                    | Where                                          | Rule                               |
| `*_current*` snapshots   | every resource folder                          | keep                               |
| dated text/HTML archives | */archive/MM-DD-YYYY/, */raw/archive/…         | keep 90 days                       |
| daily zips               | */archives/MM-DD-YYYY_Daily_Archive.zip        | keep 90 days                       |
| imagery archives         | GOES / radar / IR-loop / wwamap archive/       | keep 14 days of dated folders      |
| generated reports        | reports/*/archived/                            | keep 30 days                       |
| hurricanes               | hurricanes/                                    | keep all                           |
| daemon log               | logs/weather-poller.log                        | rotate at 10 MB x 5 (copytruncate) |
| older than the windows   | —                                              | MOVE (never delete) to             |
|                          |   2 - RootRecord-Database/Archive/Previous-Datasets/Weather-<YYYYMM>/<path under Weather/> |
| budget alarm             | —                                              | WARN Weather/ > 20 GB or free < 50 GB |

Modes: --dry-run (DEFAULT; read-only, reports counts/bytes it WOULD move) · --apply (moves; only after
Alexander reviews a dry run). Nothing is ever deleted: the 6th rotated log is moved to the archive too.
Daily zips hold text AND imagery together, so they follow the 90-day zip rule (the 14-day imagery rule
applies to unzipped dated imagery folders) — flagged in the report as an open question.

  python3 weather-retention.py                    # dry run, report to stdout + Database Logs
  python3 weather-retention.py --apply            # act (gated; job disabled by default)
  --no-save   do not write the report file · --report PATH  explicit report path
"""
from __future__ import annotations
import argparse, fcntl, json, os, re, shutil, sys
from datetime import date, datetime
from pathlib import Path

DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
WEATHER = Path(os.environ.get("WEATHER_DATA_ROOT", str(DB / "Weather")))
DATASET = WEATHER / "Hawai'i"
ARCHIVE_ROOT = Path(os.environ.get("WEATHER_RETENTION_ARCHIVE", str(DB / "Archive" / "Previous-Datasets")))
REPORT_DIR = DB / "Logs" / "Weather" / "Retention"
KEEP_TEXT_DAYS, KEEP_ZIP_DAYS, KEEP_IMAGERY_DAYS, KEEP_REPORT_DAYS = 90, 90, 14, 30
LOG_ROTATE_BYTES, LOG_KEEP = 10 * 1024 * 1024, 5
BUDGET_BYTES, MIN_FREE_BYTES = 20 * 1024**3, 50 * 1024**3
DATED = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")
ZIP = re.compile(r"^(\d{2})-(\d{2})-(\d{4})_Daily_Archive\.zip$")
IMAGERY_MARKERS = ("cdn.star.nesdis.noaa.gov", "radar.weather.gov", "/images/", "/wwamap/")
IMAGE_EXT = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}


def tree_size(p: Path) -> tuple[int, int]:
    if p.is_file():
        return 1, p.stat().st_size
    n = b = 0
    for root, _d, files in os.walk(p):
        for f in files:
            try:
                b += os.lstat(os.path.join(root, f)).st_size; n += 1
            except OSError:
                pass
    return n, b


def human(b: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024 or u == "GB":
            return f"{b:.1f} {u}" if u != "B" else f"{b} B"
        b /= 1024
    return f"{b:.1f} GB"


def is_imagery(d: Path) -> bool:
    s = str(d)
    if any(m in s for m in IMAGERY_MARKERS):
        return True
    files = [f for f in d.iterdir() if f.is_file()]
    return bool(files) and sum(f.suffix.lower() in IMAGE_EXT for f in files) * 2 >= len(files)


def dest_for(src: Path, yyyymm: str) -> Path:
    return ARCHIVE_ROOT / f"Weather-{yyyymm}" / src.relative_to(WEATHER)


def plan(today: date) -> dict:
    classes = {k: {"kept_n": 0, "kept_b": 0, "move": []} for k in
               ("current", "text_dated", "imagery_dated", "daily_zip", "reports_archived", "hurricanes", "other")}
    seen_dirs: set[Path] = set()
    oldest: list[date] = []

    def add_move(cls, path, n, b, when: date, rule_days):
        classes[cls]["move"].append({"src": str(path), "dest": str(dest_for(path, when.strftime("%Y%m"))), "files": n, "bytes": b,
                                     "age_days": (today - when).days, "rule_days": rule_days})

    for root, dirs, files in os.walk(DATASET):
        r = Path(root)
        rel = str(r.relative_to(DATASET))
        if rel == "hurricanes" or rel.startswith("hurricanes/"):
            n, b = sum(1 for _ in files), 0
            for f in files:
                try:
                    b += os.lstat(r / f).st_size
                except OSError:
                    pass
            classes["hurricanes"]["kept_n"] += n; classes["hurricanes"]["kept_b"] += b
            continue
        if rel == "logs":
            continue  # handled by log rotation
        # dated archive folders (whole folder is one unit)
        if r.name in ("archive",):
            for d in list(dirs):
                m = DATED.match(d)
                if not m:
                    continue
                dd = r / d
                when = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
                oldest.append(when)
                n, b = tree_size(dd)
                cls = "imagery_dated" if is_imagery(dd) else "text_dated"
                keep = KEEP_IMAGERY_DAYS if cls == "imagery_dated" else KEEP_TEXT_DAYS
                if (today - when).days > keep:
                    add_move(cls, dd, n, b, when, keep)
                else:
                    classes[cls]["kept_n"] += n; classes[cls]["kept_b"] += b
                dirs.remove(d); seen_dirs.add(dd)
        in_reports_archived = "/archived" in f"/{rel}" and rel.startswith("reports/")
        for f in files:
            p = r / f
            try:
                st = os.lstat(p)
            except OSError:
                continue
            if "_current" in f:
                classes["current"]["kept_n"] += 1; classes["current"]["kept_b"] += st.st_size
                continue
            m = ZIP.match(f)
            if m and r.name == "archives":
                when = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
                oldest.append(when)
                if (today - when).days > KEEP_ZIP_DAYS:
                    add_move("daily_zip", p, 1, st.st_size, when, KEEP_ZIP_DAYS)
                else:
                    classes["daily_zip"]["kept_n"] += 1; classes["daily_zip"]["kept_b"] += st.st_size
                continue
            if in_reports_archived:
                when = datetime.fromtimestamp(st.st_mtime).date()
                if (today - when).days > KEEP_REPORT_DAYS:
                    add_move("reports_archived", p, 1, st.st_size, when, KEEP_REPORT_DAYS)
                else:
                    classes["reports_archived"]["kept_n"] += 1; classes["reports_archived"]["kept_b"] += st.st_size
                continue
            classes["other"]["kept_n"] += 1; classes["other"]["kept_b"] += st.st_size

    # daemon log rotation (10 MB x 5, copytruncate so the >> writer keeps its fd)
    log = DATASET / "logs" / "weather-poller.log"
    log_b = log.stat().st_size if log.is_file() else 0
    rot = {"path": str(log), "bytes": log_b, "rotate": log_b >= LOG_ROTATE_BYTES,
           "existing_rotations": sorted(p.name for p in log.parent.glob("weather-poller.log.*")) if log.parent.is_dir() else []}
    total_n, total_b = tree_size(WEATHER) if WEATHER.exists() else (0, 0)
    du = shutil.disk_usage(WEATHER if WEATHER.exists() else DB)
    alarms = []
    if total_b > BUDGET_BYTES:
        alarms.append(f"WARN Weather/ is {human(total_b)} (> 20 GB)")
    if du.free < MIN_FREE_BYTES:
        alarms.append(f"WARN disk free {human(du.free)} (< 50 GB)")
    return {"classes": classes, "oldest_dated": min(oldest).isoformat() if oldest else None, "log": rot, "total_files": total_n, "total_bytes": total_b, "disk_free": du.free, "alarms": alarms}


def move_into(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir() and dest.exists():
        for child in list(src.iterdir()):
            move_into(child, dest / child.name)
        src.rmdir()  # now empty: all children moved
        return
    if dest.exists():
        dest = dest.with_name(dest.name + f".dup-{datetime.now():%Y%m%d%H%M%S}")
    shutil.move(str(src), str(dest))


def ensure_dataset_readme(ds_dir: Path) -> None:
    rd = ds_dir / "README.md"
    if not rd.exists():
        ds_dir.mkdir(parents=True, exist_ok=True)
        rd.write_text(f"# {ds_dir.name}\n\nWeather data older than the retention windows, MOVED here by Pacific "
                      "`Weather/scripts/weather-retention.py --apply` (never deleted). Paths mirror `2 - RootRecord-Database/Weather/`.\n"
                      "Contents are local only (git-ignored); only this README is tracked.\n", encoding="utf-8")


def apply(p: dict) -> list[str]:
    done = []
    for cls, c in p["classes"].items():
        for m in c["move"]:
            src, dest = Path(m["src"]), Path(m["dest"])
            if not src.exists():
                continue
            ensure_dataset_readme(ARCHIVE_ROOT / dest.relative_to(ARCHIVE_ROOT).parts[0])
            move_into(src, dest)
            done.append(f"moved {cls} {src} -> {dest}")
    lg = p["log"]
    if lg["rotate"]:
        log = Path(lg["path"])
        oldest = log.with_name(f"{log.name}.{LOG_KEEP}")
        if oldest.exists():
            yyyymm = datetime.fromtimestamp(oldest.stat().st_mtime).strftime("%Y%m")
            ensure_dataset_readme(ARCHIVE_ROOT / f"Weather-{yyyymm}")
            move_into(oldest, dest_for(oldest, yyyymm).with_name(f"{log.name}.{datetime.now():%Y%m%d-%H%M%S}"))
            done.append(f"moved oldest rotated log {oldest.name} to archive")
        for i in range(LOG_KEEP - 1, 0, -1):
            a = log.with_name(f"{log.name}.{i}")
            if a.exists():
                os.replace(a, log.with_name(f"{log.name}.{i + 1}"))
        shutil.copy2(log, log.with_name(f"{log.name}.1"))
        with log.open("r+b") as fh:
            fh.truncate(0)
        done.append("rotated weather-poller.log (copytruncate)")
    return done


def render(p: dict, mode: str, now: datetime, actions: list[str]) -> str:
    L = [f"# Weather retention — {mode.upper()} — {now.isoformat(timespec='seconds')} (HST)", "",
         f"Script: Pacific `Weather/scripts/weather-retention.py` ({'read-only; nothing moved' if mode == 'dry-run' else 'APPLY'}). "
         f"Dataset: `{DATASET}`. Archive target: `{ARCHIVE_ROOT}/Weather-<YYYYMM>/` (move, never delete).", "",
         "| Class | Rule | Kept files | Kept bytes | Would move (items / files) | Would move bytes |",
         "| --- | --- | ---: | ---: | ---: | ---: |"]
    rules = {"current": "keep", "text_dated": f"keep {KEEP_TEXT_DAYS} d", "imagery_dated": f"keep {KEEP_IMAGERY_DAYS} d",
             "daily_zip": f"keep {KEEP_ZIP_DAYS} d", "reports_archived": f"keep {KEEP_REPORT_DAYS} d", "hurricanes": "keep all", "other": "keep (no rule)"}
    tm_n = tm_b = 0
    for k, c in p["classes"].items():
        mn = sum(m["files"] for m in c["move"]); mb = sum(m["bytes"] for m in c["move"])
        tm_n += mn; tm_b += mb
        L.append(f"| {k} | {rules[k]} | {c['kept_n']} | {c['kept_b']} ({human(c['kept_b'])}) | {len(c['move'])} / {mn} | {mb} ({human(mb)}) |")
    L += ["", f"**Total would move:** {tm_n} files, {tm_b} bytes ({human(tm_b)}). **Would delete:** 0 (policy never deletes).",
          f"**Weather/ total:** {p['total_files']} files, {p['total_bytes']} bytes ({human(p['total_bytes'])}). **Disk free:** {human(p['disk_free'])}.",
          f"**Daemon log:** {p['log']['bytes']} bytes; rotate needed: {'yes' if p['log']['rotate'] else 'no'} (10 MB x 5); existing rotations: {p['log']['existing_rotations'] or 'none'}.",
          f"**Budget alarms:** {'; '.join(p['alarms']) if p['alarms'] else 'none (Weather/ < 20 GB, free >= 50 GB)'}.", ""]
    moves = [m for c in p["classes"].values() for m in c["move"]]
    if moves:
        L += ["## Items older than their window", ""] + [f"- `{m['src']}` ({m['files']} files, {m['bytes']} B, age {m['age_days']} d > {m['rule_days']} d) → `{m['dest']}`" for m in moves[:200]]
        if len(moves) > 200:
            L.append(f"- … {len(moves) - 200} more")
        L.append("")
    if actions:
        L += ["## Actions", ""] + [f"- {a}" for a in actions] + [""]
    L += ["## Notes", "", "- Daily zips mix text and imagery; they follow the 90-day zip rule. Whether zipped imagery should leave after 14 days is an open question for Alexander.",
          f"- Oldest dated archive folder / daily zip: {p['oldest_dated'] or 'none'} (windows: imagery {KEEP_IMAGERY_DAYS} d, text and zips {KEEP_TEXT_DAYS} d, reports {KEEP_REPORT_DAYS} d by mtime).", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="Weather retention (dry-run by default)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True, help="default: read-only report")
    g.add_argument("--apply", action="store_true", help="move data past its window (needs Alexander's review of a dry run)")
    ap.add_argument("--report"); ap.add_argument("--no-save", action="store_true"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    mode = "apply" if a.apply else "dry-run"
    if not DATASET.is_dir():
        print(f"No data: {DATASET}", file=sys.stderr); return 1
    lock = open("/tmp/weather-retention.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[skip] another weather-retention run holds the lock"); return 0
    now = datetime.now().astimezone()
    p = plan(now.date())
    actions = apply(p) if mode == "apply" else []
    text = render(p, mode, now, actions)
    print(text)
    if not a.no_save:
        out = Path(a.report) if a.report else REPORT_DIR / f"weather-retention_{mode}_{now:%Y-%m-%d_%H%M}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"[saved] {out}")
    if a.json:
        print(json.dumps({"mode": mode, "would_move_files": sum(m["files"] for c in p["classes"].values() for m in c["move"]),
                          "would_move_bytes": sum(m["bytes"] for c in p["classes"].values() for m in c["move"]), "alarms": p["alarms"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
