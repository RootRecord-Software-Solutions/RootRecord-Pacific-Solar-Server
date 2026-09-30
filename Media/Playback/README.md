# Media/Playback

On-demand player for one Kokoro WAV. Work order: Library `Documentation/06-development/Work-Orders/drafts/Report_playback_Work_Order_WO-MIG-15-2026-09-29.md`.

| Path | Role |
| --- | --- |
| `Media/Playback/scripts/play.py` | Code |
| Database `Media/Playback/` | Last-play state (gitignored) |
| Database `Logs/Media/Playback/` | Player log (gitignored) |

Clips stay in Database `Media/Audio/Voice`. `--report NAME` reads `<name>_current.wav`. `--clip Persona/slug` reads `Clips/<Persona>/<slug>.wav`. Any other path is refused.

Default is `--dry-run` (`played: false`, no device). Live `aplay` needs both `RR_PLAYBACK=1` and `--play`. Quiet hours are 22:00–06:00 HST unless `--force`. `--force` does not bypass the flag. A second caller gets `busy`. No `jobs.py` entry. The old morning / midday / late / periodic play crons are not restored.

No `master-key.env` keys.
