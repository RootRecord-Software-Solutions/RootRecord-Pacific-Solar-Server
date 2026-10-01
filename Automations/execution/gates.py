# ==============================================================================
# FILE: Automations/execution/gates.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Read and write execution gates. Missing write gates stay closed. Does not launch programs."""
from __future__ import annotations  # info: from __future__ import annotations
import json, os  # info: import json , os
from pathlib import Path  # info: from pathlib import Path

ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
SEED = ROOT / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server" / "Apps" / "Control-Panel" / "execution-gates.json"  # info: set SEED
LIVE = Path(os.environ.get("RR_EXECUTION_GATES", str(ROOT / "2 - RootRecord-Database" / "System" / "control-panel" / "execution-gates.json")))  # info: set LIVE
READ_PERMISSIONS = {"READ", "DIAGNOSE"}  # info: set READ_PERMISSIONS

# ====================================================
# SECTION: function seed_doc
# What it does: Load the committed gate seed. Returns an empty deny-all document if the seed is missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def seed_doc() -> dict:  # info: def seed_doc
    try:  # info: try :
        data = json.loads(SEED.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return {"schema_version": 1, "modes": {}, "steps": {}}  # info: return { "schema_version" : 1 , "modes" : { } , "steps" : { } }
    return data if isinstance(data, dict) else {"schema_version": 1, "modes": {}, "steps": {}}  # info: return data if isinstance ( data , dict ) else { "schema_version" : 1 , "modes" : { } , "steps" : { } }

# ====================================================
# SECTION: function load
# What it does: Load the live gate file, or the seed when the live file is absent. Does not launch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load(path: Path | None = None) -> dict:  # info: def load
    target = path or LIVE  # info: set target
    if not target.is_file():  # info: if not target . is_file ( )
        return seed_doc()  # info: return seed_doc ( )
    try:  # info: try :
        data = json.loads(target.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return {"schema_version": 1, "modes": {}, "steps": {}}  # info: return { "schema_version" : 1 , "modes" : { } , "steps" : { } }
    return data if isinstance(data, dict) else {"schema_version": 1, "modes": {}, "steps": {}}  # info: return data if isinstance ( data , dict ) else { "schema_version" : 1 , "modes" : { } , "steps" : { } }

# ====================================================
# SECTION: function lookup
# What it does: Read one dotted gate. Missing keys are closed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lookup(doc: dict, dotted: str) -> bool:  # info: def lookup
    cur = doc  # info: set cur
    for part in dotted.split("."):  # info: for part in dotted . split ( "." )
        if not isinstance(cur, dict) or part not in cur:  # info: if not isinstance ( cur , dict ) or part not in cur
            return False  # info: return False
        cur = cur[part]  # info: set cur
    return cur is True  # info: return cur is True

# ====================================================
# SECTION: function allowed
# What it does: Decide one capability against the gate file. Read permissions stay open when their gate key is absent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def allowed(cap: dict, doc: dict | None = None) -> bool:  # info: def allowed
    doc = load() if doc is None else doc  # info: set doc
    permission = cap.get("permission") or ""  # info: set permission
    gate = cap.get("monitor_gate") or ""  # info: set gate
    if permission in READ_PERMISSIONS and not gate:  # info: if permission in READ_PERMISSIONS and not gate
        return True  # info: return True
    if not gate:  # info: if not gate
        return permission in READ_PERMISSIONS  # info: return permission in READ_PERMISSIONS
    parts = gate.split(".")  # info: set parts
    if permission in READ_PERMISSIONS and len(parts) >= 2:  # info: if permission in READ_PERMISSIONS and len ( parts ) >= 2
        parent = doc.get(parts[0]) if isinstance(doc.get(parts[0]), dict) else {}  # info: set parent
        if parts[1] not in parent:  # info: if parts [ 1 ] not in parent
            return True  # info: return True
    return lookup(doc, gate)  # info: return lookup ( doc , gate )

# ====================================================
# SECTION: function save
# What it does: Atomically write the live gate file. Does not launch a program.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save(doc: dict, path: Path | None = None) -> None:  # info: def save
    target = path or LIVE  # info: set target
    target.parent.mkdir(parents=True, exist_ok=True)  # info: target . parent . mkdir ( parents = True , exist_ok = True )
    tmp = target.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps ( doc , indent = 2 ) + "\n" , encoding = "utf-8" )
    os.replace(tmp, target)  # info: os . replace ( tmp , target )
    os.chmod(target, 0o600)  # info: os . chmod ( target , 0o600 )

# ====================================================
# SECTION: function set_gate
# What it does: Turn a gate on only after confirm. Turning a gate off does not require confirm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_gate(dotted: str, value: bool, confirmed: bool = False, path: Path | None = None) -> dict:  # info: def set_gate
    if value and not confirmed:  # info: if value and not confirmed
        raise PermissionError(f"refusing to enable {dotted} without confirm")  # info: raise PermissionError ( f" refusing to enable { dotted } without confirm " )
    doc = load(path)  # info: set doc
    parts = dotted.split(".")  # info: set parts
    cur = doc  # info: set cur
    for part in parts[:-1]:  # info: for part in parts [ : - 1 ]
        nxt = cur.get(part)  # info: set nxt
        if not isinstance(nxt, dict):  # info: if not isinstance ( nxt , dict )
            nxt = {}  # info: set nxt
            cur[part] = nxt  # info: cur [ part ] = nxt
        cur = nxt  # info: set cur
    cur[parts[-1]] = bool(value)  # info: cur [ parts [ - 1 ] ] = bool ( value )
    save(doc, path)  # info: call save
    return doc  # info: return doc
