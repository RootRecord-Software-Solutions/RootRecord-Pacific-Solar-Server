# Root Monitor (Apps/Control-Panel) — RootRecord native desk control panel (GTK4 + libadwaita) and Conky readout

Added 2026-09-29 as "RootRecord Control Panel"; renamed **Root Monitor** 2026-09-29 ~13:00 HST (folder, file names and app id unchanged, so the existing launcher keeps working). A native Linux app, read-only except the Settings editor (masked diff + confirm + backup + atomic write; never restarts anything). No browser, no Chromium, no Electron, no network server. It is added **alongside** the existing viewers. `poller-dashboard.py`, `poller-watch.py`, `open-poller-window.sh`, the poller ENERGY status line and `npu-status.sh` are unchanged and still work.

State: **LANDED**. Headless `--check` PASS, settings editor tests 103/103 PASS, real-window render PASS. `--check` RSS 84.5 MB is over the 80 MB target (flagged). **VERIFY PENDING** (sign-off): default-viewer swap, autostart unit, starting Conky (now installed; config copied, not started).

## Launch

- **App menu:** "Root Monitor" (`~/.local/share/applications/rootrecord-control-panel.desktop`). The original terminal dashboard stays installed: app menu **"Poller Dashboard (terminal)"** (`rootrecord-poller-dashboard-terminal.desktop` → unchanged `open-poller-window.sh`), plus the untouched Desktop launcher and autostart entry.
- **Make Root Monitor the default viewer at login (sign-off):** `bash Packaging/swap-default-viewer.sh status|apply|revert`. `apply` moves the unchanged `~/.config/autostart/rootrecord-poller-watch.desktop` into `~/.config/autostart/.root-monitor-swap/` (sha256 kept) and installs `root-monitor.desktop`; `revert` restores it byte-identically. The poller still starts at login by itself (unit enabled via `default.target`).
- **Terminal:** `python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Apps/Control-Panel/rr_control_panel.py"`
- It runs as a single instance. A second launch raises the open window. Closing the window closes only the panel; the poller keeps running.
- **Test (no window):** `nice -n 10 python3 rr_control_panel.py --check [--camera-viewer on|off] [--no-starlink]` or `bash Tests/run-check.sh <outdir>` (both modes under `/usr/bin/time` and `strace`, then `Tests/test_settings_io.py`, which edits **temporary copies** only).
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
| Running | poller + child jobs (ports), RootRecord processes (masked cmdlines), listeners, tunnels, Ollama/FLM, systemd user + system units, timers, cron — read-only, each row links to its Settings page | `/proc`, `/proc/net/tcp*`, `systemctl list-units/list-timers`, `crontab -l` (cached 15 s), Ollama `GET /api/version|ps` on 127.0.0.1 | 5 s while visible |
| Network | per-interface rx/tx rates, totals since boot; Starlink state/uptime/latency/throughput/obstruction | `/proc/net/dev`, sysfs; `Starlink/starlink_status.py` (own venv process) | 5 s while visible; Starlink every ≥ 10 s, helper exists only while visible |
| SSH | `rr-aws`, `rr-aws-ip` (alias, user@host:port, ProxyCommand/identity present — keys never read); Open terminal; Status = `timeout 5 ssh -o BatchMode=yes rr-aws uptime`; Mainland placeholder | `~/.ssh/config` | on click only |
| AWS Fallback | one row per AWS fallback function (18, from `Lib/rr_aws_fallback.json`): RAM / disk / net estimates, fits, default; a switch per toggleable function; budget vs the 512 MB RAM / 1.5 GB disk floors (t3.micro now vs 2 GB). **Dry-run by default** (`aws_fallback_mode`): a toggle opens a confirm with the exact AWS change, then writes nothing. `write` mode (sign-off) = one SSH call: dated backup of AWS `flags/` → atomic write of `flags/<id>`. **Status** = one read-only SSH (`rr-aws-ip`) for flags, MemAvailable, disk free | catalog JSON; SSH only on button press | built on visit, **released on leave**; no timer |
| Not migrated | 23 G2/G1 placeholders with WO + state + "not migrated" | `Lib/rr_migration.json` | no timer |
| Settings | 10 sub-pages (Network, Messaging, Environment, Flags, Services/Poller, Weather, Voice, AI/NPU, Cameras, Panel) — 1,590 settings from 27 files; secrets masked; Replace/Clear/Edit with masked diff + confirm | `Lib/rr_registry.py`, `Lib/rr_config_io.py`; Panel = `settings.json` | built on visit, released on leave |

Cameras are discovered from `Security/Cameras/grab_all.sh` (`for ch in 1 2 3 4`). The Cameras page never reads `Security/Cameras/store/CONNECTION.json` (strace-checked); only the Settings → Cameras registry parses it in code and shows every value masked. Missing or flapping stills (for example during camera hardware work) are shown as "no still on disk" and are expected. If a camera has no still at all, one local still is fetched from `http://127.0.0.1:8791/current_chN.jpg`, and only while the page is visible (`camera_live_fallback`).

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
- `starlink_enabled` true, `starlink_poll_sec` 10 (minimum 10)
- `ssh_mainland_alias` "" (empty = Mainland placeholder)
- `aws_fallback_mode` **"dry-run"** (`write` is a sign-off item and also needs the AWS fallback runtime; the remote script refuses with exit 3 until `~/rootrecord/fallback/flags/` exists)
- `aws_fallback_alias` "rr-aws-ip"

Camera toggles only change what the **panel** shows. They never touch collectors, grab jobs or the poller.

**On/off controls are buttons (2026-09-29 16:15 HST).** There are no switches. Each on/off setting is a labelled toggle button, for example `Camera viewer: Off` (red outline) or `Camera viewer: On` (green), from `rr_ui.state_toggle`. The **camera viewer button** is the first row of the **Cameras** page and the first row of **Settings → Panel** (Cameras group first). The two stay in sync. It is Off by default. A click changes the running panel only; **Save settings** keeps it. Risky actions still need the confirm dialog. AWS Fallback rows (`AWS: On/Off`) keep confirm, dry-run revert and failed-write revert. Test: `Tests/test_toggle_buttons.py` (30 checks, AWS ssh stubbed) · record: `/home/rootrecord/RootRecord-Ecosystem/5 - RootRecord-Library/Documentation/07-testing/2026-09-29-root-monitor-toggle-buttons.md`.

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
| `--check`, viewer off, 14 pages incl. AWS Fallback — 15:04 HST | **85.3 MB** (A/B same run without the page: 80.9 MB → +4.4 MB when every page is built; in the window the page is released on leave) | 1.0 s |
| `--check`, viewer off (13 pages + all sub-pages built once) — 13:08 HST | **84.5 MB — over the 80 MB target** (was 73.8 MB before Running/Network/SSH/Settings) | 1.2 s |
| `--check`, viewer on | 98.9 MB — opt-in | 1.4 s |
| real window 25 s, Energy page, cairo | 85.7 MB (an empty GTK4/Adw window alone is 66–68 MB here) | 0.59 s incl. startup |
| Starlink helper (separate process, only while Network is visible) | 55.7 MB | 0.43 s per poll incl. start |
| real window, default GL renderer (not used) | ~180 MB (gl 275 MB) | — |

## Conky readout — `Conky/rootrecord.conkyrc`

The readout shows:

- the B1/B2/B3 bars and SOC text
- CPU and RAM (conky built-ins)
- load
- NPU state and poller state

The values come from `Conky/conky_readout.py` (the same read-only readers, every 15–30 s, nice 10; it never runs `npu-status.sh`).

`conky-all` 1.22.2 is installed on the desk (dpkg 12:35 HST 2026-09-29, not by this app). `Packaging/install-launcher.sh` copied the config to `~/.config/conky/rootrecord.conkyrc`; it was **not started**. Start it with `conky -c ~/.config/conky/rootrecord.conkyrc` (sign-off; autostart is a separate decision).

## Packaging

- `Packaging/rootrecord-control-panel.desktop` (Name "Root Monitor") and `Packaging/poller-dashboard-terminal.desktop` (Name "Poller Dashboard (terminal)") are installed by `Packaging/install-launcher.sh` (user level, no sudo).
- `Packaging/swap-default-viewer.sh` + `Packaging/root-monitor-autostart.desktop`: reversible default-viewer swap — **not applied** (sign-off).
- `Packaging/rootrecord-control-panel.service` is a systemd **--user** unit. It is written here only and is **NOT installed or enabled** (sign-off item). The enable commands are in the file header.

## Files

`rr_control_panel.py` · `rr_pages.py` · `rr_ui.py` · `Lib/rr_sources.py` · `Lib/rr_settings.py` · `Lib/rr_registry.py` · `Lib/rr_config_io.py` · `Lib/rr_running.py` · `Lib/rr_netstat.py` · `Lib/rr_ssh.py` · `Lib/rr_migration.json` · `rr_aws_page.py` · `Lib/rr_aws_fallback.py` · `Lib/rr_aws_fallback.json` · `Starlink/starlink_status.py` (+ gitignored `Starlink/.venv`, py3.12 + `starlink-grpc-core`) · `settings.json` · `Conky/` · `Packaging/` · `Tests/run-check.sh` · `Tests/test_settings_io.py`

Settings saves back up to `/home/rootrecord/Database/GITHUB/control-panel-settings-backups/` (0600 for secret files). Secrets are never displayed, logged or screenshotted (the `--screenshot` mode checks every PNG first).

Docs: Library `Documentation/00-architecture/Control-Panel-GTK.md` · test records `Documentation/07-testing/2026-09-29-control-panel-gtk.md`, `Documentation/07-testing/2026-09-29-root-monitor-settings-running-network-ssh.md`.


**AWS Fallback page, 2026-09-29 16:05 HST:** `settings.json` has `aws_fallback_mode: "write"` (the Phase 2 runtime is deployed on AWS). The catalog `Lib/rr_aws_fallback.json` holds the trimmed-micro profile (RAM floor 485 MB) and the `relay_send` row (sign-off). Every toggle takes a dated backup on AWS (`~/rootrecord/bin.bak-fallback-flags-<ts>/`), then writes one flag. Service flags are applied by the root `rr-fallback-apply` on AWS. Record: Library `07-testing/2026-09-29-aws-fallback-phase2-runtime-deploy.md`.
