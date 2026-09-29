# Media/Voice — G3 Kokoro-82M voice (non-resident)

Full doc: Library `Documentation/00-architecture/Voice-Reports-G3.md`.

- `scripts/voice-render.sh render|stitch|clips|asr …` runs `voice_generate.py` in `.venv` through the single-flight inference lock at nice 10. The model loads per process and is gone when it exits.
- Voices: Ava `af_heart` 0.82 (default) · Bruce `am_echo` 0.92 · Carly `af_nova` 0.74. Output: 24 kHz 16-bit mono WAV.
- Model: Database `AI/Kokoro/Kokoro-82M/` (git-ignored). Audio: Database `Media/Audio/Voice/<report>_current.wav`, history in `Archive/<report>_YYYYMMDDTHHMM.wav`, phrase clips in `Clips/<Persona>/<slug>.wav` + tracked `Clips/clips_manifest.json`.
- `scripts/system_perf.py`: the first ported report (Bruce). jobs.py id `voice_system_perf` is gated OFF (`RR_VOICE_SYSTEM_PERF=1`, read at poller start).
- `scripts/voice_reports.py earthquake_report` (Carly, G1 `earthquake-hourly` spoken script): reads Database `Geology/Earthquakes/{hawaii,global}-last.json` from Pacific `Geology/scripts/geology_collect.py`; "new since last report" state in `<report out>/earthquake_report_seen.json`. jobs.py id `voice_earthquake_report` (:08) gated OFF (`RR_VOICE_QUAKE=1`). Text PASS 2026-09-29 13:20 HST (`--no-voice`); WAV not rendered yet (VERIFY PENDING).
- `scripts/voice_reports.py hurricane_desk` (Carly, G1 `weather/hurricane-desk` Hawaiʻi block): nearest tracked storm to Honolulu / Hilo / Līhuʻe / Kona from Database `Weather/Hawai'i/hurricanes/tracking/*/track.json` (weather poller) + NWS HI tropical alerts. jobs.py id `voice_hurricane_desk` (05:50, 09:50, 12:50, 16:55, 20:50) gated OFF (`RR_VOICE_HURRICANE=1`). G1 global JTWC/RAMMB board not collected in G3. Text PASS 2026-09-29 13:43 HST; WAV VERIFY PENDING.
- `scripts/voice_reports.py kilauea_report` (Carly, G1 hourly Kīlauea desk + cached HVO-notice lead-in): Database `Geology/Volcanoes/{kilauea,mauna-loa}-last.json` + `Geology/Earthquakes/hawaii-last.json`. jobs.py id `voice_kilauea_report` (:03) gated OFF (`RR_VOICE_KILAUEA=1`). Text PASS 2026-09-29 13:43 HST; WAV VERIFY PENDING.
- The jobs.py registrations above are a **sign-off item** (standing rule: jobs.py is edited only when Alexander asks or a work order requires it). Exact blocks: Database `Logs/Migration/migration-jobs-py-additions-20260929.md`.
- **No delivery** (Telegram / AWS radio / speakers) until Alexander signs off.
- `.venv/` is git-ignored. Rebuild it with:
  `uv python install 3.12 && uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python --index-url https://download.pytorch.org/whl/cpu torch && uv pip install --python .venv/bin/python kokoro==0.9.4 "misaki[en]==0.9.4" soundfile openai-whisper==20250625 https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl`
  Then copy `.venv/lib/python3.12/site-packages/espeakng_loader/espeak-ng-data` to `~/.local/share/rootrecord/` (espeak-ng's 160-character path limit).
