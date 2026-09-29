# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-28 ~16:40 HST) — Phase 1 LIVE + soak

| Item | State |
| --- | --- |
| Domain | **Live** on Pacific |
| Scripts | `Energy/scripts/read/` |
| jobs.py | Pacific paths (quoted) |
| Package | `Pacific/energy` → `Energy/` symlink; `lib/py` PYTHONPATH = vendor + Pacific root |
| Live reads | **OK** — alternating SUMMARY delta2 / river2pro (~15s) |
| Evidence | 16:39–16:40 HST poller window: SUMMARY + ENERGY status=live |
| Data | `/home/rootrecord/Database/ENERGY/` |
| Logs / state | `/home/rootrecord/Database/Logs/Energy/`, `/home/rootrecord/Database/Energy/state/` |
| Actions / hybrid | Phase 2+ |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/
```

### Package name (required)

```bash
cd /home/rootrecord/RootRecord-Ecosystem/1\ -\ Servers/1\ -\ RootRecord-Pacific-Solar-Server
ln -sfn Energy energy
```

### Sample live lines

```text
SUMMARY=delta2 soc=39% solar=35W ac_out=72W usbc=55W src=api db=ok
SUMMARY=river2pro soc=100% solar=0W ac_out=46W usbc=0W src=api charge=battery_transfer db=ok
ENERGY  status=live  B2=41.1%  B1=98.9%  solar=15 W  ac=58 W  src=sqlite
```

### Policy

No old desk for Energy reads. G2 `~/.ollama/skills/energy` is archive candidate after Phase 2 (actions) if desired.

---

*Phase 1 LIVE + soak confirmed 2026-09-28 HST.*
