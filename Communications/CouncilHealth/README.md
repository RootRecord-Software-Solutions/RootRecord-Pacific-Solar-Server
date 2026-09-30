# CouncilHealth

Health check for the live council relay. Report only unless a later sign-off turns alerts on.

Folder name, used in all three places: `CouncilHealth` (inside Communications).

| Place | Path |
| --- | --- |
| Server code | `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/CouncilHealth/scripts` |
| Database data | `2 - RootRecord-Database/Communications/CouncilHealth/` |
| Database logs | `2 - RootRecord-Database/Logs/Communications/CouncilHealth/` |

No `Logs/` directory on the server. The job `council_health` stays off unless `RR_COUNCIL_HEALTH=1` at poller start. The default command is `--no-alert --no-probe`. A model probe also needs `RR_COUNCIL_HEALTH_PROBE=1` and `--probe`. A Telegram send also needs `RR_RELAY_REPLIES=1` and `--alert`.

Token names, allowlisted from `/home/rootrecord/master/master-key.env`: `TELEGRAM_AVA_TOKEN`, `TELEGRAM_BRUCE_TOKEN`, `TELEGRAM_CARLY_TOKEN`.
