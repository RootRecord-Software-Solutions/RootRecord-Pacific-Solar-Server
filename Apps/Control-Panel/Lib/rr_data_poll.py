"""rr_data_poll.py — Local Pacific data-poll vs ML2 toggle helpers for Root Monitor.

INFO — MUST HAVE (future agents), added 2026-10-02:
- Pacific env flag RR_LOCAL_DATA_POLL gates LOCAL_DATA_POLL_JOBS inside Automations/scripts/automation_control.py.
  Default is local ON (1 / unset). This is a TOGGLE, not a cutover that deletes home collectors.
- Root Monitor UI mirrors AWS Fallback safety: data_poll_toggle_mode defaults to "dry-run" (confirm only,
  write nothing that affects the live poller). "write" mode (Settings → Panel) may persist panel intent +
  an intent YAML under Database System/control-panel/. Writing the systemd drop-in requires
  data_poll_apply_dropin=true (default false). The panel NEVER restarts the poller.
- Exclusive gate: RR_LOCAL_DATA_POLL=0 → Pacific LOCAL_DATA_POLL_JOBS off (ML2 collectors own them);
  RR_LOCAL_DATA_POLL=1 → Pacific local on (ML2 collectors/stream soft-stopped when data_poll_sync_ml2).
  EcoFlow / cams never gated. Soft toggle only — never delete collectors.
- When write + data_poll_apply_dropin and the drop-in value differs from live, confirm may also
  daemon-reload + restart rr-rootserver-poller (data_poll_restart_poller). Prefer no bounce otherwise.
  Docs: Library 15-Domains US-Mainland-Two.md; ML2 host docs/TOGGLE.md; Automations/config/data_poll_mode.example.yaml.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

ENV_NAME = "RR_LOCAL_DATA_POLL"
MODES = ("dry-run", "write")
DESIRED = ("local", "ml2")  # local = Pacific polls; ml2 = offload gated jobs

# Keep in sync with Automations/scripts/automation_control.py LOCAL_DATA_POLL_JOBS.
GATED_JOBS = frozenset({
    "geology_collect",
    "geology_kilauea_cams",
    "weather_poller",
    "weather_us_states",
    "weather_radar_zip",
    "weather_retention",
    "country_location_pollers",
    "radio_rss_poll",
})

DATABASE_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
INTENT_FILE = DATABASE_ROOT / "System/control-panel/data_poll_mode.yaml"
DROPIN_DIR = Path.home() / ".config/systemd/user/rr-rootserver-poller.service.d"
DROPIN_FILE = DROPIN_DIR / "rr-data-poll.conf"
UNIT_NAME = "rr-rootserver-poller.service"

_ENV_LINE = re.compile(rf"^Environment={ENV_NAME}=(?P<val>\S+)\s*$")


def normalize_mode(raw) -> str:
    v = str(raw or "dry-run").strip().lower()
    return v if v in MODES else "dry-run"


def normalize_desired(raw) -> str:
    v = str(raw or "local").strip().lower()
    if v in ("remote", "0", "off", "false", "no", "ml2"):
        return "ml2"
    return "local"


def env_means_local(raw) -> bool:
    """True when Pacific should run internet data-poll jobs (fail-safe default)."""
    v = (str(raw) if raw is not None else "1").strip().lower()
    if v == "":
        return True
    return v not in ("0", "false", "off", "no")


def desired_to_env(desired: str) -> str:
    return "1" if normalize_desired(desired) == "local" else "0"


def read_poller_environ(unit: str = UNIT_NAME) -> dict[str, str]:
    """Best-effort read of the live poller process environment (no restart, no write)."""
    out: dict[str, str] = {}
    try:
        import subprocess
        pid_s = subprocess.check_output(
            ["systemctl", "--user", "show", "-p", "MainPID", "--value", unit],
            text=True, timeout=3,
        ).strip()
        pid = int(pid_s or "0")
        if pid <= 0:
            return out
        raw = Path(f"/proc/{pid}/environ").read_bytes()
        for chunk in raw.split(b"\0"):
            if not chunk or b"=" not in chunk:
                continue
            k, _, v = chunk.partition(b"=")
            try:
                out[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
            except Exception:
                continue
    except Exception:
        return out
    return out


def read_dropin_value(path: Path = DROPIN_FILE) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for ln in text.splitlines():
        m = _ENV_LINE.match(ln.strip())
        if m:
            return m.group("val")
    return None


def read_intent(path: Path = INTENT_FILE) -> dict:
    """Parse a tiny YAML-ish intent file (mode: local|remote). Missing → empty.

    Inline comments after the value are stripped (e.g. `mode: remote  # maps to …`).
    """
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    mode = None
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith("#") or not s:
            continue
        if s.lower().startswith("mode:"):
            raw = s.split(":", 1)[1].strip()
            if "#" in raw:
                raw = raw.split("#", 1)[0].strip()
            mode = raw.strip("\"'")
            break
    if mode is None:
        return {}
    return {"mode": "ml2" if normalize_desired(mode) == "ml2" else "local"}


def snapshot(settings: dict | None = None) -> dict:
    """Current panel + live + drop-in + intent view for the UI (read-only)."""
    s = settings or {}
    mode = normalize_mode(s.get("data_poll_toggle_mode"))
    desired = normalize_desired(s.get("data_poll_desired"))
    apply_dropin = bool(s.get("data_poll_apply_dropin"))
    live_env = read_poller_environ()
    live_raw = live_env.get(ENV_NAME)
    live_local = env_means_local(live_raw if live_raw is not None else "1")
    drop_raw = read_dropin_value()
    drop_local = None if drop_raw is None else env_means_local(drop_raw)
    intent = read_intent()
    intent_desired = intent.get("mode")
    # Panel process env (usually unset) — informational only.
    panel_raw = os.environ.get(ENV_NAME)
    return {
        "env_name": ENV_NAME,
        "toggle_mode": mode,
        "desired": desired,
        "apply_dropin": apply_dropin,
        "live_raw": live_raw,  # None = unset on poller → local ON
        "live_local": live_local,
        "live_label": "Local Pacific poll" if live_local else "ML2 offload (local gated)",
        "dropin_raw": drop_raw,
        "dropin_local": drop_local,
        "dropin_path": str(DROPIN_FILE),
        "intent_path": str(INTENT_FILE),
        "intent_desired": intent_desired,
        "panel_raw": panel_raw,
        "gated_jobs": sorted(GATED_JOBS),
        "fail_safe": "If ML2/AWS is down: RR_LOCAL_DATA_POLL=1 runs ML2 collectors from the US-Mainland-Two desk tree (run-local-bank.sh) into Database — no Pacific poller copies.",
    }


def _atomic_write(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass


def write_intent(desired: str, path: Path = INTENT_FILE) -> Path:
    """Persist panel intent only. Poller does not read this file yet (env remains primary)."""
    d = normalize_desired(desired)
    yaml_mode = "local" if d == "local" else "remote"
    env_val = desired_to_env(d)
    text = (
        f"# Written by Root Monitor data-poll toggle. Documentation / intent only until a file reader is added.\n"
        f"# Primary live control remains env {ENV_NAME} on the poller process.\n"
        f"#   1 / unset = Local Pacific poll (fail-safe default)\n"
        f"#   0         = gate LOCAL_DATA_POLL_JOBS; ML2 collectors + stream should be healthy\n"
        f"# TOGGLE only — home collectors stay in jobs.py. If ML2 dies: set {ENV_NAME}=1 and restart poller.\n"
        f"mode: {yaml_mode}\n# maps to {ENV_NAME}={env_val}\n"
    )
    _atomic_write(path, text, 0o644)
    return path


def write_dropin(desired: str, path: Path = DROPIN_FILE) -> Path:
    """Write Environment=RR_LOCAL_DATA_POLL=… drop-in. Does NOT restart the poller."""
    env_val = desired_to_env(desired)
    text = (
        f"# Root Monitor data-poll toggle (do not hand-edit while the panel owns this file).\n"
        f"# Takes effect after daemon-reload + restart of {UNIT_NAME} (panel does that when data_poll_restart_poller=true).\n"
        f"# Default fail-safe is local ON (RR_LOCAL_DATA_POLL=1 / unset). Soft exclusive gate only.\n"
        f"[Service]\n"
        f"Environment={ENV_NAME}={env_val}\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, text, 0o644)
    return path



def restart_poller(unit: str = UNIT_NAME) -> dict:
    """daemon-reload + restart poller so a new drop-in RR_LOCAL_DATA_POLL takes effect.

    Prefer not calling this unless drop-in apply changed the live gate. Returns rc/out.
    """
    import subprocess
    steps = []
    for argv in (
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "restart", unit],
    ):
        p = subprocess.run(argv, capture_output=True, text=True, timeout=120)
        steps.append({"argv": argv, "rc": p.returncode, "out": ((p.stdout or "") + (p.stderr or "")).strip()[:400]})
        if p.returncode != 0:
            return {"ok": False, "steps": steps}
    # Brief settle + ActiveState probe
    import time
    time.sleep(1.5)
    st = subprocess.run(
        ["systemctl", "--user", "show", "-p", "ActiveState", "--value", unit],
        capture_output=True, text=True, timeout=15,
    )
    active = (st.stdout or "").strip()
    return {"ok": active == "active", "active": active, "steps": steps}


def sync_ml2_exclusive(desired: str, alias: str = "ml2-ip") -> dict:
    """Soft exclusive-gate peer on ML2: local → stop collectors/stream timers; ml2 → start them.

    Never deletes units. EcoFlow/cams are Pacific-only and are not touched. Best-effort SSH.
    """
    import subprocess
    d = normalize_desired(desired)
    if d == "local":
        remote = (
            "sudo -n systemctl stop ml2-collectors.timer ml2-db-stream.timer; "
            "sudo -n systemctl is-active ml2-collectors.timer ml2-db-stream.timer || true"
        )
        action = "stop"
    else:
        remote = (
            "sudo -n systemctl start ml2-collectors.timer ml2-db-stream.timer; "
            "sudo -n systemctl is-active ml2-collectors.timer ml2-db-stream.timer || true"
        )
        action = "start"
    argv = ["timeout", "20", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", alias, remote]
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=25)
        return {
            "ok": p.returncode == 0,
            "action": action,
            "alias": alias,
            "rc": p.returncode,
            "out": ((p.stdout or "") + (p.stderr or "")).strip()[:400],
        }
    except Exception as exc:
        return {"ok": False, "action": action, "alias": alias, "error": str(exc)}


def apply_write(settings: dict, desired: str) -> dict:
    """Persist intent (+ optional drop-in / restart / ML2 soft sync). Mutates settings dict.

    Restart only when data_poll_apply_dropin writes a value that differs from live AND
    data_poll_restart_poller is true (kill-switch needs env to bind on the poller process).
    """
    d = normalize_desired(desired)
    settings["data_poll_desired"] = d
    intent = write_intent(d)
    env_val = desired_to_env(d)
    dropin_written = None
    live_before = read_poller_environ().get(ENV_NAME)
    live_local_before = env_means_local(live_before if live_before is not None else "1")
    want_local = d == "local"
    if bool(settings.get("data_poll_apply_dropin")):
        dropin_written = str(write_dropin(d))
    needs_restart = bool(dropin_written) and (live_local_before != want_local)
    do_restart = needs_restart and bool(settings.get("data_poll_restart_poller"))
    restart = None
    if do_restart:
        restart = restart_poller()
    ml2 = None
    if bool(settings.get("data_poll_sync_ml2")):
        alias = str(settings.get("data_poll_ml2_alias") or "ml2-ip")
        ml2 = sync_ml2_exclusive(d, alias=alias)
    live_after = read_poller_environ().get(ENV_NAME)
    return {
        "desired": d,
        "env_value": env_val,
        "intent_path": str(intent),
        "dropin_path": dropin_written,
        "needs_poller_restart": needs_restart,
        "restart": restart,
        "ml2": ml2,
        "live_unchanged": (live_after == live_before),
        "live_raw_after": live_after,
        "live_local_after": env_means_local(live_after if live_after is not None else "1"),
    }


def confirm_body(snap: dict, new_local: bool, write_mode: bool, apply_dropin: bool,
                 restart_poller_flag: bool = False, sync_ml2: bool = False) -> str:
    target = "Local Pacific poll (RR_LOCAL_DATA_POLL=1)" if new_local else "ML2 offload (RR_LOCAL_DATA_POLL=0)"
    jobs = ", ".join(snap.get("gated_jobs") or sorted(GATED_JOBS))
    live_local = bool(snap.get("live_local"))
    gate_flip = live_local != bool(new_local)
    lines = [
        f"Desired: {target}",
        f"Live poller now: {snap.get('live_label')} "
        f"(env {ENV_NAME}={'unset → local ON' if snap.get('live_raw') is None else snap.get('live_raw')})",
        f"Gated jobs when local is Off: {jobs}",
        "",
        "EXCLUSIVE GATE: Local On ⇒ ML2 collectors/stream soft-off; ML2 On ⇒ Pacific gated jobs off.",
        "This is a TOGGLE, not a replacement. Home collectors stay installed.",
        "EcoFlow / Energy, cams, LAN globe, voice, tunnel stay on Pacific always.",
        "If AWS/ML2 dies: flip Local Pacific back On (and let the panel restart the poller if drop-in apply is on).",
    ]
    if not write_mode:
        lines += ["", "DRY-RUN: confirm shows this change and writes nothing."]
    else:
        lines += [
            "",
            "WRITE: saves panel intent (settings + Database System/control-panel/data_poll_mode.yaml).",
        ]
        if apply_dropin:
            lines += [f"Also writes drop-in {DROPIN_FILE} (Environment={ENV_NAME}=…)."]
            if restart_poller_flag and gate_flip:
                lines += [
                    "Then: systemctl --user daemon-reload && restart rr-rootserver-poller "
                    "(required for the new env to bind on the live process).",
                ]
            elif gate_flip:
                lines += [
                    "data_poll_restart_poller is false: drop-in is written but LIVE env stays until YOU restart the poller.",
                ]
            else:
                lines += ["Live env already matches desired — no poller restart needed."]
        else:
            lines += [
                "data_poll_apply_dropin is false: systemd drop-in is NOT written.",
                "Live poller env stays unchanged (safe default until ML2 stream banks are verified).",
            ]
        if sync_ml2:
            lines += [
                "Also soft-syncs ML2 timers (ml2-collectors + ml2-db-stream) via SSH — start for ML2 side, stop for Local.",
            ]
    return "\n".join(lines)
