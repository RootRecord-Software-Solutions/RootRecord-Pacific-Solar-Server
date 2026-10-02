# ==============================================================================
# FILE: Media/Voice/scripts/hourly_chimes.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Prebuild 48 chimes, every hour and half hour. Ava, Bruce, and Carly leapfrog by the hour. No live Kokoro at chime time.

  python3 hourly_chimes.py                 print the 48 sentences
  python3 hourly_chimes.py --render        render any missing wav; keep files that already exist
  python3 hourly_chimes.py --render --force   render all 48 again

Hawaii is the clock. Mountain Daylight Time is four hours ahead, Eastern time is six
hours ahead (daylight, paired with Mountain Daylight Time), and UTC is ten hours ahead.
The minute is the same in each zone. Files are hour-HH-00.wav and hour-HH-30.wav.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 , str ( HERE ) )
from speakable import speakable, spoken_clock  # noqa: E402
import speakers  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
PACIFIC = HERE.parents[2]  # info: set PACIFIC
CHIME_MP3 = PACIFIC / "Media" / "Voice" / "assets" / "deep-ui-chime.mp3"  # info: set CHIME_MP3
CHIME_DIR = DB / "Media" / "Audio" / "Voice" / "Chimes"  # info: set CHIME_DIR
ROSTER = ("ava", "bruce", "carly")  # info: set ROSTER
MDT_AHEAD = 4  # info: Mountain Daylight Time is four hours ahead of Hawaii
EASTERN_AHEAD = 6  # info: Eastern daylight is six hours ahead of Hawaii
UTC_AHEAD = 10  # info: UTC is ten hours ahead of Hawaii
PHRASE_GAP_S = 0.6  # info: silence between the Hawaii, Mountain, Eastern, and UTC lines
SLOTS = tuple((hour, minute) for hour in range(24) for minute in (0, 30))  # info: set SLOTS


# ====================================================
# SECTION: function persona_for
# What it does: Midnight is Ava, 1 a.m. is Bruce, 2 a.m. is Carly, then it repeats.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona_for(hour: int) -> str:  # info: def persona_for
    return ROSTER[int(hour) % 3]  # info: return ROSTER [ int ( hour ) % 3 ]


# ====================================================
# SECTION: function slot_minute
# What it does: A chime slot is :00 or :30. Anything else is refused.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def slot_minute(minute: int) -> int:  # info: def slot_minute
    m = int(minute)  # info: set m
    if m not in (0, 30):  # info: if m not in ( 0 , 30 ) :
        raise ValueError(f"chime minute must be 0 or 30, got {m}")  # info: raise ValueError ( f" chime minute must be 0 or 30, got { m } " )
    return m  # info: return m


# ====================================================
# SECTION: function wav_path
# What it does: Path of the prebuilt wav for one Hawaii hour and :00 or :30.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def wav_path(hour: int, minute: int = 0) -> Path:  # info: def wav_path
    h = int(hour) % 24  # info: set h
    m = slot_minute(minute)  # info: set m
    return CHIME_DIR / f"hour-{h:02d}-{m:02d}.wav"  # info: return CHIME_DIR / f" hour- { h : 02d } - { m : 02d } .wav "


# ====================================================
# SECTION: function chime_phrases
# What it does: Four spoken lines for one slot. Render inserts a pause between them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chime_phrases(hour: int, minute: int = 0) -> list[str]:  # info: def chime_phrases
    h = int(hour) % 24  # info: set h
    m = slot_minute(minute)  # info: set m
    lines = [  # info: set lines
        f"Report generated at {spoken_clock(h, m)}.",  # info: f" Report generated at { spoken_clock ( h , m ) } . "
        f"Mountain Daylight Time is {spoken_clock((h + MDT_AHEAD) % 24, m)}.",  # info: f" Mountain Daylight Time is { spoken_clock ( ( h + MDT_AHEAD ) % 24 , m ) } . "
        f"Eastern time is {spoken_clock((h + EASTERN_AHEAD) % 24, m)}.",  # info: f" Eastern time is { spoken_clock ( ( h + EASTERN_AHEAD ) % 24 , m ) } . "
        f"Universal time is {spoken_clock((h + UTC_AHEAD) % 24, m)}.",  # info: f" Universal time is { spoken_clock ( ( h + UTC_AHEAD ) % 24 , m ) } . "
    ]  # info: ]
    return [line.replace("..", ".") for line in lines]  # info: return [ line . replace ( ".." , "." ) for line in lines ]


# ====================================================
# SECTION: function chime_sentence
# What it does: The four lines as one caption. The wav pauses between them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chime_sentence(hour: int, minute: int = 0) -> str:  # info: def chime_sentence
    return " ".join(chime_phrases(hour, minute))  # info: return " " . join ( chime_phrases ( hour , minute ) )


# ====================================================
# SECTION: function load_chime
# What it does: UI chime as 24 kHz mono, peak-capped so it sits with the voice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_chime():  # info: def load_chime
    import numpy as np  # info: import numpy as np
    import soundfile as sf  # info: import soundfile as sf
    if not CHIME_MP3.is_file():  # info: if not CHIME_MP3 . is_file ( ) :
        raise FileNotFoundError(CHIME_MP3)  # info: raise FileNotFoundError ( CHIME_MP3 )
    wav = CHIME_MP3.with_suffix(".wav")  # info: set wav
    subprocess.run(  # info: call subprocess . run
        ["ffmpeg", "-y", "-i", str(CHIME_MP3), "-ac", "1", "-ar", "24000", str(wav)],  # info: [ "ffmpeg" , "-y" , "-i" , str ( CHIME_MP3 )
        check=True,  # info: check = True
        capture_output=True,  # info: capture_output = True
        timeout=30,  # info: timeout = 30
    )  # info: )
    data, sr = sf.read(str(wav), dtype="float32")  # info: data , sr = sf . read (
    if sr != 24000:  # info: if sr != 24000 :
        raise RuntimeError(f"chime sample rate {sr}")  # info: raise RuntimeError ( f" chime sample rate { sr } " )
    peak = float(np.max(np.abs(data))) if len(data) else 0.0  # info: set peak
    if peak > 0:  # info: if peak > 0 :
        data = data * (0.7 / peak)  # info: set data
    return np.asarray(data, dtype=np.float32)  # info: return np . asarray ( data , dtype = np . float32 )


# ====================================================
# SECTION: function adopt_legacy
# What it does: Rename hour-HH.wav from the 24-file set to hour-HH-00.wav.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def adopt_legacy() -> None:  # info: def adopt_legacy
    for hour in range(24):  # info: for hour in range ( 24 ) :
        old = CHIME_DIR / f"hour-{hour:02d}.wav"  # info: set old
        new = wav_path(hour, 0)  # info: set new
        if old.is_file() and not new.is_file():  # info: if old . is_file ( ) and not new . is_file ( ) :
            old.replace(new)  # info: old . replace ( new )


# ====================================================
# SECTION: function render_all
# What it does: Write :00 and :30 wavs in one Kokoro load, with a pause between the four lines. Existing files stay unless force is set.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_all(force: bool = False) -> list[dict]:  # info: def render_all
    import numpy as np  # info: import numpy as np
    import voice_generate as vg  # info: import voice_generate as vg
    CHIME_DIR.mkdir(parents=True, exist_ok=True)  # info: CHIME_DIR . mkdir ( parents = True , exist_ok = True )
    adopt_legacy()  # info: call adopt_legacy
    tone = None  # info: set tone
    gap = None  # info: set gap
    rows = []  # info: set rows
    for hour, minute in SLOTS:  # info: for hour , minute in SLOTS :
        who = persona_for(hour)  # info: set who
        voice = speakers.AGENTS[who]["kokoro"]  # info: set voice
        rate = float(speakers.AGENTS[who]["speed"])  # info: set rate
        phrases = chime_phrases(hour, minute)  # info: set phrases
        read = " ".join(phrases)  # info: set read
        spoken = " ".join(speakable(line) for line in phrases)  # info: set spoken
        dest = wav_path(hour, minute)  # info: set dest
        row = {"hour": hour, "minute": minute, "persona": who, "voice": voice, "speed": rate, "text": read, "spoken": spoken, "phrases": phrases, "wav": str(dest)}  # info: set row
        if dest.is_file() and not force:  # info: if dest . is_file ( ) and not force :
            rows.append(row)  # info: rows . append ( row )
            print(json.dumps({"hour": hour, "minute": minute, "persona": who, "wav": str(dest), "kept": True}), flush=True)  # info: call print
            continue  # info: continue
        if tone is None:  # info: if tone is None :
            tone = load_chime()  # info: set tone
            gap = np.zeros(int(vg.SAMPLE_RATE * 0.25), dtype=np.float32)  # info: set gap
        phrase_gap = np.zeros(int(vg.SAMPLE_RATE * PHRASE_GAP_S), dtype=np.float32)  # info: set phrase_gap
        pieces = []  # info: set pieces
        for line in phrases:  # info: for line in phrases :
            speech = vg.synth(speakable(line), voice, rate)  # info: set speech
            if speech is None:  # info: if speech is None :
                raise RuntimeError(f"no audio for {hour:02d}:{minute:02d}")  # info: raise RuntimeError ( f" no audio for { hour : 02d } : { minute : 02d } " )
            body, _lead, _tail = vg.prepare(np.asarray(speech, dtype=np.float32))  # info: body , _lead , _tail = vg . prepare (
            pieces.append(body)  # info: pieces . append ( body )
        voiced = pieces[0]  # info: set voiced
        for body in pieces[1:]:  # info: for body in pieces [ 1 : ] :
            voiced = np.concatenate([voiced, phrase_gap, body])  # info: set voiced
        mixed = np.concatenate([tone, gap, voiced])  # info: set mixed
        vg.write_wav(dest, mixed)  # info: call vg . write_wav
        rows.append(row)  # info: rows . append ( row )
        print(json.dumps({"hour": hour, "minute": minute, "persona": who, "wav": str(dest), "kept": False}), flush=True)  # info: call print
    (CHIME_DIR / "chimes.json").write_text(json.dumps({"ok": True, "count": len(rows), "chimes": rows}, indent=2) + "\n", encoding="utf-8")  # info: call (
    return rows  # info: return rows


# ====================================================
# SECTION: function main
# What it does: Print the 48 sentences, or render missing wavs when --render is passed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if "--render" not in sys.argv:  # info: if "--render" not in sys . argv :
        for hour, minute in SLOTS:  # info: for hour , minute in SLOTS :
            print(f"{hour:02d}:{minute:02d} {persona_for(hour)}: {chime_sentence(hour, minute)}")  # info: call print
        return 0  # info: return 0
    render_all(force="--force" in sys.argv)  # info: call render_all
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
