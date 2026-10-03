#!/usr/bin/env python3
"""Generate every hour-desk voice report into Database Media/Audio/Voice/.

Measured batch wall time (2026-10-03): ~8.6 minutes for all desks.
jobs.py starts this at :42 by default. When the batch finishes it:
  1. records wall + per-report seconds under Media/Audio/Voice/Timing/
  2. updates running averages, then recalculates next start minute (keeps :42 unless averages need earlier)
  3. radio_push --all to ML1 immediately

:55 radio_push_hour remains a catch-up if this send missed.

Writes under the single voice tree:
  Media/Audio/Voice/<report>_current.wav
  Media/Audio/Voice/<report>_current.ogg
  Media/Audio/Voice/Reports/<report>_current.md

Hourly chimes stay on voice_hourly_chime (:00/:30) unless --include-chime.

Usage:
  python3 generate_hour_reports.py
  python3 generate_hour_reports.py --only solar_desk,kilauea_report
  python3 generate_hour_reports.py --include-chime
  python3 generate_hour_reports.py --no-push
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parents[2]
HST = ZoneInfo("Pacific/Honolulu")
DB = Path(
    os.environ.get(
        "RR_DATABASE_ROOT",
        "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
    )
)
OUT_DIR = Path(
    os.environ.get(
        "RR_AUDIO_REPORTS_OUT",
        str(DB / "Media" / "Audio" / "Voice"),
    )
)
TIMING_DIR = Path(
    os.environ.get(
        "RR_VOICE_HOUR_TIMING_DIR",
        str(OUT_DIR / "Timing"),
    )
)
VOICE_WAV = OUT_DIR
VOICE_PY = Path(
    os.environ.get(
        "RR_VOICE_PY",
        str(PACIFIC / "Media" / "Voice" / ".venv" / "bin" / "python"),
    )
)
CUSHION_MINUTES = float(os.environ.get("RR_VOICE_HOUR_CUSHION_MIN", "3"))
HISTORY_KEEP = int(os.environ.get("RR_VOICE_HOUR_HISTORY_KEEP", "200"))
# Preferred start minute (answer to life). Recalc may move earlier if averages need more lead before :55.
BASE_START_MINUTE = int(os.environ.get("RR_VOICE_HOUR_BASE_MINUTE", "42"))
PUSH_MINUTE = int(os.environ.get("RR_VOICE_HOUR_PUSH_MINUTE", "55"))

# Hour batch for :55 radio_push (no chime — that stays :00/:30).
HOUR_REPORTS: list[tuple[str, str, str]] = [
    ("boot_brief", "ava", "voice_reports"),
    ("official_weather", "ava", "voice_reports"),
    ("nws_weather", "ava", "voice_reports"),
    ("current_report", "ava", "voice_reports"),
    ("solar_desk", "bruce", "voice_reports"),
    ("remaining_tasks", "bruce", "voice_reports"),
    ("system_perf", "bruce", "system_perf"),
    ("earthquake_report", "carly", "voice_reports"),
    ("hurricane_desk", "carly", "voice_reports"),
    ("kilauea_report", "carly", "voice_reports"),
    ("kilauea_image_check", "carly", "voice_reports"),
    ("security_desk", "carly", "voice_reports"),
    ("bandwidth_desk", "carly", "voice_reports"),
]

CHIME_REPORT = ("hourly_chime", "ava", "chime")

ENV_BASE = {
    "RR_RADIO_PUSH": "0",
    "RR_VOICE_DELIVER": "0",
    "RR_VOICE_STATUS": "0",
    "RR_DATABASE_ROOT": str(DB),
}


def encode_ogg(wav: Path, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.parent / f".{dest.stem}.partial.ogg"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(wav),
        "-c:a",
        "libopus",
        "-b:a",
        "24k",
        "-application",
        "voip",
        "-ac",
        "1",
        "-f",
        "ogg",
        str(tmp),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if p.returncode != 0 or not tmp.is_file() or tmp.stat().st_size < 64:
        tmp.unlink(missing_ok=True)
        return {"ok": False, "detail": "encode_failed", "stderr": (p.stderr or "")[-400:]}
    os.replace(tmp, dest)
    dest.chmod(0o644)
    return {"ok": True, "ogg": str(dest), "bytes": dest.stat().st_size}


def find_wav(report: str) -> Path | None:
    for c in (VOICE_WAV / f"{report}_current.wav", VOICE_WAV / "Chimes" / f"{report}_current.wav"):
        if c.is_file() and c.stat().st_size > 64:
            return c
    return None


def run_voice_reports(report: str) -> dict:
    env = {**os.environ, **ENV_BASE}
    cmd = [str(VOICE_PY if VOICE_PY.is_file() else sys.executable), str(HERE / "voice_reports.py"), report]
    p = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True, timeout=900, env=env)
    last = (p.stdout.strip().splitlines() or ["{}"])[-1]
    try:
        res = json.loads(last)
    except ValueError:
        res = {"ok": False, "detail": "bad_json", "stdout": p.stdout[-500:], "stderr": p.stderr[-500:]}
    res["rc"] = p.returncode
    if p.stderr:
        res["stderr_tail"] = p.stderr[-800:]
    voice = res.get("voice") if isinstance(res.get("voice"), dict) else None
    if voice is not None and voice.get("rc") not in (None, 0) and not voice.get("detail"):
        voice["detail"] = (p.stderr or "").strip().splitlines()[-1] if p.stderr else f"voice_rc={voice.get('rc')}"
    return res


def run_system_perf() -> dict:
    env = {**os.environ, **ENV_BASE}
    cmd = [str(VOICE_PY if VOICE_PY.is_file() else sys.executable), str(HERE / "system_perf.py")]
    p = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True, timeout=600, env=env)
    last = (p.stdout.strip().splitlines() or ["{}"])[-1]
    try:
        res = json.loads(last)
    except ValueError:
        res = {"ok": False, "detail": "bad_json", "stdout": p.stdout[-500:], "stderr": p.stderr[-500:]}
    res["rc"] = p.returncode
    return res


def run_chime() -> dict:
    sys.path.insert(0, str(HERE))
    from datetime import datetime
    from zoneinfo import ZoneInfo

    try:
        from hourly_chimes import persona_for, wav_path
    except Exception as exc:
        return {"ok": False, "detail": f"hourly_chimes: {exc}"}

    t = datetime.now(ZoneInfo("Pacific/Honolulu"))
    who = persona_for(t.hour)
    pre = wav_path(t.hour, 0 if t.minute < 30 else 30)
    if pre.is_file() and pre.stat().st_size > 64:
        return {"ok": True, "mode": "prebuilt", "wav": str(pre), "agent": who}

    line = f"Root Record hourly chime test for {who}."
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(line)
        text_path = f.name
    try:
        cmd = [
            "bash",
            str(HERE / "voice-render.sh"),
            "stitch",
            "--report",
            "hourly_chime",
            "--kind",
            "chime",
            "--text-file",
            text_path,
            "--no-gate",
        ]
        env = {**os.environ, **ENV_BASE}
        p = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True, timeout=600, env=env)
        last = (p.stdout.strip().splitlines() or ["{}"])[-1]
        try:
            res = json.loads(last)
        except ValueError:
            res = {"ok": False, "detail": "bad_json", "stdout": p.stdout[-500:]}
        res["rc"] = p.returncode
        res["agent"] = who
        res["mode"] = "stitched_test"
        return res
    finally:
        os.unlink(text_path)


def one(report: str, agent: str, how: str) -> dict:
    started = time.time()
    row: dict = {"report": report, "agent": agent, "how": how}
    try:
        if how == "voice_reports":
            gen = run_voice_reports(report)
        elif how == "system_perf":
            gen = run_system_perf()
        elif how == "chime":
            gen = run_chime()
        else:
            return {**row, "ok": False, "detail": f"unknown how={how}"}
        row["generate"] = {
            k: gen.get(k)
            for k in ("ok", "rc", "skipped", "detail", "wav", "mode", "agent", "sentences")
            if k in gen or gen.get(k) is not None
        }
        if gen.get("voice"):
            row["generate"]["voice"] = {
                k: gen["voice"].get(k)
                for k in ("ok", "rc", "wav", "detail", "skipped", "mode")
                if k in gen["voice"]
            }
        wav: Path | None = None
        if isinstance(gen.get("wav"), str):
            wav = Path(gen["wav"])
        voice = gen.get("voice") or {}
        if wav is None and isinstance(voice.get("wav"), str):
            wav = Path(voice["wav"])
        if wav is None or not wav.is_file():
            wav = find_wav(report)
        if wav is None or not wav.is_file():
            row["ok"] = False
            row["detail"] = "no_wav_after_generate"
            row["seconds"] = round(time.time() - started, 1)
            return row
        enc = encode_ogg(wav, OUT_DIR / f"{report}_current.ogg")
        row["encode"] = enc
        row["wav"] = str(wav)
        row["ok"] = bool(enc.get("ok"))
        row["ogg"] = enc.get("ogg")
        row["seconds"] = round(time.time() - started, 1)
        return row
    except subprocess.TimeoutExpired:
        return {**row, "ok": False, "detail": "timeout", "seconds": round(time.time() - started, 1)}
    except Exception as exc:
        return {
            **row,
            "ok": False,
            "detail": f"{type(exc).__name__}: {exc}",
            "seconds": round(time.time() - started, 1),
        }


def _load_history() -> list[dict]:
    path = TIMING_DIR / "hour_batch_history.jsonl"
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and obj.get("wall_seconds") is not None:
            rows.append(obj)
    return rows[-HISTORY_KEEP:]


def _mean(vals: list[float]) -> float | None:
    return round(statistics.fmean(vals), 1) if vals else None


def _percentile(vals: list[float], pct: float) -> float | None:
    if not vals:
        return None
    ordered = sorted(vals)
    if len(ordered) == 1:
        return round(ordered[0], 1)
    k = (len(ordered) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(ordered[int(k)], 1)
    return round(ordered[f] * (c - k) + ordered[c] * (k - f), 1)


def record_timing(summary: dict) -> dict:
    """Bank this run's durations and recompute averages for scheduling.

    Writes:
      Media/Audio/Voice/Timing/hour_batch_current.json
      Media/Audio/Voice/Timing/hour_batch_averages.json
      Media/Audio/Voice/Timing/hour_batch_history.jsonl  (append)
    """
    TIMING_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(HST).replace(microsecond=0)
    per_report = {
        r["report"]: r.get("seconds")
        for r in summary.get("results") or []
        if isinstance(r.get("seconds"), (int, float))
    }
    wall = summary.get("wall_seconds")
    if not isinstance(wall, (int, float)) and per_report:
        # Sequential batch: sum of per-report seconds when wall clock wasn't recorded.
        wall = round(sum(float(v) for v in per_report.values()), 1)
    count = len(summary.get("results") or [])
    # Full hour batch only — --only smokes must not skew averages / start-minute suggestion.
    full_batch = count >= len(HOUR_REPORTS)
    entry = {
        "at": now.isoformat(),
        "ok": bool(summary.get("ok")),
        "wall_seconds": wall,
        "passed": summary.get("passed"),
        "failed": summary.get("failed"),
        "count": count,
        "full_batch": full_batch,
        "per_report_seconds": per_report,
    }

    history_path = TIMING_DIR / "hour_batch_history.jsonl"
    if full_batch and wall is not None:
        with history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    history = _load_history()
    # Keep file trimmed.
    if len(history) > HISTORY_KEEP:
        history_path.write_text(
            "".join(json.dumps(h, ensure_ascii=False) + "\n" for h in history[-HISTORY_KEEP:]),
            encoding="utf-8",
        )
        history = history[-HISTORY_KEEP:]

    totals = [float(h["wall_seconds"]) for h in history if h.get("wall_seconds") is not None]
    by_report: dict[str, list[float]] = {}
    for h in history:
        for name, sec in (h.get("per_report_seconds") or {}).items():
            if isinstance(sec, (int, float)):
                by_report.setdefault(name, []).append(float(sec))

    def _stats(vals: list[float], last: float | None = None) -> dict:
        return {
            "avg": _mean(vals),
            "median": round(statistics.median(vals), 1) if vals else None,
            "p95": _percentile(vals, 0.95),
            "min": round(min(vals), 1) if vals else None,
            "max": round(max(vals), 1) if vals else None,
            "last": last,
        }

    total_stats = _stats(totals, last=entry.get("wall_seconds") if isinstance(entry.get("wall_seconds"), (int, float)) else None)
    # Human-readable minutes beside seconds (schedule math still uses seconds).
    total_minutes = {
        k: (round(v / 60.0, 2) if isinstance(v, (int, float)) else None)
        for k, v in total_stats.items()
    }
    avg_total = total_stats["avg"]
    p95_total = total_stats["p95"]
    lead_from = p95_total if p95_total is not None else avg_total
    suggested_lead_min = (
        math.ceil((lead_from or 0) / 60.0 + CUSHION_MINUTES) if lead_from is not None else None
    )
    suggested_start_minute = (
        (PUSH_MINUTE - suggested_lead_min) % 60 if suggested_lead_min is not None else None
    )

    averages = {
        "at": now.isoformat(),
        "runs": len(history),
        "cushion_minutes": CUSHION_MINUTES,
        "base_start_minute": BASE_START_MINUTE,
        "push_minute": PUSH_MINUTE,
        # TOTAL batch duration across full hour runs — this drives schedule recalculation.
        "total": {
            "seconds": total_stats,
            "minutes": total_minutes,
        },
        # Alias kept for older readers.
        "wall_seconds": total_stats,
        "per_report_avg_seconds": {k: _mean(v) for k, v in sorted(by_report.items())},
        "suggested_lead_minutes_before_55": suggested_lead_min,
        "suggested_start_minute": suggested_start_minute,
    }

    current = {
        **entry,
        "averages": averages,
        "paths": {
            "history": str(history_path),
            "averages": str(TIMING_DIR / "hour_batch_averages.json"),
        },
    }
    (TIMING_DIR / "hour_batch_current.json").write_text(
        json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (TIMING_DIR / "hour_batch_averages.json").write_text(
        json.dumps(averages, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return current


def recalculate_start_time(timing: dict | None = None) -> dict:
    """After a batch finishes, recompute the next voice_hour_batch minute from averages.

    Keeps BASE_START_MINUTE (:42) unless measured lead needs an earlier start before :55.
    Writes Media/Audio/Voice/Timing/hour_batch_schedule.json for jobs.py to read.
    """
    TIMING_DIR.mkdir(parents=True, exist_ok=True)
    averages = None
    if isinstance(timing, dict):
        averages = timing.get("averages") if isinstance(timing.get("averages"), dict) else None
    if averages is None:
        avg_path = TIMING_DIR / "hour_batch_averages.json"
        if avg_path.is_file():
            try:
                averages = json.loads(avg_path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                averages = None
    averages = averages if isinstance(averages, dict) else {}

    suggested = averages.get("suggested_start_minute")
    if not isinstance(suggested, int):
        try:
            suggested = int(suggested) if suggested is not None else None
        except (TypeError, ValueError):
            suggested = None

    # Both minutes are in the pre-:55 window: earlier start = smaller minute.
    if suggested is None:
        at_minute = BASE_START_MINUTE
        reason = "base_default"
    elif suggested <= BASE_START_MINUTE:
        at_minute = suggested
        reason = "averages_need_earlier" if suggested < BASE_START_MINUTE else "averages_match_base"
    else:
        # Batch got faster than :42 lead — keep the answer to life (extra cushion).
        at_minute = BASE_START_MINUTE
        reason = "keep_base_extra_cushion"

    at_minute = max(0, min(59, int(at_minute)))
    lead = (PUSH_MINUTE - at_minute) % 60
    now = datetime.now(HST).replace(microsecond=0)
    schedule = {
        "at": now.isoformat(),
        "job_id": "voice_hour_batch",
        "at_minute": at_minute,
        "at_second": 0,
        "push_minute": PUSH_MINUTE,
        "base_start_minute": BASE_START_MINUTE,
        "suggested_start_minute": suggested,
        "lead_minutes_before_push": lead,
        "reason": reason,
        "averages_runs": averages.get("runs"),
        "total_avg_seconds": (
            ((averages.get("total") or {}).get("seconds") or averages.get("wall_seconds") or {}).get("avg")
        ),
        "total_p95_seconds": (
            ((averages.get("total") or {}).get("seconds") or averages.get("wall_seconds") or {}).get("p95")
        ),
        "total_avg_minutes": ((averages.get("total") or {}).get("minutes") or {}).get("avg"),
        "total_p95_minutes": ((averages.get("total") or {}).get("minutes") or {}).get("p95"),
    }
    schedule_path = TIMING_DIR / "hour_batch_schedule.json"
    schedule_path.write_text(json.dumps(schedule, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Mirror scheduled minute onto averages for a single read surface.
    if averages:
        averages["scheduled_at_minute"] = at_minute
        averages["schedule_reason"] = reason
        averages["at"] = now.isoformat()
        (TIMING_DIR / "hour_batch_averages.json").write_text(
            json.dumps(averages, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    schedule["path"] = str(schedule_path)
    return schedule


def push_to_ml1() -> dict:
    """Send every finished hour-desk WAV to ML1 as soon as the batch finishes."""
    if os.environ.get("RR_HOUR_BATCH_PUSH", "1") != "1":
        return {"ok": True, "skipped": True, "detail": "RR_HOUR_BATCH_PUSH=0"}
    try:
        import radio_push
    except Exception as exc:
        return {"ok": False, "detail": f"import_radio_push: {type(exc).__name__}: {exc}"}
    try:
        return radio_push.push_all()
    except Exception as exc:
        return {"ok": False, "detail": f"push_all: {type(exc).__name__}: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated report ids")
    ap.add_argument("--include-chime", action="store_true", help="also render hourly_chime (not used by :42 job)")
    ap.add_argument("--no-push", action="store_true", help="skip ML1 radio_push after generate")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    catalog = list(HOUR_REPORTS)
    if args.include_chime or (only and "hourly_chime" in only):
        catalog.append(CHIME_REPORT)
    jobs = [r for r in catalog if not only or r[0] in only]
    if not jobs:
        print(json.dumps({"ok": False, "detail": "no reports selected"}))
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    t0 = time.time()
    print(json.dumps({"ok": True, "phase": "start", "out": str(OUT_DIR), "count": len(jobs)}), flush=True)
    for report, agent, how in jobs:
        print(json.dumps({"ok": True, "phase": "begin", "report": report, "agent": agent}), flush=True)
        row = one(report, agent, how)
        results.append(row)
        print(json.dumps({"ok": True, "phase": "done", **row}, ensure_ascii=False), flush=True)

    summary = {
        "ok": all(r.get("ok") for r in results),
        "out": str(OUT_DIR),
        "passed": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "wall_seconds": round(time.time() - t0, 1),
        "results": results,
    }
    summary["timing"] = record_timing(summary)
    print(json.dumps({"ok": True, "phase": "timing", **summary["timing"]}, ensure_ascii=False), flush=True)
    summary["schedule"] = recalculate_start_time(summary["timing"])
    print(
        json.dumps({"ok": True, "phase": "schedule", **summary["schedule"]}, ensure_ascii=False),
        flush=True,
    )

    if args.no_push:
        summary["radio"] = {"ok": True, "skipped": True, "detail": "--no-push"}
    else:
        print(json.dumps({"ok": True, "phase": "push_begin"}), flush=True)
        summary["radio"] = push_to_ml1()
        print(json.dumps({"ok": True, "phase": "push_done", **summary["radio"]}, ensure_ascii=False), flush=True)
        if not summary["radio"].get("ok") and not summary["radio"].get("skipped"):
            summary["ok"] = False

    summary_path = OUT_DIR / "generate_hour_reports_last.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
