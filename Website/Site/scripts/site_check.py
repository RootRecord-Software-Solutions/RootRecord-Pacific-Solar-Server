# ==============================================================================
# FILE: Website/Site/scripts/site_check.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Check the Site route manifest. Stdlib only. No network. No secrets. On demand."""  # info: """Check the Site route manifest. Stdlib only. No network. No secrets. On demand."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

# ====================================================
# SECTION: FORBIDDEN
# What it does: Set FORBIDDEN.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
FORBIDDEN = frozenset(  # info: set FORBIDDEN
    {  # info: {
        "token",  # info: "token" ,
        "credentials-file",  # info: "credentials-file" ,
        "credentials_file",  # info: "credentials_file" ,
        "credentialsfile",  # info: "credentialsfile" ,
        "tunnel-token",  # info: "tunnel-token" ,
        "password",  # info: "password" ,
        "secret",  # info: "secret" ,
        "api_key",  # info: "api_key" ,
        "apikey",  # info: "apikey" ,
    }  # info: }
)  # info: )
GLOBE = "http://127.0.0.1:8090"  # info: set GLOBE
SSH = "ssh://localhost:22"  # info: set SSH


# ====================================================
# SECTION: function ecosystem_root
# What it does: ecosystem root.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ecosystem_root() -> Path:  # info: def ecosystem_root
    for parent in Path(__file__).resolve().parents:  # info: for parent in Path ( __file__ ) .
        if (parent / "2 - RootRecord-Database").is_dir() and (parent / "1 - Servers").is_dir():  # info: if ( parent / "2 - RootRecord-Database" ) . is_dir
            return parent  # info: return parent
    raise SystemExit("ecosystem root not found")  # info: raise SystemExit ( "ecosystem root not found" )


# ====================================================
# SECTION: function manifest_path
# What it does: manifest path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def manifest_path() -> Path:  # info: def manifest_path
    return Path(__file__).resolve().parents[1] / "config" / "routes.yml"  # info: return Path ( __file__ ) . resolve (


# ====================================================
# SECTION: function parse_manifest
# What it does: Parse the small routes.yml subset this folder writes. Not a general YAML parser.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_manifest(text: str) -> dict:  # info: def parse_manifest
    """Parse the small routes.yml subset this folder writes. Not a general YAML parser."""  # info: """Parse the small routes.yml subset this folder writes. Not a general YAML parser."""
    data: dict = {"routes": []}  # info: set data
    current: dict | None = None  # info: set current
    for raw in text.splitlines():  # info: for raw in text . splitlines ( )
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():  # info: if not line . strip ( ) :
            continue  # info: continue
        if line.startswith("  - "):  # info: if line . startswith ( " - " ) :
            current = {}  # info: set current
            data["routes"].append(current)  # info: data [ "routes" ] . append ( current
            key, _, value = line.strip()[2:].partition(":")  # info: key , _ , value = line .
            current[key.strip()] = value.strip()  # info: current [ key . strip ( ) ]
            continue  # info: continue
        if line.startswith("    ") and current is not None:  # info: if line . startswith ( " " ) and
            key, _, value = line.strip().partition(":")  # info: key , _ , value = line .
            current[key.strip()] = value.strip()  # info: current [ key . strip ( ) ]
            continue  # info: continue
        if line[:1].isspace():  # info: if line [ : 1 ] . isspace
            raise ValueError("unexpected indent")  # info: raise ValueError ( "unexpected indent" )
        key, _, value = line.strip().partition(":")  # info: key , _ , value = line .
        name = key.strip()  # info: set name
        if not value.strip():  # info: if not value . strip ( ) :
            if name != "routes":  # info: if name != "routes" :
                data[name] = ""  # info: data [ name ] = ""
            current = None  # info: set current
            continue  # info: continue
        data[name] = value.strip()  # info: data [ name ] = value . strip
        current = None  # info: set current
    return data  # info: return data


# ====================================================
# SECTION: function key_names
# What it does: key names.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def key_names(obj: object):  # info: def key_names
    if isinstance(obj, dict):  # info: if isinstance ( obj , dict ) :
        for key, value in obj.items():  # info: for key , value in obj . items
            yield str(key)  # info: yield str ( key )
            yield from key_names(value)  # info: yield from key_names ( value )
    elif isinstance(obj, list):  # info: elif isinstance ( obj , list ) :
        for item in obj:  # info: for item in obj :
            yield from key_names(item)  # info: yield from key_names ( item )


# ====================================================
# SECTION: function problems
# What it does: problems.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def problems(data: dict) -> list[str]:  # info: def problems
    found: list[str] = []  # info: set found
    for key in key_names(data):  # info: for key in key_names ( data ) :
        folded = key.strip().lower()  # info: set folded
        if folded in FORBIDDEN or "token" in folded or "secret" in folded or "credential" in folded:  # info: if folded in FORBIDDEN or "token" in folded
            found.append(f"forbidden key {key}")  # info: found . append ( f" forbidden key { key
    if data.get("home_card") != "off":  # info: if data . get ( "home_card" ) !=
        found.append("home_card must be off")  # info: found . append ( "home_card must be off" )
    if data.get("vercel_site") != "one":  # info: if data . get ( "vercel_site" ) !=
        found.append("vercel_site must be one")  # info: found . append ( "vercel_site must be one" )
    if data.get("home_url") != "https://rootrecord.cloud/home":  # info: if data . get ( "home_url" ) !=
        found.append("home_url must be the one site home")  # info: found . append ( "home_url must be the one site home" )
    routes = data.get("routes")  # info: set routes
    if not isinstance(routes, list):  # info: if not isinstance ( routes , list )
        found.append("routes missing")  # info: found . append ( "routes missing" )
        return found  # info: return found
    seen: dict[str, dict] = {}  # info: set seen
    for route in routes:  # info: for route in routes :
        if not isinstance(route, dict):  # info: if not isinstance ( route , dict )
            found.append("route is not a map")  # info: found . append ( "route is not a map" )
            continue  # info: continue
        host = str(route.get("hostname") or "")  # info: set host
        if "avaivy" in host.lower():  # info: if "avaivy" in host . lower ( )
            found.append("avaivy hostname is not applied")  # info: found . append ( "avaivy hostname is not applied" )
        seen[host] = route  # info: seen [ host ] = route
    www = seen.get("www.rootrecord.cloud")  # info: set www
    ssh = seen.get("ssh.rootrecord.cloud")  # info: set ssh
    if www is None or www.get("keep") != "true" or www.get("service") != GLOBE or www.get("role") != "globe":  # info: if www is None or www . get
        found.append("www must stay on the globe")  # info: found . append ( "www must stay on the globe" )
    if ssh is None or ssh.get("keep") != "true" or ssh.get("service") != SSH or ssh.get("role") != "ssh":  # info: if ssh is None or ssh . get
        found.append("ssh route must stay")  # info: found . append ( "ssh route must stay" )
    extra = sorted(set(seen) - {"www.rootrecord.cloud", "ssh.rootrecord.cloud"})  # info: set extra
    if extra:  # info: if extra :
        found.append("unexpected hostname")  # info: found . append ( "unexpected hostname" )
    return found  # info: return found


# ====================================================
# SECTION: function write_result
# What it does: write result.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_result(root: Path) -> None:  # info: def write_result
    data_dir = root / "2 - RootRecord-Database" / "Communications" / "Site"  # info: set data_dir
    log_dir = root / "2 - RootRecord-Database" / "Logs" / "Communications" / "Site"  # info: set log_dir
    data_dir.mkdir(parents=True, exist_ok=True)  # info: data_dir . mkdir ( parents = True ,
    log_dir.mkdir(parents=True, exist_ok=True)  # info: log_dir . mkdir ( parents = True ,
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # info: set stamp
    payload = {  # info: set payload
        "ok": True,  # info: "ok" : True ,
        "checked_at": stamp,  # info: "checked_at" : stamp ,
        "home_card": "off",  # info: "home_card" : "off" ,
        "www": "globe",  # info: "www" : "globe" ,
        "ssh": "keep",  # info: "ssh" : "keep" ,
        "vercel_site": "one",  # info: "vercel_site" : "one" ,
    }  # info: }
    (data_dir / "routes-last.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: call (
    with (log_dir / "site_check.log").open("a", encoding="utf-8") as handle:  # info: with ( log_dir / "site_check.log" ) . open
        handle.write(f"{stamp} ok home_card=off www=globe\n")  # info: handle . write ( f" { stamp }


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(argv if argv is not None else sys.argv[1:])  # info: set args
    default = len(args) == 0  # info: set default
    path = manifest_path() if default else Path(args[0])  # info: set path
    if len(args) > 1:  # info: if len ( args ) > 1 :
        print(json.dumps({"ok": False, "error": "usage"}))  # info: call print
        return 2  # info: return 2
    try:  # info: try :
        data = parse_manifest(path.read_text(encoding="utf-8"))  # info: set data
    except Exception as exc:  # info: except Exception as exc :
        print(json.dumps({"ok": False, "error": type(exc).__name__}))  # info: call print
        return 2  # info: return 2
    bad = problems(data)  # info: set bad
    if bad:  # info: if bad :
        print(json.dumps({"ok": False, "error": bad[0]}))  # info: call print
        return 2  # info: return 2
    if default:  # info: if default :
        write_result(ecosystem_root())  # info: call write_result
    print(json.dumps({"ok": True, "home_card": "off", "www": "globe"}))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
