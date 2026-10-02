# Website / Site

Local route manifest for the one Vercel site. On demand only. No job.

| Field | Value |
| --- | --- |
| **Work order** | `Documentation/06-development/Work-Orders/drafts/Site_Cloudflare_config_and_thumbnails_Work_Order_WO-MIG-08-2026-09-29.md` |
| **State** | Production is `https://www.rootrecord.cloud/` on Vercel. `ssh.rootrecord.cloud` is retired. Mainland One is radio. `api.rootrecord.cloud` is aimed at Mainland Two and is not live yet. |
| **Secrets** | none. Allowlist is empty. Does not read `master-key.env`. |

Production is `https://www.rootrecord.cloud/` on Vercel. The apex CNAME is the same Vercel target and returns 308 to `www`. Do not point `www` at the Mainland tunnel. `ssh.rootrecord.cloud` is retired. `ml1` and `rr-aws` use `ml1.rootrecord.cloud` through cloudflared. Direct fallback `rr-aws-ip` is `3.140.195.32`. `rootserver.rootrecord.cloud` stays the Pacific poller. `api.rootrecord.cloud` is aimed at Mainland Two. The API process is not there yet. The page still requests `https://api.rootrecord.cloud/api/state` and `/api/operations`. A missing reading stays missing. Listeners use `https://radio.rootrecord.cloud/radio/live.mp3`. `play.rootmc.net` stays the game. The contract is [HANDOFF-vercel-homepage-2026-09-30.md](../HANDOFF-vercel-homepage-2026-09-30.md). The locked radio plan is Library `Documentation/01-operations/2026-10-01-mainland-rename-and-ssh-tunnels.md`.

The public page is `Website/Home/`, published by the `website` catalog row. This folder is the route manifest. It does not push the site. Old avaivy.cloud skins stay in Library `Archive/Website-Themes/avaivy.cloud/` and are not in `Website/Home/`. `3 - RootRecord-Website/` is not on this desk. Do not bind port 3001. `https://rootserver.rootrecord.cloud/` is the poller on `127.0.0.1:8799`, not a site.

```bash
nice -n 10 python3 scripts/site_check.py
```

A manifest that adds a `token` or `credentials-file` key exits non-zero. Pass that file as the only argument. The default run still writes Database `Communications/Site/routes-last.json` and appends Logs `Communications/Site/site_check.log`. That output path was not moved.

Code lives at `Website/Site/`. It is the Vercel route manifest, not the live `cloudflared` tunnel.
