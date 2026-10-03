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
#   Then recurring: EXACT_TIME (hourly process sequence).
# EXACT_TIME = hourly process sequence. Same minute:second every hour (desk TZ = HST).
#   at_minute 0-59, at_second 0/5/10/15/20/25/30/35/40/45/50/55 (start of that 5-second slot).
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
# Canonical internet collectors live here (not under Pacific/). Fail-safe = run-local-bank.sh.
ML2 = "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/3 - RootRecord-US-Mainland-Two"  # info: set ML2
# Radio station + RadioRss live here (not under Pacific or ML2).
ML1 = "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/2 - RootRecord-US-Mainland-One"  # info: set ML1
DATABASE = "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"  # info: set DATABASE

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
        "description": "Fail-safe: one ML2 weather_hawaii collect → Database (ML2 tree only). Gated off when RR_LOCAL_DATA_POLL=0 (remote ML2 owns).",  # info: ML2 local-bank fail-safe
        "builtin": "",  # info: "builtin" : "" ,
        "command": f'bash "{ML2}/scripts/run-local-bank.sh" --only weather_hawaii',  # info: ML2 canonical
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}",  # info: "cwd" : ML2
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: bank into Pacific Database
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
# SECTION: EXACT_TIME
# What it does: :00–:29 is stats, github, and EcoFlow leapfrog. All other hourly work is :30 or later. Voice batch at :42; :55 catch-up push to ML1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
EXACT_TIME = [  # info: set EXACT_TIME
    # --- TEMPLATE (EXACT_TIME) — copy from the next line through the closing brace, paste under the minute + 5-second slot, remove the leading # ---
    # {
    #     "id": "example_exact_time",
    #     "enabled": False,
    #     "at_minute": 0,
    #     "at_second": 0,
    #     "description": "One sentence: what this job does and whether it sends, spends, or moves hardware.",
    #     "builtin": "",
    #     "command": f'nice -n 10 python3 "{PACIFIC}/path/to/script.py"',
    #     "timeout_sec": 5,
    #     "needs_internet": False,
    #     "cwd": f"{PACIFIC}",
    #     "env": {},
    # },
    # --- end TEMPLATE (EXACT_TIME) ---
    # :00–:29 is only sys_stats, github_sync, and the EcoFlow leapfrog. Everything else is :30 or later.
    # Voice hour batch at :42 (generate_hour_reports.py → Timing + early ML1 push). :55 radio_push is catch-up.
    {  # info: {
        # stacks on every 5s slot, all hour.
        "id": "sys_stats_cycle",  # info: "id" : "sys_stats_cycle" ,
        "enabled": True,  # info: "enabled" : True,
        "every_seconds": 5,  # info: "every_seconds" : 5 ,
        "description": "Host CPU/load/mem \u2192 Database/SYSTEM.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/System/scripts/sys-sample.sh\"",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/System",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # stacks on every 5s slot, all hour.
        "id": "github_sync_all",  # info: "id" : "github_sync_all" ,
        "enabled": True,  # info: "enabled" : True,
        "every_seconds": 5,  # info: "every_seconds" : 5 ,
        "description": "Sync all repos.conf rows (pull/merge/push) via Pacific Github catalog.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Github/scripts/sync-all.sh\"",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Github",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # leapfrog: Delta 2 on even 10s marks, all hour.
        "id": "delta2_read",  # info: "id" : "delta2_read" ,
        "enabled": True,
        "every_seconds": 10,  # info: "every_seconds" : 10 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Delta 2 BLE snapshot on seconds 0, 10, 20, 30, 40, 50. River 2 Pro takes the other 5-second slots.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Energy/scripts/read/delta2-read.sh\"",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Energy/scripts/read",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # leapfrog: River 2 Pro on the other 5s slots, all hour.
        "id": "river2pro_read",  # info: "id" : "river2pro_read" ,
        "enabled": True,
        "every_seconds": 10,  # info: "every_seconds" : 10 ,
        "at_second": 5,  # info: "at_second" : 5 ,
        "description": "River 2 Pro BLE snapshot on seconds 5, 15, 25, 35, 45, 55. Delta 2 takes the other 5-second slots.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Energy/scripts/read/river2pro-read.sh\"",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Energy/scripts/read",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # stacks every 10s, all hour.
        "id": "security_camera_frame_grab",  # info: "id" : "security_camera_frame_grab" ,
        "enabled": True,  # info: "enabled" : True,
        "every_seconds": 10,  # info: "every_seconds" : 10 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Grab ch1-4 stills to /home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Images/.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Security/Cameras/grab_all.sh\"",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Security/Cameras",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # every minute at second 0. Rolls 1sec into 1min, 5min, and 15min.
        "id": "energy_consolidate_minutes",  # info: "id" : "energy_consolidate_minutes" ,
        "enabled": True,  # info: "enabled" : True ,
        "every_seconds": 60,  # info: "every_seconds" : 60 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Every minute at :00, Energy/scripts/consolidate.py minutes — roll closed EcoFlow samples into the 1min, 5min, and 15min buckets.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Energy/scripts/consolidate.py\" minutes",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Energy",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # every minute at second 30. Rolls those buckets into the hour and above.
        "id": "energy_consolidate_hours",  # info: "id" : "energy_consolidate_hours" ,
        "enabled": True,  # info: "enabled" : True ,
        "every_seconds": 60,  # info: "every_seconds" : 60 ,
        "at_second": 30,  # info: "at_second" : 30 ,
        "description": "Every minute at :30, Energy/scripts/consolidate.py hours — roll closed EcoFlow buckets into the hour and above, rewrite Energy/layers/periods.json, and at clock :30 archive automations_current.log into Logs/Automations/Archive.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Energy/scripts/consolidate.py\" hours",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Energy",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # every minute at second 0. Same tree shape as Energy: System/system.db + System/layers.
        "id": "system_consolidate_minutes",  # info: "id" : "system_consolidate_minutes" ,
        "enabled": True,  # info: "enabled" : True ,
        "every_seconds": 60,  # info: "every_seconds" : 60 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Every minute at :00, System/scripts/consolidate.py minutes — roll closed host samples into the 1min, 5min, and 15min buckets.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/System/scripts/consolidate.py\" minutes",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/System",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # every minute at second 30. Hour and above for the System tree.
        "id": "system_consolidate_hours",  # info: "id" : "system_consolidate_hours" ,
        "enabled": True,  # info: "enabled" : True ,
        "every_seconds": 60,  # info: "every_seconds" : 60 ,
        "at_second": 30,  # info: "at_second" : 30 ,
        "description": "Every minute at :30, System/scripts/consolidate.py hours — roll closed host buckets into the hour, day, week, month, and year.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/System/scripts/consolidate.py\" hours",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/System",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,

    # ---------- minute 00 of every hour ----------
    # --- 00:00–00:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # Prebuilt hour chime. The same job also sits at :30.
        "id": "voice_hourly_chime",  # info: "id" : "voice_hourly_chime" ,
        "enabled": os.environ.get("RR_VOICE_HOURLY_CHIME", "0") == "1",
        "at_minute": 0,  # info: "at_minute" : 0 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Prebuilt chime at :00 and :30 (Ava, Bruce, Carly leapfrog by the hour). Plays Media/Audio/Voice/Chimes. No live render.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" hourly_chime",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 00:05–00:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 00:10–00:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 00:15–00:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 00:20–00:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 00:25–00:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 00:30–00:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 00:35–00:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 00:40–00:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 00:45–00:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 00:50–00:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 00:55–00:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 01 of every hour ----------
    # --- 01:00–01:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 01:05–01:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 01:10–01:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 01:15–01:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 01:20–01:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 01:25–01:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 01:30–01:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 01:35–01:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 01:40–01:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 01:45–01:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 01:50–01:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 01:55–01:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 02 of every hour ----------
    # --- 02:00–02:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 02:05–02:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 02:10–02:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 02:15–02:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 02:20–02:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 02:25–02:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 02:30–02:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 02:35–02:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 02:40–02:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 02:45–02:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 02:50–02:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 02:55–02:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 03 of every hour ----------
    # --- 03:00–03:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 03:05–03:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 03:10–03:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 03:15–03:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 03:20–03:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 03:25–03:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 03:30–03:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 03:35–03:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 03:40–03:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 03:45–03:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 03:50–03:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 03:55–03:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 04 of every hour ----------
    # --- 04:00–04:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 04:05–04:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 04:10–04:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 04:15–04:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 04:20–04:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 04:25–04:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 04:30–04:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 04:35–04:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 04:40–04:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 04:45–04:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 04:50–04:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 04:55–04:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 05 of every hour ----------
    # --- 05:00–05:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 05:05–05:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 05:10–05:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 05:15–05:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 05:20–05:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 05:25–05:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 05:30–05:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 05:35–05:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 05:40–05:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 05:45–05:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 05:50–05:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 05:55–05:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 06 of every hour ----------
    # --- 06:00–06:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 06:05–06:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 06:10–06:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 06:15–06:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 06:20–06:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 06:25–06:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 06:30–06:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 06:35–06:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 06:40–06:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 06:45–06:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 06:50–06:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 06:55–06:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 07 of every hour ----------
    # --- 07:00–07:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 07:05–07:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 07:10–07:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 07:15–07:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 07:20–07:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 07:25–07:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 07:30–07:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 07:35–07:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 07:40–07:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 07:45–07:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 07:50–07:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 07:55–07:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 08 of every hour ----------
    # --- 08:00–08:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 08:05–08:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 08:10–08:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 08:15–08:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 08:20–08:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 08:25–08:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 08:30–08:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 08:35–08:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 08:40–08:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 08:45–08:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 08:50–08:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 08:55–08:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 09 of every hour ----------
    # --- 09:00–09:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 09:05–09:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 09:10–09:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 09:15–09:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 09:20–09:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 09:25–09:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 09:30–09:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 09:35–09:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 09:40–09:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 09:45–09:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 09:50–09:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 09:55–09:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 10 of every hour ----------
    # --- 10:00–10:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 10:05–10:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 10:10–10:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 10:15–10:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 10:20–10:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 10:25–10:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 10:30–10:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 10:35–10:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 10:40–10:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 10:45–10:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 10:50–10:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 10:55–10:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 11 of every hour ----------
    # --- 11:00–11:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 11:05–11:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 11:10–11:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 11:15–11:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 11:20–11:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 11:25–11:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 11:30–11:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 11:35–11:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 11:40–11:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 11:45–11:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 11:50–11:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 11:55–11:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 12 of every hour ----------
    # --- 12:00–12:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 12:05–12:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 12:10–12:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 12:15–12:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 12:20–12:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 12:25–12:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 12:30–12:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 12:35–12:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 12:40–12:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 12:45–12:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 12:50–12:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 12:55–12:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 13 of every hour ----------
    # --- 13:00–13:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 13:05–13:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 13:10–13:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 13:15–13:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 13:20–13:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 13:25–13:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 13:30–13:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 13:35–13:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 13:40–13:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 13:45–13:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 13:50–13:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 13:55–13:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 14 of every hour ----------
    # --- 14:00–14:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 14:05–14:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 14:10–14:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 14:15–14:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 14:20–14:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 14:25–14:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 14:30–14:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 14:35–14:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 14:40–14:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 14:45–14:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 14:50–14:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 14:55–14:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 15 of every hour ----------
    # --- 15:00–15:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 15:05–15:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 15:10–15:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 15:15–15:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 15:20–15:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 15:25–15:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 15:30–15:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 15:35–15:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 15:40–15:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 15:45–15:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 15:50–15:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 15:55–15:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 16 of every hour ----------
    # --- 16:00–16:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 16:05–16:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 16:10–16:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 16:15–16:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 16:20–16:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 16:25–16:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 16:30–16:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 16:35–16:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 16:40–16:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 16:45–16:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 16:50–16:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 16:55–16:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 17 of every hour ----------
    # --- 17:00–17:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 17:05–17:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 17:10–17:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 17:15–17:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 17:20–17:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 17:25–17:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 17:30–17:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 17:35–17:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 17:40–17:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 17:45–17:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 17:50–17:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 17:55–17:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 18 of every hour ----------
    # --- 18:00–18:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 18:05–18:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 18:10–18:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 18:15–18:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 18:20–18:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 18:25–18:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 18:30–18:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 18:35–18:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 18:40–18:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 18:45–18:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 18:50–18:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 18:55–18:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 19 of every hour ----------
    # --- 19:00–19:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 19:05–19:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 19:10–19:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 19:15–19:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 19:20–19:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 19:25–19:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 19:30–19:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 19:35–19:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 19:40–19:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 19:45–19:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 19:50–19:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 19:55–19:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 20 of every hour ----------
    # --- 20:00–20:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 20:05–20:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 20:10–20:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 20:15–20:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 20:20–20:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 20:25–20:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 20:30–20:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 20:35–20:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 20:40–20:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 20:45–20:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 20:50–20:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 20:55–20:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 21 of every hour ----------
    # --- 21:00–21:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 21:05–21:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 21:10–21:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 21:15–21:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 21:20–21:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 21:25–21:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 21:30–21:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 21:35–21:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 21:40–21:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 21:45–21:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 21:50–21:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 21:55–21:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 22 of every hour ----------
    # --- 22:00–22:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 22:05–22:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 22:10–22:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 22:15–22:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 22:20–22:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 22:25–22:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 22:30–22:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 22:35–22:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 22:40–22:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 22:45–22:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 22:50–22:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 22:55–22:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 23 of every hour ----------
    # --- 23:00–23:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 23:05–23:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 23:10–23:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 23:15–23:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 23:20–23:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 23:25–23:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 23:30–23:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 23:35–23:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 23:40–23:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 23:45–23:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 23:50–23:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 23:55–23:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 24 of every hour ----------
    # --- 24:00–24:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 24:05–24:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 24:10–24:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 24:15–24:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 24:20–24:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 24:25–24:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 24:30–24:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 24:35–24:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 24:40–24:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 24:45–24:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 24:50–24:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 24:55–24:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 25 of every hour ----------
    # --- 25:00–25:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 25:05–25:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 25:10–25:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 25:15–25:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 25:20–25:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 25:25–25:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 25:30–25:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 25:35–25:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 25:40–25:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 25:45–25:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 25:50–25:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 25:55–25:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 26 of every hour ----------
    # --- 26:00–26:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 26:05–26:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 26:10–26:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 26:15–26:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 26:20–26:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 26:25–26:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 26:30–26:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 26:35–26:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 26:40–26:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 26:45–26:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 26:50–26:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 26:55–26:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 27 of every hour ----------
    # --- 27:00–27:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 27:05–27:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 27:10–27:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 27:15–27:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 27:20–27:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 27:25–27:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 27:30–27:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 27:35–27:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 27:40–27:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 27:45–27:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 27:50–27:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 27:55–27:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 28 of every hour ----------
    # --- 28:00–28:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 28:05–28:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 28:10–28:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 28:15–28:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 28:20–28:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 28:25–28:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 28:30–28:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 28:35–28:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 28:40–28:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 28:45–28:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 28:50–28:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 28:55–28:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 29 of every hour ----------
    # --- 29:00–29:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 29:05–29:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 29:10–29:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 29:15–29:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 29:20–29:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 29:25–29:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 29:30–29:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 29:35–29:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 29:40–29:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 29:45–29:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 29:50–29:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 29:55–29:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 30 of every hour ----------
    # --- 30:00–30:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # Prebuilt half-hour chime. The same job also sits at :00.
        "id": "voice_hourly_chime",  # info: "id" : "voice_hourly_chime" ,
        "enabled": os.environ.get("RR_VOICE_HOURLY_CHIME", "0") == "1",
        "at_minute": 30,  # info: "at_minute" : 30 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Prebuilt chime at :00 and :30 (Ava, Bruce, Carly leapfrog by the hour). Plays Media/Audio/Voice/Chimes. No live render.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" hourly_chime",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 30:05–30:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # automations_current.log archive is owned by Energy/scripts/consolidate.py hours at clock :30
    {  # info: {
        # hourly work at :30 or later.
        "id": "heartbeat",  # info: "id" : "heartbeat" ,
        "enabled": True,
        "at_minute": 30,  # info: "at_minute" : 30 ,
        "at_second": 5,  # info: "at_second" : 5 ,
        "description": "ENERGY snapshot once per minute.",  # info: "description"
        "builtin": "heartbeat",  # info: "builtin"
        "command": "",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": "",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 30:10–30:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # hourly work at :30 or later.
        "id": "system_uptime_log",  # info: "id" : "system_uptime_log" ,
        "enabled": os.environ.get("RR_UPTIME_LOG", "0") == "1",
        "at_minute": 30,  # info: "at_minute" : 30 ,
        "at_second": 10,  # info: "at_second" : 10 ,
        "description": "Desk heartbeat plus offline and morning-return samples -> Database System/uptime/. Averages start from the first sample after recording begins.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{PACIFIC}/System/scripts/uptime_log.py\" tick",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/System",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 30:15–30:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "ensure_tunnel_online",  # info: "id" : "ensure_tunnel_online" ,
        "enabled": True,
        "at_minute": 30,  # info: "at_minute" : 30 ,
        "at_second": 15,  # info: "at_second" : 15 ,
        "description": "Start Cloudflare if internet is up and tunnel is down.",  # info: "description"
        "builtin": "ensure_tunnel_online",  # info: "builtin"
        "command": "",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": "",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 30:20–30:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 30:25–30:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 30:30–30:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # Once a day at 00:30:30. Moves closed human ops logs into the ISO-week archive.
        "id": "reports_weekly_archive",  # info: "id" : "reports_weekly_archive" ,
        "enabled": True,  # info: "enabled" : True,
        "at_hour": 0,  # info: "at_hour" : 0 ,
        "at_minute": 30,  # info: "at_minute" : 30 ,
        "at_second": 30,  # info: "at_second" : 30 ,
        "description": "Move closed human ops logs into archive/YYYY-Www. Runs once a day at 00:30:30.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Reports/scripts/weekly_archive_logs.sh\"",  # info: "command"
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "cwd": f"{PACIFIC}/Reports/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 30:35–30:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 30:40–30:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 30:45–30:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 30:50–30:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 30:55–30:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 31 of every hour ----------
    # --- 31:00–31:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # One interface counter snapshot at :31. Hour and day figures are byte deltas, not an all-time sum.
        "id": "system_net_sample",  # info: "id" : "system_net_sample" ,
        "enabled": os.environ.get("RR_NET_SAMPLES", "0") == "1",
        "at_minute": 31,  # info: "at_minute" : 31 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "One default-route counter snapshot at :31. Hour and day totals are rx+tx deltas for that window, not an all-time sum. No send.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/System/scripts/host_desks.py\" net-sample",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/System/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 31:05–31:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 31:10–31:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 31:15–31:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 31:20–31:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 31:25–31:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 31:30–31:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 31:35–31:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 31:40–31:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 31:45–31:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 31:50–31:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 31:55–31:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 32 of every hour ----------
    # --- 32:00–32:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 32:05–32:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 32:10–32:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 32:15–32:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 32:20–32:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 32:25–32:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 32:30–32:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 32:35–32:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 32:40–32:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 32:45–32:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 32:50–32:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # hourly work at :30 or later.
        "id": "energy_moon_phase",  # info: "id" : "energy_moon_phase" ,
        "enabled": os.environ.get("RR_MOON", "1") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 32,  # info: "at_minute" : 32 ,
        "at_second": 50,  # info: "at_second" : 50 ,
        "description": "Moon phase HST (Volcano/Puna) -> Database Weather/moon/moon_current.json. No send.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{PACIFIC}/Energy/scripts/moon_phase.py\"",  # info: "command"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Energy",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 32:55–32:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 33 of every hour ----------
    # --- 33:00–33:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 33:05–33:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 33:10–33:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 33:15–33:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 33:20–33:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 33:25–33:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "ml2_datapack_pickup",  # info: "id" : "ml2_datapack_pickup" ,
        "enabled": True,
        "at_minute": 33,  # info: "at_minute" : 33 ,
        "at_second": 25,  # info: "at_second" : 25 ,
        "description": "Solar catch-up: drain ML2 Telegram offline datapacks into Database (timer + boot). Same path_rel tree as SSH bank stream.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 bash \"{PACIFIC}/Communications/telegram/scripts/run-datapack-pickup.sh\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/telegram",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 33:30–33:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 33:35–33:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "geology_kilauea_cams",  # info: "id" : "geology_kilauea_cams" ,
        "enabled": os.environ.get("RR_KILAUEA_CAMS", "0") == "1",
        "at_minute": 33,  # info: "at_minute" : 33 ,
        "at_second": 35,  # info: "at_second" : 35 ,
        "description": "Fail-safe: ML2 geology_kilauea_cams → Database Volcanoes/Hawaii/Cams/*_current (ML2 tree only).",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f'bash "{ML2}/scripts/run-local-bank.sh" --only geology_kilauea_cams',  # info: ML2 canonical
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: bank into Pacific Database
    },  # info: } ,
    {  # info: {
        "id": "geology_collect",  # info: "id" : "geology_collect" ,
        "enabled": os.environ.get("RR_GEOLOGY", "0") == "1",
        "every_seconds": 300,  # info: "every_seconds" : 300 ,
        "description": "Fail-safe: ML2 geology (quakes + HVO) → Database Geology/ (ML2 tree only). Gated off when RR_LOCAL_DATA_POLL=0.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f'bash "{ML2}/scripts/run-local-bank.sh" --only geology',  # info: ML2 canonical
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: bank into Pacific Database
    },  # info: } ,
    {  # info: {
        "id": "hawaii_to_ml2",  # info: "id" : "hawaii_to_ml2" ,
        "enabled": os.environ.get("RR_HUB_HAWAII", "1") == "1",
        "every_seconds": 300,  # info: "every_seconds" : 300 ,
        "description": "Hub inbound: Database Geology/Weather/RadioRss/Discord → ML2 var/bank (SSH). Desk paths when RR_HUB_MODE=local. Voice air stays radio_push → ML1 only.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f'bash "{ML2}/scripts/hawaii-to-ml2.sh"',  # info: "command"
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE, "RR_HUB_MODE": os.environ.get("RR_HUB_MODE", "auto")},  # info: "env"
    },  # info: } ,
    # --- 33:40–33:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # hourly work at :30 or later.
        "id": "geology_kilauea_public_draft",  # info: "id" : "geology_kilauea_public_draft" ,
        "enabled": os.environ.get("RR_KILAUEA_DRAFT", "0") == "1",
        "at_minute": 33,  # info: "at_minute" : 33 ,
        "at_second": 40,  # info: "at_second" : 40 ,
        "description": "Queue a Kilauea public draft from Geology/Volcanoes/Hawaii/kilauea_current.json when the HVO notice id or alert level changes. No send.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Geology/PublicDraftQueue/scripts/queue_draft.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Geology/PublicDraftQueue",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 33:45–33:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "ai_processing_report_hourly",  # info: "id" : "ai_processing_report_hourly" ,
        "enabled": os.environ.get("RR_AI_REPORT", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 33,  # info: "at_minute" : 33 ,
        "at_second": 45,  # info: "at_second" : 45 ,
        "description": "Rotate inference JSONL (daily Archive/) + write Database Logs/AI/Reports/ai-processing-report_current.md.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/System/scripts/plumbing/ai-log-rotate.sh\" && nice -n 10 python3 \"{PACIFIC}/Reports/ai_processing_report.py\"",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 33:50–33:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 33:55–33:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 34 of every hour ----------
    # --- 34:00–34:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 34:05–34:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 34:10–34:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 34:15–34:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 34:20–34:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 34:25–34:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 34:30–34:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 34:35–34:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 34:40–34:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 34:45–34:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 34:50–34:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 34:55–34:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 35 of every hour ----------
    # --- 35:00–35:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 35:05–35:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 35:10–35:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 35:15–35:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 35:20–35:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 35:25–35:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 35:30–35:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 35:35–35:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 35:40–35:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 35:45–35:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 35:50–35:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 35:55–35:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "ai_usage_report",  # info: "id" : "ai_usage_report" ,
        "enabled": os.environ.get("RR_AI_USAGE", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 35,  # info: "at_minute" : 35 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Write Database Reports/AI-Usage/last-summary.json from the local token ledger. No network.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/AI-Usage/scripts/ai_usage_report.py\"",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Reports/AI-Usage/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # ---------- minute 36 of every hour ----------
    # --- 36:00–36:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 36:05–36:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 36:10–36:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 36:15–36:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 36:20–36:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 36:25–36:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 36:30–36:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 36:35–36:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 36:40–36:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 36:45–36:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 36:50–36:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 36:55–36:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 37 of every hour ----------
    # --- 37:00–37:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 37:05–37:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "template_reports_event",  # info: "id" : "template_reports_event" ,
        "enabled": os.environ.get("RR_TEMPLATE_REPORTS", "0") == "1",
        "at_minute": 37,  # info: "at_minute" : 37 ,
        "at_second": 5,  # info: "at_second" : 5 ,
        "description": "Fill Event Action Log (AI Inference Activity Log) from inference JSONL. No Library write.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/template_fill.py\" --template event --draft auto",  # info: "command"
        "timeout_sec": 90,  # info: "timeout_sec" : 90 ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 37:10–37:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 37:15–37:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 37:20–37:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 37:25–37:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 37:30–37:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 37:35–37:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 37:40–37:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 37:45–37:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "template_reports_worklog",  # info: "id" : "template_reports_worklog" ,
        "enabled": os.environ.get("RR_TEMPLATE_REPORTS", "0") == "1",
        "at_minute": 37,  # info: "at_minute" : 37 ,
        "at_second": 45,  # info: "at_second" : 45 ,
        "description": "Fill Library worklog session template from measured data. No Library write.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/template_fill.py\" --template worklog --draft auto",  # info: "command"
        "timeout_sec": 90,  # info: "timeout_sec" : 90 ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 37:50–37:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 37:55–37:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 38 of every hour ----------
    # --- 38:00–38:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 38:05–38:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 38:10–38:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 38:15–38:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 38:20–38:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 38:25–38:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "template_reports_checkpoint",  # info: "id" : "template_reports_checkpoint" ,
        "enabled": os.environ.get("RR_TEMPLATE_REPORTS", "0") == "1",
        "at_minute": 38,  # info: "at_minute" : 38 ,
        "at_second": 25,  # info: "at_second" : 25 ,
        "description": "Fill Library checkpoint template from measured data. No Library write.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/template_fill.py\" --template checkpoint --draft auto",  # info: "command"
        "timeout_sec": 90,  # info: "timeout_sec" : 90 ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 38:30–38:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 38:35–38:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 38:40–38:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 38:45–38:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 38:50–38:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 38:55–38:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 39 of every hour ----------
    # --- 39:00–39:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 39:05–39:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "template_reports_workorder",  # info: "id" : "template_reports_workorder" ,
        "enabled": os.environ.get("RR_TEMPLATE_REPORTS", "0") == "1",
        "at_minute": 39,  # info: "at_minute" : 39 ,
        "at_second": 5,  # info: "at_second" : 5 ,
        "description": "Fill Library work-order draft template from measured backlog. No Library write.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/template_fill.py\" --template workorder --draft auto",  # info: "command"
        "timeout_sec": 90,  # info: "timeout_sec" : 90 ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 39:10–39:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 39:15–39:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 39:20–39:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 39:25–39:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 39:30–39:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 39:35–39:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 39:40–39:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 39:45–39:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "cloud_narrative_merged",  # info: "id" : "cloud_narrative_merged" ,
        "enabled": os.environ.get("RR_CLOUD_NARRATIVE", "0") == "1",
        "at_minute": 39,  # info: "at_minute" : 39 ,
        "at_second": 45,  # info: "at_second" : 45 ,
        "description": "CloudNarrative merged dry-run prompt package. No HTTP unless a separate spend sign-off.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/CloudNarrative/scripts/cloud_narrative.py\" merged --dry-run",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Reports/CloudNarrative/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 39:50–39:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 39:55–39:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 40 of every hour ----------
    # --- 40:00–40:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 40:05–40:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 40:10–40:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 40:15–40:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 40:20–40:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 40:25–40:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "cloud_narrative_kilauea",  # info: "id" : "cloud_narrative_kilauea" ,
        "enabled": os.environ.get("RR_CLOUD_NARRATIVE", "0") == "1",
        "at_minute": 40,  # info: "at_minute" : 40 ,
        "at_second": 25,  # info: "at_second" : 25 ,
        "description": "CloudNarrative kilauea dry-run prompt package. No HTTP unless a separate spend sign-off.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/CloudNarrative/scripts/cloud_narrative.py\" kilauea --dry-run",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Reports/CloudNarrative/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 40:30–40:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 40:35–40:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 40:40–40:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 40:45–40:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 40:50–40:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 40:55–40:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 41 of every hour ----------
    # --- 41:00–41:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 41:05–41:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "economy_brief",  # info: "id" : "economy_brief" ,
        "enabled": os.environ.get("RR_ECONOMY_BRIEF", "0") == "1",
        "at_minute": 41,  # info: "at_minute" : 41 ,
        "at_second": 5,  # info: "at_second" : 5 ,
        "description": "Daily economy brief markdown from desk-facts + kilauea-last. No Discord send.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/Economy-Brief/scripts/economy_brief.py\"",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Reports/Economy-Brief/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 41:10–41:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 41:15–41:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 41:20–41:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 41:25–41:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 41:30–41:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 41:35–41:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 41:40–41:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 41:45–41:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "cursor_fallback",  # info: "id" : "cursor_fallback" ,
        "enabled": False,  # info: "enabled" : False,
        "at_minute": 41,  # info: "at_minute" : 41 ,
        "at_second": 45,  # info: "at_second" : 45 ,
        "description": "One Cursor ask-mode fallback. Gated off. No agent unless RR_API_SPEND=1. Does not write reports.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/System/ApiPrices/scripts/job.py\" cursor-drain",  # info: "command"
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/System/ApiPrices",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 41:50–41:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 41:55–41:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 42 of every hour ----------
    # --- 42:00–42:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 42:05–42:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 42:10–42:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 42:15–42:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 42:20–42:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 42:25–42:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 42:30–42:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 42:35–42:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 42:40–42:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 42:45–42:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 42:50–42:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 42:55–42:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 43 of every hour ----------
    # --- 43:00–43:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # VOICE batch — measured ~8.6 min + 3 min cushion → start 12 min before :55.
        "id": "voice_hour_batch",  # info: "id" : "voice_hour_batch" ,
        "enabled": os.environ.get("RR_VOICE_HOUR_BATCH", os.environ.get("RR_RADIO_PUSH", "1")) == "1",
        "at_minute": 43,  # info: "at_minute" : 43 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Generate all hour-desk voice reports into Media/Audio/Voice/, record Timing averages, then radio_push --all to ML1 as soon as the batch finishes. :55 radio_push_hour is catch-up only.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/generate_hour_reports.py\"",  # info: "command"
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_VOICE_DELIVER": "0", "RR_VOICE_STATUS": "0", "RR_HOUR_BATCH_PUSH": "1"},  # info: push after batch; child desks still skip mid-push
    },  # info: } ,
    # --- 43:05–43:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 43:10–43:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 43:15–43:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 43:20–43:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 43:25–43:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 43:30–43:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 43:35–43:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 43:40–43:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 43:45–43:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 43:50–43:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 43:55–43:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 44 of every hour ----------
    # --- 44:00–44:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 44:05–44:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 44:10–44:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 44:15–44:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 44:20–44:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 44:25–44:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 44:30–44:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 44:35–44:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 44:40–44:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 44:45–44:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 44:50–44:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 44:55–44:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # TEXT/AI — :30 or later, finish before voice generation.
        "id": "api_prices",  # info: "id" : "api_prices" ,
        "enabled": False,  # info: "enabled" : False,
        "at_minute": 44,  # info: "at_minute" : 44 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Public API price catalog -> Database System/ApiPrices/. Gated off. No HTTP unless RR_API_PRICES=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/System/ApiPrices/scripts/job.py\" refresh",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/System/ApiPrices",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # ---------- minute 45 of every hour ----------
    # --- 45:00–45:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 45:05–45:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 45:10–45:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 45:15–45:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 45:20–45:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 45:25–45:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 45:30–45:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 45:35–45:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 45:40–45:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 45:45–45:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 45:50–45:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 45:55–45:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 46 of every hour ----------
    # --- 46:00–46:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 46:05–46:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_system_perf",  # info: "id" : "voice_system_perf" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_SYSTEM_PERF", "0") == "1",
        "at_minute": 46,  # info: "at_minute" : 46 ,
        "at_second": 5,  # info: "at_second" : 5 ,
        "description": "Bruce system report at :45, before the radio playlist snapshot. Host temperature is degrees Celsius. Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/system_perf.py\"",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 46:10–46:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 46:15–46:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 46:20–46:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 46:25–46:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 46:30–46:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 46:35–46:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 46:40–46:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 46:45–46:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 46:50–46:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_nws_weather",  # info: "id" : "voice_nws_weather" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_NWS", "0") == "1",
        "at_minute": 46,  # info: "at_minute" : 46 ,
        "at_second": 50,  # info: "at_second" : 50 ,
        "description": "Ava NWS Hawaii report from Database Weather/, at :45 so the file is on the station before the chime. Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" nws_weather",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 46:55–46:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 47 of every hour ----------
    # --- 47:00–47:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 47:05–47:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 47:10–47:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 47:15–47:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 47:20–47:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 47:25–47:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 47:30–47:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 47:35–47:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 47:40–47:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_remaining_tasks",  # info: "id" : "voice_remaining_tasks" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_REMAINING", "0") == "1",
        "at_minute": 47,  # info: "at_minute" : 47 ,
        "at_second": 40,  # info: "at_second" : 40 ,
        "description": "Bruce remaining tasks from the report board, at :45 before the radio snapshot. Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" remaining_tasks",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 47:45–47:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 47:50–47:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 47:55–47:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 48 of every hour ----------
    # --- 48:00–48:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 48:05–48:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 48:10–48:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 48:15–48:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_earthquake_report",  # info: "id" : "voice_earthquake_report" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_QUAKE", "0") == "1",
        "at_minute": 48,  # info: "at_minute" : 48 ,
        "at_second": 15,  # info: "at_second" : 15 ,
        "description": "Carly USGS earthquake report at :45 from Database Geology/, before the radio snapshot. Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" earthquake_report",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 48:20–48:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 48:25–48:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 48:30–48:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 48:35–48:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 48:40–48:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 48:45–48:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 48:50–48:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 48:55–48:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 49 of every hour ----------
    # --- 49:00–49:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_kilauea_report",  # info: "id" : "voice_kilauea_report" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_KILAUEA", "0") == "1",
        "at_minute": 49,  # info: "at_minute" : 49 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Carly Kilauea report at :45 from the HVO notice, before the radio snapshot. Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" kilauea_report",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 49:05–49:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 49:10–49:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 49:15–49:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 49:20–49:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 49:25–49:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 49:30–49:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 49:35–49:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 49:40–49:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 49:45–49:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_solar_desk",  # info: "id" : "voice_solar_desk" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_SOLAR", "0") == "1",
        "at_minute": 49,  # info: "at_minute" : 49 ,
        "at_second": 45,  # info: "at_second" : 45 ,
        "description": "Bruce combined energy+solar desk at :45: packs, sun times, newest channel-1 still, and this hour's camera look (refreshes when needed). Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" solar_desk",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 49:50–49:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 49:55–49:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 50 of every hour ----------
    # --- 50:00–50:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 50:05–50:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 50:10–50:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 50:15–50:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 50:20–50:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 50:25–50:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 50:30–50:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 50:35–50:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 50:40–50:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 50:45–50:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 50:50–50:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_security_desk",  # info: "id" : "voice_security_desk" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_SECURITY", "0") == "1",
        "at_minute": 50,  # info: "at_minute" : 50 ,
        "at_second": 50,  # info: "at_second" : 50 ,
        "description": "Carly security desk at :45 (firewall boot, ssh, listeners, failed sign-ins), before the radio snapshot. Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" security_desk",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 50:55–50:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 51 of every hour ----------
    # --- 51:00–51:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 51:05–51:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 51:10–51:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 51:15–51:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 51:20–51:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 51:25–51:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_bandwidth_desk",  # info: "id" : "voice_bandwidth_desk" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_BANDWIDTH", "0") == "1",
        "at_minute": 51,  # info: "at_minute" : 51 ,
        "at_second": 25,  # info: "at_second" : 25 ,
        "description": "Carly bandwidth desk at :45 from host byte samples plus Mainland Home/Radio analytics, before the radio snapshot. Voice note when RR_VOICE_DELIVER=1. Needs system_net_sample; analytics_pull optional.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" bandwidth_desk",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 51:30–51:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 51:35–51:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 51:40–51:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 51:45–51:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 51:50–51:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 51:55–51:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 52 of every hour ----------
    # --- 52:00–52:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 52:05–52:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_current_report",  # info: "id" : "voice_current_report" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1",  # info: legacy single; hour batch owns this
        "at_minute": 52,  # info: "at_minute" : 52 ,
        "at_second": 5,  # info: "at_second" : 5 ,
        "description": "Full current report at :45, after the other desks and before the radio snapshot. Heading is the slot time. Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" current_report",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 52:10–52:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 52:15–52:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 52:20–52:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 52:25–52:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 52:30–52:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 52:35–52:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 52:40–52:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 52:45–52:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 52:50–52:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 52:55–52:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 53 of every hour ----------
    # --- 53:00–53:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 53:05–53:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 53:10–53:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 53:15–53:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 53:20–53:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 53:25–53:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 53:30–53:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_hurricane_desk",  # info: "id" : "voice_hurricane_desk" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_HURRICANE", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 53,  # info: "at_minute" : 53 ,
        "at_second": 30,  # info: "at_second" : 30 ,
        "description": "Carly hurricane desk at :45, with the other desks, the hour snapshot (nearest tracked storm to a Hawaiian island + NWS tropical alerts). No delivery.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" hurricane_desk",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 53:35–53:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 53:40–53:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 53:45–53:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 53:50–53:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 53:55–53:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 54 of every hour ----------
    # --- 54:00–54:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 54:05–54:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 54:10–54:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 54:15–54:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # VOICE generation — :30 or later, finish by :55; no SSH here.
        "id": "voice_kilauea_image_check",  # info: "id" : "voice_kilauea_image_check" ,
        "enabled": os.environ.get("RR_VOICE_SINGLE", "0") == "1" and os.environ.get("RR_VOICE_KILAUEA_IMAGE", "0") == "1",  # info: soft gate,
        "at_minute": 54,  # info: "at_minute" : 54 ,
        "at_second": 15,  # info: "at_second" : 15 ,
        "description": "Carly Kilauea observation image check every 15 minutes: USGS HVO still through Gemma look; speaks checked line plus measured fountaining/activity. Voice note when RR_VOICE_DELIVER=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/voice_reports.py\" kilauea_image_check",  # info: "command"
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {"RR_RADIO_PUSH": "0"},  # info: "env"
    },  # info: } ,
    # --- 54:20–54:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 54:25–54:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 54:30–54:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 54:35–54:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 54:40–54:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 54:45–54:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 54:50–54:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 54:55–54:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 55 of every hour ----------
    # --- 55:00–55:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # SEND — all finished WAVs to ML1 over SSH.
        "id": "radio_push_hour",  # info: "id" : "radio_push_hour" ,
        "enabled": os.environ.get("RR_RADIO_PUSH", "1") == "1",
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 0,  # info: "at_second" : 0 ,
        "description": "Catch-up at :55: encode/send any hour-desk WAVs still missing on ML1 after voice_hour_batch early push (SSH remote, or desk rootrecord-radio/ when RR_RADIO_MODE=local/auto).",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{PACIFIC}/Media/Voice/scripts/radio_push.py\" --all",  # info: "command"
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 55:05–55:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "kilauea_draft_count",  # info: "id" : "kilauea_draft_count" ,
        "enabled": os.environ.get("RR_KILAUEA_DRAFT_ANNOUNCE", "0") == "1",
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 5,  # info: "at_second" : 5 ,
        "description": "Count queued Kilauea public drafts and write the sentence. Does not publish. Send stays off unless RR_KILAUEA_DRAFT_SEND=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Geology/PublicDraftQueue/scripts/announce_count.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Geology/PublicDraftQueue",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 55:10–55:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # hourly work at :30 or later.
        "id": "earthquake_discord_post",  # info: "id" : "earthquake_discord_post" ,
        "enabled": os.environ.get("RR_EARTHQUAKE_DISCORD", "0") == "1",
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 10,  # info: "at_second" : 10 ,
        "description": "Format Database Geology/Earthquakes last files and hand text to the Discord send pipe. Dry-run unless a separate send sign-off is set.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Geology/Earthquake-Discord/scripts/earthquake_discord_post.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Geology/Earthquake-Discord",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 55:15–55:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "council_quake_telegram",  # info: "id" : "council_quake_telegram" ,
        "enabled": os.environ.get("RR_COUNCIL_QUAKE", "0") == "1",
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 15,  # info: "at_second" : 15 ,
        "description": "Carly per-quake notice from Database Geology/Earthquakes/hawaii_current.json. Dry-run unless RR_COUNCIL_QUAKE_SEND=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Communications/CouncilQuake/scripts/quake_posts.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Communications/CouncilQuake",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 55:20–55:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # hourly work at :30 or later.
        "id": "analytics_pull",  # info: "id" : "analytics_pull" ,
        "enabled": os.environ.get("RR_ANALYTICS_PULL", "0") == "1",
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 20,  # info: "at_second" : 20 ,
        "description": "Mirror ML2 /api/analytics/daily -> Database Logs/Website/analytics/daily/. Gated off. No page JS. No send.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Website/scripts/analytics_pull.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Website",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 55:25–55:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "status_snapshot",  # info: "id" : "status_snapshot" ,
        "enabled": True,
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 25,  # info: "at_second" : 25 ,
        "description": "Backup write of the public status snapshot. The user timer publishes it every 30 s.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Website/scripts/live_data_pages.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Website",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 55:30–55:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # hourly work at :30 or later.
        "id": "live_picture",  # info: "id" : "live_picture" ,
        "enabled": os.environ.get("RR_LIVE_PICTURE", "0") == "1",
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 30,  # info: "at_second" : 30 ,
        "description": "Cover the stream still with the live desk numbers and copy it to the mainland thumb. Does not start a second encoder.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Video/scripts/live_picture.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Media/Video/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 55:35–55:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "radio_rss_poll",  # info: "id" : "radio_rss_poll" ,
        "enabled": os.environ.get("RR_RADIO_RSS", "0") == "1",
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 35,  # info: "at_second" : 35 ,
        "description": "ML1 RadioRss poll → Database Media/RadioRss/ (ML1 tree only). Does not speak.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f'bash "{ML1}/scripts/run-radio-rss.sh" poll',  # info: ML1 canonical
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML1}",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: bank into Pacific Database
    },  # info: } ,
    # --- 55:40–55:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    {  # info: {
        # hourly work at :30 or later.
        "id": "radio_news_update",  # info: "id" : "radio_news_update" ,
        "enabled": os.environ.get("RR_RADIO_NEWS", "0") == "1",
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 40,  # info: "at_second" : 40 ,
        "description": "Hourly ~20-25 minute news update at :08 (universities, science, NVIDIA/big tech, world, mainland weather, centrist government/politics). Ava, Bruce, and Carly share airtime. Writes news_update_part1 and news_update_part2, Uploads part 1 and part 2 only.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{ML1}/vendor/RadioRss/scripts/rss_radio.py\" news-hour --speak",  # info: ML1 vendor canonical
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML1}/vendor/RadioRss",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: Database bank
    },  # info: } ,
    # --- 55:45–55:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "media_hurricane_radio",  # info: "id" : "media_hurricane_radio" ,
        "enabled": os.environ.get("RR_HURRICANE_RADIO", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 55,  # info: "at_minute" : 55 ,
        "at_second": 45,  # info: "at_second" : 45 ,
        "description": "Request hurricane desk WAV through Report playback. No speaker.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{PACIFIC}/Media/HurricaneRadio/scripts/radio.py\" run",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Media/HurricaneRadio",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    # --- 55:50–55:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 55:55–55:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 56 of every hour ----------
    # --- 56:00–56:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 56:05–56:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 56:10–56:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 56:15–56:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 56:20–56:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 56:25–56:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 56:30–56:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 56:35–56:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 56:40–56:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 56:45–56:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 56:50–56:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 56:55–56:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 57 of every hour ----------
    # --- 57:00–57:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 57:05–57:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 57:10–57:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 57:15–57:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 57:20–57:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 57:25–57:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 57:30–57:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 57:35–57:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 57:40–57:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 57:45–57:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 57:50–57:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 57:55–57:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 58 of every hour ----------
    # --- 58:00–58:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 58:05–58:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 58:10–58:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 58:15–58:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 58:20–58:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 58:25–58:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 58:30–58:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 58:35–58:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 58:40–58:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 58:45–58:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 58:50–58:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 58:55–58:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # ---------- minute 59 of every hour ----------
    # --- 59:00–59:04 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 59:05–59:09 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 59:10–59:14 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 59:15–59:19 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 59:20–59:24 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 59:25–59:29 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 59:30–59:34 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 59:35–59:39 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 59:40–59:44 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 59:45–59:49 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    # --- 59:50–59:54 ---
    # stack: sys_stats_cycle, github_sync_all, delta2_read, security_camera_frame_grab
    # --- 59:55–59:59 ---
    # stack: sys_stats_cycle, github_sync_all, river2pro_read
    {  # info: {
        # hourly work at :30 or later.
        "id": "note_work_draft",  # info: "id" : "note_work_draft" ,
        "enabled": os.environ.get("RR_NOTE_DRAFT", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Turn one voice-report note into a Library work-order draft. Gated off. Does not call development.execute_work_order.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Media/Voice/scripts/note_draft.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Media/Voice/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "discord_report_relay",  # info: "id" : "discord_report_relay" ,
        "enabled": True,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Post each changed automated report to its Reports channel. Chat poller stays off.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{ML2}/vendor/Discord/scripts/report_relay.py\"",  # info: ML2 vendor canonical
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}/vendor/Discord",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: Database bank
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "reports_pipeline_tick",  # info: "id" : "reports_pipeline_tick" ,
        "enabled": os.environ.get("RR_REPORT_PIPELINE", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Record due news-select windows and refresh the stream queue. Does not render audio or open YouTube.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/pipeline/run.py\" tick",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Reports/pipeline",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "reports_board_catchup",  # info: "id" : "reports_board_catchup" ,
        "enabled": os.environ.get("RR_REPORT_BOARD", "0") == "1",  # info: "enabled" : os . environ . get ( "RR_REPORT_BOARD" , "0" ) == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Run one due morning or midday report from the board. Text only. No --voice and no speaker playback.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/scripts/report_board.py\" run-due",  # info: "command"
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "cwd": f"{PACIFIC}/Reports",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "reports_daily_roll_up",  # info: "id" : "reports_daily_roll_up" ,
        "enabled": True,  # info: "enabled" : True,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "WO-RPT-001 Phase C: WORKLOG counts \u2192 Library Session auto.md (measured only).",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Reports/scripts/daily_roll_up.sh\"",  # info: "command"
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{PACIFIC}/Reports/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "voice_timing_report",  # info: "id" : "voice_timing_report" ,
        "enabled": True,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Rewrite Library voice-timing.md from the automations log. Measured durations only. No model.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Reports/Voice-Timing/scripts/voice_timing_report.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Reports/Voice-Timing/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "bruce_stats_posts",  # info: "id" : "bruce_stats_posts" ,
        "enabled": os.environ.get("RR_BRUCE_STATS", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Bruce measured host and EcoFlow desk sample. Dry-run unless RR_BRUCE_STATS_SEND=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Communications/BruceStats/scripts/bruce_stats.py\"",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "cwd": f"{PACIFIC}/Communications/BruceStats",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "adsense_eod",  # info: "id" : "adsense_eod" ,
        "enabled": os.environ.get("RR_ADSENSE", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "AdSense 7-day snapshot -> Database Advertising/adsense-last.json. Gated off. No key does not call the API.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Advertising/scripts/adsense_eod.py\"",  # info: "command"
        "timeout_sec": 60,  # info: "timeout_sec" : 60 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Advertising",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "admob_eod",  # info: "id" : "admob_eod" ,
        "enabled": os.environ.get("RR_ADMOB", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "AdMob 7-day snapshot -> Database Advertising/admob-last.json. Gated off. No key does not call the API.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Advertising/scripts/admob_eod.py\"",  # info: "command"
        "timeout_sec": 90,  # info: "timeout_sec" : 90 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Advertising",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "overnight_relay",  # info: "id" : "overnight_relay" ,
        "enabled": os.environ.get("RR_OVERNIGHT_RELAY", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Write Database Communications/Inbox/overnight-last.txt at 22:20 HST. Gated off. No Discord post.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Communications/Inbox/scripts/inbox.py\" overnight",  # info: "command"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "cwd": f"{PACIFIC}/Communications/Inbox",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "discord_report_24h",  # info: "id" : "discord_report_24h" ,
        "enabled": False,  # hourly desks replace the noon repost,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Off. The hourly desks are the update. This was a second post of the same numbers.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{ML2}/vendor/Discord/scripts/report_rollups.py\" 24h",  # info: ML2 vendor canonical
        "timeout_sec": 180,  # info: "timeout_sec" : 180 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}/vendor/Discord",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: Database bank
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "weather_retention",  # info: "id" : "weather_retention" ,
        "enabled": False,  # GATED: off until Alexander reviews the dry run (Logs/Weather/Retention/). Apply = swap --dry-run for --apply.,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "ML2 vendor weather-retention.py (Database archive moves). Dry run by default. Code lives under US-Mainland-Two only.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{ML2}/vendor/Weather/scripts/weather-retention.py\" --dry-run",  # info: ML2 canonical
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{ML2}/vendor/Weather",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: Database bank
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "log_retention",  # info: "id" : "log_retention" ,
        "enabled": False,  # GATED: off. Command stays --dry-run. Live --apply needs RR_LOG_RETENTION_APPLY=1 (WO-MIG-41).,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Log retention (WO-MIG-41): move Database logs past 7 days to Archive/Previous-Datasets/Logs-<YYYYMM>/ (never delete). Dry run by default.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{PACIFIC}/System/LogRetention/scripts/log_retention.py\" --dry-run",  # info: "command"
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/System/LogRetention",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "path_index",  # info: "id" : "path_index" ,
        "enabled": False,  # info: "enabled" : False,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Path index (WO-MIG-42): path and kind for Pacific, Website, Library, and Android. No file contents.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{PACIFIC}/System/PathIndex/scripts/path_index.py\"",  # info: "command"
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "cwd": f"{PACIFIC}/System/PathIndex",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "weather_us_states",  # info: "id" : "weather_us_states" ,
        "enabled": os.environ.get("RR_US_STATES", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Fail-safe: ML2 weather_us_states → Database Weather/US-States/us_current.json (ML2 tree only).",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f'bash "{ML2}/scripts/run-local-bank.sh" --only weather_us_states',  # info: ML2 canonical
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: bank into Pacific Database
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "smart_devices_collect",  # info: "id" : "smart_devices_collect" ,
        "enabled": os.environ.get("RR_SMART_DEVICES", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "WiZ bulb + Tuya plug state -> Database Energy/Smart-Devices/{wiz,plugs,collector}_current.json.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Energy/Smart-Devices/scripts/smart_devices_collect.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Energy/Smart-Devices",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "weather_radar_zip",  # info: "id" : "weather_radar_zip" ,
        "enabled": os.environ.get("RR_RADAR_ZIP", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "ML2 vendor radar_zip.py → Database Weather/RadarZip/radar_archive.zip. Code under US-Mainland-Two only.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{ML2}/vendor/Weather/RadarZip/scripts/radar_zip.py\"",  # info: ML2 canonical
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "cwd": f"{ML2}/vendor/Weather/RadarZip",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: Database bank
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "country_location_pollers",  # info: "id" : "country_location_pollers" ,
        "enabled": False,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Fail-safe: ML2 weather_country_locations → Database Weather/CountryLocations/ (ML2 tree only).",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f'bash "{ML2}/scripts/run-local-bank.sh" --only weather_country_locations',  # info: ML2 canonical
        "timeout_sec": 300,  # info: "timeout_sec" : 300 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: bank into Pacific Database
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "stripe_poll",  # info: "id" : "stripe_poll" ,
        "enabled": os.environ.get("RR_STRIPE", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Stripe balance snapshot -> Database Website/stripe-snapshot.json. Gated off. No key does not call the API.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Website/scripts/stripe_poll.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Website",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "vercel_builds",  # info: "id" : "vercel_builds" ,
        "enabled": os.environ.get("RR_VERCEL_BUILDS", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Redacted Vercel failed-build records -> Database Logs/Website/. Gated off. No token does not call the API.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Website/scripts/vercel_builds.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Website",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "worklog_scan",  # info: "id" : "worklog_scan" ,
        "enabled": True,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Offline work auto-doc scan into Database/WORKLOG (Pacific Reports \u2014 WO-RPT-001).",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Reports/scripts/worklog_once.sh\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Reports/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "discord_poller",  # info: "id" : "discord_poller" ,
        "enabled": False,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Fail-safe: ML2 discord_poller (vendor Discord). OFF until token. Code under US-Mainland-Two only.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f'bash "{ML2}/scripts/run-local-bank.sh" --only discord_poller',  # info: ML2 canonical
        "timeout_sec": 120,  # info: "timeout_sec" : 120 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{ML2}",  # info: "cwd"
        "env": {"RR_DATABASE_ROOT": DATABASE},  # info: Database bank
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "communications_slack",  # info: "id" : "communications_slack" ,
        "enabled": os.environ.get("RR_SLACK", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Slack poller -> Database Communications/Slack/slack-last.json. No HTTP and no post until a token and sign-off exist.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Communications/Slack/scripts/poll.py\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Communications/Slack",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "service_supervisor",  # info: "id" : "service_supervisor" ,
        "enabled": True,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Mid-session auto-recovery (08-Ideas weather-relay-auto-recovery, approved 2026-09-29): respawn weather / council relay via their ensure scripts if dead; max 3 per 30 min, then BLOCKED. Dry run: supervise-services.sh --dry-run.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Automations/scripts/supervise-services.sh\"",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/Automations/scripts",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "system_python_drop",  # info: "id" : "system_python_drop" ,
        "enabled": os.environ.get("RR_PYTHON_DROP", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Allowlisted PythonDrop scripts only. Gate RR_PYTHON_DROP stays unset. Empty catalog spawns nothing.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"python3 \"{PACIFIC}/System/PythonDrop/scripts/python_drop.py\" tick",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "cwd": f"{PACIFIC}/System/PythonDrop",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "council_health",  # info: "id" : "council_health" ,
        "enabled": os.environ.get("RR_COUNCIL_HEALTH", "0") == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Council relay process, getMe, and 409 tail -> Database Communications/CouncilHealth/latest.json. Gated off. No send.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Communications/CouncilHealth/scripts/council_health.py\" --no-alert --no-probe",  # info: "command"
        "timeout_sec": 5,  # info: "timeout_sec" : 5 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/CouncilHealth",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "inbox_drain",  # info: "id" : "inbox_drain" ,
        "enabled": os.environ.get("RR_INBOX_DRAIN", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Copy quiet-mode Relay-Inbox rows into Database Communications/Inbox/feedback.jsonl. Gated off. No D1. No send.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Communications/Inbox/scripts/inbox.py\" drain",  # info: "command"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "cwd": f"{PACIFIC}/Communications/Inbox",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "public_health",  # info: "id" : "public_health" ,
        "enabled": os.environ.get("RR_PUBLIC_HEALTH", "0") == "1",  # info: "enabled" : os . environ . get ( "RR_PUBLIC_HEALTH" , "0" ) == "1",
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Check origin radio and 127.0.0.1:8787. Writes a status file. Does not start the origin. Send stays off unless RR_PUBLIC_HEALTH_SEND=1.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Communications/PublicHealth/scripts/public_health.py\"",  # info: "command"
        "timeout_sec": 40,  # info: "timeout_sec" : 40 ,
        "needs_internet": True,  # info: "needs_internet" : True ,
        "cwd": f"{PACIFIC}/Communications/PublicHealth",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "energy_river_car_drive",  # info: "id" : "energy_river_car_drive" ,
        "enabled": os.environ.get("RR_RIVER_CAR_DRIVE", "0") == "1",  # info: "enabled" : os . environ . get (,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "River 2 Pro car DC drive tick. Gated off. Skips until auto and a copy job. Does not switch power.",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"nice -n 10 python3 \"{PACIFIC}/Energy/River-Car/scripts/drive_automation.py\" --tick",  # info: "command"
        "timeout_sec": 30,  # info: "timeout_sec" : 30 ,
        "cwd": f"{PACIFIC}/Energy/River-Car",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "security_timelapse_hourly_compile",  # info: "id" : "security_timelapse_hourly_compile" ,
        "enabled": True,  # info: "enabled" : True,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Compile previous hour ch1 frames into hour_HH.mp4. Window 05:00-19:00 HST (hours 05-18).",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Security/Cameras/timelapse_hourly.sh\"",  # info: "command"
        "timeout_sec": 600,  # info: "timeout_sec" : 600 ,
        "cwd": f"{PACIFIC}/Security/Cameras",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
    {  # info: {
        # hourly work at :30 or later.
        "id": "security_timelapse_daily_render",  # info: "id" : "security_timelapse_daily_render" ,
        "enabled": True,  # info: "enabled" : True,
        "at_minute": 59,  # info: "at_minute" : 59 ,
        "at_second": 55,  # info: "at_second" : 55 ,
        "description": "Stitch hour_HH.mp4 chunks (05-18) into master_stitched_timelapse.mp4 (MP4 only, no GIF).",  # info: "description"
        "builtin": "",  # info: "builtin"
        "command": f"bash \"{PACIFIC}/Security/Cameras/timelapse_daily.sh\"",  # info: "command"
        "timeout_sec": 900,  # info: "timeout_sec" : 900 ,
        "cwd": f"{PACIFIC}/Security/Cameras",  # info: "cwd"
        "env": {},  # info: "env" : { } ,
    },  # info: } ,
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
