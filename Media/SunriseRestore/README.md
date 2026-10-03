# Media/SunriseRestore

Playback request after night sleep. Package name `SunriseRestore`.

- Code: `scripts/sunrise_restore.py`
- Pending flag: Database `Media/SunriseRestore/pending.json` (runtime, not committed). Night sleep writes `pending: true`. This script only clears it.
- Logs: Database `Logs/Media/SunriseRestore/sunrise-restore.log`
- Sunrise clock: Database `Energy/sun/sun-times_current.json` (read only)
- Player: `Media/Playback/scripts/play.py` (Report playback). If that Folder is missing, each clip is skipped with `player_missing`. This desk does not play audio and does not call `aplay`.
- Clips, in order: `battery_reconnect` (no spoken line in the old source), then `boot_all_systems_running` ("All systems running.").

`jobs.py` was already being edited when this was built, so the gated block was not inserted. The block to add, still default off, is in `proposed-job-block.txt`.
