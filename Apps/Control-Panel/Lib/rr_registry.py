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
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import rr_config_io as io

ECO = Path("/home/rootrecord/RootRecord-Ecosystem")
PAC = ECO / "1 - Servers/1 - RootRecord-Pacific-Solar-Server"
DBR = ECO / "2 - RootRecord-Database"
LIB = ECO / "5 - RootRecord-Library"
HOME = Path.home()
FORBIDDEN = (str(HOME / "Desktop/old txt"), str(ECO / "I'll sort these models tomorrow"))
REPOS = (PAC, DBR, LIB)

PAGES = [("network", "Network"), ("messaging", "Messaging"), ("environment", "Environment (.env)"),
         ("flags", "Feature Flags (RR_*)"), ("services", "Services / Poller"), ("weather", "Weather"),
         ("voice", "Voice"), ("ai", "AI / NPU"), ("cameras", "Cameras"), ("panel", "Panel")]

POLLER = "rr-rootserver-poller.service"
R_POLLER = f"takes effect after {POLLER} restart"
R_RELAY = "takes effect after council relay restart (poller council_relay / ensure-relay.sh)"
R_EACH = "read at each job run (no restart)"
R_UNIT = "takes effect after systemctl --user daemon-reload + restart of {unit}"


@dataclass
class FileSpec:
    id: str
    path: Path
    fmt: str
    page: str
    service: str
    restart: str
    secret_file: bool = False
    read_only: str = ""               # non-empty = reason
    columns: list = field(default_factory=list)
    key_pages: list = field(default_factory=list)   # [(regex, page)]
    not_secret: tuple = ()            # key regexes that look secret but are not (e.g. token_env NAMES)
    ro_keys: tuple = ()               # key regexes shown read-only
    kinds: tuple = ()                 # [(regex, kind)]
    note: str = ""


@dataclass
class Setting:
    page: str
    file_id: str
    path: str
    key: str
    kind: str
    secret: bool
    service: str
    restart: str
    editable: bool
    ro_reason: str
    display: str
    dup: bool = False
    _value: object = None   # private — never render for secrets

    def value_text(self) -> str:
        return "" if self.secret else ("" if self._value is None else str(self._value))


def _unit(name, page="services", **kw):
    return FileSpec(f"unit:{name}", HOME / ".config/systemd/user" / name, "ini", page, name,
                    R_UNIT.format(unit=name), **kw)


FILES: list[FileSpec] = [
    # ---- Network
    FileSpec("cf-status", PAC / "Communications/network/cloudflare/config/cf-status.json", "json", "network", "cloudflare tunnel (docs/status)",
             "status snapshot", read_only="status snapshot written by tooling"),
    FileSpec("cf-blocker", PAC / "Communications/network/cloudflare/config/cf-blocker.json", "json", "network", "cloudflare tunnel (docs/status)",
             "status snapshot", read_only="findings snapshot written by tooling"),
    FileSpec("tunnel-token", HOME / ".cloudflared/rootserver.token", "raw", "network", "cloudflared (poller tunnel_start)", R_POLLER,
             secret_file=True),
    # ---- Messaging
    FileSpec("relay.conf", PAC / "Communications/telegram/config/relay.conf", "env", "messaging", "council-relay.py", R_RELAY,
             kinds=((r"^(ENABLED)$", "bool01"), (r"^(POLL_TIMEOUT|MAX_TEXT)$", "int"))),
    FileSpec("voices.conf", PAC / "Communications/telegram/config/voices.conf", "tsv", "messaging", "council-relay.py", R_RELAY,
             columns=["id", "enabled", "telegram_username", "token_env", "ollama_model", "fallback_model"],
             not_secret=(r"\.token_env$",), kinds=((r"\.enabled$", "bool01"),)),
    # ---- Environment
    FileSpec("master-key.env", HOME / "master/master-key.env", "env", "environment", "poller stack, relay, Energy, GitHub sync, globe relay",
             "takes effect after restart of the services that source it (poller stack, relay, BLE)", secret_file=True,
             key_pages=[(r"^(TELEGRAM_|RR_DATAPACK_)", "messaging"), (r"^(ROOTSERVER_TUNNEL|CLOUDFLARE_|API_TOKEN|ACCESS_KEY_R2|S3_API)", "network"),
                        (r"^AEYES_", "cameras")]),
    FileSpec("gh-hosts", HOME / ".config/gh/hosts.yml", "yaml", "environment", "GitHub CLI (gh)", "gh reads it per call",
             read_only="managed by `gh auth` — not edited here (oauth_token is detected by key name and masked)"),
    FileSpec("gh-config", HOME / ".config/gh/config.yml", "yaml", "environment", "GitHub CLI (gh)", "gh reads it per call",
             read_only="managed by `gh config`"),
    FileSpec("repos.conf", PAC / "Github/scripts/repos.conf", "tsv", "services", "github_sync_all / github_autopush", R_EACH,
             columns=["id", "enabled", "mode", "local_path", "github_slug", "remote_name"], kinds=((r"\.enabled$", "bool01"),)),
    # ---- Services / Poller
    _unit(POLLER, ro_keys=(r"\.(ExecStart|WorkingDirectory|KillMode|Type|After|WantedBy|Description)$",),
          key_pages=[(r"Environment\.POLLER_(BIND|PORT|PUBLIC_HOST)$", "network")],
          kinds=((r"POLLER_PORT$", "port"), (r"RestartSec$|Timeout\w*Sec$", "int"), (r"POLLER_PUBLIC_HOST$|POLLER_BIND$", "host"))),
    FileSpec("unit:poller-logging", HOME / ".config/systemd/user/rr-rootserver-poller.service.d/logging.conf", "ini", "services",
             POLLER, R_UNIT.format(unit=POLLER)),
    _unit("ava-ecoflow-ble.service", ro_keys=(r"\.(ExecStart|KillMode|Type|After|Wants|WantedBy|Description)$",),
          kinds=((r"RestartSec$|Timeout\w*Sec$", "int"),)),
    _unit("network-globe-hawaii.service", page="network", ro_keys=(r"\.(ExecStart|WorkingDirectory|KillMode|Type|After|Wants|WantedBy|Description)$",),
          kinds=((r"Timeout\w*Sec$", "int"),)),
    FileSpec("unit:ollama", Path("/etc/systemd/system/ollama.service"), "ini", "ai", "ollama.service (system)",
             "systemctl daemon-reload + restart ollama (root)", read_only="system unit in /etc — needs sudo (sign-off)"),
    FileSpec("devices.conf", PAC / "Energy/config/devices.conf", "ini", "services", "EcoFlow readers + BLE owner (ava-ecoflow-ble.service)",
             "read at each EcoFlow job run; BLE owner after ava-ecoflow-ble.service restart",
             kinds=((r"\.(prefer_api|poll_enabled)$", "bool01"), (r"_interval_s$", "int"))),
    FileSpec("jobs.py", PAC / "Automations/scripts/jobs.py", "code-jobs", "services", POLLER, R_POLLER,
             read_only="Python code — job table shown read-only; edit jobs.py offline"),
    # ---- Weather
    *[FileSpec(f"weather:{n}", PAC / f"Weather/config/{n}", "yaml", "weather", "weather poller (Weather/scripts/run_poller.py)",
               "takes effect after weather poller restart (service_supervisor / ensure-weather-poller.sh)",
               kinds=((r"seconds$|_s$|_sec$", "int"),))
      for n in ("hosts.yaml", "tiers.yaml", "resources.yaml", "counties.yaml", "report_counties.yaml", "text_cleaning.yaml")],
    FileSpec("weather-retention", PAC / "Weather/scripts/weather-retention.py", "code-const", "weather", "weather_retention job (gated OFF)",
             R_EACH, read_only="Python constants (KEEP_*_DAYS) — code change + review of a dry run"),
    # ---- AI / NPU
    FileSpec("specialist-routes", PAC / "System/config/specialist-routes.json", "json", "ai", "route-specialist.py / run-infer.sh",
             R_EACH, kinds=((r"^(threshold|saturation)$", "float"), (r"\.keywords\.", "int"), (r"^version$", "int")),
             not_secret=(r"\.keywords\.",)),   # routing keyword weights such as "token*" / "password*" — not credentials
    FileSpec("kokoro-config", DBR / "AI/Kokoro/Kokoro-82M/config.json", "json", "voice", "voice_generate.py (Kokoro-82M)",
             "model config", read_only="model file config — not a setting (never edited; no model is loaded)"),
    # ---- Cameras
    FileSpec("CONNECTION.json", PAC / "Security/Cameras/store/CONNECTION.json", "json", "cameras", "grab_frame.py / cam_server.py",
             "read at each grab; cam_server after restart", secret_file=True,
             kinds=((r"crop_right_pct$", "float"),)),
    # ---- Panel
    FileSpec("panel-settings", PAC / "Apps/Control-Panel/settings.json", "json", "panel", "Root Monitor (rr_control_panel.py)", "applies on Save / next start",
             note="edited on the Panel page (dedicated controls)", read_only="edit with the Panel page controls"),
]

# env vars from scripts -> page
ENV_PAGE_RULES = [
    (r"^RR_", "flags"),
    (r"^(POLLER_(BIND|PORT|PUBLIC_HOST|LOCAL|ENABLE_TUNNEL|TUNNEL_\w+)|CLOUDFLARED_\w+|AWS_\w+|SSH_\w+|ORIGIN_\w+|SOURCE_\w+|PACKET_WINDOW_MS|POLL_MS)$", "network"),
    (r"^(TELEGRAM_\w+|AVA_TELEGRAM\w*|DESK_LIVE_FILE)$", "messaging"),
    (r"^(FLM_\w+|OLLAMA_\w+|CALLER|MEM0|SPEC_LOG|FAKE|HOOKTEST_PORT)$", "ai"),
    (r"^(KOKORO_\w+)$", "voice"),
    (r"^(WEATHER_\w+)$", "weather"),
    (r"^(A_EYES_\w+|AEYES_\w+)$", "cameras"),
    (r"^(POLLER_\w+|ENERGY_\w+|ECOFLOW_\w+|AVA_ECOFLOW\w*|ROOTRECORD_\w+|SYSTEM_STATUS_JSON|STACK_RELOAD_LOG|OPEN_POLLER_WINDOW|BAK_ROOT|SOLAR_GATE_STATE|REPOS_CONF|MAX_FILE_MB|INTAKE_ROOT|DATABASE_ROOT)$", "services"),
]
FLAG_PAGE_VOICE = r"^RR_(VOICE|ESPEAK|KOKORO|WHISPER)"
FLAG_PAGE_AI = r"^RR_(SPEC|INFER|ROUTE|ALLOW_IGPU|PROMPT|INFERENCE_LOCK|PLUMBING|CALLER|AI_REPORT)"
FLAGS_DROPIN = HOME / ".config/systemd/user/rr-rootserver-poller.service.d/rr-flags.conf"


def _match(rules, key):
    return next((v for rx, v in rules if re.search(rx, key)), None)


def infer_kind(key: str, value) -> str:
    leaf = key.rsplit(".", 1)[-1]
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "port" if re.search(r"port$", leaf, re.I) else "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, (list, dict)):
        return "complex"
    s = "" if value is None else str(value)
    if re.search(r"(^|_)PORT$", leaf, re.I) and re.fullmatch(r"\d+", s):
        return "port"
    if re.match(r"^(https?|rtsp|wss?)://", s):
        return "url"
    if s in ("0", "1") and re.search(r"(enabled|enable|_on|prefer|poll_enabled|^RR_)", leaf, re.I):
        return "bool01"
    if re.fullmatch(r"-?\d+", s):
        return "int"
    if re.fullmatch(r"-?\d+\.\d+", s):
        return "float"
    return "str"


class Registry:
    def __init__(self):
        self._cache: dict = {}
        self._tracked: set[str] | None = None
        self._env_scan = None
        self.security_items: list[dict] = []

    # ---------------------------------------------------------- git tracking (3 calls, cached)
    def tracked(self) -> set[str]:
        """Which registry files are git-tracked. Asks git only about those paths (cheap; no full index listing)."""
        if self._tracked is None:
            s = set()
            for r in REPOS:
                mine = [str(f.path.relative_to(r)) for f in FILES if str(f.path).startswith(str(r) + "/")]
                if not mine:
                    continue
                try:
                    out = subprocess.run(["git", "-C", str(r), "ls-files", "-z", "--", *mine], capture_output=True, timeout=10).stdout
                    s.update(str(r / p.decode(errors="replace")) for p in out.split(b"\0") if p)
                except Exception:
                    pass
            self._tracked = s
        return self._tracked

    # ---------------------------------------------------------- per-file settings
    def file_settings(self, spec: FileSpec) -> list[Setting]:
        p = spec.path
        if any(str(p).startswith(f) for f in FORBIDDEN):
            return []
        try:
            st = p.stat()
        except OSError:
            return [Setting(spec.page, spec.id, str(p), "(file)", "info", False, spec.service, spec.restart, False,
                            "file not present", "not present")]
        key = (spec.id, st.st_mtime_ns, st.st_size)
        if key in self._cache:
            return self._cache[key]
        try:
            text = p.read_text(encoding="utf-8", errors="surrogateescape")
        except PermissionError:
            res = [Setting(spec.page, spec.id, str(p), "(file)", "info", spec.secret_file, spec.service, spec.restart, False,
                           "no read permission", "unreadable")]
            self._cache[key] = res
            return res
        tracked = str(p) in self.tracked()
        out: list[Setting] = []
        if spec.fmt == "code-jobs":
            out = self._jobs_settings(spec, text)
        elif spec.fmt == "code-const":
            for m in re.finditer(r"^(KEEP_[A-Z_]+(?:\s*,\s*KEEP_[A-Z_]+)*)\s*=\s*([0-9 ,]+)$", text, re.M):
                for k, v in zip([x.strip() for x in m.group(1).split(",")], [x.strip() for x in m.group(2).split(",")]):
                    out.append(Setting(spec.page, spec.id, str(p), k, "int", False, spec.service, spec.restart, False,
                                       spec.read_only, f"{v} days", _value=v))
        else:
            try:
                ents = io.parse(spec.fmt, text, spec.columns)
            except Exception as e:
                ents = []
                out.append(Setting(spec.page, spec.id, str(p), "(file)", "info", False, spec.service, spec.restart, False,
                                   f"unparseable: {type(e).__name__}", "unparseable"))
            for e in ents:
                leaf = e.key.rsplit(".", 1)[-1]
                secret = spec.secret_file or (io.is_secret_key(leaf) and not any(re.search(rx, e.key) for rx in spec.not_secret))
                kind = _match(spec.kinds, e.key) or infer_kind(e.key, e.value)
                page = _match(spec.key_pages, e.key) or spec.page
                ro = spec.read_only
                if not ro and any(re.search(rx, e.key) for rx in spec.ro_keys):
                    ro = "structural unit key — edit the unit file offline"
                if not ro and e.dup:
                    ro = "key defined more than once — ambiguous, edit offline"
                if not ro and kind == "complex":
                    ro = "list/object — edit the file offline"
                if not ro and spec.fmt == "tsv" and e.key.endswith(".id"):
                    ro = "row id"
                if secret and tracked:
                    ro = "SECURITY: secret-looking key in a git-tracked file — never written here"
                    self._flag(spec, e, text)
                disp = io.describe(e.value if not isinstance(e.value, (list, dict)) else str(e.value)) if secret else _short(e.value)
                if not secret and disp and any(v in str(e.value) for v in self.secret_values()):
                    disp = "masked (value matches a secret held in another file)"
                    ro = ro or "value matches a secret held in another file — edit offline"
                    if tracked:
                        item = {"file": str(p), "key": e.key,
                                "assessment": "value equals an entry of a secret file (e.g. master-key.env) — in a git-tracked file"}
                        if item not in self.security_items:
                            self.security_items.append(item)
                out.append(Setting(page, spec.id, str(p), e.key, "secret" if secret else kind, secret, spec.service, spec.restart,
                                   not ro and os.access(p, os.W_OK), ro or ("" if os.access(p, os.W_OK) else "no write permission"),
                                   disp, e.dup, e.value))
        self._cache = {k: v for k, v in self._cache.items() if k[0] != spec.id}
        self._cache[key] = out
        return out

    def _flag(self, spec, e, text):
        v = "" if e.value is None else str(e.value)
        looks = "empty" if not v else ("file path / reference (not a credential)" if v.startswith(("/", "~", "$")) else
                                        "env-var NAME (not a credential)" if re.fullmatch(r"[A-Z][A-Z0-9_]+", v) else
                                        "non-empty value — review (may be a credential or a status note)")
        item = {"file": str(spec.path), "key": e.key, "assessment": looks}
        if item not in self.security_items:
            self.security_items.append(item)

    def _jobs_settings(self, spec, text):
        out = []
        for m in re.finditer(r'"id":\s*"([^"]+)",\s*(?:#[^\n]*\n\s*)*"enabled":\s*([^\n]+?),?\s*\n', text):
            jid, en = m.group(1), m.group(2).strip().rstrip(",")
            win = text[m.end():m.end() + 1500]
            iv = re.search(r'"interval_sec":\s*([0-9.]+)', win.split('"id":')[0])
            at = re.search(r'"at_times":\s*(\[[^\]]*\])', win.split('"id":')[0])
            mins = re.search(r'"only_at_minutes":\s*(\[[^\]]*\])', win.split('"id":')[0])
            sched = f"every {iv.group(1)} s" if iv else (f"at {at.group(1)}" if at else (f"minutes {mins.group(1)}" if mins else "boot/once/hourly"))
            gated = re.search(r'os\.environ\.get\("(RR_[A-Z0-9_]+)"', en)
            disp = f"enabled={('flag ' + gated.group(1)) if gated else en} · {sched}"
            out.append(Setting(spec.page, spec.id, str(spec.path), jid, "job", False, spec.service, spec.restart, False,
                               spec.read_only, disp, _value=en))
        return out

    # ---------------------------------------------------------- env vars used by scripts
    def env_scan(self):
        if self._env_scan is not None:
            return self._env_scan
        py = re.compile(r'os\.environ\.get\(\s*["\']([A-Z][A-Z0-9_]+)["\'](?:\s*,\s*([^)]{0,120}))?\)|os\.environ\[\s*["\']([A-Z][A-Z0-9_]+)["\']\s*\]|os\.getenv\(\s*["\']([A-Z][A-Z0-9_]+)["\'](?:\s*,\s*([^)]{0,120}))?\)')
        sh = re.compile(r'\$\{([A-Z][A-Z0-9_]+):?[-=]([^}]{0,120})\}')
        js = re.compile(r'process\.env\.([A-Z][A-Z0-9_]+)(?:\s*\|\|\s*([^;,)]{0,80}))?')
        std = {"HOME", "PATH", "USER", "PWD", "XDG_RUNTIME_DIR", "DISPLAY", "SHELL", "TERM", "LANG", "PPID", "BASH_SOURCE",
               "TMPDIR", "HOSTNAME", "EUID", "UID", "DBUS_SESSION_BUS_ADDRESS", "XAUTHORITY", "MONDAY"}
        uses: dict = {}
        skip = {".git", ".venv", "node_modules", "vendor", "__pycache__", "Control-Panel"}
        for root, dirs, files in os.walk(PAC):
            dirs[:] = [d for d in dirs if d not in skip]
            for fn in files:
                if ".bak" in fn or not fn.endswith((".py", ".sh", ".js", ".awk")):
                    continue
                fp = os.path.join(root, fn)
                try:
                    t = open(fp, errors="replace").read()
                except OSError:
                    continue
                for rx in (py, sh, js):
                    for m in rx.finditer(t):
                        g = list(m.groups())
                        name = next(x for x in g if x and re.fullmatch(r"[A-Z][A-Z0-9_]+", x))
                        if name in std:
                            continue
                        d = (g[1] or g[4]) if rx is py else g[1]
                        u = uses.setdefault(name, {"files": set(), "defaults": set()})
                        u["files"].add(os.path.relpath(fp, PAC))
                        if d is not None:
                            u["defaults"].add(d.strip()[:80])
        self._env_scan = uses
        return uses

    def where_set(self) -> dict:
        """Env var -> where it is set on this desk (unit Environment=, flags drop-in, master-key.env)."""
        res = {}
        for spec in FILES:
            if spec.id.startswith("unit:") and spec.path.exists():
                for s in self.file_settings(spec):
                    m = re.search(r"\.Environment\.([A-Z0-9_]+)$", s.key)
                    if m:
                        res.setdefault(m.group(1), []).append(f"{spec.path.name} Environment=")
        if FLAGS_DROPIN.exists():
            for e in io.parse_ini(FLAGS_DROPIN.read_text(errors="replace")):
                m = re.search(r"\.Environment\.([A-Z0-9_]+)$", e.key)
                if m:
                    res.setdefault(m.group(1), []).append(f"rr-flags.conf = {e.value}")
        mk = HOME / "master/master-key.env"
        try:
            for e in io.parse_env(mk.read_text(errors="replace")):
                res.setdefault(e.key, []).append("master-key.env")
        except OSError:
            pass
        return res

    def env_settings(self) -> list[Setting]:
        uses, where = self.env_scan(), self.where_set()
        out = []
        dropin = FLAGS_DROPIN
        for name in sorted(uses):
            u = uses[name]
            secret = io.is_secret_key(name)
            page = _match(ENV_PAGE_RULES, name) or "environment"
            if name.startswith("RR_"):
                page = "flags"
            defaults = sorted(u["defaults"])
            dflt = "<hidden>" if secret else (" | ".join(defaults)[:80] or "(no default)")
            ws = where.get(name, [])
            disp = f"default {dflt} · set in: {', '.join(ws) if ws else 'not set (default applies)'}"
            used = ", ".join(sorted(u["files"])[:3]) + (" …" if len(u["files"]) > 3 else "")
            is_flag = page == "flags"
            kind = "bool01" if is_flag and any(d.strip("\"'") in ("0", "1") for d in defaults) else ("secret" if secret else "str")
            ro = "" if is_flag and not secret else "reference — set where the service reads it (see 'set in')"
            val = None
            if is_flag and dropin.exists():
                for e in io.parse_ini(dropin.read_text(errors="replace")):
                    if e.key.endswith(f".Environment.{name}"):
                        val = e.value
            out.append(Setting(page, "env:" + name, str(dropin) if is_flag else used, name, kind, secret,
                               "poller + its jobs (env at poller start)" if is_flag else used, R_POLLER if is_flag else "service restart",
                               is_flag and not secret, ro, disp, _value=val))
        return out

    # ---------------------------------------------------------- read-only system info
    def network_info(self) -> list[Setting]:
        out = []
        try:
            r = subprocess.run(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,AUTOCONNECT", "con", "show"], capture_output=True, text=True, timeout=5)
            for ln in r.stdout.splitlines():
                parts = ln.split(":")
                if len(parts) >= 3:
                    out.append(Setting("network", "nmcli", "NetworkManager (nmcli)", parts[0], "info", False, "NetworkManager",
                                       "system", False, "NetworkManager — read-only (sign-off needed; secrets never read)",
                                       f"{parts[1]} · device {parts[2] or '—'} · autoconnect {parts[3] if len(parts) > 3 else '?'}"))
        except Exception:
            pass
        ports = {8799: "poller HTTP (rootserver_poller.py)", 8791: "A-EYES cam_server.py", 11434: "Ollama", 52625: "FLM (on demand)"}
        listening = set()
        for f in ("/proc/net/tcp", "/proc/net/tcp6"):
            try:
                for ln in Path(f).read_text().splitlines()[1:]:
                    p = ln.split()
                    if len(p) > 3 and p[3] == "0A":
                        listening.add(int(p[1].rsplit(":", 1)[1], 16))
            except OSError:
                pass
        for port, what in ports.items():
            out.append(Setting("network", "ports", "/proc/net/tcp", f"port {port}", "info", False, what, "—", False,
                               "live status (read-only)", f"{what} · {'listening' if port in listening else 'closed'}"))
        return out

    # ---------------------------------------------------------- aggregate
    def page_settings(self, page: str) -> list[Setting]:
        out = []
        for spec in FILES:
            for s in self.file_settings(spec):
                if s.page == page:
                    out.append(s)
        out += [s for s in self.env_settings() if s.page == page]
        if page == "network":
            out += self.network_info()
        return out

    def all_settings(self) -> dict:
        return {p: self.page_settings(p) for p, _t in PAGES}

    def spec(self, file_id: str) -> FileSpec | None:
        return next((f for f in FILES if f.id == file_id), None)

    def plan(self, s: Setting, new_raw: str):
        """Build a masked-diff plan for one setting change (nothing written)."""
        if not s.editable:
            raise ValueError(s.ro_reason or "read-only")
        if s.file_id.startswith("env:"):
            # RR_* flags -> poller drop-in (Environment=RR_X=v); file created by commit if missing
            path = FLAGS_DROPIN
            if not path.exists():
                raise ValueError(f"{path.name} does not exist yet — creating the flags drop-in is a sign-off item")
            return io.plan_edit(path, "ini", f"Service.Environment.{s.key}", new_raw, s.kind, secret_keys=set(),
                                whole_file_secret=False, restart_note=R_POLLER, create=True)
        spec = self.spec(s.file_id)
        secret_keys = {x.key for x in self.file_settings(spec) if x.secret}
        if s.secret and str(spec.path) in self.tracked():
            raise ValueError("refused: secrets are never written into git-tracked files")
        return io.plan_edit(spec.path, spec.fmt, s.key, new_raw, "str" if s.kind == "secret" else s.kind,
                            secret_keys=secret_keys, whole_file_secret=spec.secret_file, restart_note=spec.restart,
                            columns=spec.columns)

    def secret_values(self) -> list[str]:
        """Credential-like secret values (for masking elsewhere, the leak tests and the screenshot guard).
        NEVER print the result. Path references and env-var NAMES are not credentials and are skipped.
        Cached by the mtimes of the files involved."""
        stamp = []
        for spec in FILES:
            try:
                st = spec.path.stat()
                stamp.append((spec.id, st.st_mtime_ns, st.st_size))
            except OSError:
                pass
        stamp = tuple(stamp)
        if getattr(self, "_sv", None) and self._sv[0] == stamp:
            return self._sv[1]
        vals = []
        for spec in FILES:
            try:
                text = spec.path.read_text(errors="replace")
            except OSError:
                continue
            if spec.fmt == "raw" and spec.secret_file:
                vals.append(text.strip())
                continue
            try:
                ents = io.parse(spec.fmt, text, spec.columns) if spec.fmt not in ("code-jobs", "code-const") else []
            except Exception:
                continue
            for e in ents:
                leaf = e.key.rsplit(".", 1)[-1]
                if any(re.search(rx, e.key) for rx in spec.not_secret):
                    continue
                if spec.secret_file or io.is_secret_key(leaf):
                    v = e.value
                    if not isinstance(v, (str, int, float)) or len(str(v)) < 6:
                        continue
                    sv = str(v)
                    if sv.startswith(("/", "~", "$", "./")) or re.fullmatch(r"[A-Z][A-Z0-9_]+", sv) or sv.lower() in ("true", "false"):
                        continue  # path reference / env-var name, not a credential
                    vals.append(sv)
        res = sorted(set(vals), key=len, reverse=True)
        self._sv = (stamp, res)
        io.KNOWN_SECRETS[:] = res
        return res


def _short(v) -> str:
    s = "" if v is None else str(v)
    return s if len(s) <= 160 else s[:157] + "…"
