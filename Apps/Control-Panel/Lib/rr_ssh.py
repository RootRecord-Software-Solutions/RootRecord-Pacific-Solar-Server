# ==============================================================================
# FILE: Apps/Control-Panel/Lib/rr_ssh.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""rr_ssh.py — SSH host list for Root Monitor's SSH page (added 2026-09-29).

- Parses ~/.ssh/config for Host / HostName / User / Port and whether ProxyCommand / IdentityFile are set.
  It NEVER opens key files and never shows IdentityFile paths or key contents.
- Status check = `ssh -o BatchMode=yes -o ConnectTimeout=5 <alias> uptime` wrapped in `timeout 5` (read-only),
  run only when the button is pressed. Open = a terminal (ptyxis / gnome-terminal / x-terminal-emulator) running ssh.
- Mainland: no Host alias exists on this desk (2026-09-29). The Library design doc 'GithubAI with Ava.md' carries an
  EMPTY MAINLAND_SSH_HOST/PORT/USER template, and WO-ECO/WO-GH list US-Mainland-One as a stub continuity node
  with its sync disabled. Set settings.json "ssh_mainland_alias" once a Host block exists.
"""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import shutil  # info: import shutil
from pathlib import Path  # info: from pathlib import Path

SSH_CONFIG = Path.home() / ".ssh/config"  # info: set SSH_CONFIG
ROLES = {"rr-aws": "AWS host (Cloudflare Access hostname)", "rr-aws-ip": "AWS host (direct IP fallback)"}  # info: set ROLES


# ====================================================
# SECTION: function hosts
# What it does: hosts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hosts() -> list[dict]:  # info: def hosts
    out, cur = [], None  # info: out , cur = [ ] , None
    try:  # info: try :
        lines = SSH_CONFIG.read_text(errors="replace").splitlines()  # info: set lines
    except OSError:  # info: except OSError :
        return []  # info: return [ ]
    for ln in lines:  # info: for ln in lines :
        s = ln.strip()  # info: set s
        if not s or s.startswith("#"):
            continue  # info: continue
        parts = s.split(None, 1)  # info: set parts
        k, v = parts[0].lower(), (parts[1].strip() if len(parts) > 1 else "")  # info: k , v = parts [ 0 ]
        if k == "host":  # info: if k == "host" :
            cur = {"alias": v, "hostname": "", "user": "", "port": "22", "proxy": False, "proxy_ok": None, "identity": False}  # info: set cur
            out.append(cur)  # info: out . append ( cur )
        elif cur is None:  # info: elif cur is None :
            continue  # info: continue
        elif k == "hostname":  # info: elif k == "hostname" :
            cur["hostname"] = v  # info: cur [ "hostname" ] = v
        elif k == "user":  # info: elif k == "user" :
            cur["user"] = v  # info: cur [ "user" ] = v
        elif k == "port":  # info: elif k == "port" :
            cur["port"] = v  # info: cur [ "port" ] = v
        elif k == "proxycommand":  # info: elif k == "proxycommand" :
            cur["proxy"] = True  # info: cur [ "proxy" ] = True
            exe = v.split()[0] if v else ""  # info: set exe
            cur["proxy_ok"] = bool(exe) and (os.path.exists(os.path.expanduser(exe)) or shutil.which(exe) is not None)  # info: cur [ "proxy_ok" ] = bool ( exe
        elif k == "identityfile":  # info: elif k == "identityfile" :
            cur["identity"] = True  # info: cur [ "identity" ] = True
    return [h for h in out if "*" not in h["alias"]]  # info: return [ h for h in out if


# ====================================================
# SECTION: function terminal_argv
# What it does: terminal argv.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def terminal_argv(alias: str) -> list[str] | None:  # info: def terminal_argv
    for t, pre in (("ptyxis", ["ptyxis", "--new-window", "--"]), ("gnome-terminal", ["gnome-terminal", "--"]),  # info: for t , pre in ( ( "ptyxis"
                   ("x-terminal-emulator", ["x-terminal-emulator", "-e"])):  # info: call (
        if shutil.which(t):  # info: if shutil . which ( t ) :
            return pre + ["ssh", alias]  # info: return pre + [ "ssh" , alias ]
    return None  # info: return None


# ====================================================
# SECTION: function check_argv
# What it does: check argv.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def check_argv(alias: str) -> list[str]:  # info: def check_argv
    return ["timeout", "5", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", alias, "uptime"]  # info: return [ "timeout" , "5" , "ssh" ,
