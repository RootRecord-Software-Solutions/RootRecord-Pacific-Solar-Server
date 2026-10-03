#!/usr/bin/env python3
"""Ad-hoc wrapper around generate_hour_reports.py (includes chime by default).

Production hour batch is generate_hour_reports.py (jobs.py voice_hour_batch at :43).
"""
from __future__ import annotations

import sys

from generate_hour_reports import main

if __name__ == "__main__":
    # Preserve old one-shot behavior: include chime unless caller already set flags.
    if "--include-chime" not in sys.argv and "--only" not in sys.argv:
        sys.argv.append("--include-chime")
    raise SystemExit(main())
