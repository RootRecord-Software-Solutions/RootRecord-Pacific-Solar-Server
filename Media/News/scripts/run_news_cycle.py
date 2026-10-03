#!/usr/bin/env python3
# ==============================================================================
# FILE: Media/News/scripts/run_news_cycle.py
# What this file is: Pacific :35 entrypoint — poll News Data, four lanes, stitch, push.
# Kind: python
# ==============================================================================
"""One news cycle at :35: poll → lane scripts → numbered TTS → Pacific stitch WAV.

Push is off by default in the jobs env (`RR_RADIO_PUSH=0`). The :42 hour batch
folds `news_update_current.wav` after the desk reports into `report_current`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PACIFIC = Path(__file__).resolve().parents[3]
ML1 = Path(
    os.environ.get(
        "RR_ML1_ROOT",
        "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/2 - RootRecord-US-Mainland-One",
    )
)
VENDOR = PACIFIC / "Media" / "News" / "radiorss" / "scripts"
DB = Path(
    os.environ.get(
        "RR_DATABASE_ROOT",
        "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
    )
)
NEWS_ROOT = Path(
    os.environ.get(
        "RR_NEWS_DATA_ROOT",
        str(DB / "Media" / "News Data"),
    )
)


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    speak = "--no-speak" not in args
    os.environ.setdefault("RR_DATABASE_ROOT", str(DB))
    os.environ.setdefault("RR_NEWS_DATA_ROOT", str(NEWS_ROOT))
    os.environ.setdefault("RR_PACIFIC_ROOT", str(PACIFIC))
    os.environ.setdefault("RR_RADIO_RSS_CONFIG", str(PACIFIC / "Media" / "News" / "radiorss" / "config"))
    if str(VENDOR) not in sys.path:
        sys.path.insert(0, str(VENDOR))
    NEWS_ROOT.mkdir(parents=True, exist_ok=True)
    from common import ROOT  # noqa: E402
    from registry import load_registry  # noqa: E402
    from store import connect  # noqa: E402
    from news_hour import news_hour  # noqa: E402

    registry = load_registry()
    conn = connect(ROOT)
    try:
        result = news_hour(registry, conn, speak=speak, root=ROOT)
    finally:
        conn.close()
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
