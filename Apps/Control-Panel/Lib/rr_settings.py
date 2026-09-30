"""rr_settings.py — single settings file for Root Monitor (was "RootRecord Control Panel"; Apps/Control-Panel/settings.json).

INFO — MUST HAVE (future agents), added 2026-09-29:
- ONE file holds every panel setting. Missing keys fall back to DEFAULTS; unknown keys are kept.
- NO SECRETS. Known URLs are name + URL only; save() refuses URLs that carry user:password@ or
  token/key/password query parameters. Never copy anything from Security/Cameras/store/CONNECTION.json.
- Camera toggles only decide what the PANEL shows. They never change collectors, grab jobs or the poller.
- risky_actions_enabled is False by default; turning it on is a sign-off item (see README).
"""
from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = Path(os.environ.get("RR_CONTROL_PANEL_SETTINGS", str(APP_DIR / "settings.json")))

DEFAULTS: dict = {
    "schema": 1,
    "refresh_sec": 5,
    "gsk_renderer": "cairo",
    "database_root": "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
    "pacific_root": "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server",
    "stale_after_sec": 900,
    "weather_zone": "Honolulu Metro",
    "log_lines": 40,
    "flm_port": 52625,
    "start_page": "energy",
    "camera_viewer_enabled": False,
    "camera_refresh_sec": 10,
    "camera_live_fallback": True,
    "camera_live_fallback_url": "http://127.0.0.1:8791/{still}",
    "cameras": {},
    "risky_actions_enabled": False,
    "risky_actions": [
        {"id": "poller_restart", "label": "Restart poller stack (rr-rootserver-poller.service)",
         "argv": ["systemctl", "--user", "restart", "rr-rootserver-poller.service"], "signed_off": False},
        {"id": "telegram_send", "label": "Telegram send (not wired — needs a signed-off command)",
         "argv": [], "signed_off": False},
        {"id": "voice_send", "label": "Voice playback / send (not wired — needs a signed-off command)",
         "argv": [], "signed_off": False},
        {"id": "rr_flags", "label": "Enable gated RR_* flags (not wired — needs sign-off + a poller restart)",
         "argv": [], "signed_off": False},
    ],
    "known_urls": [],
    "starlink_enabled": True,
    "starlink_poll_sec": 10,
    "ssh_mainland_alias": "",
    # AWS Fallback page (2026-09-29): dry-run by default; "write" is a sign-off item.
    "aws_fallback_mode": "dry-run",
    "aws_fallback_alias": "rr-aws-ip",
}

# Seeded 2026-09-29 by read-only discovery from poller-watch.py, rootserver_poller.py, cam_server.py,
# run-infer.sh / flm-warmup.sh, ollama-warmup.sh and the camera README. No credentials, tokens or secrets.
SEED_URLS = [
    {"name": "Poller status line (local /health)", "url": "http://127.0.0.1:8799/"},
    {"name": "Poller energy JSON (local)", "url": "http://127.0.0.1:8799/energy"},
    {"name": "Poller system-status JSON (local)", "url": "http://127.0.0.1:8799/system-status.json"},
    {"name": "RootServer public (tunnel)", "url": "https://rootserver.rootrecord.cloud/"},
    {"name": "A-EYES cameras (public, login)", "url": "https://rootserver.rootrecord.cloud/aeyes"},
    {"name": "A-EYES cameras (local, login)", "url": "http://127.0.0.1:8791/aeyes"},
    {"name": "Ollama models (local)", "url": "http://127.0.0.1:11434/api/tags"},
    {"name": "FLM / NPU models (local, on demand)", "url": "http://127.0.0.1:52625/v1/models"},
]

_SECRETISH = re.compile(r"(//[^/@\s]+:[^/@\s]*@)|([?&](token|key|apikey|api_key|password|pass|secret|sig)=)", re.I)


def url_is_clean(url: str) -> bool:
    return bool(re.match(r"^(https?|file)://", url or "")) and not _SECRETISH.search(url)


def load(path: Path = SETTINGS_FILE) -> dict:
    s = copy.deepcopy(DEFAULTS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            s.update(data)
    except Exception:
        pass
    if not s.get("known_urls"):
        s["known_urls"] = copy.deepcopy(SEED_URLS)
    s["known_urls"] = [u for u in s["known_urls"] if isinstance(u, dict) and url_is_clean(u.get("url", ""))]
    s["refresh_sec"] = max(2, int(s.get("refresh_sec") or 5))
    s["camera_refresh_sec"] = max(5, int(s.get("camera_refresh_sec") or 10))
    return s


def save(s: dict, path: Path = SETTINGS_FILE) -> None:
    out = copy.deepcopy(s)
    out["known_urls"] = [u for u in out.get("known_urls", []) if url_is_clean(u.get("url", ""))]
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".settings.", suffix=".tmp", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
