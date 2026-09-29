from pathlib import Path
import tempfile

from PIL import Image

from reports.banner import CROP_BOX, OUTPUT_RELATIVE, TARGET_SIZE, generate_readme_banner


def _make_source(base: Path) -> Path:
    source = base / (
        "cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/"
        "GOES18-HI-GEOCOLOR-600x600/GOES18-HI-GEOCOLOR-600x600_current.gif"
    )
    source.parent.mkdir(parents=True)
    frames = []
    for index in range(3):
        image = Image.new("RGB", (600, 600), (index * 60, 40, 120))
        frames.append(image)
    frames[0].save(
        source,
        save_all=True,
        append_images=frames[1:],
        duration=[80, 100, 120],
        loop=0,
    )
    return source


def test_banner_is_locked_size_and_preserves_animation():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = _make_source(base)
        output = generate_readme_banner(base)

        assert output == base.parent / OUTPUT_RELATIVE
        assert output.is_file()
        assert source.read_bytes() != output.read_bytes()

        with Image.open(source) as original, Image.open(output) as banner:
            assert original.size == (600, 600)
            assert banner.size == TARGET_SIZE
            assert TARGET_SIZE == (1122, 449)
            assert CROP_BOX == (0, 280, 600, 520)
            assert getattr(banner, "n_frames", 1) == 3
            assert banner.info.get("loop") == 0


def test_banner_does_not_modify_source():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = _make_source(base)
        before = source.read_bytes()
        generate_readme_banner(base)
        assert source.read_bytes() == before
