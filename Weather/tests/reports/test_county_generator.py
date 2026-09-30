# ==============================================================================
# FILE: Weather/tests/reports/test_county_generator.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
from reports.county_generator import _targets  # info: from reports . county_generator import _targets

# ====================================================
# SECTION: function cfg
# What it does: cfg.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cfg():  # info: def cfg
    return {  # info: return {
        "counties": [  # info: "counties" : [
            {"key": "honolulu", "same": "HIC003", "aliases": ["Honolulu", "Oahu"]},  # info: { "key" : "honolulu" , "same" : "HIC003"
            {"key": "hawaii", "same": "HIC001", "aliases": ["Hawaii", "Big Island"]},  # info: { "key" : "hawaii" , "same" : "HIC001"
            {"key": "maui", "same": "HIC009", "aliases": ["Maui"]},  # info: { "key" : "maui" , "same" : "HIC009"
            {"key": "kauai", "same": "HIC007", "aliases": ["Kauai"]},  # info: { "key" : "kauai" , "same" : "HIC007"
            {"key": "kalawao", "same": "HIC005", "aliases": ["Kalawao"]},  # info: { "key" : "kalawao" , "same" : "HIC005"
        ],  # info: ] ,
        "statewide_resource_ids": ["state_report"],  # info: "statewide_resource_ids" : [ "state_report" ] ,
        "resource_routing": {"county_patterns": {"hawaii": ["hilo"]}},  # info: "resource_routing" : { "county_patterns" : { "hawaii" :
    }  # info: }

# ====================================================
# SECTION: function test_statewide_all
# What it does: test statewide all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_statewide_all():  # info: def test_statewide_all
    found, scope = _targets("state_report", "x", cfg())  # info: found , scope = _targets ( "state_report" ,
    assert found == {"honolulu", "hawaii", "maui", "kauai", "kalawao"}  # info: assert found == { "honolulu" , "hawaii" ,
    assert scope == "statewide"  # info: assert scope == "statewide"

# ====================================================
# SECTION: function test_resource_route
# What it does: test resource route.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_resource_route():  # info: def test_resource_route
    found, scope = _targets("hilo_forecast", "x", cfg())  # info: found , scope = _targets ( "hilo_forecast" ,
    assert found == {"hawaii"}  # info: assert found == { "hawaii" }
    assert scope == "explicit-resource"  # info: assert scope == "explicit-resource"

# ====================================================
# SECTION: function test_text_route
# What it does: test text route.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_text_route():  # info: def test_text_route
    found, scope = _targets("local", "Wind on Oahu", cfg())  # info: found , scope = _targets ( "local" ,
    assert found == {"honolulu"}  # info: assert found == { "honolulu" }
    assert scope == "explicit-text"  # info: assert scope == "explicit-text"

# ====================================================
# SECTION: function test_unknown_preserved
# What it does: test unknown preserved.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_unknown_preserved():  # info: def test_unknown_preserved
    found, scope = _targets("unknown", "No geography here", cfg())  # info: found , scope = _targets ( "unknown" ,
    assert found == set()  # info: assert found == set ( )
    assert scope == "unresolved/no-geographic-assignment"  # info: assert scope == "unresolved/no-geographic-assignment"


# ====================================================
# SECTION: function test_county_ugc_route
# What it does: test county ugc route.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_county_ugc_route():  # info: def test_county_ugc_route
    found, scope = _targets("local", "HIC003", cfg())  # info: found , scope = _targets ( "local" ,
    assert found == {"honolulu"}  # info: assert found == { "honolulu" }
    assert scope == "NWS-county-UGC"  # info: assert scope == "NWS-county-UGC"


# ====================================================
# SECTION: function test_zone_ugc_route
# What it does: test zone ugc route.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_zone_ugc_route():  # info: def test_zone_ugc_route
    found, scope = _targets("local", "HIZ301", cfg(), {"HIZ301": "003"})  # info: found , scope = _targets ( "local" ,
    assert found == {"honolulu"}  # info: assert found == { "honolulu" }
    assert scope == "NWS-zone-county-correlation"  # info: assert scope == "NWS-zone-county-correlation"
