"""rr_settings.py — single settings file for Root Monitor.

The live file is Database System/control-panel/settings.json (gitignored).
Apps/Control-Panel/settings.json is only the seed copied across when the live file is missing.

INFO — MUST HAVE (future agents), added 2026-09-29:
- ONE file holds every panel setting. Missing keys fall back to DEFAULTS; unknown keys are kept.
- NO SECRETS. Known URLs are name + URL only; save() refuses URLs that carry user:password@ or
  token/key/password query parameters. Never copy anything from Security/Cameras/store/CONNECTION.json.
- Camera toggles only decide what the PANEL shows. They never change collectors, grab jobs or the poller.
- risky_actions_enabled is False by default; turning it on is a sign-off item (see README).
"""
from __future__ import annotations  # info: from __future__ import annotations

import copy  # info: import copy
import json  # info: import json
import os  # info: import os
import re  # info: import re
import tempfile  # info: import tempfile
from pathlib import Path  # info: from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent  # info: set APP_DIR
DATABASE_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE_ROOT
SEED_FILE = APP_DIR / "settings.json"  # info: set SEED_FILE
SETTINGS_FILE = Path(os.environ.get(  # info: set SETTINGS_FILE
    "RR_CONTROL_PANEL_SETTINGS",
    str(DATABASE_ROOT / "System/control-panel/settings.json"),
))

# ====================================================
# SECTION: DEFAULTS
# What it does: Set DEFAULTS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
DEFAULTS: dict = {  # info: set DEFAULTS
    "schema": 1,  # info: "schema" : 1 ,
    "refresh_sec": 5,  # info: "refresh_sec" : 5 ,
    "gsk_renderer": "cairo",  # info: "gsk_renderer" : "cairo" ,
    "database_root": "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: "database_root" : "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database" ,
    "pacific_root": "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server",  # info: "pacific_root" : "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server" ,
    "stale_after_sec": 900,  # info: "stale_after_sec" : 900 ,
    "weather_zone": "Big Island",  # info: "weather_zone" : "Big Island" ,
    "log_lines": 40,  # info: "log_lines" : 40 ,
    "flm_port": 52625,  # info: "flm_port" : 52625 ,
    "start_page": "energy",  # info: "start_page" : "energy" ,
    "camera_viewer_enabled": False,  # info: "camera_viewer_enabled" : False ,
    "camera_refresh_sec": 10,  # info: "camera_refresh_sec" : 10 ,
    "camera_live_fallback": True,  # info: "camera_live_fallback" : True ,
    "camera_live_fallback_url": "http://127.0.0.1:8791/{still}",  # info: "camera_live_fallback_url" : "http://127.0.0.1:8791/{still}" ,
    "cameras": {},  # info: "cameras" : { } ,
    "risky_actions_enabled": False,  # info: "risky_actions_enabled" : False ,
    "risky_actions": [  # info: "risky_actions" : [
        {"id": "poller_restart", "label": "Restart poller stack (rr-rootserver-poller.service)",  # info: { "id" : "poller_restart" , "label" : "Restart poller stack (rr-rootserver-poller.service)"
         "argv": ["systemctl", "--user", "restart", "rr-rootserver-poller.service"], "signed_off": False},  # info: "argv" : [ "systemctl" , "--user" , "restart"
        {"id": "telegram_send", "label": "Telegram send (not wired — needs a signed-off command)",  # info: { "id" : "telegram_send" , "label" : "Telegram send (not wired — needs a signed-off command)"
         "argv": [], "signed_off": False},  # info: "argv" : [ ] , "signed_off" : False
        {"id": "voice_send", "label": "Voice playback / send (not wired — needs a signed-off command)",  # info: { "id" : "voice_send" , "label" : "Voice playback / send (not wired — needs a signed-off command)"
         "argv": [], "signed_off": False},  # info: "argv" : [ ] , "signed_off" : False
        {"id": "rr_flags", "label": "Enable gated RR_* flags (not wired — needs sign-off + a poller restart)",  # info: { "id" : "rr_flags" , "label" : "Enable gated RR_* flags (not wired — needs sign-off + a poller restart)"
         "argv": [], "signed_off": False},  # info: "argv" : [ ] , "signed_off" : False
    ],  # info: ] ,
    "known_urls": [],  # info: "known_urls" : [ ] ,
    "starlink_enabled": True,  # info: "starlink_enabled" : True ,
    "starlink_poll_sec": 10,  # info: "starlink_poll_sec" : 10 ,
    "ssh_mainland_alias": "",  # info: "ssh_mainland_alias" : "" ,
    # AWS Fallback page (2026-09-29): dry-run by default; "write" is a sign-off item.
    "aws_fallback_mode": "dry-run",  # info: "aws_fallback_mode" : "dry-run" ,
    "aws_fallback_alias": "rr-aws-ip",  # info: "aws_fallback_alias" : "rr-aws-ip" ,
}  # info: }

# Seeded 2026-09-29 by read-only discovery from poller-watch.py, rootserver_poller.py, cam_server.py,
# run-infer.sh / flm-warmup.sh, ollama-warmup.sh and the camera README. No credentials, tokens or secrets.
# ====================================================
# SECTION: SEED_URLS
# What it does: Set SEED_URLS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
SEED_URLS = [  # info: set SEED_URLS
    {"name": "Poller status line (local /health)", "url": "http://127.0.0.1:8799/"},  # info: { "name" : "Poller status line (local /health)" , "url" : "http://127.0.0.1:8799/"
    {"name": "Poller energy JSON (local)", "url": "http://127.0.0.1:8799/energy"},  # info: { "name" : "Poller energy JSON (local)" , "url" : "http://127.0.0.1:8799/energy"
    {"name": "Poller system-status JSON (local)", "url": "http://127.0.0.1:8799/system-status.json"},  # info: { "name" : "Poller system-status JSON (local)" , "url" : "http://127.0.0.1:8799/system-status.json"
    {"name": "RootServer public (tunnel)", "url": "https://rootserver.rootrecord.cloud/"},  # info: { "name" : "RootServer public (tunnel)" , "url" : "https://rootserver.rootrecord.cloud/"
    {"name": "A-EYES cameras (public, login)", "url": "https://rootserver.rootrecord.cloud/aeyes"},  # info: { "name" : "A-EYES cameras (public, login)" , "url" : "https://rootserver.rootrecord.cloud/aeyes"
    {"name": "A-EYES cameras (local, login)", "url": "http://127.0.0.1:8791/aeyes"},  # info: { "name" : "A-EYES cameras (local, login)" , "url" : "http://127.0.0.1:8791/aeyes"
    {"name": "Ollama models (local)", "url": "http://127.0.0.1:11434/api/tags"},  # info: { "name" : "Ollama models (local)" , "url" : "http://127.0.0.1:11434/api/tags"
    {"name": "FLM / NPU models (local, on demand)", "url": "http://127.0.0.1:52625/v1/models"},  # info: { "name" : "FLM / NPU models (local, on demand)" , "url" : "http://127.0.0.1:52625/v1/models"
]  # info: ]

_SECRETISH = re.compile(r"(//[^/@\s]+:[^/@\s]*@)|([?&](token|key|apikey|api_key|password|pass|secret|sig)=)", re.I)  # info: set _SECRETISH


# ====================================================
# SECTION: function url_is_clean
# What it does: url is clean.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def url_is_clean(url: str) -> bool:  # info: def url_is_clean
    return bool(re.match(r"^(https?|file)://", url or "")) and not _SECRETISH.search(url)  # info: return bool ( re . match ( r"^(https?|file)://"


# ====================================================
# SECTION: function load
# What it does: load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load(path: Path = SETTINGS_FILE) -> dict:  # info: def load
    if path == SETTINGS_FILE and not path.exists() and SEED_FILE.is_file():  # info: if path == SETTINGS_FILE and not path . exists ( ) and SEED_FILE . is_file ( ) :
        path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents = True , exist_ok = True )
        path.write_text(SEED_FILE.read_text(encoding="utf-8"), encoding="utf-8")  # info: path . write_text ( SEED_FILE . read_text ( encoding = "utf-8" ) , encoding = "utf-8" )
    s = copy.deepcopy(DEFAULTS)  # info: set s
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
        if isinstance(data, dict):  # info: if isinstance ( data , dict ) :
            s.update(data)  # info: s . update ( data )
    except Exception:  # info: except Exception :
        pass  # info: pass
    if not s.get("known_urls"):  # info: if not s . get ( "known_urls" )
        s["known_urls"] = copy.deepcopy(SEED_URLS)  # info: s [ "known_urls" ] = copy . deepcopy
    s["known_urls"] = [u for u in s["known_urls"] if isinstance(u, dict) and url_is_clean(u.get("url", ""))]  # info: s [ "known_urls" ] = [ u for
    s["refresh_sec"] = max(2, int(s.get("refresh_sec") or 5))  # info: s [ "refresh_sec" ] = max ( 2
    s["camera_refresh_sec"] = max(5, int(s.get("camera_refresh_sec") or 10))  # info: s [ "camera_refresh_sec" ] = max ( 5
    return s  # info: return s


# ====================================================
# SECTION: function save
# What it does: save.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save(s: dict, path: Path = SETTINGS_FILE) -> None:  # info: def save
    out = copy.deepcopy(s)  # info: set out
    out["known_urls"] = [u for u in out.get("known_urls", []) if url_is_clean(u.get("url", ""))]  # info: out [ "known_urls" ] = [ u for
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    fd, tmp = tempfile.mkstemp(prefix=".settings.", suffix=".tmp", dir=str(path.parent))  # info: fd , tmp = tempfile . mkstemp (
    with os.fdopen(fd, "w", encoding="utf-8") as f:  # info: with os . fdopen ( fd , "w"
        json.dump(out, f, indent=2, ensure_ascii=False)  # info: json . dump ( out , f ,
        f.write("\n")  # info: f . write ( "\n" )
    os.replace(tmp, path)  # info: os . replace ( tmp , path )
