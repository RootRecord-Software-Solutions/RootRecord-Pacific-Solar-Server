# Weather reports

This folder is the generator. Generated report text is not stored here.

The weather daemon writes under the Database, which this repo ignores:

- Statewide README: `2 - RootRecord-Database/Weather/README.md`
- Level 0, county, and official reports: `2 - RootRecord-Database/Weather/Hawai'i/reports/`

`README_TEMPLATE.md` and `WEATHER_DATABASE_README_TEMPLATE.md` in this folder are source templates. The running generator fills those templates into the Database paths above.
