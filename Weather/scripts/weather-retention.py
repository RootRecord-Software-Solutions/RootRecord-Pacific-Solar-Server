# ==============================================================================
# FILE: Weather/scripts/weather-retention.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""weather-retention.py — Weather data retention (policy signed off by Alexander 2026-09-29).

Policy source: Pacific Weather/README.md §Retention; Library 08-Ideas/2026-09-29-weather-retention-and-repo.md
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
from __future__ import annotations  # info: from __future__ import annotations
import argparse, fcntl, json, os, re, shutil, sys  # info: import argparse , fcntl , json , os
from datetime import date, datetime  # info: from datetime import date , datetime
from pathlib import Path  # info: from pathlib import Path

DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DB
WEATHER = Path(os.environ.get("WEATHER_DATA_ROOT", str(DB / "Weather")))  # info: set WEATHER
DATASET = WEATHER / "Hawai'i"  # info: set DATASET
ARCHIVE_ROOT = Path(os.environ.get("WEATHER_RETENTION_ARCHIVE", str(DB / "Archive" / "Previous-Datasets")))  # info: set ARCHIVE_ROOT
REPORT_DIR = DB / "Logs" / "Weather" / "Retention"  # info: set REPORT_DIR
KEEP_TEXT_DAYS, KEEP_ZIP_DAYS, KEEP_IMAGERY_DAYS, KEEP_REPORT_DAYS = 90, 90, 14, 30  # info: KEEP_TEXT_DAYS , KEEP_ZIP_DAYS , KEEP_IMAGERY_DAYS , KEEP_REPORT_DAYS =
LOG_ROTATE_BYTES, LOG_KEEP = 10 * 1024 * 1024, 5  # info: LOG_ROTATE_BYTES , LOG_KEEP = 10 * 1024 *
BUDGET_BYTES, MIN_FREE_BYTES = 20 * 1024**3, 50 * 1024**3  # info: BUDGET_BYTES , MIN_FREE_BYTES = 20 * 1024 **
DATED = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")  # info: set DATED
ZIP = re.compile(r"^(\d{2})-(\d{2})-(\d{4})_Daily_Archive\.zip$")  # info: set ZIP
IMAGERY_MARKERS = ("cdn.star.nesdis.noaa.gov", "radar.weather.gov", "/images/", "/wwamap/")  # info: set IMAGERY_MARKERS
IMAGE_EXT = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}  # info: set IMAGE_EXT


# ====================================================
# SECTION: function tree_size
# What it does: tree size.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tree_size(p: Path) -> tuple[int, int]:  # info: def tree_size
    if p.is_file():  # info: if p . is_file ( ) :
        return 1, p.stat().st_size  # info: return 1 , p . stat ( )
    n = b = 0  # info: set n
    for root, _d, files in os.walk(p):  # info: for root , _d , files in os
        for f in files:  # info: for f in files :
            try:  # info: try :
                b += os.lstat(os.path.join(root, f)).st_size; n += 1  # info: set b
            except OSError:  # info: except OSError :
                pass  # info: pass
    return n, b  # info: return n , b


# ====================================================
# SECTION: function human
# What it does: human.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def human(b: int) -> str:  # info: def human
    for u in ("B", "KB", "MB", "GB"):  # info: for u in ( "B" , "KB" ,
        if b < 1024 or u == "GB":  # info: if b < 1024 or u == "GB"
            return f"{b:.1f} {u}" if u != "B" else f"{b} B"  # info: return f" { b : .1f }
        b /= 1024  # info: b /= 1024
    return f"{b:.1f} GB"  # info: return f" { b : .1f } GB


# ====================================================
# SECTION: function is_imagery
# What it does: is imagery.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_imagery(d: Path) -> bool:  # info: def is_imagery
    s = str(d)  # info: set s
    if any(m in s for m in IMAGERY_MARKERS):  # info: if any ( m in s for m
        return True  # info: return True
    files = [f for f in d.iterdir() if f.is_file()]  # info: set files
    return bool(files) and sum(f.suffix.lower() in IMAGE_EXT for f in files) * 2 >= len(files)  # info: return bool ( files ) and sum (


# ====================================================
# SECTION: function dest_for
# What it does: dest for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def dest_for(src: Path, yyyymm: str) -> Path:  # info: def dest_for
    return ARCHIVE_ROOT / f"Weather-{yyyymm}" / src.relative_to(WEATHER)  # info: return ARCHIVE_ROOT / f" Weather- { yyyymm }


# ====================================================
# SECTION: function plan
# What it does: plan.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def plan(today: date) -> dict:  # info: def plan
    classes = {k: {"kept_n": 0, "kept_b": 0, "move": []} for k in  # info: set classes
               ("current", "text_dated", "imagery_dated", "daily_zip", "reports_archived", "hurricanes", "other")}  # info: call (
    seen_dirs: set[Path] = set()  # info: set seen_dirs
    oldest: list[date] = []  # info: set oldest

    def add_move(cls, path, n, b, when: date, rule_days):  # info: def add_move
        classes[cls]["move"].append({"src": str(path), "dest": str(dest_for(path, when.strftime("%Y%m"))), "files": n, "bytes": b,  # info: classes [ cls ] [ "move" ] .
                                     "age_days": (today - when).days, "rule_days": rule_days})  # info: call "age_days"

    for root, dirs, files in os.walk(DATASET):  # info: for root , dirs , files in os
        r = Path(root)  # info: set r
        rel = str(r.relative_to(DATASET))  # info: set rel
        if rel == "hurricanes" or rel.startswith("hurricanes/"):  # info: if rel == "hurricanes" or rel . startswith
            n, b = sum(1 for _ in files), 0  # info: n , b = sum ( 1 for
            for f in files:  # info: for f in files :
                try:  # info: try :
                    b += os.lstat(r / f).st_size  # info: set b
                except OSError:  # info: except OSError :
                    pass  # info: pass
            classes["hurricanes"]["kept_n"] += n; classes["hurricanes"]["kept_b"] += b  # info: classes [ "hurricanes" ] [ "kept_n" ] +=
            continue  # info: continue
        if rel == "logs":  # info: if rel == "logs" :
            continue  # handled by log rotation
        # dated archive folders (whole folder is one unit)
        if r.name in ("archive",):  # info: if r . name in ( "archive" ,
            for d in list(dirs):  # info: for d in list ( dirs ) :
                m = DATED.match(d)  # info: set m
                if not m:  # info: if not m :
                    continue  # info: continue
                dd = r / d  # info: set dd
                when = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))  # info: set when
                oldest.append(when)  # info: oldest . append ( when )
                n, b = tree_size(dd)  # info: n , b = tree_size ( dd )
                cls = "imagery_dated" if is_imagery(dd) else "text_dated"  # info: set cls
                keep = KEEP_IMAGERY_DAYS if cls == "imagery_dated" else KEEP_TEXT_DAYS  # info: set keep
                if (today - when).days > keep:  # info: if ( today - when ) . days
                    add_move(cls, dd, n, b, when, keep)  # info: call add_move
                else:  # info: else :
                    classes[cls]["kept_n"] += n; classes[cls]["kept_b"] += b  # info: classes [ cls ] [ "kept_n" ] +=
                dirs.remove(d); seen_dirs.add(dd)  # info: dirs . remove ( d ) ; seen_dirs
        in_reports_archived = "/archived" in f"/{rel}" and rel.startswith("reports/")  # info: set in_reports_archived
        for f in files:  # info: for f in files :
            p = r / f  # info: set p
            try:  # info: try :
                st = os.lstat(p)  # info: set st
            except OSError:  # info: except OSError :
                continue  # info: continue
            if "_current" in f:  # info: if "_current" in f :
                classes["current"]["kept_n"] += 1; classes["current"]["kept_b"] += st.st_size  # info: classes [ "current" ] [ "kept_n" ] +=
                continue  # info: continue
            m = ZIP.match(f)  # info: set m
            if m and r.name == "archives":  # info: if m and r . name == "archives"
                when = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))  # info: set when
                oldest.append(when)  # info: oldest . append ( when )
                if (today - when).days > KEEP_ZIP_DAYS:  # info: if ( today - when ) . days
                    add_move("daily_zip", p, 1, st.st_size, when, KEEP_ZIP_DAYS)  # info: call add_move
                else:  # info: else :
                    classes["daily_zip"]["kept_n"] += 1; classes["daily_zip"]["kept_b"] += st.st_size  # info: classes [ "daily_zip" ] [ "kept_n" ] +=
                continue  # info: continue
            if in_reports_archived:  # info: if in_reports_archived :
                when = datetime.fromtimestamp(st.st_mtime).date()  # info: set when
                if (today - when).days > KEEP_REPORT_DAYS:  # info: if ( today - when ) . days
                    add_move("reports_archived", p, 1, st.st_size, when, KEEP_REPORT_DAYS)  # info: call add_move
                else:  # info: else :
                    classes["reports_archived"]["kept_n"] += 1; classes["reports_archived"]["kept_b"] += st.st_size  # info: classes [ "reports_archived" ] [ "kept_n" ] +=
                continue  # info: continue
            classes["other"]["kept_n"] += 1; classes["other"]["kept_b"] += st.st_size  # info: classes [ "other" ] [ "kept_n" ] +=

    # daemon log rotation (10 MB x 5, copytruncate so the >> writer keeps its fd)
    log = DATASET / "logs" / "weather-poller.log"  # info: set log
    log_b = log.stat().st_size if log.is_file() else 0  # info: set log_b
    rot = {"path": str(log), "bytes": log_b, "rotate": log_b >= LOG_ROTATE_BYTES,  # info: set rot
           "existing_rotations": sorted(p.name for p in log.parent.glob("weather-poller.log.*")) if log.parent.is_dir() else []}  # info: "existing_rotations" : sorted ( p . name for
    total_n, total_b = tree_size(WEATHER) if WEATHER.exists() else (0, 0)  # info: total_n , total_b = tree_size ( WEATHER )
    du = shutil.disk_usage(WEATHER if WEATHER.exists() else DB)  # info: set du
    alarms = []  # info: set alarms
    if total_b > BUDGET_BYTES:  # info: if total_b > BUDGET_BYTES :
        alarms.append(f"WARN Weather/ is {human(total_b)} (> 20 GB)")  # info: alarms . append ( f" WARN Weather/ is { human
    if du.free < MIN_FREE_BYTES:  # info: if du . free < MIN_FREE_BYTES :
        alarms.append(f"WARN disk free {human(du.free)} (< 50 GB)")  # info: alarms . append ( f" WARN disk free { human
    return {"classes": classes, "oldest_dated": min(oldest).isoformat() if oldest else None, "log": rot, "total_files": total_n, "total_bytes": total_b, "disk_free": du.free, "alarms": alarms}  # info: return { "classes" : classes , "oldest_dated" :


# ====================================================
# SECTION: function move_into
# What it does: move into.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def move_into(src: Path, dest: Path) -> None:  # info: def move_into
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir ( parents =
    if src.is_dir() and dest.exists():  # info: if src . is_dir ( ) and dest
        for child in list(src.iterdir()):  # info: for child in list ( src . iterdir
            move_into(child, dest / child.name)  # info: call move_into
        src.rmdir()  # now empty: all children moved
        return  # info: return
    if dest.exists():  # info: if dest . exists ( ) :
        dest = dest.with_name(dest.name + f".dup-{datetime.now():%Y%m%d%H%M%S}")  # info: set dest
    shutil.move(str(src), str(dest))  # info: shutil . move ( str ( src )


# ====================================================
# SECTION: function ensure_dataset_readme
# What it does: ensure dataset readme.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_dataset_readme(ds_dir: Path) -> None:  # info: def ensure_dataset_readme
    rd = ds_dir / "README.md"  # info: set rd
    if not rd.exists():  # info: if not rd . exists ( ) :
        ds_dir.mkdir(parents=True, exist_ok=True)  # info: ds_dir . mkdir ( parents = True ,
        rd.write_text(f"# {ds_dir.name}\n\nWeather data older than the retention windows, MOVED here by Pacific "
                      "`Weather/scripts/weather-retention.py --apply` (never deleted). Paths mirror `2 - RootRecord-Database/Weather/`.\n"  # info: "`Weather/scripts/weather-retention.py --apply` (never deleted). Paths mirror `2 - RootRecord-Database/Weather
                      "Contents are local only (git-ignored); only this README is tracked.\n", encoding="utf-8")  # info: "Contents are local only (git-ignored); only this README is tracked.\n" , encoding = "utf-8" )


# ====================================================
# SECTION: function apply
# What it does: apply.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply(p: dict) -> list[str]:  # info: def apply
    done = []  # info: set done
    for cls, c in p["classes"].items():  # info: for cls , c in p [ "classes"
        for m in c["move"]:  # info: for m in c [ "move" ] :
            src, dest = Path(m["src"]), Path(m["dest"])  # info: src , dest = Path ( m [
            if not src.exists():  # info: if not src . exists ( ) :
                continue  # info: continue
            ensure_dataset_readme(ARCHIVE_ROOT / dest.relative_to(ARCHIVE_ROOT).parts[0])  # info: call ensure_dataset_readme
            move_into(src, dest)  # info: call move_into
            done.append(f"moved {cls} {src} -> {dest}")  # info: done . append ( f" moved { cls
    lg = p["log"]  # info: set lg
    if lg["rotate"]:  # info: if lg [ "rotate" ] :
        log = Path(lg["path"])  # info: set log
        oldest = log.with_name(f"{log.name}.{LOG_KEEP}")  # info: set oldest
        if oldest.exists():  # info: if oldest . exists ( ) :
            yyyymm = datetime.fromtimestamp(oldest.stat().st_mtime).strftime("%Y%m")  # info: set yyyymm
            ensure_dataset_readme(ARCHIVE_ROOT / f"Weather-{yyyymm}")  # info: call ensure_dataset_readme
            move_into(oldest, dest_for(oldest, yyyymm).with_name(f"{log.name}.{datetime.now():%Y%m%d-%H%M%S}"))  # info: call move_into
            done.append(f"moved oldest rotated log {oldest.name} to archive")  # info: done . append ( f" moved oldest rotated log { oldest
        for i in range(LOG_KEEP - 1, 0, -1):  # info: for i in range ( LOG_KEEP - 1
            a = log.with_name(f"{log.name}.{i}")  # info: set a
            if a.exists():  # info: if a . exists ( ) :
                os.replace(a, log.with_name(f"{log.name}.{i + 1}"))  # info: os . replace ( a , log .
        shutil.copy2(log, log.with_name(f"{log.name}.1"))  # info: shutil . copy2 ( log , log .
        with log.open("r+b") as fh:  # info: with log . open ( "r+b" ) as
            fh.truncate(0)  # info: fh . truncate ( 0 )
        done.append("rotated weather-poller.log (copytruncate)")  # info: done . append ( "rotated weather-poller.log (copytruncate)" )
    return done  # info: return done


# ====================================================
# SECTION: function render
# What it does: render.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render(p: dict, mode: str, now: datetime, actions: list[str]) -> str:  # info: def render
    L = [f"# Weather retention — {mode.upper()} — {now.isoformat(timespec='seconds')} (HST)", "",
         f"Script: Pacific `Weather/scripts/weather-retention.py` ({'read-only; nothing moved' if mode == 'dry-run' else 'APPLY'}). "  # info: f" Script: Pacific `Weather/scripts/weather-retention.py` ( { 'read-only; nothing moved' if mode == 'dry-run'
         f"Dataset: `{DATASET}`. Archive target: `{ARCHIVE_ROOT}/Weather-<YYYYMM>/` (move, never delete).", "",  # info: f" Dataset: ` { DATASET } `. Archive target: ` { ARCHIVE_ROOT
         "| Class | Rule | Kept files | Kept bytes | Would move (items / files) | Would move bytes |",  # info: "| Class | Rule | Kept files | Kept bytes | Would move (items / files) | Would move bytes |" ,
         "| --- | --- | ---: | ---: | ---: | ---: |"]  # info: "| --- | --- | ---: | ---: | ---: | ---: |" ]
    rules = {"current": "keep", "text_dated": f"keep {KEEP_TEXT_DAYS} d", "imagery_dated": f"keep {KEEP_IMAGERY_DAYS} d",  # info: set rules
             "daily_zip": f"keep {KEEP_ZIP_DAYS} d", "reports_archived": f"keep {KEEP_REPORT_DAYS} d", "hurricanes": "keep all", "other": "keep (no rule)"}  # info: "daily_zip" : f" keep { KEEP_ZIP_DAYS } d
    tm_n = tm_b = 0  # info: set tm_n
    for k, c in p["classes"].items():  # info: for k , c in p [ "classes"
        mn = sum(m["files"] for m in c["move"]); mb = sum(m["bytes"] for m in c["move"])  # info: set mn
        tm_n += mn; tm_b += mb  # info: set tm_n
        L.append(f"| {k} | {rules[k]} | {c['kept_n']} | {c['kept_b']} ({human(c['kept_b'])}) | {len(c['move'])} / {mn} | {mb} ({human(mb)}) |")  # info: L . append ( f" | { k
    L += ["", f"**Total would move:** {tm_n} files, {tm_b} bytes ({human(tm_b)}). **Would delete:** 0 (policy never deletes).",  # info: set L
          f"**Weather/ total:** {p['total_files']} files, {p['total_bytes']} bytes ({human(p['total_bytes'])}). **Disk free:** {human(p['disk_free'])}.",  # info: f" **Weather/ total:** { p [ 'total_files' ] }
          f"**Daemon log:** {p['log']['bytes']} bytes; rotate needed: {'yes' if p['log']['rotate'] else 'no'} (10 MB x 5); existing rotations: {p['log']['existing_rotations'] or 'none'}.",  # info: f" **Daemon log:** { p [ 'log' ] [
          f"**Budget alarms:** {'; '.join(p['alarms']) if p['alarms'] else 'none (Weather/ < 20 GB, free >= 50 GB)'}.", ""]  # info: f" **Budget alarms:** { '; ' . join ( p
    moves = [m for c in p["classes"].values() for m in c["move"]]  # info: set moves
    if moves:  # info: if moves :
        L += ["## Items older than their window", ""] + [f"- `{m['src']}` ({m['files']} files, {m['bytes']} B, age {m['age_days']} d > {m['rule_days']} d) → `{m['dest']}`" for m in moves[:200]]
        if len(moves) > 200:  # info: if len ( moves ) > 200 :
            L.append(f"- … {len(moves) - 200} more")  # info: L . append ( f" - … { len
        L.append("")  # info: L . append ( "" )
    if actions:  # info: if actions :
        L += ["## Actions", ""] + [f"- {a}" for a in actions] + [""]
    L += ["## Notes", "", "- Daily zips mix text and imagery; they follow the 90-day zip rule. Whether zipped imagery should leave after 14 days is an open question for Alexander.",
          f"- Oldest dated archive folder / daily zip: {p['oldest_dated'] or 'none'} (windows: imagery {KEEP_IMAGERY_DAYS} d, text and zips {KEEP_TEXT_DAYS} d, reports {KEEP_REPORT_DAYS} d by mtime).", ""]  # info: f" - Oldest dated archive folder / daily zip: { p [ 'oldest_dated' ] or
    return "\n".join(L)  # info: return "\n" . join ( L )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser(description="Weather retention (dry-run by default)")  # info: set ap
    g = ap.add_mutually_exclusive_group()  # info: set g
    g.add_argument("--dry-run", action="store_true", default=True, help="default: read-only report")  # info: g . add_argument ( "--dry-run" , action =
    g.add_argument("--apply", action="store_true", help="move data past its window (needs Alexander's review of a dry run)")  # info: g . add_argument ( "--apply" , action =
    ap.add_argument("--report"); ap.add_argument("--no-save", action="store_true"); ap.add_argument("--json", action="store_true")  # info: ap . add_argument ( "--report" ) ; ap
    a = ap.parse_args()  # info: set a
    mode = "apply" if a.apply else "dry-run"  # info: set mode
    if not DATASET.is_dir():  # info: if not DATASET . is_dir ( ) :
        print(f"No data: {DATASET}", file=sys.stderr); return 1  # info: call print
    lock = open("/tmp/weather-retention.lock", "w")  # info: set lock
    try:  # info: try :
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # info: fcntl . flock ( lock , fcntl .
    except BlockingIOError:  # info: except BlockingIOError :
        print("[skip] another weather-retention run holds the lock"); return 0  # info: call print
    now = datetime.now().astimezone()  # info: set now
    p = plan(now.date())  # info: set p
    actions = apply(p) if mode == "apply" else []  # info: set actions
    text = render(p, mode, now, actions)  # info: set text
    print(text)  # info: call print
    if not a.no_save:  # info: if not a . no_save :
        out = Path(a.report) if a.report else REPORT_DIR / f"weather-retention_{mode}_{now:%Y-%m-%d_%H%M}.md"  # info: set out
        out.parent.mkdir(parents=True, exist_ok=True)  # info: out . parent . mkdir ( parents =
        out.write_text(text + "\n", encoding="utf-8")  # info: out . write_text ( text + "\n" ,
        print(f"[saved] {out}")  # info: call print
    if a.json:  # info: if a . json :
        print(json.dumps({"mode": mode, "would_move_files": sum(m["files"] for c in p["classes"].values() for m in c["move"]),  # info: call print
                          "would_move_bytes": sum(m["bytes"] for c in p["classes"].values() for m in c["move"]), "alarms": p["alarms"]}))  # info: "would_move_bytes" : sum ( m [ "bytes" ]
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
