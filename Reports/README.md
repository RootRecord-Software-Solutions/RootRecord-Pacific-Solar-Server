# Reports

Worklog and operational reporting for the Pacific desk.

**Machine SOT:** `/home/rootrecord/Database/WORKLOG/`  
**Human narrative:** Library `Documentation/01-operations/` (templates + session logs)  
**Work order:** [WO-RPT-001](https://github.com/RootRecord-Software-Solutions/RootRecord-Library/blob/main/Documentation/06-development/Work-Orders/WO-RPT-001-Reports-Worklog-Domain-Import.md)

---

## Status (2026-09-28 ~19:00 HST) — Phase B in git (desk soak)

| Item | State |
| --- | --- |
| Domain folder | **`Reports/` only** |
| scripts | `worklog_lib.sh`, `worklog_once.sh`, `worklog_poller.sh` (from G2 + hygiene) |
| jobs.py | `worklog_scan` → Pacific `Reports/scripts/worklog_once.sh` |
| Data | `/home/rootrecord/Database/WORKLOG/` |
| Daily Library roll-up | Phase C — not yet |
| Weekly archive | Phase D / WO-ARCH — not yet |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Reports/
```

### Manual one-shot

```bash
bash "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Reports/scripts/worklog_once.sh"
```

### Policy

- Path/size/mtime only — no keystrokes, clipboard, or file contents
- Never log secrets; scrub against `master-key.env` delete/key patterns
- Do not bulk-import G1 `reports.py` public draft queue in this phase
- A-Eyes / clips are not owned here

### Naming

Use **`Reports/`** only. Do not create a parallel lowercase `reports` package path for imports.

---

*WO-RPT-001 Phase A+B 2026-09-28 HST.*
