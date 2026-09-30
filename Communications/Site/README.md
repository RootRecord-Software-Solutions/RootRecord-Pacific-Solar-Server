# Communications / Site

Local route manifest for the one Vercel site. On demand only. No job.

| Field | Value |
| --- | --- |
| **Work order** | `Documentation/06-development/Work-Orders/drafts/Site_Cloudflare_config_and_thumbnails_Work_Order_WO-MIG-08-2026-09-29.md` |
| **State** | Manifest and checker landed. DNS not changed. `home_card` stays off. |
| **Secrets** | none. Allowlist is empty. Does not read `master-key.env`. |

`www.rootrecord.cloud` stays on the globe (`http://127.0.0.1:8090`). `ssh.rootrecord.cloud` stays. The Vercel home URL is recorded as `https://rootrecord.cloud/home` and is not routed here.

Old avaivy.cloud skins are copied unchanged under Library `Archive/Website-Themes/avaivy.cloud/` and are not applied to the Vercel app. The 24 thumbnail images are imported at `3 - RootRecord-Website/media/thumbnails/`. They are not a theme. This folder does not push the site.

```bash
nice -n 10 python3 scripts/site_check.py
```

A manifest that adds a `token` or `credentials-file` key exits non-zero. Pass that file as the only argument. The default run writes Database `Communications/Site/routes-last.json` and appends Logs `Communications/Site/site_check.log`.
