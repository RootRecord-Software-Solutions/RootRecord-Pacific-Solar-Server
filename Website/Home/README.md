# Root Record

Public home page for Root Record Software Solutions. Vercel builds this repository.

The globe is the page background. A compact activity readout sits on the left. Sign up, a short about card, and operations sit on the right. The glass is light so the globe stays visible. Arc width from the feed (about 1.2–1.5) is drawn near 0.14–0.18. Close a box to use the globe. **+ Activity**, **+ Sign up**, **+ About**, and **+ Operations** bring a closed box back. Sign up opens `https://rootrecord.info/login`.

| File | Role |
| --- | --- |
| [index.html](index.html) | The page |
| [vercel.json](vercel.json) | Static hosting headers |

This repository does not hold measurements. The homepage is this Vercel app. AWS is not the site.

`https://www.rootrecord.cloud/` is still the AWS globe on `127.0.0.1:8090` only because DNS has not moved. The page currently reads `/api/state` and `/api/operations` there because that host is the globe process. Those URLs are not a data hostname. When `www` moves to this deployment, they go away with it. Do not iframe `www`. Do not call port 8787. That port serves a frozen append file.

The globe inputs are two replaced files on the mainland host, or a future data-only URL that returns the same `/api/state` object. The contract is [HANDOFF-vercel-homepage-2026-09-30.md](../HANDOFF-vercel-homepage-2026-09-30.md). That file stays on the Pacific desk. It is not part of this Vercel repository.

On the desk, edit `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Website/Home/`. The `website` row in `Github/scripts/repos.conf` mirror-publishes that folder here. Do not put a `.git` directory in the umbrella tree. Do not bind port 3001.

Desk scripts, Stripe, and Cloudflare worker source stay in `Website/` outside this folder. They publish with the Pacific repository, not with this one.
