## Handoff — 2026-09-30 — Mainland → Vercel homepage

### Locked 2026-10-01

`www.rootrecord.cloud` stays on Vercel. Do not point it at the Mainland tunnel. `ssh.rootrecord.cloud` is retired. `ml1` and `rr-aws` use `ml1.rootrecord.cloud` through cloudflared. Direct fallback `rr-aws-ip` is `3.140.195.32`. `ml2` uses `ml2.rootrecord.cloud`. Direct fallback `ml2-ip` is `3.149.238.83`. Do not restart cloudflared over `ssh ml1`.

Mainland One is radio only. Tunnel Mainland-One is `939b16f7-7d13-4776-bd4d-80fe8021fc72`. `radio.rootrecord.cloud` is HTTP to `127.0.0.1:8092`. The listener stream is `https://radio.rootrecord.cloud/radio/live.mp3` (`audio/mpeg`, 128 kbps). Now-playing is `https://radio.rootrecord.cloud/radio/now.json`. The station library is Opus. The public mix is that mp3. There is no music bed on the live host.

`api.rootrecord.cloud` is aimed at Mainland Two (tunnel `bd8e68a4-8a97-4b20-afd9-b058473a0a22`). The API process is not there yet. Do not treat it as live on Mainland One. `rootserver.rootrecord.cloud` stays the Pacific poller. Earthquake and hurricane voice reports are Pacific poller jobs. Pollers have not moved to Mainland Two.

The DNS table and SSH paragraph below are the evening of 2026-09-30. They are not the live routes.

### Evening of 2026-09-30 (not the live routes)

The public page is Vercel project `rootrecord` (team `rrc-ore`). Production is `https://www.rootrecord.cloud/`. `https://rootrecord.vercel.app/` serves the same page. AWS is not the site.

Cloudflare DNS for `rootrecord.cloud`, proxy off:

| Name | Type | Value |
| --- | --- | --- |
| `@` | CNAME | `658fd2bfe7dcb292.vercel-dns-017.com` |
| `www` | CNAME | `658fd2bfe7dcb292.vercel-dns-017.com` |
| `ssh` | A | `18.118.30.226` |
| `api` | A | `18.118.30.226` |

The apex answers from Vercel with **308** to `https://www.rootrecord.cloud/`. That host returns **200**, title “Root Record — Software Solutions”.

SSH is direct. `ssh.rootrecord.cloud` is that A record, not the globe tunnel. Desk aliases `rr-aws` and `rr-aws-ip` in `~/.ssh/config` both use `HostName 18.118.30.226` and have no `ProxyCommand`. A login on 2026-09-30 returned the same address and an uptime of about 4 days 16 hours.

Alexander’s data path: SSH carries Hawaii database snapshots to AWS. The public API is served from AWS to the Vercel page. `api.rootrecord.cloud` is A `18.118.30.226`, proxy off. Caddy on that host proxies HTTPS to `127.0.0.1:8091`. The page source requests `https://api.rootrecord.cloud/api/state` and `/api/operations`. Do not call port 8787. Do not treat `www` as `/api/state`.

`rootserver.rootrecord.cloud` was not retargeted. It remains the Hawaii poller tunnel (`127.0.0.1:8799`). `play.rootmc.net` stays the game. Do not recreate `3 - RootRecord-Website`. Do not bind port 3001.

### Confirmed facts from earlier the same evening

These were true before the DNS cutover. They are not the live hosts now.

- `https://root-record-cloud.vercel.app/` returned **404** `DEPLOYMENT_NOT_FOUND`. That project was deleted. The live project is `rootrecord` on `rrc-ore`.
- Do not use `http://<aws-ip>:8787/hawaii.ndjson`. That process serves a **frozen** append file (`/home/ubuntu/network-globe/network-globe/data/hawaii.ndjson`, 60,371,626 bytes). It is not the live snapshot.

### Live data the globe needs

Two replaced files on the mainland host. Neither is a log. Anything else dropped in `/home/ubuntu/rebroadcast/` is deleted by the fetch script, except these names.

| File | Writer | Cadence | Size at handoff |
| --- | --- | --- | --- |
| `/home/ubuntu/rebroadcast/hawaii-current.ndjson` | AWS pulls it from Pacific | every 30 s (`rr-pacific-fetch.timer`) | ~21 KB, ~40 flows |
| `/home/ubuntu/rebroadcast/aws-current.ndjson` | globe process samples local `ss` | every 2 s | ~1 KB |

Pacific source, overwritten in place (not appended):

`1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/network/local-data-globe/rebroadcast/hawaii-current.ndjson`

AWS cannot open SSH to Pacific (`192.168.1.66`). Pacific holds `rr-aws-fetch-tunnel.service`: reverse forward `127.0.0.1:17022` on AWS to Pacific port 22. The AWS fetch key can only print the Hawaii snapshot. Pull script: `/home/ubuntu/rebroadcast/fetch-pacific.sh`. A download over 1 MiB is discarded.

Record shape (one JSON object per line):

```json
{
  "type": "network-globe-telemetry",
  "version": 1,
  "timestamp": 0,
  "sourceNode": "HawaiiRoot | AwsOhio",
  "sourceRegion": "local-hawaii | us-east-2",
  "source": { "latitude": 0, "longitude": 0, "label": "Hawaii | AWS Ohio" },
  "destination": { "type": "public-ip", "ip": "<public ip>", "port": 443 },
  "protocol": "tcp | udp",
  "process": "<name>"
}
```

Hawaii rows also include `packets` and `bytes` (currently 0). AWS rows omit them. `source.publicIp` on Hawaii is null.

Merged JSON the globe process built while `www` was still that process, `GET /api/state`:

- `origin.label`: `"Hawaii + AWS Ohio"`
- `stats.activeFlows`, `stats.localActiveFlows`, `stats.hawaiiActiveFlows`, `stats.endpoints`, `stats.packetRate`, `stats.bytesPerSec`, `stats.collector` = `"ss + hawaii snapshot"`
- `aws`: `{ "ok": true, "region": "us-east-2", "label": "AWS Ohio", "localFlows": <n> }` when the socket sample works
- `points`: `{ type: "origin", label: "Hawaii" }` and `{ type: "aws", label: "AWS Ohio" }`, plus `type: "dest"` after geolocation
- `arcs[]`: `startLat`, `startLng`, `endLat`, `endLng`, `process`, `protocol`, `endpoint` (destination IP), `port`, `city`, `country`, `org`, `sourceLabel`, `color`, `altitude`, `stroke`
  - Hawaii flows: `sourceLabel` `"Hawaii"`, color `#22c55e`, start near 21.307, -157.858
  - Mainland flows: `sourceLabel` `"AWS Ohio"`, color `#38bdf8`, start near 39.961, -82.999 (measured; fallback 40.417, -82.907)
  - One link arc: `protocol` `"persistent"`, process `"Hawaii ↔ Mainland"`, color `#38bdf8`
- Arc count can be lower than flow count until `ip-api.com` geolocation fills. `packetRate` and `bytesPerSec` are 0 with the current snapshots.
- `GET /health` returns `{ status, flows, hawaii, local, geo }`. `GET /api/operations` reads `data/operations.json` or `{ ok: false, detail: "no_data" }`.

### What changed

- Pacific no longer appends `hawaii.ndjson` on AWS. The collector writes one replaced snapshot.
- AWS pulls that snapshot. It also writes its own replaced snapshot and merges both for the globe.
- `network-globe-connection-history.service` was stopped, then came back **active / enabled**. SQLite is still 450,560 bytes. It reads the frozen ndjson, not the live snapshot. It is not a homepage source.

### Evidence

- 2026-10-01 06:20 UTC: `/api/state` had `hawaiiActiveFlows` 41, `localActiveFlows` 4, `collector` `ss + hawaii snapshot`.
- Public page HUD: “Hawaii N flows · Mainland N flows” and “Mainland measuring · us-east-2”. Green arcs from Hawaii, blue arcs from Ohio.
- Frozen feed byte size unchanged at 60,371,626 after the append stopped.

### Still open / unresolved

- Other public web hosts 301 to `https://www.rootrecord.cloud/`. Checked 2026-09-30 21:25 HST: `rootrecord.online`, `rootrecord.info`, `avaivy.cloud`, `kilauea.cloud`, `kilauea.online`, `rootmc.net`, `advancedcraft.net`, `alexrs94.site`, and their `www` names. `play.rootmc.net` stays the game at `15.204.13.9`.
- `api.rootrecord.cloud` answers from AWS. Hawaii snapshots were arriving (`hawaii-current.ndjson` updated the same minute). `GET /api/state` returned `collector` `ss + hawaii snapshot`. Do not point the API at port 8787 or at `www`.
- Cloudflare worker in `Website/Cloudflare-Workers/` is not deployed. Its origin default is still `https://root-record-cloud.vercel.app`.

### Explicitly historical (do not treat as current)

- AWS as the public homepage, and the globe HTML on `www`, are not the target. `www` is the Vercel page.
- The 60 MB `hawaii.ndjson` and `:8787` are the old append feed.
- `ssh.rootrecord.cloud` as a Cloudflare tunnel CNAME, and a `ProxyCommand` on `rr-aws`, are the previous SSH path.

### Next recommended action

- Leave `play.rootmc.net` and the `rootserver` poller tunnel alone unless Alexander asks. Desk SSH is `ml1.rootrecord.cloud` and `ml2.rootrecord.cloud`. `api.rootrecord.cloud` is aimed at Mainland Two and is not live yet.
