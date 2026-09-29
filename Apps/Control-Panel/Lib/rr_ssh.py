"""rr_ssh.py — SSH host list for Root Monitor's SSH page (added 2026-09-29).

- Parses ~/.ssh/config for Host / HostName / User / Port and whether ProxyCommand / IdentityFile are set.
  It NEVER opens key files and never shows IdentityFile paths or key contents.
- Status check = `ssh -o BatchMode=yes -o ConnectTimeout=5 <alias> uptime` wrapped in `timeout 5` (read-only),
  run only when the button is pressed. Open = a terminal (ptyxis / gnome-terminal / x-terminal-emulator) running ssh.
- Mainland: no Host alias exists on this desk (2026-09-29). The Library design doc 'GithubAI with Ava.md' carries an
  EMPTY MAINLAND_SSH_HOST/PORT/USER template, and WO-ECO/WO-GH list US-Mainland-Server as a stub continuity node
  with its sync disabled. Set settings.json "ssh_mainland_alias" once a Host block exists.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

SSH_CONFIG = Path.home() / ".ssh/config"
ROLES = {"rr-aws": "AWS host (Cloudflare Access hostname)", "rr-aws-ip": "AWS host (direct IP fallback)"}


def hosts() -> list[dict]:
    out, cur = [], None
    try:
        lines = SSH_CONFIG.read_text(errors="replace").splitlines()
    except OSError:
        return []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split(None, 1)
        k, v = parts[0].lower(), (parts[1].strip() if len(parts) > 1 else "")
        if k == "host":
            cur = {"alias": v, "hostname": "", "user": "", "port": "22", "proxy": False, "proxy_ok": None, "identity": False}
            out.append(cur)
        elif cur is None:
            continue
        elif k == "hostname":
            cur["hostname"] = v
        elif k == "user":
            cur["user"] = v
        elif k == "port":
            cur["port"] = v
        elif k == "proxycommand":
            cur["proxy"] = True
            exe = v.split()[0] if v else ""
            cur["proxy_ok"] = bool(exe) and (os.path.exists(os.path.expanduser(exe)) or shutil.which(exe) is not None)
        elif k == "identityfile":
            cur["identity"] = True
    return [h for h in out if "*" not in h["alias"]]


def terminal_argv(alias: str) -> list[str] | None:
    for t, pre in (("ptyxis", ["ptyxis", "--new-window", "--"]), ("gnome-terminal", ["gnome-terminal", "--"]),
                   ("x-terminal-emulator", ["x-terminal-emulator", "-e"])):
        if shutil.which(t):
            return pre + ["ssh", alias]
    return None


def check_argv(alias: str) -> list[str]:
    return ["timeout", "5", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", alias, "uptime"]
