# CouncilQuake

Carly’s per-quake Telegram notice, read from the existing Hawaiʻi quake file. Dry-run unless a send flag is set.

Folder name, used in all three places: `CouncilQuake` (inside Communications).

| Place | Path |
| --- | --- |
| Server code | `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/CouncilQuake/scripts` |
| Database data | `2 - RootRecord-Database/Communications/CouncilQuake/` |
| Database logs | `2 - RootRecord-Database/Logs/Communications/CouncilQuake/` |

`scripts/quake_posts.py` reads `2 - RootRecord-Database/Geology/Earthquakes/hawaii-last.json`. It does not fetch USGS and it does not replace `geology_collect.py`.

The live job seeds once (marks current M≥2 ids seen, prints nothing) and later prepares at most four new notices. `--feed` skips that seed so a fixture with an empty seen list prints the notice. `RR_COUNCIL_QUAKE_SEND` and `RR_COUNCIL_QUAKE_WAV` stay off. The token name is `TELEGRAM_CARLY_TOKEN`. The script does not load it unless the send flag is on, and it never prints the value.

Persona text for council chat already lives in Library `Agent Context/{Ava,Bruce,Carly}-Agent-Context/` and in `2 - RootRecord-Database/AI/Ollama/Modelfiles/Production/{ava,bruce,carly}-telegram.Modelfile`. This notice is the fixed USGS template. It does not copy those prompts and it does not call `run-infer`.

Job `council_quake_telegram` is gated `RR_COUNCIL_QUAKE=1` and stays off. It is on the night-sleep allow list so a later enable is not skipped. Do not restart the poller from this folder.
