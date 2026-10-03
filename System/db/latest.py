# ==============================================================================
# FILE: System/db/latest.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Read the newest host sample from System/system.db for JSON exporters."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

from pathlib import Path  # info: from pathlib import Path

from db.store import connect  # info: from db . store import connect
import paths  # info: import paths


# ====================================================
# SECTION: function latest_snapshot
# What it does: Return the newest observation in the same shape as the old host-last.json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def latest_snapshot(db_path: Path | None = None) -> dict | None:  # info: def latest_snapshot
    conn = connect(db_path or paths.SYSTEM_DB)  # info: set conn
    try:  # info: try
        row = conn.execute(  # info: set row
            "SELECT observation_id, observed_at, host, source FROM observation ORDER BY observed_at DESC LIMIT 1"  # info: newest row
        ).fetchone()  # info: fetchone
        if not row:  # info: if not row
            return None  # info: return None
        fields = {}  # info: set fields
        for metric in conn.execute(  # info: for metric in conn . execute
            "SELECT metric_key, value_num, unit, state FROM measurement WHERE observation_id=?",  # info: this observation
            (row["observation_id"],),  # info: id
        ):  # info: end for
            fields[metric["metric_key"]] = {  # info: fields [ metric ]
                "value": metric["value_num"],  # info: "value"
                "unit": metric["unit"],  # info: "unit"
                "state": metric["state"],  # info: "state"
            }  # info: end field
        return {  # info: return
            "alias": "host",  # info: "alias"
            "host": row["host"],  # info: "host"
            "fields": fields,  # info: "fields"
            "at": row["observed_at"],  # info: "at"
            "source": row["source"] or "proc",  # info: "source"
        }  # info: end return
    finally:  # info: finally
        conn.close()  # info: conn . close
