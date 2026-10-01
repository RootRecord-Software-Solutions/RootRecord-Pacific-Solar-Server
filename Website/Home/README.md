# Root Record

Public home page for Root Record Software Solutions. Vercel builds this repository.

The globe is the page background. A compact activity readout sits on the left. Sign up, a short about card, and operations sit on the right. The glass is light so the globe stays visible. Arc width from the feed (about 1.2–1.5) is drawn near 0.14–0.18. Close a box to use the globe. **+ Activity**, **+ Sign up**, **+ About**, and **+ Operations** bring a closed box back. Sign up opens `/login` on this site.

| File | Role |
| --- | --- |
| [index.html](index.html) | The page |
| [vercel.json](vercel.json) | Static hosting headers |

This repository does not hold measurements. The homepage is this Vercel app. AWS is not the site.

Public page hosts in the desk manifest point at `https://www.rootrecord.cloud/`. The page source requests `https://api.rootrecord.cloud`, and that name has no public DNS yet. SSH carries Hawaii snapshots to AWS at `18.118.30.226`. Do not call port 8787. Do not treat `www` as the API.

The globe state file and the Hawaii status snapshot live on AWS. The contract is [HANDOFF-vercel-homepage-2026-09-30.md](../HANDOFF-vercel-homepage-2026-09-30.md). That file stays on the Pacific desk. It is not part of this Vercel repository.

On the desk, edit `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Website/Home/`. The `website` row in `Github/scripts/repos.conf` mirror-publishes that folder here. Do not put a `.git` directory in the umbrella tree. Do not bind port 3001.

Desk scripts, Stripe, and Cloudflare worker source stay in `Website/` outside this folder. They publish with the Pacific repository, not with this one.
