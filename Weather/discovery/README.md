# Hazard catalog discovery

`hazard_catalog.py` is a deterministic crawler/parser for NWS/NOAA
product catalogs. It exists so the weather project can enumerate hazard
products without manually opening hundreds of product pages.

Recommended seeds include:

- https://www.weather.gov/prh/data_products_hfo
- https://www.weather.gov/hfo/office_products
- https://forecast.weather.gov/product_types.php
- https://www.nhc.noaa.gov/
- https://www.nhc.noaa.gov/ftp/graphics/xgtwo/

The output is an inventory for review. It does not decide that a product is
"important"; it records identifiers and source pages using explicit rules.
