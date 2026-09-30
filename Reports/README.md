# Reports

Worklog and operational reporting for the Pacific desk — **and the structured intake spine for future radio / live-stream automation**.

**Machine SOT:** `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Worklog/`  
**News (2026-09-29):** `News/` — G0 Hawaiʻi state news collector port (on demand; job PROPOSED; smoke rc 0 but 0 posts, see `News/README.md`)  
**Human narrative:** Library `Documentation/01-operations/` (templates + session logs)  
**Work order:** [WO-RPT-001](https://github.com/RootRecord-Software-Solutions/RootRecord-Library/blob/main/Documentation/06-development/Work-Orders/WO-RPT-001-Reports-Worklog-Domain-Import.md)

---

## Why this domain exists (perspective)

In the old skill-tree era, AIs **heavily automated reports** — useful for radio, live streaming, and public status, but **messy**: sprawling packets (`reports.py` draft queues, hourly clips, day-board, merged-morning), unclear ownership, and easy confusion with ops worklogs.

WO-RPT-001 deliberately **stabilizes the foundation first**:

1. Measured file activity → Database/WORKLOG (no secrets, domain tags)
2. Thin daily roll-up → Library (human-readable, not invention)
3. Weekly log archive + closed WOs → `Complete/`

That is not the end state. It is the **clean spine** so a later AI-processing redesign can attach:

| Future layer (not in Phase B–D) | Feeds from | Consumers |
| --- | --- | --- |
| Structured day / hour digests | WORKLOG tags + domain LIVE status | Radio rundown, stream overlays |
| Public / voice-safe summaries | Carly-sealed measured facts | Ava public voice, Discord/Telegram |
| Clip / A-Eyes pointers | A-Eyes domain (separate owner) | Stream segments, highlight reels |
| Draft queue (G1 `reports.py` ideas) | Diff-only recovery | Website / status boards |

**Do not** collapse A-Eyes, Communications, or Website into this folder. Reports **aggregates and shapes**; those domains **own capture and delivery**.

When AI processing is redesigned, prefer:

- Python + templates + measured inputs first (Carly WO rules apply to any auto-draft)
- Optional local LLM only for prose after structure exists
- Explicit seal before anything leaves the desk for radio/stream/public

---

## Status (2026-09-28) — Phase B LIVE · C/D scripts shipped · E done

| Item | State |
| --- | --- |
| Domain folder | **`Reports/` only** |
| worklog | `worklog_lib.sh`, `worklog_once.sh`, `worklog_poller.sh` |
| jobs.py | `worklog_scan` 90s; `reports_daily_roll_up` 18:30; `reports_weekly_archive` 19:00 |
| Data | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Worklog/` |
| Radio / stream pipeline | **Deferred** — spine ready; no on-air automation in this phase |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Reports/
```

### Manual commands

```bash
bash "…/Reports/scripts/worklog_once.sh"
bash "…/Reports/scripts/daily_roll_up.sh"
DRY_RUN=1 bash "…/Reports/scripts/weekly_archive_logs.sh"
```

### Template reports (2026-09-29, gated)

`template_fill.py` fills the four Library ops templates (`Documentation/01-operations/templates/`) from measured data,
in the templates' exact structure; `template_validate.py` rejects any heading / table-column / vocabulary mismatch and
flags numbers not found in the sources. Output: non-git `test-reports/Templates/<Template-Name>_current.md` (+ `Archive/`),
never the Library; publishing to the Library stays manual. Free text only: `rr-exec` via `run-infer.sh` (facts-only prompt; unsupported drafts fall back to fixed text).
Job `template_reports_daily` 18:40, **OFF** unless `RR_TEMPLATE_REPORTS=1`. Doc: Library `00-architecture/Template-Report-Generation.md`.

```bash
python3 "…/Reports/template_fill.py" --all --draft none --dry-run     # validate only, no writes, no model
python3 "…/Reports/template_fill.py" --template checkpoint --draft none
python3 "…/Reports/template_validate.py" --help
```

### Policy

- Path/size/mtime only — no keystrokes, clipboard, or file contents
- Never log secrets; scrub against `master-key.env`
- Closed **WOs** → `Work-Orders/Complete/`
- Prefer `jobs.py` over standalone `worklog_poller.sh`
- Future radio/stream features **extend** this domain; they do not replace measured intake

---

*WO-RPT-001 foundation 2026-09-28 HST. Radio/live-stream integration = later redesign.*
