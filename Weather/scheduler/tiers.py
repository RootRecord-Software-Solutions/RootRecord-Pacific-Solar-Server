# ==============================================================================
# FILE: Weather/scheduler/tiers.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Reads config/tiers.yaml, decides what's due to run right now.

Pure decision logic -- no HTTP, no dispatch. scheduler/run_cycle.py calls
into this to ask "is tier N due?" and does the actual dispatching itself.

KNOWN SIMPLIFICATION (flagged honestly rather than silently assumed): the
plan's tier table is per-RESOURCE, but several fetch/ modules mix resources
of different tiers in one file (e.g. fetch/radar.py has a Tier 6 image and
a Tier 5 text status; fetch/climate.py spans Tier 5 climate summaries and
Tier 5 obhistory). Dispatch below is done at the MODULE level, on the
FASTEST (lowest-numbered) tier cadence among that module's own resources,
via MODULE_MIN_TIER. This means a module's slower-tier resources get
checked more often than their own tier strictly requires -- harmless for
correctness (core/change_detection.py still no-ops an unchanged resource
every time, per-host rate floors in core/http_client.py are still
respected), just not maximally efficient. Splitting mixed-tier modules
further, or moving to true per-resource scheduling, is listed as pending
work in BUILD_STATUS.md rather than solved here.
"""
from __future__ import annotations  # info: from __future__ import annotations

from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

import yaml  # info: import yaml

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"  # info: set _CONFIG_DIR

# module name (matches fetch/<name>.py) -> fastest tier among its resources.
# Derived by hand from config/resources.yaml's own category comments; revisit
# if a module's resource mix changes.
# ====================================================
# SECTION: MODULE_MIN_TIER
# What it does: Set MODULE_MIN_TIER.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
MODULE_MIN_TIER: dict[str, int] = {  # info: set MODULE_MIN_TIER
    "alerts": 0,  # info: "alerts" : 0 ,
    "text_products": 1,  # info: "text_products" : 1 ,
    "satellite": 2,  # info: "satellite" : 2 ,
    "analyses": 3,  # info: "analyses" : 3 ,
    "marine": 4,  # info: "marine" : 4 ,
    "aviation": 4,  # info: "aviation" : 4 ,
    "maps": 6,        # gfe_graphics only
    "radar": 5,        # loop gif is tier 6, FTM status text is tier 5 -- min is 5
    "climate": 5,      # also covers fetch_observations()
    "ndfd_gridpoint": 6,  # info: "ndfd_gridpoint" : 6 ,
    "misc": 1,        # includes NHC GTWO resources; host floor still applies
    "gis": 6,  # info: "gis" : 6 ,
}  # info: }


# ====================================================
# SECTION: function load_tiers_config
# What it does: load tiers config.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_tiers_config() -> dict[str, Any]:  # info: def load_tiers_config
    with open(_CONFIG_DIR / "tiers.yaml", encoding="utf-8") as f:  # info: with open ( _CONFIG_DIR / "tiers.yaml" , encoding
        return yaml.safe_load(f)  # info: return yaml . safe_load ( f )


# ====================================================
# SECTION: function cadence_seconds
# What it does: cadence seconds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cadence_seconds(tier: int) -> float:  # info: def cadence_seconds
    config = load_tiers_config()  # info: set config
    tier_def = config["tiers"][tier]  # info: set tier_def
    return float(tier_def["cadence_seconds"])  # info: return float ( tier_def [ "cadence_seconds" ] )


# ====================================================
# SECTION: function is_due
# What it does: True if `tier`'s cadence has elapsed since `last_run_monotonic` (None means "never run yet" -> always due).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_due(*, last_run_monotonic: float | None, now_monotonic: float, tier: int) -> bool:  # info: def is_due
    """True if `tier`'s cadence has elapsed since `last_run_monotonic`
    (None means "never run yet" -> always due)."""
    if last_run_monotonic is None:  # info: if last_run_monotonic is None :
        return True  # info: return True
    return (now_monotonic - last_run_monotonic) >= cadence_seconds(tier)  # info: return ( now_monotonic - last_run_monotonic ) >= cadence_seconds


# ====================================================
# SECTION: function module_tier
# What it does: module tier.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def module_tier(module_name: str) -> int:  # info: def module_tier
    return MODULE_MIN_TIER[module_name]  # info: return MODULE_MIN_TIER [ module_name ]
