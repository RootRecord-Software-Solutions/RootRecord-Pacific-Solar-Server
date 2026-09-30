# ==============================================================================
# FILE: System/scripts/state-aggregate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Build rootrecord-state.json from live sources. Does not send, launch, or restart anything."""
from __future__ import annotations  # info: from __future__ import annotations
import importlib.util, json, os, re, subprocess  # info: import importlib . util , json , os , re , subprocess
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

PACIFIC = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server")  # info: set PACIFIC
DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DB
ECOSYSTEM = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ECOSYSTEM
OUT = DB / "System" / "status" / "rootrecord-state.json"  # info: set OUT
BRIEF = DB / "System" / "status" / "rootrecord-state-brief.txt"  # info: set BRIEF
REGISTRY = PACIFIC / "System" / "config" / "program-registry.json"  # info: set REGISTRY
JOBS = PACIFIC / "Automations" / "scripts" / "jobs.py"  # info: set JOBS
RELAY_CONF = PACIFIC / "Communications" / "telegram" / "config" / "relay.conf"  # info: set RELAY_CONF
REPOS = PACIFIC / "Github" / "scripts" / "repos.conf"  # info: set REPOS
HOST_STATUS = DB / "System" / "status" / "system-status.json"  # info: set HOST_STATUS
DESK = DB / "Intake" / "desk-live.txt"  # info: set DESK
ENERGY = DB / "Energy"  # info: set ENERGY
SCHEMA = 1  # info: set SCHEMA

# ====================================================
# SECTION: function now_local
# What it does: Current local time as an ISO string. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_local() -> str:  # info: def now_local
    return datetime.now().astimezone().isoformat(timespec="seconds")  # info: return datetime . now ( ) . astimezone ( ) . isoformat

# ====================================================
# SECTION: function why
# What it does: A why-not record. Does not change any gate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def why(status: str, kind: str, reason: str, blocked_by: str = "", enable_condition: str = "") -> dict:  # info: def why
    return {"status": status, "kind": kind, "reason": reason, "blocked_by": blocked_by, "enable_condition": enable_condition}  # info: return { "status" : status , "kind" : kind

# ====================================================
# SECTION: function obs
# What it does: One measured or declared field with source and confidence. Does not invent a value.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def obs(value, source: str, confidence: str, **extra) -> dict:  # info: def obs
    row = {"value": value, "source": source, "confidence": confidence, "observed_at": now_local()}  # info: set row
    row.update(extra)  # info: row . update ( extra )
    return row  # info: return row

# ====================================================
# SECTION: function load_json
# What it does: Read one JSON file, or None. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_json(path: Path):  # info: def load_json
    try:  # info: try :
        return json.loads(path.read_text(encoding="utf-8"))  # info: return json . loads ( path . read_text
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return None  # info: return None

# ====================================================
# SECTION: function kv_file
# What it does: Read key=value lines. Skips comments. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def kv_file(path: Path) -> dict:  # info: def kv_file
    out = {}  # info: set out
    try:  # info: try :
        lines = path.read_text(encoding="utf-8").splitlines()  # info: set lines
    except OSError:  # info: except OSError :
        return out  # info: return out
    for ln in lines:  # info: for ln in lines :
        if not ln.strip() or ln.strip().startswith("#") or "=" not in ln:  # info: if not ln . strip ( ) or ln . strip ( ) . startswith
            continue  # info: continue
        k, v = ln.split("=", 1)  # info: k , v = ln . split ( "=" , 1 )
        out[k.strip()] = v.strip()  # info: out [ k . strip ( ) ] = v . strip ( )
    return out  # info: return out

# ====================================================
# SECTION: function process_cmds
# What it does: List pid and command line from /proc. Does not send signals.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def process_cmds() -> list[tuple[int, str]]:  # info: def process_cmds
    found = []  # info: set found
    for name in os.listdir("/proc"):  # info: for name in os . listdir ( "/proc" )
        if not name.isdigit():  # info: if not name . isdigit ( )
            continue  # info: continue
        try:  # info: try :
            raw = Path(f"/proc/{name}/cmdline").read_bytes()  # info: set raw
        except OSError:  # info: except OSError :
            continue  # info: continue
        cmd = raw.replace(b"\0", b" ").decode("utf-8", "replace").strip()  # info: set cmd
        if cmd:  # info: if cmd :
            found.append((int(name), cmd))  # info: found . append ( ( int ( name ) , cmd ) )
    return found  # info: return found

# ====================================================
# SECTION: function match_procs
# What it does: Pids whose command contains a needle. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def match_procs(rows: list[tuple[int, str]], needle: str) -> list[int]:  # info: def match_procs
    return [pid for pid, cmd in rows if needle in cmd]  # info: return [ pid for pid , cmd in rows if needle in cmd ]

# ====================================================
# SECTION: function poller_env
# What it does: RR_ flags from the poller process. Values are not returned, only names that are set. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poller_flags(rows: list[tuple[int, str]]) -> tuple[dict, str]:  # info: def poller_flags
    pids = [pid for pid, cmd in rows if "rootserver_poller.py" in cmd and "poller-watch" not in cmd]  # info: set pids
    if not pids:  # info: if not pids :
        return {}, "no_poller"  # info: return { } , "no_poller"
    try:  # info: try :
        raw = Path(f"/proc/{pids[0]}/environ").read_bytes()  # info: set raw
    except OSError:  # info: except OSError :
        return {}, "unreadable"  # info: return { } , "unreadable"
    flags = {}  # info: set flags
    for item in raw.split(b"\0"):  # info: for item in raw . split ( b"\0" )
        if not item.startswith(b"RR_") or b"=" not in item:  # info: if not item . startswith ( b"RR_" ) or b"=" not in item
            continue  # info: continue
        k, v = item.split(b"=", 1)  # info: k , v = item . split ( b"=" , 1 )
        flags[k.decode()] = "set" if v else "empty"  # info: flags [ k . decode ( ) ] = "set" if v else "empty"
    return flags, "process_environ"  # info: return flags , "process_environ"

# ====================================================
# SECTION: function load_jobs
# What it does: Import the poller catalog. Does not start the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_jobs():  # info: def load_jobs
    spec = importlib.util.spec_from_file_location("rr_jobs_catalog", JOBS)  # info: set spec
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    buckets = {  # info: set buckets
        "boot": mod.ON_BOOT,  # info: "boot" : mod . ON_BOOT ,
        "once": mod.ONCE_AT_START,  # info: "once" : mod . ONCE_AT_START ,
        "seconds": mod.EVERY_SECONDS,  # info: "seconds" : mod . EVERY_SECONDS ,
        "minute": mod.EVERY_MINUTE,  # info: "minute" : mod . EVERY_MINUTE ,
        "hour": mod.EVERY_HOUR,  # info: "hour" : mod . EVERY_HOUR ,
        "at": mod.ON_AT,  # info: "at" : mod . ON_AT ,
    }  # info: }
    return buckets  # info: return buckets

# ====================================================
# SECTION: function job_row
# What it does: One catalog job without commands or secrets. Does not enable the job.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def job_row(bucket: str, job: dict) -> dict:  # info: def job_row
    desc = str(job.get("description") or "")[:240]  # info: set desc
    enabled = bool(job.get("enabled"))  # info: set enabled
    flag = ""  # info: set flag
    found = re.search(r"RR_[A-Z0-9_]+", desc)  # info: set found
    if found:  # info: if found :
        flag = found.group(0)  # info: set flag
    row = {  # info: set row
        "id": job.get("id"),  # info: "id" : job . get ( "id" ) ,
        "schedule": bucket,  # info: "schedule" : bucket ,
        "enabled": enabled,  # info: "enabled" : enabled ,
        "interval_sec": job.get("interval_sec"),  # info: "interval_sec" : job . get ( "interval_sec" ) ,
        "at_times": job.get("at_times"),  # info: "at_times" : job . get ( "at_times" ) ,
        "needs_internet": bool(job.get("needs_internet")),  # info: "needs_internet" : bool ( job . get ( "needs_internet" ) ) ,
        "description": desc,  # info: "description" : desc ,
        "source": "jobs.py",  # info: "source" : "jobs.py" ,
        "confidence": "configured",  # info: "confidence" : "configured" ,
        "observed_at": now_local(),  # info: "observed_at" : now_local ( ) ,
    }  # info: }
    if not enabled:  # info: if not enabled :
        row["why_not"] = why("disabled", "gated" if flag else "disabled", "Catalog job is off. Leave it off.", flag, f"{flag}=1 at poller start" if flag else "")  # info: row [ "why_not" ] = why
    return row  # info: return row

# ====================================================
# SECTION: function host_block
# What it does: Host identity and the latest system-status metrics. Does not sample a new average.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host_block() -> dict:  # info: def host_block
    doc = load_json(HOST_STATUS) or {}  # info: set doc
    current = doc.get("current") if isinstance(doc, dict) else None  # info: set current
    metrics = (current or {}).get("metrics") if isinstance(current, dict) else {}  # info: set metrics
    picked = {}  # info: set picked
    if isinstance(metrics, dict):  # info: if isinstance ( metrics , dict )
        for key in ("cpu_percent", "mem_used_percent", "load1", "load5", "load15"):  # info: for key in ( "cpu_percent" , "mem_used_percent"
            row = metrics.get(key) or {}  # info: set row
            if isinstance(row, dict) and row.get("value") is not None:  # info: if isinstance ( row , dict ) and row . get ( "value" )
                picked[key] = row.get("value")  # info: picked [ key ] = row . get ( "value" )
    try:  # info: try :
        uname = os.uname()  # info: set uname
        os_name = f"{uname.sysname} {uname.release}"  # info: set os_name
        host = uname.nodename  # info: set host
    except AttributeError:  # info: except AttributeError :
        os_name, host = "unknown", "unknown"  # info: os_name , host = "unknown" , "unknown"
    return {  # info: return {
        "host": obs(host, "uname", "live"),  # info: "host" : obs ( host , "uname" , "live" ) ,
        "os": obs(os_name, "uname", "live"),  # info: "os" : obs ( os_name , "uname" , "live" ) ,
        "resources": obs(picked or None, "system-status.json", "recent" if picked else "unknown", measured_at=(current or {}).get("observed_at")),  # info: "resources" : obs ( picked or None , "system-status.json" , "recent" if picked else "unknown"
    }  # info: }

# ====================================================
# SECTION: function power_block
# What it does: Latest EcoFlow SOC files. Does not open Bluetooth.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def power_block() -> dict:  # info: def power_block
    packs = {}  # info: set packs
    for key, name in (("delta2", "Delta 2"), ("river2pro", "River 2 Pro")):  # info: for key , name in ( ( "delta2" , "Delta 2" ) , ( "river2pro" , "River 2 Pro" ) )
        soc = load_json(ENERGY / "soc" / f"{key}-last.json")  # info: set soc
        watts = load_json(ENERGY / "watts" / f"{key}-last.json")  # info: set watts
        if not isinstance(soc, dict) or "soc" not in soc:  # info: if not isinstance ( soc , dict ) or "soc" not in soc
            packs[key] = obs(None, f"Energy/soc/{key}-last.json", "unknown", name=name, why_not=why("unknown", "unavailable", "SOC file missing", "", ""))  # info: packs [ key ] = obs
            continue  # info: continue
        watt_keep = {}  # info: set watt_keep
        if isinstance(watts, dict):  # info: if isinstance ( watts , dict )
            for src in ("solar_input_power", "ac_output_power", "ac_input_power", "usbc_output_power", "charge_source"):  # info: for src in ( "solar_input_power" , "ac_output_power"
                if src in watts:  # info: if src in watts :
                    watt_keep[src] = watts.get(src)  # info: watt_keep [ src ] = watts . get ( src )
        packs[key] = obs({"name": name, "soc_percent": soc.get("soc"), "at": soc.get("at"), "watts": watt_keep}, f"Energy/soc/{key}-last.json", "recent")  # info: packs [ key ] = obs
    return packs  # info: return packs

# ====================================================
# SECTION: function service_proc
# What it does: Running or stopped from a process scan. Does not start the service.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def service_proc(name: str, pids: list[int], extra: dict | None = None) -> dict:  # info: def service_proc
    row = {"service": name, "status": "running" if pids else "stopped", "pids": pids, "source": "process_scan", "confidence": "live", "observed_at": now_local()}  # info: set row
    if extra:  # info: if extra :
        row.update(extra)  # info: row . update ( extra )
    if not pids and not extra:  # info: if not pids and not extra :
        row["why_not"] = why("stopped", "unknown", "No matching process. This scan cannot tell a crash from something that is not a daemon.", "", "")  # info: row [ "why_not" ] = why
    return row  # info: return row

# ====================================================
# SECTION: function repos_block
# What it does: Catalog rows plus branch name. Does not push or commit.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def repos_block() -> list[dict]:  # info: def repos_block
    rows = []  # info: set rows
    try:  # info: try :
        text = REPOS.read_text(encoding="utf-8").splitlines()  # info: set text
    except OSError:  # info: except OSError :
        return [obs(None, "repos.conf", "unknown", why_not=why("unknown", "unavailable", "repos.conf unreadable", "", ""))]  # info: return [ obs ( None , "repos.conf" , "unknown"
    for ln in text:  # info: for ln in text :
        if not ln.strip() or ln.strip().startswith("#"):  # info: if not ln . strip ( ) or ln . strip ( ) . startswith
            continue  # info: continue
        parts = ln.split("\t")  # info: set parts
        if len(parts) < 5:  # info: if len ( parts ) < 5 :
            continue  # info: continue
        rid, enabled, mode, local, slug = parts[:5]  # info: rid , enabled , mode , local , slug = parts [ : 5 ]
        branch, dirty = "unknown", None  # info: branch , dirty = "unknown" , None
        if Path(local).is_dir():  # info: if Path ( local ) . is_dir ( )
            try:  # info: try :
                branch = subprocess.check_output(["git", "-C", local, "rev-parse", "--abbrev-ref", "HEAD"], text=True, timeout=8, stderr=subprocess.DEVNULL).strip()  # info: set branch
                porcelain = subprocess.check_output(["git", "-C", local, "status", "--porcelain"], text=True, timeout=20, stderr=subprocess.DEVNULL)  # info: set porcelain
                dirty = len([x for x in porcelain.splitlines() if x.strip()])  # info: set dirty
            except (OSError, subprocess.SubprocessError):  # info: except ( OSError , subprocess . SubprocessError )
                branch = "unknown"  # info: set branch
        rows.append({"id": rid, "enabled": enabled == "1", "mode": mode, "slug": slug, "branch": branch, "dirty_files": dirty, "source": "repos.conf", "confidence": "configured" if branch == "unknown" else "live", "observed_at": now_local()})  # info: rows . append ( { "id" : rid , "enabled" : enabled == "1"
    return rows  # info: return rows

# ====================================================
# SECTION: function model_names
# What it does: Installed Ollama model names. Does not load a model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def model_names() -> dict:  # info: def model_names
    try:  # info: try :
        text = subprocess.check_output(["ollama", "list"], text=True, timeout=15, stderr=subprocess.DEVNULL)  # info: set text
    except (OSError, subprocess.SubprocessError):  # info: except ( OSError , subprocess . SubprocessError )
        return obs(None, "ollama list", "unknown", why_not=why("unknown", "unavailable", "ollama list failed", "", ""))  # info: return obs ( None , "ollama list" , "unknown"
    names = []  # info: set names
    for ln in text.splitlines()[1:]:  # info: for ln in text . splitlines ( ) [ 1 : ]
        name = ln.split()[0] if ln.split() else ""  # info: set name
        if name:  # info: if name :
            names.append(name)  # info: names . append ( name )
    return obs(names, "ollama list", "live")  # info: return obs ( names , "ollama list" , "live" )

# ====================================================
# SECTION: function programs_block
# What it does: Merge the registry with catalog enabled flags. Does not launch a program.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def programs_block(job_by_id: dict) -> list[dict]:  # info: def programs_block
    reg = load_json(REGISTRY) or {}  # info: set reg
    out = []  # info: set out
    for prog in reg.get("programs") or []:  # info: for prog in reg . get ( "programs" ) or [ ]
        row = dict(prog)  # info: set row
        job = job_by_id.get(row.get("owner_job") or "")  # info: set job
        row["catalog_enabled"] = None if job is None else job.get("enabled")  # info: row [ "catalog_enabled" ] = None if job is None else job . get ( "enabled" )
        row["status"] = "not_launchable"  # info: row [ "status" ] = "not_launchable"
        row["source"] = "program-registry.json"  # info: row [ "source" ] = "program-registry.json"
        row["confidence"] = "configured"  # info: row [ "confidence" ] = "configured"
        row["observed_at"] = now_local()  # info: row [ "observed_at" ] = now_local ( )
        row["last_run"] = None  # info: row [ "last_run" ] = None
        row["last_result"] = "unknown"  # info: row [ "last_result" ] = "unknown"
        row["last_result_why"] = why("unknown", "not_implemented", "No program run log is read yet. unknown is not success.", "", "")  # info: row [ "last_result_why" ] = why
        out.append(row)  # info: out . append ( row )
    return out  # info: return out

# ====================================================
# SECTION: function capabilities
# What it does: Declared gates. Does not flip any flag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def capabilities(relay: dict, flags: dict) -> dict:  # info: def capabilities
    def flag_on(name: str) -> bool:  # info: def flag_on
        return flags.get(name) == "set"  # info: return flags . get ( name ) == "set"
    sandbox_on = relay.get("SANDBOX_REPLIES") == "1"  # info: set sandbox_on
    return {  # info: return {
        "available": [  # info: "available" : [
            {"id": "sandbox_replies", "status": "available" if sandbox_on else "disabled", "source": "relay.conf", "confidence": "configured", "why_not": None if sandbox_on else why("disabled", "disabled", "SANDBOX_REPLIES is not 1", "SANDBOX_REPLIES", "SANDBOX_REPLIES=1")},  # info: { "id" : "sandbox_replies" , "status" : "available" if sandbox_on else "disabled"
            {"id": "npu_council_infer", "status": "available", "source": "ensure-relay.sh", "confidence": "configured", "note": "On demand llama3.2:3b, context 4096. Not resident."},  # info: { "id" : "npu_council_infer" , "status" : "available" , "source" : "ensure-relay.sh"
        ],  # info: ] ,
        "gated": [  # info: "gated" : [
            {"id": "live_council_replies", "why_not": why("gated", "gated", "Live council stays quiet on purpose.", "RR_RELAY_REPLIES", "RR_RELAY_REPLIES=1")},  # info: { "id" : "live_council_replies" , "why_not" : why
            {"id": "private_dm_replies", "why_not": why("gated", "gated", "Private DMs stay quiet on purpose.", "RR_RELAY_REPLIES", "RR_RELAY_REPLIES=1")},  # info: { "id" : "private_dm_replies" , "why_not" : why
            {"id": "quake_telegram_send", "why_not": why("gated", "gated", "Quake posts do not send.", "RR_COUNCIL_QUAKE_SEND", "RR_COUNCIL_QUAKE_SEND=1")},  # info: { "id" : "quake_telegram_send" , "why_not" : why
            {"id": "bruce_stats_send", "why_not": why("gated", "gated", "Bruce stats do not send.", "RR_BRUCE_STATS_SEND", "RR_BRUCE_STATS_SEND=1")},  # info: { "id" : "bruce_stats_send" , "why_not" : why
            {"id": "agent_program_launch", "why_not": why("not_implemented", "not_implemented", "No agent may launch a program from this snapshot.", "agent_execution_layer", "Alexander adds an execution layer")},  # info: { "id" : "agent_program_launch" , "why_not" : why
        ],  # info: ] ,
        "disabled": [  # info: "disabled" : [
            {"id": "ollama_fallback_for_council", "why_not": why("disabled", "disabled", "Council inference stays on the NPU.", "RR_NPU_ONLY", "Unset RR_NPU_ONLY only if Alexander says so")},  # info: { "id" : "ollama_fallback_for_council" , "why_not" : why
            {"id": "specialist_routing", "why_not": why("disabled", "disabled", "Council voices use their persona files, not specialist routing.", "RR_SPECIALIST_ROUTING", "RR_SPECIALIST_ROUTING=1")},  # info: { "id" : "specialist_routing" , "why_not" : why
        ],  # info: ] ,
        "experimental": [],  # info: "experimental" : [ ] ,
        "poller_flags_present": sorted(flags) if flags else [],  # info: "poller_flags_present" : sorted ( flags ) if flags else [ ] ,
        "poller_flag_rr_relay_replies": "on" if flag_on("RR_RELAY_REPLIES") else "off_or_unreadable",  # info: "poller_flag_rr_relay_replies" : "on" if flag_on ( "RR_RELAY_REPLIES" ) else "off_or_unreadable" ,
    }  # info: }

# ====================================================
# SECTION: function brief_text
# What it does: Short lines an agent can read inside a small context window. Derived from the snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def brief_text(doc: dict) -> str:  # info: def brief_text
    lines = [f"generated_at={doc['generated_at']}", "secrets=none", "empty_incident_list_is_not_all_clear=true"]  # info: set lines
    res = (doc.get("system") or {}).get("resources") or {}  # info: set res
    lines.append(f"host_resources={json.dumps(res.get('value'), separators=(',', ':'))}")  # info: lines . append ( f" host_resources=
    power = doc.get("system", {}).get("power") or {}  # info: set power
    for key, row in power.items():  # info: for key , row in power . items ( )
        val = row.get("value") or {}  # info: set val
        lines.append(f"power_{key}_soc={val.get('soc_percent')} at={val.get('at')} confidence={row.get('confidence')}")  # info: lines . append ( f" power_ { key } _soc=
    for name, row in (doc.get("services") or {}).items():  # info: for name , row in ( doc . get ( "services" ) or { } ) . items ( )
        lines.append(f"service_{name}={row.get('status')} confidence={row.get('confidence')}")  # info: lines . append ( f" service_ { name } =
    launchable = [p.get("program_id") for p in doc.get("programs", {}).get("agent_launchable") or []]  # info: set launchable
    lines.append(f"agent_launchable={','.join(launchable) if launchable else 'none'}")  # info: lines . append ( f" agent_launchable=
    lines.append("agent_launch_kind=not_implemented")  # info: lines . append ( "agent_launch_kind=not_implemented" )
    lines.append("do_not=enable gates, launch programs, restart the poller, start a second relay, invent numbers")  # info: lines . append ( "do_not=enable gates, launch programs, restart the poller, start a second relay, invent numbers" )
    for cap in (doc.get("capabilities") or {}).get("gated") or []:  # info: for cap in ( doc . get ( "capabilities" ) or { } ) . get ( "gated" ) or [ ]
        w = cap.get("why_not") or {}  # info: set w
        lines.append(f"gated_{cap.get('id')}={w.get('blocked_by')} ({w.get('kind')})")  # info: lines . append ( f" gated_ { cap . get ( 'id' ) } =
    health = doc.get("health") or {}  # info: set health
    lines.append(f"health_failed={','.join(health.get('failed') or []) or 'none'}")  # info: lines . append ( f" health_failed=
    lines.append(f"health_degraded={','.join(health.get('degraded') or []) or 'none'}")  # info: lines . append ( f" health_degraded=
    lines.append(f"health_unknown={','.join(health.get('unknown') or []) or 'none'}")  # info: lines . append ( f" health_unknown=
    text = "\n".join(lines) + "\n"  # info: set text
    return text[:4000]  # info: return text [ : 4000 ]

# ====================================================
# SECTION: function build
# What it does: Assemble the snapshot. Does not send or launch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build() -> dict:  # info: def build
    rows = process_cmds()  # info: set rows
    flags, flag_source = poller_flags(rows)  # info: flags , flag_source = poller_flags ( rows )
    buckets = load_jobs()  # info: set buckets
    jobs = []  # info: set jobs
    for bucket, items in buckets.items():  # info: for bucket , items in buckets . items ( )
        for job in items:  # info: for job in items :
            if isinstance(job, dict) and job.get("id"):  # info: if isinstance ( job , dict ) and job . get ( "id" )
                jobs.append(job_row(bucket, job))  # info: jobs . append ( job_row ( bucket , job ) )
    by_id = {j["id"]: j for j in jobs}  # info: set by_id
    relay = kv_file(RELAY_CONF)  # info: set relay
    relay_pids = match_procs(rows, "council-relay.py")  # info: set relay_pids
    ollama_pids = match_procs(rows, "ollama serve")  # info: set ollama_pids
    poller_pids = [pid for pid, cmd in rows if "rootserver_poller.py" in cmd and "poller-watch" not in cmd]  # info: set poller_pids
    flm_pids = match_procs(rows, "flm serve")  # info: set flm_pids
    monitor_pids = match_procs(rows, "root-monitor")  # info: set monitor_pids
    desk_ok = DESK.is_file()  # info: set desk_ok
    npu = Path("/dev/accel/accel0").exists()  # info: set npu
    programs = programs_block(by_id)  # info: set programs
    launchable = [p for p in programs if p.get("agent_launchable") is True]  # info: set launchable
    failed, degraded, healthy, unknown = [], [], [], []  # info: failed , degraded , healthy , unknown = [ ] , [ ] , [ ] , [ ]
    if len(relay_pids) == 1:  # info: if len ( relay_pids ) == 1 :
        healthy.append("council_relay")  # info: healthy . append ( "council_relay" )
    elif len(relay_pids) == 0:  # info: elif len ( relay_pids ) == 0 :
        failed.append("council_relay")  # info: failed . append ( "council_relay" )
    else:  # info: else :
        degraded.append("council_relay_duplicate")  # info: degraded . append ( "council_relay_duplicate" )
    if poller_pids:  # info: if poller_pids :
        healthy.append("rootserver_poller")  # info: healthy . append ( "rootserver_poller" )
    else:  # info: else :
        failed.append("rootserver_poller")  # info: failed . append ( "rootserver_poller" )
    if npu:  # info: if npu :
        healthy.append("npu_device")  # info: healthy . append ( "npu_device" )
    else:  # info: else :
        failed.append("npu_device")  # info: failed . append ( "npu_device" )
    if not desk_ok:  # info: if not desk_ok :
        degraded.append("desk_live_missing")  # info: degraded . append ( "desk_live_missing" )
    else:  # info: else :
        healthy.append("desk_live")  # info: healthy . append ( "desk_live" )
    if not flm_pids:  # info: if not flm_pids :
        healthy.append("flm_idle_on_demand")  # info: healthy . append ( "flm_idle_on_demand" )
    unknown.append("incidents")  # info: unknown . append ( "incidents" )
    unknown.append("root_monitor")  # info: unknown . append ( "root_monitor" )
    doc = {  # info: set doc
        "generated_at": now_local(),  # info: "generated_at" : now_local ( ) ,
        "schema_version": SCHEMA,  # info: "schema_version" : SCHEMA ,
        "secrets_included": False,  # info: "secrets_included" : False ,
        "system": {**host_block(), "power": power_block()},  # info: "system" : { * * host_block ( ) , "power" : power_block ( ) } ,
        "services": {  # info: "services" : {
            "ollama": service_proc("ollama", ollama_pids, {"why_not": None if ollama_pids else why("stopped", "unavailable", "No ollama serve process. Council chat still uses the NPU.", "", "")}),  # info: "ollama" : service_proc ( "ollama" , ollama_pids
            "council_relay": service_proc("council_relay", relay_pids, {"owner": relay.get("POLL_VOICE") or "ava", "why_not": None if len(relay_pids) == 1 else why("degraded" if relay_pids else "failed", "broken", "Relay count is not exactly one.", "single_getUpdates", "")}),  # info: "council_relay" : service_proc ( "council_relay" , relay_pids
            "desk_live": {"service": "desk_live", "status": "present" if desk_ok else "missing", "source": "desk-live.txt", "confidence": "live", "observed_at": now_local()},  # info: "desk_live" : { "service" : "desk_live" , "status" : "present" if desk_ok else "missing"
            "root_monitor": service_proc("root_monitor", monitor_pids),  # info: "root_monitor" : service_proc ( "root_monitor" , monitor_pids ) ,
            "github_sync": {"service": "github_sync", "status": "scheduled" if (by_id.get("github_sync_all") or {}).get("enabled") else "disabled", "resident": False, "source": "jobs.py", "confidence": "configured", "observed_at": now_local(), "why_not": None if (by_id.get("github_sync_all") or {}).get("enabled") else why("disabled", "disabled", "github_sync_all is off in the catalog", "", "")},  # info: "github_sync" : { "service" : "github_sync" , "status" : "scheduled" if ( by_id . get ( "github_sync_all" ) or { } ) . get ( "enabled" ) else "disabled"
            "rootserver_poller": service_proc("rootserver_poller", poller_pids),  # info: "rootserver_poller" : service_proc ( "rootserver_poller" , poller_pids ) ,
            "flm": {"service": "flm", "status": "active" if flm_pids else "idle", "pids": flm_pids, "source": "process_scan", "confidence": "live", "observed_at": now_local(), "note": "Idle is normal. The model loads per reply."},  # info: "flm" : { "service" : "flm" , "status" : "active" if flm_pids else "idle"
        },  # info: } ,
        "models": {"installed": model_names(), "active": obs(flm_pids or None, "process_scan", "live", note="empty pids means no resident FLM"), "performance": obs({"model": "llama3.2:3b", "ctx": 4096, "pmode": "performance", "resident": False}, "ensure-relay.sh", "configured")},  # info: "models" : { "installed" : model_names ( ) , "active" : obs
        "agents": {  # info: "agents" : {
            "ava": {"role": "default voice and the only getUpdates owner", "persona": "Database/AI/FLM/Personas/ava.json", "launch_programs": False},  # info: "ava" : { "role" : "default voice and the only getUpdates owner"
            "bruce": {"role": "replies when addressed or in a room round", "persona": "Database/AI/FLM/Personas/bruce.json", "launch_programs": False},  # info: "bruce" : { "role" : "replies when addressed or in a room round"
            "carly": {"role": "replies when addressed or in a room round", "persona": "Database/AI/FLM/Personas/carly.json", "launch_programs": False},  # info: "carly" : { "role" : "replies when addressed or in a room round"
        },  # info: } ,
        "communication": {  # info: "communication" : {
            "telegram": {"credentials": "not_in_this_file", "source": "policy", "confidence": "configured"},  # info: "telegram" : { "credentials" : "not_in_this_file" , "source" : "policy" , "confidence" : "configured" } ,
            "sandbox": {"chat_configured": bool(relay.get("SANDBOX_CHAT_ID")), "replies": relay.get("SANDBOX_REPLIES") == "1", "source": "relay.conf", "confidence": "configured"},  # info: "sandbox" : { "chat_configured" : bool ( relay . get ( "SANDBOX_CHAT_ID" ) ) , "replies" : relay . get ( "SANDBOX_REPLIES" ) == "1"
            "live_council": {"chat_configured": bool(relay.get("COUNCIL_CHAT_ID")), "replies": False, "why_not": why("gated", "gated", "Live council replies are off on purpose.", "RR_RELAY_REPLIES", "RR_RELAY_REPLIES=1"), "source": "relay.conf", "confidence": "configured"},  # info: "live_council" : { "chat_configured" : bool ( relay . get ( "COUNCIL_CHAT_ID" ) )
            "private_dms": {"replies": False, "why_not": why("gated", "gated", "Private DMs are off on purpose.", "RR_RELAY_REPLIES", "RR_RELAY_REPLIES=1"), "source": "council-relay.py", "confidence": "configured"},  # info: "private_dms" : { "replies" : False , "why_not" : why
        },  # info: } ,
        "repositories": repos_block(),  # info: "repositories" : repos_block ( ) ,
        "automation": {"scheduled": jobs, "running_processes": {"rootserver_poller": poller_pids, "council_relay": relay_pids}, "poller_flag_source": flag_source},  # info: "automation" : { "scheduled" : jobs , "running_processes" : { "rootserver_poller" : poller_pids , "council_relay" : relay_pids } , "poller_flag_source" : flag_source } ,
        "programs": {"available": programs, "running": [], "failed": [], "agent_launchable": launchable},  # info: "programs" : { "available" : programs , "running" : [ ] , "failed" : [ ] , "agent_launchable" : launchable } ,
        "capabilities": capabilities(relay, flags),  # info: "capabilities" : capabilities ( relay , flags ) ,
        "health": {"healthy": healthy, "degraded": degraded, "failed": failed, "unknown": unknown},  # info: "health" : { "healthy" : healthy , "degraded" : degraded , "failed" : failed , "unknown" : unknown } ,
        "incidents": {"items": [], "why_not": why("unknown", "not_implemented", "No incident store is read. An empty list is not an all-clear.", "", "")},  # info: "incidents" : { "items" : [ ] , "why_not" : why
        "recent_changes": obs(None, "not_collected", "unknown", why_not=why("unknown", "not_implemented", "Git history is not copied into this snapshot yet.", "", "")),  # info: "recent_changes" : obs ( None , "not_collected" , "unknown"
        "known_limitations": [  # info: "known_limitations" : [
            "Context for council chat is 4096. Do not raise it.",  # info: "Context for council chat is 4096. Do not raise it." ,
            "FLM is on demand. A missing flm process is normal between replies.",  # info: "FLM is on demand. A missing flm process is normal between replies." ,
            "One getUpdates owner. Do not start a second relay.",  # info: "One getUpdates owner. Do not start a second relay." ,
            "This file has no secrets. A missing credential field means it was left out on purpose.",  # info: "This file has no secrets. A missing credential field means it was left out on purpose." ,
            "agent_launchable empty means agents cannot start programs yet.",  # info: "agent_launchable empty means agents cannot start programs yet." ,
        ],  # info: ] ,
        "agent_instructions": [  # info: "agent_instructions" : [
            "Answer what exists, what is running, what is broken, what is gated, and what you can launch from this snapshot only.",  # info: "Answer what exists, what is running, what is broken, what is gated, and what you can launch from this snapshot only." ,
            "kind gated or disabled means leave it alone.",  # info: "kind gated or disabled means leave it alone." ,
            "kind not_implemented means do not pretend it exists and do not build a workaround in the reply.",  # info: "kind not_implemented means do not pretend it exists and do not build a workaround in the reply." ,
            "kind broken means say it is broken. Do not restart anything.",  # info: "kind broken means say it is broken. Do not restart anything." ,
            "You cannot launch programs from this snapshot.",  # info: "You cannot launch programs from this snapshot." ,
        ],  # info: ] ,
        "npu_device_present": obs(npu, "/dev/accel/accel0", "live"),  # info: "npu_device_present" : obs ( npu , "/dev/accel/accel0" , "live" ) ,
    }  # info: }
    return doc  # info: return doc

# ====================================================
# SECTION: function write_out
# What it does: Atomically write the snapshot and the brief, mode 0600. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_out(doc: dict) -> None:  # info: def write_out
    OUT.parent.mkdir(parents=True, exist_ok=True)  # info: OUT . parent . mkdir ( parents = True , exist_ok = True )
    text = json.dumps(doc, indent=2) + "\n"  # info: set text
    brief = brief_text(doc)  # info: set brief
    for path, body in ((OUT, text), (BRIEF, brief)):  # info: for path , body in ( ( OUT , text ) , ( BRIEF , brief ) )
        tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
        tmp.write_text(body, encoding="utf-8")  # info: tmp . write_text ( body , encoding = "utf-8" )
        os.chmod(tmp, 0o600)  # info: os . chmod ( tmp , 0o600 )
        os.replace(tmp, path)  # info: os . replace ( tmp , path )
        os.chmod(path, 0o600)  # info: os . chmod ( path , 0o600 )

# ====================================================
# SECTION: function main
# What it does: Write the snapshot and print counts. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    doc = build()  # info: set doc
    write_out(doc)  # info: call write_out
    print(f"[ok] state jobs={len(doc['automation']['scheduled'])} programs={len(doc['programs']['available'])} launchable={len(doc['programs']['agent_launchable'])}")  # info: call print
    return 0  # info: return 0

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
