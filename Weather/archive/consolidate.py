"""Thin wrapper around core/daily_zip.py -- decides *when* and *where*,
per nws_plan.md Section 8. The actual zip/verify/delete mechanics live in
core/daily_zip.py; this file owns none of that, per archive/README.md.
"""
from __future__ import annotations

import logging

from core.daily_zip import ConsolidationResult, consolidate_day

logger = logging.getLogger("weather.archive")


def consolidate_yesterday(base_dir: str, date_folder: str) -> ConsolidationResult:
    """Called by scheduler/run_cycle.py exactly once, right after it
    detects an HST calendar-date rollover. `date_folder` is the HST
    MM-DD-YYYY of the day that just closed (already computed by the
    scheduler from core/hst_time.hst_date_folder before the rollover).
    """
    result = consolidate_day(base_dir, date_folder)

    if result.status == "nothing_to_do":
        logger.info("Daily consolidation for %s: nothing to zip (no resource changed that day).", date_folder)
    elif result.status == "verification_failed":
        logger.error(
            "Daily consolidation for %s FAILED verification (%d files discovered, %d written) -- "
            "original archive/ folders left untouched, zip left at %s for inspection.",
            date_folder, result.files_discovered, result.files_written, result.zip_path,
        )
    else:
        logger.info(
            "Daily consolidation for %s: %d files zipped to %s, %d dated archive/ folders removed.",
            date_folder, result.files_written, result.zip_path, result.deleted_source_dirs,
        )

    return result
