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
"""Prebuild 24 hourly chimes. Ava, Bruce, and Carly leapfrog. No live Kokoro at chime time.

  python3 hourly_chimes.py            print the 24 sentences
  python3 hourly_chimes.py --render   render speech, prepend the UI chime, write the wavs

Hawaii is the hour. Mountain Daylight Time is four hours ahead, Eastern time is six
hours ahead (daylight, paired with Mountain Daylight Time), and UTC is ten hours ahead.
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


# ====================================================
# SECTION: function persona_for
# What it does: Midnight is Ava, 1 a.m. is Bruce, 2 a.m. is Carly, then it repeats.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona_for(hour: int) -> str:  # info: def persona_for
    return ROSTER[int(hour) % 3]  # info: return ROSTER [ int ( hour ) % 3 ]


# ====================================================
# SECTION: function wav_path
# What it does: Path of the prebuilt wav for one Hawaii hour.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def wav_path(hour: int) -> Path:  # info: def wav_path
    return CHIME_DIR / f"hour-{int(hour) % 24:02d}.wav"  # info: return CHIME_DIR / f" hour- { int ( hour ) % 24 : 02d } .wav "


# ====================================================
# SECTION: function chime_sentence
# What it does: Spoken line for one Hawaii hour, plus Mountain Daylight Time, Eastern time, and UTC.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chime_sentence(hour: int) -> str:  # info: def chime_sentence
    h = int(hour) % 24  # info: set h
    return (  # info: return (
        f"It is currently {spoken_clock(h, 0)} in Hawaii. "  # info: f" It is currently { spoken_clock ( h , 0 ) } in Hawaii. "
        f"Mountain Daylight Time is {spoken_clock((h + MDT_AHEAD) % 24, 0)}. "  # info: f" Mountain Daylight Time is { spoken_clock ( ( h + MDT_AHEAD ) % 24 , 0 ) } . "
        f"Eastern time is {spoken_clock((h + EASTERN_AHEAD) % 24, 0)}. "  # info: f" Eastern time is { spoken_clock ( ( h + EASTERN_AHEAD ) % 24 , 0 ) } . "
        f"U.T.C. is {spoken_clock((h + UTC_AHEAD) % 24, 0)}."  # info: f" U.T.C. is { spoken_clock ( ( h + UTC_AHEAD ) % 24 , 0 ) } . "
    ).replace("..", ".")  # info: ) . replace ( ".." , "." )


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
# SECTION: function render_all
# What it does: Render all 24 hours in one Kokoro load and write wavs with the chime in front.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_all() -> list[dict]:  # info: def render_all
    import numpy as np  # info: import numpy as np
    import voice_generate as vg  # info: import voice_generate as vg
    tone = load_chime()  # info: set tone
    gap = np.zeros(int(vg.SAMPLE_RATE * 0.25), dtype=np.float32)  # info: set gap
    CHIME_DIR.mkdir(parents=True, exist_ok=True)  # info: CHIME_DIR . mkdir ( parents = True , exist_ok = True )
    rows = []  # info: set rows
    for hour in range(24):  # info: for hour in range ( 24 ) :
        who = persona_for(hour)  # info: set who
        voice = speakers.AGENTS[who]["kokoro"]  # info: set voice
        rate = float(speakers.AGENTS[who]["speed"])  # info: set rate
        read = chime_sentence(hour)  # info: set read
        spoken = speakable(read)  # info: set spoken
        speech = vg.synth(spoken, voice, rate)  # info: set speech
        if speech is None:  # info: if speech is None :
            raise RuntimeError(f"no audio for hour {hour}")  # info: raise RuntimeError ( f" no audio for hour { hour } " )
        body, _lead, _tail = vg.prepare(np.asarray(speech, dtype=np.float32))  # info: body , _lead , _tail = vg . prepare (
        mixed = np.concatenate([tone, gap, body])  # info: set mixed
        dest = wav_path(hour)  # info: set dest
        vg.write_wav(dest, mixed)  # info: call vg . write_wav
        rows.append({"hour": hour, "persona": who, "voice": voice, "speed": rate, "text": read, "spoken": spoken, "wav": str(dest)})  # info: rows . append ( { "hour" : hour
        print(json.dumps({"hour": hour, "persona": who, "wav": str(dest)}), flush=True)  # info: call print
    (CHIME_DIR / "chimes.json").write_text(json.dumps({"ok": True, "count": len(rows), "chimes": rows}, indent=2) + "\n", encoding="utf-8")  # info: call (
    return rows  # info: return rows


# ====================================================
# SECTION: function main
# What it does: Print the sentences, or render them when --render is passed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if "--render" not in sys.argv:  # info: if "--render" not in sys . argv :
        for hour in range(24):  # info: for hour in range ( 24 ) :
            print(f"{hour:02d} {persona_for(hour)}: {chime_sentence(hour)}")  # info: call print
        return 0  # info: return 0
    render_all()  # info: call render_all
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
