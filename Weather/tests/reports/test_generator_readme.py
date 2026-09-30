# ==============================================================================
# FILE: Weather/tests/reports/test_generator_readme.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Regression tests for clean report text extraction and README rendering."""  # info: """Regression tests for clean report text extraction and README rendering."""
from reports.generator import (  # info: from reports . generator import (
    _build_readme_sections,  # info: _build_readme_sections ,
    _cell_text,  # info: _cell_text ,
    _html_to_text,  # info: _html_to_text ,
    _normalize_inline_whitespace,  # info: _normalize_inline_whitespace ,
    _parse_rwr_stations,  # info: _parse_rwr_stations ,
    _pre_product_text,  # info: _pre_product_text ,
    _render_readme,  # info: _render_readme ,
    _strip_chrome,  # info: _strip_chrome ,
)  # info: )


# ====================================================
# SECTION: function test_normalize_does_not_strip_letter_t
# What it does: test normalize does not strip letter t.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_normalize_does_not_strip_letter_t():  # info: def test_normalize_does_not_strip_letter_t
    text = "Light rain; East 25 gusts to 37; Information Act"  # info: set text
    out = _normalize_inline_whitespace(text)  # info: set out
    assert out == text  # info: assert out == text
    assert "t" in out  # info: assert "t" in out
    assert "Light" in out  # info: assert "Light" in out
    assert "gusts" in out  # info: assert "gusts" in out
    assert "to" in out  # info: assert "to" in out


# ====================================================
# SECTION: function test_cell_text_preserves_words
# What it does: test cell text preserves words.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_cell_text_preserves_words():  # info: def test_cell_text_preserves_words
    assert _cell_text("Light rain") == "Light rain"  # info: assert _cell_text ( "Light rain" ) == "Light rain"
    assert _cell_text("East 25 gusts to 37") == "East 25 gusts to 37"  # info: assert _cell_text ( "East 25 gusts to 37" ) == "East 25 gusts to 37"
    assert _cell_text("  Fair   ") == "Fair"  # info: assert _cell_text ( " Fair " ) == "Fair"


# ====================================================
# SECTION: function test_pre_product_preserves_fixed_width_spacing
# What it does: test pre product preserves fixed width spacing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_pre_product_preserves_fixed_width_spacing():  # info: def test_pre_product_preserves_fixed_width_spacing
    raw = """<html><body><pre>
WEATHER ITEM   OBSERVED TIME
  MAXIMUM         88   1156 AM
</pre><footer>Privacy Policy</footer></body></html>"""
    body = _pre_product_text(raw)  # info: set body
    assert body is not None  # info: assert body is not None
    assert "WEATHER ITEM   OBSERVED TIME" in body  # info: assert "WEATHER ITEM OBSERVED TIME" in body
    assert "  MAXIMUM         88" in body  # info: assert " MAXIMUM 88" in body
    assert "Privacy Policy" not in body  # info: assert "Privacy Policy" not in body


# ====================================================
# SECTION: function test_html_to_text_prefers_pre_over_chrome
# What it does: test html to text prefers pre over chrome.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_html_to_text_prefers_pre_over_chrome():  # info: def test_html_to_text_prefers_pre_over_chrome
    raw = """<html><body>
<div>National Weather Service Home</div>
<pre>
CLIMATE REPORT
  MAXIMUM         88
</pre>
<div>Freedom of Information Act</div>
</body></html>"""
    text = _html_to_text(raw, preserve_pre=True)  # info: set text
    assert "CLIMATE REPORT" in text  # info: assert "CLIMATE REPORT" in text
    assert "  MAXIMUM         88" in text  # info: assert " MAXIMUM 88" in text
    assert "Freedom of Information Act" not in text  # info: assert "Freedom of Information Act" not in text


# ====================================================
# SECTION: function test_parse_rwr_stations_maps_each_icao
# What it does: test parse rwr stations maps each icao.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_parse_rwr_stations_maps_each_icao():  # info: def test_parse_rwr_stations_maps_each_icao
    raw = """
    <table>
    <tr><td><a href="http://www.weather.gov/data/obhistory/PHNL.html">HONOLULU</a></td>
        <td>Fair</td><td>84</td><td>70</td><td>63</td><td>Northeast 12</td><td>30.01</td><td></td></tr>
    <tr><td><a href="http://www.weather.gov/data/obhistory/PHLI.html">LIHUE APT</a></td>
        <td>Light rain</td><td>78</td><td>73</td><td>84</td><td>East 25 gusts to 37</td><td>29.97R</td><td></td></tr>
    </table>
    """
    stations = _parse_rwr_stations(raw)  # info: set stations
    assert stations["PHNL"]["conditions"] == "Fair"  # info: assert stations [ "PHNL" ] [ "conditions" ]
    assert stations["PHNL"]["temp"] == "84"  # info: assert stations [ "PHNL" ] [ "temp" ]
    assert stations["PHLI"]["conditions"] == "Light rain"  # info: assert stations [ "PHLI" ] [ "conditions" ]
    assert stations["PHLI"]["wind"] == "East 25 gusts to 37"  # info: assert stations [ "PHLI" ] [ "wind" ]


# ====================================================
# SECTION: function test_strip_chrome_cuts_footer
# What it does: test strip chrome cuts footer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_strip_chrome_cuts_footer():  # info: def test_strip_chrome_cuts_footer
    text = "PRODUCT BODY\n\nPrivacy Policy\nUSA.gov"  # info: set text
    assert _strip_chrome(text) == "PRODUCT BODY"  # info: assert _strip_chrome ( text ) == "PRODUCT BODY"


# ====================================================
# SECTION: function test_build_readme_sections_formats_product_blocks
# What it does: test build readme sections formats product blocks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_build_readme_sections_formats_product_blocks():  # info: def test_build_readme_sections_formats_product_blocks
    sections = [  # info: set sections
        (  # info: call (
            "cli_daily_climate_summary_HNL",  # info: "cli_daily_climate_summary_HNL" ,
            "Daily Climate Summary — HNL",  # info: "Daily Climate Summary — HNL" ,
            "https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=HNL",  # info: "https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=HNL" ,
            "2026-09-25T18:15:57-10:00",  # info: "2026-09-25T18:15:57-10:00" ,
            "CLIMATE REPORT\nHONOLULU",  # info: "CLIMATE REPORT\nHONOLULU" ,
        )  # info: )
    ]  # info: ]
    body = _build_readme_sections(sections)  # info: set body
    assert "### 1. Daily Climate Summary — HNL" in body
    assert "```text" in body  # info: assert "```text" in body
    assert "CLIMATE REPORT" in body  # info: assert "CLIMATE REPORT" in body


# ====================================================
# SECTION: function test_render_readme_replaces_all_placeholders
# What it does: test render readme replaces all placeholders.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_render_readme_replaces_all_placeholders():  # info: def test_render_readme_replaces_all_placeholders
    template = "\n".join([  # info: set template
        "Banner: {{README_BANNER_URL}}",  # info: "Banner: {{README_BANNER_URL}}" ,
        "Conditions: {{CURRENT_CONDITIONS}}",  # info: "Conditions: {{CURRENT_CONDITIONS}}" ,
        "Updated: {{REPORT_UPDATED}}",  # info: "Updated: {{REPORT_UPDATED}}" ,
        "Count: {{REPORT_SECTION_COUNT}}",  # info: "Count: {{REPORT_SECTION_COUNT}}" ,
        "Sections:",  # info: "Sections:" ,
        "{{REPORT_SECTIONS}}",  # info: "{{REPORT_SECTIONS}}" ,
        "",  # info: "" ,
    ])  # info: ] )
    rendered = _render_readme(  # info: set rendered
        template,  # info: template ,
        {  # info: {
            "{{README_BANNER_URL}}": "https://example.test/banner.gif",  # info: "{{README_BANNER_URL}}" : "https://example.test/banner.gif" ,
            "{{CURRENT_CONDITIONS}}": "| Honolulu | Fair |",  # info: "{{CURRENT_CONDITIONS}}" : "| Honolulu | Fair |" ,
            "{{REPORT_UPDATED}}": "2026-09-25T21:00:00-10:00 HST",  # info: "{{REPORT_UPDATED}}" : "2026-09-25T21:00:00-10:00 HST" ,
            "{{REPORT_SECTION_COUNT}}": "1",  # info: "{{REPORT_SECTION_COUNT}}" : "1" ,
            "{{REPORT_SECTIONS}}": "### 1. Example",
        },  # info: } ,
    )  # info: )
    assert "{{" not in rendered  # info: assert "{{" not in rendered
    assert rendered.endswith("\n")  # info: assert rendered . endswith ( "\n" )
