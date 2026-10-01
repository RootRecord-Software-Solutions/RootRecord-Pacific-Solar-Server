# Website / Site

Local route manifest for the one Vercel site. On demand only. No job.

| Field | Value |
| --- | --- |
| **Work order** | `Documentation/06-development/Work-Orders/drafts/Site_Cloudflare_config_and_thumbnails_Work_Order_WO-MIG-08-2026-09-29.md` |
| **State** | Manifest and checker landed. Public page hosts are the one Vercel site. `api.rootrecord.cloud` is the AWS status API. `ssh.rootrecord.cloud` stays. |
| **Secrets** | none. Allowlist is empty. Does not read `master-key.env`. |

Page hosts in `config/routes.yml` are the one Vercel site at `https://rootrecord.online/`. `ssh.rootrecord.cloud` stays. `rootserver.rootrecord.cloud` stays the poller. `api.rootrecord.cloud` stays the AWS status API on `127.0.0.1:8091`. `play.rootmc.net` stays the game.

The public page is `Website/Home/`, published by the `website` catalog row. This folder is the route manifest. It does not push the site. Old avaivy.cloud skins stay in Library `Archive/Website-Themes/avaivy.cloud/` and are not in `Website/Home/`. `3 - RootRecord-Website/` is not on this desk. Do not bind port 3001. `https://rootserver.rootrecord.cloud/` is the poller on `127.0.0.1:8799`, not a site.

```bash
nice -n 10 python3 scripts/site_check.py
```

A manifest that adds a `token` or `credentials-file` key exits non-zero. Pass that file as the only argument. The default run still writes Database `Communications/Site/routes-last.json` and appends Logs `Communications/Site/site_check.log`. That output path was not moved.

Code lives at `Website/Site/`. It is the Vercel route manifest, not the live `cloudflared` tunnel.
