# ==============================================================================
# FILE: Automations/execution/verifier.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Check a work order's verification list. Does not restart the target."""
from __future__ import annotations  # info: from __future__ import annotations
import json, os, sys  # info: import json , os , sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
ORDERS = ROOT / "5 - RootRecord-Library" / "Documentation" / "02-Agents" / "Work-Orders"  # info: set ORDERS
REQUESTS = Path(os.environ.get("RR_REQUEST_DIR", str(ROOT / "2 - RootRecord-Database" / "System" / "status" / "requests")))  # info: set REQUESTS

# ====================================================
# SECTION: function relay_alive
# What it does: Count python processes running council-relay.py. Does not signal them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def relay_alive() -> int:  # info: def relay_alive
    count = 0  # info: set count
    for name in os.listdir("/proc"):  # info: for name in os . listdir ( "/proc" )
        if not name.isdigit():  # info: if not name . isdigit ( )
            continue  # info: continue
        try:  # info: try :
            raw = Path(f"/proc/{name}/cmdline").read_bytes()  # info: set raw
        except OSError:  # info: except OSError :
            continue  # info: continue
        toks = raw.replace(b"\0", b" ").decode("utf-8", "replace").split()  # info: set toks
        if len(toks) < 2 or toks[0].rsplit("/", 1)[-1] not in ("python", "python3"):  # info: if len ( toks ) < 2 or toks [ 0 ] . rsplit
            continue  # info: continue
        if any(t.rsplit("/", 1)[-1] == "council-relay.py" for t in toks[1:]):  # info: if any ( t . rsplit ( "/" , 1 ) [ - 1 ] == "council-relay.py" for t in toks [ 1 : ] )
            count += 1  # info: set count
    return count  # info: return count

# ====================================================
# SECTION: function write_report
# What it does: Grade an execution report into a verification report. Does not change files the executor touched.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_report(exec_path: Path) -> int:  # info: def write_report
    report = json.loads(exec_path.read_text(encoding="utf-8"))  # info: set report
    request_id = report.get("request_id")  # info: set request_id
    checks = []  # info: set checks
    pairs = [("request_record_present", REQUESTS / f"{request_id}.json"), ("handoff_package_present", REQUESTS / "handoff" / f"{request_id}.json"), ("execution_report_present", exec_path)]  # info: set pairs
    for check_id, path in pairs:  # info: for check_id , path in pairs
        ok = path.is_file()  # info: set ok
        checks.append({"id": check_id, "measured": str(ok), "expected": "true", "result": "pass" if ok else "fail"})  # info: checks . append ( { "id" : check_id , "measured" : str ( ok ) , "expected" : "true" , "result" : "pass" if ok else "fail" } )
    status = "verified" if all(row["result"] == "pass" for row in checks) else "failed"  # info: set status
    out = {"schema_version": 1, "report_id": f"VR-{request_id}", "execution_report_id": report.get("report_id"), "checks": checks, "status": status, "observed_at": datetime.now().astimezone().isoformat(timespec="seconds"), "visibility": "operator"}  # info: set out
    dest = REQUESTS / "reports" / "verification" / f"VR-{request_id}.json"  # info: set dest
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir ( parents = True , exist_ok = True )
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")  # info: dest . write_text ( json . dumps ( out , indent = 2 ) + "\n" , encoding = "utf-8" )
    os.chmod(dest, 0o600)  # info: os . chmod ( dest , 0o600 )
    print(f"[{status.upper()}] {out['report_id']}")  # info: call print
    return 0 if status == "verified" else 1  # info: return 0 if status == "verified" else 1

# ====================================================
# SECTION: function main
# What it does: Print PASS or FAIL for the order, or write a verification report. Exit 1 on FAIL. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if len(sys.argv) > 2 and sys.argv[1] == "report":  # info: if len ( sys . argv ) > 2 and sys . argv [ 1 ] == "report"
        return write_report(Path(sys.argv[2]))  # info: return write_report ( Path ( sys . argv [ 2 ] ) )
    order_id = sys.argv[1] if len(sys.argv) > 1 else "WO-SRV-RELAY"  # info: set order_id
    path = ORDERS / f"{order_id}.json"  # info: set path
    if not path.is_file():  # info: if not path . is_file ( )
        print(f"[FAIL] missing {order_id}")  # info: call print
        return 1  # info: return 1
    order = json.loads(path.read_text(encoding="utf-8"))  # info: set order
    failed = 0  # info: set failed
    for check in order.get("verification") or []:  # info: for check in order . get ( "verification" ) or [ ]
        if check == "process_alive" and order.get("target") == "council_relay":  # info: if check == "process_alive" and order . get ( "target" ) == "council_relay"
            n = relay_alive()  # info: set n
            level = "PASS" if n == 1 else "FAIL"  # info: set level
            print(f"[{level}] {order_id} process_alive count={n}")  # info: call print
            if level == "FAIL":  # info: if level == "FAIL"
                failed += 1  # info: set failed
        else:  # info: else :
            print(f"[FAIL] {order_id} no checker for {check}")  # info: call print
            failed += 1  # info: set failed
    if order.get("agent_may_invoke"):  # info: if order . get ( "agent_may_invoke" )
        print(f"[FAIL] {order_id} agent_may_invoke must stay false")  # info: call print
        failed += 1  # info: set failed
    else:  # info: else :
        print(f"[PASS] {order_id} agent_may_invoke false")  # info: call print
    return 1 if failed else 0  # info: return 1 if failed else 0

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
