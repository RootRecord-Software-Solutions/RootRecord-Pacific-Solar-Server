# System

Host operating-system integration, system sampling, and desk host services.

---

## Status (2026-09-28 ~16:43 HST) — Phase 1 import

| Item | State |
| --- | --- |
| Domain | **Phase 1** — sys-sample on Pacific |
| jobs.py | `sys_stats_cycle` → `System/scripts/sys-sample.sh` (quoted) |
| Sample writes | `/home/rootrecord/Database/SYSTEM/` |
| Plumbing (ollama/flm) | Still G2 — optional later under `System/scripts/plumbing/` |
| worklog | Still G2 reports/ |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/System/
```

### Desk fill (from G2)

```bash
PACIFIC="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"
G2="/home/rootrecord/.ollama/skills/system-stats"

mkdir -p "$PACIFIC/System/scripts" "$PACIFIC/System/lib"
# scripts
cp -an "$G2/scripts/." "$PACIFIC/System/scripts/" 2>/dev/null || true
# if sys-sample only at scripts root:
cp -an "$G2/scripts/sys-sample.sh" "$PACIFIC/System/scripts/" 2>/dev/null || true
# lib helpers (sample.py etc.)
cp -an "$G2/lib/." "$PACIFIC/System/lib/" 2>/dev/null || true
chmod +x "$PACIFIC/System/scripts/"*.sh 2>/dev/null || true

# smoke
bash "$PACIFIC/System/scripts/sys-sample.sh"
ls -lt /home/rootrecord/Database/SYSTEM/samples/ | head -5

# apply jobs rewire
cd "$PACIFIC" && git pull --ff-only origin main
systemctl --user restart rr-rootserver-poller.service
```

### Expected layout

```text
System/
  README.md
  scripts/
    sys-sample.sh
  lib/          # sample.py etc. if present on G2
```

### Policy

No old desk for sys-stats once fill + restart succeed. G2 system-stats becomes archive-only.

---

*Phase 1 jobs rewire 2026-09-28 HST — desk fill required.*
