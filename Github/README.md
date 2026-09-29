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
| Evidence | Poller syncs pacific, database, library, and skills; website/mainland remain disabled |
| Logs / bak | `/home/rootrecord/Database/GITHUB/` |
| Token | `/home/rootrecord/master/master-key.env` (`GITHUB_TOKEN`) — never commit |

### Catalog rows

| id | enabled | mode | notes |
| --- | --- | --- | --- |
| pacific | 1 | inplace | Ecosystem Pacific → org `RootRecord-Pacific-Solar-Server` |
| database | 1 | inplace | Ecosystem Database → org `RootRecord-Database` |
| library | 1 | inplace | Ecosystem Library → org `RootRecord-Library` |
| skills | 1 | inplace | `~/.ollama/skills` → legacy Solar-Pacific remote; restore commit `1dcee66` verified intact |
| website | 0 | mirror | enable when worktree under `Database/GITHUB/worktrees/website` exists |
| mainland | 0 | inplace | enable when path is a real git clone |

### Policy

Same automation as G2; home is **`Github/`**. No parallel `github/` folder. Quote paths with spaces in jobs.

---

*Updated 2026-09-29 HST — skills restore state and current sync boundaries documented.*
