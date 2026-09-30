# DirectoryBrowser

One-level listing of a directory the caller names. On demand. No poller and no listening port.

---

## Status (2026-09-30 HST — WO-MIG-47)

| Item | State |
| --- | --- |
| Domain folder | **`Security/DirectoryBrowser/` only** (no lowercase twin) |
| Package | `scripts/DirectoryBrowser` |
| CLI | `scripts/directory_browser.py` — `--root` required |
| Listener | None. No `serve` command. File bytes are not read. |
| Data | Database `2 - RootRecord-Database/Security/DirectoryBrowser/` — README only |
| Logs | Database `Logs/Security/DirectoryBrowser/` — reserved. The CLI prints JSON and does not write a log file. |
| jobs.py | Not edited. No periodic job. |
| Secrets | None |

### Command

```text
python3 directory_browser.py --root DIR [--rel REL]
```

`--root` has no default. A relative path containing `..` is refused. A directory symlink on the way to `--rel` is refused. A symlink whose target resolves outside `--root` is listed under `refused` and is not followed.

The old `/directory` browser in `operations/broadcast.py` bound `0.0.0.0:8080` and served `/home/ava-core`. That server is not ported. `broadcast.py` stays in the old repo because it also serves EcoFlow, system, uptime, and static pages. EcoFlow BLE, the poller, Hawaiʻi weather, the globe collector, camera grabs, Kokoro, and `geology_collect.py` are untouched.
