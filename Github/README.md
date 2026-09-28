# Github

GitHub repository catalog, sync automation, mirrors, and metadata for the Pacific desk.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Shell only** (+ automation-records placeholders) |
| Catalog / sync scripts today | Legacy `~/.ollama/skills/github/` |
| Canonical Library remote | `RootRecord-Software-Solutions/RootRecord-Library` |
| Canonical Pacific remote | `RootRecord-Software-Solutions/RootRecord-Pacific-Solar-Server` |

Related work order: Library WO-GH (catalog hygiene).

---

## jobs.py references (residual)

| Job id | Legacy path |
| --- | --- |
| `github_setup_remotes` | `…/skills/github/scripts/setup-all-remotes.sh` |
| `github_sync_all` | `…/skills/github/scripts/sync-all.sh` (every 300s) |

**Note:** Catalog `repos.conf` local_path for Pacific/skills should eventually point at Ecosystem `1 - Servers/…` (WO-GH / WO-SRV).

---

## Expected layout after import (docs only)

```text
Github/
  README.md
  scripts/
    repos.conf
    setup-all-remotes.sh
    sync-all.sh
    push-repo-once.sh
    setup-remote.sh
  automation-records/
```

Tokens stay in local env / master-key — never commit.

---

*Docs-only update 2026-09-28 HST.*
