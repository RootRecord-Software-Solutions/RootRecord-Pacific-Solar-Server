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

---

## Runtime boundary

Closing the viewer must not stop the production poller. The stack-stop path remains explicit through Ctrl-C/SIGTERM and the stack scripts.

