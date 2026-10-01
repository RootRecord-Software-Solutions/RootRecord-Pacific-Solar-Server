# Website / Site

Local route manifest for the one Vercel site. On demand only. No job.

| Field | Value |
| --- | --- |
| **Work order** | `Documentation/06-development/Work-Orders/drafts/Site_Cloudflare_config_and_thumbnails_Work_Order_WO-MIG-08-2026-09-29.md` |
| **State** | Production is `https://www.rootrecord.cloud/`. Apex 308s there. `ssh.rootrecord.cloud` and `api.rootrecord.cloud` are A `18.118.30.226`. Caddy proxies the API to `127.0.0.1:8091`. |
| **Secrets** | none. Allowlist is empty. Does not read `master-key.env`. |

Production is `https://www.rootrecord.cloud/` on Vercel. The apex CNAME is the same Vercel target and returns 308 to `www`. `ssh.rootrecord.cloud` is A `18.118.30.226`, proxy off. Desk aliases `rr-aws` and `rr-aws-ip` use that address with no ProxyCommand. `rootserver.rootrecord.cloud` stays the poller. `api.rootrecord.cloud` is A `18.118.30.226`, proxy off. Caddy on AWS proxies it to `127.0.0.1:8091`. The page requests `https://api.rootrecord.cloud/api/state` and `/api/operations`. `play.rootmc.net` stays the game. The contract is [HANDOFF-vercel-homepage-2026-09-30.md](../HANDOFF-vercel-homepage-2026-09-30.md).

The public page is `Website/Home/`, published by the `website` catalog row. This folder is the route manifest. It does not push the site. Old avaivy.cloud skins stay in Library `Archive/Website-Themes/avaivy.cloud/` and are not in `Website/Home/`. `3 - RootRecord-Website/` is not on this desk. Do not bind port 3001. `https://rootserver.rootrecord.cloud/` is the poller on `127.0.0.1:8799`, not a site.

```bash
nice -n 10 python3 scripts/site_check.py
```

A manifest that adds a `token` or `credentials-file` key exits non-zero. Pass that file as the only argument. The default run still writes Database `Communications/Site/routes-last.json` and appends Logs `Communications/Site/site_check.log`. That output path was not moved.

Code lives at `Website/Site/`. It is the Vercel route manifest, not the live `cloudflared` tunnel.
