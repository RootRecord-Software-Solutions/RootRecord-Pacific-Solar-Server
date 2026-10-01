# ==============================================================================
# FILE: Communications/telegram/scripts/desk-live.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Write measured desk lines for the council NPU. Reads existing last files only. Does not send."""
from __future__ import annotations  # info: from __future__ import annotations
import argparse, json, os, re  # info: import argparse , json , os , re
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DB
ENERGY = DB / "Energy"  # info: set ENERGY
HOST = DB / "System" / "status" / "system-status.json"  # info: set HOST
DEFAULT_OUT = DB / "Intake" / "desk-live.txt"  # info: set DEFAULT_OUT
PACKS = (("delta2", "Delta 2"), ("river2pro", "River 2 Pro"))  # info: set PACKS
WATTS = (  # info: set WATTS
    ("solar_input_power", "solar_input_w"),  # info: ( "solar_input_power" , "solar_input_w" )
    ("ac_output_power", "ac_output_w"),  # info: ( "ac_output_power" , "ac_output_w" )
    ("ac_input_power", "ac_input_w"),  # info: ( "ac_input_power" , "ac_input_w" )
    ("usbc_output_power", "usbc_output_w"),  # info: ( "usbc_output_power" , "usbc_output_w" )
)  # info: )
WATT_SAY = (  # info: set WATT_SAY
    ("solar_input_w", "solar in"),  # info: ( "solar_input_w" , "solar in" )
    ("ac_output_w", "AC out"),  # info: ( "ac_output_w" , "AC out" )
    ("ac_input_w", "AC in"),  # info: ( "ac_input_w" , "AC in" )
    ("usbc_output_w", "USB-C out"),  # info: ( "usbc_output_w" , "USB-C out" )
)  # info: )
PACK_LINE = re.compile(r"^(?P<name>.+?) (?P<key>SOC_percent|solar_input_w|ac_output_w|ac_input_w|usbc_output_w|charge_source)=(?P<val>\S+)")  # info: set PACK_LINE
HOST_LINE = re.compile(r"^host (?P<key>cpu_percent|mem_used_percent|load1|load5|load15)=(?P<val>\S+)")  # info: set HOST_LINE

# ====================================================
# SECTION: function load_json
# What it does: Read one JSON file. Returns None when it is missing or unreadable. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_json(path: Path):  # info: def load_json
    try:  # info: try :
        return json.loads(path.read_text(encoding="utf-8"))  # info: return json . loads ( path . read_text
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return None  # info: return None

# ====================================================
# SECTION: function age_min
# What it does: Minutes since an ISO timestamp. None when the stamp cannot be read.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def age_min(stamp: str, now: datetime):  # info: def age_min
    try:  # info: try :
        return int((now - datetime.fromisoformat(stamp)).total_seconds() // 60)  # info: return int ( ( now - datetime
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError )
        return None  # info: return None

# ====================================================
# SECTION: function pack_lines
# What it does: Measured SOC and watt lines for one pack. Missing files become No data. Does not invent numbers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pack_lines(key: str, name: str, now: datetime) -> list[str]:  # info: def pack_lines
    soc = load_json(ENERGY / "soc" / f"{key}-last.json")  # info: set soc
    watts = load_json(ENERGY / "watts" / f"{key}-last.json") or {}  # info: set watts
    if not isinstance(soc, dict) or "soc" not in soc:  # info: if not isinstance ( soc , dict ) or
        return [f"{name} SOC_percent=No data"]  # info: return [ f" { name } SOC_percent=No data" ]
    age = age_min(soc.get("at"), now)  # info: set age
    lines = [f"{name} SOC_percent={soc['soc']} measured_at={soc.get('at')} age_min={age if age is not None else 'No data'} source={soc.get('source') or 'No data'}"]  # info: set lines
    if not isinstance(watts, dict):  # info: if not isinstance ( watts , dict )
        return lines  # info: return lines
    for src, label in WATTS:  # info: for src , label in WATTS :
        if src in watts and watts[src] is not None:  # info: if src in watts and watts [ src ]
            lines.append(f"{name} {label}={watts[src]}")  # info: lines . append ( f" { name }
    if watts.get("charge_source"):  # info: if watts . get ( "charge_source" )
        lines.append(f"{name} charge_source={watts['charge_source']}")  # info: lines . append ( f" { name } charge_source=
    return lines  # info: return lines

# ====================================================
# SECTION: function host_lines
# What it does: Measured host CPU, memory, and load from system-status.json. Does not sample /proc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host_lines() -> list[str]:  # info: def host_lines
    doc = load_json(HOST)  # info: set doc
    current = (doc or {}).get("current") if isinstance(doc, dict) else None  # info: set current
    metrics = (current or {}).get("metrics") if isinstance(current, dict) else None  # info: set metrics
    if not isinstance(metrics, dict):  # info: if not isinstance ( metrics , dict )
        return ["host=No data"]  # info: return [ "host=No data" ]
    lines = [f"host measured_at={current.get('observed_at')}"]  # info: set lines
    for key in ("cpu_percent", "mem_used_percent", "load1", "load5", "load15"):  # info: for key in ( "cpu_percent" , "mem_used_percent"
        row = metrics.get(key) or {}  # info: set row
        if isinstance(row, dict) and row.get("value") is not None:  # info: if isinstance ( row , dict ) and row
            lines.append(f"host {key}={row['value']}")  # info: lines . append ( f" host { key } =
    return lines  # info: return lines

# ====================================================
# SECTION: function render
# What it does: All measured desk lines. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render(now: datetime | None = None) -> str:  # info: def render
    now = now or datetime.now().astimezone()  # info: set now
    lines = [f"desk_written_at={now.isoformat(timespec='seconds')}"]  # info: set lines
    for key, name in PACKS:  # info: for key , name in PACKS :
        lines.extend(pack_lines(key, name, now))  # info: lines . extend ( pack_lines ( key , name , now
    lines.extend(host_lines())  # info: lines . extend ( host_lines ( ) )
    return "\n".join(lines) + "\n"  # info: return "\n" . join ( lines ) + "\n"

# ====================================================
# SECTION: function write_out
# What it does: Atomically write the desk file mode 0600. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_out(path: Path, text: str) -> None:  # info: def write_out
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
    tmp.write_text(text, encoding="utf-8")  # info: tmp . write_text ( text , encoding =
    os.chmod(tmp, 0o600)  # info: os . chmod ( tmp , 0o600 )
    os.replace(tmp, path)  # info: os . replace ( tmp , path )
    os.chmod(path, 0o600)  # info: os . chmod ( path , 0o600 )

# ====================================================
# SECTION: function join_and
# What it does: Join phrases with commas and a final and. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def join_and(parts: list[str]) -> str:  # info: def join_and
    if not parts:  # info: if not parts
        return ""  # info: return ""
    if len(parts) == 1:  # info: if len ( parts ) == 1
        return parts[0]  # info: return parts [ 0 ]
    if len(parts) == 2:  # info: if len ( parts ) == 2
        return f"{parts[0]} and {parts[1]}"  # info: return f" { parts [ 0 ] } and { parts [ 1 ] } "
    return ", ".join(parts[:-1]) + ", and " + parts[-1]  # info: return ", " . join ( parts [ : -1 ] ) + ", and " + parts [ -1 ]

# ====================================================
# SECTION: function _zero
# What it does: True when a measured watt string is zero. Does not invent a number.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _zero(raw: str) -> bool:  # info: def _zero
    try:  # info: try
        return float(raw) == 0  # info: return float ( raw ) == 0
    except ValueError:  # info: except ValueError
        return False  # info: return False

# ====================================================
# SECTION: function _pack_sentence
# What it does: One or two spoken sentences for one pack. Skips missing fields. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pack_sentence(name: str, fields: dict) -> str:  # info: def _pack_sentence
    soc = fields.get("SOC_percent")  # info: set soc
    if soc == "No data":  # info: if soc == "No data"
        head = f"I cannot see {name}'s charge"  # info: set head
    elif soc:  # info: elif soc
        head = f"{name} is at {soc}% full"  # info: set head
    else:  # info: else
        head = name  # info: set head
    active, idle = [], []  # info: set active , idle
    for key, label in WATT_SAY:  # info: for key , label in WATT_SAY
        if key not in fields:  # info: if key not in fields
            continue  # info: continue
        raw = fields[key]  # info: set raw
        if _zero(raw):  # info: if _zero ( raw )
            idle.append(label)  # info: idle . append ( label )
        else:  # info: else
            active.append(f"{raw} watts {label}")  # info: active . append ( f" { raw } watts { label } " )
    sentence = head  # info: set sentence
    if active:  # info: if active
        sentence += ", with " + join_and(active)  # info: set sentence
    sentence += "."  # info: set sentence
    if idle:  # info: if idle
        names = join_and(idle)  # info: set names
        sentence += " " + names[:1].upper() + names[1:] + (" is 0." if len(idle) == 1 else " are 0.")  # info: set sentence
    source = (fields.get("charge_source") or "").strip()  # info: set source
    if source.lower() == "none":  # info: if source . lower ( ) == "none"
        sentence += " It is not charging."  # info: set sentence
    elif source:  # info: elif source
        sentence += f" It is charging from {source.replace('_', ' ')}."  # info: set sentence
    return sentence  # info: return sentence

# ====================================================
# SECTION: function _host_sentence
# What it does: One spoken sentence for host CPU, memory, and load. Skips missing fields. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _host_sentence(host: dict) -> str:  # info: def _host_sentence
    bits = []  # info: set bits
    if host.get("cpu_percent"):  # info: if host . get ( "cpu_percent" )
        bits.append(f"CPU is {host['cpu_percent']}%")  # info: bits . append ( f" CPU is { host [ 'cpu_percent' ] } % " )
    if host.get("mem_used_percent"):  # info: if host . get ( "mem_used_percent" )
        bits.append(f"memory is {host['mem_used_percent']}% used")  # info: bits . append ( f" memory is { host [ 'mem_used_percent' ] } % used " )
    loads = [host[key] for key in ("load1", "load5", "load15") if host.get(key)]  # info: set loads
    if len(loads) == 3:  # info: if len ( loads ) == 3
        bits.append(f"load is {loads[0]}, {loads[1]}, and {loads[2]}")  # info: bits . append ( f" load is { loads [ 0 ] } , { loads [ 1 ] } , and { loads [ 2 ] } " )
    elif loads:  # info: elif loads
        bits.append("load is " + join_and(loads))  # info: bits . append ( "load is " + join_and ( loads ) )
    if not bits:  # info: if not bits
        return ""  # info: return ""
    return "The host " + join_and(bits) + "."  # info: return "The host " + join_and ( bits ) + "."

# ====================================================
# SECTION: function speak_desk
# What it does: Turn measured desk lines into two or three spoken sentences. Does not invent numbers or send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speak_desk(text: str) -> str:  # info: def speak_desk
    packs: dict[str, dict] = {}  # info: set packs
    order: list[str] = []  # info: set order
    host: dict[str, str] = {}  # info: set host
    for raw in text.splitlines():  # info: for raw in text . splitlines
        line = raw.strip()  # info: set line
        if not line or line.startswith("#") or line.startswith("desk_written_at="):  # info: if not line or line . startswith
            continue  # info: continue
        host_hit = HOST_LINE.match(line)  # info: set host_hit
        if host_hit:  # info: if host_hit
            host[host_hit.group("key")] = host_hit.group("val")  # info: host [ host_hit . group ( "key" ) ] = host_hit . group ( "val" )
            continue  # info: continue
        hit = PACK_LINE.match(line)  # info: set hit
        if not hit:  # info: if not hit
            continue  # info: continue
        name = hit.group("name")  # info: set name
        if name not in packs:  # info: if name not in packs
            packs[name] = {}  # info: packs [ name ] = { }
            order.append(name)  # info: order . append ( name )
        packs[name][hit.group("key")] = hit.group("val")  # info: packs [ name ] [ hit . group ( "key" ) ] = hit . group ( "val" )
    sentences = [_pack_sentence(name, packs[name]) for name in order]  # info: set sentences
    host_sentence = _host_sentence(host)  # info: set host_sentence
    if host_sentence:  # info: if host_sentence
        sentences.append(host_sentence)  # info: sentences . append ( host_sentence )
    return " ".join(s for s in sentences if s).strip()  # info: return " " . join ( s for s in sentences if s ) . strip

# ====================================================
# SECTION: function main
# What it does: Write desk-live.txt, or with --speak print a spoken summary and do not write. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--out", default=str(DEFAULT_OUT))  # info: ap . add_argument ( "--out" , default =
    args = ap.parse_args()  # info: set args
    text = render()  # info: set text
    write_out(Path(args.out), text)  # info: call write_out
    print(f"[ok] desk lines={text.count(chr(10))}")  # info: call print
    return 0  # info: return 0

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
