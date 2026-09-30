# ==============================================================================
# FILE: Media/CloudTTS/__init__.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Cloud TTS routing. Package name matches the folder."""  # info: """Cloud TTS routing. Package name matches the folder."""

from CloudTTS.scripts.route import route  # info: from CloudTTS . scripts . route import route

__all__ = ["route"]  # info: set __all__
