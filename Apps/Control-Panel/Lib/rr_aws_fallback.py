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
from __future__ import annotations

import json
import re
from pathlib import Path

CATALOG = Path(__file__).resolve().parent / "rr_aws_fallback.json"
ID_RE = re.compile(r"^[a-z0-9_]{2,40}$")
MODES = ("dry-run", "write")


def load(path: Path = CATALOG) -> dict:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {"functions": [], "budget": {}}
    d.setdefault("functions", [])
    d.setdefault("budget", {})
    return d


def budget(cat: dict, enabled: dict[str, bool], ram_total_mb: int) -> dict:
    """Sum of estimated RAM (resident + transient peaks) and disk caps for the enabled set vs the floors."""
    b = cat.get("budget", {})
    base = int(b.get("baseline_os_mb", 300))
    ram = sum(int(f.get("ram_mb", 0)) for f in cat["functions"] if enabled.get(f["id"]))
    disk = sum(int(f.get("disk_mb", 0)) for f in cat["functions"] if enabled.get(f["id"]))
    free = ram_total_mb - base - ram
    floor = int(b.get("ram_floor_mb", 512))
    return {"baseline_mb": base, "functions_ram_mb": ram, "functions_disk_mb": disk,
            "ram_total_mb": ram_total_mb, "ram_free_est_mb": free, "ram_floor_mb": floor, "ram_ok": free >= floor,
            "disk_floor_mb": int(b.get("disk_floor_mb", 1536))}


def defaults(cat: dict) -> dict[str, bool]:
    return {f["id"]: bool(f.get("default_on")) for f in cat["functions"]}


def status_argv(alias: str, remote_root: str) -> list[str]:
    """Read-only: flag files, mode, MemAvailable, disk free. Output is key=value lines."""
    script = (f'D={remote_root}; if [ -d "$D/flags" ]; then echo deployed=1; for f in "$D"/flags/*; do '
              '[ -f "$f" ] && echo "flag.$(basename "$f")=$(head -c 8 "$f")"; done; '
              '[ -f "$D/state/mode" ] && echo "mode=$(head -c 20 "$D/state/mode")"; '
              'echo "release=$(basename "$(dirname "$(readlink "$D/app")")")"; else echo deployed=0; fi; '
              "awk '/MemTotal/{print \"mem_total_mb=\" int($2/1024)} /MemAvailable/{print \"mem_avail_mb=\" int($2/1024)}' /proc/meminfo; "
              "df -Pm / | awk 'NR==2{print \"disk_free_mb=\" $4}'")
    return ["timeout", "10", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", alias, script]


def parse_status(out: str) -> dict:
    st = {"flags": {}}
    for ln in (out or "").splitlines():
        if "=" not in ln:
            continue
        k, v = ln.split("=", 1)
        k, v = k.strip(), v.strip()
        if k.startswith("flag."):
            st["flags"][k[5:]] = v in ("1", "on", "true")
        elif k in ("deployed", "mem_total_mb", "mem_avail_mb", "disk_free_mb"):
            try:
                st[k] = int(v)
            except ValueError:
                pass
        elif k in ("mode", "release"):
            st[k] = v
    return st


def write_script(fn_id: str, on: bool, remote_root: str) -> str:
    if not ID_RE.match(fn_id):
        raise ValueError(f"invalid function id {fn_id!r}")
    val = "1" if on else "0"
    return (f'set -eu; D={remote_root}; F={fn_id}; test -d "$D/flags" || {{ echo "fallback runtime not deployed"; exit 3; }}; '
            'TS=$(TZ=Pacific/Honolulu date +%Y%m%d-%H%M%S); B="$HOME/rootrecord/bin.bak-fallback-flags-$TS"; '
            'mkdir -p "$B"; cp -a "$D/flags/." "$B/"; '
            f'printf "%s\\n" {val} > "$D/flags/.$F.tmp"; mv -f "$D/flags/.$F.tmp" "$D/flags/$F"; '
            'echo "ok $F=$(cat "$D/flags/$F") backup=$B"')


def write_argv(alias: str, fn_id: str, on: bool, remote_root: str) -> list[str]:
    return ["timeout", "15", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", alias,
            write_script(fn_id, on, remote_root)]


def preview(alias: str, fn_id: str, on: bool, remote_root: str) -> str:
    return f"ssh -o BatchMode=yes {alias} '<backup {remote_root}/flags -> ~/rootrecord/bin.bak-fallback-flags-<HST ts>/; " \
           f"atomic write {remote_root}/flags/{fn_id} = {'1' if on else '0'}>'"
