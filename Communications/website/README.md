# Communications / website — RootRecord-Cloud (Vercel)

The public Vercel site `rootrecord.cloud` (`root-record-cloud.vercel.app`) is checked out at `3 - RootRecord-Website/` (`rootrecordsoftwaresolutions/RootRecord-Cloud` @ `84dec4a`). This folder is no longer the checkout.
Library architecture: `Documentation/00-architecture/Website-RootRecord-Cloud-Staging.md`.

## Status (2026-09-30 00:05 HST)

| Item | State |
| --- | --- |
| Checkout `3 - RootRecord-Website/` of `rootrecordsoftwaresolutions/RootRecord-Cloud` @ `84dec4a` | **LANDED** — own repo, token-free `origin`, ignored by the ecosystem root `.gitignore` |
| `RootRecord-Cloud/` here | **Removed** 2026-09-30 after sign-off. It had no `.git`. |
| `npm ci --ignore-scripts` (30 packages, 506 MB `node_modules`) | **PASS** |
| `npm run build` (Next.js 15.5.23, 293 static pages) | **PASS** |
| Brief `next start` on 127.0.0.1:3099 (`/`, `/blog`, `/status` 200; allowlist 404) — stopped | **PASS** · `/api/*` proxy → origin `origin.avaivy.cloud` returned **530** (origin tunnel down) |
| Auto-sync of the clone (`repos.conf`) | not added — sign-off |
| Vercel deploy / project settings | **not touched** |

## Layout

```text
3 - RootRecord-Website/     checkout of RootRecord-Cloud (own .git, ignored by the ecosystem repo)
Communications/website/
  README.md                 this file
  .env.example              env var NAMES only
```

The checkout stays its own repo so Vercel keeps deploying from `RootRecord-Cloud` and the ecosystem repo does not record a gitlink.

## Commands (nice 10)

```bash
cd "/home/rootrecord/RootRecord-Ecosystem/3 - RootRecord-Website"
export NEXT_TELEMETRY_DISABLED=1
nice -n 10 npm ci --ignore-scripts --no-audit --no-fund
nice -n 10 npm run build
nice -n 10 ./node_modules/.bin/next start -H 127.0.0.1 -p 3099   # brief checks only; stop it after
```

**Do not run `scripts/auto-push.py`** — it `git add`/`commit`/`push`es to `origin main`, which would trigger a Vercel production deploy.

*Checkout moved 2026-09-30 HST. 2026-09-29 staging record kept in the Library page.*
