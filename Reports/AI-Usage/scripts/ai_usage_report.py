#!/usr/bin/env python3
"""Write Database Reports/AI-Usage/last-summary.json from the local ledger. No network."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_usage  # noqa: E402


def main() -> int:
    summary = ai_usage.summary(days=30)
    out = ai_usage.data_dir() / "last-summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    ts = datetime.now(timezone.utc).isoformat()
    ai_usage._log(f"{ts} summary path={out.name} calls={summary.get('totals', {}).get('calls', 0)}")
    print(json.dumps({"ok": True, "path": str(out), "totals": summary.get("totals")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
