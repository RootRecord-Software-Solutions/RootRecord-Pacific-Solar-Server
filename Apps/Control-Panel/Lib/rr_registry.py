"""rr_registry.py — registry of every RootRecord setting the Control Panel can show (and, where allowed, edit).

INFO — MUST HAVE (future agents), added 2026-09-29 (control-panel-settings pass):
- For each setting: file, key, type, secret?, service that uses it, restart needed, editable? (+ why not).
- Secret VALUES stay inside this process: Setting.display is always masked for secrets ("set (len N)" / "empty").
  secret_values() exists ONLY for the leak tests / screenshot guard; never print its result.
- Read-only by design: NetworkManager, /etc (system units), cloudflare status snapshots, jobs.py (code),
  code constants (weather retention windows), GitHub CLI files, model configs, and ANY secret inside a
  git-tracked file (flagged as a security item instead of editable).
- Files are parsed lazily per page and cached by mtime. Env-var usage is scanned from scripts on demand.
- Never reads the private archive or the models-drafts folder.
"""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
from dataclasses import dataclass, field  # info: from dataclasses import dataclass , field
from pathlib import Path  # info: from pathlib import Path

import rr_config_io as io  # info: import rr_config_io as io

ECO = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ECO
PAC = ECO / "1 - Servers/1 - RootRecord-Pacific-Solar-Server"  # info: set PAC
DBR = ECO / "2 - RootRecord-Database"  # info: set DBR
LIB = ECO / "5 - RootRecord-Library"  # info: set LIB
HOME = Path.home()  # info: set HOME
FORBIDDEN = (str(HOME / "Desktop/old txt"), str(ECO / "I'll sort these models tomorrow"))  # info: set FORBIDDEN
REPOS = (PAC, DBR, LIB)  # info: set REPOS

PAGES = [("network", "Network"), ("messaging", "Messaging"), ("environment", "Environment (.env)"),  # info: set PAGES
         ("flags", "Feature Flags (RR_*)"), ("services", "Services / Poller"), ("weather", "Weather"),  # info: call (
         ("voice", "Voice"), ("ai", "AI / NPU"), ("cameras", "Cameras"), ("panel", "Panel")]  # info: call (

POLLER = "rr-rootserver-poller.service"  # info: set POLLER
R_POLLER = f"takes effect after {POLLER} restart"  # info: set R_POLLER
R_RELAY = "takes effect after council relay restart (poller council_relay / ensure-relay.sh)"  # info: set R_RELAY
R_EACH = "read at each job run (no restart)"  # info: set R_EACH
R_UNIT = "takes effect after systemctl --user daemon-reload + restart of {unit}"  # info: set R_UNIT


# ====================================================
# SECTION: class FileSpec
# What it does: FileSpec.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class FileSpec:  # info: class FileSpec
    id: str  # info: set id
    path: Path  # info: set path
    fmt: str  # info: set fmt
    page: str  # info: set page
    service: str  # info: set service
    restart: str  # info: set restart
    secret_file: bool = False  # info: set secret_file
    read_only: str = ""               # non-empty = reason
    columns: list = field(default_factory=list)  # info: set columns
    key_pages: list = field(default_factory=list)   # [(regex, page)]
    not_secret: tuple = ()            # key regexes that look secret but are not (e.g. token_env NAMES)
    ro_keys: tuple = ()               # key regexes shown read-only
    kinds: tuple = ()                 # [(regex, kind)]
    note: str = ""  # info: set note


# ====================================================
# SECTION: class Setting
# What it does: Setting.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class Setting:  # info: class Setting
    page: str  # info: set page
    file_id: str  # info: set file_id
    path: str  # info: set path
    key: str  # info: set key
    kind: str  # info: set kind
    secret: bool  # info: set secret
    service: str  # info: set service
    restart: str  # info: set restart
    editable: bool  # info: set editable
    ro_reason: str  # info: set ro_reason
    display: str  # info: set display
    dup: bool = False  # info: set dup
    _value: object = None   # private — never render for secrets

    def value_text(self) -> str:  # info: def value_text
        return "" if self.secret else ("" if self._value is None else str(self._value))  # info: return "" if self . secret else (


# ====================================================
# SECTION: function _unit
# What it does:  unit.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _unit(name, page="services", **kw):  # info: def _unit
    return FileSpec(f"unit:{name}", HOME / ".config/systemd/user" / name, "ini", page, name,  # info: return FileSpec ( f" unit: { name }
                    R_UNIT.format(unit=name), **kw)  # info: R_UNIT . format ( unit = name )


# ====================================================
# SECTION: FILES
# What it does: Set FILES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
FILES: list[FileSpec] = [  # info: set FILES
    # ---- Network
    FileSpec("cf-status", PAC / "Communications/network/cloudflare/config/cf-status.json", "json", "network", "cloudflare tunnel (docs/status)",  # info: call FileSpec
             "status snapshot", read_only="status snapshot written by tooling"),  # info: "status snapshot" , read_only = "status snapshot written by tooling" ) ,
    FileSpec("cf-blocker", PAC / "Communications/network/cloudflare/config/cf-blocker.json", "json", "network", "cloudflare tunnel (docs/status)",  # info: call FileSpec
             "status snapshot", read_only="findings snapshot written by tooling"),  # info: "status snapshot" , read_only = "findings snapshot written by tooling" ) ,
    FileSpec("tunnel-token", HOME / ".cloudflared/rootserver.token", "raw", "network", "cloudflared (poller tunnel_start)", R_POLLER,  # info: call FileSpec
             secret_file=True),  # info: set secret_file
    # ---- Messaging
    FileSpec("relay.conf", PAC / "Communications/telegram/config/relay.conf", "env", "messaging", "council-relay.py", R_RELAY,  # info: call FileSpec
             kinds=((r"^(ENABLED)$", "bool01"), (r"^(POLL_TIMEOUT|MAX_TEXT)$", "int"))),  # info: set kinds
    FileSpec("voices.conf", PAC / "Communications/telegram/config/voices.conf", "tsv", "messaging", "council-relay.py", R_RELAY,  # info: call FileSpec
             columns=["id", "enabled", "telegram_username", "token_env", "ollama_model", "fallback_model"],  # info: set columns
             not_secret=(r"\.token_env$",), kinds=((r"\.enabled$", "bool01"),)),  # info: set not_secret
    # ---- Environment
    FileSpec("master-key.env", HOME / "master/master-key.env", "env", "environment", "poller stack, relay, Energy, GitHub sync, globe relay",  # info: call FileSpec
             "takes effect after restart of the services that source it (poller stack, relay, BLE)", secret_file=True,  # info: "takes effect after restart of the services that source it (poller stack, relay, BLE)" , secret_file = True ,
             key_pages=[(r"^(TELEGRAM_|RR_DATAPACK_)", "messaging"), (r"^(ROOTSERVER_TUNNEL|CLOUDFLARE_|API_TOKEN|ACCESS_KEY_R2|S3_API)", "network"),  # info: set key_pages
                        (r"^AEYES_", "cameras")]),  # info: call (
    FileSpec("gh-hosts", HOME / ".config/gh/hosts.yml", "yaml", "environment", "GitHub CLI (gh)", "gh reads it per call",  # info: call FileSpec
             read_only="managed by `gh auth` — not edited here (oauth_token is detected by key name and masked)"),  # info: set read_only
    FileSpec("gh-config", HOME / ".config/gh/config.yml", "yaml", "environment", "GitHub CLI (gh)", "gh reads it per call",  # info: call FileSpec
             read_only="managed by `gh config`"),  # info: set read_only
    FileSpec("repos.conf", PAC / "Github/scripts/repos.conf", "tsv", "services", "github_sync_all / github_autopush", R_EACH,  # info: call FileSpec
             columns=["id", "enabled", "mode", "local_path", "github_slug", "remote_name"], kinds=((r"\.enabled$", "bool01"),)),  # info: set columns
    # ---- Services / Poller
    _unit(POLLER, ro_keys=(r"\.(ExecStart|WorkingDirectory|KillMode|Type|After|WantedBy|Description)$",),  # info: call _unit
          key_pages=[(r"Environment\.POLLER_(BIND|PORT|PUBLIC_HOST)$", "network")],  # info: set key_pages
          kinds=((r"POLLER_PORT$", "port"), (r"RestartSec$|Timeout\w*Sec$", "int"), (r"POLLER_PUBLIC_HOST$|POLLER_BIND$", "host"))),  # info: set kinds
    FileSpec("unit:poller-logging", HOME / ".config/systemd/user/rr-rootserver-poller.service.d/logging.conf", "ini", "services",  # info: call FileSpec
             POLLER, R_UNIT.format(unit=POLLER)),  # info: POLLER , R_UNIT . format ( unit =
    _unit("ava-ecoflow-ble.service", ro_keys=(r"\.(ExecStart|KillMode|Type|After|Wants|WantedBy|Description)$",),  # info: call _unit
          kinds=((r"RestartSec$|Timeout\w*Sec$", "int"),)),  # info: set kinds
    _unit("network-globe-hawaii.service", page="network", ro_keys=(r"\.(ExecStart|WorkingDirectory|KillMode|Type|After|Wants|WantedBy|Description)$",),  # info: call _unit
          kinds=((r"Timeout\w*Sec$", "int"),)),  # info: set kinds
    FileSpec("unit:ollama", Path("/etc/systemd/system/ollama.service"), "ini", "ai", "ollama.service (system)",  # info: call FileSpec
             "systemctl daemon-reload + restart ollama (root)", read_only="system unit in /etc — needs sudo (sign-off)"),  # info: "systemctl daemon-reload + restart ollama (root)" , read_only = "system unit in /etc — needs sudo (sign-off)" 
    FileSpec("devices.conf", PAC / "Energy/config/devices.conf", "ini", "services", "EcoFlow readers + BLE owner (ava-ecoflow-ble.service)",  # info: call FileSpec
             "read at each EcoFlow job run; BLE owner after ava-ecoflow-ble.service restart",  # info: "read at each EcoFlow job run; BLE owner after ava-ecoflow-ble.service restart" ,
             kinds=((r"\.(prefer_api|poll_enabled)$", "bool01"), (r"_interval_s$", "int"))),  # info: set kinds
    FileSpec("jobs.py", PAC / "Automations/scripts/jobs.py", "code-jobs", "services", POLLER, R_POLLER,  # info: call FileSpec
             read_only="Python code — job table shown read-only; edit jobs.py offline"),  # info: set read_only
    # ---- Weather (canonical YAML under ML2 vendor — Pacific has no Weather/config copy)
    *[FileSpec(f"weather:{n}", ECO / "1 - Servers/3 - RootRecord-US-Mainland-Two/vendor/Weather/config" / n, "yaml", "weather", "ML2 vendor/Weather config (Hawai'i fetch)",  # info: ML2 canonical
               "edit on ML2 desk tree; remote host picks up on deploy",  # info: deploy note
               kinds=((r"seconds$|_s$|_sec$", "int"),))  # info: set kinds
      for n in ("hosts.yaml", "tiers.yaml", "resources.yaml", "counties.yaml", "report_counties.yaml", "text_cleaning.yaml")],  # info: for n in ( "hosts.yaml" , "tiers.yaml" ,
    FileSpec("weather-retention", Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/3 - RootRecord-US-Mainland-Two/vendor/Weather/scripts/weather-retention.py"), "code-const", "weather", "weather_retention job (gated OFF)",  # info: call FileSpec
             R_EACH, read_only="Python constants (KEEP_*_DAYS) — code change + review of a dry run"),  # info: R_EACH , read_only = "Python constants (KEEP_*_DAYS) — code change + review of a dry run" ) ,
    # ---- AI / NPU
    FileSpec("specialist-routes", PAC / "System/config/specialist-routes.json", "json", "ai", "route-specialist.py / run-infer.sh",  # info: call FileSpec
             R_EACH, kinds=((r"^(threshold|saturation)$", "float"), (r"\.keywords\.", "int"), (r"^version$", "int")),  # info: R_EACH , kinds = ( ( r"^(threshold|saturation)$" ,
             not_secret=(r"\.keywords\.",)),   # routing keyword weights such as "token*" / "password*" — not credentials
    FileSpec("kokoro-config", DBR / "AI/Kokoro/Kokoro-82M/config.json", "json", "voice", "voice_generate.py (Kokoro-82M)",  # info: call FileSpec
             "model config", read_only="model file config — not a setting (never edited; no model is loaded)"),  # info: "model config" , read_only = "model file config — not a setting (never edited; no model is loaded)" ) ,
    # ---- Cameras
    FileSpec("CONNECTION.json", PAC / "Security/Cameras/store/CONNECTION.json", "json", "cameras", "grab_frame.py / cam_server.py",  # info: call FileSpec
             "read at each grab; cam_server after restart", secret_file=True,  # info: "read at each grab; cam_server after restart" , secret_file = True ,
             kinds=((r"crop_right_pct$", "float"),)),  # info: set kinds
    # ---- Panel
    FileSpec("panel-settings", DBR / "System/control-panel/settings.json", "json", "panel", "Root Monitor (rr_control_panel.py)", "applies on Save / next start",  # info: call FileSpec
             note="edited on the Panel page (dedicated controls)", read_only="edit with the Panel page controls"),  # info: set note
]  # info: ]

# env vars from scripts -> page
# ====================================================
# SECTION: ENV_PAGE_RULES
# What it does: Set ENV_PAGE_RULES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ENV_PAGE_RULES = [  # info: set ENV_PAGE_RULES
    (r"^RR_", "flags"),  # info: call (
    (r"^(POLLER_(BIND|PORT|PUBLIC_HOST|LOCAL|ENABLE_TUNNEL|TUNNEL_\w+)|CLOUDFLARED_\w+|AWS_\w+|SSH_\w+|ORIGIN_\w+|SOURCE_\w+|PACKET_WINDOW_MS|POLL_MS)$", "network"),  # info: call (
    (r"^(TELEGRAM_\w+|AVA_TELEGRAM\w*|DESK_LIVE_FILE)$", "messaging"),  # info: call (
    (r"^(FLM_\w+|OLLAMA_\w+|CALLER|MEM0|SPEC_LOG|FAKE|HOOKTEST_PORT)$", "ai"),  # info: call (
    (r"^(KOKORO_\w+)$", "voice"),  # info: call (
    (r"^(WEATHER_\w+)$", "weather"),  # info: call (
    (r"^(A_EYES_\w+|AEYES_\w+)$", "cameras"),  # info: call (
    (r"^(POLLER_\w+|ENERGY_\w+|ECOFLOW_\w+|AVA_ECOFLOW\w*|ROOTRECORD_\w+|SYSTEM_STATUS_JSON|STACK_RELOAD_LOG|OPEN_POLLER_WINDOW|BAK_ROOT|SOLAR_GATE_STATE|REPOS_CONF|MAX_FILE_MB|INTAKE_ROOT|DATABASE_ROOT)$", "services"),  # info: call (
]  # info: ]
FLAG_PAGE_VOICE = r"^RR_(VOICE|ESPEAK|KOKORO|WHISPER)"  # info: set FLAG_PAGE_VOICE
FLAG_PAGE_AI = r"^RR_(SPEC|INFER|ROUTE|ALLOW_IGPU|PROMPT|INFERENCE_LOCK|PLUMBING|CALLER|AI_REPORT)"  # info: set FLAG_PAGE_AI
FLAGS_DROPIN = HOME / ".config/systemd/user/rr-rootserver-poller.service.d/rr-flags.conf"  # info: set FLAGS_DROPIN


# ====================================================
# SECTION: function _match
# What it does:  match.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _match(rules, key):  # info: def _match
    return next((v for rx, v in rules if re.search(rx, key)), None)  # info: return next ( ( v for rx ,


# ====================================================
# SECTION: function infer_kind
# What it does: infer kind.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def infer_kind(key: str, value) -> str:  # info: def infer_kind
    leaf = key.rsplit(".", 1)[-1]  # info: set leaf
    if isinstance(value, bool):  # info: if isinstance ( value , bool ) :
        return "bool"  # info: return "bool"
    if isinstance(value, int):  # info: if isinstance ( value , int ) :
        return "port" if re.search(r"port$", leaf, re.I) else "int"  # info: return "port" if re . search ( r"port$"
    if isinstance(value, float):  # info: if isinstance ( value , float ) :
        return "float"  # info: return "float"
    if isinstance(value, (list, dict)):  # info: if isinstance ( value , ( list ,
        return "complex"  # info: return "complex"
    s = "" if value is None else str(value)  # info: set s
    if re.search(r"(^|_)PORT$", leaf, re.I) and re.fullmatch(r"\d+", s):  # info: if re . search ( r"(^|_)PORT$" , leaf
        return "port"  # info: return "port"
    if re.match(r"^(https?|rtsp|wss?)://", s):  # info: if re . match ( r"^(https?|rtsp|wss?)://" , s
        return "url"  # info: return "url"
    if s in ("0", "1") and re.search(r"(enabled|enable|_on|prefer|poll_enabled|^RR_)", leaf, re.I):  # info: if s in ( "0" , "1" )
        return "bool01"  # info: return "bool01"
    if re.fullmatch(r"-?\d+", s):  # info: if re . fullmatch ( r"-?\d+" , s
        return "int"  # info: return "int"
    if re.fullmatch(r"-?\d+\.\d+", s):  # info: if re . fullmatch ( r"-?\d+\.\d+" , s
        return "float"  # info: return "float"
    return "str"  # info: return "str"


# ====================================================
# SECTION: class Registry
# What it does: Registry.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class Registry:  # info: class Registry
    def __init__(self):  # info: def __init__
        self._cache: dict = {}  # info: self . _cache : dict = { }
        self._tracked: set[str] | None = None  # info: self . _tracked : set [ str ]
        self._env_scan = None  # info: self . _env_scan = None
        self.security_items: list[dict] = []  # info: self . security_items : list [ dict ]

    # ---------------------------------------------------------- git tracking (3 calls, cached)
    def tracked(self) -> set[str]:  # info: def tracked
        """Which registry files are git-tracked. Asks git only about those paths (cheap; no full index listing)."""  # info: """Which registry files are git-tracked. Asks git only about those paths (cheap; no full index listing)."""
        if self._tracked is None:  # info: if self . _tracked is None :
            s = set()  # info: set s
            for r in REPOS:  # info: for r in REPOS :
                mine = [str(f.path.relative_to(r)) for f in FILES if str(f.path).startswith(str(r) + "/")]  # info: set mine
                if not mine:  # info: if not mine :
                    continue  # info: continue
                try:  # info: try :
                    out = subprocess.run(["git", "-C", str(r), "ls-files", "-z", "--", *mine], capture_output=True, timeout=10).stdout  # info: set out
                    s.update(str(r / p.decode(errors="replace")) for p in out.split(b"\0") if p)  # info: s . update ( str ( r /
                except Exception:  # info: except Exception :
                    pass  # info: pass
            self._tracked = s  # info: self . _tracked = s
        return self._tracked  # info: return self . _tracked

    # ---------------------------------------------------------- per-file settings
    def file_settings(self, spec: FileSpec) -> list[Setting]:  # info: def file_settings
        p = spec.path  # info: set p
        if any(str(p).startswith(f) for f in FORBIDDEN):  # info: if any ( str ( p ) .
            return []  # info: return [ ]
        try:  # info: try :
            st = p.stat()  # info: set st
        except OSError:  # info: except OSError :
            return [Setting(spec.page, spec.id, str(p), "(file)", "info", False, spec.service, spec.restart, False,  # info: return [ Setting ( spec . page ,
                            "file not present", "not present")]  # info: "file not present" , "not present" ) ]
        key = (spec.id, st.st_mtime_ns, st.st_size)  # info: set key
        if key in self._cache:  # info: if key in self . _cache :
            return self._cache[key]  # info: return self . _cache [ key ]
        try:  # info: try :
            text = p.read_text(encoding="utf-8", errors="surrogateescape")  # info: set text
        except PermissionError:  # info: except PermissionError :
            res = [Setting(spec.page, spec.id, str(p), "(file)", "info", spec.secret_file, spec.service, spec.restart, False,  # info: set res
                           "no read permission", "unreadable")]  # info: "no read permission" , "unreadable" ) ]
            self._cache[key] = res  # info: self . _cache [ key ] = res
            return res  # info: return res
        tracked = str(p) in self.tracked()  # info: set tracked
        out: list[Setting] = []  # info: set out
        if spec.fmt == "code-jobs":  # info: if spec . fmt == "code-jobs" :
            out = self._jobs_settings(spec, text)  # info: set out
        elif spec.fmt == "code-const":  # info: elif spec . fmt == "code-const" :
            for m in re.finditer(r"^(KEEP_[A-Z_]+(?:\s*,\s*KEEP_[A-Z_]+)*)\s*=\s*([0-9 ,]+)$", text, re.M):  # info: for m in re . finditer ( r"^(KEEP_[A-Z_]+(?:\s*,\s*KEEP_[A-Z_]+)*)\s*=\s*([0-9 ,]+)$"
                for k, v in zip([x.strip() for x in m.group(1).split(",")], [x.strip() for x in m.group(2).split(",")]):  # info: for k , v in zip ( [
                    out.append(Setting(spec.page, spec.id, str(p), k, "int", False, spec.service, spec.restart, False,  # info: out . append ( Setting ( spec .
                                       spec.read_only, f"{v} days", _value=v))  # info: spec . read_only , f" { v }
        else:  # info: else :
            try:  # info: try :
                ents = io.parse(spec.fmt, text, spec.columns)  # info: set ents
            except Exception as e:  # info: except Exception as e :
                ents = []  # info: set ents
                out.append(Setting(spec.page, spec.id, str(p), "(file)", "info", False, spec.service, spec.restart, False,  # info: out . append ( Setting ( spec .
                                   f"unparseable: {type(e).__name__}", "unparseable"))  # info: f" unparseable: { type ( e ) .
            for e in ents:  # info: for e in ents :
                leaf = e.key.rsplit(".", 1)[-1]  # info: set leaf
                secret = spec.secret_file or (io.is_secret_key(leaf) and not any(re.search(rx, e.key) for rx in spec.not_secret))  # info: set secret
                kind = _match(spec.kinds, e.key) or infer_kind(e.key, e.value)  # info: set kind
                page = _match(spec.key_pages, e.key) or spec.page  # info: set page
                ro = spec.read_only  # info: set ro
                if not ro and any(re.search(rx, e.key) for rx in spec.ro_keys):  # info: if not ro and any ( re .
                    ro = "structural unit key — edit the unit file offline"  # info: set ro
                if not ro and e.dup:  # info: if not ro and e . dup :
                    ro = "key defined more than once — ambiguous, edit offline"  # info: set ro
                if not ro and kind == "complex":  # info: if not ro and kind == "complex" :
                    ro = "list/object — edit the file offline"  # info: set ro
                if not ro and spec.fmt == "tsv" and e.key.endswith(".id"):  # info: if not ro and spec . fmt ==
                    ro = "row id"  # info: set ro
                if secret and tracked:  # info: if secret and tracked :
                    ro = "SECURITY: secret-looking key in a git-tracked file — never written here"  # info: set ro
                    self._flag(spec, e, text)  # info: self . _flag ( spec , e ,
                disp = io.describe(e.value if not isinstance(e.value, (list, dict)) else str(e.value)) if secret else _short(e.value)  # info: set disp
                if not secret and disp and any(v in str(e.value) for v in self.secret_values()):  # info: if not secret and disp and any (
                    disp = "masked (value matches a secret held in another file)"  # info: set disp
                    ro = ro or "value matches a secret held in another file — edit offline"  # info: set ro
                    if tracked:  # info: if tracked :
                        item = {"file": str(p), "key": e.key,  # info: set item
                                "assessment": "value equals an entry of a secret file (e.g. master-key.env) — in a git-tracked file"}  # info: "assessment" : "value equals an entry of a secret file (e.g. master-key.env) — in a git-tracked file" }
                        if item not in self.security_items:  # info: if item not in self . security_items :
                            self.security_items.append(item)  # info: self . security_items . append ( item )
                out.append(Setting(page, spec.id, str(p), e.key, "secret" if secret else kind, secret, spec.service, spec.restart,  # info: out . append ( Setting ( page ,
                                   not ro and os.access(p, os.W_OK), ro or ("" if os.access(p, os.W_OK) else "no write permission"),  # info: not ro and os . access ( p
                                   disp, e.dup, e.value))  # info: disp , e . dup , e .
        self._cache = {k: v for k, v in self._cache.items() if k[0] != spec.id}  # info: self . _cache = { k : v
        self._cache[key] = out  # info: self . _cache [ key ] = out
        return out  # info: return out

    def _flag(self, spec, e, text):  # info: def _flag
        v = "" if e.value is None else str(e.value)  # info: set v
        looks = "empty" if not v else ("file path / reference (not a credential)" if v.startswith(("/", "~", "$")) else  # info: set looks
                                        "env-var NAME (not a credential)" if re.fullmatch(r"[A-Z][A-Z0-9_]+", v) else  # info: "env-var NAME (not a credential)" if re . fullmatch ( r"[A-Z][A-Z0-9_]+" ,
                                        "non-empty value — review (may be a credential or a status note)")  # info: "non-empty value — review (may be a credential or a status note)" )
        item = {"file": str(spec.path), "key": e.key, "assessment": looks}  # info: set item
        if item not in self.security_items:  # info: if item not in self . security_items :
            self.security_items.append(item)  # info: self . security_items . append ( item )

    def _jobs_settings(self, spec, text):  # info: def _jobs_settings
        out = []  # info: set out
        for m in re.finditer(r'"id":\s*"([^"]+)",\s*(?:#[^\n]*\n\s*)*"enabled":\s*([^\n]+?),?\s*\n', text):
            jid, en = m.group(1), m.group(2).strip().rstrip(",")  # info: jid , en = m . group (
            win = text[m.end():m.end() + 1500]  # info: set win
            iv = re.search(r'"interval_sec":\s*([0-9.]+)', win.split('"id":')[0])  # info: set iv
            at = re.search(r'"at_times":\s*(\[[^\]]*\])', win.split('"id":')[0])  # info: set at
            mins = re.search(r'"only_at_minutes":\s*(\[[^\]]*\])', win.split('"id":')[0])  # info: set mins
            sched = f"every {iv.group(1)} s" if iv else (f"at {at.group(1)}" if at else (f"minutes {mins.group(1)}" if mins else "boot/once/hourly"))  # info: set sched
            gated = re.search(r'os\.environ\.get\("(RR_[A-Z0-9_]+)"', en)  # info: set gated
            disp = f"enabled={('flag ' + gated.group(1)) if gated else en} · {sched}"  # info: set disp
            out.append(Setting(spec.page, spec.id, str(spec.path), jid, "job", False, spec.service, spec.restart, False,  # info: out . append ( Setting ( spec .
                               spec.read_only, disp, _value=en))  # info: spec . read_only , disp , _value =
        return out  # info: return out

    # ---------------------------------------------------------- env vars used by scripts
    def env_scan(self):  # info: def env_scan
        if self._env_scan is not None:  # info: if self . _env_scan is not None :
            return self._env_scan  # info: return self . _env_scan
        py = re.compile(r'os\.environ\.get\(\s*["\']([A-Z][A-Z0-9_]+)["\'](?:\s*,\s*([^)]{0,120}))?\)|os\.environ\[\s*["\']([A-Z][A-Z0-9_]+)["\']\s*\]|os\.getenv\(\s*["\']([A-Z][A-Z0-9_]+)["\'](?:\s*,\s*([^)]{0,120}))?\)')  # info: set py
        sh = re.compile(r'\$\{([A-Z][A-Z0-9_]+):?[-=]([^}]{0,120})\}')  # info: set sh
        js = re.compile(r'process\.env\.([A-Z][A-Z0-9_]+)(?:\s*\|\|\s*([^;,)]{0,80}))?')  # info: set js
        std = {"HOME", "PATH", "USER", "PWD", "XDG_RUNTIME_DIR", "DISPLAY", "SHELL", "TERM", "LANG", "PPID", "BASH_SOURCE",  # info: set std
               "TMPDIR", "HOSTNAME", "EUID", "UID", "DBUS_SESSION_BUS_ADDRESS", "XAUTHORITY", "MONDAY"}  # info: "TMPDIR" , "HOSTNAME" , "EUID" , "UID" ,
        uses: dict = {}  # info: set uses
        skip = {".git", ".venv", "node_modules", "vendor", "__pycache__", "Control-Panel"}  # info: set skip
        for root, dirs, files in os.walk(PAC):  # info: for root , dirs , files in os
            dirs[:] = [d for d in dirs if d not in skip]  # info: dirs [ : ] = [ d for
            for fn in files:  # info: for fn in files :
                if ".bak" in fn or not fn.endswith((".py", ".sh", ".js", ".awk")):  # info: if ".bak" in fn or not fn .
                    continue  # info: continue
                fp = os.path.join(root, fn)  # info: set fp
                try:  # info: try :
                    t = open(fp, errors="replace").read()  # info: set t
                except OSError:  # info: except OSError :
                    continue  # info: continue
                for rx in (py, sh, js):  # info: for rx in ( py , sh ,
                    for m in rx.finditer(t):  # info: for m in rx . finditer ( t
                        g = list(m.groups())  # info: set g
                        name = next(x for x in g if x and re.fullmatch(r"[A-Z][A-Z0-9_]+", x))  # info: set name
                        if name in std:  # info: if name in std :
                            continue  # info: continue
                        d = (g[1] or g[4]) if rx is py else g[1]  # info: set d
                        u = uses.setdefault(name, {"files": set(), "defaults": set()})  # info: set u
                        u["files"].add(os.path.relpath(fp, PAC))  # info: u [ "files" ] . add ( os
                        if d is not None:  # info: if d is not None :
                            u["defaults"].add(d.strip()[:80])  # info: u [ "defaults" ] . add ( d
        self._env_scan = uses  # info: self . _env_scan = uses
        return uses  # info: return uses

    def where_set(self) -> dict:  # info: def where_set
        """Env var -> where it is set on this desk (unit Environment=, flags drop-in, master-key.env)."""  # info: """Env var -> where it is set on this desk (unit Environment=, flags drop-in, master-key.env)."""
        res = {}  # info: set res
        for spec in FILES:  # info: for spec in FILES :
            if spec.id.startswith("unit:") and spec.path.exists():  # info: if spec . id . startswith ( "unit:"
                for s in self.file_settings(spec):  # info: for s in self . file_settings ( spec
                    m = re.search(r"\.Environment\.([A-Z0-9_]+)$", s.key)  # info: set m
                    if m:  # info: if m :
                        res.setdefault(m.group(1), []).append(f"{spec.path.name} Environment=")  # info: res . setdefault ( m . group (
        if FLAGS_DROPIN.exists():  # info: if FLAGS_DROPIN . exists ( ) :
            for e in io.parse_ini(FLAGS_DROPIN.read_text(errors="replace")):  # info: for e in io . parse_ini ( FLAGS_DROPIN
                m = re.search(r"\.Environment\.([A-Z0-9_]+)$", e.key)  # info: set m
                if m:  # info: if m :
                    res.setdefault(m.group(1), []).append(f"rr-flags.conf = {e.value}")  # info: res . setdefault ( m . group (
        mk = HOME / "master/master-key.env"  # info: set mk
        try:  # info: try :
            for e in io.parse_env(mk.read_text(errors="replace")):  # info: for e in io . parse_env ( mk
                res.setdefault(e.key, []).append("master-key.env")  # info: res . setdefault ( e . key ,
        except OSError:  # info: except OSError :
            pass  # info: pass
        return res  # info: return res

    def env_settings(self) -> list[Setting]:  # info: def env_settings
        uses, where = self.env_scan(), self.where_set()  # info: uses , where = self . env_scan (
        out = []  # info: set out
        dropin = FLAGS_DROPIN  # info: set dropin
        for name in sorted(uses):  # info: for name in sorted ( uses ) :
            u = uses[name]  # info: set u
            secret = io.is_secret_key(name)  # info: set secret
            page = _match(ENV_PAGE_RULES, name) or "environment"  # info: set page
            if name.startswith("RR_"):  # info: if name . startswith ( "RR_" ) :
                page = "flags"  # info: set page
            defaults = sorted(u["defaults"])  # info: set defaults
            dflt = "<hidden>" if secret else (" | ".join(defaults)[:80] or "(no default)")  # info: set dflt
            ws = where.get(name, [])  # info: set ws
            disp = f"default {dflt} · set in: {', '.join(ws) if ws else 'not set (default applies)'}"  # info: set disp
            used = ", ".join(sorted(u["files"])[:3]) + (" …" if len(u["files"]) > 3 else "")  # info: set used
            is_flag = page == "flags"  # info: set is_flag
            kind = "bool01" if is_flag and any(d.strip("\"'") in ("0", "1") for d in defaults) else ("secret" if secret else "str")  # info: set kind
            ro = "" if is_flag and not secret else "reference — set where the service reads it (see 'set in')"  # info: set ro
            val = None  # info: set val
            if is_flag and dropin.exists():  # info: if is_flag and dropin . exists ( )
                for e in io.parse_ini(dropin.read_text(errors="replace")):  # info: for e in io . parse_ini ( dropin
                    if e.key.endswith(f".Environment.{name}"):  # info: if e . key . endswith ( f"
                        val = e.value  # info: set val
            out.append(Setting(page, "env:" + name, str(dropin) if is_flag else used, name, kind, secret,  # info: out . append ( Setting ( page ,
                               "poller + its jobs (env at poller start)" if is_flag else used, R_POLLER if is_flag else "service restart",  # info: "poller + its jobs (env at poller start)" if is_flag else used , R_POLLER if
                               is_flag and not secret, ro, disp, _value=val))  # info: is_flag and not secret , ro , disp
        return out  # info: return out

    # ---------------------------------------------------------- read-only system info
    def network_info(self) -> list[Setting]:  # info: def network_info
        out = []  # info: set out
        try:  # info: try :
            r = subprocess.run(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,AUTOCONNECT", "con", "show"], capture_output=True, text=True, timeout=5)  # info: set r
            for ln in r.stdout.splitlines():  # info: for ln in r . stdout . splitlines
                parts = ln.split(":")  # info: set parts
                if len(parts) >= 3:  # info: if len ( parts ) >= 3 :
                    out.append(Setting("network", "nmcli", "NetworkManager (nmcli)", parts[0], "info", False, "NetworkManager",  # info: out . append ( Setting ( "network" ,
                                       "system", False, "NetworkManager — read-only (sign-off needed; secrets never read)",  # info: "system" , False , "NetworkManager — read-only (sign-off needed; secrets never read)" ,
                                       f"{parts[1]} · device {parts[2] or '—'} · autoconnect {parts[3] if len(parts) > 3 else '?'}"))  # info: f" { parts [ 1 ] } · device
        except Exception:  # info: except Exception :
            pass  # info: pass
        ports = {8799: "poller HTTP (rootserver_poller.py)", 8791: "A-EYES cam_server.py", 11434: "Ollama", 52625: "FLM (on demand)"}  # info: set ports
        listening = set()  # info: set listening
        for f in ("/proc/net/tcp", "/proc/net/tcp6"):  # info: for f in ( "/proc/net/tcp" , "/proc/net/tcp6" )
            try:  # info: try :
                for ln in Path(f).read_text().splitlines()[1:]:  # info: for ln in Path ( f ) .
                    p = ln.split()  # info: set p
                    if len(p) > 3 and p[3] == "0A":  # info: if len ( p ) > 3 and
                        listening.add(int(p[1].rsplit(":", 1)[1], 16))  # info: listening . add ( int ( p [
            except OSError:  # info: except OSError :
                pass  # info: pass
        for port, what in ports.items():  # info: for port , what in ports . items
            out.append(Setting("network", "ports", "/proc/net/tcp", f"port {port}", "info", False, what, "—", False,  # info: out . append ( Setting ( "network" ,
                               "live status (read-only)", f"{what} · {'listening' if port in listening else 'closed'}"))  # info: "live status (read-only)" , f" { what } · {
        return out  # info: return out

    # ---------------------------------------------------------- aggregate
    def page_settings(self, page: str) -> list[Setting]:  # info: def page_settings
        out = []  # info: set out
        for spec in FILES:  # info: for spec in FILES :
            for s in self.file_settings(spec):  # info: for s in self . file_settings ( spec
                if s.page == page:  # info: if s . page == page :
                    out.append(s)  # info: out . append ( s )
        out += [s for s in self.env_settings() if s.page == page]  # info: set out
        if page == "network":  # info: if page == "network" :
            out += self.network_info()  # info: set out
        return out  # info: return out

    def all_settings(self) -> dict:  # info: def all_settings
        return {p: self.page_settings(p) for p, _t in PAGES}  # info: return { p : self . page_settings (

    def spec(self, file_id: str) -> FileSpec | None:  # info: def spec
        return next((f for f in FILES if f.id == file_id), None)  # info: return next ( ( f for f in

    def plan(self, s: Setting, new_raw: str):  # info: def plan
        """Build a masked-diff plan for one setting change (nothing written)."""  # info: """Build a masked-diff plan for one setting change (nothing written)."""
        if not s.editable:  # info: if not s . editable :
            raise ValueError(s.ro_reason or "read-only")  # info: raise ValueError ( s . ro_reason or "read-only"
        if s.file_id.startswith("env:"):  # info: if s . file_id . startswith ( "env:"
            # RR_* flags -> poller drop-in (Environment=RR_X=v). The file is created on the first confirmed save.
            # Nothing is restarted; the running poller keeps its current environment until it is restarted by hand.
            return io.plan_edit(FLAGS_DROPIN, "ini", f"Service.Environment.{s.key}", new_raw, s.kind, secret_keys=set(),  # info: return io . plan_edit ( FLAGS_DROPIN , "ini"
                                whole_file_secret=False, restart_note=R_POLLER, create=True)  # info: set whole_file_secret
        spec = self.spec(s.file_id)  # info: set spec
        secret_keys = {x.key for x in self.file_settings(spec) if x.secret}  # info: set secret_keys
        if s.secret and str(spec.path) in self.tracked():  # info: if s . secret and str ( spec
            raise ValueError("refused: secrets are never written into git-tracked files")  # info: raise ValueError ( "refused: secrets are never written into git-tracked files" )
        return io.plan_edit(spec.path, spec.fmt, s.key, new_raw, "str" if s.kind == "secret" else s.kind,  # info: return io . plan_edit ( spec . path
                            secret_keys=secret_keys, whole_file_secret=spec.secret_file, restart_note=spec.restart,  # info: set secret_keys
                            columns=spec.columns)  # info: set columns

    def secret_values(self) -> list[str]:  # info: def secret_values
        """Credential-like secret values (for masking elsewhere, the leak tests and the screenshot guard).
        NEVER print the result. Path references and env-var NAMES are not credentials and are skipped.
        Cached by the mtimes of the files involved."""
        stamp = []  # info: set stamp
        for spec in FILES:  # info: for spec in FILES :
            try:  # info: try :
                st = spec.path.stat()  # info: set st
                stamp.append((spec.id, st.st_mtime_ns, st.st_size))  # info: stamp . append ( ( spec . id
            except OSError:  # info: except OSError :
                pass  # info: pass
        stamp = tuple(stamp)  # info: set stamp
        if getattr(self, "_sv", None) and self._sv[0] == stamp:  # info: if getattr ( self , "_sv" , None
            return self._sv[1]  # info: return self . _sv [ 1 ]
        vals = []  # info: set vals
        for spec in FILES:  # info: for spec in FILES :
            try:  # info: try :
                text = spec.path.read_text(errors="replace")  # info: set text
            except OSError:  # info: except OSError :
                continue  # info: continue
            if spec.fmt == "raw" and spec.secret_file:  # info: if spec . fmt == "raw" and spec
                vals.append(text.strip())  # info: vals . append ( text . strip (
                continue  # info: continue
            try:  # info: try :
                ents = io.parse(spec.fmt, text, spec.columns) if spec.fmt not in ("code-jobs", "code-const") else []  # info: set ents
            except Exception:  # info: except Exception :
                continue  # info: continue
            for e in ents:  # info: for e in ents :
                leaf = e.key.rsplit(".", 1)[-1]  # info: set leaf
                if any(re.search(rx, e.key) for rx in spec.not_secret):  # info: if any ( re . search ( rx
                    continue  # info: continue
                if spec.secret_file or io.is_secret_key(leaf):  # info: if spec . secret_file or io . is_secret_key
                    v = e.value  # info: set v
                    if not isinstance(v, (str, int, float)) or len(str(v)) < 6:  # info: if not isinstance ( v , ( str
                        continue  # info: continue
                    sv = str(v)  # info: set sv
                    if sv.startswith(("/", "~", "$", "./")) or re.fullmatch(r"[A-Z][A-Z0-9_]+", sv) or sv.lower() in ("true", "false"):  # info: if sv . startswith ( ( "/" ,
                        continue  # path reference / env-var name, not a credential
                    vals.append(sv)  # info: vals . append ( sv )
        res = sorted(set(vals), key=len, reverse=True)  # info: set res
        self._sv = (stamp, res)  # info: self . _sv = ( stamp , res
        io.KNOWN_SECRETS[:] = res  # info: io . KNOWN_SECRETS [ : ] = res
        return res  # info: return res


# ====================================================
# SECTION: function _short
# What it does:  short.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _short(v) -> str:  # info: def _short
    s = "" if v is None else str(v)  # info: set s
    return s if len(s) <= 160 else s[:157] + "…"  # info: return s if len ( s ) <=
