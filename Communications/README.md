# Communications

Communication subsystem: network (Cloudflare tunnel, Hawaii globe), and messaging shells (discord, email, slack, telegram, github messaging).

---

## Status (2026-09-28)

| Area | State |
| --- | --- |
| `network/cloudflare/` | **Live** |
| `network/scripts/ensure-network-globe-hawaii.sh` | Present; job cwd may be legacy |
| telegram / discord / slack | Shells; relay still G2 `coms/telegram` |
| discord | Shell only — **WO-COM-002** token rotation required before LIVE |
| G1 | `communications/*`, `network-globe`, `local-data-globe`, `council/council-telegram` |

---

## jobs.py

| Job id | Notes |
| --- | --- |
| `cloudflare_tunnel` | Binary under this domain; abs string may still be skills-prefixed |
| `network_globe_hawaii` | ensure in-repo; cwd may be legacy coms/ssh |
| `council_relay` | G2 `…/skills/coms/telegram/scripts/ensure-relay.sh` |

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

*Docs-only 2026-09-28 HST.*
