# Github

GitHub repository catalog and automated push/pull for the Pacific desk.

---

## Status (2026-09-30 02:00 HST) — Phase 1 LIVE

| Item | State |
| --- | --- |
| Domain | **`Github/` only** |
| Scripts | `Github/scripts/` (from G2 github skill) |
| Catalog | `Github/scripts/repos.conf` (tab-separated) |
| jobs.py | `github_setup_remotes` + `github_sync_all` → Pacific paths |
| Evidence | Poller publishes ecosystem inplace, plus pacific, database, library, and website from mirror worktrees. The live folders stay inside the umbrella and do not have their own .git. `website` publishes `Website/Home/` only |
| Logs / bak | `2 - RootRecord-Database/Github/` (flags, logs). Worktrees: `Github-worktrees/` at the ecosystem root |
| Token | `/home/rootrecord/master/master-key.env` (`GITHUB_TOKEN`) — never commit |

### Catalog rows

| id | enabled | mode | notes |
| --- | --- | --- | --- |
| ecosystem | 1 | inplace | `/home/rootrecord/RootRecord-Ecosystem` → `RootRecord-Software-Solutions/RootRecord-Ecosystem`. Does not auto-commit paths in `ecosystem-skip-autocommit.txt` (live telemetry, databases, logs, worklogs). A pull reloads the poller only when Pacific runtime code changes. |
| pacific | 1 | mirror | Live folder inside the ecosystem tree. Published to `RootRecord-Pacific-Solar-Server` from `Github-worktrees/pacific`. |
| database | 1 | mirror | Live folder inside the ecosystem tree. Published to `RootRecord-Database` from `Github-worktrees/database`. |
| library | 1 | mirror | Live folder inside the ecosystem tree. Published to `RootRecord-Library` from `Github-worktrees/library`. |
| skills | 0 | inplace | Retired 2026-09-30. Checkout moved to `Old repos deleted and merged/ollama-skills-g2-2026-09-30`. `~/.ollama/skills` is Ollama's. Leave this row off |
| website | 1 | mirror | `Website/Home/` → `RootRecord-Software-Solutions/RootRecord-Website`. Vercel builds that repository. A merge of this row does not reload the poller |
| mainland | 0 | inplace | Disabled. Path is the archived empty `us-mainland-server` folder. Live desk is `1 - Servers/2 - RootRecord-US-Mainland-Server`. Leave it off |

### Policy

Same automation as G2; home is **`Github/`**. No parallel `github/` folder. Quote paths with spaces in jobs.

**Automatic authority (WO-GH-001 Option B, Alexander, 2026-09-29):** poller job `github_sync_all` every 5 seconds. Enabled catalog rows are `ecosystem`, `pacific`, `database`, `library`, and `website`. Pacific, Database, and Library are mirror publishes of the live subfolders. `website` mirror-publishes `Website/Home/` only. There is no Core-Processor pull timer on this desk. Root `Pull.sh` and `Push.sh` are manual scripts, not a second timer. Do not add one. Do not re-enable `skills`. Do not bind port 3001.

---

*Updated 2026-09-30 20:05 HST — `website` publishes `Website/Home/` to `RootRecord-Software-Solutions/RootRecord-Website`. `skills` and `mainland` stay off.*
