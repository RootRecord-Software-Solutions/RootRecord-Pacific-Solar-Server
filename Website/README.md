# Website

Desk runtime for Stripe snapshots, Vercel failed-build records, and last-known operation JSON. The public page is `Website/Home/`.

| Item | Where |
| --- | --- |
| Public page | [Home/](Home/) — globe background, closable services and operations panels |
| GitHub / Vercel | `RootRecord-Software-Solutions/RootRecord-Website`, mirror row `website` in `Github/scripts/repos.conf` |
| Globe feed | `https://www.rootrecord.cloud/api/state` on AWS |
| Operations feed | `https://www.rootrecord.cloud/api/operations` on AWS. The route is in the mainland server source and is not deployed, so the panel reads No data until that file is on AWS |
| Last-known file | `2 - RootRecord-Database/Website/operations.json` |

`3 - RootRecord-Website/` is not on this desk. Do not recreate it. Do not bind port 3001. `https://rootserver.rootrecord.cloud/` is the poller on `127.0.0.1:8799`, not this page.

## Status (2026-09-30 HST — WO-MIG-10)

| Item | State |
| --- | --- |
| Folder | **`Website/`** on Pacific. No lowercase twin and no symlink |
| Scripts | `scripts/stripe_poll.py`, `scripts/vercel_builds.py`, `scripts/live_data_pages.py` — landed. No-key run PASS |
| Keys | `lib/envload.py` reads `/home/rootrecord/master/master-key.env` only. Names: `STRIPE_SECRET_KEY`, `AVA_STRIPE_SECRET_KEY`, `VERCEL_TOKEN`, `VERCEL_API_TOKEN`, `VERCEL_TEAM_ID`, `VERCEL_ORG_ID`. None of those names are in the file today. Values are never printed |
| `jobs.py` | `stripe_poll` every 1800 s behind `RR_STRIPE=1`. `vercel_builds` every 300 s behind `RR_VERCEL_BUILDS=1`. Both **gated off** |
| Data | `2 - RootRecord-Database/Website/` — `stripe-snapshot.json`, `pages/{power,weather,kilauea}.json` |
| Logs | `2 - RootRecord-Database/Logs/Website/` — failed-build JSON only. Empty until a token exists. No prune |
| Public pages | `Website/Home/` is the Vercel source. See the table at the top of this file |
| Holding skin | Unchanged copy in `5 - RootRecord-Library/Archive/Website-Themes/holding/`. Out of the Vercel build |

### Scripts

| Script | What it does | Writes |
| --- | --- | --- |
| `scripts/stripe_poll.py` | Stripe balance snapshot. No key writes `not_configured` and does not call Stripe. A failed live poll keeps the last `ok` file | `Website/stripe-snapshot.json` |
| `scripts/vercel_builds.py` | Redacted failed-build records. No token writes nothing and does not call Vercel. Does not delete records | `Logs/Website/*.json` |
| `scripts/live_data_pages.py` | Power from Energy last files, weather from the Hawaiʻi state report header, Kīlauea from `Geology/Volcanoes/kilauea-last.json`. Missing numbers are omitted | `Website/pages/{power,weather,kilauea}.json` |

Chat, voice packs, day board, Minecraft, and context are not built here.

The public app is remote. `Website/.env.example` lists Vercel env names only. Do not clone `RootRecord-Cloud` into this tree. Do not run a local `next` server.

`Website/Site/` is the local route manifest and on-demand checker. `www.rootrecord.cloud` stays on the globe. `home_card` stays off. No job.

`Website/Cloudflare-Workers/` is the undeployed worker in front of `root-record-cloud.vercel.app`. No route is attached. It is not the live poller tunnel. That tunnel is `Communications/network/cloudflare/` (`rootserver.rootrecord.cloud` → `127.0.0.1:8799`).

Live Energy BLE, the poller, Hawaiʻi weather, the globe, cameras, Kokoro, and `geology_collect.py` are not replaced.

## Paths

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Website/
```
