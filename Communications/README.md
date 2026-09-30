# Communications

Communication subsystem: network (Cloudflare tunnel, Hawaii globe), and messaging shells (discord, email, slack, telegram, github messaging).

---

## Status (2026-09-29 22:23 HST)

| Area | State |
| --- | --- |
| `network/cloudflare/` | **Live.** `jobs.py` starts `Communications/network/cloudflare/bin/cloudflared` (token file `~/.cloudflared/rootserver.token`, public host `rootserver.rootrecord.cloud` → `127.0.0.1:8799`). The binary stays untracked and is on `Github/scripts/ecosystem-skip-autocommit.txt`. Do not commit it. |
| `network/scripts/ensure-network-globe-hawaii.sh` | **Live.** Job cwd is Pacific `Communications/network`. Collector is `network/local-data-globe/collector.js`. |
| telegram | **Live and quiet.** `council_relay` runs `Communications/telegram/scripts/ensure-relay.sh`. `RR_RELAY_REPLIES` stays `0` (poll and log only; no infer, no post). |
| discord | Shell only — **WO-COM-002** token rotation required before LIVE |
| slack / email | Shells only. Not a second live relay. |
| Notify policy | Still the unsealed draft under Library `Documentation/00-architecture/Communications-Notify-Policy-Draft-2026-09-28.md`. Do not add notify jobs from this page. |
| `web-facts/` | G1 `websites/web-facts` port (allowlisted HTTPS GET), on demand only — LANDED, smoke PASS 2026-09-29 13:58 HST; not wired to the council relay |
| `live-wx/` | G1 `weather/live-wx` port (NWS point forecast + HI alert names + nearest hurricane, for chat), on demand only (`--offline` = no HTTP) — LANDED, smoke PASS 2026-09-29 14:09 HST; not wired to the council relay |
| `website/` | RootRecord-Cloud Vercel site (Next.js 15) staged as its **own clone** `website/RootRecord-Cloud/` (gitignored here; Vercel deploys from that repo). `npm ci` + `npm run build` PASS 2026-09-29 14:04 HST; no deploy, no auto-sync row (sign-off). See `website/README.md` |

---

## jobs.py

| Job id | Notes |
| --- | --- |
| `cloudflare_tunnel` | Pacific `bin/cloudflared`. ON_BOOT builtin `tunnel_start`. |
| `network_globe_hawaii` | Pacific `network/scripts/ensure-network-globe-hawaii.sh` |
| `council_relay` | Pacific `telegram/scripts/ensure-relay.sh`. Replies stay off. |

Token: `/home/rootrecord/.cloudflared/rootserver.token` (local only).

Messaging bot tokens (Discord, Telegram, etc.): **local secrets only** — never from git history or inventory mirrors. Discord enablement: see `discord/README.md` and Library **WO-COM-002**.

---

## G1 recovery (after G2 telegram / globe)

| Packet | Target |
| --- | --- |
| communications/telegram, discord, slack | Matching shells under this domain |
| network-globe, local-data-globe | `network/` |
| council-telegram | Policy + relay — one getUpdates only |
| cloudflare-workers | Edge workers — separate from poller `cloudflared` binary |

---

## Layout

```text
Communications/
  network/cloudflare/{bin,config}/
  network/scripts/
  telegram/ discord/ email/ slack/
  github/{api,messaging,notifications,webhooks}/
```

---

*Paths corrected 2026-09-29 22:23 HST. Replies and Discord stay off.*
