# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Shell only** (README + `.gitkeep`) |
| Live EcoFlow / ENERGY data | **Active** via poller jobs |
| Script location today (**G2**) | `~/.ollama/skills/energy/` |
| Historical packets (**G1**) | `Solar-Pacific-RootRecord-Server-Old` → `energy/ecoflow-*` |
| Data writes | `/home/rootrecord/Database/ENERGY/` (never commit) |

**Import order:** bring **G2** skills energy tree here first (matches `jobs.py`). Only then selectively diff G1 packets for missing features.

See Library:

- `Documentation/00-architecture/Migration-Lineage-Three-Generations-2026-09-28.md`
- `Documentation/00-architecture/Solar-Pacific-Old-Inventory-Map-2026-09-28.md`
- `Documentation/00-architecture/Pacific-Domain-Import-Playbook-2026-09-28.md`

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

## jobs.py references (residual G2)

| Job id | Role |
| --- | --- |
| `ecoflow_read_boot` | ONCE_AT_START dual read |
| `ecoflow_read_cycle` | EVERY_SECONDS leap-frog |
| `heartbeat` | Builtin ENERGY snapshot (engine) |
| READS / `ecoflow_command()` | Manual/API action helpers |

**G2 path prefix:** `/home/rootrecord/.ollama/skills/energy/`

**Target after G2 import:** `Energy/scripts/…` under this repo on the Ecosystem Servers path.

---

## G1 Old packets (recover only after G2)

| Old path | Role |
| --- | --- |
| `energy/ecoflow-ble-poller` | BLE poller ancestry |
| `energy/ecoflow-automations` | Automation helpers |
| `energy/ecoflow-ac-solar-gate` | AC/solar gate |
| `energy/ecoflow-quota` | Quota |
| `energy/ecoflow-river-car` | Device-specific |

---

## Expected layout after G2 import

```text
Energy/
  README.md
  scripts/
    read/
      delta2-read.sh
      river2pro-read.sh
      leapfrog-read.sh
    actions/
```

Do not commit BLE keys, cloud API tokens, or device credentials.

---

## Import checklist (operator)

1. Provide G2 source from live `~/.ollama/skills/energy/`.
2. Copy into `Energy/`; strip secrets.
3. Rewire `Automations/scripts/jobs.py`.
4. `schedule-stack-reload` after sync.
5. Confirm SUMMARY / ENERGY lines.
6. Optional later: diff G1 `ecoflow-*` packets for unique scripts only.

---

*Docs-only update 2026-09-28 HST.*
