# ==============================================================================
# FILE: Reports/pipeline/model.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Canonical report object. The report id is the window, not the filename."""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib

GENERATOR_VERSION = "1"  # info: set GENERATOR_VERSION
STATUSES = (  # info: set STATUSES
    "scheduled", "collecting", "assembling", "generating", "generated",  # info: scheduled through generated
    "assets_pending", "assets_ready", "published", "archived", "failed", "cancelled",  # info: asset and terminal statuses
)  # info: )


# ====================================================
# SECTION: function report_id
# What it does: Stable id from profile, topic, scope, window start, and timezone. A second run keeps this id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def report_id(profile: str, topic: str, scope: str, window_start: str, timezone: str) -> str:  # info: def report_id
    raw = "|".join([profile or "", topic or "", scope or "", window_start or "", timezone or ""])  # info: set raw
    return "rpt_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]  # info: return rpt_ + hash


# ====================================================
# SECTION: function empty_stages
# What it does: Stage map. A failed stage does not erase the others.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def empty_stages() -> dict:  # info: def empty_stages
    return {  # info: return {
        name: {"status": "pending", "path": "", "error": "", "retry": 0}  # info: pending stage
        for name in ("text", "audio", "image", "video", "publication")  # info: for name in stages
    }  # info: }


# ====================================================
# SECTION: function new_report
# What it does: Build one report record. It does not write a file and it does not call a model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def new_report(profile: dict, window: dict, when: str) -> dict:  # info: def new_report
    topic = str(profile.get("topic") or "")  # info: set topic
    scope = str(profile.get("scope") or "")  # info: set scope
    start = str(window.get("window_start") or "")  # info: set start
    zone = str(window.get("timezone") or "Pacific/Honolulu")  # info: set zone
    rid = report_id(str(profile.get("id") or ""), topic, scope, start, zone)  # info: set rid
    return {  # info: return {
        "report_id": rid,  # info: "report_id" : rid
        "profile": profile.get("id") or "",  # info: "profile"
        "slug": profile.get("slug") or "",  # info: "slug"
        "topic": topic,  # info: "topic" : topic
        "subtopic": profile.get("subtopic") or "",  # info: "subtopic"
        "scope": scope,  # info: "scope" : scope
        "window_start": start,  # info: "window_start" : start
        "window_end": window.get("window_end") or "",  # info: "window_end"
        "timezone": zone,  # info: "timezone" : zone
        "status": "scheduled",  # info: "status" : "scheduled"
        "created_at": when,  # info: "created_at" : when
        "generated_at": "",  # info: "generated_at"
        "published_at": "",  # info: "published_at"
        "generator": profile.get("generator") or "deterministic",  # info: "generator"
        "provider": "",  # info: "provider"
        "model": "",  # info: "model"
        "generator_version": GENERATOR_VERSION,  # info: "generator_version"
        "sources": [],  # info: "sources"
        "observations": [],  # info: "observations"
        "sections": [],  # info: "sections"
        "spoken": [],  # info: "spoken"
        "owns": list(profile.get("owns") or []),  # info: "owns"
        "assets": [],  # info: "assets"
        "stages": empty_stages(),  # info: "stages"
        "publication": {  # info: "publication"
            "publication_id": "pub_" + rid,  # info: publication_id
            "target": "youtube",  # info: target youtube
            "status": "not_configured",  # info: status not_configured
            "error": "",  # info: error
            "retry": 0,  # info: retry
        },  # info: }
        "provenance": {"legacy_path": "", "file_mtime": "", "window_from_file": False},  # info: "provenance"
    }  # info: }
