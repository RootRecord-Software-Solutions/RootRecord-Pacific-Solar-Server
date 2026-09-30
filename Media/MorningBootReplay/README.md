# MorningBootReplay

Same-day replay of the morning `boot_brief` WAV until noon HST. It does not synthesize speech and it does not open a speaker.

| | |
| --- | --- |
| Code | `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Media/MorningBootReplay/scripts` |
| Database | `2 - RootRecord-Database/Media/MorningBootReplay/replay-last.json` (runtime only, `at` field) |
| Logs | `2 - RootRecord-Database/Logs/Media/MorningBootReplay/` |

The WAV is `2 - RootRecord-Database/Media/Audio/Voice/boot_brief_current.wav`, written by `Media/Voice`. Replay hands that report to `Media/Playback/scripts/play.py --report boot_brief --dry-run`. This folder never passes `--play`.

`RR_MORNING_BOOT_REPLAY` is the proposed job gate (default `0`). It is not registered in `jobs.py`. Speaker playback still needs Alexander's sign-off on the player (`RR_PLAYBACK` and `--play`).

`run` arms itself when today's state is not already disarmed and the morning WAV is on disk. A same-day `disarm` stays off until the next morning.

```text
python3 scripts/replay.py arm
python3 scripts/replay.py run --dry-run
python3 scripts/replay.py disarm --reason operator
```
