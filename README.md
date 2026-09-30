# ☀️ RootRecord Pacific Solar Server

> **Primary Pacific runtime for the RootRecord ecosystem.**
>
> Energy • automation • system monitoring • security • communications • resilient services

<p align="center">
  <a href="https://github.com/RootRecord-Software-Solutions"><strong>RootRecord Software Solutions</strong></a>
  ·
  <a href="https://github.com/RootRecord-Software-Solutions/RootRecord-Library"><strong>Library</strong></a>
  ·
  <a href="https://github.com/RootRecord-Software-Solutions/RootRecord-Database"><strong>Database</strong></a>
  ·
  <a href="https://rootrecord.cloud"><strong>rootrecord.cloud</strong></a>
</p>

---

## 🌴 What this is

**RootRecord-Pacific-Solar-Server** is the canonical Pacific runtime repository for the RootRecord ecosystem.

It contains the executable domains and orchestration that operate the Pacific node. Durable architecture, agent context, and work orders live in **RootRecord-Library**; data, media, and log placement is defined by **RootRecord-Database**.

> **Canonical runtime home.** Legacy personal-account trees are historical and are not the target for new domain work.

---

## 🧩 Runtime domains

| Directory | Role |
| --- | --- |
| ⚙️ `Automations/` | Poller, jobs, stack orchestration |
| ⚡ `Energy/` | Energy telemetry, reports & actions |
| 🖥️ `System/` | Host statistics & system services |
| 📝 `Reports/` | Runtime worklog / reporting |
| 🌦️ `Weather/` | Weather domain |
| 🌋 `Geology/` | Geology / hazard domain |
| 💬 `Communications/` | Messaging, tunnel & network communications |
| 🐙 `Github/` | Git catalog & synchronization helpers |
| 🔐 `Security/` | Security posture & camera runtime |

---

## 📐 Canonical boundaries

```text
RootRecord-Library
    │
    │  architecture / context / work orders
    ▼
RootRecord-Pacific-Solar-Server
    │
    │  executable runtime
    ▼
RootRecord-Database
    │
    │  data / media / logs
    ▼
Pacific node
```

The repositories are intentionally separated so that **code, durable context, and persistent data layout have clear homes**.

---

## 📍 Live desk path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server
```

The corresponding database tree is:

```text
/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database
```

This directory is inside the umbrella git root. It does not have its own `.git`. Desk publish uses the `ecosystem` row and the `pacific` mirror row in `Github/scripts/repos.conf`.

**2026-09-30 01:24 HST:** this path was the live poller cwd after boot. River 2 Pro BLE reads are the live energy path. Delta 2 is dead and does not transmit. What still needs Alexander: [What's left for Alexander](../../5%20-%20RootRecord-Library/Documentation/01-operations/2026-09-30-whats-left-for-alexander.md).

---

## 🛡️ Runtime discipline

- Domain imports follow Library work orders.
- Prefer canonical Pacific paths over legacy skill-desk paths.
- Credentials and other secrets stay outside Git.
- Runtime verification is evidence-based.
- A GitHub commit proves a repository change; it does **not** by itself prove runtime activation.
- Physical actuation remains explicitly authorized work.

---

## 🔗 Related repositories

| Repository | Role |
| --- | --- |
| **[RootRecord-Ecosystem](https://github.com/RootRecord-Software-Solutions/RootRecord-Ecosystem)** | Public umbrella and this desk's git root |
| **[RootRecord-Library](https://github.com/RootRecord-Software-Solutions/RootRecord-Library)** | Durable docs, agent context & work orders |
| **[RootRecord-Database](https://github.com/RootRecord-Software-Solutions/RootRecord-Database)** | Data, media & log layout |
| **[US-Mainland-Server](https://github.com/rootrecordsoftwaresolutions/US-Mainland-Server)** | Continuity node |

Work orders and migration status live in the Library under `Documentation/06-development/Work-Orders/`.

---

<p align="center">
  <strong>Root Record Software Solutions</strong><br/>
  <em>Oriented from Hawaiʻi Island · building resilient software, infrastructure, automation & AI systems</em>
</p>
