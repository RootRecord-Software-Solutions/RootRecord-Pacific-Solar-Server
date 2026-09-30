# Github

GitHub repository catalog and automated push/pull for the Pacific desk.

---

## Status (2026-09-29 HST) — Phase 1 LIVE

| Item | State |
| --- | --- |
| Domain | **`Github/` only** |
| Scripts | `Github/scripts/` (from G2 github skill) |
| Catalog | `Github/scripts/repos.conf` (tab-separated) |
| jobs.py | `github_setup_remotes` + `github_sync_all` → Pacific paths |
| Evidence | Poller publishes ecosystem inplace, plus pacific, database, and library from mirror worktrees. The live folders stay inside the umbrella and do not have their own .git. |
| Logs / bak | `/home/rootrecord/Database/GITHUB/` |
| Token | `/home/rootrecord/master/master-key.env` (`GITHUB_TOKEN`) — never commit |

### Catalog rows

| id | enabled | mode | notes |
| --- | --- | --- | --- |
| ecosystem | 1 | inplace | `/home/rootrecord/RootRecord-Ecosystem` → `RootRecord-Software-Solutions/RootRecord-Ecosystem`. Does not auto-commit paths in `ecosystem-skip-autocommit.txt` (live telemetry, databases, logs, worklogs). A pull reloads the poller only when Pacific runtime code changes. |
| pacific | 1 | mirror | Live folder inside the ecosystem tree. Published to `RootRecord-Pacific-Solar-Server` from `Database/GITHUB/worktrees/pacific`. |
| database | 1 | mirror | Live folder inside the ecosystem tree. Published to `RootRecord-Database` from `Database/GITHUB/worktrees/database`. |
| library | 1 | mirror | Live folder inside the ecosystem tree. Published to `RootRecord-Library` from `Database/GITHUB/worktrees/library`. |
| skills | 1 | inplace | `~/.ollama/skills` → legacy Solar-Pacific remote; restore commit `1dcee66` verified intact |
| website | 0 | mirror | enable when worktree under `Database/GITHUB/worktrees/website` exists |
| mainland | 0 | inplace | enable when path is a real git clone |

### Policy

Same automation as G2; home is **`Github/`**. No parallel `github/` folder. Quote paths with spaces in jobs.

**Automatic authority (WO-GH-001 Option B, Alexander, 2026-09-29):** poller job `github_sync_all` every 5 seconds. Enabled catalog rows are `ecosystem`, `pacific`, `database`, `library`, and `skills`. Pacific, Database, and Library are mirror publishes of the live subfolders. There is no Core-Processor pull timer on this desk. Root `Pull.sh` and `Push.sh` are manual scripts, not a second timer. Do not add one.

---

*Updated 2026-09-29 HST — ecosystem stays the one git root. Pacific, Database, and Library publish from mirror worktrees so the live folders are not nested git checkouts.*
