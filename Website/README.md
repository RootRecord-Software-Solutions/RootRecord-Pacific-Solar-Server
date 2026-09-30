# Website

Desk runtime for the Stripe snapshot, Vercel failed-build records, and live-data pages. The public cards live in the one Vercel app under `3 - RootRecord-Website/src/app/data/`.

## Status (2026-09-30 HST — WO-MIG-10)

| Item | State |
| --- | --- |
| Folder | **`Website/`** on Pacific. No lowercase twin and no symlink |
| Scripts | `scripts/stripe_poll.py`, `scripts/vercel_builds.py`, `scripts/live_data_pages.py` — landed. No-key run PASS |
| Keys | `lib/envload.py` reads `/home/rootrecord/master/master-key.env` only. Names: `STRIPE_SECRET_KEY`, `AVA_STRIPE_SECRET_KEY`, `VERCEL_TOKEN`, `VERCEL_API_TOKEN`, `VERCEL_TEAM_ID`, `VERCEL_ORG_ID`. None of those names are in the file today. Values are never printed |
| `jobs.py` | `stripe_poll` every 1800 s behind `RR_STRIPE=1`. `vercel_builds` every 300 s behind `RR_VERCEL_BUILDS=1`. Both **gated off** |
| Data | `2 - RootRecord-Database/Website/` — `stripe-snapshot.json`, `pages/{power,weather,kilauea}.json` |
| Logs | `2 - RootRecord-Database/Logs/Website/` — failed-build JSON only. Empty until a token exists. No prune |
| Public pages | In the one Vercel app at `3 - RootRecord-Website/src/app/data/` (`/data`, `/data/power`, `/data/weather`, `/data/kilauea`). Glass cards. They read Database `Website/pages/*.json`. On a host without those files they say the snapshot is not mounted. Not deployed |
| Holding skin | Unchanged copy in `5 - RootRecord-Library/Archive/Website-Themes/holding/`. Out of the Vercel build |

### Scripts

| Script | What it does | Writes |
| --- | --- | --- |
| `scripts/stripe_poll.py` | Stripe balance snapshot. No key writes `not_configured` and does not call Stripe. A failed live poll keeps the last `ok` file | `Website/stripe-snapshot.json` |
| `scripts/vercel_builds.py` | Redacted failed-build records. No token writes nothing and does not call Vercel. Does not delete records | `Logs/Website/*.json` |
| `scripts/live_data_pages.py` | Power from Energy last files, weather from the Hawaiʻi state report header, Kīlauea from `Geology/Volcanoes/kilauea-last.json`. Missing numbers are omitted | `Website/pages/{power,weather,kilauea}.json` |

Chat, voice packs, day board, Minecraft, and context are not built here.

Live Energy BLE, the poller, Hawaiʻi weather, the globe, cameras, Kokoro, and `geology_collect.py` are not replaced.

## Paths

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Website/
```
