# Reports

Worklog and operational reporting for the Pacific desk.

**Machine SOT:** `/home/rootrecord/Database/WORKLOG/`  
**Human narrative:** Library `Documentation/01-operations/` (templates + session logs)  
**Work order:** [WO-RPT-001](https://github.com/RootRecord-Software-Solutions/RootRecord-Library/blob/main/Documentation/06-development/Work-Orders/WO-RPT-001-Reports-Worklog-Domain-Import.md)

---

## Status (2026-09-28 ~19:15 HST) — Phase B LIVE · C/D scripts shipped

| Item | State |
| --- | --- |
| Domain folder | **`Reports/` only** |
| worklog | `worklog_lib.sh`, `worklog_once.sh`, `worklog_poller.sh` |
| jobs.py | `worklog_scan` every 90s; `reports_daily_roll_up` ON_AT 18:30; `reports_weekly_archive` ON_AT Sun 19:00 |
| Data | `/home/rootrecord/Database/WORKLOG/` |
| Desk soak | **Confirmed** Phase B |
| Daily Library roll-up | **Phase C** — `daily_roll_up.sh` |
| Weekly log archive | **Phase D** — `weekly_archive_logs.sh` (WO-ARCH) |
| G1 marker | **Phase E** — `reports/MIGRATED.md` on -Old |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Reports/
```

### Manual commands

```bash
# one worklog scan
bash "…/Reports/scripts/worklog_once.sh"

# daily session auto summary → Library ops logs
bash "…/Reports/scripts/daily_roll_up.sh"

# weekly log archive (dry run first)
DRY_RUN=1 bash "…/Reports/scripts/weekly_archive_logs.sh"
bash "…/Reports/scripts/weekly_archive_logs.sh"
```

### Policy

- Path/size/mtime only — no keystrokes, clipboard, or file contents
- Never log secrets; scrub against `master-key.env`
- Closed **WOs** → `Work-Orders/Complete/` (not weekly trees)
- Prefer `jobs.py` over standalone `worklog_poller.sh`

---

*WO-RPT-001 B LIVE · C/D scripts 2026-09-28 HST.*
