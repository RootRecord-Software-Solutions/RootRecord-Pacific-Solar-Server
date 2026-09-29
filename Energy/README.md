# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-28) — Phase 1 desk fill done

| Item | State |
| --- | --- |
| Domain folder in this repo | **Phase 1 live read path** |
| Scripts | `Energy/scripts/read/` (leapfrog, delta2, river2pro) |
| Runtime | `Energy/lib/` + `Energy/db/` + `Energy/config/` (desk filled from G2) |
| Data writes | `/home/rootrecord/Database/ENERGY/` (never commit) |
| Logs / state | `/home/rootrecord/Database/Logs/Energy/`, `/home/rootrecord/Database/Energy/state/` |
| Actions / hybrid reports | **Not yet** (Phase 2+) |
| jobs.py | **Rewired** to Ecosystem `Energy/scripts/read/`; `ENERGY_EFLIB_PATH` → `Energy/lib/vendor` |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/
```

### jobs rewired

| Job | Path |
| --- | --- |
| ecoflow_read_boot | dual delta2 + river2pro under flock |
| ecoflow_read_cycle | `Energy/scripts/read/leapfrog-read.sh` every 15s |
| READS helpers | same read/ scripts |

### After this push on the desk

```bash
PACIFIC="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"
cd "$PACIFIC"
git pull --ff-only origin main
./Automations/scripts/stack/schedule-stack-reload.sh
tail -f /home/rootrecord/Database/Logs/Automations/automations_current.log
```

Do not delete `~/.ollama/skills/energy` until soak is done.

---

*Phase 1 import + desk fill + path tighten 2026-09-28 HST.*
