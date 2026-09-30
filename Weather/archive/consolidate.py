# ==============================================================================
# FILE: Weather/archive/consolidate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Thin wrapper around core/daily_zip.py -- decides *when* and *where*,
per nws_plan.md Section 8. The actual zip/verify/delete mechanics live in
core/daily_zip.py; this file owns none of that, per archive/README.md.
"""
from __future__ import annotations  # info: from __future__ import annotations

import logging  # info: import logging

from core.daily_zip import ConsolidationResult, consolidate_day  # info: from core . daily_zip import ConsolidationResult , consolidate_day

logger = logging.getLogger("weather.archive")  # info: set logger


# ====================================================
# SECTION: function consolidate_yesterday
# What it does: Called by scheduler/run_cycle.py exactly once, right after it detects an HST calendar-date rollover. `date_folder` is the HST MM-DD-YYYY of the day that just closed (already comput
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def consolidate_yesterday(base_dir: str, date_folder: str) -> ConsolidationResult:  # info: def consolidate_yesterday
    """Called by scheduler/run_cycle.py exactly once, right after it
    detects an HST calendar-date rollover. `date_folder` is the HST
    MM-DD-YYYY of the day that just closed (already computed by the
    scheduler from core/hst_time.hst_date_folder before the rollover).
    """
    result = consolidate_day(base_dir, date_folder)  # info: set result

    if result.status == "nothing_to_do":  # info: if result . status == "nothing_to_do" :
        logger.info("Daily consolidation for %s: nothing to zip (no resource changed that day).", date_folder)  # info: logger . info ( "Daily consolidation for %s: nothing to zip (no resource changed that day)." , date_folder )
    elif result.status == "verification_failed":  # info: elif result . status == "verification_failed" :
        logger.error(  # info: logger . error (
            "Daily consolidation for %s FAILED verification (%d files discovered, %d written) -- "  # info: "Daily consolidation for %s FAILED verification (%d files discovered, %d written) -- "
            "original archive/ folders left untouched, zip left at %s for inspection.",  # info: "original archive/ folders left untouched, zip left at %s for inspection." ,
            date_folder, result.files_discovered, result.files_written, result.zip_path,  # info: date_folder , result . files_discovered , result .
        )  # info: )
    else:  # info: else :
        logger.info(  # info: logger . info (
            "Daily consolidation for %s: %d files zipped to %s, %d dated archive/ folders removed.",  # info: "Daily consolidation for %s: %d files zipped to %s, %d dated archive/ folders removed." ,
            date_folder, result.files_written, result.zip_path, result.deleted_source_dirs,  # info: date_folder , result . files_written , result .
        )  # info: )

    return result  # info: return result
