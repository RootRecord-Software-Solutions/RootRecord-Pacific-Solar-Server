# fetch/

**Owns:** one thin module per resource category, mirroring the categories in
`NWS_Hawaii_Resource_Map.md` so the code tree and the `Database/WEATHER/` tree
read the same way:

- `text_products.py` — api.weather.gov products API (primary path)
- `text_products_fallback.py` — forecast.weather.gov/product.php scrape,
  only called if `text_products.py` fails
- `alerts.py` — api.weather.gov/alerts/active?area=HI (Tier 0)
- `satellite.py` — HFO IR gifs + GOES-18 NESDIS sector gif
- `analyses.py` — streamline/surface/seastate charts
- `radar.py` — radar.weather.gov static loop gif
- `marine.py` — CWF, offshore, high seas, surf forecast
- `aviation.py` — TAFs, AIRMETs, SIGMETs
- `climate.py` — CLI/CLM/RRA daily+monthly summaries
- `maps.py` — wwamap PNG + marine zone JPGs
- `ndfd_gridpoint.py` — api.weather.gov/points/{lat,lon} resolver + cache

**Owns:** building the request, calling `core.http_client`, running the
result through `core.change_detection`, handing anything changed to
`core.archiver` (and, for text, through `core.text_cleaner` +
`core.validators` first).

**Does NOT own:** rate limiting, hashing, archiving mechanics, or cleaning
logic — all of that is delegated to `core/`. A fetch module should be
readable top-to-bottom in under a minute; if it's re-implementing something
`core/` already does, that's a bug.

**Depends on:** `core/`, `config/resources.yaml`.

Tropical cyclone fetching does **not** live here — see `hurricanes/`, which
is a full sub-skill because its data shapes and per-storm state are
genuinely different from a flat "fetch a URL, save it" resource.
