# Github

GitHub repository catalog, sync automation, mirrors, and metadata for the Pacific desk.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder | **Shell only** (+ automation-records placeholders) |
| G2 residual | `~/.ollama/skills/github/` |
| G1 cousin | `git-auto-push/` (diff after G2) |
| Canonical Library | `RootRecord-Software-Solutions/RootRecord-Library` |
| Canonical Pacific | `RootRecord-Software-Solutions/RootRecord-Pacific-Solar-Server` |

Related: Library WO-GH, WO-OLD.

---

## jobs.py (residual G2)

| Job id | Path |
| --- | --- |
| `github_setup_remotes` | `…/skills/github/scripts/setup-all-remotes.sh` |
| `github_sync_all` | `…/skills/github/scripts/sync-all.sh` |

Align `repos.conf` local_path to Ecosystem `1 - Servers/…` when catalog is imported.

---

## Expected layout after G2 import

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

Tokens stay local — never commit.

---

*Docs-only 2026-09-28 HST.*
