# Website

Desk runtime for Stripe snapshots, Vercel failed-build records, and last-known operation JSON. The public site is `Website/Home/`. That folder is the RootRecord-Website presentation layer: the pages Vercel publishes. It is not a second copy of the runtime. Public vocabulary in that folder is Hawaiʻi and Mainland Server. Do not put a provider name, a finer server location, or private infrastructure there.

| Item | Where |
| --- | --- |
| Public page | [Home/](Home/) — globe background, closable services and operations panels |
| GitHub / Vercel | Org `RootRecord-Software-Solutions/RootRecord-Website` (row `website`, Vercel) and personal `rootrecordsoftwaresolutions/RootRecord-Website` (row `website-personal`). Both pull and push from `Github/scripts/repos.conf` |
| Public page | `https://www.rootrecord.cloud/` on Vercel. Apex CNAME matches `www` and 308s there. Contract: [HANDOFF-vercel-homepage-2026-09-30.md](HANDOFF-vercel-homepage-2026-09-30.md) |
| SSH | `ssh.rootrecord.cloud` A `18.118.30.226`, proxy off. `rr-aws` and `rr-aws-ip` use that address. Hawaii snapshots go to AWS over SSH |
| API | The page requests `https://api.rootrecord.cloud`. That name is A `18.118.30.226`, proxy off. Caddy on AWS proxies it to `127.0.0.1:8091`. Do not use port 8787 |
| Last-known file | `2 - RootRecord-Database/Website/operations.json` and the Hawaii snapshot `Communications/network/local-data-globe/rebroadcast/status-current.json` |

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
| `scripts/live_data_pages.py` | Power from Energy last files, weather from the Hawaiʻi state report header, Kīlauea from `Geology/Volcanoes/kilauea-last.json`. Missing numbers are omitted. Also writes the operations bundle | `2 - RootRecord-Database/Website/pages/{power,weather,kilauea}.json` and `2 - RootRecord-Database/Website/operations.json` |

Chat, voice packs, day board, Minecraft, and context are not built here.

`Website/Home/` is the public page and the Vercel repository. `Website/.env.example` lists Vercel env names only. Do not clone `RootRecord-Cloud` into this tree. Do not run a local `next` server. Do not bind port 3001.

`Website/Site/` is the local route manifest and on-demand checker. It does not publish the page. Page hosts are the one Vercel site. `api.rootrecord.cloud` is the AWS status API. No job.

`Website/Cloudflare-Workers/` is an undeployed worker. Its origin variable still names the deleted `root-record-cloud.vercel.app` project. No route is attached. It is not the live poller tunnel. That tunnel is `Communications/network/cloudflare/` (`rootserver.rootrecord.cloud` → `127.0.0.1:8799`).

Live Energy BLE, the poller, Hawaiʻi weather, the globe, cameras, Kokoro, and `geology_collect.py` are not replaced.

## Paths

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Website/
```
