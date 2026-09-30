# ==============================================================================
# FILE: Weather/tests/reports/test_banner.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
from pathlib import Path  # info: from pathlib import Path
import tempfile  # info: import tempfile

from PIL import Image  # info: from PIL import Image

from reports.banner import CROP_BOX, OUTPUT_RELATIVE, TARGET_SIZE, generate_readme_banner  # info: from reports . banner import CROP_BOX , OUTPUT_RELATIVE


# ====================================================
# SECTION: function _make_source
# What it does:  make source.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _make_source(base: Path) -> Path:  # info: def _make_source
    source = base / (  # info: set source
        "cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/"  # info: "cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/"
        "GOES18-HI-GEOCOLOR-600x600/GOES18-HI-GEOCOLOR-600x600_current.gif"  # info: "GOES18-HI-GEOCOLOR-600x600/GOES18-HI-GEOCOLOR-600x600_current.gif"
    )  # info: )
    source.parent.mkdir(parents=True)  # info: source . parent . mkdir ( parents =
    frames = []  # info: set frames
    for index in range(3):  # info: for index in range ( 3 ) :
        image = Image.new("RGB", (600, 600), (index * 60, 40, 120))  # info: set image
        frames.append(image)  # info: frames . append ( image )
    frames[0].save(  # info: frames [ 0 ] . save (
        source,  # info: source ,
        save_all=True,  # info: set save_all
        append_images=frames[1:],  # info: set append_images
        duration=[80, 100, 120],  # info: set duration
        loop=0,  # info: set loop
    )  # info: )
    return source  # info: return source


# ====================================================
# SECTION: function test_banner_is_locked_size_and_preserves_animation
# What it does: test banner is locked size and preserves animation.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_banner_is_locked_size_and_preserves_animation():  # info: def test_banner_is_locked_size_and_preserves_animation
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        base = Path(tmp)  # info: set base
        source = _make_source(base)  # info: set source
        output = generate_readme_banner(base)  # info: set output

        assert output == base.parent / OUTPUT_RELATIVE  # info: assert output == base . parent / OUTPUT_RELATIVE
        assert output.is_file()  # info: assert output . is_file ( )
        assert source.read_bytes() != output.read_bytes()  # info: assert source . read_bytes ( ) != output

        with Image.open(source) as original, Image.open(output) as banner:  # info: with Image . open ( source ) as
            assert original.size == (600, 600)  # info: assert original . size == ( 600 ,
            assert banner.size == TARGET_SIZE  # info: assert banner . size == TARGET_SIZE
            assert TARGET_SIZE == (1122, 449)  # info: assert TARGET_SIZE == ( 1122 , 449 )
            assert CROP_BOX == (0, 280, 600, 520)  # info: assert CROP_BOX == ( 0 , 280 ,
            assert getattr(banner, "n_frames", 1) == 3  # info: assert getattr ( banner , "n_frames" , 1
            assert banner.info.get("loop") == 0  # info: assert banner . info . get ( "loop"


# ====================================================
# SECTION: function test_banner_does_not_modify_source
# What it does: test banner does not modify source.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_banner_does_not_modify_source():  # info: def test_banner_does_not_modify_source
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        base = Path(tmp)  # info: set base
        source = _make_source(base)  # info: set source
        before = source.read_bytes()  # info: set before
        generate_readme_banner(base)  # info: call generate_readme_banner
        assert source.read_bytes() == before  # info: assert source . read_bytes ( ) == before
