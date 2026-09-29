# poller

RootRecord poller lifecycle scripts, monitoring, and display handling.

---

## Current viewer behavior

`poller-watch.py` is a **viewer**, while the poller stack remains the production service.

- **Ctrl-C / SIGTERM:** requests the full stack stop.
- **Window close / SIGHUP:** exits the viewer only; the poller remains running.
- The viewer tails the canonical Database log:
  `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log`.
- `open-poller-window.sh` starts `rr-rootserver-poller.service` and opens the viewer.
- The intended steady state is one viewer window; duplicate-window prevention/redraw work remains a pending operator-facing improvement.

### Planned viewer refinement

The next viewer pass is intended to provide:

- HST time in the header
- color-coded service status
- B1/B2 battery bars
- refresh countdown
- redraw-in-place behavior without flicker

These are **planned viewer changes**, not claims that they are already deployed.

---

## Runtime boundary

Closing the viewer must not stop the production poller. The stack-stop path remains explicit through Ctrl-C/SIGTERM and the stack scripts.

