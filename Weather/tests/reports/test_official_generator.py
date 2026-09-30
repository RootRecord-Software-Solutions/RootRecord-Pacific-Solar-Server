# ==============================================================================
# FILE: Weather/tests/reports/test_official_generator.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
from reports.official_generator import _source_name  # info: from reports . official_generator import _source_name


# ====================================================
# SECTION: function test_nws_sources_group_together
# What it does: test nws sources group together.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_nws_sources_group_together():  # info: def test_nws_sources_group_together
    assert _source_name("https://api.weather.gov/products/types/AFD/locations/HFO") == "NWS-HFO"  # info: assert _source_name ( "https://api.weather.gov/products/types/AFD/locations/HFO" ) == "NWS-HFO"
    assert _source_name("https://www.weather.gov/hfo/office_products") == "NWS-HFO"  # info: assert _source_name ( "https://www.weather.gov/hfo/office_products" ) == "NWS-HFO"
    assert _source_name("https://forecast.weather.gov/product.php?site=HFO") == "NWS-HFO"  # info: assert _source_name ( "https://forecast.weather.gov/product.php?site=HFO" ) == "NWS-HFO"


# ====================================================
# SECTION: function test_nhc_isolated
# What it does: test nhc isolated.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_nhc_isolated():  # info: def test_nhc_isolated
    assert _source_name("https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=7") == "NHC"  # info: assert _source_name ( "https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=7" ) == "NHC"


# ====================================================
# SECTION: function test_noaa_nesdis_isolated
# What it does: test noaa nesdis isolated.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_noaa_nesdis_isolated():  # info: def test_noaa_nesdis_isolated
    assert _source_name("https://www.noaa.gov/") == "NOAA"  # info: assert _source_name ( "https://www.noaa.gov/" ) == "NOAA"
    assert _source_name("https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/") == "NOAA-NESDIS"  # info: assert _source_name ( "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/" ) == "NOAA-NESDIS"


# ====================================================
# SECTION: function test_relative_hfo_source_normalizes_to_nws
# What it does: test relative hfo source normalizes to nws.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_relative_hfo_source_normalizes_to_nws():  # info: def test_relative_hfo_source_normalizes_to_nws
    assert _source_name("/hfo/surfreports") == "NWS-HFO"  # info: assert _source_name ( "/hfo/surfreports" ) == "NWS-HFO"


# ====================================================
# SECTION: function test_gml_source_isolated
# What it does: test gml source isolated.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_gml_source_isolated():  # info: def test_gml_source_isolated
    assert _source_name("https://gml.noaa.gov/grad/solcalc/table.php?lat=21.3&lon=-157.85") == "NOAA-GML"  # info: assert _source_name ( "https://gml.noaa.gov/grad/solcalc/table.php?lat=21.3&lon=-157.85" ) == "NOAA-GML"
