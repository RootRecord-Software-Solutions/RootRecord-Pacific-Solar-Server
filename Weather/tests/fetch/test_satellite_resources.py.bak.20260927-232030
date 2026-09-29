from pathlib import Path

import yaml


CONFIG = Path(__file__).resolve().parents[2] / "config" / "resources.yaml"


EXPECTED_GOES_URLS = {
    "goes19_eep_geocolor": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/GEOCOLOR/GOES19-EEP-GEOCOLOR-900x540.gif",
    "goes19_eep_glm_extent3": "https://cdn.star.nesdis.noaa.gov/GOES19/GLM/SECTOR/eep/EXTENT3/GOES19-GLM-EEP-EXTENT3-900x540.gif",
    "goes19_eep_airmass": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/AirMass/GOES19-EEP-AirMass-900x540.gif",
    "goes19_eep_sandwich": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/Sandwich/GOES19-EEP-Sandwich-900x540.gif",
    "goes19_eep_fire_temperature": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/FireTemperature/GOES19-EEP-FireTemperature-900x540.gif",
    "goes19_eep_02": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/02/GOES19-EEP-02-900x540.gif",
    "goes19_eep_07": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/07/GOES19-EEP-07-900x540.gif",
    "goes19_eep_13": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/13/GOES19-EEP-13-900x540.gif",
    "goes19_eep_14": "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/eep/14/GOES19-EEP-14-900x540.gif",
    "goes18_hi_geocolor": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/GEOCOLOR/GOES18-HI-GEOCOLOR-600x600.gif",
    "goes18_hi_glm_extent3": "https://cdn.star.nesdis.noaa.gov/GOES18/GLM/SECTOR/hi/EXTENT3/GOES18-GLM-HI-EXTENT3-600x600.gif",
    "goes18_hi_airmass": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/AirMass/GOES18-HI-AirMass-600x600.gif",
    "goes18_hi_sandwich": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/Sandwich/GOES18-HI-Sandwich-600x600.gif",
    "goes18_hi_daynight_cloud_micro_combo": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/DayNightCloudMicroCombo/GOES18-HI-DayNightCloudMicroCombo-600x600.gif",
    "goes18_hi_fire_temperature": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/FireTemperature/GOES18-HI-FireTemperature-600x600.gif",
    "goes18_hi_07": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/07/GOES18-HI-07-600x600.gif",
    "goes18_hi_08": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/08/GOES18-HI-08-600x600.gif",
    "goes18_hi_14": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/hi/14/GOES18-HI-14-600x600.gif",
}


def _goes_items():
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["satellite"]["items"] if item["id"].startswith("goes")}


def test_all_requested_goes_products_use_stable_dynamic_gif_endpoints():
    items = _goes_items()
    assert set(items) == set(EXPECTED_GOES_URLS)
    assert {rid: items[rid]["url"] for rid in items} == EXPECTED_GOES_URLS


def test_goes_urls_are_not_timestamped_archive_filenames():
    for url in EXPECTED_GOES_URLS.values():
        filename = url.rsplit("/", 1)[-1]
        assert not filename[:10].isdigit(), url
        assert filename.endswith(".gif"), url
