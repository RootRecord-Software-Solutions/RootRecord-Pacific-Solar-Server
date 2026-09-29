# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-28 ~16:38 HST) — Phase 1 LIVE

| Item | State |
| --- | --- |
| Domain | **Live** on Pacific |
| Scripts | `Energy/scripts/read/` |
| jobs.py | Pacific paths (quoted) |
| Package import | `Pacific/energy` → symlink to `Energy/` + `lib/py` puts Pacific root on PYTHONPATH |
| Live reads | **OK** — SUMMARY delta2 + river2pro (api/db) observed |
| Data | `/home/rootrecord/Database/ENERGY/` |
| Logs / state | `/home/rootrecord/Database/Logs/Energy/`, `/home/rootrecord/Database/Energy/state/` |
| Actions / hybrid | Phase 2+ |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/
```

### Package name (required on Linux)

Python imports use lowercase `energy` (`import energy.db.ingest`). Folder on disk is `Energy/`.

On every desk checkout:

```bash
cd /home/rootrecord/RootRecord-Ecosystem/1\ -\ Servers/1\ -\ RootRecord-Pacific-Solar-Server
ln -sfn Energy energy
```

`Energy/lib/py` sets:

```text
PYTHONPATH = ENERGY_EFLIB_PATH|vendor : Pacific_root : …
```

### Verify

```bash
export ENERGY_EFLIB_PATH="$PWD/lib/vendor"   # from Energy/
bash scripts/read/delta2-read.sh
# expect: SUMMARY=delta2 soc=… src=api db=ok
```

### Policy

No old desk for Energy reads. G2 `~/.ollama/skills/energy` is source-of-copy only until archived after soak.

---

*Phase 1 live 2026-09-28 HST.*
