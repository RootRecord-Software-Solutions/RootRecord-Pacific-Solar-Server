# ==============================================================================
# # INFO — MUST HAVE (future agents / operators)
# ------------------------------------------------------------------------------
# Ctrl-C in the poller window / `rootserver-poller stop` MUST kill the whole stack
# (poller + cloudflared + systemd unit). Never "window only".
# Data intake → /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Intake/
# Baks/logs  → /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Github/
# GitHub catalog: Github/scripts/repos.conf (same ids as G2; Ecosystem local_path).
# Pacific .gitignore excludes us-mainland-server/ (own repo). No rclone / aws-sync.
# Inference: prefer FLM llama3.2:1b on NPU (:52625), loaded on demand by run-infer.sh; Ollama dolphin lanes = CPU fallback.
# Telegram council-relay via coms/telegram (one getUpdates). Plumbing single-flight.
#
# Deploy format (standing, all future builds):
#   push to GitHub → github_sync_all merge → schedule-stack-reload full stop/start + window.
#   Do not suggest parallel pollers or default manual restart after ordinary pushes.
#
# Internet gate:
#   needs_internet=True jobs skip while offline; tunnel deferred; ensure_tunnel_online each minute.
#   Local jobs (BLE, Ollama, FLM, heartbeat, worklog, reports roll-up/archive) always run.
#
# File layout (standing): keep SECTION banners + TEMPLATE blocks.
# Energy + System + Reports LIVE (WO-RPT-001). Residual: energy-action retirement verification; Telegram and Security Pacific surfaces landed, runtime verification pending.
# Live runtime: /home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server
# Paths with spaces MUST be double-quoted in every bash command string.
# ==============================================================================
#
# HOW TO ADD A JOB (no AI required)
#   1) Copy the blank TEMPLATE block from the matching section below.
#   2) Paste it inside that section's list (keep the commas).
#   3) Set enabled=True, fill labeled fields.
#   4) Keep the same key order and quoting style as the examples.
#   5) Code apply is automatic after GitHub pull; manual restart only if hung/operator asks.
#
# ACTION TYPES
#   builtin  — engine built-in (see labels on each live job)
#   command  — shell string run with bash -lc
#
# BOOT ORDER
#   ON_BOOT runs first, sorted by priority (0 = highest / first).
#   Then ONCE_AT_START (if any).
#   Then recurring: EVERY_SECONDS / EVERY_MINUTE / EVERY_HOUR / ON_AT.
# ON_AT = exact local wall-clock HH:MM (desk TZ = HST). Example: at_times=["13:00"]
# ====================================================

import os  # env gates below are read once, at poller start (jobs.py is imported once)

DEFAULTS = {
    "enabled": False,
    "timeout_sec": 120,
    "cwd": "",
    "env": {},
}

PACIFIC = "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"

# Paths with spaces: always double-quote inside bash command strings.
ECOFLOW_DUAL_READ = (
    "flock -w 90 /tmp/ecoflow-ble.lock bash -c "
    f"'ok=0; "
    f"bash \"{PACIFIC}/Energy/scripts/read/delta2-read.sh\" && ok=1 || true; "
    f"bash \"{PACIFIC}/Energy/scripts/read/river2pro-read.sh\" && ok=1 || true; "
    "exit $((1-ok))'"
)

ON_BOOT = [
    {
        "id": "self_terminal",
        "enabled": True,
        "priority": 0,
        "description": "This desk process + status terminal (self registry).",
        "builtin": "self_process",
        "command": "",
        "process": f"{PACIFIC}/Automations/scripts/rootserver_poller.py",
        "terminal": "RootRecord poller — rootserver",
        "watch": f"{PACIFIC}/Automations/scripts/poller/poller-watch.py",
        "timeout_sec": 5,
        "cwd": "",
        "env": {},
    },
    {
        "id": "cloudflare_tunnel",
        "enabled": True,
        "priority": 1,
        "description": "Start Cloudflare tunnel when internet is up (deferred if offline).",
        "builtin": "tunnel_start",
        "command": "",
        "public_host": "rootserver.rootrecord.cloud",
        "token_file": "/home/rootrecord/.cloudflared/rootserver.token",
        "cloudflared_bin": f"{PACIFIC}/Communications/network/cloudflare/bin/cloudflared",
        "local_service": "http://127.0.0.1:8799",
        "timeout_sec": 45,
        "needs_internet": True,
        "cwd": "",
        "env": {},
    },
    {
        "id": "github_setup_remotes",
        "enabled": True,
        "priority": 2,
        "description": "Ensure remotes for all repos.conf rows (Pacific Github catalog).",
        "builtin": "",
        "command": f'bash "{PACIFIC}/Github/scripts/setup-all-remotes.sh"',
        "timeout_sec": 180,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Github",
        "env": {},
    },
    {
        "id": "ollama_warmup",
        "enabled": True,
        "priority": 3,
        "description": "Ensure ollama serve is up (CPU fallback lanes).",
        "builtin": "",
        "command": "bash '/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/System/scripts/plumbing/ollama-warmup.sh'",
        "timeout_sec": 120,
        "cwd": "/home/rootrecord",
        "env": {},
    },
    {
        "id": "flm_npu_warmup",
        "enabled": True,
        "priority": 4,
        "description": "FLM warmup: no-op unless FLM_WARMUP_RESIDENT=1 (llama3.2:1b, :52625). Default: on demand via run-infer.sh.",
        "builtin": "",
        "command": "bash '/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/System/scripts/plumbing/flm-warmup.sh'",
        "timeout_sec": 240,
        "cwd": "/home/rootrecord",
        "env": {},
    },
    {
        "id": "council_relay",
        "enabled": True,
        "priority": 5,
        "description": "Start council-relay.py if not already running (single getUpdates).",
        "builtin": "",
        "command": f'bash "{PACIFIC}/Communications/telegram/scripts/ensure-relay.sh"',
        "timeout_sec": 30,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Communications/telegram",
        "env": {},
    },
    {
        "id": "security_camera_server",
        "enabled": True,
        "priority": 6,
        "description": "Ensure Security camera server (127.0.0.1:8791) is running.",
        "builtin": "",
        "command": f'bash "{PACIFIC}/Security/Cameras/ensure_cam_server.sh"',
        "timeout_sec": 30,
        "cwd": f"{PACIFIC}/Security/Cameras",
        "env": {},
    },
    {
        "id": "security_timelapse_catchup",
        "enabled": True,
        "priority": 7,
        "description": "Compile any completed hour missing a chunk today + stitch master MP4 if past 19:00 HST (covers late boot/downtime).",
        "builtin": "",
        "command": f'bash "{PACIFIC}/Security/Cameras/timelapse_catchup.sh"',
        "timeout_sec": 600,
        "cwd": f"{PACIFIC}/Security/Cameras",
        "env": {},
    },
    {
        "id": "weather_poller",
        "enabled": True,
        "priority": 8,
        "description": "Ensure the Pacific Weather/ scheduler daemon is running (Pacific venv; data under canonical Database WEATHER/). Enabled 2026-09-29.",
        "builtin": "",
        "command": f'bash "{PACIFIC}/Weather/scripts/ensure-weather-poller.sh"',
        "timeout_sec": 30,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Weather",
        "env": {},
    },
    {
        "id": "network_globe_hawaii",
        "enabled": True,
        "priority": 9,
        "description": "Ensure the live Hawaii Network Globe SSH collector is running.",
        "builtin": "",
        "command": f'bash "{PACIFIC}/Communications/network/scripts/ensure-network-globe-hawaii.sh"',
        "timeout_sec": 30,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Communications/network",
        "env": {},
    },
]

ONCE_AT_START = [
    {
        "id": "ecoflow_read_boot",
        "enabled": True,
        "description": "One BLE read of Delta 2 + River 2 Pro after boot.",
        "builtin": "",
        "command": ECOFLOW_DUAL_READ,
        "timeout_sec": 180,
        "cwd": f"{PACIFIC}/Energy",
        "env": {"ENERGY_EFLIB_PATH": f"{PACIFIC}/Energy/lib/vendor"},
    },
]

EVERY_SECONDS = [
    {
        "id": "heartbeat",
        "enabled": True,
        "description": "ENERGY snapshot once per minute.",
        "interval_sec": 60,
        "builtin": "heartbeat",
        "command": "",
        "timeout_sec": 5,
        "cwd": "",
        "env": {},
    },
    {
        "id": "ecoflow_read_cycle",
        "enabled": True,
        "description": "Leap-frog: Delta2 / River2Pro alternate.",
        "interval_sec": 15,
        "builtin": "",
        "command": f'bash "{PACIFIC}/Energy/scripts/read/leapfrog-read.sh"',
        "timeout_sec": 180,
        "cwd": f"{PACIFIC}/Energy",
        "env": {"ENERGY_EFLIB_PATH": f"{PACIFIC}/Energy/lib/vendor"},
    },
    {
        "id": "sys_stats_cycle",
        "enabled": True,
        "description": "Host CPU/load/mem → Database/SYSTEM.",
        "interval_sec": 5,
        "builtin": "",
        "command": f'bash "{PACIFIC}/System/scripts/sys-sample.sh"',
        "timeout_sec": 60,
        "cwd": f"{PACIFIC}/System",
        "env": {},
    },
    {
        "id": "github_sync_all",
        "enabled": True,
        "description": "Sync all repos.conf rows (pull/merge/push) via Pacific Github catalog.",
        "interval_sec": 5,
        "builtin": "",
        "command": f'bash "{PACIFIC}/Github/scripts/sync-all.sh"',
        "timeout_sec": 300,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Github",
        "env": {},
    },
    {
        "id": "worklog_scan",
        "enabled": True,
        "description": "Offline work auto-doc scan into Database/WORKLOG (Pacific Reports — WO-RPT-001).",
        "interval_sec": 90,
        "builtin": "",
        "command": f'bash "{PACIFIC}/Reports/scripts/worklog_once.sh"',
        "timeout_sec": 180,
        "cwd": f"{PACIFIC}/Reports/scripts",
        "env": {},
    },
    {
        "id": "security_camera_frame_grab",
        "enabled": True,
        "description": "Grab ch1-4 stills to /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Images/.",
        "interval_sec": 1,
        "builtin": "",
        "command": f'bash "{PACIFIC}/Security/Cameras/grab_all.sh"',
        "timeout_sec": 120,
        "cwd": f"{PACIFIC}/Security/Cameras",
        "env": {},
    },
    {
        "id": "service_supervisor",
        "enabled": True,
        "description": "Mid-session auto-recovery (08-ideas weather-relay-auto-recovery, approved 2026-09-29): respawn weather / council relay via their ensure scripts if dead; max 3 per 30 min, then BLOCKED. Dry run: supervise-services.sh --dry-run.",
        "interval_sec": 300,
        "builtin": "",
        "command": f'bash "{PACIFIC}/Automations/scripts/supervise-services.sh"',
        "timeout_sec": 60,
        "cwd": f"{PACIFIC}/Automations/scripts",
        "env": {},
    },
    {
        # Geology collector (2026-09-29, migration-geology): G1 earthquake-hourly / rr-kilauea fetch + G0 quakes.py port.
        # OFF unless RR_GEOLOGY=1 is in the poller's environment at poller start. Stdlib, 10 s per HTTP call, no delivery.
        "id": "geology_collect",
        "enabled": os.environ.get("RR_GEOLOGY", "0") == "1",
        "description": "USGS Hawaii (FDSN bbox M1+) + global M2.5+ quakes and HVO Kilauea/Mauna Loa status -> Database Geology/{Earthquakes,Volcanoes}/*-last.json + Daily/*.jsonl.",
        "interval_sec": 300,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/scripts/geology_collect.py" all',
        "timeout_sec": 60,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Geology",
        "env": {},
    },
    {
        # Council quake Telegram notices (WO-MIG-25): read hawaii-last.json only. OFF unless
        # RR_COUNCIL_QUAKE=1 at poller start. Dry-run: no send, no WAV. First live pass seeds.
        "id": "council_quake_telegram",
        "enabled": os.environ.get("RR_COUNCIL_QUAKE", "0") == "1",
        "description": "Carly per-quake notice from Database Geology/Earthquakes/hawaii-last.json. Dry-run unless RR_COUNCIL_QUAKE_SEND=1.",
        "interval_sec": 120,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/CouncilQuake/scripts/quake_posts.py"',
        "timeout_sec": 30,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Communications/CouncilQuake",
        "env": {},
    },
    {
        # Kilauea webcam stills (2026-09-29, migration-geology): G1 kilauea/kilauea-cams port (catalog + USGS still
        # fallback; OBS push not ported). OFF unless RR_KILAUEA_CAMS=1 at poller start. Conditional GET, ~0.85 MB per change.
        "id": "geology_kilauea_cams",
        "enabled": os.environ.get("RR_KILAUEA_CAMS", "0") == "1",
        "description": "USGS HVO V1/V2/V3 Halemaumau stills -> Database Geology/Volcanoes/Cams/*-last.jpg + cams-last.json (YouTube live ids).",
        "interval_sec": 600,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/scripts/kilauea_cams.py"',
        "timeout_sec": 60,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Geology",
        "env": {},
    },
    {
        # Kilauea public draft queue (WO-MIG-24): from kilauea-last.json only. OFF unless
        # RR_KILAUEA_DRAFT=1 at poller start. No HTTP and no send.
        "id": "geology_kilauea_public_draft",
        "enabled": os.environ.get("RR_KILAUEA_DRAFT", "0") == "1",
        "description": "Queue a Kilauea public draft from Geology/Volcanoes/kilauea-last.json when the HVO notice id or alert level changes. No send.",
        "interval_sec": 3600,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/PublicDraftQueue/scripts/queue_draft.py"',
        "timeout_sec": 30,
        "cwd": f"{PACIFIC}/Geology/PublicDraftQueue",
        "env": {},
    },
    {
        # Energy smart devices (2026-09-29, smart-devices): WiZ bulbs (UDP 38899) + Tuya BSD01 plugs, read-only status.
        # OFF unless RR_SMART_DEVICES=1 is in the poller's environment at poller start. LAN only, never switches, no BLE.
        "id": "smart_devices_collect",
        "enabled": os.environ.get("RR_SMART_DEVICES", "0") == "1",
        "description": "WiZ bulb + Tuya plug state -> Database Energy/Smart-Devices/{wiz,plugs,collector}-last.json.",
        "interval_sec": 300,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Energy/Smart-Devices/scripts/smart_devices_collect.py"',
        "timeout_sec": 45,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Energy/Smart-Devices",
        "env": {},
    },
    {
        # Uptime log (2026-09-29, migration-geology pass): G1 uptime-log port. OFF unless RR_UPTIME_LOG=1 at poller start.
        "id": "system_uptime_log",
        "enabled": os.environ.get("RR_UPTIME_LOG", "0") == "1",
        "description": "Desk-up/down events (origin_start, heartbeat_gap, desk_up, boot) -> Database System/uptime/ (KEEP 400).",
        "interval_sec": 60,
        "builtin": "",
        "command": f'python3 "{PACIFIC}/System/scripts/uptime_log.py" tick',
        "timeout_sec": 15,
        "cwd": f"{PACIFIC}/System",
        "env": {},
    },
    {
        # Python drop allowlist (WO-MIG-46). OFF unless RR_PYTHON_DROP=1 at poller start.
        # Empty catalog.json runs nothing. No drop-folder scan.
        "id": "system_python_drop",
        "enabled": os.environ.get("RR_PYTHON_DROP", "0") == "1",
        "description": "Allowlisted PythonDrop scripts only. Gate RR_PYTHON_DROP stays unset. Empty catalog spawns nothing.",
        "interval_sec": 300,
        "builtin": "",
        "command": f'python3 "{PACIFIC}/System/PythonDrop/scripts/python_drop.py" tick',
        "timeout_sec": 70,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/System/PythonDrop",
        "env": {},
    },
    {
        # All-time radar zip (WO-MIG-05). Reads frames the weather poller already saved.
        # OFF unless RR_RADAR_ZIP=1 is in the poller's environment at poller start. No fetch, no delete.
        "id": "weather_radar_zip",
        "enabled": os.environ.get("RR_RADAR_ZIP", "0") == "1",
        "description": "Append HAWAII_loop archive GIFs into Database Weather/RadarZip/radar_archive.zip (all-time; loose folders stay on the 14-day rule).",
        "interval_sec": 600,
        "builtin": "",
        "command": f'python3 "{PACIFIC}/Weather/RadarZip/scripts/radar_zip.py"',
        "timeout_sec": 120,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Weather/RadarZip",
        "env": {},
    },
    {
        # Country location pollers (WO-MIG-13). OFF. One script, allowlist of
        # locations the one Vercel site routes. Empty allowlist does not call Open-Meteo.
        "id": "country_location_pollers",
        "enabled": False,
        "description": "Open-Meteo current conditions for CountryLocations allowlist -> Database Weather/CountryLocations/. Gate RR_COUNTRY_LOCATIONS stays unset.",
        "interval_sec": 900,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Weather/CountryLocations/scripts/poll_locations.py"',
        "timeout_sec": 60,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Weather/CountryLocations",
        "env": {},
    },
    {
        # Discord poller (WO-MIG-21). OFF. No token and no post.
        # Gate RR_DISCORD_POLLER stays unset. Empty channels.json does not call Discord.
        "id": "discord_poller",
        "enabled": False,
        "description": "Discord poller (WO-MIG-21). OFF. No token and no post. Gate RR_DISCORD_POLLER stays unset.",
        "interval_sec": 60,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Discord/scripts/poll.py"',
        "timeout_sec": 30,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Communications/Discord",
        "env": {},
    },
    {
        # Earthquake Discord post (WO-MIG-23). OFF unless RR_EARTHQUAKE_DISCORD=1
        # is in the poller's environment at poller start. Dry-run by default. No send.
        "id": "earthquake_discord_post",
        "enabled": os.environ.get("RR_EARTHQUAKE_DISCORD", "0") == "1",
        "description": "Format Database Geology/Earthquakes last files and hand text to the Discord send pipe. Dry-run unless a separate send sign-off is set.",
        "interval_sec": 3600,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/Earthquake-Discord/scripts/earthquake_discord_post.py"',
        "timeout_sec": 30,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Geology/Earthquake-Discord",
        "env": {},
    },
    {
        # Slack poller (WO-MIG-22). OFF unless RR_SLACK=1 at poller start. No token and no post.
        "id": "communications_slack",
        "enabled": os.environ.get("RR_SLACK", "0") == "1",
        "description": "Slack poller -> Database Communications/Slack/slack-last.json. No HTTP and no post until a token and sign-off exist.",
        "interval_sec": 60,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Slack/scripts/poll.py"',
        "timeout_sec": 20,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Communications/Slack",
        "env": {},
    },
    {
        # Stripe snapshot (2026-09-29, WO-MIG-10). OFF unless RR_STRIPE=1 at poller start.
        # No key writes not_configured and does not call Stripe. No delivery.
        "id": "stripe_poll",
        "enabled": os.environ.get("RR_STRIPE", "0") == "1",
        "description": "Stripe balance snapshot -> Database Website/stripe-snapshot.json. Gated off. No key does not call the API.",
        "interval_sec": 1800,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Website/scripts/stripe_poll.py"',
        "timeout_sec": 60,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Website",
        "env": {},
    },
    {
        # Vercel failed builds (2026-09-29, WO-MIG-10). OFF unless RR_VERCEL_BUILDS=1 at poller start.
        # Missing token writes nothing. Does not prune records and does not deploy.
        "id": "vercel_builds",
        "enabled": os.environ.get("RR_VERCEL_BUILDS", "0") == "1",
        "description": "Redacted Vercel failed-build records -> Database Logs/Website/. Gated off. No token does not call the API.",
        "interval_sec": 300,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Website/scripts/vercel_builds.py"',
        "timeout_sec": 90,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Website",
        "env": {},
    },
    {
        # Council health (2026-09-30, WO-MIG-27). OFF unless RR_COUNCIL_HEALTH=1 at poller start.
        # Report only: no getUpdates, no send, no model load. Alerts need a separate sign-off.
        "id": "council_health",
        "enabled": os.environ.get("RR_COUNCIL_HEALTH", "0") == "1",
        "description": "Council relay process, getMe, and 409 tail -> Database Communications/CouncilHealth/latest.json. Gated off. No send.",
        "interval_sec": 300,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/CouncilHealth/scripts/council_health.py" --no-alert --no-probe',
        "timeout_sec": 45,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Communications/CouncilHealth",
        "env": {},
    },
    {
        # River car DC drive (2026-09-30, WO-MIG-39). OFF unless RR_RIVER_CAR_DRIVE=1 at poller start.
        # Tick skips until state auto is true and an enabled copy job exists. Copy is a stub.
        # Does not switch the port. A live switch still needs RR_RIVER_CAR_EXECUTE=1.
        "id": "energy_river_car_drive",
        "enabled": os.environ.get("RR_RIVER_CAR_DRIVE", "0") == "1",
        "description": "River 2 Pro car DC drive tick. Gated off. Skips until auto and a copy job. Does not switch power.",
        "interval_sec": 1800,
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Energy/River-Car/scripts/drive_automation.py" --tick',
        "timeout_sec": 30,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Energy/River-Car",
        "env": {},
    },
]

EVERY_MINUTE = [
    {
        # G3 voice (2026-09-29, g3-voice-ailog): first ported G1 voice report. OFF unless RR_VOICE_SYSTEM_PERF=1
        # is in the poller's environment at poller start. Text _current.md + stitched WAV; NO delivery.
        "id": "voice_system_perf",
        "enabled": os.environ.get("RR_VOICE_SYSTEM_PERF", "0") == "1",
        "description": "Bruce system_perf voice report at :06 (CPU/RAM/disk/battery template) → Database System/Reports + Media/Audio/Voice. No delivery.",
        "only_at_minutes": [6],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/system_perf.py"',
        "timeout_sec": 300,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    # G3 voice reports batch 2 (2026-09-29, g3-voice-reports2): ported G1 voice reports, one flag each, all OFF unless
    # the flag =1 is in the poller's environment at poller start. voice_reports.py -> Database Media/Audio/Voice/Reports/
    # <report>_current.md + stitched <report>_current.wav (Archive rotation). NO delivery. Skips WAV if single-flight busy.
    {
        "id": "voice_hourly_chime",
        "enabled": os.environ.get("RR_VOICE_HOURLY_CHIME", "0") == "1",
        "description": "Ava hourly chime at :00/:30 (fully cached clips, no model load). No delivery.",
        "only_at_minutes": [0, 30],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" hourly_chime',
        "timeout_sec": 120,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        "id": "voice_nws_weather",
        "enabled": os.environ.get("RR_VOICE_NWS", "0") == "1",
        "description": "Ava NWS Hawaii report from Database Weather/ (HI alerts API sample + HFO SFP). No delivery.",
        "only_at_minutes": [7, 22, 37, 52],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" nws_weather',
        "timeout_sec": 300,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        "id": "voice_energy_report",
        "enabled": os.environ.get("RR_VOICE_ENERGY", "0") == "1",
        "description": "Carly energy report from Database Energy/ EcoFlow BLE last readings (no vision caption). No delivery.",
        "only_at_minutes": [15, 45],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" energy_report',
        "timeout_sec": 300,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        "id": "voice_remaining_tasks",
        "enabled": os.environ.get("RR_VOICE_REMAINING", "0") == "1",
        "description": "Bruce remaining tasks from Library Work-Orders unchecked boxes. No delivery.",
        "only_at_minutes": [32],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" remaining_tasks',
        "timeout_sec": 300,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        # Earthquake voice report (2026-09-29, migration-geology): G1 earthquake-hourly spoken script, Carly. OFF unless
        # RR_VOICE_QUAKE=1 at poller start. Reads Database Geology/Earthquakes/*-last.json (needs geology_collect). No delivery.
        "id": "voice_earthquake_report",
        "enabled": os.environ.get("RR_VOICE_QUAKE", "0") == "1",
        "description": "Carly USGS earthquake report at :08 (Hawaii first, then global) from Database Geology/. No delivery.",
        "only_at_minutes": [8],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" earthquake_report',
        "timeout_sec": 300,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        # Kilauea voice report (2026-09-29, old-repo migration): G1 hourly Kilauea desk line + HVO notice excerpt, Carly.
        # G1 ran it with the :02 hourly desks; :03 here so it never shares the single-flight lock with the :02 roll-ups.
        # OFF unless RR_VOICE_KILAUEA=1 at poller start. Reads Database Geology/Volcanoes (needs geology_collect). No delivery.
        "id": "voice_kilauea_report",
        "enabled": os.environ.get("RR_VOICE_KILAUEA", "0") == "1",
        "description": "Carly Kilauea report at :03 (HVO alert level, erupting state, latest notice excerpt). No delivery.",
        "only_at_minutes": [3],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" kilauea_report',
        "timeout_sec": 300,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        "id": "ensure_tunnel_online",
        "enabled": True,
        "description": "Start Cloudflare if internet is up and tunnel is down.",
        "only_at_minutes": [],
        "builtin": "ensure_tunnel_online",
        "command": "",
        "timeout_sec": 90,
        "cwd": "",
        "env": {},
    },
]

EVERY_HOUR = [
    {
        # Sun times (2026-09-29, migration-geology pass): G1 hourly-solar-weather sun_times.py port. OFF unless
        # RR_SUN_TIMES=1 at poller start. Fetches Open-Meteo once per HST day (refresh-if-stale), else no network.
        "id": "energy_sun_times",
        "enabled": os.environ.get("RR_SUN_TIMES", "0") == "1",
        "description": "Sunrise/sunset HST (Volcano/Puna) -> Database Energy/sun/sun-times-last.json.",
        "only_at_hours": [],
        "builtin": "",
        "command": f'python3 "{PACIFIC}/Energy/scripts/sun_times.py"',
        "timeout_sec": 30,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Energy",
        "env": {},
    },
    {
        # US all-states weather (2026-09-29, WO-MIG-11). OFF unless RR_US_STATES=1 at poller start.
        # Does not replace the Hawaiʻi weather poller. NWS runs only when NWS_USER_AGENT is set. No delivery.
        "id": "weather_us_states",
        "enabled": os.environ.get("RR_US_STATES", "0") == "1",
        "description": "US state weather (Open-Meteo; NWS if NWS_USER_AGENT) -> Database Weather/US-States/us-last.json.",
        "only_at_hours": [],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Weather/US-States/scripts/fetch_us_states.py"',
        "timeout_sec": 900,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Weather/US-States",
        "env": {},
    },
    {
        # AI processing report (2026-09-29, g3-voice-ailog). OFF unless RR_AI_REPORT=1 in the poller's environment
        # at poller start. Rotates Logs/AI/Inference/inference_current.jsonl daily, then rewrites the _current report.
        "id": "ai_processing_report_hourly",
        "enabled": os.environ.get("RR_AI_REPORT", "0") == "1",
        "description": "Rotate inference JSONL (daily Archive/) + write Database Logs/AI/Reports/ai-processing-report_current.md.",
        "only_at_hours": [],
        "builtin": "",
        "command": f'bash "{PACIFIC}/System/scripts/plumbing/ai-log-rotate.sh" && nice -n 10 python3 "{PACIFIC}/Reports/ai_processing_report.py"',
        "timeout_sec": 120,
        "cwd": f"{PACIFIC}/Reports",
        "env": {},
    },
    {
        # Grok spend summary (2026-09-30, WO-MIG-37). OFF unless RR_AI_USAGE=1 at poller start.
        # Local ledger only. Does not call xAI. Does not enable ai_processing_report_hourly.
        "id": "ai_usage_report",
        "enabled": os.environ.get("RR_AI_USAGE", "0") == "1",
        "description": "Write Database Reports/AI-Usage/last-summary.json from the local token ledger. No network.",
        "only_at_hours": [],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/AI-Usage/scripts/ai_usage_report.py"',
        "timeout_sec": 60,
        "cwd": f"{PACIFIC}/Reports/AI-Usage/scripts",
        "env": {},
    },
    {
        "id": "automations_log_hourly_archive",
        "enabled": True,
        "description": "Cut and archive automations_current.log hourly into Database/Logs/Automations/Archive.",
        "only_at_hours": [],
        "builtin": "",
        "command": f'bash "{PACIFIC}/Automations/scripts/archive_automations_log_hourly.sh"',
        "timeout_sec": 120,
        "cwd": f"{PACIFIC}/Automations/scripts",
        "env": {},
    },
    {
        "id": "security_timelapse_hourly_compile",
        "enabled": True,
        "description": "Compile previous hour ch1 frames into hour_HH.mp4. Window 05:00-19:00 HST (hours 05-18).",
        "only_at_hours": [],
        "builtin": "",
        "command": f'bash "{PACIFIC}/Security/Cameras/timelapse_hourly.sh"',
        "timeout_sec": 600,
        "cwd": f"{PACIFIC}/Security/Cameras",
        "env": {},
    },
]

ON_AT = [
    {
        "id": "security_timelapse_daily_render",
        "enabled": True,
        "description": "Stitch hour_HH.mp4 chunks (05-18) into master_stitched_timelapse.mp4 (MP4 only, no GIF).",
        "at_times": ["19:01"],
        "builtin": "",
        "command": f'bash "{PACIFIC}/Security/Cameras/timelapse_daily.sh"',
        "timeout_sec": 900,
        "cwd": f"{PACIFIC}/Security/Cameras",
        "env": {},
    },
    {
        "id": "reports_daily_roll_up",
        "enabled": True,
        "description": "WO-RPT-001 Phase C: WORKLOG counts → Library Session auto.md (measured only).",
        "at_times": ["18:30"],
        "builtin": "",
        "command": f'bash "{PACIFIC}/Reports/scripts/daily_roll_up.sh"',
        "timeout_sec": 120,
        "cwd": f"{PACIFIC}/Reports/scripts",
        "env": {},
    },
    {
        "id": "reports_weekly_archive",
        "enabled": True,
        "description": "WO-RPT-001 Phase D / WO-ARCH: move old human ops logs to archive/YYYY-Www (Sun 19:00).",
        "at_times": ["19:00"],
        "builtin": "",
        "command": f'bash "{PACIFIC}/Reports/scripts/weekly_archive_logs.sh"',
        "timeout_sec": 180,
        "cwd": f"{PACIFIC}/Reports/scripts",
        "env": {},
    },
    {
        "id": "weather_retention",
        "enabled": False,  # GATED: off until Alexander reviews the dry run (Logs/Weather/Retention/). Apply = swap --dry-run for --apply.
        "description": "Weather retention (README §Retention, signed off 2026-09-29): move data past its window to Archive/Previous-Datasets/Weather-<YYYYMM>/ (never delete). Dry run by default.",
        "at_times": ["00:30"],
        "builtin": "",
        "command": f'python3 "{PACIFIC}/Weather/scripts/weather-retention.py" --dry-run',
        "timeout_sec": 600,
        "cwd": f"{PACIFIC}/Weather",
        "env": {},
    },
    {
        "id": "log_retention",
        "enabled": False,  # GATED: off. Command stays --dry-run. Live --apply needs RR_LOG_RETENTION_APPLY=1 (WO-MIG-41).
        "description": "Log retention (WO-MIG-41): move Database logs past 7 days to Archive/Previous-Datasets/Logs-<YYYYMM>/ (never delete). Dry run by default.",
        "at_times": ["04:20"],
        "builtin": "",
        "command": f'python3 "{PACIFIC}/System/LogRetention/scripts/log_retention.py" --dry-run',
        "timeout_sec": 600,
        "cwd": f"{PACIFIC}/System/LogRetention",
        "env": {},
    },
    {
        # Template reports (2026-09-29, g3-template-reports). OFF unless RR_TEMPLATE_REPORTS=1 in the poller's environment
        # at poller start. Fills the 4 Library ops templates from measured data -> Database Reports/Generated/*_current.md
        # (Archive rotation, structure validator; never writes the Library). Free text via rr-exec, skipped if RAM < 3 GB / lock busy.
        "id": "template_reports_daily",
        "enabled": os.environ.get("RR_TEMPLATE_REPORTS", "0") == "1",
        "description": "Library templates (worklog, checkpoint, event log, work order) filled from measured data -> Database Reports/Generated/.",
        "at_times": ["18:40"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/template_fill.py" --all --draft auto',
        "timeout_sec": 900,
        "cwd": f"{PACIFIC}/Reports",
        "env": {},
    },
    {
        # G3 voice roll-ups (2026-09-29, g3-voice-reports2). OFF unless RR_VOICE_ROLLUPS=1 at poller start; LLM summary line only if RR_VOICE_ROLLUP_LLM=1 too (run-infer.sh). No delivery.
        "id": "voice_morning_report",
        "enabled": os.environ.get("RR_VOICE_ROLLUPS", "0") == "1",
        "description": "Ava morning roll-up (energy, NWS, host, tasks; template-first). No delivery.",
        "at_times": ["09:02"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" morning_report',
        "timeout_sec": 600,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        "id": "voice_midday_report",
        "enabled": os.environ.get("RR_VOICE_ROLLUPS", "0") == "1",
        "description": "Ava midday roll-up (template-first). No delivery.",
        "at_times": ["12:02"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" midday_report',
        "timeout_sec": 600,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        "id": "voice_late_report",
        "enabled": os.environ.get("RR_VOICE_ROLLUPS", "0") == "1",
        "description": "Ava late roll-up (template-first). No delivery.",
        "at_times": ["21:02"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" late_report',
        "timeout_sec": 600,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        # 23:30 late-final (WO-MIG-02). Second fire of the optional late slot. OFF unless
        # RR_VOICE_LATE_FINAL=1 at poller start. Text only. Skips when that slot is already done.
        # No delivery. Night-sleep skip is System/NightSleep when that Folder exists.
        "id": "voice_late_final_report",
        "enabled": os.environ.get("RR_VOICE_LATE_FINAL", "0") == "1",
        "description": "23:30 second chance for the optional late roll-up if that board slot is not done. Text only. No delivery.",
        "at_times": ["23:30"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/Late-Final/scripts/late_final.py"',
        "timeout_sec": 600,
        "cwd": f"{PACIFIC}/Reports/Late-Final/scripts",
        "env": {},
    },
    {
        # Hurricane desk voice report (2026-09-29, old-repo migration): G1 weather/hurricane-desk Hawaii block, Carly, at the
        # G1 times. OFF unless RR_VOICE_HURRICANE=1 at poller start. Reads Database Weather/Hawai'i/hurricanes/tracking
        # (weather poller) + NWS HI alerts. No delivery, no OBS. Radio is media_hurricane_radio, gated off.
        "id": "voice_hurricane_desk",
        "enabled": os.environ.get("RR_VOICE_HURRICANE", "0") == "1",
        "description": "Carly hurricane desk (nearest tracked storm to a Hawaiian island + NWS tropical alerts). No delivery.",
        "at_times": ["05:50", "09:50", "12:50", "16:55", "20:50"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" hurricane_desk',
        "timeout_sec": 300,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",
        "env": {},
    },
    {
        # Hurricane radio (2026-09-30, WO-MIG-19). OFF unless RR_HURRICANE_RADIO=1 at poller start.
        # Hands hurricane_desk to Report playback --dry-run. Does not call aplay.
        "id": "media_hurricane_radio",
        "enabled": os.environ.get("RR_HURRICANE_RADIO", "0") == "1",
        "description": "Request hurricane desk WAV through Report playback. No speaker.",
        "at_times": ["06:35", "13:12", "17:02"],
        "builtin": "",
        "command": f'python3 "{PACIFIC}/Media/HurricaneRadio/scripts/radio.py" run',
        "timeout_sec": 60,
        "cwd": f"{PACIFIC}/Media/HurricaneRadio",
        "env": {},
    },
    {
        # Bruce desk sample (WO-MIG-26). OFF unless RR_BRUCE_STATS=1 at poller start.
        # Dry-run: no Telegram. Send only when RR_BRUCE_STATS_SEND=1 as well.
        "id": "bruce_stats_posts",
        "enabled": os.environ.get("RR_BRUCE_STATS", "0") == "1",
        "description": "Bruce measured host and EcoFlow desk sample. Dry-run unless RR_BRUCE_STATS_SEND=1.",
        "at_times": ["07:18", "15:18", "21:18"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/BruceStats/scripts/bruce_stats.py"',
        "timeout_sec": 60,
        "needs_internet": os.environ.get("RR_BRUCE_STATS_SEND", "0") == "1",
        "cwd": f"{PACIFIC}/Communications/BruceStats",
        "env": {},
    },
    {
        # AdSense end-of-day (2026-09-30, WO-MIG-38). OFF unless RR_ADSENSE=1 at poller start.
        # No key writes not_configured and does not call Google. No Discord.
        "id": "adsense_eod",
        "enabled": os.environ.get("RR_ADSENSE", "0") == "1",
        "description": "AdSense 7-day snapshot -> Database Advertising/adsense-last.json. Gated off. No key does not call the API.",
        "at_times": ["21:00"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Advertising/scripts/adsense_eod.py"',
        "timeout_sec": 60,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Advertising",
        "env": {},
    },
    {
        # AdMob end-of-day (2026-09-30, WO-MIG-38). OFF unless RR_ADMOB=1 at poller start.
        # No key writes not_configured and does not call Google. Refresh token does not fall back.
        "id": "admob_eod",
        "enabled": os.environ.get("RR_ADMOB", "0") == "1",
        "description": "AdMob 7-day snapshot -> Database Advertising/admob-last.json. Gated off. No key does not call the API.",
        "at_times": ["21:05"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Advertising/scripts/admob_eod.py"',
        "timeout_sec": 90,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Advertising",
        "env": {},
    },
]

ECOFLOW_ACTIONS = f"{PACIFIC}/Energy/scripts/actions"
ECOFLOW_LOCK = "/tmp/ecoflow-ble.lock"


def ecoflow_command(script: str) -> str:
    return f"flock -w 60 {ECOFLOW_LOCK} bash {ECOFLOW_ACTIONS}/{script}"


TOGGLES = []
READS = [
    {"id": "delta2_read", "script": f"{PACIFIC}/Energy/scripts/read/delta2-read.sh"},
    {"id": "river2pro_read", "script": f"{PACIFIC}/Energy/scripts/read/river2pro-read.sh"},
]
