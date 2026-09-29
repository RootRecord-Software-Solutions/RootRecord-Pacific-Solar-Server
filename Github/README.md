# Github

GitHub repository catalog and **automated push/pull (sync)** for the Pacific desk.

---

## Status (2026-09-28 ~17:05 HST) — Phase 1 import

| Item | State |
| --- | --- |
| Domain folder | **`Github/` only** (no parallel `github` symlink) |
| Scripts | Import from G2 `~/.ollama/skills/github/` → `Github/scripts/` |
| Catalog | `Github/scripts/repos.conf` — same repo **ids** as old; **local_path** + **org** remotes updated |
| jobs.py | `github_setup_remotes` + `github_sync_all` → Pacific paths (after rewire) |
| Logs | Prefer `/home/rootrecord/Database/GITHUB/logs/` (not Pacific Logs/) |
| Tokens | Local only — never commit |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Github/
```

### Expected layout after desk fill

```text
Github/
  README.md
  scripts/
    repos.conf
    setup-all-remotes.sh
    sync-all.sh
    push-repo-once.sh
    setup-remote.sh
    …
  automation-records/
  metadata/
  mirrors/
  repositories/
```

### Canonical org (standing)

| Id (typical) | Remote |
| --- | --- |
| pacific / server | `RootRecord-Software-Solutions/RootRecord-Pacific-Solar-Server` |
| database | `RootRecord-Software-Solutions/RootRecord-Database` |
| library | `RootRecord-Software-Solutions/RootRecord-Library` |

Plus the **same additional rows** as the old catalog (skills, website, mainland, …) with corrected `local_path` under Ecosystem or documented desk paths. Do not invent new ids unless the old `repos.conf` had them.

### Policy

- Same automation behavior as G2; new home is **`Github/`**.
- No force-push; no secrets in git.
- Quote Pacific paths with spaces in jobs.

---

*Phase 1 import started 2026-09-28 HST.*
