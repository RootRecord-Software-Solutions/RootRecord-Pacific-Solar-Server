# ==============================================================================
# FILE: Media/Voice/scripts/voice_asr_check.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""On-demand ASR round-trip QC for phrase clips (whisper tiny, CPU, non-resident).

Called as `voice-render.sh asr [--limit N]` (voice_generate.py dispatches here), so it holds the
same single-flight lock and nice 10. Loads whisper tiny once, transcribes the clips in
clips_manifest.json, stores {"asr": {...}} per clip, then exits (model freed).
Model file: Database/AI/Whisper/tiny.pt (git-ignored *.pt). RR_WHISPER_DIR overrides.
Score = difflib word ratio between the expected text (or its speakable respelling, whichever is higher) and the transcript, after lower-casing,
dropping punctuation and turning clock digits ("3:30 p.m.") into words. >= 0.8 -> "match",
otherwise "review" (goes on the manual listen list). Hawaiian respellings are expected to
land in "review" — ASR cannot judge them; Alexander's ear is the gate for those.
Added 2026-09-29 (g3-voice-ailog).
"""
from __future__ import annotations  # info: from __future__ import annotations

import difflib  # info: import difflib
import os  # info: import os
import re  # info: import re
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path

from speakable import spoken_clock  # info: from speakable import spoken_clock

_CLOCK = re.compile(r"\b(\d{1,2})(?:[:.]?(\d{2}))?\s*([ap])\.?\s*m\b\.?", re.I)  # info: set _CLOCK


# ====================================================
# SECTION: function _norm
# What it does:  norm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _norm(text: str) -> list[str]:  # info: def _norm
    def clock(m):  # info: def clock
        h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3).lower()  # info: h , mi , ap = int (
        h24 = (h % 12) + (12 if ap == "p" else 0)  # info: set h24
        return spoken_clock(h24, mi)  # info: return spoken_clock ( h24 , mi )
    t = _CLOCK.sub(clock, text or "")  # info: set t
    t = t.lower().replace("p.m.", "pm").replace("a.m.", "am").replace("’", "'")  # info: set t
    return re.findall(r"[a-z0-9']+", t)  # info: return re . findall ( r"[a-z0-9']+" , t


# ====================================================
# SECTION: function score
# What it does: score.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def score(expected: str, heard: str) -> float:  # info: def score
    return round(difflib.SequenceMatcher(None, _norm(expected), _norm(heard)).ratio(), 3)  # info: return round ( difflib . SequenceMatcher ( None


# ====================================================
# SECTION: function best_score
# What it does: Against the written text and the speakable() respelling; the better one counts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def best_score(c: dict, heard: str) -> float:  # info: def best_score
    """Against the written text and the speakable() respelling; the better one counts."""  # info: """Against the written text and the speakable() respelling; the better one counts."""
    return max(score(c["text"], heard), score(c.get("spoken") or c["text"], heard))  # info: return max ( score ( c [ "text"


# ====================================================
# SECTION: function rescore
# What it does: Re-score stored transcripts (no model load).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def rescore(manifest: dict) -> dict:  # info: def rescore
    """Re-score stored transcripts (no model load)."""  # info: """Re-score stored transcripts (no model load)."""
    n = match = 0  # info: set n
    for c in manifest["clips"].values():  # info: for c in manifest [ "clips" ] .
        a = c.get("asr")  # info: set a
        if not a:  # info: if not a :
            continue  # info: continue
        a["score"] = best_score(c, a["heard"])  # info: a [ "score" ] = best_score ( c
        a["verdict"] = "match" if a["score"] >= 0.8 else "review"  # info: a [ "verdict" ] = "match" if a
        n += 1  # info: set n
        match += a["verdict"] == "match"  # info: set match
    return {"asr_clips": n, "asr_match": match, "asr_review": n - match}  # info: return { "asr_clips" : n , "asr_match" :


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run(manifest: dict, clips_dir: Path, db_root: Path, limit: int = 0) -> dict:  # info: def run
    import numpy as np  # info: import numpy as np
    import soundfile as sf  # info: import soundfile as sf
    import torch  # info: import torch
    import whisper  # info: import whisper
    torch.set_num_threads(int(os.environ.get("RR_VOICE_THREADS", "4")))  # info: torch . set_num_threads ( int ( os .
    pacific = Path(__file__).resolve().parents[3]  # info: Pacific server root
    root = Path(os.environ.get("RR_WHISPER_DIR", str(pacific / "AI" / "Whisper")))  # info: Whisper bank on Pacific AI/
    root.mkdir(parents=True, exist_ok=True)  # info: root . mkdir ( parents = True ,
    t0 = time.monotonic()  # info: set t0
    model = whisper.load_model("tiny", device="cpu", download_root=str(root))  # info: set model
    load_s = round(time.monotonic() - t0, 2)  # info: set load_s
    n = match = 0  # info: set n
    t1 = time.monotonic()  # info: set t1
    for key, c in manifest["clips"].items():  # info: for key , c in manifest [ "clips"
        if limit and n >= limit:  # info: if limit and n >= limit :
            break  # info: break
        path = clips_dir / c["persona"] / f"{c['slug']}.wav"  # info: set path
        if not path.is_file():  # info: if not path . is_file ( ) :
            continue  # info: continue
        w, sr = sf.read(str(path), dtype="float32")  # info: w , sr = sf . read (
        x = np.interp(np.arange(0, len(w), sr / 16000.0), np.arange(len(w)), w).astype(np.float32)  # info: set x
        heard = whisper.transcribe(model, x, language="en", fp16=False, temperature=0.0,  # info: set heard
                                   condition_on_previous_text=False)["text"].strip()  # info: set condition_on_previous_text
        s = best_score(c, heard)  # info: set s
        c["asr"] = {"engine": "whisper-tiny", "heard": heard, "score": s, "verdict": "match" if s >= 0.8 else "review"}  # info: c [ "asr" ] = { "engine" :
        n += 1  # info: set n
        match += s >= 0.8  # info: set match
    return {"asr_clips": n, "asr_match": match, "asr_review": n - match, "whisper_load_s": load_s,  # info: return { "asr_clips" : n , "asr_match" :
            "asr_s": round(time.monotonic() - t1, 2)}  # info: "asr_s" : round ( time . monotonic (
