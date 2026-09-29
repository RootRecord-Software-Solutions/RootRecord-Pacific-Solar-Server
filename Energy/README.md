# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-28 ~16:25 HST)

| Item | State |
| --- | --- |
| Domain folder | **Phase 1** — scripts + jobs on Pacific |
| Scripts | `Energy/scripts/read/` (leapfrog, delta2, river2pro) on org git |
| jobs.py | Commands + cwd point at Ecosystem Energy; paths quoted |
| `ENERGY_EFLIB_PATH` | `{PACIFIC}/Energy/lib/vendor` |
| Data writes | `/home/rootrecord/Database/ENERGY/` (never commit) |
| Logs / state | `/home/rootrecord/Database/Logs/Energy/`, `/home/rootrecord/Database/Energy/state/` |
| Live BLE cycle | **Blocked** until `Energy/lib/read_runner.py` (and related modules) exist on desk |
| Heartbeat ENERGY line | Works from Database snapshot even when BLE cycle FAILs |
| Actions / hybrid | Phase 2+ |

**Policy:** No old desk. Fill missing lib from G2 once, then own everything under Pacific Energy/.

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/
```

### Org git vs desk fill

On org main, `Energy/lib/` currently has: `config.py`, `envload.py`, `paths.py`, `py`, `vendor/`, `__init__.py`.

Read scripts **require**:

```text
Energy/lib/py → Energy/lib/read_runner.py --device {delta2|river2pro}
```

If `read_runner.py` is missing, `ecoflow_read_boot` / `ecoflow_read_cycle` exit code 1.

### Desk fill (P0)

```bash
PACIFIC="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"
G2="/home/rootrecord/.ollama/skills/energy"
mkdir -p "$PACIFIC/Energy/lib" "$PACIFIC/Energy/db" "$PACIFIC/Energy/config"
cp -an "$G2/lib/."    "$PACIFIC/Energy/lib/"
cp -an "$G2/db/."     "$PACIFIC/Energy/db/"
cp -an "$G2/config/." "$PACIFIC/Energy/config/"
chmod +x "$PACIFIC/Energy/lib/py" "$PACIFIC/Energy/scripts/read/"*.sh
# verify
ls -la "$PACIFIC/Energy/lib/read_runner.py"
export ENERGY_EFLIB_PATH="$PACIFIC/Energy/lib/vendor"
bash -x "$PACIFIC/Energy/scripts/read/delta2-read.sh" 2>&1 | tail -40
systemctl --user restart rr-rootserver-poller.service
```

After soak: commit non-secret lib modules to org Pacific (or document intentional desk-only vendor bits). Then G2 `energy/` can be archived — not used at runtime.

---

*Updated 2026-09-28 HST — systemd Pacific live; read_runner gap documented.*
