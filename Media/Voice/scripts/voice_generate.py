# ==============================================================================
# FILE: Media/Voice/scripts/voice_generate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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

Voices (locked): Ava af_heart 1.0 (default) · Bruce am_echo 1.0 · Carly af_nova 1.0.
Output: 24 kHz, 16-bit PCM, mono WAV. Lexicon: Ava/Ayeva/Avaivy fixes + hawaiian_lexicon (verbatim G1).
Delivery (Telegram sendVoice, speaker playback, AWS radio) is NOT implemented here — OFF by design.
Env: RR_DATABASE_ROOT, RR_KOKORO_MODEL_DIR, RR_VOICE_OUT_DIR, RR_VOICE_THREADS (4), RR_VOICE_GAP_MS (180).
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import re  # info: import re
import resource  # info: import resource
import sys  # info: import sys
import time  # info: import time
import warnings  # info: import warnings
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
from hawaiian_lexicon import lexicon_entries  # noqa: E402
from speakable import speakable  # noqa: E402
import speakers  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
STORE = Path(os.environ.get("RR_KOKORO_MODEL_DIR", str(DB / "AI" / "Kokoro" / "Kokoro-82M")))  # info: set STORE
OUT_DIR = Path(os.environ.get("RR_VOICE_OUT_DIR", str(DB / "Media" / "Audio" / "Voice")))  # info: set OUT_DIR
REPORT_OUT_DIR = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))  # info: set REPORT_OUT_DIR
CLIPS_DIR = OUT_DIR / "Clips"  # info: set CLIPS_DIR
MANIFEST = CLIPS_DIR / "clips_manifest.json"  # info: set MANIFEST
SAMPLE_RATE = 24000  # info: set SAMPLE_RATE
DEFAULT_VOICE = "af_heart"  # info: set DEFAULT_VOICE
SPEEDS = {"af_heart": 1.0, "am_echo": 1.0, "af_nova": 1.0}  # info: set SPEEDS
# ====================================================
# SECTION: VOICE_ALIASES
# What it does: Set VOICE_ALIASES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
VOICE_ALIASES = {  # info: set VOICE_ALIASES
    "ara": "af_heart", "local": "af_heart", "kokoro": "af_heart", "cloud": "af_heart",  # info: "ara" : "af_heart" , "local" : "af_heart" ,
    "ava": "af_heart", "heart": "af_heart", "bruce": "am_echo", "echo": "am_echo",  # info: "ava" : "af_heart" , "heart" : "af_heart" ,
    "carly": "af_nova", "nova": "af_nova",  # info: "carly" : "af_nova" , "nova" : "af_nova" ,
}  # info: }
PERSONA_DIR = {"ava": "Ava", "bruce": "Bruce", "carly": "Carly"}  # info: set PERSONA_DIR
GAP_MS = int(os.environ.get("RR_VOICE_GAP_MS", "180"))  # info: set GAP_MS
TARGET_RMS_DB = -20.0   # speech-frame RMS target for clips and live parts (consistent joins)
PEAK_CEIL_DB = -1.5     # hard ceiling; QC fails at >= -1.0 dBFS
TRIM_DB = -45.0         # leading/trailing silence threshold (dBFS)
TRIM_KEEP_MS = 25  # info: set TRIM_KEEP_MS
FADE_MS = 8  # info: set FADE_MS
AYEVA_PHONEME = "ˈAvə"  # Ayeva / Ava = AY-vah (Kokoro US: A = /eɪ/)
_PIPELINE = None  # info: set _PIPELINE
HST_FMT = "%Y-%m-%dT%H:%M:%S%z"  # info: set HST_FMT


# ====================================================
# SECTION: function now_iso
# What it does: now iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_iso() -> str:  # info: def now_iso
    s = datetime.now().astimezone().strftime(HST_FMT)  # info: set s
    return s[:-2] + ":" + s[-2:]  # info: return s [ : - 2 ] +


# ====================================================
# SECTION: function be_polite
# What it does: be polite.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def be_polite() -> None:  # info: def be_polite
    try:  # info: try :
        cur = os.nice(0)  # info: set cur
        if cur < 10:  # info: if cur < 10 :
            os.nice(10 - cur)  # info: os . nice ( 10 - cur )
    except OSError:  # info: except OSError :
        pass  # info: pass


# ====================================================
# SECTION: function apply_lexicon
# What it does: apply lexicon.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_lexicon(pipeline) -> None:  # info: def apply_lexicon
    g2p = getattr(pipeline, "g2p", None)  # info: set g2p
    lexicon = getattr(g2p, "lexicon", None) if g2p is not None else None  # info: set lexicon
    if lexicon is None or not hasattr(lexicon, "golds"):  # info: if lexicon is None or not hasattr (
        return  # info: return
    extra = {  # info: set extra
        "Ava": AYEVA_PHONEME,  # info: "Ava" : AYEVA_PHONEME ,
        "Ayeva": AYEVA_PHONEME,  # info: "Ayeva" : AYEVA_PHONEME ,
        "Ava's": AYEVA_PHONEME + "z",  # info: "Ava's" : AYEVA_PHONEME + "z" ,
        "Ayeva's": AYEVA_PHONEME + "z",  # info: "Ayeva's" : AYEVA_PHONEME + "z" ,
        "Avaivy": AYEVA_PHONEME + "ˈIvi",  # info: "Avaivy" : AYEVA_PHONEME + "ˈIvi" ,
        "avaivy": AYEVA_PHONEME + "ˈIvi",  # info: "avaivy" : AYEVA_PHONEME + "ˈIvi" ,
    }  # info: }
    extra.update(lexicon_entries())  # info: extra . update ( lexicon_entries ( ) )
    if hasattr(lexicon, "grow_dictionary"):  # info: if hasattr ( lexicon , "grow_dictionary" ) :
        extra = lexicon.grow_dictionary(extra)  # info: set extra
    lexicon.golds.update(extra)  # info: lexicon . golds . update ( extra )


# ====================================================
# SECTION: function resolve_voice
# What it does: resolve voice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def resolve_voice(name: str | None) -> str:  # info: def resolve_voice
    raw = (name or os.getenv("KOKORO_VOICE") or DEFAULT_VOICE).strip()  # info: set raw
    return VOICE_ALIASES.get(raw.lower(), raw)  # info: return VOICE_ALIASES . get ( raw . lower


# ====================================================
# SECTION: function _pipeline
# What it does:  pipeline.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pipeline():  # info: def _pipeline
    global _PIPELINE  # info: global _PIPELINE
    if _PIPELINE is None:  # info: if _PIPELINE is None :
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")  # info: os . environ . setdefault ( "HF_HUB_DISABLE_TELEMETRY" ,
        os.environ.setdefault("HF_HUB_OFFLINE", "1")  # info: os . environ . setdefault ( "HF_HUB_OFFLINE" ,
        import torch  # info: import torch
        torch.set_num_threads(int(os.environ.get("RR_VOICE_THREADS", "4")))  # info: torch . set_num_threads ( int ( os .
        # espeak-ng ignores data paths over 160 chars; the venv copy under this Pacific path is 163.
        # Use a short user-space copy (RR_ESPEAK_DATA, default ~/.local/share/rootrecord/espeak-ng-data).
        import misaki.espeak  # noqa: F401  (sets the long venv path first)
        from phonemizer.backend.espeak.wrapper import EspeakWrapper  # info: from phonemizer . backend . espeak . wrapper
        ed = os.environ.get("RR_ESPEAK_DATA", str(Path.home() / ".local" / "share" / "rootrecord" / "espeak-ng-data"))  # info: set ed
        if (Path(ed) / "phontab").is_file():  # info: if ( Path ( ed ) / "phontab"
            EspeakWrapper.set_data_path(ed)  # info: EspeakWrapper . set_data_path ( ed )
        from kokoro import KModel, KPipeline  # info: from kokoro import KModel , KPipeline
        warnings.filterwarnings("ignore")  # info: warnings . filterwarnings ( "ignore" )
        weights, cfg = STORE / "kokoro-v1_0.pth", STORE / "config.json"  # info: weights , cfg = STORE / "kokoro-v1_0.pth" ,
        if not weights.is_file() or not cfg.is_file():  # info: if not weights . is_file ( ) or
            raise FileNotFoundError(f"Kokoro-82M missing under {STORE}")  # info: raise FileNotFoundError ( f" Kokoro-82M missing under { STORE }
        # Kokoro has no FLM/NPU build. Speech stays on CPU so /dev/accel stays free for council chat.
        model = KModel(repo_id="hexgrad/Kokoro-82M", config=str(cfg), model=str(weights)).to("cpu").eval()  # info: set model
        _PIPELINE = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", model=model, device="cpu")  # info: set _PIPELINE
        apply_lexicon(_PIPELINE)  # info: call apply_lexicon
    return _PIPELINE  # info: return _PIPELINE


# ====================================================
# SECTION: function synth
# What it does: spoken = already speakable() text. Returns float32 mono array at 24 kHz.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def synth(spoken: str, voice_name: str, rate: float):  # info: def synth
    """spoken = already speakable() text. Returns float32 mono array at 24 kHz."""  # info: """spoken = already speakable() text. Returns float32 mono array at 24 kHz."""
    import numpy as np  # info: import numpy as np
    pack = STORE / "voices" / f"{voice_name}.pt"  # info: set pack
    voice_arg = str(pack) if pack.is_file() else voice_name  # info: set voice_arg
    chunks = [np.asarray(a, dtype=np.float32) for _g, _p, a in _pipeline()(spoken, voice=voice_arg, speed=rate) if a is not None]  # info: set chunks
    if not chunks:  # info: if not chunks :
        return None  # info: return None
    return np.concatenate(chunks) if len(chunks) > 1 else chunks[0]  # info: return np . concatenate ( chunks ) if


# ---------------------------------------------------------------- audio helpers (numpy)
# ====================================================
# SECTION: function db
# What it does: db.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def db(x: float) -> float:  # info: def db
    import math  # info: import math
    return -120.0 if x <= 1e-9 else 20 * math.log10(x)  # info: return - 120.0 if x <= 1e-9 else


# ====================================================
# SECTION: function trim
# What it does: trim.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def trim(w):  # info: def trim
    import numpy as np  # info: import numpy as np
    thr = 10 ** (TRIM_DB / 20)  # info: set thr
    idx = np.flatnonzero(np.abs(w) > thr)  # info: set idx
    if idx.size == 0:  # info: if idx . size == 0 :
        return w[:0], 0, 0  # info: return w [ : 0 ] , 0
    keep = int(SAMPLE_RATE * TRIM_KEEP_MS / 1000)  # info: set keep
    a, b = max(0, idx[0] - keep), min(len(w), idx[-1] + keep + 1)  # info: a , b = max ( 0 ,
    return w[a:b], a, len(w) - b  # info: return w [ a : b ] ,


# ====================================================
# SECTION: function speech_rms
# What it does: speech rms.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speech_rms(w) -> float:  # info: def speech_rms
    import numpy as np  # info: import numpy as np
    f = int(SAMPLE_RATE * 0.02)  # info: set f
    n = len(w) // f  # info: set n
    if n == 0:  # info: if n == 0 :
        return float(np.sqrt(np.mean(w ** 2))) if len(w) else 0.0  # info: return float ( np . sqrt ( np
    frames = w[: n * f].reshape(n, f)  # info: set frames
    r = np.sqrt(np.mean(frames ** 2, axis=1))  # info: set r
    voiced = r[r > 10 ** (-50 / 20)]  # info: set voiced
    return float(np.sqrt(np.mean(voiced ** 2))) if voiced.size else float(np.sqrt(np.mean(w ** 2)))  # info: return float ( np . sqrt ( np


# ====================================================
# SECTION: function normalize
# What it does: RMS-normalize speech frames to TARGET_RMS_DB, then hard-cap the peak at PEAK_CEIL_DB; short fades.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def normalize(w):  # info: def normalize
    """RMS-normalize speech frames to TARGET_RMS_DB, then hard-cap the peak at PEAK_CEIL_DB; short fades."""  # info: """RMS-normalize speech frames to TARGET_RMS_DB, then hard-cap the peak at PEAK_CEIL_DB; short fades."""
    import numpy as np  # info: import numpy as np
    w = w.astype(np.float32)  # info: set w
    r = speech_rms(w)  # info: set r
    if r > 0:  # info: if r > 0 :
        w = w * (10 ** (TARGET_RMS_DB / 20) / r)  # info: set w
    pk = float(np.max(np.abs(w))) if len(w) else 0.0  # info: set pk
    ceil = 10 ** (PEAK_CEIL_DB / 20)  # info: set ceil
    if pk > ceil:  # info: if pk > ceil :
        w = w * (ceil / pk)  # info: set w
    fl = min(len(w) // 4, int(SAMPLE_RATE * FADE_MS / 1000))  # info: set fl
    if fl > 1:  # info: if fl > 1 :
        ramp = np.linspace(0.0, 1.0, fl, dtype=np.float32)  # info: set ramp
        w[:fl] *= ramp  # info: w [ : fl ] *= ramp
        w[-fl:] *= ramp[::-1]  # info: w [ - fl : ] *= ramp
    return w  # info: return w


# ====================================================
# SECTION: function prepare
# What it does: prepare.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def prepare(w):  # info: def prepare
    t, lead, tail = trim(w)  # info: t , lead , tail = trim (
    return normalize(t), lead, tail  # info: return normalize ( t ) , lead ,


# ====================================================
# SECTION: function write_wav
# What it does: write wav.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_wav(path: Path, w) -> None:  # info: def write_wav
    import soundfile as sf  # info: import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_name("." + path.stem + ".rendering.wav")  # info: set tmp
    sf.write(str(tmp), w, SAMPLE_RATE, subtype="PCM_16", format="WAV")  # info: sf . write ( str ( tmp )
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function qc
# What it does: qc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def qc(path: Path) -> dict:  # info: def qc
    import numpy as np  # info: import numpy as np
    import soundfile as sf  # info: import soundfile as sf
    info = sf.info(str(path))  # info: set info
    data, sr = sf.read(str(path), dtype="float32")  # info: data , sr = sf . read (
    pk = float(np.max(np.abs(data))) if len(data) else 0.0  # info: set pk
    dur = len(data) / sr if sr else 0.0  # info: set dur
    lead = int(np.argmax(np.abs(data) > 10 ** (TRIM_DB / 20))) / sr if len(data) else 0.0  # info: set lead
    res = {  # info: set res
        "sample_rate": sr, "channels": info.channels, "subtype": info.subtype,  # info: "sample_rate" : sr , "channels" : info .
        "duration_s": round(dur, 3), "peak_dbfs": round(db(pk), 2), "rms_dbfs": round(db(speech_rms(data)), 2),  # info: "duration_s" : round ( dur , 3 )
        "lead_silence_ms": round(lead * 1000),  # info: "lead_silence_ms" : round ( lead * 1000 )
    }  # info: }
    res["qc"] = "PASS" if (sr == SAMPLE_RATE and info.channels == 1 and info.subtype == "PCM_16"  # info: res [ "qc" ] = "PASS" if (
                           and dur > 0.2 and res["peak_dbfs"] < -1.0) else "FAIL"  # info: and dur > 0.2 and res [ "peak_dbfs"
    return res  # info: return res


# ====================================================
# SECTION: function sha256
# What it does: sha256.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sha256(path: Path) -> str:  # info: def sha256
    h = hashlib.sha256()  # info: set h
    with open(path, "rb") as f:  # info: with open ( path , "rb" ) as
        for b in iter(lambda: f.read(1 << 20), b""):  # info: for b in iter ( lambda : f
            h.update(b)  # info: h . update ( b )
    return h.hexdigest()  # info: return h . hexdigest ( )


# ====================================================
# SECTION: function peak_rss_mb
# What it does: peak rss mb.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def peak_rss_mb() -> int:  # info: def peak_rss_mb
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)  # info: return int ( resource . getrusage ( resource


# ====================================================
# SECTION: function versions
# What it does: versions.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def versions() -> dict:  # info: def versions
    from importlib.metadata import version  # info: from importlib . metadata import version
    out = {}  # info: set out
    for p in ("kokoro", "misaki", "torch"):  # info: for p in ( "kokoro" , "misaki" ,
        try:  # info: try :
            out[p] = version(p)  # info: out [ p ] = version ( p
        except Exception:  # info: except Exception :
            out[p] = "?"  # info: out [ p ] = "?"
    return out  # info: return out


# ====================================================
# SECTION: function norm_key
# What it does: norm key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def norm_key(text: str) -> str:  # info: def norm_key
    return re.sub(r"\s+", " ", (text or "").strip()).lower()  # info: return re . sub ( r"\s+" , " "


# ====================================================
# SECTION: function split_sentences
# What it does: split sentences.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def split_sentences(text: str) -> list[str]:  # info: def split_sentences
    body = " ".join((text or "").split())  # info: set body
    return [s for s in re.split(r"(?<=[.!?])(?<![ap]\.m\.)\s+(?=[A-Z0-9\"'])", body) if s.strip()]  # info: return [ s for s in re .


# ====================================================
# SECTION: function load_manifest
# What it does: load manifest.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_manifest() -> dict:  # info: def load_manifest
    if MANIFEST.is_file():  # info: if MANIFEST . is_file ( ) :
        try:  # info: try :
            return json.loads(MANIFEST.read_text(encoding="utf-8"))  # info: return json . loads ( MANIFEST . read_text
        except ValueError:  # info: except ValueError :
            pass  # info: pass
    return {"format": "24 kHz 16-bit PCM mono WAV", "clips": {}}  # info: return { "format" : "24 kHz 16-bit PCM mono WAV" , "clips" :


# ====================================================
# SECTION: function save_manifest
# What it does: save manifest.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_manifest(m: dict) -> None:  # info: def save_manifest
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)  # info: MANIFEST . parent . mkdir ( parents =
    m["updated"] = now_iso()  # info: m [ "updated" ] = now_iso ( )
    m["clips"] = dict(sorted(m["clips"].items()))  # info: m [ "clips" ] = dict ( sorted
    tmp = MANIFEST.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, MANIFEST)  # info: os . replace ( tmp , MANIFEST )


# ---------------------------------------------------------------- modes
# ====================================================
# SECTION: function retire_report_sidecars
# What it does: retire report sidecars.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def retire_report_sidecars(report: str) -> None:  # info: def retire_report_sidecars
    for suffix in (".read.txt", ".speak.txt"):  # info: for suffix in ( ".read.txt" , ".speak.txt" )
        side = REPORT_OUT_DIR / f"{report}_current{suffix}"  # info: set side
        if not side.is_file():  # info: if not side . is_file ( ) :
            continue  # info: continue
        stamp = datetime.fromtimestamp(side.stat().st_mtime).astimezone().strftime("%Y%m%dT%H%M")  # info: set stamp
        arch = REPORT_OUT_DIR / "Archive"  # info: set arch
        arch.mkdir(parents=True, exist_ok=True)  # info: arch . mkdir ( parents = True ,
        dest = arch / f"{report}_{stamp}{suffix}"  # info: set dest
        n = 0  # info: set n
        while dest.exists():  # info: while dest . exists ( ) :
            n += 1  # info: set n
            dest = arch / f"{report}_{stamp}-{n}{suffix}"  # info: set dest
        side.replace(dest)  # info: side . replace ( dest )


DAYPARTS = ("morning_report", "midday_report", "late_report")  # info: set DAYPARTS


# ====================================================
# SECTION: function daypart_open
# What it does: True when this rollup is the current Pacific/Honolulu daypart.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def daypart_open(report: str) -> bool:  # info: def daypart_open
    if report not in DAYPARTS:  # info: if report not in DAYPARTS
        return True  # info: return True
    from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo
    clock = datetime.now(ZoneInfo("Pacific/Honolulu"))  # info: set clock
    minute = clock.hour * 60 + clock.minute  # info: set minute
    if report == "morning_report":  # info: if report == "morning_report"
        return 9 * 60 <= minute < 12 * 60  # info: return 9 * 60 <= minute < 12 * 60
    if report == "midday_report":  # info: if report == "midday_report"
        return 12 * 60 <= minute < 21 * 60  # info: return 12 * 60 <= minute < 21 * 60
    return minute >= 21 * 60 or minute < 9 * 60  # info: return minute >= 21 * 60 or minute < 9 * 60


# ====================================================
# SECTION: function daypart_blocked
# What it does: A daypart outside its Hawaii window must not be written as _current.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def daypart_blocked(report: str, out: Path | None) -> bool:  # info: def daypart_blocked
    dest = out or (OUT_DIR / f"{report}_current.wav")  # info: set dest
    if report not in DAYPARTS or dest.name != f"{report}_current.wav":  # info: if report not in DAYPARTS or dest . name != current wav
        return False  # info: return False
    return not daypart_open(report)  # info: return not daypart_open ( report )


# ====================================================
# SECTION: function keep_only_this_daypart
# What it does: After one daypart _current is saved, remove the other two audio copies beside it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def keep_only_this_daypart(dest: Path, report: str) -> None:  # info: def keep_only_this_daypart
    if report not in DAYPARTS or dest.name != f"{report}_current.wav":  # info: if report not in DAYPARTS or dest name is not the current wav
        return  # info: return
    for other in DAYPARTS:  # info: for other in DAYPARTS
        if other == report:  # info: if other == report
            continue  # info: continue
        for ext in (".wav", ".opus", ".ogg"):  # info: for ext in ( ".wav" , ".opus" , ".ogg" )
            path = dest.parent / f"{other}_current{ext}"  # info: set path
            try:  # info: try
                path.unlink()  # info: path . unlink ( )
            except FileNotFoundError:  # info: except FileNotFoundError
                continue  # info: continue


# ====================================================
# SECTION: function publish
# What it does: publish.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def publish(report: str, w, read: str, speak: str, out: Path | None) -> Path | None:  # info: def publish
    if daypart_blocked(report, out):  # info: if daypart_blocked ( report , out )
        return None  # info: return None
    dest = out or (OUT_DIR / f"{report}_current.wav")  # info: set dest
    tmp = dest.with_name("." + dest.stem + ".new.wav")  # info: set tmp
    write_wav(tmp, w)                          # render fully first ...
    if speakers.is_current_audio(dest):  # info: if speakers . is_current_audio ( dest ) :
        speakers.retire_current(dest)          # ... then retire the old _current (G1 pattern) ...
    retire_report_sidecars(report)  # info: call retire_report_sidecars
    os.replace(tmp, dest)                      # ... and move the new one into place
    keep_only_this_daypart(dest, report)  # info: call keep_only_this_daypart
    REPORT_OUT_DIR.mkdir(parents=True, exist_ok=True)  # info: REPORT_OUT_DIR . mkdir ( parents = True ,
    (REPORT_OUT_DIR / f"{report}_current.read.txt").write_text(read.strip() + "\n", encoding="utf-8")  # info: call (
    (REPORT_OUT_DIR / f"{report}_current.speak.txt").write_text(speak.strip() + "\n", encoding="utf-8")  # info: call (
    return dest  # info: return dest


# ====================================================
# SECTION: function mode_render
# What it does: mode render.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mode_render(a) -> dict:  # info: def mode_render
    if daypart_blocked(a.report, Path(a.out) if a.out else None):  # info: if daypart_blocked ( a . report , a . out )
        return {"ok": False, "skipped": True, "detail": "outside_daypart", "report": a.report}  # info: return { "ok" : False , "skipped" : True , "detail" : "outside_daypart" }
    import numpy as np  # info: import numpy as np
    text = speakers.without_name(a.text)  # info: set text
    if not a.no_gate and not speakers.is_live(a.kind, text):  # info: if not a . no_gate and not speakers
        return {"ok": False, "skipped": True, "detail": "no_live_data", "kind": a.kind}  # info: return { "ok" : False , "skipped" :
    voice = resolve_voice(a.voice or speakers.kokoro_voice_for(a.kind))  # info: set voice
    rate = float(a.speed) if a.speed else SPEEDS.get(voice, 1.0)  # info: set rate
    spoken = speakable(text)  # info: set spoken
    t0 = time.monotonic()  # info: set t0
    w = synth(spoken, voice, rate)  # info: set w
    if w is None:  # info: if w is None :
        return {"ok": False, "detail": "no_audio"}  # info: return { "ok" : False , "detail" :
    dest = publish(a.report, np.asarray(w, dtype=np.float32), text, spoken, Path(a.out) if a.out else None)  # info: set dest
    if dest is None:  # info: if dest is None
        return {"ok": False, "skipped": True, "detail": "outside_daypart", "report": a.report}  # info: return { "ok" : False , "skipped" : True , "detail" : "outside_daypart" }
    return {"ok": True, "mode": "render", "report": a.report, "agent": speakers.agent_for(a.kind), "voice": voice,  # info: return { "ok" : True , "mode" :
            "speed": rate, "wav": str(dest), "render_s": round(time.monotonic() - t0, 2), **qc(dest)}  # info: "speed" : rate , "wav" : str (


# ====================================================
# SECTION: function mode_stitch
# What it does: mode stitch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mode_stitch(a) -> dict:  # info: def mode_stitch
    if daypart_blocked(a.report, Path(a.out) if a.out else None):  # info: if daypart_blocked ( a . report , a . out )
        return {"ok": False, "skipped": True, "detail": "outside_daypart", "report": a.report}  # info: return { "ok" : False , "skipped" : True , "detail" : "outside_daypart" }
    import numpy as np  # info: import numpy as np
    import soundfile as sf  # info: import soundfile as sf
    text = speakers.without_name(a.text)  # info: set text
    if not a.no_gate and not speakers.is_live(a.kind, text):  # info: if not a . no_gate and not speakers
        return {"ok": False, "skipped": True, "detail": "no_live_data", "kind": a.kind}  # info: return { "ok" : False , "skipped" :
    agent = speakers.agent_for(a.kind)  # info: set agent
    voice, rate = speakers.kokoro_voice_for(a.kind), speakers.speed_for(a.kind)  # info: voice , rate = speakers . kokoro_voice_for (
    persona = PERSONA_DIR[agent]  # info: set persona
    index = {}  # info: set index
    for key, c in load_manifest().get("clips", {}).items():  # info: for key , c in load_manifest ( )
        if c.get("persona") == persona and c.get("qc") == "PASS" and c.get("voice") == voice and c.get("speed") == rate and not c.get("proposed"):  # info: if c . get ( "persona" ) == persona and speed matches
            index[norm_key(c["text"])] = CLIPS_DIR / persona / f"{c['slug']}.wav"  # info: index [ norm_key ( c [ "text" ]
    gap = np.zeros(int(SAMPLE_RATE * GAP_MS / 1000), dtype=np.float32)  # info: set gap
    parts, plan, spoken_all = [], [], []  # info: parts , plan , spoken_all = [ ]
    t0 = time.monotonic()  # info: set t0
    for sent in split_sentences(text):  # info: for sent in split_sentences ( text ) :
        clip = index.get(norm_key(sent))  # info: set clip
        if clip and clip.is_file():  # info: if clip and clip . is_file ( )
            w, sr = sf.read(str(clip), dtype="float32")  # info: w , sr = sf . read (
            if sr == SAMPLE_RATE:  # info: if sr == SAMPLE_RATE :
                parts.append(w); plan.append({"clip": clip.stem}); spoken_all.append(speakable(sent))  # info: parts . append ( w ) ; plan
                continue  # info: continue
        sp = speakable(sent)  # info: set sp
        w = synth(sp, voice, rate)  # info: set w
        if w is None:  # info: if w is None :
            continue  # info: continue
        parts.append(prepare(np.asarray(w, dtype=np.float32))[0]); plan.append({"live": len(sent)}); spoken_all.append(sp)  # info: parts . append ( prepare ( np .
    if not parts:  # info: if not parts :
        return {"ok": False, "detail": "no_audio"}  # info: return { "ok" : False , "detail" :
    joined = [gap[: len(gap) // 2]]  # info: set joined
    for i, w in enumerate(parts):  # info: for i , w in enumerate ( parts
        joined += ([gap] if i else []) + [w]  # info: set joined
    joined.append(gap[: len(gap) // 2])  # info: joined . append ( gap [ : len
    dest = publish(a.report, np.concatenate(joined), text, " ".join(spoken_all), Path(a.out) if a.out else None)  # info: set dest
    if dest is None:  # info: if dest is None
        return {"ok": False, "skipped": True, "detail": "outside_daypart", "report": a.report}  # info: return { "ok" : False , "skipped" : True , "detail" : "outside_daypart" }
    return {"ok": True, "mode": "stitch", "report": a.report, "agent": agent, "voice": voice, "speed": rate,  # info: return { "ok" : True , "mode" :
            "wav": str(dest), "clips_used": sum(1 for p in plan if "clip" in p),  # info: "wav" : str ( dest ) , "clips_used"
            "live_sentences": sum(1 for p in plan if "live" in p), "model_loaded": _PIPELINE is not None,  # info: "live_sentences" : sum ( 1 for p in
            "render_s": round(time.monotonic() - t0, 2), **qc(dest)}  # info: "render_s" : round ( time . monotonic (


# ====================================================
# SECTION: function mode_clips
# What it does: mode clips.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mode_clips(a) -> dict:  # info: def mode_clips
    import numpy as np  # info: import numpy as np
    from clip_catalog import catalog  # info: from clip_catalog import catalog
    man = load_manifest()  # info: set man
    ver = versions()  # info: set ver
    done, failed, skipped, t_all = [], [], 0, time.monotonic()  # info: done , failed , skipped , t_all =
    for c in catalog():  # info: for c in catalog ( ) :
        if a.persona and c["persona"].lower() != a.persona.lower():  # info: if a . persona and c [ "persona"
            continue  # info: continue
        if getattr(a, "slug", "") and c["slug"] != a.slug:  # info: if one slug was named , render only that clip
            continue  # info: continue
        agent = c["persona"].lower()  # info: set agent
        voice, rate = speakers.AGENTS[agent]["kokoro"], speakers.AGENTS[agent]["speed"]  # info: voice , rate = speakers . AGENTS [
        key = f"{c['persona']}/{c['slug']}"  # info: set key
        path = CLIPS_DIR / c["persona"] / f"{c['slug']}.wav"  # info: set path
        old = man["clips"].get(key)  # info: set old
        if a.only_missing and old and old.get("text") == c["text"] and old.get("qc") == "PASS" and path.is_file():  # info: if a . only_missing and old and old
            skipped += 1  # info: set skipped
            continue  # info: continue
        spoken = c.get("spoken") or speakable(c["text"])  # catalog "spoken" = explicit respelling (PROPOSED names)
        t0 = time.monotonic()  # info: set t0
        w = synth(spoken, voice, rate)  # info: set w
        if w is None:  # info: if w is None :
            failed.append(key)  # info: failed . append ( key )
            continue  # info: continue
        w, lead, tail = prepare(np.asarray(w, dtype=np.float32))  # info: w , lead , tail = prepare (
        write_wav(path, w)  # info: call write_wav
        q = qc(path)  # info: set q
        man["clips"][key] = {  # info: man [ "clips" ] [ key ] =
            "slug": c["slug"], "persona": c["persona"], "kinds": c.get("kinds", []), "text": c["text"],  # info: "slug" : c [ "slug" ] , "persona"
            "spoken": spoken, "voice": voice, "speed": rate, "sha256": sha256(path), **q,  # info: "spoken" : spoken , "voice" : voice ,
            "trimmed_ms": {"lead": round(lead * 1000 / SAMPLE_RATE), "tail": round(tail * 1000 / SAMPLE_RATE)},  # info: "trimmed_ms" : { "lead" : round ( lead
            "render_s": round(time.monotonic() - t0, 2), "rendered": now_iso(), "engine": ver,  # info: "render_s" : round ( time . monotonic (
            "source": c.get("source", ""), "proposed": bool(c.get("proposed")),  # info: "source" : c . get ( "source" ,
        }  # info: }
        (done if q["qc"] == "PASS" else failed).append(key)  # info: call (
        save_manifest(man)  # after each clip: an interrupted batch keeps its progress
    return {"ok": not failed, "mode": "clips", "rendered": len(done), "failed": failed, "skipped": skipped,  # info: return { "ok" : not failed , "mode"
            "total_s": round(time.monotonic() - t_all, 2), "manifest": str(MANIFEST)}  # info: "total_s" : round ( time . monotonic (


# ====================================================
# SECTION: function mode_asr
# What it does: mode asr.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mode_asr(a) -> dict:  # info: def mode_asr
    import voice_asr_check  # info: import voice_asr_check
    man = load_manifest()  # info: set man
    res = voice_asr_check.run(man, CLIPS_DIR, DB, limit=a.limit)  # info: set res
    save_manifest(man)  # info: call save_manifest
    return {"ok": True, "mode": "asr", **res}  # info: return { "ok" : True , "mode" :


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    be_polite()  # info: call be_polite
    p = argparse.ArgumentParser(description="G3 Kokoro-82M voice renderer (non-resident)")  # info: set p
    p.add_argument("mode", choices=["render", "stitch", "clips", "asr"])  # info: p . add_argument ( "mode" , choices =
    p.add_argument("--report", default="voice_test")  # info: p . add_argument ( "--report" , default =
    p.add_argument("--kind", default="ava")  # info: p . add_argument ( "--kind" , default =
    p.add_argument("--text", default="")  # info: p . add_argument ( "--text" , default =
    p.add_argument("--text-file")  # info: p . add_argument ( "--text-file" )
    p.add_argument("--out")  # info: p . add_argument ( "--out" )
    p.add_argument("--voice")  # info: p . add_argument ( "--voice" )
    p.add_argument("--speed", type=float)  # info: p . add_argument ( "--speed" , type =
    p.add_argument("--no-gate", action="store_true", help="skip the G1 live-facts gate (tests only)")  # info: p . add_argument ( "--no-gate" , action =
    p.add_argument("--catalog", action="store_true")  # info: p . add_argument ( "--catalog" , action =
    p.add_argument("--persona")  # info: p . add_argument ( "--persona" )
    p.add_argument("--only-missing", action="store_true")  # info: p . add_argument ( "--only-missing" , action =
    p.add_argument("--slug", default="", help="clips: render this one slug")  # info: p . add_argument ( "--slug" , default = ""
    p.add_argument("--limit", type=int, default=0, help="asr: max clips to transcribe (0 = all)")  # info: p . add_argument ( "--limit" , type =
    a = p.parse_args()  # info: set a
    if a.text_file:  # info: if a . text_file :
        a.text = Path(a.text_file).read_text(encoding="utf-8")  # info: a . text = Path ( a .
    if a.mode not in ("clips", "asr") and not a.text.strip():  # info: if a . mode not in ( "clips"
        print(json.dumps({"ok": False, "detail": "empty_text"}))  # info: call print
        return 1  # info: return 1
    if a.mode not in ("clips", "asr") and not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", a.report):  # info: if a . mode not in ( "clips"
        print(json.dumps({"ok": False, "detail": "report name must be lower_snake_case"}))  # info: call print
        return 2  # info: return 2
    t0 = time.monotonic()  # info: set t0
    res = {"render": mode_render, "stitch": mode_stitch, "clips": mode_clips, "asr": mode_asr}[a.mode](a)  # info: set res
    res["wall_s"] = round(time.monotonic() - t0, 2)  # info: res [ "wall_s" ] = round ( time
    res["peak_rss_mb"] = peak_rss_mb()  # info: res [ "peak_rss_mb" ] = peak_rss_mb ( )
    print(json.dumps(res, ensure_ascii=False))  # info: call print
    return 0 if res.get("ok") or res.get("skipped") else 1  # info: return 0 if res . get ( "ok"


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
