# Communications / website — RootRecord-Cloud (Vercel)

Alexander removed the desk folder `3 - RootRecord-Website/` on 2026-09-30. There is no desk checkout. Do not recreate that folder. Do not start it again.

The public Vercel app `rootrecord.cloud` (`root-record-cloud.vercel.app`) is remote only. This folder is a pointer. It does not hold the site.

`https://rootserver.rootrecord.cloud/` is the poller on `127.0.0.1:8799`, not a site.

Library architecture: `Documentation/00-architecture/Website-RootRecord-Cloud-Staging.md`.

## Status (2026-09-30 HST)

| Item | State |
| --- | --- |
| Desk folder `3 - RootRecord-Website/` | **Removed** 2026-09-30. Do not recreate it. Do not start `next`. |
| `RootRecord-Cloud/` here | **Removed** 2026-09-30 after sign-off. It had no `.git`. |
| Auto-sync of a clone (`repos.conf`) | not added |
| Vercel deploy / project settings | **not touched** |

## Layout

```text
Communications/website/
  README.md                 this file
  .env.example              env var NAMES only
```

**Do not run `scripts/auto-push.py`** — it `git add`/`commit`/`push`es to `origin main`, which would trigger a Vercel production deploy.

*Desk folder removed 2026-09-30 HST. 2026-09-29 staging record kept in the Library page.*
