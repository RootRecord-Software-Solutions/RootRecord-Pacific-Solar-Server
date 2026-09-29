#!/usr/bin/env python3
"""G3 Kokoro-82M voice renderer (port of G1 old skills/kokoro/scripts/generate.py). Non-resident: one process per job.

Run through voice-render.sh (single-flight inference lock + nice 10), with Media/Voice/.venv python.

  render  --report NAME --kind KIND (--text T | --text-file F) [--out WAV]
          Whole text in one Kokoro pass (G1 behaviour). Writes <OUT_DIR>/<report>_current.wav + sidecars,
          after retiring the old one to Archive/<report>_YYYYMMDDTHHMM.wav.
  stitch  --report NAME --kind KIND (--text T | --text-file F)
          Sentence-level phrase cache: each sentence that exactly matches a QC-passed clip for this
          persona in clips_manifest.json is reused; every other sentence (numbers, names, values) is
          rendered live. Missing clip -> the whole sentence is rendered live. The model is only
          loaded if at least one sentence is live.
  asr     [--limit N]   whisper-tiny round trip of the clips (QC; results stored in the manifest)
  clips   --catalog [--persona Ava|Bruce|Carly] [--only-missing]
          Pre-render the phrase catalog (clip_catalog.py) into Clips/<Persona>/<slug>.wav with QC and
          update Clips/clips_manifest.json.

Voices (locked, from G1): Ava af_heart 0.82 (default) · Bruce am_echo 0.92 · Carly af_nova 0.74.
Output: 24 kHz, 16-bit PCM, mono WAV. Lexicon: Ava/Ayeva/Avaivy fixes + hawaiian_lexicon (verbatim G1).
Delivery (Telegram sendVoice, speaker playback, AWS radio) is NOT implemented here — OFF by design.
Env: RR_DATABASE_ROOT, RR_KOKORO_MODEL_DIR, RR_VOICE_OUT_DIR, RR_VOICE_THREADS (4), RR_VOICE_GAP_MS (180).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import resource
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hawaiian_lexicon import lexicon_entries  # noqa: E402
from speakable import speakable  # noqa: E402
import speakers  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
STORE = Path(os.environ.get("RR_KOKORO_MODEL_DIR", str(DB / "AI" / "Kokoro" / "Kokoro-82M")))
OUT_DIR = Path(os.environ.get("RR_VOICE_OUT_DIR", str(DB / "Media" / "Audio" / "Voice")))
CLIPS_DIR = OUT_DIR / "Clips"
MANIFEST = CLIPS_DIR / "clips_manifest.json"
SAMPLE_RATE = 24000
DEFAULT_VOICE = "af_heart"
SPEEDS = {"af_heart": 0.82, "am_echo": 0.92, "af_nova": 0.74}
VOICE_ALIASES = {
    "ara": "af_heart", "local": "af_heart", "kokoro": "af_heart", "cloud": "af_heart",
    "ava": "af_heart", "heart": "af_heart", "bruce": "am_echo", "echo": "am_echo",
    "carly": "af_nova", "nova": "af_nova",
}
PERSONA_DIR = {"ava": "Ava", "bruce": "Bruce", "carly": "Carly"}
GAP_MS = int(os.environ.get("RR_VOICE_GAP_MS", "180"))
TARGET_RMS_DB = -20.0   # speech-frame RMS target for clips and live parts (consistent joins)
PEAK_CEIL_DB = -1.5     # hard ceiling; QC fails at >= -1.0 dBFS
TRIM_DB = -45.0         # leading/trailing silence threshold (dBFS)
TRIM_KEEP_MS = 25
FADE_MS = 8
AYEVA_PHONEME = "ˈAvə"  # Ayeva / Ava = AY-vah (Kokoro US: A = /eɪ/)
_PIPELINE = None
HST_FMT = "%Y-%m-%dT%H:%M:%S%z"


def now_iso() -> str:
    s = datetime.now().astimezone().strftime(HST_FMT)
    return s[:-2] + ":" + s[-2:]


def be_polite() -> None:
    try:
        cur = os.nice(0)
        if cur < 10:
            os.nice(10 - cur)
    except OSError:
        pass


def apply_lexicon(pipeline) -> None:
    g2p = getattr(pipeline, "g2p", None)
    lexicon = getattr(g2p, "lexicon", None) if g2p is not None else None
    if lexicon is None or not hasattr(lexicon, "golds"):
        return
    extra = {
        "Ava": AYEVA_PHONEME,
        "Ayeva": AYEVA_PHONEME,
        "Ava's": AYEVA_PHONEME + "z",
        "Ayeva's": AYEVA_PHONEME + "z",
        "Avaivy": AYEVA_PHONEME + "ˈIvi",
        "avaivy": AYEVA_PHONEME + "ˈIvi",
    }
    extra.update(lexicon_entries())
    if hasattr(lexicon, "grow_dictionary"):
        extra = lexicon.grow_dictionary(extra)
    lexicon.golds.update(extra)


def resolve_voice(name: str | None) -> str:
    raw = (name or os.getenv("KOKORO_VOICE") or DEFAULT_VOICE).strip()
    return VOICE_ALIASES.get(raw.lower(), raw)


def _pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        import torch
        torch.set_num_threads(int(os.environ.get("RR_VOICE_THREADS", "4")))
        # espeak-ng ignores data paths over 160 chars; the venv copy under this Pacific path is 163.
        # Use a short user-space copy (RR_ESPEAK_DATA, default ~/.local/share/rootrecord/espeak-ng-data).
        import misaki.espeak  # noqa: F401  (sets the long venv path first)
        from phonemizer.backend.espeak.wrapper import EspeakWrapper
        ed = os.environ.get("RR_ESPEAK_DATA", str(Path.home() / ".local" / "share" / "rootrecord" / "espeak-ng-data"))
        if (Path(ed) / "phontab").is_file():
            EspeakWrapper.set_data_path(ed)
        from kokoro import KModel, KPipeline
        warnings.filterwarnings("ignore")
        weights, cfg = STORE / "kokoro-v1_0.pth", STORE / "config.json"
        if not weights.is_file() or not cfg.is_file():
            raise FileNotFoundError(f"Kokoro-82M missing under {STORE}")
        model = KModel(repo_id="hexgrad/Kokoro-82M", config=str(cfg), model=str(weights)).to("cpu").eval()
        _PIPELINE = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", model=model, device="cpu")
        apply_lexicon(_PIPELINE)
    return _PIPELINE


def synth(spoken: str, voice_name: str, rate: float):
    """spoken = already speakable() text. Returns float32 mono array at 24 kHz."""
    import numpy as np
    pack = STORE / "voices" / f"{voice_name}.pt"
    voice_arg = str(pack) if pack.is_file() else voice_name
    chunks = [np.asarray(a, dtype=np.float32) for _g, _p, a in _pipeline()(spoken, voice=voice_arg, speed=rate) if a is not None]
    if not chunks:
        return None
    return np.concatenate(chunks) if len(chunks) > 1 else chunks[0]


# ---------------------------------------------------------------- audio helpers (numpy)
def db(x: float) -> float:
    import math
    return -120.0 if x <= 1e-9 else 20 * math.log10(x)


def trim(w):
    import numpy as np
    thr = 10 ** (TRIM_DB / 20)
    idx = np.flatnonzero(np.abs(w) > thr)
    if idx.size == 0:
        return w[:0], 0, 0
    keep = int(SAMPLE_RATE * TRIM_KEEP_MS / 1000)
    a, b = max(0, idx[0] - keep), min(len(w), idx[-1] + keep + 1)
    return w[a:b], a, len(w) - b


def speech_rms(w) -> float:
    import numpy as np
    f = int(SAMPLE_RATE * 0.02)
    n = len(w) // f
    if n == 0:
        return float(np.sqrt(np.mean(w ** 2))) if len(w) else 0.0
    frames = w[: n * f].reshape(n, f)
    r = np.sqrt(np.mean(frames ** 2, axis=1))
    voiced = r[r > 10 ** (-50 / 20)]
    return float(np.sqrt(np.mean(voiced ** 2))) if voiced.size else float(np.sqrt(np.mean(w ** 2)))


def normalize(w):
    """RMS-normalize speech frames to TARGET_RMS_DB, then hard-cap the peak at PEAK_CEIL_DB; short fades."""
    import numpy as np
    w = w.astype(np.float32)
    r = speech_rms(w)
    if r > 0:
        w = w * (10 ** (TARGET_RMS_DB / 20) / r)
    pk = float(np.max(np.abs(w))) if len(w) else 0.0
    ceil = 10 ** (PEAK_CEIL_DB / 20)
    if pk > ceil:
        w = w * (ceil / pk)
    fl = min(len(w) // 4, int(SAMPLE_RATE * FADE_MS / 1000))
    if fl > 1:
        ramp = np.linspace(0.0, 1.0, fl, dtype=np.float32)
        w[:fl] *= ramp
        w[-fl:] *= ramp[::-1]
    return w


def prepare(w):
    t, lead, tail = trim(w)
    return normalize(t), lead, tail


def write_wav(path: Path, w) -> None:
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.stem + ".rendering.wav")
    sf.write(str(tmp), w, SAMPLE_RATE, subtype="PCM_16", format="WAV")
    os.replace(tmp, path)


def qc(path: Path) -> dict:
    import numpy as np
    import soundfile as sf
    info = sf.info(str(path))
    data, sr = sf.read(str(path), dtype="float32")
    pk = float(np.max(np.abs(data))) if len(data) else 0.0
    dur = len(data) / sr if sr else 0.0
    lead = int(np.argmax(np.abs(data) > 10 ** (TRIM_DB / 20))) / sr if len(data) else 0.0
    res = {
        "sample_rate": sr, "channels": info.channels, "subtype": info.subtype,
        "duration_s": round(dur, 3), "peak_dbfs": round(db(pk), 2), "rms_dbfs": round(db(speech_rms(data)), 2),
        "lead_silence_ms": round(lead * 1000),
    }
    res["qc"] = "PASS" if (sr == SAMPLE_RATE and info.channels == 1 and info.subtype == "PCM_16"
                           and dur > 0.2 and res["peak_dbfs"] < -1.0) else "FAIL"
    return res


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def peak_rss_mb() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)


def versions() -> dict:
    from importlib.metadata import version
    out = {}
    for p in ("kokoro", "misaki", "torch"):
        try:
            out[p] = version(p)
        except Exception:
            out[p] = "?"
    return out


def norm_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def split_sentences(text: str) -> list[str]:
    body = " ".join((text or "").split())
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", body) if s.strip()]


def load_manifest() -> dict:
    if MANIFEST.is_file():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"format": "24 kHz 16-bit PCM mono WAV", "clips": {}}


def save_manifest(m: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    m["updated"] = now_iso()
    m["clips"] = dict(sorted(m["clips"].items()))
    tmp = MANIFEST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, MANIFEST)


# ---------------------------------------------------------------- modes
def publish(report: str, w, read: str, speak: str, out: Path | None) -> Path:
    dest = out or (OUT_DIR / f"{report}_current.wav")
    tmp = dest.with_name("." + dest.stem + ".new.wav")
    write_wav(tmp, w)                          # render fully first ...
    if speakers.is_current_audio(dest):
        speakers.retire_current(dest)          # ... then retire the old _current (G1 pattern) ...
    os.replace(tmp, dest)                      # ... and move the new one into place
    dest.with_suffix(".read.txt").write_text(read.strip() + "\n", encoding="utf-8")
    dest.with_suffix(".speak.txt").write_text(speak.strip() + "\n", encoding="utf-8")
    return dest


def mode_render(a) -> dict:
    import numpy as np
    text = speakers.without_name(a.text)
    if not a.no_gate and not speakers.is_live(a.kind, text):
        return {"ok": False, "skipped": True, "detail": "no_live_data", "kind": a.kind}
    voice = resolve_voice(a.voice or speakers.kokoro_voice_for(a.kind))
    rate = float(a.speed) if a.speed else SPEEDS.get(voice, 1.0)
    spoken = speakable(text)
    t0 = time.monotonic()
    w = synth(spoken, voice, rate)
    if w is None:
        return {"ok": False, "detail": "no_audio"}
    dest = publish(a.report, np.asarray(w, dtype=np.float32), text, spoken, Path(a.out) if a.out else None)
    return {"ok": True, "mode": "render", "report": a.report, "agent": speakers.agent_for(a.kind), "voice": voice,
            "speed": rate, "wav": str(dest), "render_s": round(time.monotonic() - t0, 2), **qc(dest)}


def mode_stitch(a) -> dict:
    import numpy as np
    import soundfile as sf
    text = speakers.without_name(a.text)
    if not a.no_gate and not speakers.is_live(a.kind, text):
        return {"ok": False, "skipped": True, "detail": "no_live_data", "kind": a.kind}
    agent = speakers.agent_for(a.kind)
    voice, rate = speakers.kokoro_voice_for(a.kind), speakers.speed_for(a.kind)
    persona = PERSONA_DIR[agent]
    index = {}
    for key, c in load_manifest().get("clips", {}).items():
        if c.get("persona") == persona and c.get("qc") == "PASS" and c.get("voice") == voice:
            index[norm_key(c["text"])] = CLIPS_DIR / persona / f"{c['slug']}.wav"
    gap = np.zeros(int(SAMPLE_RATE * GAP_MS / 1000), dtype=np.float32)
    parts, plan, spoken_all = [], [], []
    t0 = time.monotonic()
    for sent in split_sentences(text):
        clip = index.get(norm_key(sent))
        if clip and clip.is_file():
            w, sr = sf.read(str(clip), dtype="float32")
            if sr == SAMPLE_RATE:
                parts.append(w); plan.append({"clip": clip.stem}); spoken_all.append(speakable(sent))
                continue
        sp = speakable(sent)
        w = synth(sp, voice, rate)
        if w is None:
            continue
        parts.append(prepare(np.asarray(w, dtype=np.float32))[0]); plan.append({"live": len(sent)}); spoken_all.append(sp)
    if not parts:
        return {"ok": False, "detail": "no_audio"}
    joined = [gap[: len(gap) // 2]]
    for i, w in enumerate(parts):
        joined += ([gap] if i else []) + [w]
    joined.append(gap[: len(gap) // 2])
    dest = publish(a.report, np.concatenate(joined), text, " ".join(spoken_all), Path(a.out) if a.out else None)
    return {"ok": True, "mode": "stitch", "report": a.report, "agent": agent, "voice": voice, "speed": rate,
            "wav": str(dest), "clips_used": sum(1 for p in plan if "clip" in p),
            "live_sentences": sum(1 for p in plan if "live" in p), "model_loaded": _PIPELINE is not None,
            "render_s": round(time.monotonic() - t0, 2), **qc(dest)}


def mode_clips(a) -> dict:
    import numpy as np
    from clip_catalog import catalog
    man = load_manifest()
    ver = versions()
    done, failed, skipped, t_all = [], [], 0, time.monotonic()
    for c in catalog():
        if a.persona and c["persona"].lower() != a.persona.lower():
            continue
        agent = c["persona"].lower()
        voice, rate = speakers.AGENTS[agent]["kokoro"], speakers.AGENTS[agent]["speed"]
        key = f"{c['persona']}/{c['slug']}"
        path = CLIPS_DIR / c["persona"] / f"{c['slug']}.wav"
        old = man["clips"].get(key)
        if a.only_missing and old and old.get("text") == c["text"] and old.get("qc") == "PASS" and path.is_file():
            skipped += 1
            continue
        spoken = speakable(c["text"])
        t0 = time.monotonic()
        w = synth(spoken, voice, rate)
        if w is None:
            failed.append(key)
            continue
        w, lead, tail = prepare(np.asarray(w, dtype=np.float32))
        write_wav(path, w)
        q = qc(path)
        man["clips"][key] = {
            "slug": c["slug"], "persona": c["persona"], "kinds": c.get("kinds", []), "text": c["text"],
            "spoken": spoken, "voice": voice, "speed": rate, "sha256": sha256(path), **q,
            "trimmed_ms": {"lead": round(lead * 1000 / SAMPLE_RATE), "tail": round(tail * 1000 / SAMPLE_RATE)},
            "render_s": round(time.monotonic() - t0, 2), "rendered": now_iso(), "engine": ver,
            "source": c.get("source", ""),
        }
        (done if q["qc"] == "PASS" else failed).append(key)
        save_manifest(man)  # after each clip: an interrupted batch keeps its progress
    return {"ok": not failed, "mode": "clips", "rendered": len(done), "failed": failed, "skipped": skipped,
            "total_s": round(time.monotonic() - t_all, 2), "manifest": str(MANIFEST)}


def mode_asr(a) -> dict:
    import voice_asr_check
    man = load_manifest()
    res = voice_asr_check.run(man, CLIPS_DIR, DB, limit=a.limit)
    save_manifest(man)
    return {"ok": True, "mode": "asr", **res}


def main() -> int:
    be_polite()
    p = argparse.ArgumentParser(description="G3 Kokoro-82M voice renderer (non-resident)")
    p.add_argument("mode", choices=["render", "stitch", "clips", "asr"])
    p.add_argument("--report", default="voice_test")
    p.add_argument("--kind", default="ava")
    p.add_argument("--text", default="")
    p.add_argument("--text-file")
    p.add_argument("--out")
    p.add_argument("--voice")
    p.add_argument("--speed", type=float)
    p.add_argument("--no-gate", action="store_true", help="skip the G1 live-facts gate (tests only)")
    p.add_argument("--catalog", action="store_true")
    p.add_argument("--persona")
    p.add_argument("--only-missing", action="store_true")
    p.add_argument("--limit", type=int, default=0, help="asr: max clips to transcribe (0 = all)")
    a = p.parse_args()
    if a.text_file:
        a.text = Path(a.text_file).read_text(encoding="utf-8")
    if a.mode not in ("clips", "asr") and not a.text.strip():
        print(json.dumps({"ok": False, "detail": "empty_text"}))
        return 1
    if a.mode not in ("clips", "asr") and not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", a.report):
        print(json.dumps({"ok": False, "detail": "report name must be lower_snake_case"}))
        return 2
    t0 = time.monotonic()
    res = {"render": mode_render, "stitch": mode_stitch, "clips": mode_clips, "asr": mode_asr}[a.mode](a)
    res["wall_s"] = round(time.monotonic() - t0, 2)
    res["peak_rss_mb"] = peak_rss_mb()
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("ok") or res.get("skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
