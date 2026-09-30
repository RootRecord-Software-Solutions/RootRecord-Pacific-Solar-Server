"""rr_aws_fallback.py — logic for Root Monitor's "AWS Fallback" page (added 2026-09-29, Phase 1).

INFO — MUST HAVE (future agents):
- Catalog = Lib/rr_aws_fallback.json (function id, default, RAM/disk/net estimates). Design: Library
  08-ideas/2026-09-29-aws-fallback-rebuild.md. The desk is canonical; AWS only holds per-function flag files.
- DEFAULT MODE IS "dry-run" (settings.json "aws_fallback_mode"); the desk settings.json is set to "write" since
  2026-09-29 16:05 HST (Phase 2 runtime deployed, Alexander approved AWS changes). In dry-run nothing is sent to AWS except the
  read-only Status button. "write" mode is a sign-off item AND needs the AWS runtime (remote flags/ dir) to exist;
  the remote write script refuses (exit 3) until then.
- A write = one SSH call: validate id -> dated backup of flags/ on AWS -> atomic write of flags/<id> ("1"/"0").
  Nothing is restarted by the panel; the AWS path unit / runner picks the change up.
- No secrets are read, shown or sent. SSH uses BatchMode and the ~/.ssh/config alias only.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
from pathlib import Path  # info: from pathlib import Path

CATALOG = Path(__file__).resolve().parent / "rr_aws_fallback.json"  # info: set CATALOG
ID_RE = re.compile(r"^[a-z0-9_]{2,40}$")  # info: set ID_RE
MODES = ("dry-run", "write")  # info: set MODES


# ====================================================
# SECTION: function load
# What it does: load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load(path: Path = CATALOG) -> dict:  # info: def load
    try:  # info: try :
        d = json.loads(path.read_text(encoding="utf-8"))  # info: set d
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        d = {"functions": [], "budget": {}}  # info: set d
    d.setdefault("functions", [])  # info: d . setdefault ( "functions" , [ ]
    d.setdefault("budget", {})  # info: d . setdefault ( "budget" , { }
    return d  # info: return d


# ====================================================
# SECTION: function budget
# What it does: Sum of estimated RAM (resident + transient peaks) and disk caps for the enabled set vs the floors.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def budget(cat: dict, enabled: dict[str, bool], ram_total_mb: int) -> dict:  # info: def budget
    """Sum of estimated RAM (resident + transient peaks) and disk caps for the enabled set vs the floors."""  # info: """Sum of estimated RAM (resident + transient peaks) and disk caps for the enabled set vs the floors."""
    b = cat.get("budget", {})  # info: set b
    base = int(b.get("baseline_os_mb", 300))  # info: set base
    ram = sum(int(f.get("ram_mb", 0)) for f in cat["functions"] if enabled.get(f["id"]))  # info: set ram
    disk = sum(int(f.get("disk_mb", 0)) for f in cat["functions"] if enabled.get(f["id"]))  # info: set disk
    free = ram_total_mb - base - ram  # info: set free
    floor = int(b.get("ram_floor_mb", 512))  # info: set floor
    return {"baseline_mb": base, "functions_ram_mb": ram, "functions_disk_mb": disk,  # info: return { "baseline_mb" : base , "functions_ram_mb" :
            "ram_total_mb": ram_total_mb, "ram_free_est_mb": free, "ram_floor_mb": floor, "ram_ok": free >= floor,  # info: "ram_total_mb" : ram_total_mb , "ram_free_est_mb" : free ,
            "disk_floor_mb": int(b.get("disk_floor_mb", 1536))}  # info: "disk_floor_mb" : int ( b . get (


# ====================================================
# SECTION: function defaults
# What it does: defaults.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def defaults(cat: dict) -> dict[str, bool]:  # info: def defaults
    return {f["id"]: bool(f.get("default_on")) for f in cat["functions"]}  # info: return { f [ "id" ] : bool


# ====================================================
# SECTION: function status_argv
# What it does: Read-only: flag files, mode, MemAvailable, disk free. Output is key=value lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def status_argv(alias: str, remote_root: str) -> list[str]:  # info: def status_argv
    """Read-only: flag files, mode, MemAvailable, disk free. Output is key=value lines."""  # info: """Read-only: flag files, mode, MemAvailable, disk free. Output is key=value lines."""
    script = (f'D={remote_root}; if [ -d "$D/flags" ]; then echo deployed=1; for f in "$D"/flags/*; do '  # info: set script
              '[ -f "$f" ] && echo "flag.$(basename "$f")=$(head -c 8 "$f")"; done; '  # info: '[ -f "$f" ] && echo "flag.$(basename "$f")=$(head -c 8 "$f")"; done; '
              '[ -f "$D/state/mode" ] && echo "mode=$(head -c 20 "$D/state/mode")"; '  # info: '[ -f "$D/state/mode" ] && echo "mode=$(head -c 20 "$D/state/mode")"; '
              'echo "release=$(basename "$(dirname "$(readlink "$D/app")")")"; else echo deployed=0; fi; '  # info: 'echo "release=$(basename "$(dirname "$(readlink "$D/app")")")"; else echo deployed=0; fi; '
              "awk '/MemTotal/{print \"mem_total_mb=\" int($2/1024)} /MemAvailable/{print \"mem_avail_mb=\" int($2/1024)}' /proc/meminfo; "  # info: "awk '/MemTotal/{print \"mem_total_mb=\" int($2/1024)} /MemAvailable/{print \"mem_avail_mb=\" int($2/1024)}' /
              "df -Pm / | awk 'NR==2{print \"disk_free_mb=\" $4}'")  # info: "df -Pm / | awk 'NR==2{print \"disk_free_mb=\" $4}'" )
    return ["timeout", "10", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", alias, script]  # info: return [ "timeout" , "10" , "ssh" ,


# ====================================================
# SECTION: function parse_status
# What it does: parse status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_status(out: str) -> dict:  # info: def parse_status
    st = {"flags": {}}  # info: set st
    for ln in (out or "").splitlines():  # info: for ln in ( out or "" )
        if "=" not in ln:  # info: if "=" not in ln :
            continue  # info: continue
        k, v = ln.split("=", 1)  # info: k , v = ln . split (
        k, v = k.strip(), v.strip()  # info: k , v = k . strip (
        if k.startswith("flag."):  # info: if k . startswith ( "flag." ) :
            st["flags"][k[5:]] = v in ("1", "on", "true")  # info: st [ "flags" ] [ k [ 5
        elif k in ("deployed", "mem_total_mb", "mem_avail_mb", "disk_free_mb"):  # info: elif k in ( "deployed" , "mem_total_mb" ,
            try:  # info: try :
                st[k] = int(v)  # info: st [ k ] = int ( v
            except ValueError:  # info: except ValueError :
                pass  # info: pass
        elif k in ("mode", "release"):  # info: elif k in ( "mode" , "release" )
            st[k] = v  # info: st [ k ] = v
    return st  # info: return st


# ====================================================
# SECTION: function write_script
# What it does: write script.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_script(fn_id: str, on: bool, remote_root: str) -> str:  # info: def write_script
    if not ID_RE.match(fn_id):  # info: if not ID_RE . match ( fn_id )
        raise ValueError(f"invalid function id {fn_id!r}")  # info: raise ValueError ( f" invalid function id { fn_id !
    val = "1" if on else "0"  # info: set val
    return (f'set -eu; D={remote_root}; F={fn_id}; test -d "$D/flags" || {{ echo "fallback runtime not deployed"; exit 3; }}; '  # info: return ( f' set -eu; D= { remote_root } ; F=
            'TS=$(TZ=Pacific/Honolulu date +%Y%m%d-%H%M%S); B="$HOME/rootrecord/bin.bak-fallback-flags-$TS"; '  # info: 'TS=$(TZ=Pacific/Honolulu date +%Y%m%d-%H%M%S); B="$HOME/rootrecord/bin.bak-fallback-flags-$TS"; '
            'mkdir -p "$B"; cp -a "$D/flags/." "$B/"; '  # info: 'mkdir -p "$B"; cp -a "$D/flags/." "$B/"; '
            f'printf "%s\\n" {val} > "$D/flags/.$F.tmp"; mv -f "$D/flags/.$F.tmp" "$D/flags/$F"; '  # info: f' printf "%s\\n" { val } > "$D/flags/.$F.tmp"; mv -f "$D/flags/.$F.tmp" "$D/flags/$F"; '
            'echo "ok $F=$(cat "$D/flags/$F") backup=$B"')  # info: 'echo "ok $F=$(cat "$D/flags/$F") backup=$B"' )


# ====================================================
# SECTION: function write_argv
# What it does: write argv.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_argv(alias: str, fn_id: str, on: bool, remote_root: str) -> list[str]:  # info: def write_argv
    return ["timeout", "15", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", alias,  # info: return [ "timeout" , "15" , "ssh" ,
            write_script(fn_id, on, remote_root)]  # info: call write_script


# ====================================================
# SECTION: function preview
# What it does: preview.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def preview(alias: str, fn_id: str, on: bool, remote_root: str) -> str:  # info: def preview
    return f"ssh -o BatchMode=yes {alias} '<backup {remote_root}/flags -> ~/rootrecord/bin.bak-fallback-flags-<HST ts>/; " \
           f"atomic write {remote_root}/flags/{fn_id} = {'1' if on else '0'}>'"  # info: f" atomic write { remote_root } /flags/ { fn_id
