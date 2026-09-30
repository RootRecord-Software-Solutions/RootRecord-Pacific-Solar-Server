# poller

RootRecord poller lifecycle scripts, monitoring, and display handling.

---

## Current viewer behavior

`poller-watch.py` is a **viewer**, while the poller stack remains the production service.

- **Ctrl-C / SIGTERM:** requests the full stack stop.
- **Window close / SIGHUP:** exits the viewer only; the poller remains running.
- The viewer tails the canonical Database log:
  `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log`.
- `open-poller-window.sh` starts `rr-rootserver-poller.service` (no-op if active) and opens **one** viewer window; if a viewer is already open it does nothing.

### Status dashboard — PASS (2026-09-29 02:15–02:19 HST)

`poller-dashboard.py` (default viewer; `POLLER_VIEWER=poller-watch.py` selects the scrolling log view) is **read-only**: Ctrl-C / close / SIGTERM exit the viewer only. It shows HST header, PASS/WARN/FAIL for poller, relay, BLE, globe, cam, weather, ollama, tunnel, B1/B2 battery bars, refresh countdown, in-place redraw (no flicker), and survives stack reloads and the hourly log truncation.

Verified: one viewer (pid 938130) open 226 s with no respawn; poller MainPID unchanged; second launch refused as duplicate. Evidence: `2 - RootRecord-Database/Logs/Migration/g3-poller-viewer-evidence-20260929T121959Z.md`.

Note: `poller-watch.py` still requests a full stack stop on Ctrl-C/SIGTERM (Bruce's design, unchanged).

The default dashboard header shows the log file name (`automations_current.log`) and seconds since the last write. `poller-watch.py` prints the full path in its banner. The user unit `rr-rootserver-poller.service` sets `POLLER_LOG` to that same file.

## FAIL policy

Written 2026-09-29 from the running poller. These are the codes already logged. Nothing here sends Telegram or any other alert (that waits on WO-COM-001).

### Job lines (`rootserver_poller.py`)

| Line | Meaning |
| --- | --- |
| `job:<id> OK` | Command exited 0. |
| `job:<id> FAIL code=<n>` | Command exited non-zero. Up to 20 following `job:<id> !` lines are stderr, or stdout if stderr is empty. |
| `job:<id> TIMEOUT after <n>s` | Command ran longer than that job's `timeout_sec` (default 120). |
| `job:<id> ERROR <message>` | The runner raised before a return code existed. |
| `✗ <id> FAIL code=<n>` | EcoFlow read failed (non-zero, and the script did not print `No data` or `WAITING`). |

EcoFlow reads stay quiet on success: one `SUMMARY=` or `INTERNAL=` line, or `<id> OK`. GitHub sync jobs stay quiet on success and still log FAIL.

### Dashboard rows (`poller-dashboard.py`)

| Badge | Meaning |
| --- | --- |
| PASS | Unit is `active` when the row has a unit, and the process count matches the expected count. |
| WARN | Unit is active and at least one process is running, but the count is not the expected number. |
| FAIL | The unit is not `active`, or the process count is 0. |

Rows with no unit (relay, cam, weather, tunnel) FAIL only when the process count is 0. `ollama` and `tunnel` accept any count above 0. A battery bar is yellow under 50% and red under 20%. A reading older than 900 seconds is labeled stale. Those colors are display only. They are not job FAIL codes.

### How to read the window

The header clock is HST. Service rows are poller, relay, BLE, globe, cam, weather, ollama, and tunnel. B1 is River 2 Pro, B2 is Delta 2, B3 is the laptop battery. The bottom block is the tail of `automations_current.log`. On the dashboard, Ctrl-C or closing the window exits the viewer only. Stop the stack with `Automations/scripts/stack/stop-poller-stack.sh`.

---

## Runtime boundary

Closing the viewer must not stop the production poller. The stack-stop path remains explicit through Ctrl-C/SIGTERM and the stack scripts.

