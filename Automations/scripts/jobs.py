# ==============================================================================
# # INFO — MUST HAVE (future agents / operators)
# ------------------------------------------------------------------------------
# Ctrl-C in the poller window / `rootserver-poller stop` MUST kill the whole stack
# (poller + cloudflared + systemd unit). Never "window only".
# Data intake → /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Intake/
# Baks/logs  → /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Github/
# GitHub catalog: Github/scripts/repos.conf (same ids as G2; Ecosystem local_path).
# Pacific .gitignore excludes us-mainland-one/ (own repo). No rclone / aws-sync.
# Council relay (ensure-relay.sh): FLM llama3.2:3b on the NPU, RR_NPU_ONLY=1, no Ollama fallback, context 4096, on demand.
# Other callers and flm-warmup.sh still default to llama3.2:1b on demand. That 1b default is not the council model.
# Telegram council-relay: one getUpdates (Ava). Original council replies on (COUNCIL_REPLIES=1). Sandbox replies off (SANDBOX_REPLIES=0). Private DMs stay quiet (RR_RELAY_REPLIES default 0). Delivery dest is the original council (RR_TELEGRAM_DEST=council).
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

# ====================================================
# SECTION: DEFAULTS
# What it does: Fields every job inherits when the job itself does not set them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
DEFAULTS = {  # info: set DEFAULTS
    "enabled": False,  # info: "enabled" : False ,
    "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
    "cwd": "",  # info: "cwd" : "" ,
    "env": {},  # info: "env" : { } ,
}  # info: }

PACIFIC = "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"  # info: set PACIFIC

# Paths with spaces: always double-quote inside bash command strings.
# ====================================================
# SECTION: ECOFLOW_DUAL_READ
# What it does: Set ECOFLOW_DUAL_READ.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ECOFLOW_DUAL_READ = (  # info: set ECOFLOW_DUAL_READ
    "flock -w 90 /tmp/ecoflow-ble.lock bash -c "  # info: "flock -w 90 /tmp/ecoflow-ble.lock bash -c "
    f"'ok=0; "  # info: f" 'ok=0; "
    f"bash \"{PACIFIC}/Energy/scripts/read/delta2-read.sh\" && ok=1 || true; "  # info: f" bash \" { PACIFIC } /Energy/scripts/read/delta2-read.sh\" && ok=1 || true; "
    f"bash \"{PACIFIC}/Energy/scripts/read/river2pro-read.sh\" && ok=1 || true; "  # info: f" bash \" { PACIFIC } /Energy/scripts/read/river2pro-read.sh\" && ok=1 || true; "
    "exit $((1-ok))'"  # info: "exit $((1-ok))'"
)  # info: )

# ====================================================
# SECTION: ON_BOOT
# What it does: Runs once when the poller process starts, lowest priority number first. Paste a new job above the TEMPLATE at the bottom of this list.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ON_BOOT = [  # info: set ON_BOOT
    {  # info: {
        "id": "self_terminal",  # info: "id" : "self_terminal" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 0,  # info: "priority" : 0 ,
        "description": "This desk process + status terminal (self registry).",  # info: "description" : "This desk process + status terminal (self registry)." ,
        "builtin": "self_process",  # info: "builtin" : "self_process" ,
        "command": "",  # info: "command" : "" ,
        "process": f"{PACIFIC}/Automations/scripts/rootserver_poller.py",  # info: "process" : f" { PACIFIC } /Automations/scripts/rootserver_poller.py "
        "terminal": "RootRecord poller — rootserver",  # info: "terminal" : "RootRecord poller — rootserver" ,
        "watch": f"{PACIFIC}/Automations/scripts/poller/poller-watch.py",  # info: "watch" : f" { PACIFIC } /Automations/scripts/poller/poller-watch.py "
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": "",  # info: "cwd" : "" ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "cloudflare_tunnel",  # info: "id" : "cloudflare_tunnel" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 1,  # info: "priority" : 1 ,
        "description": "Start Cloudflare tunnel when internet is up (deferred if offline).",  # info: "description" : "Start Cloudflare tunnel when internet is up (deferred if offline)." ,
        "builtin": "tunnel_start",  # info: "builtin" : "tunnel_start" ,
        "command": "",  # info: "command" : "" ,
        "public_host": "rootserver.rootrecord.cloud",  # info: "public_host" : "rootserver.rootrecord.cloud" ,
        "token_file": "/home/rootrecord/.cloudflared/rootserver.token",  # info: "token_file" : "/home/rootrecord/.cloudflared/rootserver.token" ,
        "cloudflared_bin": f"{PACIFIC}/Communications/network/cloudflare/bin/cloudflared",  # info: "cloudflared_bin" : f" { PACIFIC } /Communications/network/cloudflare/bin/cloudflared "
        "local_service": "http://127.0.0.1:8799",  # info: "local_service" : "http://127.0.0.1:8799" ,
        "timeout_sec": 45,  # info: "timeout_sec" : 45 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": "",  # info: "cwd" : "" ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "github_setup_remotes",  # info: "id" : "github_setup_remotes" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 2,  # info: "priority" : 2 ,
        "description": "Ensure remotes for all repos.conf rows (Pacific Github catalog).",  # info: "description" : "Ensure remotes for all repos.conf rows (Pacific Github catalog)." ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Github/scripts/setup-all-remotes.sh"',  # info: "command" : f' bash " { PACIFIC } /Github/scripts/setup-all-remotes.sh"
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Github",  # info: "cwd" : f" { PACIFIC } /Github "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "ollama_warmup",  # info: "id" : "ollama_warmup" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 3,  # info: "priority" : 3 ,
        "description": "Ensure ollama serve is up (CPU fallback lanes).",  # info: "description" : "Ensure ollama serve is up (CPU fallback lanes)." ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": "bash '/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/System/scripts/plumbing/ollama-warmup.sh'",  # info: "command" : "bash '/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Syste
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": "/home/rootrecord",  # info: "cwd" : "/home/rootrecord" ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "flm_npu_warmup",  # info: "id" : "flm_npu_warmup" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 4,  # info: "priority" : 4 ,
        "description": "FLM warmup: no-op unless FLM_WARMUP_RESIDENT=1. Non-council default llama3.2:1b. Council relay uses llama3.2:3b via ensure-relay.sh.",  # info: "description" : "FLM warmup: no-op unless FLM_WARMUP_RESIDENT=1. Non-council default llama3.2:1b. Council relay uses llama3.2:3b via ensure-relay.sh." , 
        "builtin": "",  # info: "builtin" : "" ,
        "command": "bash '/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/System/scripts/plumbing/flm-warmup.sh'",  # info: "command" : "bash '/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Syste
        "timeout_sec": 240,  # info: "timeout_sec" : 240 ,
        "cwd": "/home/rootrecord",  # info: "cwd" : "/home/rootrecord" ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "council_relay",  # info: "id" : "council_relay" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 5,  # info: "priority" : 5 ,
        "description": "Start council-relay.py if not already running (single getUpdates).",  # info: "description" : "Start council-relay.py if not already running (single getUpdates)." ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Communications/telegram/scripts/ensure-relay.sh"',  # info: "command" : f' bash " { PACIFIC } /Communications/telegram/scripts/ensure-relay.sh"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/telegram",  # info: "cwd" : f" { PACIFIC } /Communications/telegram "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "security_camera_server",  # info: "id" : "security_camera_server" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 6,  # info: "priority" : 6 ,
        "description": "Ensure Security camera server (127.0.0.1:8791) is running.",  # info: "description" : "Ensure Security camera server (127.0.0.1:8791) is running." ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Security/Cameras/ensure_cam_server.sh"',  # info: "command" : f' bash " { PACIFIC } /Security/Cameras/ensure_cam_server.sh"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "cwd": f"{PACIFIC}/Security/Cameras",  # info: "cwd" : f" { PACIFIC } /Security/Cameras "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "security_timelapse_catchup",  # info: "id" : "security_timelapse_catchup" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 7,  # info: "priority" : 7 ,
        "description": "Compile any completed hour missing a chunk today + stitch master MP4 if past 19:00 HST (covers late boot/downtime).",  # info: "description" : "Compile any completed hour missing a chunk today + stitch master MP4 if past 19:00 HST (cover
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Security/Cameras/timelapse_catchup.sh"',  # info: "command" : f' bash " { PACIFIC } /Security/Cameras/timelapse_catchup.sh"
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Security/Cameras",  # info: "cwd" : f" { PACIFIC } /Security/Cameras "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "weather_poller",  # info: "id" : "weather_poller" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 8,  # info: "priority" : 8 ,
        "description": "Ensure the Pacific Weather/ scheduler daemon is running (Pacific venv; data under canonical Database WEATHER/). Enabled 2026-09-29.",  # info: "description" : "Ensure the Pacific Weather/ scheduler daemon is running (Pacific venv; data under canonical D
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Weather/scripts/ensure-weather-poller.sh"',  # info: "command" : f' bash " { PACIFIC } /Weather/scripts/ensure-weather-poller.sh"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Weather",  # info: "cwd" : f" { PACIFIC } /Weather "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "network_globe_hawaii",  # info: "id" : "network_globe_hawaii" ,
        "enabled": True,  # info: "enabled" : True ,
        "priority": 9,  # info: "priority" : 9 ,
        "description": "Ensure the live Hawaii Network Globe SSH collector is running.",  # info: "description" : "Ensure the live Hawaii Network Globe SSH collector is running." ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Communications/network/scripts/ensure-network-globe-hawaii.sh"',  # info: "command" : f' bash " { PACIFIC } /Communications/network/scripts/ensure-network-globe-hawaii.sh"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Communications/network",  # info: "cwd" : f" { PACIFIC } /Communications/network "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- TEMPLATE (ON_BOOT) — copy from the next line through the closing brace, paste ABOVE this template, remove the leading # ---
    # {
    #     "id": "example_on_boot",
    #     "enabled": False,
    #     "priority": 50,
    #     "description": "One sentence: what this job does and whether it sends, spends, or moves hardware.",
    #     "builtin": "",
    #     "command": f'nice -n 10 python3 "{PACIFIC}/path/to/script.py"',
    #     "timeout_sec": 120,
    #     "needs_internet": False,
    #     "cwd": f"{PACIFIC}",
    #     "env": {},
    # },
    # --- end TEMPLATE (ON_BOOT) ---
    # Leave enabled False until Alexander names this job. A flag of the form RR_SOMETHING=1 belongs in enabled, not hardcoded True.
]  # info: ]

# ====================================================
# SECTION: ONCE_AT_START
# What it does: Runs once after ON_BOOT, before the repeating schedules. Paste a new job above the TEMPLATE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ONCE_AT_START = [  # info: set ONCE_AT_START
    {  # info: {
        "id": "ecoflow_read_boot",  # info: "id" : "ecoflow_read_boot" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "One BLE read of Delta 2 + River 2 Pro after boot.",  # info: "description" : "One BLE read of Delta 2 + River 2 Pro after boot." ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": ECOFLOW_DUAL_READ,  # info: "command" : ECOFLOW_DUAL_READ ,
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "cwd": f"{PACIFIC}/Energy",  # info: "cwd" : f" { PACIFIC } /Energy "
        "env": {"ENERGY_EFLIB_PATH": f"{PACIFIC}/Energy/lib/vendor"},  # info: "env" : { "ENERGY_EFLIB_PATH" : f" { PACIFIC
    },  # info: } ,
    # --- TEMPLATE (ONCE_AT_START) — copy from the next line through the closing brace, paste ABOVE this template, remove the leading # ---
    # {
    #     "id": "example_once_at_start",
    #     "enabled": False,
    #     "description": "One sentence: what this job does and whether it sends, spends, or moves hardware.",
    #     "builtin": "",
    #     "command": f'nice -n 10 python3 "{PACIFIC}/path/to/script.py"',
    #     "timeout_sec": 120,
    #     "needs_internet": False,
    #     "cwd": f"{PACIFIC}",
    #     "env": {},
    # },
    # --- end TEMPLATE (ONCE_AT_START) ---
    # Leave enabled False until Alexander names this job. A flag of the form RR_SOMETHING=1 belongs in enabled, not hardcoded True.
]  # info: ]

# ====================================================
# SECTION: EVERY_SECONDS
# What it does: Repeating jobs. interval_sec is how often the poller may start them. Paste a new job above the TEMPLATE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
EVERY_SECONDS = [  # info: set EVERY_SECONDS
    {  # info: {
        "id": "heartbeat",  # info: "id" : "heartbeat" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "ENERGY snapshot once per minute.",  # info: "description" : "ENERGY snapshot once per minute." ,
        "interval_sec": 60,  # info: "interval_sec" : 60 ,
        "builtin": "heartbeat",  # info: "builtin" : "heartbeat" ,
        "command": "",  # info: "command" : "" ,
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": "",  # info: "cwd" : "" ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "ecoflow_read_cycle",  # info: "id" : "ecoflow_read_cycle" ,
        "enabled": False,  # info: "enabled" : False ,
        "description": "Off. rr-ecoflow-read.timer reads the older pack so voice and GitHub jobs cannot freeze solar.",  # info: "description" : "Off. rr-ecoflow-read.timer reads the older pack so voice and GitHub jobs cannot freeze solar." ,
        "interval_sec": 15,  # info: "interval_sec" : 15 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Energy/scripts/read/leapfrog-read.sh"',  # info: "command" : f' bash " { PACIFIC } /Energy/scripts/read/leapfrog-read.sh"
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "cwd": f"{PACIFIC}/Energy",  # info: "cwd" : f" { PACIFIC } /Energy "
        "env": {"ENERGY_EFLIB_PATH": f"{PACIFIC}/Energy/lib/vendor"},  # info: "env" : { "ENERGY_EFLIB_PATH" : f" { PACIFIC
    },  # info: } ,
    {  # info: {
        "id": "sys_stats_cycle",  # info: "id" : "sys_stats_cycle" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Host CPU/load/mem → Database/SYSTEM.",  # info: "description" : "Host CPU/load/mem → Database/SYSTEM." ,
        "interval_sec": 5,  # info: "interval_sec" : 5 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/System/scripts/sys-sample.sh"',  # info: "command" : f' bash " { PACIFIC } /System/scripts/sys-sample.sh"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/System",  # info: "cwd" : f" { PACIFIC } /System "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "github_sync_all",  # info: "id" : "github_sync_all" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Sync all repos.conf rows (pull/merge/push) via Pacific Github catalog.",  # info: "description" : "Sync all repos.conf rows (pull/merge/push) via Pacific Github catalog." ,
        "interval_sec": 5,  # info: "interval_sec" : 5 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Github/scripts/sync-all.sh"',  # info: "command" : f' bash " { PACIFIC } /Github/scripts/sync-all.sh"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Github",  # info: "cwd" : f" { PACIFIC } /Github "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "worklog_scan",  # info: "id" : "worklog_scan" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Offline work auto-doc scan into Database/WORKLOG (Pacific Reports — WO-RPT-001).",  # info: "description" : "Offline work auto-doc scan into Database/WORKLOG (Pacific Reports — WO-RPT-001)." ,
        "interval_sec": 90,  # info: "interval_sec" : 90 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Reports/scripts/worklog_once.sh"',  # info: "command" : f' bash " { PACIFIC } /Reports/scripts/worklog_once.sh"
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "cwd": f"{PACIFIC}/Reports/scripts",  # info: "cwd" : f" { PACIFIC } /Reports/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "security_camera_frame_grab",  # info: "id" : "security_camera_frame_grab" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Grab ch1-4 stills to /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Images/.",  # info: "description" : "Grab ch1-4 stills to /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Imag
        "interval_sec": 1,  # info: "interval_sec" : 1 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Security/Cameras/grab_all.sh"',  # info: "command" : f' bash " { PACIFIC } /Security/Cameras/grab_all.sh"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Security/Cameras",  # info: "cwd" : f" { PACIFIC } /Security/Cameras "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "service_supervisor",  # info: "id" : "service_supervisor" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Mid-session auto-recovery (08-Ideas weather-relay-auto-recovery, approved 2026-09-29): respawn weather / council relay via their ensure scripts if dead; max 3 per 30 min, then BLOCKED. Dry run: supervise-services.sh --dry-run.",  # info: "description" : "Mid-session auto-recovery (08-Ideas weather-relay-auto-recovery, approved 2026-09-29): respaw
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Automations/scripts/supervise-services.sh"',  # info: "command" : f' bash " { PACIFIC } /Automations/scripts/supervise-services.sh"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Automations/scripts",  # info: "cwd" : f" { PACIFIC } /Automations/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Geology collector (2026-09-29, migration-geology): G1 earthquake-hourly / rr-kilauea fetch + G0 quakes.py port.
        # OFF unless RR_GEOLOGY=1 is in the poller's environment at poller start. Stdlib, 10 s per HTTP call, no delivery.
        "id": "geology_collect",  # info: "id" : "geology_collect" ,
        "enabled": os.environ.get("RR_GEOLOGY", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "USGS Hawaii (FDSN bbox M1+) + global M2.5+ quakes and HVO Kilauea/Mauna Loa status -> Database Geology/{Earthquakes,Volcanoes}/*-last.json + Daily/*.jsonl.",  # info: "description" : "USGS Hawaii (FDSN bbox M1+) + global M2.5+ quakes and HVO Kilauea/Mauna Loa status -> Databas
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/scripts/geology_collect.py" all',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Geology/scripts/geology_collect.py" all
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Geology",  # info: "cwd" : f" { PACIFIC } /Geology "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Council quake Telegram notices (WO-MIG-25): read hawaii-last.json only. OFF unless
        # RR_COUNCIL_QUAKE=1 at poller start. Dry-run: no send, no WAV. First live pass seeds.
        "id": "council_quake_telegram",  # info: "id" : "council_quake_telegram" ,
        "enabled": os.environ.get("RR_COUNCIL_QUAKE", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Carly per-quake notice from Database Geology/Earthquakes/hawaii-last.json. Dry-run unless RR_COUNCIL_QUAKE_SEND=1.",  # info: "description" : "Carly per-quake notice from Database Geology/Earthquakes/hawaii-last.json. Dry-run unless RR_
        "interval_sec": 120,  # info: "interval_sec" : 120 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/CouncilQuake/scripts/quake_posts.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/CouncilQuake/scripts/quake_posts.py"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Communications/CouncilQuake",  # info: "cwd" : f" { PACIFIC } /Communications/CouncilQuake "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Kilauea webcam stills (2026-09-29, migration-geology): G1 kilauea/kilauea-cams port (catalog + USGS still
        # fallback; OBS push not ported). OFF unless RR_KILAUEA_CAMS=1 at poller start. Conditional GET, ~0.85 MB per change.
        "id": "geology_kilauea_cams",  # info: "id" : "geology_kilauea_cams" ,
        "enabled": os.environ.get("RR_KILAUEA_CAMS", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "USGS HVO V1/V2/V3 Halemaumau stills -> Database Geology/Volcanoes/Cams/*-last.jpg + cams-last.json (YouTube live ids).",  # info: "description" : "USGS HVO V1/V2/V3 Halemaumau stills -> Database Geology/Volcanoes/Cams/*-last.jpg + cams-last
        "interval_sec": 600,  # info: "interval_sec" : 600 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/scripts/kilauea_cams.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Geology/scripts/kilauea_cams.py"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Geology",  # info: "cwd" : f" { PACIFIC } /Geology "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Kilauea public draft queue (WO-MIG-24): from kilauea-last.json only. OFF unless
        # RR_KILAUEA_DRAFT=1 at poller start. No HTTP and no send.
        "id": "geology_kilauea_public_draft",  # info: "id" : "geology_kilauea_public_draft" ,
        "enabled": os.environ.get("RR_KILAUEA_DRAFT", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Queue a Kilauea public draft from Geology/Volcanoes/kilauea-last.json when the HVO notice id or alert level changes. No send.",  # info: "description" : "Queue a Kilauea public draft from Geology/Volcanoes/kilauea-last.json when the HVO notice id 
        "interval_sec": 3600,  # info: "interval_sec" : 3600 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/PublicDraftQueue/scripts/queue_draft.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Geology/PublicDraftQueue/scripts/queue_draft.py"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "cwd": f"{PACIFIC}/Geology/PublicDraftQueue",  # info: "cwd" : f" { PACIFIC } /Geology/PublicDraftQueue "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Energy smart devices (2026-09-29, smart-devices): WiZ bulbs (UDP 38899) + Tuya BSD01 plugs, read-only status.
        # OFF unless RR_SMART_DEVICES=1 is in the poller's environment at poller start. LAN only, never switches, no BLE.
        "id": "smart_devices_collect",  # info: "id" : "smart_devices_collect" ,
        "enabled": os.environ.get("RR_SMART_DEVICES", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "WiZ bulb + Tuya plug state -> Database Energy/Smart-Devices/{wiz,plugs,collector}-last.json.",  # info: "description" : "WiZ bulb + Tuya plug state -> Database Energy/Smart-Devices/{wiz,plugs,collector}-last.json."
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Energy/Smart-Devices/scripts/smart_devices_collect.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Energy/Smart-Devices/scripts/smart_devices_collect.py"
        "timeout_sec": 45,  # info: "timeout_sec" : 45 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Energy/Smart-Devices",  # info: "cwd" : f" { PACIFIC } /Energy/Smart-Devices "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Uptime log (2026-09-29, migration-geology pass): G1 uptime-log port. OFF unless RR_UPTIME_LOG=1 at poller start.
        "id": "system_uptime_log",  # info: "id" : "system_uptime_log" ,
        "enabled": os.environ.get("RR_UPTIME_LOG", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Desk heartbeat plus offline and morning-return samples -> Database System/uptime/. Averages start from the first sample after recording begins.",  # info: "description" : "Desk heartbeat plus offline and morning-return samples -> Database System/uptime/. Averages start from the first sample after recording begins." ,
        "interval_sec": 60,  # info: "interval_sec" : 60 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/System/scripts/uptime_log.py" tick',  # info: "command" : f' python3 " { PACIFIC } /System/scripts/uptime_log.py" tick
        "timeout_sec": 15,  # info: "timeout_sec" : 15 ,
        "cwd": f"{PACIFIC}/System",  # info: "cwd" : f" { PACIFIC } /System "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Python drop allowlist (WO-MIG-46). OFF unless RR_PYTHON_DROP=1 at poller start.
        # Empty catalog.json runs nothing. No drop-folder scan.
        "id": "system_python_drop",  # info: "id" : "system_python_drop" ,
        "enabled": os.environ.get("RR_PYTHON_DROP", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Allowlisted PythonDrop scripts only. Gate RR_PYTHON_DROP stays unset. Empty catalog spawns nothing.",  # info: "description" : "Allowlisted PythonDrop scripts only. Gate RR_PYTHON_DROP stays unset. Empty catalog spawns no
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/System/PythonDrop/scripts/python_drop.py" tick',  # info: "command" : f' python3 " { PACIFIC } /System/PythonDrop/scripts/python_drop.py" tick
        "timeout_sec": 70,  # info: "timeout_sec" : 70 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/System/PythonDrop",  # info: "cwd" : f" { PACIFIC } /System/PythonDrop "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # All-time radar zip (WO-MIG-05). Reads frames the weather poller already saved.
        # OFF unless RR_RADAR_ZIP=1 is in the poller's environment at poller start. No fetch, no delete.
        "id": "weather_radar_zip",  # info: "id" : "weather_radar_zip" ,
        "enabled": os.environ.get("RR_RADAR_ZIP", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Append HAWAII_loop archive GIFs into Database Weather/RadarZip/radar_archive.zip (all-time; loose folders stay on the 14-day rule).",  # info: "description" : "Append HAWAII_loop archive GIFs into Database Weather/RadarZip/radar_archive.zip (all-time; l
        "interval_sec": 600,  # info: "interval_sec" : 600 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/Weather/RadarZip/scripts/radar_zip.py"',  # info: "command" : f' python3 " { PACIFIC } /Weather/RadarZip/scripts/radar_zip.py"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Weather/RadarZip",  # info: "cwd" : f" { PACIFIC } /Weather/RadarZip "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Country location pollers (WO-MIG-13). OFF. One script, allowlist of
        # locations the one Vercel site routes. Empty allowlist does not call Open-Meteo.
        "id": "country_location_pollers",  # info: "id" : "country_location_pollers" ,
        "enabled": False,  # info: "enabled" : False ,
        "description": "Open-Meteo current conditions for CountryLocations allowlist -> Database Weather/CountryLocations/. Gate RR_COUNTRY_LOCATIONS stays unset.",  # info: "description" : "Open-Meteo current conditions for CountryLocations allowlist -> Database Weather/CountryLocat
        "interval_sec": 900,  # info: "interval_sec" : 900 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Weather/CountryLocations/scripts/poll_locations.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Weather/CountryLocations/scripts/poll_locations.py"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Weather/CountryLocations",  # info: "cwd" : f" { PACIFIC } /Weather/CountryLocations "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Discord poller (WO-MIG-21). OFF. No token and no post.
        # Gate RR_DISCORD_POLLER stays unset. Empty channels.json does not call Discord.
        # RR_DISCORD_REVIEW_PIPELINE stays unset. Timeout fits four sequential inferences when that gate is later turned on.
        "id": "discord_poller",  # info: "id" : "discord_poller" ,
        "enabled": False,  # info: "enabled" : False ,
        "description": "Discord poller (WO-MIG-21). OFF. No token and no post. Gates RR_DISCORD_POLLER, RR_DISCORD_REVIEW_PIPELINE, and RR_GLOBAL_UPDATER stay unset.",  # info: "description" : "Discord poller (WO-MIG-21). OFF. No token and no post. Gates stay unset." ,
        "interval_sec": 60,  # info: "interval_sec" : 60 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Discord/scripts/poll.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/Discord/scripts/poll.py"
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/Discord",  # info: "cwd" : f" { PACIFIC } /Communications/Discord "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Earthquake Discord post (WO-MIG-23). OFF unless RR_EARTHQUAKE_DISCORD=1
        # is in the poller's environment at poller start. Dry-run by default. No send.
        "id": "earthquake_discord_post",  # info: "id" : "earthquake_discord_post" ,
        "enabled": os.environ.get("RR_EARTHQUAKE_DISCORD", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Format Database Geology/Earthquakes last files and hand text to the Discord send pipe. Dry-run unless a separate send sign-off is set.",  # info: "description" : "Format Database Geology/Earthquakes last files and hand text to the Discord send pipe. Dry-ru
        "interval_sec": 3600,  # info: "interval_sec" : 3600 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/Earthquake-Discord/scripts/earthquake_discord_post.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Geology/Earthquake-Discord/scripts/earthquake_discord_post.py
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Geology/Earthquake-Discord",  # info: "cwd" : f" { PACIFIC } /Geology/Earthquake-Discord "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Slack poller (WO-MIG-22). OFF unless RR_SLACK=1 at poller start. No token and no post.
        "id": "communications_slack",  # info: "id" : "communications_slack" ,
        "enabled": os.environ.get("RR_SLACK", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Slack poller -> Database Communications/Slack/slack-last.json. No HTTP and no post until a token and sign-off exist.",  # info: "description" : "Slack poller -> Database Communications/Slack/slack-last.json. No HTTP and no post until a to
        "interval_sec": 60,  # info: "interval_sec" : 60 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Slack/scripts/poll.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/Slack/scripts/poll.py"
        "timeout_sec": 20,  # info: "timeout_sec" : 20 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Communications/Slack",  # info: "cwd" : f" { PACIFIC } /Communications/Slack "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Stripe snapshot (2026-09-29, WO-MIG-10). OFF unless RR_STRIPE=1 at poller start.
        # No key writes not_configured and does not call Stripe. No delivery.
        "id": "stripe_poll",  # info: "id" : "stripe_poll" ,
        "enabled": os.environ.get("RR_STRIPE", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Stripe balance snapshot -> Database Website/stripe-snapshot.json. Gated off. No key does not call the API.",  # info: "description" : "Stripe balance snapshot -> Database Website/stripe-snapshot.json. Gated off. No key does not 
        "interval_sec": 1800,  # info: "interval_sec" : 1800 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Website/scripts/stripe_poll.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Website/scripts/stripe_poll.py"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Website",  # info: "cwd" : f" { PACIFIC } /Website "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Vercel failed builds (2026-09-29, WO-MIG-10). OFF unless RR_VERCEL_BUILDS=1 at poller start.
        # Missing token writes nothing. Does not prune records and does not deploy.
        "id": "vercel_builds",  # info: "id" : "vercel_builds" ,
        "enabled": os.environ.get("RR_VERCEL_BUILDS", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Redacted Vercel failed-build records -> Database Logs/Website/. Gated off. No token does not call the API.",  # info: "description" : "Redacted Vercel failed-build records -> Database Logs/Website/. Gated off. No token does not 
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Website/scripts/vercel_builds.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Website/scripts/vercel_builds.py"
        "timeout_sec": 90,  # info: "timeout_sec" : 90 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Website",  # info: "cwd" : f" { PACIFIC } /Website "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Backup copy of the public snapshot. rr-status-snapshot.timer owns the 30 s cadence
        # so a long poller job cannot leave AWS on an old EcoFlow reading.
        "id": "status_snapshot",  # info: "id" : "status_snapshot" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Backup write of the public status snapshot. The user timer publishes it every 30 s.",  # info: "description" : "Backup write of the public status snapshot. The user timer publishes it every 30 s." ,
        "interval_sec": 60,  # info: "interval_sec" : 60 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Website/scripts/live_data_pages.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Website/scripts/live_data_pages.py"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Website",  # info: "cwd" : f" { PACIFIC } /Website "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Council health (2026-09-30, WO-MIG-27). OFF unless RR_COUNCIL_HEALTH=1 at poller start.
        # Report only: no getUpdates, no send, no model load. Alerts need a separate sign-off.
        "id": "council_health",  # info: "id" : "council_health" ,
        "enabled": os.environ.get("RR_COUNCIL_HEALTH", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Council relay process, getMe, and 409 tail -> Database Communications/CouncilHealth/latest.json. Gated off. No send.",  # info: "description" : "Council relay process, getMe, and 409 tail -> Database Communications/CouncilHealth/latest.js
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/CouncilHealth/scripts/council_health.py" --no-alert --no-probe',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/CouncilHealth/scripts/council_health.py" --no-
        "timeout_sec": 45,  # info: "timeout_sec" : 45 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/CouncilHealth",  # info: "cwd" : f" { PACIFIC } /Communications/CouncilHealth "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # River car DC drive (2026-09-30, WO-MIG-39). OFF unless RR_RIVER_CAR_DRIVE=1 at poller start.
        # Tick skips until state auto is true and an enabled copy job exists. Copy is a stub.
        # Does not switch the port. A live switch still needs RR_RIVER_CAR_EXECUTE=1.
        "id": "energy_river_car_drive",  # info: "id" : "energy_river_car_drive" ,
        "enabled": os.environ.get("RR_RIVER_CAR_DRIVE", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "River 2 Pro car DC drive tick. Gated off. Skips until auto and a copy job. Does not switch power.",  # info: "description" : "River 2 Pro car DC drive tick. Gated off. Skips until auto and a copy job. Does not switch po
        "interval_sec": 1800,  # info: "interval_sec" : 1800 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Energy/River-Car/scripts/drive_automation.py" --tick',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Energy/River-Car/scripts/drive_automation.py" --tick
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Energy/River-Car",  # info: "cwd" : f" { PACIFIC } /Energy/River-Car "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Inbox drain (WO-MIG-31). OFF unless RR_INBOX_DRAIN=1 at poller start.
        # Copies the quiet-mode hold locally. No Cloudflare. No send.
        "id": "inbox_drain",  # info: "id" : "inbox_drain" ,
        "enabled": os.environ.get("RR_INBOX_DRAIN", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Copy quiet-mode Relay-Inbox rows into Database Communications/Inbox/feedback.jsonl. Gated off. No D1. No send.",  # info: "description" : "Copy quiet-mode Relay-Inbox rows into Database Communications/Inbox/feedback.jsonl. Gated off
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Inbox/scripts/inbox.py" drain',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/Inbox/scripts/inbox.py" drain
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Communications/Inbox",  # info: "cwd" : f" { PACIFIC } /Communications/Inbox "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Bandwidth desk needs a byte sample. OFF unless RR_NET_SAMPLES=1 at poller start. Does not send.
        "id": "system_net_sample",  # info: "id" : "system_net_sample" ,
        "enabled": os.environ.get("RR_NET_SAMPLES", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Byte-counter sample of the default-route iface -> Database System/network/. No send.",  # info: "description" : "Byte-counter sample of the default-route iface -> Database System/network/. No send." ,
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/System/scripts/host_desks.py" net-sample',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /System/scripts/host_desks.py" net-sample
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/System/scripts",  # info: "cwd" : f" { PACIFIC } /System/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Public radio and origin checks. OFF unless RR_PUBLIC_HEALTH=1. Writes a file. Does not start port 8787.
        # Ava posts the down list only when RR_PUBLIC_HEALTH_SEND=1. That flag stays off here.
        "id": "public_health",  # info: "id" : "public_health" ,
        "enabled": os.environ.get("RR_PUBLIC_HEALTH", "0") == "1",  # info: "enabled" : os . environ . get ( "RR_PUBLIC_HEALTH" , "0" ) == "1" ,
        "description": "Check origin radio and 127.0.0.1:8787. Writes a status file. Does not start the origin. Send stays off unless RR_PUBLIC_HEALTH_SEND=1.",  # info: "description" : "Check origin radio and 127.0.0.1:8787. Writes a status file. Does not start the origin. Send stays off unless RR_PUBLIC_HEALTH_SEND=1." ,
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/PublicHealth/scripts/public_health.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/PublicHealth/scripts/public_health.py" ' ,
        "timeout_sec": 40,  # info: "timeout_sec" : 40 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/PublicHealth",  # info: "cwd" : f" { PACIFIC } /Communications/PublicHealth " ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Count queued Kilauea drafts. OFF unless RR_KILAUEA_DRAFT_ANNOUNCE=1. Does not publish. Send stays off unless RR_KILAUEA_DRAFT_SEND=1.
        "id": "kilauea_draft_count",  # info: "id" : "kilauea_draft_count" ,
        "enabled": os.environ.get("RR_KILAUEA_DRAFT_ANNOUNCE", "0") == "1",  # info: "enabled" : os . environ . get ( "RR_KILAUEA_DRAFT_ANNOUNCE" , "0" ) == "1" ,
        "description": "Count queued Kilauea public drafts and write the sentence. Does not publish. Send stays off unless RR_KILAUEA_DRAFT_SEND=1.",  # info: "description" : "Count queued Kilauea public drafts and write the sentence. Does not publish. Send stays off unless RR_KILAUEA_DRAFT_SEND=1." ,
        "interval_sec": 3600,  # info: "interval_sec" : 3600 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Geology/PublicDraftQueue/scripts/announce_count.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Geology/PublicDraftQueue/scripts/announce_count.py" ' ,
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Geology/PublicDraftQueue",  # info: "cwd" : f" { PACIFIC } /Geology/PublicDraftQueue " ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # One notes.jsonl line becomes a work-order draft. OFF unless RR_NOTE_DRAFT=1. Does not build.
        "id": "note_work_draft",  # info: "id" : "note_work_draft" ,
        "enabled": os.environ.get("RR_NOTE_DRAFT", "0") == "1",  # info: "enabled" : os . environ . get ( "RR_NOTE_DRAFT" , "0" ) == "1" ,
        "description": "Turn one voice-report note into a Library work-order draft. Gated off. Does not call development.execute_work_order.",  # info: "description" : "Turn one voice-report note into a Library work-order draft. Gated off. Does not call development.execute_work_order." ,
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/note_draft.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/note_draft.py" ' ,
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts " ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Automated report relay (2026-09-30). Alexander asked to start posting.
        # RR_DISCORD_POST is set only in this job's env. The chat poller stays off.
        "id": "discord_report_relay",  # info: "id" : "discord_report_relay" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Post each changed automated report to its Reports channel. Chat poller stays off.",  # info: "description" : "Post each changed automated report to its Reports channel. Chat poller stays off." ,
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Discord/scripts/report_relay.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/Discord/scripts/report_relay.py" ' ,
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/Discord",  # info: "cwd" : f" { PACIFIC } /Communications/Discord " ,
        "env": {"RR_DISCORD_POST": "1"},  # info: "env" : { "RR_DISCORD_POST" : "1" } ,
    },  # info: } ,
    {  # info: {
        # External RSS for RootRecord Radio. On when RR_RADIO_RSS=1. The poller script defaults that on.
        # Polls the feed registry into the story queue. Does not speak, push audio, or change the broadcaster.
        "id": "radio_rss_poll",  # info: "id" : "radio_rss_poll" ,
        "enabled": os.environ.get("RR_RADIO_RSS", "0") == "1",  # info: "enabled" : os . environ . get ( "RR_RADIO_RSS" , "0" ) == "1" ,
        "description": "Poll external RSS into the Radio story queue. Does not speak or push audio.",  # info: "description" : "Poll external RSS into the Radio story queue. Does not speak or push audio." ,
        "interval_sec": 300,  # info: "interval_sec" : 300 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/RadioRss/scripts/rss_radio.py" poll',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/RadioRss/scripts/rss_radio.py" poll ' ,
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Media/RadioRss",  # info: "cwd" : f" { PACIFIC } /Media/RadioRss " ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Mainland site analytics mirror (2026-10-02). OFF unless RR_ANALYTICS_PULL=1 at poller start.
        # Prefer Logs/Website/analytics/pull-from-api.sh; writes daily/YYYY-MM-DD.json. No send.
        "id": "analytics_pull",  # info: "id" : "analytics_pull" ,
        "enabled": os.environ.get("RR_ANALYTICS_PULL", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Mirror ML2 /api/analytics/daily -> Database Logs/Website/analytics/daily/. Gated off. No page JS. No send.",  # info: description
        "interval_sec": 900,  # info: "interval_sec" : 900 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Website/scripts/analytics_pull.py"',  # info: command
        "timeout_sec": 40,  # info: "timeout_sec" : 40 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Website",  # info: cwd
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- TEMPLATE (EVERY_SECONDS) — copy from the next line through the closing brace, paste ABOVE this template, remove the leading # ---
    # {
    #     "id": "example_every_seconds",
    #     "enabled": False,
    #     "interval_sec": 300,
    #     "description": "One sentence: what this job does and whether it sends, spends, or moves hardware.",
    #     "builtin": "",
    #     "command": f'nice -n 10 python3 "{PACIFIC}/path/to/script.py"',
    #     "timeout_sec": 120,
    #     "needs_internet": False,
    #     "cwd": f"{PACIFIC}",
    #     "env": {},
    # },
    # --- end TEMPLATE (EVERY_SECONDS) ---
    # Leave enabled False until Alexander names this job. A flag of the form RR_SOMETHING=1 belongs in enabled, not hardcoded True.
]  # info: ]

# ====================================================
# SECTION: EVERY_MINUTE
# What it does: Jobs that run on chosen minutes of each hour (only_at_minutes). An empty list means every minute. Paste a new job above the TEMPLATE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
EVERY_MINUTE = [  # info: set EVERY_MINUTE
    {  # info: {
        # G3 voice (2026-09-29, g3-voice-ailog): first ported G1 voice report. OFF unless RR_VOICE_SYSTEM_PERF=1
        # is in the poller's environment at poller start. Text _current.md + stitched WAV; NO delivery.
        "id": "voice_system_perf",  # info: "id" : "voice_system_perf" ,
        "enabled": os.environ.get("RR_VOICE_SYSTEM_PERF", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Bruce system report at :22 and :52, before the radio playlist snapshot. Host temperature is degrees Celsius. Voice note when RR_VOICE_DELIVER=1.",  # info: "description" : "Bruce system report at :22 and :52, before the radio playlist snapshot. Host temperature is degrees Celsius. Voice note when RR_VOICE_DELIVER=1." ,
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/system_perf.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/system_perf.py"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # G3 voice reports batch 2 (2026-09-29, g3-voice-reports2): ported G1 voice reports, one flag each, all OFF unless
    # the flag =1 is in the poller's environment at poller start. voice_reports.py -> Database Media/Audio/Voice/Reports/
    # <report>_current.md + stitched <report>_current.wav (Archive rotation). NO delivery. Skips WAV if single-flight busy.
    {  # info: {
        "id": "voice_hourly_chime",  # info: "id" : "voice_hourly_chime" ,
        "enabled": os.environ.get("RR_VOICE_HOURLY_CHIME", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Prebuilt chime at :00 and :30 (Ava, Bruce, Carly leapfrog by the hour). Plays Media/Audio/Voice/Chimes. No live render.",  # info: "description" : "Prebuilt chime at :00 and :30 (Ava, Bruce, Carly leapfrog by the hour). Plays Media/Audio/Voice/Chimes. No live render." ,
        "only_at_minutes": [0, 30],  # info: "only_at_minutes" : [ 0 , 30 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" hourly_chime',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" hourly_chime
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "voice_nws_weather",  # info: "id" : "voice_nws_weather" ,
        "enabled": os.environ.get("RR_VOICE_NWS", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Ava NWS Hawaii report from Database Weather/, at :22 and :52 so the file is on the station before the chime. Voice note when RR_VOICE_DELIVER=1.",  # info: "description" : "Ava NWS Hawaii report from Database Weather/, at :22 and :52 so the file is on the station before the chime. Voice note when RR_VOICE_DELIVER=1." ,
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" nws_weather',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" nws_weather
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "voice_remaining_tasks",  # info: "id" : "voice_remaining_tasks" ,
        "enabled": os.environ.get("RR_VOICE_REMAINING", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Bruce remaining tasks from the report board, at :22 and :52 before the radio snapshot. Voice note when RR_VOICE_DELIVER=1.",  # info: "description" : "Bruce remaining tasks from the report board, at :22 and :52 before the radio snapshot. Voice note when RR_VOICE_DELIVER=1." ,
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" remaining_tasks',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" remaining_tasks
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Earthquake voice report (2026-09-29, migration-geology): G1 earthquake-hourly spoken script, Carly. OFF unless
        # RR_VOICE_QUAKE=1 at poller start. Reads Database Geology/Earthquakes/*-last.json (needs geology_collect). No delivery.
        "id": "voice_earthquake_report",  # info: "id" : "voice_earthquake_report" ,
        "enabled": os.environ.get("RR_VOICE_QUAKE", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Carly USGS earthquake report at :22 and :52 from Database Geology/, before the radio snapshot. Voice note when RR_VOICE_DELIVER=1.",  # info: "description" : "Carly USGS earthquake report at :22 and :52 from Database Geology/, before the radio snapshot. Voice note when RR_VOICE_DELIVER=1." ,
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" earthquake_report',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" earthquake_report
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Kilauea voice report (2026-09-29, old-repo migration): G1 hourly Kilauea desk line + HVO notice excerpt, Carly.
        # :22 and :52 with the other full desks, before the station snapshots the playlist.
        # OFF unless RR_VOICE_KILAUEA=1 at poller start. Reads Database Geology/Volcanoes (needs geology_collect). No delivery.
        "id": "voice_kilauea_report",  # info: "id" : "voice_kilauea_report" ,
        "enabled": os.environ.get("RR_VOICE_KILAUEA", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Carly Kilauea report at :22 and :52 from the HVO notice, before the radio snapshot. Voice note when RR_VOICE_DELIVER=1.",  # info: "description" : "Carly Kilauea report at :22 and :52 from the HVO notice, before the radio snapshot. Voice note when RR_VOICE_DELIVER=1." ,
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" kilauea_report',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" kilauea_report
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "ensure_tunnel_online",  # info: "id" : "ensure_tunnel_online" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Start Cloudflare if internet is up and tunnel is down.",  # info: "description" : "Start Cloudflare if internet is up and tunnel is down." ,
        "only_at_minutes": [],  # info: "only_at_minutes" : [ ] ,
        "builtin": "ensure_tunnel_online",  # info: "builtin" : "ensure_tunnel_online" ,
        "command": "",  # info: "command" : "" ,
        "timeout_sec": 90,  # info: "timeout_sec" : 90 ,
        "cwd": "",  # info: "cwd" : "" ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Combined energy+solar voice (2026-10-02). OFF unless RR_VOICE_SOLAR=1 at poller start.
        # Voice note posts only when RR_VOICE_DELIVER=1. Default chat is the sandbox.
        "id": "voice_solar_desk",  # info: "id" : "voice_solar_desk" ,
        "enabled": os.environ.get("RR_VOICE_SOLAR", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Bruce combined energy+solar desk at :22 and :52: packs, sun times, newest channel-1 still, and this hour's camera look (refreshes when needed). Voice note when RR_VOICE_DELIVER=1.",  # info: solar desk description
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" solar_desk',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" solar_desk
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "voice_security_desk",  # info: "id" : "voice_security_desk" ,
        "enabled": os.environ.get("RR_VOICE_SECURITY", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Carly security desk at :22 and :52 (firewall boot, ssh, listeners, failed sign-ins), before the radio snapshot. Voice note when RR_VOICE_DELIVER=1.",  # info: "description" : "Carly security desk at :22 and :52 (firewall boot, ssh, listeners, failed sign-ins), before the radio snapshot. Voice note when RR_VOICE_DELIVER=1." ,
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" security_desk',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" security_desk
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "voice_bandwidth_desk",  # info: "id" : "voice_bandwidth_desk" ,
        "enabled": os.environ.get("RR_VOICE_BANDWIDTH", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Carly bandwidth desk at :22 and :52 from host byte samples plus Mainland Home/Radio analytics, before the radio snapshot. Voice note when RR_VOICE_DELIVER=1. Needs system_net_sample; analytics_pull optional.",  # info: bandwidth desk description
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" bandwidth_desk',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" bandwidth_desk
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "voice_current_report",  # info: "id" : "voice_current_report" ,
        "enabled": os.environ.get("RR_VOICE_CURRENT", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Full current report at :22 and :52, after the other desks and before the radio snapshot. Heading is the slot time. Voice note when RR_VOICE_DELIVER=1.",  # info: "description" : "Full current report at :22 and :52, after the other desks and before the radio snapshot. Heading is the slot time. Voice note when RR_VOICE_DELIVER=1." ,
        "only_at_minutes": [22, 52],  # info: "only_at_minutes" : [ 22 , 52 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" current_report',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" current_report
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Hourly RSS news update. Speaks about five minutes, rotates Ava, Bruce, and Carly, replaces news_update_current.
        "id": "radio_news_update",  # info: "id" : "radio_news_update" ,
        "enabled": os.environ.get("RR_RADIO_NEWS", "0") == "1",  # info: "enabled" : os . environ . get ( "RR_RADIO_NEWS" , "0" ) == "1" ,
        "description": "Hourly news update at :36, before the :52 voice stack and the top-of-hour radio snapshot. Rotates Ava, Bruce, and Carly. Replaces news_update_current and uploads it to the reports playlist.",  # info: "description" : "Hourly news update at :36, before the :52 voice stack and the top-of-hour radio snapshot. Rotates Ava, Bruce, and Carly. Replaces news_update_current and uploads it to the reports playlist." ,
        "only_at_minutes": [36],  # info: "only_at_minutes" : [ 36 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/RadioRss/scripts/rss_radio.py" news-hour --speak',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/RadioRss/scripts/rss_radio.py" news-hour --speak ' ,
        "timeout_sec": 1200,  # info: "timeout_sec" : 1200 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Media/RadioRss",  # info: "cwd" : f" { PACIFIC } /Media/RadioRss " ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "voice_timing_report",  # info: "id" : "voice_timing_report" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Rewrite Library voice-timing.md from the automations log. Measured durations only. No model.",  # info: "description" : "Rewrite Library voice-timing.md from the automations log. Measured durations only. No model." ,
        "only_at_minutes": [5],  # info: "only_at_minutes" : [ 5 ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/Voice-Timing/scripts/voice_timing_report.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Reports/Voice-Timing/scripts/voice_timing_report.py"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Reports/Voice-Timing/scripts",  # info: "cwd" : f" { PACIFIC } /Reports/Voice-Timing/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- TEMPLATE (EVERY_MINUTE) — copy from the next line through the closing brace, paste ABOVE this template, remove the leading # ---
    # {
    #     "id": "example_every_minute",
    #     "enabled": False,
    #     "only_at_minutes": [],
    #     "description": "One sentence: what this job does and whether it sends, spends, or moves hardware.",
    #     "builtin": "",
    #     "command": f'nice -n 10 python3 "{PACIFIC}/path/to/script.py"',
    #     "timeout_sec": 120,
    #     "needs_internet": False,
    #     "cwd": f"{PACIFIC}",
    #     "env": {},
    # },
    # --- end TEMPLATE (EVERY_MINUTE) ---
    # Leave enabled False until Alexander names this job. A flag of the form RR_SOMETHING=1 belongs in enabled, not hardcoded True.
]  # info: ]

# ====================================================
# SECTION: EVERY_HOUR
# What it does: Jobs that run on chosen hours (only_at_hours). An empty list means every hour. Paste a new job above the TEMPLATE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
EVERY_HOUR = [  # info: set EVERY_HOUR
    {  # info: {
        # Sun times (2026-09-29, migration-geology pass): G1 hourly-solar-weather sun_times.py port. ON unless
        # RR_SUN_TIMES=0 at poller start. Fetches Open-Meteo once per HST day (refresh-if-stale), else no network.
        "id": "energy_sun_times",  # info: "id" : "energy_sun_times" ,
        "enabled": os.environ.get("RR_SUN_TIMES", "1") == "1",  # info: "enabled" : os . environ . get (
        "description": "Sunrise/sunset HST (Volcano/Puna) -> Database Energy/sun/sun-times-last.json.",  # info: "description" : "Sunrise/sunset HST (Volcano/Puna) -> Database Energy/sun/sun-times-last.json." ,
        "only_at_hours": [],  # info: "only_at_hours" : [ ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/Energy/scripts/sun_times.py"',  # info: "command" : f' python3 " { PACIFIC } /Energy/scripts/sun_times.py"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Energy",  # info: "cwd" : f" { PACIFIC } /Energy "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Moon phase (2026-10-01). Same Open-Meteo point as sun times. ON unless RR_MOON=0 at poller start.
        # One fetch when the saved file is older than 50 minutes. A failed fetch keeps the file.
        "id": "energy_moon_phase",  # info: "id" : "energy_moon_phase" ,
        "enabled": os.environ.get("RR_MOON", "1") == "1",  # info: "enabled" : os . environ . get (
        "description": "Moon phase HST (Volcano/Puna) -> Database Energy/moon/moon-last.json. No send.",  # info: "description" : "Moon phase HST (Volcano/Puna) -> Database Energy/moon/moon-last.json. No send." ,
        "only_at_hours": [],  # info: "only_at_hours" : [ ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/Energy/scripts/moon_phase.py"',  # info: "command" : f' python3 " { PACIFIC } /Energy/scripts/moon_phase.py"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Energy",  # info: "cwd" : f" { PACIFIC } /Energy "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # US all-states weather (2026-09-29, WO-MIG-11). OFF unless RR_US_STATES=1 at poller start.
        # Does not replace the Hawaiʻi weather poller. NWS runs only when NWS_USER_AGENT is set. No delivery.
        "id": "weather_us_states",  # info: "id" : "weather_us_states" ,
        "enabled": os.environ.get("RR_US_STATES", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "US state weather (Open-Meteo; NWS if NWS_USER_AGENT) -> Database Weather/US-States/us-last.json.",  # info: "description" : "US state weather (Open-Meteo; NWS if NWS_USER_AGENT) -> Database Weather/US-States/us-last.js
        "only_at_hours": [],  # info: "only_at_hours" : [ ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Weather/US-States/scripts/fetch_us_states.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Weather/US-States/scripts/fetch_us_states.py"
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Weather/US-States",  # info: "cwd" : f" { PACIFIC } /Weather/US-States "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # AI processing report (2026-09-29, g3-voice-ailog). OFF unless RR_AI_REPORT=1 in the poller's environment
        # at poller start. Rotates Logs/AI/Inference/inference_current.jsonl daily, then rewrites the _current report.
        "id": "ai_processing_report_hourly",  # info: "id" : "ai_processing_report_hourly" ,
        "enabled": os.environ.get("RR_AI_REPORT", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Rotate inference JSONL (daily Archive/) + write Database Logs/AI/Reports/ai-processing-report_current.md.",  # info: "description" : "Rotate inference JSONL (daily Archive/) + write Database Logs/AI/Reports/ai-processing-report
        "only_at_hours": [],  # info: "only_at_hours" : [ ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/System/scripts/plumbing/ai-log-rotate.sh" && nice -n 10 python3 "{PACIFIC}/Reports/ai_processing_report.py"',  # info: "command" : f' bash " { PACIFIC } /System/scripts/plumbing/ai-log-rotate.sh" && nice -n 10 python3 "
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd" : f" { PACIFIC } /Reports "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Grok spend summary (2026-09-30, WO-MIG-37). OFF unless RR_AI_USAGE=1 at poller start.
        # Local ledger only. Does not call xAI. Does not enable ai_processing_report_hourly.
        "id": "ai_usage_report",  # info: "id" : "ai_usage_report" ,
        "enabled": os.environ.get("RR_AI_USAGE", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Write Database Reports/AI-Usage/last-summary.json from the local token ledger. No network.",  # info: "description" : "Write Database Reports/AI-Usage/last-summary.json from the local token ledger. No network." ,
        "only_at_hours": [],  # info: "only_at_hours" : [ ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/AI-Usage/scripts/ai_usage_report.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Reports/AI-Usage/scripts/ai_usage_report.py"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Reports/AI-Usage/scripts",  # info: "cwd" : f" { PACIFIC } /Reports/AI-Usage/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "automations_log_hourly_archive",  # info: "id" : "automations_log_hourly_archive" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Cut and archive automations_current.log hourly into Database/Logs/Automations/Archive.",  # info: "description" : "Cut and archive automations_current.log hourly into Database/Logs/Automations/Archive." ,
        "only_at_hours": [],  # info: "only_at_hours" : [ ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Automations/scripts/archive_automations_log_hourly.sh"',  # info: "command" : f' bash " { PACIFIC } /Automations/scripts/archive_automations_log_hourly.sh"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Automations/scripts",  # info: "cwd" : f" { PACIFIC } /Automations/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "security_timelapse_hourly_compile",  # info: "id" : "security_timelapse_hourly_compile" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Compile previous hour ch1 frames into hour_HH.mp4. Window 05:00-19:00 HST (hours 05-18).",  # info: "description" : "Compile previous hour ch1 frames into hour_HH.mp4. Window 05:00-19:00 HST (hours 05-18)." ,
        "only_at_hours": [],  # info: "only_at_hours" : [ ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Security/Cameras/timelapse_hourly.sh"',  # info: "command" : f' bash " { PACIFIC } /Security/Cameras/timelapse_hourly.sh"
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Security/Cameras",  # info: "cwd" : f" { PACIFIC } /Security/Cameras "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- TEMPLATE (EVERY_HOUR) — copy from the next line through the closing brace, paste ABOVE this template, remove the leading # ---
    # {
    #     "id": "example_every_hour",
    #     "enabled": False,
    #     "only_at_hours": [],
    #     "description": "One sentence: what this job does and whether it sends, spends, or moves hardware.",
    #     "builtin": "",
    #     "command": f'nice -n 10 python3 "{PACIFIC}/path/to/script.py"',
    #     "timeout_sec": 120,
    #     "needs_internet": False,
    #     "cwd": f"{PACIFIC}",
    #     "env": {},
    # },
    # --- end TEMPLATE (EVERY_HOUR) ---
    # Leave enabled False until Alexander names this job. A flag of the form RR_SOMETHING=1 belongs in enabled, not hardcoded True.
]  # info: ]

# ====================================================
# SECTION: ON_AT
# What it does: Jobs that run at exact HST clock times in at_times (HH:MM). Paste a new job above the TEMPLATE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ON_AT = [  # info: set ON_AT
    {  # info: {
        "id": "security_timelapse_daily_render",  # info: "id" : "security_timelapse_daily_render" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Stitch hour_HH.mp4 chunks (05-18) into master_stitched_timelapse.mp4 (MP4 only, no GIF).",  # info: "description" : "Stitch hour_HH.mp4 chunks (05-18) into master_stitched_timelapse.mp4 (MP4 only, no GIF)." ,
        "at_times": ["19:01"],  # info: "at_times" : [ "19:01" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Security/Cameras/timelapse_daily.sh"',  # info: "command" : f' bash " { PACIFIC } /Security/Cameras/timelapse_daily.sh"
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "cwd": f"{PACIFIC}/Security/Cameras",  # info: "cwd" : f" { PACIFIC } /Security/Cameras "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "reports_daily_roll_up",  # info: "id" : "reports_daily_roll_up" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "WO-RPT-001 Phase C: WORKLOG counts → Library Session auto.md (measured only).",  # info: "description" : "WO-RPT-001 Phase C: WORKLOG counts → Library Session auto.md (measured only)." ,
        "at_times": ["18:30"],  # info: "at_times" : [ "18:30" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Reports/scripts/daily_roll_up.sh"',  # info: "command" : f' bash " { PACIFIC } /Reports/scripts/daily_roll_up.sh"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Reports/scripts",  # info: "cwd" : f" { PACIFIC } /Reports/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "reports_weekly_archive",  # info: "id" : "reports_weekly_archive" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "WO-RPT-001 Phase D / WO-ARCH: move old human ops logs to archive/YYYY-Www (Sun 19:00).",  # info: "description" : "WO-RPT-001 Phase D / WO-ARCH: move old human ops logs to archive/YYYY-Www (Sun 19:00)." ,
        "at_times": ["19:00"],  # info: "at_times" : [ "19:00" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{PACIFIC}/Reports/scripts/weekly_archive_logs.sh"',  # info: "command" : f' bash " { PACIFIC } /Reports/scripts/weekly_archive_logs.sh"
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "cwd": f"{PACIFIC}/Reports/scripts",  # info: "cwd" : f" { PACIFIC } /Reports/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "weather_retention",  # info: "id" : "weather_retention" ,
        "enabled": False,  # GATED: off until Alexander reviews the dry run (Logs/Weather/Retention/). Apply = swap --dry-run for --apply.
        "description": "Weather retention (README §Retention, signed off 2026-09-29): move data past its window to Archive/Previous-Datasets/Weather-<YYYYMM>/ (never delete). Dry run by default.",  # info: "description" : "Weather retention (README §Retention, signed off 2026-09-29): move data past its window to Ar
        "at_times": ["00:30"],  # info: "at_times" : [ "00:30" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/Weather/scripts/weather-retention.py" --dry-run',  # info: "command" : f' python3 " { PACIFIC } /Weather/scripts/weather-retention.py" --dry-run
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Weather",  # info: "cwd" : f" { PACIFIC } /Weather "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "log_retention",  # info: "id" : "log_retention" ,
        "enabled": False,  # GATED: off. Command stays --dry-run. Live --apply needs RR_LOG_RETENTION_APPLY=1 (WO-MIG-41).
        "description": "Log retention (WO-MIG-41): move Database logs past 7 days to Archive/Previous-Datasets/Logs-<YYYYMM>/ (never delete). Dry run by default.",  # info: "description" : "Log retention (WO-MIG-41): move Database logs past 7 days to Archive/Previous-Datasets/Logs-<
        "at_times": ["04:20"],  # info: "at_times" : [ "04:20" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/System/LogRetention/scripts/log_retention.py" --dry-run',  # info: "command" : f' python3 " { PACIFIC } /System/LogRetention/scripts/log_retention.py" --dry-run
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/System/LogRetention",  # info: "cwd" : f" { PACIFIC } /System/LogRetention "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Scoped path index (WO-MIG-42). OFF. Four source trees only. No file bytes.
        "id": "path_index",  # info: "id" : "path_index" ,
        "enabled": False,  # info: "enabled" : False ,
        "description": "Path index (WO-MIG-42): path and kind for Pacific, Website, Library, and Android. No file contents.",  # info: "description" : "Path index (WO-MIG-42): path and kind for Pacific, Website, Library, and Android. No file con
        "interval_sec": 900,  # info: "interval_sec" : 900 ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/System/PathIndex/scripts/path_index.py"',  # info: "command" : f' python3 " { PACIFIC } /System/PathIndex/scripts/path_index.py"
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/System/PathIndex",  # info: "cwd" : f" { PACIFIC } /System/PathIndex "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Template reports (2026-09-29, g3-template-reports). OFF unless RR_TEMPLATE_REPORTS=1 in the poller's environment
        # at poller start. Fills the 4 Library ops templates from measured data -> Database Reports/Generated/*_current.md
        # (Archive rotation, structure validator; never writes the Library). Free text via rr-exec, skipped if RAM < 3 GB / lock busy.
        "id": "template_reports_daily",  # info: "id" : "template_reports_daily" ,
        "enabled": os.environ.get("RR_TEMPLATE_REPORTS", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Library templates (worklog, checkpoint, event log, work order) filled from measured data -> Database Reports/Generated/.",  # info: "description" : "Library templates (worklog, checkpoint, event log, work order) filled from measured data -> D
        "at_times": ["18:40"],  # info: "at_times" : [ "18:40" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/template_fill.py" --all --draft auto',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Reports/template_fill.py" --all --draft auto
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd" : f" { PACIFIC } /Reports "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # G3 voice roll-ups (2026-09-29, g3-voice-reports2). OFF unless RR_VOICE_ROLLUPS=1 at poller start; LLM summary line only if RR_VOICE_ROLLUP_LLM=1 too (run-infer.sh). No delivery.
        "id": "voice_morning_report",  # info: "id" : "voice_morning_report" ,
        "enabled": os.environ.get("RR_VOICE_ROLLUPS", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Ava morning roll-up at 09:02, inside the morning window and before the 09:30 radio snapshot. No delivery.",  # info: "description" : "Ava morning roll-up at 09:02, inside the morning window and before the 09:30 radio snapshot. No delivery." ,
        "at_times": ["09:02"],  # info: "at_times" : [ "09:02" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" morning_report',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" morning_report
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "voice_midday_report",  # info: "id" : "voice_midday_report" ,
        "enabled": os.environ.get("RR_VOICE_ROLLUPS", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Ava midday roll-up at 12:02, inside the midday window and before the 12:30 radio snapshot. No delivery.",  # info: "description" : "Ava midday roll-up at 12:02, inside the midday window and before the 12:30 radio snapshot. No delivery." ,
        "at_times": ["12:02"],  # info: "at_times" : [ "12:02" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" midday_report',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" midday_report
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        "id": "voice_late_report",  # info: "id" : "voice_late_report" ,
        "enabled": os.environ.get("RR_VOICE_ROLLUPS", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Ava late roll-up at 21:02, inside the late window and before the 21:30 radio snapshot. No delivery.",  # info: "description" : "Ava late roll-up at 21:02, inside the late window and before the 21:30 radio snapshot. No delivery." ,
        "at_times": ["21:02"],  # info: "at_times" : [ "21:02" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" late_report',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" late_report
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # 23:00 late-final (WO-MIG-02). Second fire of the optional late slot. OFF unless
        # RR_VOICE_LATE_FINAL=1 at poller start. Text only. Skips when that slot is already done.
        # No delivery. Night-sleep skip is System/NightSleep when that Folder exists.
        "id": "voice_late_final_report",  # info: "id" : "voice_late_final_report" ,
        "enabled": os.environ.get("RR_VOICE_LATE_FINAL", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "23:02 second chance for the optional late roll-up if that board slot is not done. Off the radio boundary. Text only. No delivery.",  # info: "description" : "23:02 second chance for the optional late roll-up if that board slot is not done. Off the radio boundary. Text only. No delivery." ,
        "at_times": ["23:02"],  # info: "at_times" : [ "23:02" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/Late-Final/scripts/late_final.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Reports/Late-Final/scripts/late_final.py"
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Reports/Late-Final/scripts",  # info: "cwd" : f" { PACIFIC } /Reports/Late-Final/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Hurricane desk voice report (2026-09-29, old-repo migration): G1 weather/hurricane-desk Hawaii block, Carly, at the
        # G1 times. OFF unless RR_VOICE_HURRICANE=1 at poller start. Reads Database Weather/Hawai'i/hurricanes/tracking
        # (weather poller) + NWS HI alerts. No delivery, no OBS. Radio is media_hurricane_radio, gated off.
        "id": "voice_hurricane_desk",  # info: "id" : "voice_hurricane_desk" ,
        "enabled": os.environ.get("RR_VOICE_HURRICANE", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Carly hurricane desk at :40, twenty minutes before the hour snapshot (nearest tracked storm to a Hawaiian island + NWS tropical alerts). No delivery.",  # info: "description" : "Carly hurricane desk at :40, twenty minutes before the hour snapshot (nearest tracked storm to a Hawaiian island + NWS tropical alerts). No d
        "at_times": ["05:40", "09:40", "12:40", "16:40", "20:40"],  # info: "at_times" : [ "05:40" , "09:40" , "12:40" , "16:40" , "20:40" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Media/Voice/scripts/voice_reports.py" hurricane_desk',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Media/Voice/scripts/voice_reports.py" hurricane_desk
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd" : f" { PACIFIC } /Media/Voice/scripts "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Hurricane radio (2026-09-30, WO-MIG-19). OFF unless RR_HURRICANE_RADIO=1 at poller start.
        # Hands hurricane_desk to Report playback --dry-run. Does not call aplay.
        "id": "media_hurricane_radio",  # info: "id" : "media_hurricane_radio" ,
        "enabled": os.environ.get("RR_HURRICANE_RADIO", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Request hurricane desk WAV through Report playback. No speaker.",  # info: "description" : "Request hurricane desk WAV through Report playback. No speaker." ,
        "at_times": ["06:00", "13:00", "17:00"],  # info: "at_times" : [ "06:00" , "13:00" , "17:00" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'python3 "{PACIFIC}/Media/HurricaneRadio/scripts/radio.py" run',  # info: "command" : f' python3 " { PACIFIC } /Media/HurricaneRadio/scripts/radio.py" run
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Media/HurricaneRadio",  # info: "cwd" : f" { PACIFIC } /Media/HurricaneRadio "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Bruce desk sample (WO-MIG-26). OFF unless RR_BRUCE_STATS=1 at poller start.
        # Dry-run: no Telegram. Send only when RR_BRUCE_STATS_SEND=1 as well.
        "id": "bruce_stats_posts",  # info: "id" : "bruce_stats_posts" ,
        "enabled": os.environ.get("RR_BRUCE_STATS", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Bruce measured host and EcoFlow desk sample. Dry-run unless RR_BRUCE_STATS_SEND=1.",  # info: "description" : "Bruce measured host and EcoFlow desk sample. Dry-run unless RR_BRUCE_STATS_SEND=1." ,
        "at_times": ["07:00", "15:00", "21:00"],  # info: "at_times" : [ "07:00" , "15:00" , "21:00" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/BruceStats/scripts/bruce_stats.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/BruceStats/scripts/bruce_stats.py"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": os.environ.get("RR_BRUCE_STATS_SEND", "0") == "1",  # info: "needs_internet" : os . environ . get (
        "cwd": f"{PACIFIC}/Communications/BruceStats",  # info: "cwd" : f" { PACIFIC } /Communications/BruceStats "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # AdSense end-of-day (2026-09-30, WO-MIG-38). OFF unless RR_ADSENSE=1 at poller start.
        # No key writes not_configured and does not call Google. No Discord.
        "id": "adsense_eod",  # info: "id" : "adsense_eod" ,
        "enabled": os.environ.get("RR_ADSENSE", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "AdSense 7-day snapshot -> Database Advertising/adsense-last.json. Gated off. No key does not call the API.",  # info: "description" : "AdSense 7-day snapshot -> Database Advertising/adsense-last.json. Gated off. No key does not 
        "at_times": ["21:00"],  # info: "at_times" : [ "21:00" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Advertising/scripts/adsense_eod.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Advertising/scripts/adsense_eod.py"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Advertising",  # info: "cwd" : f" { PACIFIC } /Advertising "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # AdMob end-of-day (2026-09-30, WO-MIG-38). OFF unless RR_ADMOB=1 at poller start.
        # No key writes not_configured and does not call Google. Refresh token does not fall back.
        "id": "admob_eod",  # info: "id" : "admob_eod" ,
        "enabled": os.environ.get("RR_ADMOB", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "AdMob 7-day snapshot -> Database Advertising/admob-last.json. Gated off. No key does not call the API.",  # info: "description" : "AdMob 7-day snapshot -> Database Advertising/admob-last.json. Gated off. No key does not call
        "at_times": ["21:05"],  # info: "at_times" : [ "21:05" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Advertising/scripts/admob_eod.py"',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Advertising/scripts/admob_eod.py"
        "timeout_sec": 90,  # info: "timeout_sec" : 90 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Advertising",  # info: "cwd" : f" { PACIFIC } /Advertising "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Overnight relay (WO-MIG-31). OFF unless RR_OVERNIGHT_RELAY=1 at poller start.
        # Writes a status file only. No Discord post. No invented watts.
        "id": "overnight_relay",  # info: "id" : "overnight_relay" ,
        "enabled": os.environ.get("RR_OVERNIGHT_RELAY", "0") == "1",  # info: "enabled" : os . environ . get (
        "description": "Write Database Communications/Inbox/overnight-last.txt at 22:20 HST. Gated off. No Discord post.",  # info: "description" : "Write Database Communications/Inbox/overnight-last.txt at 22:20 HST. Gated off. No Discord po
        "at_times": ["22:20"],  # info: "at_times" : [ "22:20" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Inbox/scripts/inbox.py" overnight',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Communications/Inbox/scripts/inbox.py" overnight
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Communications/Inbox",  # info: "cwd" : f" { PACIFIC } /Communications/Inbox "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # API prices (WO-MIG-35). OFF. Public-doc GET only if RR_API_PRICES=1.
        # The script also refuses HTTP when that gate is unset.
        "id": "api_prices",  # info: "id" : "api_prices" ,
        "enabled": False,  # info: "enabled" : False ,
        "description": "Public API price catalog -> Database System/ApiPrices/. Gated off. No HTTP unless RR_API_PRICES=1.",  # info: "description" : "Public API price catalog -> Database System/ApiPrices/. Gated off. No HTTP unless RR_API_PRIC
        "at_times": ["10:25"],  # info: "at_times" : [ "10:25" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/System/ApiPrices/scripts/job.py" refresh',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /System/ApiPrices/scripts/job.py" refresh
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/System/ApiPrices",  # info: "cwd" : f" { PACIFIC } /System/ApiPrices "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Cursor fallback (WO-MIG-35). OFF. No cursor agent unless RR_API_SPEND=1.
        # Text would stay under Database System/ApiPrices/fallback/. No report write.
        "id": "cursor_fallback",  # info: "id" : "cursor_fallback" ,
        "enabled": False,  # info: "enabled" : False ,
        "description": "One Cursor ask-mode fallback. Gated off. No agent unless RR_API_SPEND=1. Does not write reports.",  # info: "description" : "One Cursor ask-mode fallback. Gated off. No agent unless RR_API_SPEND=1. Does not write repor
        "at_times": ["10:22", "16:22"],  # info: "at_times" : [ "10:22" , "16:22" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/System/ApiPrices/scripts/job.py" cursor-drain',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /System/ApiPrices/scripts/job.py" cursor-drain
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/System/ApiPrices",  # info: "cwd" : f" { PACIFIC } /System/ApiPrices "
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # Report-board catch-up. OFF unless RR_REPORT_BOARD=1. Text only. Never plays audio.
        "id": "reports_board_catchup",  # info: "id" : "reports_board_catchup" ,
        "enabled": os.environ.get("RR_REPORT_BOARD", "0") == "1",  # info: "enabled" : os . environ . get ( "RR_REPORT_BOARD" , "0" ) == "1" ,
        "description": "Run one due morning or midday report from the board. Text only. No --voice and no speaker playback.",  # info: "description" : "Run one due morning or midday report from the board. Text only. No --voice and no speaker playback." ,
        "at_times": ["14:00"],  # info: "at_times" : [ "14:00" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/scripts/report_board.py" run-due',  # info: "command" : f' nice -n 10 python3 " { PACIFIC } /Reports/scripts/report_board.py" run-due ' ,
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "needs_internet": False,  # info: "needs_internet" : False ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd" : f" { PACIFIC } /Reports " ,
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # 8-hour public consolidations. Alexander asked for these on the hour, 2026-09-30.
        # Averages only the readings already stored. Placeholder link until the site publishes the page.
        "id": "discord_report_8h",  # info: "id" : "discord_report_8h" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Public 8-hour summary of each voice report at 00:00, 08:00, and 16:00 HST.",  # info: "description" : "Public 8-hour summary of each voice report at 00:00, 08:00, and 16:00 HST." ,
        "at_times": ["00:00", "08:00", "16:00"],  # info: "at_times" : [ "00:00" , "08:00" , "16:00" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Discord/scripts/report_rollups.py" 8h',  # info: command
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/Discord",  # info: cwd
        "env": {"RR_DISCORD_POST": "1"},  # info: "env" : { "RR_DISCORD_POST" : "1" } ,
    },  # info: } ,
    {  # info: {
        # Noon 24-hour public consolidations. One message per report channel.
        "id": "discord_report_24h",  # info: "id" : "discord_report_24h" ,
        "enabled": True,  # info: "enabled" : True ,
        "description": "Public 24-hour summary of each voice report at 12:00 HST.",  # info: "description" : "Public 24-hour summary of each voice report at 12:00 HST." ,
        "at_times": ["12:00"],  # info: "at_times" : [ "12:00" ] ,
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'nice -n 10 python3 "{PACIFIC}/Communications/Discord/scripts/report_rollups.py" 24h',  # info: command
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/Discord",  # info: cwd
        "env": {"RR_DISCORD_POST": "1"},  # info: "env" : { "RR_DISCORD_POST" : "1" } ,
    },  # info: } ,
    # --- TEMPLATE (ON_AT) — copy from the next line through the closing brace, paste ABOVE this template, remove the leading # ---
    # {
    #     "id": "example_on_at",
    #     "enabled": False,
    #     "at_times": ["12:00"],
    #     "description": "One sentence: what this job does and whether it sends, spends, or moves hardware.",
    #     "builtin": "",
    #     "command": f'nice -n 10 python3 "{PACIFIC}/path/to/script.py"',
    #     "timeout_sec": 120,
    #     "needs_internet": False,
    #     "cwd": f"{PACIFIC}",
    #     "env": {},
    # },
    # --- end TEMPLATE (ON_AT) ---
    # Leave enabled False until Alexander names this job. A flag of the form RR_SOMETHING=1 belongs in enabled, not hardcoded True.
]  # info: ]

ECOFLOW_ACTIONS = f"{PACIFIC}/Energy/scripts/actions"  # info: set ECOFLOW_ACTIONS
ECOFLOW_LOCK = "/tmp/ecoflow-ble.lock"  # info: set ECOFLOW_LOCK


# ====================================================
# SECTION: function ecoflow_command
# What it does: ecoflow command.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ecoflow_command(script: str) -> str:  # info: def ecoflow_command
    return f"flock -w 60 {ECOFLOW_LOCK} bash {ECOFLOW_ACTIONS}/{script}"  # info: return f" flock -w 60 { ECOFLOW_LOCK } bash {


# ====================================================
# SECTION: TOGGLES
# What it does: EcoFlow actuating actions. Left empty on purpose until Alexander names an action to run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
TOGGLES = []  # info: set TOGGLES
# ====================================================
# SECTION: READS
# What it does: EcoFlow read scripts the poller can call. Each row is an id plus the script path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
READS = [  # info: set READS
    {"id": "delta2_read", "script": f"{PACIFIC}/Energy/scripts/read/delta2-read.sh"},  # info: { "id" : "delta2_read" , "script" : f"
    {"id": "river2pro_read", "script": f"{PACIFIC}/Energy/scripts/read/river2pro-read.sh"},  # info: { "id" : "river2pro_read" , "script" : f"
]  # info: ]
