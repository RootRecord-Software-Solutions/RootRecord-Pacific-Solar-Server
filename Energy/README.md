# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-28) — Phase 1 imported

| Item | State |
| --- | --- |
| Domain folder in this repo | **Phase 1 live read path** |
| Scripts | `Energy/scripts/read/` (leapfrog, delta2, river2pro) |
| Runtime | `Energy/lib/` + `Energy/db/` + `Energy/config/` (fill from G2 if incomplete after pull) |
| Data writes | `/home/rootrecord/Database/ENERGY/` (never commit) |
| Actions / hybrid reports | **Not yet** (Phase 2+) |
| jobs.py | **Rewired** to Ecosystem `Energy/scripts/read/` |

Source: G2 `Solar-Pacific-RootRecord-Server` `energy/` (read + lib + db + config).

`ENERGY_EFLIB_PATH` job env points at live G2 vendor for BLE until vendor is vendored into this repo.

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

### After pull on the desk

1. `git pull` on Pacific Ecosystem checkout
2. If `Energy/lib/read_runner.py` missing, copy from `~/.ollama/skills/energy/lib` (and db/config)
3. `schedule-stack-reload` / full stop-start
4. Confirm SUMMARY lines in poller window

Do not delete `~/.ollama/skills/energy` until soak is done.

---

*Phase 1 import 2026-09-28 HST.*
