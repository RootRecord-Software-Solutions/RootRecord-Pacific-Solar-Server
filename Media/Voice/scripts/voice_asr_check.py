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
from __future__ import annotations

import difflib
import os
import re
import time
from pathlib import Path

from speakable import spoken_clock

_CLOCK = re.compile(r"\b(\d{1,2})(?:[:.]?(\d{2}))?\s*([ap])\.?\s*m\b\.?", re.I)


def _norm(text: str) -> list[str]:
    def clock(m):
        h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3).lower()
        h24 = (h % 12) + (12 if ap == "p" else 0)
        return spoken_clock(h24, mi)
    t = _CLOCK.sub(clock, text or "")
    t = t.lower().replace("p.m.", "pm").replace("a.m.", "am").replace("’", "'")
    return re.findall(r"[a-z0-9']+", t)


def score(expected: str, heard: str) -> float:
    return round(difflib.SequenceMatcher(None, _norm(expected), _norm(heard)).ratio(), 3)


def best_score(c: dict, heard: str) -> float:
    """Against the written text and the speakable() respelling; the better one counts."""
    return max(score(c["text"], heard), score(c.get("spoken") or c["text"], heard))


def rescore(manifest: dict) -> dict:
    """Re-score stored transcripts (no model load)."""
    n = match = 0
    for c in manifest["clips"].values():
        a = c.get("asr")
        if not a:
            continue
        a["score"] = best_score(c, a["heard"])
        a["verdict"] = "match" if a["score"] >= 0.8 else "review"
        n += 1
        match += a["verdict"] == "match"
    return {"asr_clips": n, "asr_match": match, "asr_review": n - match}


def run(manifest: dict, clips_dir: Path, db_root: Path, limit: int = 0) -> dict:
    import numpy as np
    import soundfile as sf
    import torch
    import whisper
    torch.set_num_threads(int(os.environ.get("RR_VOICE_THREADS", "4")))
    root = Path(os.environ.get("RR_WHISPER_DIR", str(db_root / "AI" / "Whisper")))
    root.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    model = whisper.load_model("tiny", device="cpu", download_root=str(root))
    load_s = round(time.monotonic() - t0, 2)
    n = match = 0
    t1 = time.monotonic()
    for key, c in manifest["clips"].items():
        if limit and n >= limit:
            break
        path = clips_dir / c["persona"] / f"{c['slug']}.wav"
        if not path.is_file():
            continue
        w, sr = sf.read(str(path), dtype="float32")
        x = np.interp(np.arange(0, len(w), sr / 16000.0), np.arange(len(w)), w).astype(np.float32)
        heard = whisper.transcribe(model, x, language="en", fp16=False, temperature=0.0,
                                   condition_on_previous_text=False)["text"].strip()
        s = best_score(c, heard)
        c["asr"] = {"engine": "whisper-tiny", "heard": heard, "score": s, "verdict": "match" if s >= 0.8 else "review"}
        n += 1
        match += s >= 0.8
    return {"asr_clips": n, "asr_match": match, "asr_review": n - match, "whisper_load_s": load_s,
            "asr_s": round(time.monotonic() - t1, 2)}
