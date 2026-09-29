# Control-Panel — RootRecord native desk panel (GTK4 + libadwaita) and Conky readout

Added 2026-09-29. A **read-only** native Linux app. No browser, no Chromium, no Electron, no network server. It is added **alongside** the existing viewers. `poller-dashboard.py`, `poller-watch.py`, `open-poller-window.sh`, the poller ENERGY status line and `npu-status.sh` are unchanged and still work.

State: **LANDED**. Headless `--check` PASS, real-window render PASS (screenshots below). The Conky widget and the autostart unit are **VERIFY PENDING**: conky is not installed and the unit is not enabled.

## Launch

- **App menu:** "RootRecord Control Panel". The launcher is installed at `~/.local/share/applications/rootrecord-control-panel.desktop`.
- **Terminal:** `python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Apps/Control-Panel/rr_control_panel.py"`
- It runs as a single instance. A second launch raises the open window. Closing the window closes only the panel; the poller keeps running.
- **Test (no window):** `nice -n 10 python3 rr_control_panel.py --check [--camera-viewer on|off]` or `bash Tests/run-check.sh <outdir>`. The suite runs both modes under `/usr/bin/time` and `strace`.
- **Other modes:** `--screenshot DIR` opens the window, saves a PNG of every page and quits. `--run-for SEC` opens the window, quits after SEC seconds and prints peak RSS.

## Pages and data sources (all read-only)

| Page | Shows | Reads | When |
| --- | --- | --- | --- |
| header (always) | poller PASS/WARN/FAIL, B1/B2/B3 SOC, log age, HST clock | `Energy/soc/*-last.json`, sysfs `BAT*`, `/proc/*/cmdline`, log mtime | every 5 s |
| Energy | the three battery bars from `poller-dashboard.py` (B1 river2pro, B2 delta2, B3 System laptop), a watts table, the poller **status line** (latest `ENERGY` heartbeat incl. B3 expansion / `LAP=` when present), SUMMARY lines, SUN | `Energy/soc/{river2pro,delta2}-last.json`, `Energy/watts/*-last.json`, `/sys/class/power_supply`, last 64 KB of `Logs/Automations/automations_current.log`, NOAA solar table via `poller-watch.aeyes_solar_state()` | 5 s while visible |
| Weather | sun state, zone forecast Today/Tonight + advisories (default zone "Honolulu Metro") | `Weather/Hawai'i/reports/0 Level Processing/zfp_zone_forecast_current.md` (re-parsed only when mtime changes), `Hawaii_State_Weather_Report_current.md` head, solar table | 5 s while visible |
| System | CPU / RAM bars, load, 5-min averages, poller SYSTEM line | `System/last/host-last.json`, `System/status/system-status.json`, log tail | 5 s while visible |
| NPU | `/dev/accel`, FLM on-demand state, inference lock; **Run npu-status.sh** button (nice 10, output shown) | `/dev/accel`, `/proc`, `/proc/net/tcp` (:52625), `Github/plumbing/state/holder.txt` | 5 s while visible; script only on click |
| AI log | request count, today, routes/models/callers, latency, fallbacks, exits, routing rows, report head | `Logs/AI/Inference/inference_current.jsonl` (re-read only when size/mtime changes), `Logs/AI/Routing/routing_current.jsonl`, `Logs/AI/Reports/ai-processing-report_current.md` | 5 s while visible |
| Poller / services | the same 8 rows and PASS/WARN/FAIL rule as the dashboard (poller, relay, BLE, globe, cam, weather, ollama, tunnel) + MainPID, log age, recent log formatted with `poller-watch.format_line` | `/proc/*/cmdline`, `systemctl [--user] show -p Id,ActiveState,MainPID` (2 calls), log tail | 5 s while visible |
| Cameras | latest on-disk still per enabled camera (ch1–ch4) | directory listing + at most one JPEG per camera from `2 - RootRecord-Database/Media/Images/` | **OFF by default**; when on, every 10 s **only while the page is visible** |
| Controls | safe actions; risky actions (disabled, need sign-off); gated `RR_*` flags list | `Automations/scripts/jobs.py` (text scan only) | 5 s while visible |
| Settings | every setting + Known URLs + camera toggles | `settings.json` | on Save |

Cameras are discovered from `Security/Cameras/grab_all.sh` (`for ch in 1 2 3 4`). `Security/Cameras/store/CONNECTION.json` is **never** read (strace-checked). Missing or flapping stills (for example during camera hardware work) are shown as "no still on disk" and are expected. If a camera has no still at all, one local still is fetched from `http://127.0.0.1:8791/current_chN.jpg`, and only while the page is visible (`camera_live_fallback`).

## Settings — one file: `settings.json`

The keys and their defaults:

- `refresh_sec` 5
- `gsk_renderer` "cairo" (lightest renderer measured)
- `database_root`, `pacific_root`
- `stale_after_sec` 900
- `weather_zone` "Honolulu Metro"
- `log_lines` 40
- `flm_port` 52625
- `start_page` "energy"
- `camera_viewer_enabled` **false**
- `camera_refresh_sec` 10
- `camera_live_fallback` true
- `camera_live_fallback_url` (localhost only)
- `cameras` {chN: enabled, label}
- `risky_actions_enabled` **false**
- `risky_actions` [...]
- `known_urls` [...]

Camera toggles only change what the **panel** shows. They never touch collectors, grab jobs or the poller.

**Known URLs** hold a name and a URL only. You can add, edit and remove them. Clicking one opens it with `xdg-open`. URLs carrying `user:pass@` or token/key/password query parameters are refused. The seed list came from read-only discovery in `poller-watch.py`, `rootserver_poller.py`, `cam_server.py`, `ollama-warmup.sh` and `run-infer.sh`: poller `/`, `/energy` and `/system-status.json` on :8799, the public rootserver and `/aeyes`, local A-EYES :8791, Ollama :11434 and FLM :52625. It contains **no secrets**.

## Controls and safety

- **Safe:** Open Logs folder, Open Database folder, Run `npu-status.sh`, Open the poller dashboard. The dashboard button opens `poller-dashboard.py` in a new ptyxis window (read-only; it refuses if one is already open). It does **not** call `open-poller-window.sh`, because that script also runs `systemctl --user start`.
- **Risky — NEEDS SIGN-OFF:** poller restart, Telegram send, voice playback/send, enabling gated `RR_*` flags.
  - Each button is disabled unless `risky_actions_enabled` is true **and** the action has `"signed_off": true` **and** it has an `argv`.
  - Each needs a confirm dialog.
  - Only the poller restart has a command. Telegram, voice and `RR_*` are "not wired" until a command is signed off.
  - Agents must never click them.

## Resource use (2026-09-29, measured)

| Mode | Peak RSS | CPU |
| --- | --- | --- |
| `--check`, camera viewer off (default) | 73.8 MB (time -v 76.7 MB) — **PASS < 80 MB** | 0.40 s |
| `--check`, camera viewer on (4 stills decoded to ≤640×360) | 87.8 MB (time -v 89.9 MB) — over 80 MB; opt-in only | 0.50 s |
| real window 30 s, viewer off, cairo renderer | 85.0 MB — over 80 MB (an empty GTK4/Adw window alone is 66–68 MB here) | 0.58 s incl. startup |
| real window, default GL renderer (not used) | ~180 MB (gl 275 MB) | — |

## Conky readout — `Conky/rootrecord.conkyrc`

The readout shows:

- the B1/B2/B3 bars and SOC text
- CPU and RAM (conky built-ins)
- load
- NPU state and poller state

The values come from `Conky/conky_readout.py` (the same read-only readers, every 15–30 s, nice 10; it never runs `npu-status.sh`).

Conky is **not installed** on the desk. `sudo apt install conky-all` is a sign-off item. After that, run `bash Packaging/install-launcher.sh`, which copies the config to `~/.config/conky/`. Start it manually with `conky -c ~/.config/conky/rootrecord.conkyrc`.

## Packaging

- `Packaging/rootrecord-control-panel.desktop` is installed by `Packaging/install-launcher.sh` (user level, no sudo).
- `Packaging/rootrecord-control-panel.service` is a systemd **--user** unit. It is written here only and is **NOT installed or enabled** (sign-off item). The enable commands are in the file header.

## Files

`rr_control_panel.py` · `Lib/rr_sources.py` · `Lib/rr_settings.py` · `settings.json` · `Conky/` · `Packaging/` · `Tests/run-check.sh`

Docs: Library `Documentation/00-architecture/Control-Panel-GTK.md` · test record `Documentation/07-testing/2026-09-29-control-panel-gtk.md`.
