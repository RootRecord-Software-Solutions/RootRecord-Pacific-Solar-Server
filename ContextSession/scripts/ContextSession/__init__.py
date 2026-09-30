# ==============================================================================
# FILE: ContextSession/scripts/ContextSession/__init__.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Context session store. Importing this package does not open a port."""  # info: """Context session store. Importing this package does not open a port."""

from .store import DEFAULT_ROOT, SessionStore  # info: from . store import DEFAULT_ROOT , SessionStore

__all__ = ["DEFAULT_ROOT", "SessionStore", "create_app"]  # info: set __all__


# ====================================================
# SECTION: function create_app
# What it does: Load the FastAPI factory only when called. This package does not serve it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def create_app(root=None):  # info: def create_app
    """Load the FastAPI factory only when called. This package does not serve it."""  # info: """Load the FastAPI factory only when called. This package does not serve it."""
    from .api import create_app as _create_app  # info: from . api import create_app as _create_app

    return _create_app(root)  # info: return _create_app ( root )
