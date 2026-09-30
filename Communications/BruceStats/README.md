# BruceStats

Bruce’s measured desk sample, read from the live host and EcoFlow last files. Dry-run unless a send flag is set.

Folder name, used in all three places: `BruceStats` (inside Communications).

| Place | Path |
| --- | --- |
| Server code | `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/BruceStats/scripts` |
| Database data | `2 - RootRecord-Database/Communications/BruceStats/` |
| Database logs | `2 - RootRecord-Database/Logs/Communications/BruceStats/` |

`scripts/bruce_stats.py` reads `2 - RootRecord-Database/System/last/host-last.json` and `2 - RootRecord-Database/Energy/soc/` plus `Energy/watts/` for Delta 2 and River 2 Pro. It does not replace the host sampler or the EcoFlow poller.

The job fires at 07:18, 15:18, and 21:18 HST, once per hour slot. A missing file is `DOWN`. Watts that are not in the last file are left out.

`RR_BRUCE_STATS` gates the job. `RR_BRUCE_STATS_SEND` stays off. The token name is `TELEGRAM_BRUCE_TOKEN`. The script does not load it unless the send flag is on, and it never prints the value. A signed-off send uses `council_chat_id` from `Communications/CouncilQuake/scripts/quake_posts.py` and does not call that file’s Carly `maybe_send`.

Job `bruce_stats_posts` stays off. Do not restart the poller from this folder.
