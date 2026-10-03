# ==============================================================================
# FILE: Reports/pipeline/store.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Canonical report files plus an index. Legacy markdown is indexed. Nothing is deleted."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

from generate import from_measured, note_retry  # info: from generate import from_measured , note_retry
from model import empty_stages, new_report, report_id  # info: from model import empty_stages , new_report , report_id
from windows import contains, window_for  # info: from windows import window_for

HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parents[1]  # info: set PACIFIC
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
CANON = Path(os.environ.get("RR_CANONICAL_DIR", str(DB / "Reports" / "canonical")))  # info: set CANON
LOG = Path(os.environ.get("RR_REPORT_LOG", str(DB / "Logs" / "Reports" / "pipeline.jsonl")))  # info: set LOG


# ====================================================
# SECTION: function _now
# What it does: Clock stamp in Pacific/Honolulu.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now() -> str:  # info: def _now
    from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Pacific/Honolulu")).replace(microsecond=0).isoformat()  # info: return iso now


# ====================================================
# SECTION: function _write
# What it does: Atomically write one JSON file. It replaces the same path. It does not remove other files.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(path: Path, report: dict) -> None:  # info: def _write
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, path)  # info: os . replace


# ====================================================
# SECTION: function log_event
# What it does: Append one pipeline line. It records the report, window, stage, and error.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_event(event: str, report: dict, stage: str = "", error: str = "", duration: float = 0) -> None:  # info: def log_event
    LOG.parent.mkdir(parents=True, exist_ok=True)  # info: LOG . parent . mkdir
    row = {  # info: set row
        "event": event,  # info: "event" : event
        "report_id": report.get("report_id") or "",  # info: "report_id"
        "slug": report.get("slug") or "",  # info: "slug"
        "window_start": report.get("window_start") or "",  # info: "window_start"
        "window_end": report.get("window_end") or "",  # info: "window_end"
        "stage": stage,  # info: "stage" : stage
        "status": report.get("status") or "",  # info: "status"
        "error": error,  # info: "error" : error
        "retry": (report.get("stages") or {}).get(stage, {}).get("retry", 0) if stage else 0,  # info: "retry"
        "duration": duration,  # info: "duration" : duration
        "at": _now(),  # info: "at"
    }  # info: }
    with LOG.open("a", encoding="utf-8") as handle:  # info: with LOG . open
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")  # info: handle . write


# ====================================================
# SECTION: function profiles
# What it does: Read the profile file. It does not create jobs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def profiles() -> list[dict]:  # info: def profiles
    data = json.loads((HERE / "profiles.json").read_text(encoding="utf-8"))  # info: set data
    return [row for row in data.get("profiles") or [] if isinstance(row, dict)]  # info: return rows


# ====================================================
# SECTION: function profile_for
# What it does: Find the profile for a voice slug. Unknown slugs get a measured hourly profile.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def profile_for(slug: str) -> dict:  # info: def profile_for
    for row in profiles():  # info: for row in profiles
        if row.get("slug") == slug:  # info: if row . get ( "slug" ) == slug
            return row  # info: return row
    return {"id": slug.replace("_", "-"), "slug": slug, "topic": slug, "scope": "desk", "cadence": "hourly", "owns": [], "generator": "voice_build", "enabled": True, "assets": {"text": True, "audio": True, "image": False, "video": False, "youtube": False, "radio": True}}  # info: return fallback


# ====================================================
# SECTION: function path_for
# What it does: Canonical JSON path for one report id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def path_for(rid: str) -> Path:  # info: def path_for
    return CANON / f"{rid}.json"  # info: return CANON / rid


# ====================================================
# SECTION: function load
# What it does: Read one canonical report. Missing files return None.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load(rid: str) -> dict | None:  # info: def load
    path = path_for(rid)  # info: set path
    if not path.is_file():  # info: if not path . is_file
        return None  # info: return None
    return json.loads(path.read_text(encoding="utf-8"))  # info: return json


# ====================================================
# SECTION: function save
# What it does: Write the canonical file and keep the first created_at when the same id is saved again.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save(report: dict, sidecar: Path | None = None) -> dict:  # info: def save
    prior = load(report["report_id"])  # info: set prior
    if prior and prior.get("created_at"):  # info: if prior and prior . get ( "created_at" )
        report["created_at"] = prior["created_at"]  # info: report [ "created_at" ] = prior
    _write(path_for(report["report_id"]), report)  # info: call _write
    if sidecar is not None:  # info: if sidecar is not None
        _write(sidecar, report)  # info: call _write sidecar
    return report  # info: return report


# ====================================================
# SECTION: function list_reports
# What it does: List canonical reports. Filters are topic, scope, status, and a date that falls in the window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def list_reports(topic: str = "", scope: str = "", status: str = "", date: str = "") -> list[dict]:  # info: def list_reports
    rows = []  # info: set rows
    if not CANON.is_dir():  # info: if not CANON . is_dir
        return rows  # info: return rows
    for path in sorted(CANON.glob("*.json")):  # info: for path in sorted
        if path.name.startswith("."):  # info: if path . name . startswith
            continue  # info: continue
        try:  # info: try
            report = json.loads(path.read_text(encoding="utf-8"))  # info: set report
        except (OSError, json.JSONDecodeError):  # info: except
            continue  # info: continue
        if not isinstance(report, dict) or not report.get("report_id"):  # info: if not a report
            continue  # info: continue
        if topic and report.get("topic") != topic:  # info: if topic mismatch
            continue  # info: continue
        if scope and report.get("scope") != scope:  # info: if scope mismatch
            continue  # info: continue
        if status and report.get("status") != status:  # info: if status mismatch
            continue  # info: continue
        if date and date not in str(report.get("window_start") or "") and date not in str(report.get("created_at") or ""):  # info: if date mismatch
            continue  # info: continue
        rows.append(report)  # info: rows . append
    return rows  # info: return rows


# ====================================================
# SECTION: function latest_slug
# What it does: Newest canonical report for a slug, by generated_at then created_at.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def latest_slug(slug: str) -> dict | None:  # info: def latest_slug
    rows = [row for row in list_reports() if row.get("slug") == slug and row.get("window_start")]  # info: set rows
    if not rows:  # info: if not rows
        return None  # info: return None
    rows.sort(key=lambda row: row.get("generated_at") or row.get("created_at") or "")  # info: rows . sort
    return rows[-1]  # info: return rows [ -1 ]


# ====================================================
# SECTION: function _asset
# What it does: One asset row pointing at a file that already exists. It does not encode media.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _asset(kind: str, path: str) -> dict:  # info: def _asset
    return {"kind": kind, "path": path, "report_id": ""}  # info: return asset


# ====================================================
# SECTION: function apply_voice
# What it does: Attach measured text and the voice result. A failed WAV leaves the text stage ready.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_voice(report: dict, markdown: str, spoken: list, voice: dict | None, text_path: str) -> dict:  # info: def apply_voice
    made = from_measured(markdown, spoken, report.get("generator") or "voice_build")  # info: set made
    report["sections"] = made["sections"]  # info: report [ "sections" ]
    report["spoken"] = made["spoken"]  # info: report [ "spoken" ]
    report["provider"] = made["provider"]  # info: report [ "provider" ]
    report["model"] = made["model"]  # info: report [ "model" ]
    report["generator_version"] = made["generator_version"]  # info: report [ "generator_version" ]
    report["generated_at"] = _now()  # info: report [ "generated_at" ]
    report["stages"]["text"] = {"status": "ready", "path": text_path, "error": "", "retry": 0}  # info: text ready
    report["assets"] = [_asset("text", text_path)]  # info: set assets
    policy = profile_for(report.get("slug") or "").get("assets") or {}  # info: set policy
    voice = voice or {}  # info: set voice
    wav = str(voice.get("wav") or "")  # info: set wav
    rc = voice.get("rc", voice.get("voice_rc"))  # info: set rc
    if not policy.get("audio", True):  # info: if audio disabled
        report["stages"]["audio"] = {"status": "skipped", "path": "", "error": "", "retry": 0}  # info: audio skipped
    elif wav and rc in (0, None) and voice.get("ok", True):  # info: elif wav ready
        report["stages"]["audio"] = {"status": "ready", "path": wav, "error": "", "retry": 0}  # info: audio ready
        report["assets"].append(_asset("audio", wav))  # info: assets . append audio
    else:  # info: else
        stage = {"status": "failed", "path": "", "error": str(voice.get("detail") or "audio_failed"), "retry": 0}  # info: set stage
        if rc == 75:  # info: if rc == 75
            note_retry(stage)  # info: call note_retry
            stage["error"] = "busy"  # info: stage [ "error" ] = "busy"
        report["stages"]["audio"] = stage  # info: audio failed
    for kind, flag in (("image", "image"), ("video", "video")):  # info: for kind , flag
        if policy.get(flag):  # info: if policy wants the asset
            report["stages"][kind] = {"status": "pending", "path": "", "error": "", "retry": 0}  # info: stage pending
        else:  # info: else
            report["stages"][kind] = {"status": "skipped", "path": "", "error": "", "retry": 0}  # info: stage skipped
    key = os.environ.get("RR_YOUTUBE_STREAM_KEY", "")  # info: set key
    if policy.get("youtube") and key:  # info: if youtube and key
        report["publication"]["status"] = "ready"  # info: publication ready
    else:  # info: else
        report["publication"]["status"] = "not_configured"  # info: publication not_configured
        report["publication"]["error"] = ""  # info: clear error
    report["stages"]["publication"] = {"status": report["publication"]["status"], "path": "", "error": report["publication"].get("error") or "", "retry": 0}  # info: publication stage
    if report["stages"]["text"]["status"] != "ready":  # info: if text not ready
        report["status"] = "failed"  # info: status failed
    elif report["stages"]["audio"]["status"] == "failed":  # info: elif audio failed
        report["status"] = "generated"  # info: status generated
    else:  # info: else
        report["status"] = "assets_ready"  # info: status assets_ready
    for asset in report["assets"]:  # info: for asset in assets
        asset["report_id"] = report["report_id"]  # info: asset [ "report_id" ]
    return report  # info: return report


# ====================================================
# SECTION: function record_voice
# What it does: Save one voice run under its window id and beside the markdown. It does not move the markdown.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def record_voice(slug: str, markdown: str, spoken: list, voice: dict | None, text_path: Path, when: datetime | None = None) -> dict:  # info: def record_voice
    profile = profile_for(slug)  # info: set profile
    clock = when or datetime.now()  # info: set clock
    window = window_for(clock, str(profile.get("cadence") or "hourly"))  # info: set window
    report = new_report(profile, window, _now())  # info: set report
    apply_voice(report, markdown, spoken, voice, str(text_path))  # info: call apply_voice
    sidecar = text_path.with_name(text_path.stem + ".report.json")  # info: set sidecar
    save(report, sidecar)  # info: call save
    log_event("completed" if report["status"] != "failed" else "failed", report, "text")  # info: call log_event
    if report["stages"]["audio"]["status"] == "failed":  # info: if audio failed
        log_event("failed", report, "audio", report["stages"]["audio"].get("error") or "")  # info: log audio failure
    write_queue()  # info: call write_queue
    return report  # info: return report


# ====================================================
# SECTION: function record_generated
# What it does: Save a deterministic generation for one context. The same window updates the same id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def record_generated(profile: dict, context: dict, made: dict, when: str | None = None) -> dict:  # info: def record_generated
    report = new_report(profile, context["window"], when or _now())  # info: set report
    report["status"] = "generated"  # info: status generated
    report["sections"] = made.get("sections") or []  # info: sections
    report["spoken"] = made.get("spoken") or []  # info: spoken
    report["observations"] = list(context.get("observations") or [])  # info: observations
    report["sources"] = list(context.get("sources") or [])  # info: sources
    report["provider"] = made.get("provider") or "deterministic"  # info: provider
    report["model"] = made.get("model") or "template"  # info: model
    report["generator_version"] = made.get("generator_version") or report["generator_version"]  # info: generator_version
    report["generated_at"] = when or _now()  # info: generated_at
    report["stages"]["text"] = {"status": "ready", "path": "", "error": "", "retry": 0}  # info: text ready
    report["stages"]["audio"] = {"status": "skipped", "path": "", "error": "", "retry": 0}  # info: audio skipped
    report["stages"]["image"] = {"status": "skipped", "path": "", "error": "", "retry": 0}  # info: image skipped
    report["stages"]["video"] = {"status": "skipped", "path": "", "error": "", "retry": 0}  # info: video skipped
    report["publication"]["status"] = "not_configured"  # info: publication not_configured
    report["stages"]["publication"] = {"status": "not_configured", "path": "", "error": "", "retry": 0}  # info: publication stage
    save(report)  # info: call save
    log_event("completed", report, "text")  # info: call log_event
    return report  # info: return report


# ====================================================
# SECTION: function mark_publication
# What it does: Set the YouTube publication state. It does not open a stream and it does not delete the report.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mark_publication(rid: str, status: str, error: str = "") -> dict | None:  # info: def mark_publication
    report = load(rid)  # info: set report
    if report is None:  # info: if report is None
        return None  # info: return None
    report["publication"]["status"] = status  # info: set status
    report["publication"]["error"] = error  # info: set error
    if status == "failed":  # info: if status == "failed"
        note_retry(report["publication"])  # info: call note_retry
        note_retry(report["stages"]["publication"])  # info: retry stage
    report["stages"]["publication"]["status"] = status  # info: stage status
    report["stages"]["publication"]["error"] = error  # info: stage error
    if status == "published":  # info: if status == "published"
        report["status"] = "published"  # info: report published
        report["published_at"] = _now()  # info: published_at
    save(report)  # info: call save
    log_event("failed" if status == "failed" else "completed", report, "publication", error)  # info: call log_event
    return report  # info: return report


# ====================================================
# SECTION: function recover
# What it does: Report that contains now, and the next stored window after it. It does not replay the day.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def recover(when: datetime) -> dict:  # info: def recover
    current = [row for row in list_reports() if contains(row, when)]  # info: set current
    local = window_for(when, "5m")["window_start"]  # info: set local
    later = [row for row in list_reports() if (row.get("window_start") or "") > local]  # info: set later
    later.sort(key=lambda row: row.get("window_start") or "")  # info: later . sort
    return {"now": local, "current": current, "next": later[:1]}  # info: return recover


# ====================================================
# SECTION: function write_queue
# What it does: Write the stream queue from reports that have audio and have not been marked played.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_queue() -> Path:  # info: def write_queue
    items = []  # info: set items
    for report in list_reports():  # info: for report in list_reports
        if report.get("provenance", {}).get("legacy_path") and not report.get("window_start"):  # info: if legacy without window
            continue  # info: continue
        audio = ""  # info: set audio
        for asset in report.get("assets") or []:  # info: for asset in assets
            if asset.get("kind") == "audio" and asset.get("path"):  # info: if audio asset
                audio = asset["path"]  # info: set audio
        if not audio:  # info: if not audio
            continue  # info: continue
        if report.get("stream_played"):  # info: if stream_played
            continue  # info: continue
        items.append({  # info: items . append
            "report_id": report["report_id"],  # info: report_id
            "id": report.get("slug") or "",  # info: id slug
            "file": Path(audio).name,  # info: file name
            "window_start": report.get("window_start") or "",  # info: window_start
            "window_end": report.get("window_end") or "",  # info: window_end
            "priority": 0,  # info: priority
            "status": report.get("status") or "",  # info: status
            "publication": (report.get("publication") or {}).get("status") or "",  # info: publication
        })  # info: }
    path = CANON / "stream-queue.json"  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    payload = {"items": items}  # info: set payload
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, path)  # info: os . replace
    return path  # info: return path


# ====================================================
# SECTION: function index_legacy
# What it does: Index existing markdown. Window stays empty. File mtime and path are kept. Files are not moved.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def index_legacy(voice_dir: Path, audio_dir: Path | None = None) -> dict:  # info: def index_legacy
    before_md = list(voice_dir.rglob("*.md")) if voice_dir.is_dir() else []  # info: set before_md
    before_wav = list(audio_dir.rglob("*.wav")) if audio_dir and audio_dir.is_dir() else []  # info: set before_wav
    indexed = 0  # info: set indexed
    for path in before_md:  # info: for path in before_md
        rid = report_id("legacy", str(path), "", "", "legacy")  # info: set rid
        if load(rid):  # info: if load ( rid )
            continue  # info: continue
        stamp = datetime.fromtimestamp(path.stat().st_mtime).isoformat()  # info: set stamp
        report = {  # info: set report
            "report_id": rid,  # info: report_id
            "profile": "legacy",  # info: profile
            "slug": path.name.split("_current")[0].split("_20")[0],  # info: slug
            "topic": "",  # info: topic
            "subtopic": "",  # info: subtopic
            "scope": "",  # info: scope
            "window_start": "",  # info: window_start empty
            "window_end": "",  # info: window_end empty
            "timezone": "Pacific/Honolulu",  # info: timezone
            "status": "archived",  # info: status archived
            "created_at": stamp,  # info: created_at
            "generated_at": stamp,  # info: generated_at
            "published_at": "",  # info: published_at
            "generator": "legacy",  # info: generator
            "provider": "",  # info: provider
            "model": "",  # info: model
            "generator_version": "",  # info: generator_version
            "sources": [],  # info: sources
            "observations": [],  # info: observations
            "sections": [{"heading": "Legacy", "text": path.read_text(encoding="utf-8", errors="replace").split("\n## Spoken", 1)[0][:4000]}],  # info: sections
            "spoken": [],  # info: spoken
            "owns": [],  # info: owns
            "assets": [_asset("text", str(path))],  # info: assets
            "stages": empty_stages(),  # info: stages
            "publication": {"publication_id": "pub_" + rid, "target": "youtube", "status": "not_configured", "error": "", "retry": 0},  # info: publication
            "provenance": {"legacy_path": str(path), "file_mtime": stamp, "window_from_file": False},  # info: provenance
        }  # info: }
        report["stages"]["text"] = {"status": "ready", "path": str(path), "error": "", "retry": 0}  # info: text ready
        if audio_dir is not None:  # info: if audio_dir is not None
            wav = audio_dir / (path.stem + ".wav")  # info: set wav
            if not wav.is_file():  # info: if not wav . is_file
                wav = audio_dir / "Archive" / (path.stem + ".wav")  # info: set wav archive
            if wav.is_file():  # info: if wav . is_file
                report["assets"].append(_asset("audio", str(wav)))  # info: append audio
                report["stages"]["audio"] = {"status": "ready", "path": str(wav), "error": "", "retry": 0}  # info: audio ready
        save(report)  # info: call save
        indexed += 1  # info: indexed += 1
    after_md = list(voice_dir.rglob("*.md")) if voice_dir.is_dir() else []  # info: set after_md
    after_wav = list(audio_dir.rglob("*.wav")) if audio_dir and audio_dir.is_dir() else []  # info: set after_wav
    return {"indexed": indexed, "md_before": len(before_md), "md_after": len(after_md), "wav_before": len(before_wav), "wav_after": len(after_wav)}  # info: return counts
