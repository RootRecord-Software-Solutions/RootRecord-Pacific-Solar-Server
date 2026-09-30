# ==============================================================================
# FILE: Weather/reports/banner.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Generate the processed GOES-18 Hawaii GeoColor GIF used by the README.

This is a presentation-only processor. It reads the collected raw GIF and
writes a separate banner copy; the raw weather-data product is never modified.

Output is a fixed wide island strip (not the full square sector) so the README
banner stays compact and consistent on every update.
"""
from __future__ import annotations  # info: from __future__ import annotations

from pathlib import Path  # info: from pathlib import Path

from PIL import Image, ImageSequence  # info: from PIL import Image , ImageSequence

SOURCE_RELATIVE = Path(  # info: set SOURCE_RELATIVE
    "cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/"  # info: "cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/"
    "GOES18-HI-GEOCOLOR-600x600/GOES18-HI-GEOCOLOR-600x600_current.gif"  # info: "GOES18-HI-GEOCOLOR-600x600/GOES18-HI-GEOCOLOR-600x600_current.gif"
)  # info: )
OUTPUT_RELATIVE = Path("reports/assets/GOES18-HI-GEOCOLOR-README-banner.gif")  # info: set OUTPUT_RELATIVE

# Full-width horizontal band through the Hawaiian Islands (600x600 HI sector).
# Lowered so the entire chain — Kauaʻi through the Big Island — is in frame.
# X spans edge-to-edge (0..600). Stays above the NESDIS label strip (~y 580).
CROP_BOX = (0, 280, 600, 520)  # 600 x 240
# Presentation size matched to crop aspect (~2.5:1). Displayed at 100% width.
TARGET_SIZE = (1122, 449)  # info: set TARGET_SIZE
EXPECTED_SOURCE_SIZE = (600, 600)  # info: set EXPECTED_SOURCE_SIZE


# ====================================================
# SECTION: function generate_readme_banner
# What it does: Create the README banner from the current raw GOES-18 GIF.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def generate_readme_banner(base_dir: str | Path) -> Path:  # info: def generate_readme_banner
    """Create the README banner from the current raw GOES-18 GIF."""  # info: """Create the README banner from the current raw GOES-18 GIF."""
    base = Path(base_dir)  # info: set base
    source = base / SOURCE_RELATIVE  # info: set source
    output = base.parent / OUTPUT_RELATIVE  # info: set output

    if not source.is_file():  # info: if not source . is_file ( ) :
        raise FileNotFoundError("GOES-18 GeoColor source GIF not found: {}".format(source))  # info: raise FileNotFoundError ( "GOES-18 GeoColor source GIF not found: {}" . format ( source

    output.parent.mkdir(parents=True, exist_ok=True)  # info: output . parent . mkdir ( parents =

    with Image.open(source) as src:  # info: with Image . open ( source ) as
        if src.size != EXPECTED_SOURCE_SIZE:  # info: if src . size != EXPECTED_SOURCE_SIZE :
            raise ValueError(  # info: raise ValueError (
                "Unexpected GOES-18 GeoColor size: {} (expected {})".format(  # info: "Unexpected GOES-18 GeoColor size: {} (expected {})" . format (
                    src.size, EXPECTED_SOURCE_SIZE  # info: src . size , EXPECTED_SOURCE_SIZE
                )  # info: )
            )  # info: )

        frames = []  # info: set frames
        durations = []  # info: set durations

        for frame in ImageSequence.Iterator(src):  # info: for frame in ImageSequence . Iterator ( src
            cropped = frame.copy().convert("RGBA").crop(CROP_BOX)  # info: set cropped
            resized = cropped.resize(TARGET_SIZE, Image.Resampling.LANCZOS)  # info: set resized
            frames.append(  # info: frames . append (
                resized.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)  # info: resized . convert ( "P" , palette =
            )  # info: )
            durations.append(frame.info.get("duration", src.info.get("duration", 80)))  # info: durations . append ( frame . info .

        if not frames:  # info: if not frames :
            raise ValueError("GOES-18 GeoColor GIF contains no frames")  # info: raise ValueError ( "GOES-18 GeoColor GIF contains no frames" )

        frames[0].save(  # info: frames [ 0 ] . save (
            output,  # info: output ,
            format="GIF",  # info: set format
            save_all=True,  # info: set save_all
            append_images=frames[1:],  # info: set append_images
            duration=durations,  # info: set duration
            loop=0,  # info: set loop
            optimize=False,  # info: set optimize
            disposal=2,  # info: set disposal
        )  # info: )

    if not output.is_file():  # info: if not output . is_file ( ) :
        raise RuntimeError("README banner was not created: {}".format(output))  # info: raise RuntimeError ( "README banner was not created: {}" . format ( output

    with Image.open(output) as check:  # info: with Image . open ( output ) as
        if check.size != TARGET_SIZE:  # info: if check . size != TARGET_SIZE :
            raise RuntimeError(  # info: raise RuntimeError (
                "README banner size mismatch: {} (expected {})".format(  # info: "README banner size mismatch: {} (expected {})" . format (
                    check.size, TARGET_SIZE  # info: check . size , TARGET_SIZE
                )  # info: )
            )  # info: )

    return output  # info: return output


# ====================================================
# SECTION: __all__
# What it does: Set __all__.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
__all__ = [  # info: set __all__
    "generate_readme_banner",  # info: "generate_readme_banner" ,
    "SOURCE_RELATIVE",  # info: "SOURCE_RELATIVE" ,
    "OUTPUT_RELATIVE",  # info: "OUTPUT_RELATIVE" ,
    "TARGET_SIZE",  # info: "TARGET_SIZE" ,
    "CROP_BOX",  # info: "CROP_BOX" ,
]  # info: ]
