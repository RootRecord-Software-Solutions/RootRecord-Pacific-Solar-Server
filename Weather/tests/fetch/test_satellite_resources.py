# ==============================================================================
# FILE: Weather/tests/fetch/test_satellite_resources.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
from pathlib import Path  # info: from pathlib import Path

import yaml  # info: import yaml


CONFIG = Path(__file__).resolve().parents[2] / "config" / "resources.yaml"  # info: set CONFIG


# ====================================================
# SECTION: EXPECTED_GOES_URLS
# What it does: Set EXPECTED_GOES_URLS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
EXPECTED_GOES_URLS = {  # info: set EXPECTED_GOES_URLS
    "goes19_eep_geocolor": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/GEOCOLOR/GOES19-EEP-GEOCOLOR-900x540.gif",  # info: "goes19_eep_geocolor" : "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/GEOCOLOR/GOES19-EEP-GEOCOLOR-9
    "goes19_eep_airmass": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/AirMass/GOES19-EEP-AirMass-900x540.gif",  # info: "goes19_eep_airmass" : "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/AirMass/GOES19-EEP-AirMass-900x
    "goes19_eep_sandwich": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/Sandwich/GOES19-EEP-Sandwich-900x540.gif",  # info: "goes19_eep_sandwich" : "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/Sandwich/GOES19-EEP-Sandwich-9
    "goes19_eep_fire_temperature": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/FireTemperature/GOES19-EEP-FireTemperature-900x540.gif",  # info: "goes19_eep_fire_temperature" : "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/FireTemperature/GOES19
    "goes19_eep_02": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/02/GOES19-EEP-02-900x540.gif",  # info: "goes19_eep_02" : "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/02/GOES19-EEP-02-900x540.gif" ,
    "goes19_eep_07": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/07/GOES19-EEP-07-900x540.gif",  # info: "goes19_eep_07" : "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/07/GOES19-EEP-07-900x540.gif" ,
    "goes19_eep_13": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/13/GOES19-EEP-13-900x540.gif",  # info: "goes19_eep_13" : "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/13/GOES19-EEP-13-900x540.gif" ,
    "goes19_eep_14": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/14/GOES19-EEP-14-900x540.gif",  # info: "goes19_eep_14" : "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/14/GOES19-EEP-14-900x540.gif" ,
    "goes18_hi_geocolor": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/GOES18-HI-GEOCOLOR-600x600.gif",  # info: "goes18_hi_geocolor" : "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/GOES18-HI-GEOCOLOR-600x
    "goes18_hi_airmass": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/AirMass/GOES18-HI-AirMass-600x600.gif",  # info: "goes18_hi_airmass" : "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/AirMass/GOES18-HI-AirMass-600x600
    "goes18_hi_sandwich": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/Sandwich/GOES18-HI-Sandwich-600x600.gif",  # info: "goes18_hi_sandwich" : "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/Sandwich/GOES18-HI-Sandwich-600x
    "goes18_hi_daynight_cloud_micro_combo": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/DayNightCloudMicroCombo/GOES18-HI-DayNightCloudMicroCombo-600x600.gif",  # info: "goes18_hi_daynight_cloud_micro_combo" : "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/DayNightCloudM
    "goes18_hi_fire_temperature": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/FireTemperature/GOES18-HI-FireTemperature-600x600.gif",  # info: "goes18_hi_fire_temperature" : "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/FireTemperature/GOES18-H
    "goes18_hi_07": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/07/GOES18-HI-07-600x600.gif",  # info: "goes18_hi_07" : "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/07/GOES18-HI-07-600x600.gif" ,
    "goes18_hi_08": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/08/GOES18-HI-08-600x600.gif",  # info: "goes18_hi_08" : "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/08/GOES18-HI-08-600x600.gif" ,
    "goes18_hi_14": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/14/GOES18-HI-14-600x600.gif",  # info: "goes18_hi_14" : "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/14/GOES18-HI-14-600x600.gif" ,
}  # info: }


# ====================================================
# SECTION: function _goes_items
# What it does:  goes items.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _goes_items():  # info: def _goes_items
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))  # info: set data
    return {item["id"]: item for item in data["satellite"]["items"] if item["id"].startswith("goes")}  # info: return { item [ "id" ] : item


# ====================================================
# SECTION: function test_all_requested_goes_products_use_stable_dynamic_gif_endpoints
# What it does: test all requested goes products use stable dynamic gif endpoints.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_all_requested_goes_products_use_stable_dynamic_gif_endpoints():  # info: def test_all_requested_goes_products_use_stable_dynamic_gif_endpoints
    items = _goes_items()  # info: set items
    assert set(items) == set(EXPECTED_GOES_URLS)  # info: assert set ( items ) == set (
    assert {rid: items[rid]["url"] for rid in items} == EXPECTED_GOES_URLS  # info: assert { rid : items [ rid ]


# ====================================================
# SECTION: function test_goes_urls_are_not_timestamped_archive_filenames
# What it does: test goes urls are not timestamped archive filenames.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_goes_urls_are_not_timestamped_archive_filenames():  # info: def test_goes_urls_are_not_timestamped_archive_filenames
    for url in EXPECTED_GOES_URLS.values():  # info: for url in EXPECTED_GOES_URLS . values ( )
        filename = url.rsplit("/", 1)[-1]  # info: set filename
        assert not filename[:10].isdigit(), url  # info: assert not filename [ : 10 ] .
        assert filename.endswith(".gif"), url  # info: assert filename . endswith ( ".gif" ) ,
