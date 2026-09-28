# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Shell only** (README + `.gitkeep`) |
| Live EcoFlow / ENERGY data | **Active** via poller jobs |
| Script location today | Legacy `~/.ollama/skills/energy/` (not yet imported here) |
| Data writes | `/home/rootrecord/Database/ENERGY/` (never commit) |

Until the Energy skill tree is imported into this folder, job catalog commands continue to call the legacy skills path. That is intentional and keeps the desk live.

---

## Owned by this domain (when imported)

- EcoFlow BLE / API read scripts (Delta 2, River 2 Pro)
- Leap-frog / dual-read orchestration wrappers
- Action scripts gated by `/tmp/ecoflow-ble.lock`
- Energy-facing skill docs (no secrets)

## Not owned here

- Generated samples / SOC time series → Database
- Poller engine / job catalog → `Automations/`
- Public tunnel → `Communications/network/`

---

## jobs.py references (residual)

See Library: `Documentation/00-architecture/Pacific-Jobs-Path-Inventory-2026-09-28.md`.

| Job id | Role |
| --- | --- |
| `ecoflow_read_boot` | ONCE_AT_START dual read |
| `ecoflow_read_cycle` | EVERY_SECONDS leap-frog |
| `heartbeat` | Builtin ENERGY snapshot (engine) |
| READS / `ecoflow_command()` | Manual/API action helpers |

**Historical path prefix:** `/home/rootrecord/.ollama/skills/energy/`

**Target after import:** `Energy/scripts/…` under this repo root on the Ecosystem Servers path.

---

## Expected layout after import (documentation only)

```text
Energy/
  README.md
  scripts/
    read/
      delta2-read.sh
      river2pro-read.sh
      leapfrog-read.sh
    actions/
  # local secrets / device config stay off-git
```

Do not commit BLE keys, cloud API tokens, or device credentials.

---

## Import checklist (operator)

1. Provide source tree from live `~/.ollama/skills/energy/` (or equivalent).
2. Copy into `Energy/` preserving scripts layout; strip secrets.
3. Rewire `Automations/scripts/jobs.py` paths (single commit or tightly coupled).
4. `schedule-stack-reload` after sync.
5. Confirm SUMMARY / ENERGY lines in poller window.

---

*Docs-only update 2026-09-28 HST. No script import in this commit.*
