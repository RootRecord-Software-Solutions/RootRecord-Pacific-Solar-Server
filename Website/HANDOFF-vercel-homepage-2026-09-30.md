## Handoff — 2026-09-30 — Mainland → Vercel homepage

### Confirmed facts

- The public homepage is Vercel’s job. AWS must not be the homepage.
- Right now that cutover has not happened. `https://rootrecord.cloud/` returns **301** to `https://www.rootrecord.cloud/`. `www` is still **200** from the AWS globe (`network-globe-web.service` on `127.0.0.1:8090`, Cloudflare tunnel ingress `www.rootrecord.cloud`).
- `https://root-record-cloud.vercel.app/` returned **404** `DEPLOYMENT_NOT_FOUND` at 2026-10-01 06:20 UTC. No Vercel token and no Vercel CLI login are on this desk.
- Do not use `www.rootrecord.cloud` as the site, an iframe, or the canonical origin. That host is the AWS globe page.
- Do not use `http://<aws-ip>:8787/hawaii.ndjson`. That process is still listening, and it serves a **frozen** append file (`/home/ubuntu/network-globe/network-globe/data/hawaii.ndjson`, 60,371,626 bytes). It is not the live snapshot.

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

Merged JSON the page already builds, `GET /api/state` on the globe process (today also `https://www.rootrecord.cloud/api/state` because that host is this process):

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

- Page hosts are the one Vercel site (`Website/Site/config/routes.yml`). `ssh.rootrecord.cloud`, `rootserver.rootrecord.cloud`, and `play.rootmc.net` stay. The AWS globe tunnel no longer lists `www`.
- Last-known status is `https://api.rootrecord.cloud` (`/api/status`, `/api/operations`, `/api/state`). That host is not a page. DNS for it still has to be attached to the AWS tunnel.
- `https://rootrecord.online/` has Vercel DNS and returns `DEPLOYMENT_NOT_FOUND` until the GitHub repository is connected.
- Cloudflare worker in `Website/Cloudflare-Workers/` is not deployed. Its origin default is `https://root-record-cloud.vercel.app`.

### Explicitly historical (do not treat as current)

- AWS as the public homepage, and the globe HTML on `www`, are not the target.
- The 60 MB `hawaii.ndjson` and `:8787` are the old append feed.
- A signup link to `https://rootrecord.info/login` sends people through a page host. That host is the Vercel site.

### Next recommended action

- Connect the `RootRecord-Website` repository to the Vercel project for `rootrecord.online` until that host returns 200.
- Attach `api.rootrecord.cloud` to the AWS tunnel ingress for `127.0.0.1:8091` and start `status-api/rr-status-api.service`.
- Hawaii already writes `status-current.json`. AWS `fetch-pacific.sh` keeps the last good copy when a pull fails.
