# Geology

**Canonical Pacific home** for Kīlauea / volcano observation tooling and **all earthquake functions** (Hawaiʻi-local and global).

---

## Status (2026-09-28 ~17:00 HST)

| Item | State |
| --- | --- |
| Domain folder | **`Geology/` only** (no parallel `geology` / `kilauea` / `earthquakes` runtime folders on Pacific) |
| Ownership | Desk-side observation, polling, ingest, and operator tooling |
| `jobs.py` | None yet — wire jobs here when scripts are imported |
| Data (off-git) | Prefer `/home/rootrecord/Database/` under a Geology-aligned tree (e.g. `GEOLOGY/`, `KILAUEA/`, `EARTHQUAKES/`) when introduced |
| Public products | Alert apps / websites may live in product repos; **this domain owns desk runtime** for the same capability |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Geology/
```

---

## Scope (in)

| Area | Examples |
| --- | --- |
| **Kīlauea** | Alerts ingest, status snapshots, cam helpers (if desk-side), volcano-specific weather hooks used only for Kīlauea ops |
| **Earthquakes — local** | Hawaiʻi / Pacific Island region quake feeds, local magnitude filters, island event logging |
| **Earthquakes — global** | Worldwide catalog pulls, significant-event filters, cross-region digests |
| **Shared geology ops** | Schedulers, normalize/store helpers, Database writers for the above |

## Scope (out / adjacency)

| Concern | Home |
| --- | --- |
| General island weather (non-volcano product) | `Weather/` |
| Generic security cams not tied to volcano ops | `Security/` (or A-Eyes) |
| Public marketing site only | Product / Website repos — not a substitute for this domain’s desk code |
| G2 skill paths | Migrate **into `Geology/`**; do not leave long-term runtime under `~/.ollama/skills` |

---

## Naming SOP (standing)

Same as Energy / System (see Library Pacific Domain Import Playbook):

- **One folder:** `Geology/` — no `geology` symlink, no separate `Kilauea/` or `Earthquakes/` top-level on Pacific for runtime.
- Optional **subfolders inside** Geology for clarity, e.g.:

```text
Geology/
  README.md
  scripts/
    kilauea/
    earthquakes/
      local/
      global/
  lib/
  config/
```

- Python package name, if used: **`Geology`** (matches folder). Rewrite any G2 `import kilauea` / `import earthquakes` package roots accordingly, or use submodules under `Geology/`.

---

## Import sources (when ready)

| Source | Content |
| --- | --- |
| G1 / Old | `kilauea/*`, `earthquakes` packets |
| G2 skills | Any live skill paths still under ollama for volcano/quake |
| Product repos | Copy **desk** scripts only; keep secrets out of git |

Deploy path after import: rewire `jobs.py` → quoted Pacific `Geology/…` paths → reload poller.

---

## Policy

- All new Kīlauea and earthquake **desk functions** land in **`Geology/`**.
- Do not scatter quake/volcano pollers under Weather or Automations root long-term.
- Database remains the byte authority; Geology owns the code that writes those bytes.

---

*Ownership declared 2026-09-28 HST.*
