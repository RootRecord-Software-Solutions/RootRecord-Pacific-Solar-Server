# RootRecord-Pacific-Solar-Server

**Primary autonomous solar / Pacific node infrastructure** for the RootRecord ecosystem under the org [RootRecord-Software-Solutions](https://github.com/RootRecord-Software-Solutions).

Provides energy telemetry, system monitoring, automation orchestration, environmental data collection, camera services, secure communications, and resilient cloud-connected services for the Pacific RootRecord node.

> **Canonical runtime home.** Legacy personal-account trees (`Solar-Pacific-RootRecord-Server`, `Solar-Pacific-RootRecord-Server-Old`, old `~/.ollama/skills` desk) are historical. New domain work lands here.

---

## Domain layout

| Directory | Role |
| --- | --- |
| `Automations/` | Poller, jobs, stack orchestration |
| `Energy/` | EcoFlow / hybrid energy telemetry & reports |
| `System/` | Host stats, observability samples |
| `Weather/` | Weather domain (import in progress per Library WOs) |
| `Geology/` | Geology / hazard domain |
| `Communications/` | Tunnel, messaging, network surface |
| `Github/` | Git sync / catalog helpers |
| `Security/` | Security posture scripts & notes |

Desk path (live):

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server
```

---

## Related canonical repos

| Repo | Role |
| --- | --- |
| [RootRecord-Library](https://github.com/RootRecord-Software-Solutions/RootRecord-Library) | Durable docs, agent context, work orders |
| [RootRecord-Database](https://github.com/RootRecord-Software-Solutions/RootRecord-Database) | Data & log layout (source of truth for where bytes go) |
| [US-Mainland-Server](https://github.com/rootrecordsoftwaresolutions/US-Mainland-Server) | Continuity node |

Work orders and migration status: Library → `Documentation/06-development/Work Orders/` and `Work-Orders/`.

---

## Policy (docs)

- This README is documentation only; it does not change runtime behavior.
- Domain imports follow Library work orders (one domain at a time; no bulk merge from G1 Old).
- Prefer Pacific poller over legacy skills-desk paths.

---

**Root Record Software Solutions** · Oriented from Hawaiʻi Island · [rootrecord.cloud](https://rootrecord.cloud)
