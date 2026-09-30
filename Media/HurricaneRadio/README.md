# HurricaneRadio

Dry-run handoff of the hurricane desk WAV to Report playback. It does not synthesize speech and it does not open a speaker.

| | |
| --- | --- |
| Code | `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Media/HurricaneRadio/scripts` |
| Database | `2 - RootRecord-Database/Media/HurricaneRadio/` (`last-radio.json`, runtime only) |
| Logs | `2 - RootRecord-Database/Logs/Media/HurricaneRadio/` |

The WAV is `2 - RootRecord-Database/Media/Audio/Voice/hurricane_desk_current.wav`, written by `Media/Voice`. This folder hands that report to `Media/Playback/scripts/play.py --report hurricane_desk --dry-run`. It never passes `--play` and never calls `aplay`.

Night sleep is read from `System/NightSleep`. A sleeping desk skips with `night_sleep`. A missing player skips with `player_missing`. A missing WAV is `audio_missing`. A busy player is the overlap skip.

`RR_HURRICANE_RADIO` gates job `media_hurricane_radio` in `jobs.py` (default `0`) at 06:35, 13:12, and 17:02. The same block is copied in `proposed-job-block.txt`. Do not paste it again. Speaker playback still needs Alexander's sign-off on the player (`RR_PLAYBACK` and `--play`). AWS radio is not restored.

```text
python3 scripts/radio.py run
```
