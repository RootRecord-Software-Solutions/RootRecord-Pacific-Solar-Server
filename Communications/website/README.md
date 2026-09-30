# Communications / website — RootRecord-Cloud (Vercel) staging

Local staging of the public Vercel site `rootrecord.cloud` (`root-record-cloud.vercel.app`).
Library architecture: `Documentation/00-architecture/Website-RootRecord-Cloud-Staging.md`.

## Status (2026-09-29 14:05 HST)

| Item | State |
| --- | --- |
| Clone `RootRecord-Cloud/` of `rootrecordsoftwaresolutions/RootRecord-Cloud` @ `84dec4a` | **LANDED** — own repo, **gitignored by Pacific** |
| `npm ci --ignore-scripts` (30 packages, 506 MB `node_modules`) | **PASS** |
| `npm run build` (Next.js 15.5.23, 293 static pages) | **PASS** |
| Brief `next start` on 127.0.0.1:3099 (`/`, `/blog`, `/status` 200; allowlist 404) — stopped | **PASS** · `/api/*` proxy → origin `origin.avaivy.cloud` returned **530** (origin tunnel down) |
| Auto-sync of the clone (`repos.conf`) | not added — sign-off |
| Vercel deploy / project settings | **not touched** |

## Layout

```text
Communications/website/
  README.md            (Pacific-tracked) this file
  .env.example         (Pacific-tracked) env var NAMES only
  RootRecord-Cloud/    (gitignored in Pacific .gitignore) — own git clone, own GitHub repo, Vercel git-deploys from it
    src/app/…          Next.js App Router pages + /api proxy routes
    node_modules/ .next/   local only (ignored by the site's own .gitignore)
```

## Why a nested clone (not a copy into Pacific)

Vercel deploys from the `RootRecord-Cloud` GitHub repo; copying files into Pacific would create a second, non-deploying source of truth, Pacific's `.gitignore` drops `*.jpg` (the site's `media/banner.jpg`), and Pacific auto-sync would churn `node_modules/.next` rules. The clone keeps the site's history and its own ignore rules.

## Commands (nice 10)

```bash
cd "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/website/RootRecord-Cloud"
export NEXT_TELEMETRY_DISABLED=1
nice -n 10 npm ci --ignore-scripts --no-audit --no-fund
nice -n 10 npm run build
nice -n 10 ./node_modules/.bin/next start -H 127.0.0.1 -p 3099   # brief checks only; stop it after
```

**Do not run `scripts/auto-push.py`** — it `git add`/`commit`/`push`es to `origin main`, which would trigger a Vercel production deploy.

*Website staging 2026-09-29 HST.*
