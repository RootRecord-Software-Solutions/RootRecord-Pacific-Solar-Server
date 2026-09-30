# ==============================================================================
# FILE: Media/MorningBootReplay/__init__.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Morning boot replay. Package name matches the folder."""  # info: """Morning boot replay. Package name matches the folder."""

from MorningBootReplay.scripts.replay import arm, disarm, run  # info: from MorningBootReplay . scripts . replay import arm

__all__ = ["arm", "disarm", "run"]  # info: set __all__
