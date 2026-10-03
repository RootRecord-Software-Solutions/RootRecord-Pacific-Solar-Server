#!/usr/bin/env python3
"""Generate every hour-desk voice report into Database Media/Audio/Voice/.

Measured batch wall time (2026-10-03): ~8.6 minutes for all desks.
jobs.py starts this at :43 so it finishes before radio_push --all at :55
(8.6 + 3 minute cushion → 12 minutes before :55).

Writes under the single voice tree:
  Media/Audio/Voice/<report>_current.wav
  Media/Audio/Voice/<report>_current.ogg
  Media/Audio/Voice/Reports/<report>_current.md

Does not push to ML1 (RR_RADIO_PUSH=0). radio_push_hour at :55 owns the send.
Hourly chimes stay on voice_hourly_chime (:00/:30) unless --include-chime.

Usage:
  python3 generate_hour_reports.py
  python3 generate_hour_reports.py --only solar_desk,kilauea_report
  python3 generate_hour_reports.py --include-chime
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parents[2]
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
VOICE_WAV = OUT_DIR
VOICE_PY = Path(
    os.environ.get(
        "RR_VOICE_PY",
        str(PACIFIC / "Media" / "Voice" / ".venv" / "bin" / "python"),
    )
)

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated report ids")
    ap.add_argument("--include-chime", action="store_true", help="also render hourly_chime (not used by :43 job)")
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
    summary_path = OUT_DIR / "generate_hour_reports_last.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
