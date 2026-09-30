# Media/CloudTTS

Gated route for one cloud voice beside Kokoro. Work order: Library `Documentation/06-development/Work-Orders/drafts/Cloud_TTS_routing_Work_Order_WO-MIG-33-2026-09-29.md`.

| Path | Role |
| --- | --- |
| `Media/CloudTTS/scripts/route.py` | Code |
| Database `Media/CloudTTS/` | Last-route state (gitignored) |
| Database `Logs/Media/CloudTTS/` | Router log (gitignored) |

Kokoro stays in `Media/Voice`. This folder does not render a local WAV and does not call `aplay`. `Media/Playback` must already exist. If it does not, the router exits `dependency_missing` and names Report playback.

Default engine is `kokoro` (`called: false`, `detail: kokoro_local`). `--engine ara` stays `gated` unless both `RR_CLOUD_TTS=1` and `--speak` are set. That live path posts to xAI TTS with voice id `ara` and writes `ara-last.mp3` here. It was not run in the build proof. `--engine cursor` records `cursor_is_text_queue` and does not call an API.

Allowlist in `scripts/envload.py`: `XAI_API_KEY` from `/home/rootrecord/master/master-key.env` only. Values are never printed. No `jobs.py` entry.

```text
python3 -m CloudTTS --engine ara
python3 -m CloudTTS --engine ara --speak
python3 -m CloudTTS --engine kokoro
```

Run those from the Media directory, or set `PYTHONPATH` to Media. Unset `RR_CLOUD_TTS` for the gate proof.
