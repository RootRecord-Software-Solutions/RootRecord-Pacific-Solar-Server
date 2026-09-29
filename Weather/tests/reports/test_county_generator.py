from reports.county_generator import _targets

def cfg():
    return {
        "counties": [
            {"key": "honolulu", "same": "HIC003", "aliases": ["Honolulu", "Oahu"]},
            {"key": "hawaii", "same": "HIC001", "aliases": ["Hawaii", "Big Island"]},
            {"key": "maui", "same": "HIC009", "aliases": ["Maui"]},
            {"key": "kauai", "same": "HIC007", "aliases": ["Kauai"]},
            {"key": "kalawao", "same": "HIC005", "aliases": ["Kalawao"]},
        ],
        "statewide_resource_ids": ["state_report"],
        "resource_routing": {"county_patterns": {"hawaii": ["hilo"]}},
    }

def test_statewide_all():
    found, scope = _targets("state_report", "x", cfg())
    assert found == {"honolulu", "hawaii", "maui", "kauai", "kalawao"}
    assert scope == "statewide"

def test_resource_route():
    found, scope = _targets("hilo_forecast", "x", cfg())
    assert found == {"hawaii"}
    assert scope == "explicit-resource"

def test_text_route():
    found, scope = _targets("local", "Wind on Oahu", cfg())
    assert found == {"honolulu"}
    assert scope == "explicit-text"

def test_unknown_preserved():
    found, scope = _targets("unknown", "No geography here", cfg())
    assert found == set()
    assert scope == "unresolved/no-geographic-assignment"


def test_county_ugc_route():
    found, scope = _targets("local", "HIC003", cfg())
    assert found == {"honolulu"}
    assert scope == "NWS-county-UGC"


def test_zone_ugc_route():
    found, scope = _targets("local", "HIZ301", cfg(), {"HIZ301": "003"})
    assert found == {"honolulu"}
    assert scope == "NWS-zone-county-correlation"
