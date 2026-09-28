#!/usr/bin/env python3
"""RootRecord automations poller — tunnel when online, local jobs always.

Internet gate: TCP check to 1.1.1.1/8.8.8.8 before tunnel/GitHub/Telegram.
If offline at boot, tunnel is deferred; ensure_tunnel_online retries every minute.
BLE / Ollama / HTTP local continue regardless.
"""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import threading
import time
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent.parent  # repo root (Automations/../)
SKILLS_ROOT = REPO_ROOT  # alias: domain folders live at repo root
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT))
import jobs as jobmod  # noqa: E402

INTERVAL_FALLBACK = float(os.environ.get("POLLER_INTERVAL_SEC", "5"))
HOST = os.environ.get("POLLER_BIND", "127.0.0.1")
PORT = int(os.environ.get("POLLER_PORT", "8799"))
SYSTEM_STATUS_JSON = Path("/home/rootrecord/Database/SYSTEM/status/system-status.json")
ENERGY_ROOT = Path(os.environ.get("ENERGY_ROOT", "/home/rootrecord/Database/ENERGY"))
HOSTNAME = os.environ.get("POLLER_PUBLIC_HOST", "rootserver.rootrecord.cloud")
TOKEN_FILE = Path(os.environ.get("CLOUDFLARED_TOKEN_FILE", str(Path.home() / ".cloudflared" / "rootserver.token")))
CLOUDFLARED_BIN = os.environ.get(
    "CLOUDFLARED_BIN",
    str(REPO_ROOT / "Communications" / "network" / "cloudflare" / "bin" / "cloudflared"),
)
ENABLE_TUNNEL = os.environ.get("POLLER_ENABLE_TUNNEL", "1") != "0"
TUNNEL_READY_TIMEOUT_SEC = float(os.environ.get("POLLER_TUNNEL_READY_TIMEOUT_SEC", "45"))

_latest = "starting"
_lock = threading.Lock()
_stop = threading.Event()
_tunnel_ready = threading.Event()
_tunnel_proc: subprocess.Popen | None = None
_internet_ok = False
_internet_last_log = 0.0
_tunnel_start_attempts = 0

# NOTE: Full body restored from artifacts - see commit message.
# If this file appears truncated, replace from local artifacts/rootserver_poller.py
