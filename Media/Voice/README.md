# Media/Voice — G3 Kokoro-82M voice (non-resident)

Current behavior: Library [2026-09-30 voice desk](../../../../5%20-%20RootRecord-Library/Documentation/01-Operations/2026-09-30-voice-desk.md). The 2026-09-29 port record is [Voice-Reports-G3](../../../../5%20-%20RootRecord-Library/Documentation/10-AI-and-Agent-Runtime/Voice-Reports-G3.md).

- `scripts/voice-render.sh render|stitch|clips|asr …` runs `voice_generate.py` in `.venv` through the single-flight inference lock at nice 10. The model loads per process and is gone when it exits.
- Voices: Ava `af_heart` 1.0 · Bruce `am_echo` 1.0 · Carly `af_nova` 1.0. Output: 24 kHz 16-bit mono WAV.
- `Hawaii` and `Hawaiian` are spoken as those words. Other place names use the English respell in `scripts/hawaiian_lexicon.py`.
- Model: Database `AI/Kokoro/Kokoro-82M/` (git-ignored). Single bank: Database `Media/Audio/Voice/` — `<report>_current.wav` / `.ogg`, transcripts beside them, markdown under `Reports/`. Prebuilt chimes: `Media/Audio/Voice/Chimes/hour-00-00.wav` through `hour-23-30.wav` (48 files, every hour and half hour).
- The Mainland station library is Opus, not these WAV files. Hawaii still renders a WAV. `scripts/radio_push.py` encodes that one report to `<report>_current.opus` (24 kbps mono) and replaces it on `/home/ubuntu/rootrecord-radio`. Station chimes are `hour-HH-MM.opus` (48 kbps). Station music is `.opus` (96 kbps). The public mix is `https://radio.rootrecord.cloud/radio/live.mp3`. Earthquake and hurricane reports stay Pacific poller jobs.
- Hour desks: `generate_hour_reports.py` via jobs `voice_hour_batch` (default **:42**). When the batch finishes it records `Media/Audio/Voice/Timing/` total averages, recalculates the next start minute into `hour_batch_schedule.json` (stays at :42 unless averages need earlier), `radio_push --all` to ML1 immediately, then deletes local `.wav` / `.txt` under `Media/Audio/Voice/` (keeps `.ogg`). `radio_push_hour` at **:55** is catch-up only. Individual per-desk voice jobs are removed — one batch owns generation.
- Sandbox delivery is on from `run-poller.sh` (`RR_VOICE_DELIVER=1`). On in that file: NWS, Kīlauea, solar, security, bandwidth, system, energy, remaining tasks, earthquakes, geology, net samples. Off until the flag is added: hourly chime, hurricane, roll-ups, official weather, boot brief.
- System temperature is Celsius. A bare "degrees" is still spoken as Fahrenheit for weather numbers.
- Energy at :15 and :45 includes one channel 1 look per hour. Delta AC in above 550 W, or River AC in above 300 W, is generator. A matching Delta output and River input is a transfer. A reading older than 30 minutes is "out of range."
- The :00 and :30 chimes play a prebuilt file. They do not render. The job stays off until `RR_VOICE_HOURLY_CHIME=1` at poller start.
- Speakers stay off. `Media/Playback/scripts/play.py` is dry-run unless `RR_PLAYBACK=1` and `--play`.
- `.venv/` is git-ignored. Rebuild it with:
  `uv python install 3.12 && uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python --index-url https://download.pytorch.org/whl/cpu torch && uv pip install --python .venv/bin/python kokoro==0.9.4 "misaki[en]==0.9.4" soundfile openai-whisper==20250625 https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl`
  Then copy `.venv/lib/python3.12/site-packages/espeakng_loader/espeak-ng-data` to `~/.local/share/rootrecord/` (espeak-ng's 160-character path limit).
