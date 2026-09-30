# ==============================================================================
# FILE: Security/DirectoryBrowser/scripts/DirectoryBrowser/__init__.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""One-level directory listing. Importing this package does not open a port."""  # info: """One-level directory listing. Importing this package does not open a port."""

from .list_dir import list_dir  # info: from . list_dir import list_dir

__all__ = ["list_dir"]  # info: set __all__
