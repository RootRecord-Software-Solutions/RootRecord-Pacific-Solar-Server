"""Regression tests for clean report text extraction and README rendering."""
from reports.generator import (
    _build_readme_sections,
    _cell_text,
    _html_to_text,
    _normalize_inline_whitespace,
    _parse_rwr_stations,
    _pre_product_text,
    _render_readme,
    _strip_chrome,
)


def test_normalize_does_not_strip_letter_t():
    text = "Light rain; East 25 gusts to 37; Information Act"
    out = _normalize_inline_whitespace(text)
    assert out == text
    assert "t" in out
    assert "Light" in out
    assert "gusts" in out
    assert "to" in out


def test_cell_text_preserves_words():
    assert _cell_text("Light rain") == "Light rain"
    assert _cell_text("East 25 gusts to 37") == "East 25 gusts to 37"
    assert _cell_text("  Fair   ") == "Fair"


def test_pre_product_preserves_fixed_width_spacing():
    raw = """<html><body><pre>
WEATHER ITEM   OBSERVED TIME
  MAXIMUM         88   1156 AM
</pre><footer>Privacy Policy</footer></body></html>"""
    body = _pre_product_text(raw)
    assert body is not None
    assert "WEATHER ITEM   OBSERVED TIME" in body
    assert "  MAXIMUM         88" in body
    assert "Privacy Policy" not in body


def test_html_to_text_prefers_pre_over_chrome():
    raw = """<html><body>
<div>National Weather Service Home</div>
<pre>
CLIMATE REPORT
  MAXIMUM         88
</pre>
<div>Freedom of Information Act</div>
</body></html>"""
    text = _html_to_text(raw, preserve_pre=True)
    assert "CLIMATE REPORT" in text
    assert "  MAXIMUM         88" in text
    assert "Freedom of Information Act" not in text


def test_parse_rwr_stations_maps_each_icao():
    raw = """
    <table>
    <tr><td><a href="http://www.weather.gov/data/obhistory/PHNL.html">HONOLULU</a></td>
        <td>Fair</td><td>84</td><td>70</td><td>63</td><td>Northeast 12</td><td>30.01</td><td></td></tr>
    <tr><td><a href="http://www.weather.gov/data/obhistory/PHLI.html">LIHUE APT</a></td>
        <td>Light rain</td><td>78</td><td>73</td><td>84</td><td>East 25 gusts to 37</td><td>29.97R</td><td></td></tr>
    </table>
    """
    stations = _parse_rwr_stations(raw)
    assert stations["PHNL"]["conditions"] == "Fair"
    assert stations["PHNL"]["temp"] == "84"
    assert stations["PHLI"]["conditions"] == "Light rain"
    assert stations["PHLI"]["wind"] == "East 25 gusts to 37"


def test_strip_chrome_cuts_footer():
    text = "PRODUCT BODY\n\nPrivacy Policy\nUSA.gov"
    assert _strip_chrome(text) == "PRODUCT BODY"


def test_build_readme_sections_formats_product_blocks():
    sections = [
        (
            "cli_daily_climate_summary_HNL",
            "Daily Climate Summary — HNL",
            "https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=HNL",
            "2026-09-25T18:15:57-10:00",
            "CLIMATE REPORT\nHONOLULU",
        )
    ]
    body = _build_readme_sections(sections)
    assert "### 1. Daily Climate Summary — HNL" in body
    assert "```text" in body
    assert "CLIMATE REPORT" in body


def test_render_readme_replaces_all_placeholders():
    template = "\n".join([
        "Banner: {{README_BANNER_URL}}",
        "Conditions: {{CURRENT_CONDITIONS}}",
        "Updated: {{REPORT_UPDATED}}",
        "Count: {{REPORT_SECTION_COUNT}}",
        "Sections:",
        "{{REPORT_SECTIONS}}",
        "",
    ])
    rendered = _render_readme(
        template,
        {
            "{{README_BANNER_URL}}": "https://example.test/banner.gif",
            "{{CURRENT_CONDITIONS}}": "| Honolulu | Fair |",
            "{{REPORT_UPDATED}}": "2026-09-25T21:00:00-10:00 HST",
            "{{REPORT_SECTION_COUNT}}": "1",
            "{{REPORT_SECTIONS}}": "### 1. Example",
        },
    )
    assert "{{" not in rendered
    assert rendered.endswith("\n")
