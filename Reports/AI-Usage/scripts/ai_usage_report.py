# ==============================================================================
# FILE: Reports/AI-Usage/scripts/ai_usage_report.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Write Database Reports/AI-Usage/last-summary.json from the local ledger. No network."""  # info: """Write Database Reports/AI-Usage/last-summary.json from the local ledger. No network."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # info: sys . path . insert ( 0 ,
import ai_usage  # noqa: E402


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    summary = ai_usage.summary(days=30)  # info: set summary
    out = ai_usage.data_dir() / "last-summary.json"  # info: set out
    out.parent.mkdir(parents=True, exist_ok=True)  # info: out . parent . mkdir ( parents =
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")  # info: out . write_text ( json . dumps (
    ts = datetime.now(timezone.utc).isoformat()  # info: set ts
    ai_usage._log(f"{ts} summary path={out.name} calls={summary.get('totals', {}).get('calls', 0)}")  # info: ai_usage . _log ( f" { ts }
    print(json.dumps({"ok": True, "path": str(out), "totals": summary.get("totals")}, indent=2))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
