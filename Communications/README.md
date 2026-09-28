# Communications

Communication subsystem: network (Cloudflare tunnel, Hawaii globe), and messaging shells (discord, email, slack, telegram, github messaging).

---

## Status (2026-09-28)

| Area | State |
| --- | --- |
| `network/cloudflare/` | **Live** — `bin/cloudflared` + config store |
| `network/scripts/ensure-network-globe-hawaii.sh` | Present; job cwd may still point at legacy `coms/ssh/local-data-globe` |
| `telegram/` | Shell only — relay still legacy `…/skills/coms/telegram/` |
| discord / email / slack / github/{api,messaging,…} | Shells / placeholders |

---

## jobs.py references

| Job id | Notes |
| --- | --- |
| `cloudflare_tunnel` | `cloudflared_bin` skills-prefixed absolute → file lives under this domain in-repo |
| `network_globe_hawaii` | ensure script under this domain; **cwd** still legacy coms/ssh |
| `council_relay` | `…/skills/coms/telegram/scripts/ensure-relay.sh` — **unimported** |

Token: `/home/rootrecord/.cloudflared/rootserver.token` (local only).

---

## Layout

```text
Communications/
  network/
    cloudflare/{bin,config}/
    scripts/
  telegram/ discord/ email/ slack/
  github/{api,messaging,notifications,webhooks}/
```

---

*Docs-only update 2026-09-28 HST.*
