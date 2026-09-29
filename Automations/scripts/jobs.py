# ==============================================================================
# # INFO — MUST HAVE (future agents / operators)
# ------------------------------------------------------------------------------
# Ctrl-C in the poller window / `rootserver-poller stop` MUST kill the whole stack
# (poller + cloudflared + systemd unit). Never "window only".
# Data intake → /home/rootrecord/Database/intake/
# Baks/logs  → /home/rootrecord/Database/GITHUB/
# GitHub set: skills + website + mainland + library (repos.conf).
# Pacific .gitignore excludes us-mainland-server/ (own repo). No rclone / aws-sync.
# Inference: prefer FLM llama3.2:3b on NPU (:52625); Ollama dolphin lanes = CPU fallback.
# Telegram council-relay via coms/telegram (one getUpdates). Plumbing single-flight.
#
# Deploy format (standing, all future builds):
#   push to GitHub → github_sync_all merge → schedule-stack-reload full stop/start + window.
#   Do not suggest parallel pollers or default manual restart after ordinary pushes.
#
# Internet gate:
#   needs_internet=True jobs skip while offline; tunnel deferred; ensure_tunnel_online each minute.
#   Local jobs (BLE, Ollama, FLM, heartbeat, worklog) always run.
#
# File layout (standing): keep SECTION banners + TEMPLATE blocks.
# Repo domains: Automations/, Communications/, Weather/, Energy/, … at skills root.
# Energy Phase 1 read path imported under Energy/scripts/read (2026-09-28).
# Residual skill paths remain for: a-eyes, github, plumbing, telegram, energy actions.
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

DEFAULTS = {
    "enabled": False,
    "timeout_sec": 120,
    "cwd": "",
    "env": {},
}

ECOFLOW_DUAL_READ = (
    "flock -w 90 /tmp/ecoflow-ble.lock bash -c '"
    "ok=0; "
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/scripts/read/delta2-read.sh && ok=1 || true; "
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/scripts/read/river2pro-read.sh && ok=1 || true; "
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
        "process": "/home/rootrecord/.ollama/skills/Automations/scripts/rootserver_poller.py",
        "terminal": "RootRecord poller — rootserver",
        "watch": "/home/rootrecord/.ollama/skills/Automations/scripts/poller/poller-watch.py",
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
        "cloudflared_bin": "/home/rootrecord/.ollama/skills/Communications/network/cloudflare/bin/cloudflared",
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
        "description": "Ensure remotes for skills + website + mainland + library (repos.conf).",
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/github/scripts/setup-all-remotes.sh",
        "timeout_sec": 180,
        "needs_internet": True,
        "cwd": "/home/rootrecord/.ollama/skills/github",
        "env": {},
    },
    {
        "id": "ollama_warmup",
        "enabled": True,
        "priority": 3,
        "description": "Ensure ollama serve is up (CPU fallback lanes).",
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/plumbing/scripts/ollama-warmup.sh",
        "timeout_sec": 120,
        "cwd": "/home/rootrecord",
        "env": {},
    },
    {
        "id": "flm_npu_warmup",
        "enabled": True,
        "priority": 4,
        "description": "Start FastFlowLM llama3.2:3b on XDNA NPU :52625 if binary present.",
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/plumbing/scripts/flm-warmup.sh",
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
        "command": "bash /home/rootrecord/.ollama/skills/coms/telegram/scripts/ensure-relay.sh",
        "timeout_sec": 30,
        "needs_internet": True,
        "cwd": "/home/rootrecord/.ollama/skills/coms/telegram",
        "env": {},
    },
    {
        "id": "a_eyes_cam_server",
        "enabled": True,
        "priority": 6,
        "description": "Ensure a-eyes cam server (127.0.0.1:8791) is running.",
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/a-eyes/scripts/ensure_cam_server.sh",
        "timeout_sec": 30,
        "cwd": "/home/rootrecord/.ollama/skills/a-eyes",
        "env": {},
    },
    {
        "id": "a_eyes_timelapse_catchup",
        "enabled": True,
        "priority": 7,
        "description": "Compile any completed hour missing a chunk today + stitch master MP4 if past 19:00 HST (covers late boot/downtime).",
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/a-eyes/scripts/timelapse_catchup.sh",
        "timeout_sec": 600,
        "cwd": "/home/rootrecord/.ollama/skills/a-eyes",
        "env": {},
    },
    {
        "id": "weather_poller",
        "enabled": True,
        "priority": 8,
        "description": "Ensure the weather/ scheduler daemon is running.",
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/Weather/scripts/ensure-weather-poller.sh",
        "timeout_sec": 30,
        "needs_internet": False,
        "cwd": "/home/rootrecord/.ollama/skills/Weather",
        "env": {},
    },
    {
        "id": "network_globe_hawaii",
        "enabled": True,
        "priority": 9,
        "description": "Ensure the live Hawaii Network Globe SSH collector is running.",
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/Communications/network/scripts/ensure-network-globe-hawaii.sh",
        "timeout_sec": 30,
        "needs_internet": False,
        "cwd": "/home/rootrecord/.ollama/skills/coms/ssh/local-data-globe",
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
        "cwd": "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy",
        "env": {"ENERGY_EFLIB_PATH": "/home/rootrecord/.ollama/skills/energy/lib/vendor"},
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
        "command": "bash /home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/scripts/read/leapfrog-read.sh",
        "timeout_sec": 180,
        "cwd": "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy",
        "env": {"ENERGY_EFLIB_PATH": "/home/rootrecord/.ollama/skills/energy/lib/vendor"},
    },
    {
        "id": "sys_stats_cycle",
        "enabled": True,
        "description": "Host CPU/load/mem → Database/SYSTEM.",
        "interval_sec": 5,
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/system-stats/scripts/sys-sample.sh",
        "timeout_sec": 60,
        "cwd": "/home/rootrecord/.ollama/skills/system-stats",
        "env": {},
    },
    {
        "id": "github_sync_all",
        "enabled": True,
        "description": "Push skills + website + mainland + library.",
        "interval_sec": 300,
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/github/scripts/sync-all.sh",
        "timeout_sec": 300,
        "needs_internet": True,
        "cwd": "/home/rootrecord/.ollama/skills/github",
        "env": {},
    },
    {
        "id": "worklog_scan",
        "enabled": True,
        "description": "Offline work auto-doc scan into Database/WORKLOG.",
        "interval_sec": 90,
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/reports/scripts/worklog_once.sh",
        "timeout_sec": 180,
        "cwd": "/home/rootrecord/.ollama/skills/reports/scripts",
        "env": {},
    },
    {
        "id": "a_eyes_frame_grab",
        "enabled": True,
        "description": "Grab ch1-4 stills to Database/A-EYES/frames/.",
        "interval_sec": 1,
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/a-eyes/scripts/grab_all.sh",
        "timeout_sec": 120,
        "cwd": "/home/rootrecord/.ollama/skills/a-eyes",
        "env": {},
    },
]

EVERY_MINUTE = [
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
        "id": "a_eyes_timelapse_hourly_compile",
        "enabled": True,
        "description": "Compile previous hour ch1 frames into hour_HH.mp4. Window 05:00-19:00 HST (hours 05-18).",
        "only_at_hours": [],
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/a-eyes/scripts/timelapse_hourly.sh",
        "timeout_sec": 600,
        "cwd": "/home/rootrecord/.ollama/skills/a-eyes",
        "env": {},
    },
]

ON_AT = [
    {
        "id": "a_eyes_timelapse_daily_render",
        "enabled": True,
        "description": "Stitch hour_HH.mp4 chunks (05-18) into master_stitched_timelapse.mp4 (MP4 only, no GIF).",
        "at_times": ["19:01"],
        "builtin": "",
        "command": "bash /home/rootrecord/.ollama/skills/a-eyes/scripts/timelapse_daily.sh",
        "timeout_sec": 900,
        "cwd": "/home/rootrecord/.ollama/skills/a-eyes",
        "env": {},
    },
]

ECOFLOW_ACTIONS = "/home/rootrecord/.ollama/skills/energy/scripts/actions"
ECOFLOW_LOCK = "/tmp/ecoflow-ble.lock"


def ecoflow_command(script: str) -> str:
    return f"flock -w 60 {ECOFLOW_LOCK} bash {ECOFLOW_ACTIONS}/{script}"


TOGGLES = []
READS = [
    {"id": "delta2_read", "script": "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/scripts/read/delta2-read.sh"},
    {"id": "river2pro_read", "script": "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/scripts/read/river2pro-read.sh"},
]
