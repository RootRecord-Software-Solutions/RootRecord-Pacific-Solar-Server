#!/usr/bin/env python3
"""Check the Site route manifest. Stdlib only. No network. No secrets. On demand."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FORBIDDEN = frozenset(
    {
        "token",
        "credentials-file",
        "credentials_file",
        "credentialsfile",
        "tunnel-token",
        "password",
        "secret",
        "api_key",
        "apikey",
    }
)
GLOBE = "http://127.0.0.1:8090"
SSH = "ssh://localhost:22"


def ecosystem_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "2 - RootRecord-Database").is_dir() and (parent / "1 - Servers").is_dir():
            return parent
    raise SystemExit("ecosystem root not found")


def manifest_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "routes.yml"


def parse_manifest(text: str) -> dict:
    """Parse the small routes.yml subset this folder writes. Not a general YAML parser."""
    data: dict = {"routes": []}
    current: dict | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  - "):
            current = {}
            data["routes"].append(current)
            key, _, value = line.strip()[2:].partition(":")
            current[key.strip()] = value.strip()
            continue
        if line.startswith("    ") and current is not None:
            key, _, value = line.strip().partition(":")
            current[key.strip()] = value.strip()
            continue
        if line[:1].isspace():
            raise ValueError("unexpected indent")
        key, _, value = line.strip().partition(":")
        name = key.strip()
        if not value.strip():
            if name != "routes":
                data[name] = ""
            current = None
            continue
        data[name] = value.strip()
        current = None
    return data


def key_names(obj: object):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key)
            yield from key_names(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from key_names(item)


def problems(data: dict) -> list[str]:
    found: list[str] = []
    for key in key_names(data):
        folded = key.strip().lower()
        if folded in FORBIDDEN or "token" in folded or "secret" in folded or "credential" in folded:
            found.append(f"forbidden key {key}")
    if data.get("home_card") != "off":
        found.append("home_card must be off")
    if data.get("vercel_site") != "one":
        found.append("vercel_site must be one")
    if data.get("home_url") != "https://rootrecord.cloud/home":
        found.append("home_url must be the one site home")
    routes = data.get("routes")
    if not isinstance(routes, list):
        found.append("routes missing")
        return found
    seen: dict[str, dict] = {}
    for route in routes:
        if not isinstance(route, dict):
            found.append("route is not a map")
            continue
        host = str(route.get("hostname") or "")
        if "avaivy" in host.lower():
            found.append("avaivy hostname is not applied")
        seen[host] = route
    www = seen.get("www.rootrecord.cloud")
    ssh = seen.get("ssh.rootrecord.cloud")
    if www is None or www.get("keep") != "true" or www.get("service") != GLOBE or www.get("role") != "globe":
        found.append("www must stay on the globe")
    if ssh is None or ssh.get("keep") != "true" or ssh.get("service") != SSH or ssh.get("role") != "ssh":
        found.append("ssh route must stay")
    extra = sorted(set(seen) - {"www.rootrecord.cloud", "ssh.rootrecord.cloud"})
    if extra:
        found.append("unexpected hostname")
    return found


def write_result(root: Path) -> None:
    data_dir = root / "2 - RootRecord-Database" / "Communications" / "Site"
    log_dir = root / "2 - RootRecord-Database" / "Logs" / "Communications" / "Site"
    data_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "ok": True,
        "checked_at": stamp,
        "home_card": "off",
        "www": "globe",
        "ssh": "keep",
        "vercel_site": "one",
    }
    (data_dir / "routes-last.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with (log_dir / "site_check.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} ok home_card=off www=globe\n")


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    default = len(args) == 0
    path = manifest_path() if default else Path(args[0])
    if len(args) > 1:
        print(json.dumps({"ok": False, "error": "usage"}))
        return 2
    try:
        data = parse_manifest(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__}))
        return 2
    bad = problems(data)
    if bad:
        print(json.dumps({"ok": False, "error": bad[0]}))
        return 2
    if default:
        write_result(ecosystem_root())
    print(json.dumps({"ok": True, "home_card": "off", "www": "globe"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
