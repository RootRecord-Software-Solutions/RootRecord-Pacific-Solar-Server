# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-28) — Phase 1 LIVE

| Item | State |
| --- | --- |
| Domain folder | **`Energy/` only** (no lowercase `energy` sibling) |
| Python package | **`Energy`** — matches folder; rewrite G2 `import energy` → `import Energy` |
| Launcher | `Energy/lib/py` — PYTHONPATH = vendor + Pacific root |
| jobs.py | Pacific paths (quoted) |
| Data | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/ENERGY/` (sqlite store: `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/ROOTRECORD/`) |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/
```

### Package rule (standing)

Do **not** create `energy` → `Energy` symlinks. Folder name is the package name.

After any G2 copy that still says `import energy`:

```bash
find Energy -name '*.py' -print0 | xargs -0 sed -i \
  's/\bfrom energy\./from Energy./g; s/\bimport energy\./import Energy./g; s/\bimport energy\b/import Energy/g'
rm -f ../energy   # if a leftover symlink exists at Pacific root
```

### Policy

No old desk for Energy reads. See Library: `Pacific-Domain-Import-Playbook` standing rules.

---

*Naming SOP 2026-09-28 HST.*
