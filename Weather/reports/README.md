# 🌺 Hawaiʻi State Weather Database

> **RootRecord's continuously updated, source-preserving weather reporting layer for Hawaiʻi.**

## 🛰️ Live GOES-18 Hawaii GeoColor

<img src="https://raw.githubusercontent.com/rootrecordsoftwaresolutions/RootRecord-Weather-Database/main/Hawai%27i/reports/assets/GOES18-HI-GEOCOLOR-README-banner.gif" width="100%" alt="GOES-18 Hawaii GeoColor" />

## 🌐 What This Is

This directory is the human-readable reporting layer built from the locally collected Hawaiʻi weather database.

The system keeps a strict separation between:

- **Raw collected data** — the original fetched source material remains authoritative.
- **Official Sources** — readable copies preserved by issuing source, without processing-level mixing.
- **0 Level Processing** — statewide readable reports.
- **1 County Processing** — deterministic county/geographic reports.
- **Archives** — prior report versions retained when substantive source content changes.

The live report below is regenerated automatically from the current statewide report data. It is not manually maintained.

## 📚 Report Layers

- **Official Sources** — source-preserved products grouped by issuing authority.
- **0 Level Processing** — statewide Hawaiʻi reports.
- **1 County Processing** — deterministically routed county reports.
- **Archives** — previous report versions retained when source content changes.

[**Open the current statewide report →**](https://github.com/rootrecordsoftwaresolutions/RootRecord-Weather-Database/blob/main/Hawai%27i/reports/0%20Level%20Processing/Hawaii_State_Weather_Report_current.md)

## 🛡️ Source Integrity

Raw collected source data remains the authoritative record. Generated reports are separate processing/presentation layers, and products without authoritative geographic assignment are not silently assigned to counties.

---

## 🌦️ Current Conditions

| Location | Conditions | Temp | Dew point | RH | Wind | Pressure |
|---|---|---:|---:|---:|---|---:|
| Honolulu | Partly cloudy | 75°F | 67°F | 76% | Northeast 5 | 29.91F |
| Lihue | Partly cloudy | 78°F | 71°F | 79% | East 9 | 29.91F |
| Kahului | Clear | 69°F | 64°F | 84% | Southeast 6 | 29.90F |
| Hilo | Clear | 70°F | 61°F | 73% | Southwest 8 | 29.94F |
| Kona | Cloudy | 80°F | 71°F | 74% | Southeast 3 | — |

_Source: locally collected NWS-HFO Regional Weather Roundup (RWR). Values are °F._

---

## 🌦️ Live Hawaiʻi Statewide Weather Report

> **Automatically regenerated from the latest locally collected official weather products.**

| Status | Coverage | Updated | Sections |
|---|---|---|---:|
| 🟢 Active | Hawaiʻi statewide | 2026-09-29T06:37:30-10:00 HST | 29 |

The report below is generated from the same current product sections as `Hawaii_State_Weather_Report_current.md`.

---

### 1. 7-Day Zone Forecasts (all islands)

| Field | Value |
|---|---|
| **Resource ID** | zfp_zone_forecast |
| **Official source** | https://api.weather.gov/products/types/ZFP/locations/HFO |
| **Collected** | 2026-09-29T03:50:32.078020-10:00 HST |

```text
000
FPHW50 PHFO 291341
ZFPHFO

Zone Forecast Product for Hawaii
National Weather Service Honolulu HI
341 AM HST Tue Sep 29 2026

HIZ001-300715-
Niihau-
341 AM HST Tue Sep 29 2026

...HIGH SURF ADVISORY IN EFFECT UNTIL 6 PM HST THIS EVENING...

.TODAY...Windy. Cloudy with frequent showers. Highs 80 to 85.
Southeast winds 15 to 30 mph. Chance of rain 90 percent. 
.TONIGHT...Windy. Frequent showers. Lows 71 to 77. Southeast
winds 15 to 30 mph. Chance of rain near 100 percent. 
.WEDNESDAY...Breezy. Cloudy with frequent showers. Highs 79 to
85. South winds 15 to 25 mph. Chance of rain 90 percent. 
.WEDNESDAY NIGHT...Breezy. Mostly cloudy with frequent showers.
Lows 71 to 78. Southeast winds 20 to 25 mph. Chance of rain
80 percent. 
.THURSDAY...Mostly cloudy. Breezy. Numerous showers in the
morning, then scattered showers in the afternoon. Highs 80 to 85.
Southeast winds 15 to 25 mph. Chance of rain 70 percent. 
.THURSDAY NIGHT...Mostly cloudy. Breezy. Scattered showers in the
evening, then numerous showers after midnight. Lows 71 to 78.
Southeast winds 15 to 20 mph. Chance of rain 60 percent. 
.FRIDAY...Partly sunny in the morning then becoming mostly sunny.
Breezy. Scattered showers. Highs 80 to 85. Southeast winds 15 to
20 mph. Chance of rain 40 percent. 
.FRIDAY NIGHT...Partly cloudy. Breezy. Isolated showers in the
evening, then scattered showers after midnight. Lows 71 to 78.
Southeast winds 10 to 20 mph. Chance of rain 30 percent. 
.SATURDAY...Mostly sunny. Isolated showers in the morning. Highs
79 to 85. East winds around 10 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy with isolated showers. Lows 71 to
77. Northeast winds around 10 mph. Chance of rain 20 percent. 
.SUNDAY...Mostly sunny. Breezy. Isolated showers in the morning.
Highs 79 to 85. Northeast winds 10 to 20 mph. Chance of rain
20 percent. 
.SUNDAY NIGHT...Breezy. Partly cloudy with isolated showers. Lows
71 to 77. Northeast winds 10 to 20 mph. Chance of rain
20 percent. 
.MONDAY...Breezy. Mostly sunny with isolated showers. Highs 79 to
85. Northeast winds 10 to 20 mph. Chance of rain 20 percent. 

HIZ029-300715-
Kauai North-
Including Princeville, Hanalei, Na Pali State Park
341 AM HST Tue Sep 29 2026

.TODAY...Mostly cloudy. Breezy. Scattered showers in the morning,
then numerous showers in the afternoon. Highs 71 to 87. East
winds up to 15 mph shifting to the southeast in the afternoon.
Chance of rain 70 percent. 
.TONIGHT...Mostly cloudy. Breezy. Numerous showers in the
evening, then frequent showers after midnight. Lows 67 to 76.
Southeast winds 10 to 25 mph with gusts to 45 mph. Chance of rain
80 percent. 
.WEDNESDAY...Partly sunny. Breezy. Numerous showers in the
morning, then scattered showers in the afternoon. Highs 72 to 87.
Southeast winds up to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with scattered showers. Lows
67 to 76. Southeast winds 10 to 15 mph. Chance of rain
50 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 72 to 87.
Southeast winds around 10 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Partly cloudy with isolated showers. Lows 67 to
76. Southeast winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs 72 to 87.
Southeast winds up to 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 66 to
75. Light winds becoming southeast up to 10 mph after midnight.
Chance of rain 50 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 72 to 87.
East winds around 10 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
66 to 75. East winds around 10 mph. Chance of rain 40 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 71 to 87.
Northeast winds around 10 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 65 to
75. Northeast winds around 10 mph. Chance of rain 40 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 70 to 86.
Northeast winds 10 to 15 mph. Chance of rain 50 percent. 

HIZ030-300715-
Kauai East-
Including Lihue, Kapaa, Anahola
341 AM HST Tue Sep 29 2026

.TODAY...Cloudy and breezy. Scattered showers in the morning,
then frequent showers in the afternoon. Highs 77 to 86. Southeast
winds 10 to 15 mph increasing to 15 to 25 mph in the afternoon.
Chance of rain 90 percent. 
.TONIGHT...Breezy. Frequent showers. Lows 68 to 77. Southeast
winds 15 to 25 mph. Chance of rain near 100 percent. 
.WEDNESDAY...Breezy. Mostly cloudy with frequent showers. Highs
77 to 86. South winds 10 to 20 mph. Chance of rain 90 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with frequent showers. Lows
68 to 77. South winds 10 to 15 mph. Chance of rain 90 percent. 
.THURSDAY...Mostly cloudy with numerous showers. Highs 77 to 86.
Southeast winds around 10 mph. Chance of rain 70 percent. 
.THURSDAY NIGHT...Mostly cloudy. Scattered showers in the
evening, then numerous showers after midnight. Lows 68 to 77.
Southeast winds around 10 mph. Chance of rain 70 percent. 
.FRIDAY...Partly sunny in the morning then becoming mostly sunny.
Scattered showers. Highs 78 to 86. Southeast winds around 10 mph.
Chance of rain 50 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 67 to
77. Light winds becoming east around 10 mph after midnight.
Chance of rain 50 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 78 to 87.
East winds around 10 mph. Chance of rain 50 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
66 to 77. Northeast winds around 10 mph. Chance of rain
50 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 78 to 86.
Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 66 to
76. Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 77 to 85.
Northeast winds around 10 mph. Chance of rain 50 percent. 

HIZ031-300715-
Kauai South-
Including Poipu, Kalaheo, Koloa
341 AM HST Tue Sep 29 2026

...HIGH SURF ADVISORY IN EFFECT UNTIL 6 PM HST THIS EVENING...

.TODAY...Mostly cloudy. Breezy. Scattered showers in the morning,
then frequent showers in the afternoon. Highs 80 to 88. Southeast
winds 10 to 20 mph. Chance of rain 80 percent. 
.TONIGHT...Breezy. Frequent showers. Lows 72 to 77. Southeast
winds 15 to 20 mph. Chance of rain near 100 percent. 
.WEDNESDAY...Breezy. Cloudy with frequent showers. Highs 79 to
87. South winds 10 to 20 mph. Chance of rain 90 percent. 
.WEDNESDAY NIGHT...Cloudy with frequent showers. Lows 72 to 77.
Southeast winds 10 to 15 mph. Chance of rain 90 percent. 
.THURSDAY...Mostly cloudy. Frequent showers in the morning, then
numerous showers in the afternoon. Highs 79 to 88. Southeast
winds around 10 mph. Chance of rain 80 percent. 
.THURSDAY NIGHT...Mostly cloudy with numerous showers. Lows 72 to
77. Southeast winds around 10 mph. Chance of rain 70 percent. 
.FRIDAY...Partly sunny with scattered showers. Highs 79 to 89.
Southeast winds around 10 mph. Chance of rain 50 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 71 to
77. Light winds becoming east around 10 mph after midnight.
Chance of rain 50 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 79 to 89.
East winds around 10 mph. Chance of rain 50 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
70 to 77. Northeast winds 10 to 15 mph. Chance of rain
50 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 79 to 89.
Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 70 to
76. Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 78 to 88.
Northeast winds around 10 mph. Chance of rain 50 percent. 

HIZ003-300715-
Kauai Southwest-
Including Waimea, Waimea Canyon State Park, Hanapepe, Kekaha, 
Barking Sands
341 AM HST Tue Sep 29 2026

...HIGH SURF ADVISORY IN EFFECT UNTIL 6 PM HST THIS EVENING...

.TODAY...Mostly cloudy. Windy. Numerous showers in the morning,
then frequent showers in the afternoon. Highs around 87 near the
shore to around 77 above 3000 feet. East winds 10 to 25 mph
shifting to the southeast 20 to 30 mph in the afternoon. Chance
of rain 90 percent. 
.TONIGHT...Windy. Frequent showers. Lows around 75 near the shore
to around 66 above 3000 feet. Southeast winds 15 to 30 mph with
gusts to 50 mph. Chance of rain near 100 percent. 
.WEDNESDAY...Mostly cloudy. Breezy. Frequent showers in the
morning, then numerous showers in the afternoon. Highs around
86 near the shore to around 77 above 3000 feet. Southeast winds
10 to 20 mph. Chance of rain 90 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with numerous showers. Lows
65 to 77. Southeast winds 10 to 15 mph. Chance of rain
70 percent. 
.THURSDAY...Mostly cloudy with numerous showers. Highs 76 to 89.
Southeast winds 10 to 15 mph. Chance of rain 70 percent. 
.THURSDAY NIGHT...Mostly cloudy. Scattered showers in the
evening, then numerous showers after midnight. Lows 65 to 77.
Southeast winds around 10 mph. Chance of rain 70 percent. 
.FRIDAY...Partly sunny in the morning then becoming mostly sunny.
Scattered showers. Highs 76 to 89. Southeast winds around 10 mph.
Chance of rain 50 percent. 
.FRIDAY NIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Scattered showers. Lows 64 to 76. Southeast winds around
10 mph. Chance of rain 50 percent. 
.SATURDAY...Mostly sunny with scattered showers. Highs 76 to 90.
East winds around 10 mph in the morning becoming light. Chance of
rain 50 percent. 
.SATURDAY NIGHT...Partly cloudy with isolated showers. Lows 64 to
76. Light winds becoming northeast up to 10 mph after midnight.
Chance of rain 20 percent. 
.SUNDAY...Mostly sunny. Isolated showers in the morning, then
scattered showers in the afternoon. Highs 76 to 90. Northeast
winds up to 10 mph. Chance of rain 50 percent. 
.SUNDAY NIGHT...Partly cloudy with isolated showers. Lows 63 to
76. Northeast winds up to 10 mph. Chance of rain 20 percent. 
.MONDAY...Mostly sunny with isolated showers in the morning, then
partly sunny with scattered showers in the afternoon. Highs 75 to
89. Northeast winds up to 10 mph. Chance of rain 40 percent. 

HIZ004-300715-
Kauai Mountains-
Including Kokee State Park
341 AM HST Tue Sep 29 2026

.TODAY...Cloudy and windy. Numerous showers in the morning, then
frequent showers in the afternoon. Highs 74 to 82 in the valleys
to around 68 above 4000 feet. Southeast winds 10 to 20 mph
increasing to 15 to 30 mph in the afternoon. Chance of rain
90 percent. 
.TONIGHT...Windy. Frequent showers. Lows around 71 in the valleys
to around 63 above 4000 feet. South winds 10 to 30 mph with gusts
to 50 mph. Chance of rain near 100 percent. 
.WEDNESDAY...Mostly cloudy. Breezy. Frequent showers in the
morning, then scattered showers in the afternoon. Highs 75 to
83 in the valleys to around 68 above 4000 feet. Southeast winds
10 to 20 mph. Chance of rain 90 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with scattered showers. Lows
62 to 73. South winds 10 to 15 mph. Chance of rain 50 percent. 
.THURSDAY...Mostly cloudy with scattered showers. Highs 66 to 83.
Southeast winds 10 to 15 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Mostly cloudy with scattered showers. Lows
61 to 73. Southeast winds around 10 mph. Chance of rain
50 percent. 
.FRIDAY...Partly sunny with scattered showers. Highs 67 to 83.
Southeast winds up to 10 mph. Chance of rain 50 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 61 to
72. Light winds becoming southeast up to 10 mph after midnight.
Chance of rain 50 percent. 
.SATURDAY...Mostly cloudy with scattered showers. Highs 67 to 83.
East winds around 10 mph. Chance of rain 50 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
60 to 72. Northeast winds around 10 mph. Chance of rain
50 percent. 
.SUNDAY...Mostly cloudy with scattered showers. Highs 67 to 83.
Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 60 to
71. Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.MONDAY...Mostly cloudy with scattered showers. Highs 65 to 82.
Northeast winds around 10 mph. Chance of rain 50 percent. 

HIZ032-300715-
East Honolulu-
Including Hawaii Kai, Aina Haina, Kahala
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 83 to 89. Southeast winds 10 to
15 mph. 
.TONIGHT...Mostly cloudy. Breezy. Scattered showers in the
evening, then numerous showers after midnight. Lows around 78.
Southeast winds 10 to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY...Mostly cloudy. Breezy. Scattered showers in the
morning, then numerous showers in the afternoon. Highs 82 to 88.
South winds 15 to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with numerous showers. Lows
around 77. Southeast winds 10 to 15 mph. Chance of rain
70 percent. 
.THURSDAY...Partly sunny. Numerous showers in the morning, then
scattered showers in the afternoon. Highs 81 to 88. Southeast
winds around 10 mph. Chance of rain 70 percent. 
.THURSDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Scattered showers. Lows around 77. East winds
around 10 mph. Chance of rain 30 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs 81 to 88.
Southeast winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Partly cloudy in the evening then becoming mostly
cloudy. Scattered showers. Lows around 77. East winds 10 to
15 mph. Chance of rain 30 percent. 
.SATURDAY...Mostly sunny with scattered showers. Highs 81 to 87.
Northeast winds 10 to 15 mph. Chance of rain 30 percent. 
.SATURDAY NIGHT...Partly cloudy with scattered showers. Lows
around 77. Northeast winds around 15 mph. Chance of rain
30 percent. 
.SUNDAY...Mostly sunny with scattered showers. Highs 81 to 87.
Northeast winds around 15 mph. Chance of rain 30 percent. 
.SUNDAY NIGHT...Partly cloudy. Isolated showers in the evening,
then scattered showers after midnight. Lows around 76. Northeast
winds 10 to 15 mph. Chance of rain 30 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 80 to 87.
Northeast winds around 10 mph. Chance of rain 40 percent. 

HIZ033-300715-
Honolulu Metro-
Including Honolulu, Waikiki
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 85 to 90. Southeast winds 10 to
15 mph. 
.TONIGHT...Mostly cloudy. Breezy. Scattered showers in the
evening, then numerous showers after midnight. Lows around 77.
Southeast winds 15 to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY...Breezy. Mostly cloudy with numerous showers. Highs
83 to 88. Southeast winds 10 to 20 mph. Chance of rain
70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with numerous showers. Lows
around 76. Southeast winds 10 to 15 mph. Chance of rain
70 percent. 
.THURSDAY...Mostly cloudy. Numerous showers in the morning, then
scattered showers in the afternoon. Highs around 86. Southeast
winds around 10 mph. Chance of rain 70 percent. 
.THURSDAY NIGHT...Partly cloudy. Scattered showers in the
evening, then isolated showers after midnight. Lows around 76.
East winds around 10 mph in the evening becoming light. Chance of
rain 30 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs around 86.
Southeast winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Partly cloudy with isolated showers. Lows around
76. East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs around 86.
East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy with isolated showers. Lows
around 76. Northeast winds 10 to 15 mph. Chance of rain
20 percent. 
.SUNDAY...Mostly sunny with isolated showers. Highs 83 to 88.
Northeast winds 10 to 15 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Partly cloudy with isolated showers. Lows around
76. Northeast winds 10 to 15 mph. Chance of rain 20 percent. 
.MONDAY...Mostly sunny with scattered showers. Highs 83 to 88.
Light winds becoming north up to 10 mph in the afternoon. Chance
of rain 30 percent. 

HIZ034-300715-
Ewa Plain-
Including Kapolei
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Isolated showers in the afternoon. Highs
around 88. Southeast winds 10 to 15 mph. Chance of rain
20 percent. 
.TONIGHT...Mostly cloudy. Breezy. Scattered showers in the
evening, then numerous showers after midnight. Lows around 76.
Southeast winds 15 to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY...Mostly cloudy. Breezy. Scattered showers in the
morning, then numerous showers in the afternoon. Highs 83 to 88.
Southeast winds 10 to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with numerous showers. Lows
around 76. Southeast winds 10 to 15 mph. Chance of rain
70 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 84 to 89.
Southeast winds 10 to 15 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Partly cloudy with isolated showers. Lows
around 76. East winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY...Mostly sunny. Isolated showers in the morning. Highs
84 to 89. Southeast winds around 10 mph. Chance of rain
20 percent. 
.FRIDAY NIGHT...Partly cloudy with isolated showers. Lows around
75. East winds around 10 mph. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny. Isolated showers in the morning. Highs
84 to 89. East winds around 10 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy. Isolated showers after midnight.
Lows around 75. Northeast winds around 10 mph. Chance of rain
20 percent. 
.SUNDAY...Mostly sunny. Isolated showers in the morning. Highs
84 to 89. Northeast winds around 10 mph. Chance of rain
20 percent. 
.SUNDAY NIGHT...Partly cloudy. Isolated showers after midnight.
Lows around 75. Northeast winds around 10 mph in the evening
becoming light. Chance of rain 20 percent. 
.MONDAY...Mostly sunny with isolated showers. Highs 83 to 88.
Light winds. Chance of rain 20 percent. 

HIZ006-300715-
Waianae Coast-
Including Nanakuli, Waianae, Makaha
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Breezy. Isolated showers in the afternoon.
Highs 86 to 93. Southeast winds 10 to 20 mph. Chance of rain
20 percent. 
.TONIGHT...Breezy. Mostly cloudy with scattered showers. Lows
71 to 79. Southeast winds 15 to 25 mph. Chance of rain
50 percent. 
.WEDNESDAY...Mostly cloudy. Breezy. Scattered showers in the
morning, then numerous showers in the afternoon. Highs 84 to 91.
Southeast winds 15 to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with numerous showers. Lows
72 to 78. Southeast winds 10 to 15 mph. Chance of rain
70 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 84 to 91.
Southeast winds 10 to 15 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Partly cloudy. Scattered showers in the
evening, then isolated showers after midnight. Lows 71 to 78.
Southeast winds around 10 mph. Chance of rain 30 percent. 
.FRIDAY...Mostly sunny. Isolated showers in the afternoon. Highs
84 to 91. Southeast winds around 10 mph. Chance of rain
20 percent. 
.FRIDAY NIGHT...Partly cloudy with isolated showers. Lows 70 to
77. Light winds becoming northeast around 10 mph after midnight.
Chance of rain 20 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs 84 to 91.
Northeast winds up to 10 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy with isolated showers. Lows 70 to
77. East winds 10 to 15 mph. Chance of rain 20 percent. 
.SUNDAY...Mostly sunny with isolated showers. Highs 84 to 91.
Northeast winds 10 to 15 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Partly cloudy with isolated showers. Lows 70 to
77. Northeast winds 10 to 15 mph. Chance of rain 20 percent. 
.MONDAY...Mostly sunny with isolated showers. Highs 83 to 91.
Northeast winds 10 to 15 mph. Chance of rain 20 percent. 

HIZ007-300715-
Oahu North Shore-
Including Waialua, Haleiwa, Pupukea
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 83 to 90. Southeast
winds 10 to 15 mph. Chance of rain 20 percent. 
.TONIGHT...Breezy. Mostly cloudy with scattered showers. Lows
71 to 77. Southeast winds 10 to 20 mph. Chance of rain
50 percent. 
.WEDNESDAY...Mostly cloudy. Breezy. Scattered showers in the
morning, then numerous showers in the afternoon. Highs 81 to 88.
Southeast winds 10 to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with scattered showers. Lows
71 to 77. Southeast winds 10 to 15 mph. Chance of rain
50 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 81 to 88.
Southeast winds around 10 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Partly cloudy with isolated showers. Lows 70 to
77. Southeast winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs 81 to 88.
Southeast winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Partly cloudy with scattered showers. Lows 70 to
77. East winds around 10 mph. Chance of rain 40 percent. 
.SATURDAY...Mostly sunny with scattered showers. Highs 81 to 87.
East winds around 10 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Partly cloudy with scattered showers. Lows
70 to 76. East winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY...Mostly sunny with scattered showers. Highs 80 to 87.
Northeast winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Partly cloudy. Isolated showers in the evening,
then scattered showers after midnight. Lows 70 to 76. Northeast
winds 10 to 15 mph. Chance of rain 40 percent. 
.MONDAY...Partly sunny in the morning then becoming mostly sunny.
Scattered showers. Highs 79 to 86. Northeast winds around 10 mph.
Chance of rain 50 percent. 

HIZ035-300715-
Koolau Windward-
Including Kahuku, Laie, Punaluu, Kahaluu, Ahuimanu
341 AM HST Tue Sep 29 2026

.TODAY...Partly sunny with isolated showers. Highs 77 to 88.
Southeast winds 10 to 15 mph. Chance of rain 20 percent. 
.TONIGHT...Breezy. Mostly cloudy with scattered showers. Lows
69 to 79. Southeast winds 10 to 20 mph. Chance of rain
50 percent. 
.WEDNESDAY...Breezy. Mostly cloudy with numerous showers. Highs
76 to 86. Southeast winds 10 to 20 mph. Chance of rain
70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with numerous showers. Lows
69 to 79. Southeast winds 10 to 15 mph. Chance of rain
70 percent. 
.THURSDAY...Mostly cloudy. Numerous showers in the morning, then
scattered showers in the afternoon. Highs 76 to 86. Southeast
winds 10 to 15 mph. Chance of rain 70 percent. 
.THURSDAY NIGHT...Mostly cloudy with scattered showers in the
evening, then partly cloudy with isolated showers after midnight.
Lows 69 to 78. East winds 10 to 15 mph. Chance of rain
40 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs 76 to 86.
Southeast winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 68 to
78. East winds 10 to 15 mph. Chance of rain 50 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 75 to 86.
East winds 10 to 15 mph. Chance of rain 50 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
68 to 78. East winds 10 to 15 mph. Chance of rain 50 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 75 to 85.
Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 68 to
78. Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 74 to 85.
Light winds becoming northeast around 10 mph in the afternoon.
Chance of rain 50 percent. 

HIZ036-300715-
Koolau Leeward-
Including Nuuanu, Manoa, Palolo
341 AM HST Tue Sep 29 2026

.TODAY...Partly sunny with isolated showers. Highs 76 to 88. East
winds around 10 mph shifting to the southeast in the afternoon.
Chance of rain 20 percent. 
.TONIGHT...Breezy. Mostly cloudy with numerous showers. Lows
68 to 77. Southeast winds 10 to 25 mph. Chance of rain
70 percent. 
.WEDNESDAY...Mostly cloudy. Breezy. Numerous showers in the
morning, then frequent showers in the afternoon. Highs 74 to 86.
South winds 10 to 25 mph. Chance of rain 80 percent. 
.WEDNESDAY NIGHT...Mostly cloudy. Frequent showers in the
evening, then numerous showers after midnight. Lows 68 to 76.
Southeast winds 10 to 15 mph. Chance of rain 80 percent. 
.THURSDAY...Mostly cloudy with numerous showers. Highs 73 to 86.
Southeast winds 10 to 15 mph. Chance of rain 70 percent. 
.THURSDAY NIGHT...Partly cloudy. Scattered showers in the
evening, then isolated showers after midnight. Lows 67 to 76.
East winds around 10 mph. Chance of rain 30 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs 73 to 86.
Southeast winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 66 to
76. East winds 10 to 15 mph. Chance of rain 50 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 73 to 86.
East winds 10 to 15 mph. Chance of rain 50 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
67 to 76. Northeast winds 10 to 15 mph. Chance of rain
50 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 73 to 86.
Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.SUNDAY NIGHT...Partly cloudy in the evening then becoming mostly
cloudy. Scattered showers. Lows 67 to 75. Northeast winds 10 to
15 mph. Chance of rain 50 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 72 to 85.
Northeast winds up to 10 mph. Chance of rain 50 percent. 

HIZ009-300715-
Olomana-
Including Kailua, Kaneohe, Waimanalo
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Isolated showers in the morning. Highs
80 to 87. Southeast winds 10 to 15 mph. Chance of rain
20 percent. 
.TONIGHT...Breezy. Mostly cloudy with scattered showers. Lows
72 to 78. Southeast winds 10 to 20 mph. Chance of rain
50 percent. 
.WEDNESDAY...Mostly cloudy. Breezy. Scattered showers in the
morning, then numerous showers in the afternoon. Highs 79 to 85.
South winds 10 to 20 mph. Chance of rain 70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with numerous showers. Lows
72 to 78. South winds 10 to 15 mph. Chance of rain 70 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 78 to 85.
Southeast winds around 10 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Scattered showers. Lows 72 to 78. East winds
around 10 mph. Chance of rain 40 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs 78 to 85.
Southeast winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 72 to
78. East winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY...Partly sunny in the morning then becoming mostly
sunny. Scattered showers. Highs 78 to 85. Northeast winds 10 to
15 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
72 to 77. Northeast winds 10 to 15 mph. Chance of rain
40 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 78 to 84.
Northeast winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Partly cloudy in the evening then becoming mostly
cloudy. Scattered showers. Lows 71 to 77. Northeast winds 10 to
15 mph. Chance of rain 40 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 77 to 84.
Northeast winds around 10 mph. Chance of rain 50 percent. 

HIZ010-300715-
Central Oahu-
Including Mililani, Wahiawa, Pearl City
341 AM HST Tue Sep 29 2026

.TODAY...Partly sunny. Breezy. Isolated showers in the afternoon.
Highs 82 to 89. Southeast winds 10 to 20 mph. Chance of rain
20 percent. 
.TONIGHT...Breezy. Mostly cloudy with numerous showers. Lows
around 73. Southeast winds 15 to 25 mph. Chance of rain
70 percent. 
.WEDNESDAY...Breezy. Mostly cloudy with numerous showers. Highs
79 to 86. Southeast winds 10 to 20 mph. Chance of rain
70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy. Numerous showers in the
evening, then scattered showers after midnight. Lows 70 to 75.
Southeast winds 10 to 15 mph. Chance of rain 70 percent. 
.THURSDAY...Mostly cloudy with scattered showers. Highs 80 to 86.
Southeast winds around 10 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Partly cloudy. Isolated showers in the evening.
Lows around 72. East winds around 10 mph. Chance of rain
20 percent. 
.FRIDAY...Mostly sunny. Isolated showers in the afternoon. Highs
80 to 86. Southeast winds around 10 mph in the morning becoming
light. Chance of rain 20 percent. 
.FRIDAY NIGHT...Partly cloudy. Scattered showers in the evening,
then isolated showers after midnight. Lows 69 to 74. Light winds
becoming east around 10 mph after midnight. Chance of rain
40 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs 79 to 86.
East winds around 10 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy. Isolated showers in the evening,
then scattered showers after midnight. Lows around 71. Northeast
winds around 10 mph. Chance of rain 40 percent. 
.SUNDAY...Mostly sunny. Scattered showers in the morning, then
isolated showers in the afternoon. Highs 79 to 86. Northeast
winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Partly cloudy with isolated showers. Lows around
71. Northeast winds around 10 mph. Chance of rain 20 percent. 
.MONDAY...Mostly sunny in the morning then becoming partly sunny.
Scattered showers. Highs 78 to 85. Light winds becoming northeast
up to 10 mph in the afternoon. Chance of rain 40 percent. 

HIZ011-300715-
Waianae Mountains-
Including Makakilo
341 AM HST Tue Sep 29 2026

.TODAY...Breezy. Partly sunny in the morning, then mostly sunny
with isolated showers in the afternoon. Highs 78 to 93. Southeast
winds 10 to 20 mph. Chance of rain 20 percent. 
.TONIGHT...Mostly cloudy. Breezy. Scattered showers in the
evening, then numerous showers after midnight. Lows 66 to 76.
Southeast winds 15 to 25 mph. Chance of rain 70 percent. 
.WEDNESDAY...Breezy. Mostly cloudy with numerous showers. Highs
76 to 91. Southeast winds 20 to 25 mph shifting to the south
10 to 25 mph in the afternoon. Chance of rain 70 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with numerous showers. Lows
66 to 75. Southeast winds 10 to 15 mph. Chance of rain
70 percent. 
.THURSDAY...Mostly cloudy with numerous showers. Highs 76 to 91.
Southeast winds 10 to 15 mph. Chance of rain 70 percent. 
.THURSDAY NIGHT...Mostly cloudy with scattered showers in the
evening, then partly cloudy with isolated showers after midnight.
Lows 66 to 75. Southeast winds around 10 mph. Chance of rain
40 percent. 
.FRIDAY...Mostly sunny. Isolated showers in the afternoon. Highs
76 to 91. Southeast winds around 10 mph in the morning becoming
light. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 65 to
75. Light winds becoming east around 10 mph after midnight.
Chance of rain 40 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 76 to 91.
Northeast winds around 10 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
65 to 74. East winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 76 to 91.
Northeast winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Partly cloudy. Isolated showers in the evening,
then scattered showers after midnight. Lows 65 to 74. Northeast
winds 10 to 15 mph. Chance of rain 40 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 76 to 90.
Northeast winds around 10 mph. Chance of rain 40 percent. 

HIZ037-300715-
Molokai Windward-
Including Kalaupapa, Halawa Valley
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Isolated showers in the morning. Highs
69 to 86. Southeast winds up to 15 mph shifting to the east in
the afternoon. Chance of rain 20 percent. 
.TONIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Isolated showers. Lows 62 to 77. Southeast winds 10 to
15 mph. Chance of rain 20 percent. 
.WEDNESDAY...Mostly sunny in the morning then becoming partly
sunny. Scattered showers. Highs 69 to 85. Southeast winds 10 to
15 mph. Chance of rain 50 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with scattered showers. Lows
62 to 77. Southeast winds 10 to 15 mph. Chance of rain
40 percent. 
.THURSDAY...Mostly sunny with scattered showers. Highs 68 to 85.
East winds up to 15 mph. Chance of rain 30 percent. 
.THURSDAY NIGHT...Partly cloudy with isolated showers. Lows 61 to
77. East winds 10 to 15 mph. Chance of rain 20 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs 68 to 84.
East winds up to 15 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 61 to
76. East winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 67 to 83.
East winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
60 to 76. East winds around 15 mph. Chance of rain 40 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 67 to 83.
Northeast winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 60 to
76. Northeast winds 10 to 15 mph. Chance of rain 50 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 67 to 83.
Northeast winds around 10 mph. Chance of rain 50 percent. 

HIZ038-300715-
Molokai Southeast-
Including Pukoo
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Isolated showers in the morning. Highs
68 to 86. East winds 10 to 15 mph. Chance of rain 20 percent. 
.TONIGHT...Partly cloudy with isolated showers. Lows 62 to 78.
East winds 10 to 15 mph. Chance of rain 20 percent. 
.WEDNESDAY...Mostly sunny with isolated showers in the morning,
then partly sunny with scattered showers in the afternoon. Highs
68 to 86. Southeast winds 10 to 15 mph. Chance of rain
40 percent. 
.WEDNESDAY NIGHT...Partly cloudy with scattered showers. Lows
62 to 77. Southeast winds 10 to 15 mph. Chance of rain
30 percent. 
.THURSDAY...Mostly sunny with scattered showers. Highs 67 to 85.
East winds 10 to 15 mph. Chance of rain 30 percent. 
.THURSDAY NIGHT...Partly cloudy with isolated showers. Lows 61 to
77. East winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY...Mostly sunny with isolated showers. Highs 67 to 84.
East winds up to 15 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 60 to
77. East winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 66 to 84.
East winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
60 to 77. East winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 66 to 84.
Northeast winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Partly cloudy in the evening then becoming mostly
cloudy. Scattered showers. Lows 60 to 76. Northeast winds 10 to
15 mph. Chance of rain 40 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 66 to 83.
Northeast winds around 10 mph. Chance of rain 40 percent. 

HIZ039-300715-
Molokai North-
Including Hoolehua
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 76 to 88. Southeast winds 10 to
15 mph. 
.TONIGHT...Partly cloudy with isolated showers. Lows 67 to 78.
Southeast winds 10 to 15 mph. Chance of rain 20 percent. 
.WEDNESDAY...Partly sunny with scattered showers. Highs 76 to 87.
Southeast winds 10 to 15 mph. Chance of rain 50 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with scattered showers. Lows
67 to 78. Southeast winds around 10 mph. Chance of rain
40 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 74 to 86.
East winds around 10 mph. Chance of rain 30 percent. 
.THURSDAY NIGHT...Partly cloudy with isolated showers. Lows 67 to
78. East winds 10 to 15 mph. Chance of rain 20 percent. 
.FRIDAY...Mostly sunny. Isolated showers in the morning. Highs
74 to 85. East winds 10 to 15 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Partly cloudy with isolated showers. Lows 67 to
77. East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs 73 to 85.
East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy with isolated showers. Lows 66 to
77. East winds around 15 mph. Chance of rain 20 percent. 
.SUNDAY...Mostly sunny with isolated showers. Highs 72 to 84.
Northeast winds around 15 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Partly cloudy with isolated showers. Lows 66 to
77. Northeast winds 10 to 15 mph. Chance of rain 20 percent. 
.MONDAY...Mostly sunny with isolated showers. Highs 72 to 84.
Northeast winds 10 to 15 mph. Chance of rain 20 percent. 

HIZ040-300715-
Molokai West-
Including Kepuhi
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 84 to 89. Light winds becoming
southeast up to 10 mph in the afternoon. 
.TONIGHT...Partly cloudy with isolated showers in the evening,
then mostly cloudy with scattered showers after midnight. Lows
around 77. Southeast winds 10 to 15 mph. Chance of rain
40 percent. 
.WEDNESDAY...Partly sunny with scattered showers. Highs 82 to 88.
Southeast winds 10 to 15 mph. Chance of rain 50 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with scattered showers. Lows
around 77. Southeast winds 10 to 15 mph. Chance of rain
40 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 82 to 88.
Southeast winds around 10 mph. Chance of rain 30 percent. 
.THURSDAY NIGHT...Partly cloudy with isolated showers. Lows
around 76. East winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY...Mostly sunny. Isolated showers in the morning. Highs
81 to 87. Southeast winds up to 10 mph. Chance of rain
20 percent. 
.FRIDAY NIGHT...Partly cloudy with isolated showers. Lows around
76. East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs 81 to 87.
Northeast winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Mostly clear with isolated showers. Lows around
76. East winds around 15 mph. Chance of rain 20 percent. 
.SUNDAY...Sunny with isolated showers. Highs 80 to 86. Northeast
winds around 15 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly clear. Lows around 76. Northeast winds
10 to 15 mph. 
.MONDAY...Mostly sunny with isolated showers. Highs 80 to 86.
Northeast winds 10 to 15 mph. Chance of rain 20 percent. 

HIZ041-300715-
Molokai Leeward South-
Including Kaunakakai, Maunaloa
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 72 to 92. Light winds becoming south
around 10 mph in the afternoon. 
.TONIGHT...Partly cloudy with isolated showers. Lows 64 to 78.
Southeast winds around 10 mph. Chance of rain 20 percent. 
.WEDNESDAY...Partly sunny with scattered showers. Highs 72 to 91.
Southeast winds 10 to 15 mph. Chance of rain 50 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with scattered showers. Lows
64 to 78. Southeast winds 10 to 15 mph. Chance of rain
40 percent. 
.THURSDAY...Mostly sunny in the morning then becoming partly
sunny. Scattered showers. Highs 71 to 91. East winds around
10 mph. Chance of rain 40 percent. 
.THURSDAY NIGHT...Partly cloudy with isolated showers. Lows 63 to
77. East winds around 10 mph. Chance of rain 20 percent. 
.FRIDAY...Mostly sunny. Highs 71 to 90. East winds up to 15 mph. 
.FRIDAY NIGHT...Partly cloudy with isolated showers. Lows 63 to
77. East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs 70 to 90.
East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy with isolated showers. Lows 63 to
77. East winds 10 to 15 mph. Chance of rain 20 percent. 
.SUNDAY...Sunny with isolated showers. Highs 70 to 89. Northeast
winds 10 to 15 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly clear. Isolated showers after midnight.
Lows 62 to 77. Northeast winds 10 to 15 mph. Chance of rain
20 percent. 
.MONDAY...Mostly sunny with isolated showers. Highs 69 to 89.
Northeast winds around 10 mph. Chance of rain 20 percent. 

HIZ042-300715-
Lanai Windward-
Including Shipwreck Beach
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 78 to 87. Northeast winds up to
10 mph. 
.TONIGHT...Partly cloudy. Isolated showers in the evening, then
scattered showers after midnight. Lows 67 to 78. Southeast winds
10 to 15 mph. Chance of rain 30 percent. 
.WEDNESDAY...Mostly sunny with isolated showers. Highs 77 to 85.
South winds 10 to 15 mph. Chance of rain 20 percent. 
.WEDNESDAY NIGHT...Partly cloudy in the evening then becoming
mostly cloudy. Scattered showers. Lows 67 to 78. Southeast winds
around 10 mph. Chance of rain 40 percent. 
.THURSDAY...Partly sunny in the morning then becoming mostly
sunny. Scattered showers. Highs 77 to 85. East winds up to
10 mph. Chance of rain 30 percent. 
.THURSDAY NIGHT...Mostly clear. Lows 67 to 77. Light winds. 
.FRIDAY...Sunny. Highs 76 to 85. Light winds becoming east up to
10 mph in the afternoon. 
.FRIDAY NIGHT...Partly cloudy. Lows 66 to 77. Northeast winds up
to 10 mph. 
.SATURDAY...Mostly sunny. Highs 76 to 84. Northeast winds up to
10 mph. 
.SATURDAY NIGHT...Mostly clear. Lows 66 to 77. Northeast winds
around 10 mph. 
.SUNDAY...Sunny. Highs 76 to 84. Northeast winds around 10 mph. 
.SUNDAY NIGHT...Mostly clear. Lows 66 to 77. Northeast winds
around 10 mph. 
.MONDAY...Sunny. Highs 76 to 84. Light winds. 

HIZ043-300715-
Lanai Leeward-
Including Kaumalapau Harbor
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 82 to 88. Light winds becoming
southwest 10 to 15 mph in the afternoon. 
.TONIGHT...Partly cloudy with isolated showers in the evening,
then mostly cloudy with scattered showers after midnight. Lows
73 to 78. Southeast winds 10 to 15 mph. Chance of rain
30 percent. 
.WEDNESDAY...Mostly sunny with isolated showers. Highs 81 to 87.
South winds 10 to 15 mph. Chance of rain 20 percent. 
.WEDNESDAY NIGHT...Partly cloudy in the evening then becoming
mostly cloudy. Scattered showers. Lows 72 to 78. Southeast winds
around 10 mph. Chance of rain 40 percent. 
.THURSDAY...Partly sunny in the morning then becoming mostly
sunny. Scattered showers. Highs 80 to 86. Southeast winds around
10 mph. Chance of rain 30 percent. 
.THURSDAY NIGHT...Mostly clear. Isolated showers in the evening.
Lows 72 to 77. Light winds. Chance of rain 20 percent. 
.FRIDAY...Sunny. Highs 80 to 86. Light winds. 
.FRIDAY NIGHT...Partly cloudy. Lows 71 to 77. Light winds
becoming northeast around 10 mph after midnight. 
.SATURDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 80 to 86. Northeast winds up to 10 mph. Chance of rain
20 percent. 
.SATURDAY NIGHT...Mostly clear. Lows 71 to 77. Northeast winds
around 10 mph. 
.SUNDAY...Sunny. Isolated showers in the afternoon. Highs 80 to
86. Northeast winds up to 10 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly clear. Lows 71 to 77. Northeast winds
around 10 mph. 
.MONDAY...Sunny. Highs 79 to 85. Light winds. 

HIZ044-300715-
Lanai South-
Including Manele
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs around 82. Light winds becoming
southeast 10 to 15 mph in the afternoon. 
.TONIGHT...Partly cloudy. Isolated showers in the evening, then
scattered showers after midnight. Lows around 76. Southeast winds
10 to 15 mph. Chance of rain 30 percent. 
.WEDNESDAY...Mostly sunny with isolated showers. Highs 79 to 84.
South winds 10 to 15 mph. Chance of rain 20 percent. 
.WEDNESDAY NIGHT...Partly cloudy in the evening then becoming
mostly cloudy. Scattered showers. Lows around 76. Southeast winds
around 10 mph. Chance of rain 40 percent. 
.THURSDAY...Partly sunny with scattered showers in the morning,
then mostly sunny with isolated showers in the afternoon. Highs
around 81. Southeast winds up to 10 mph. Chance of rain
30 percent. 
.THURSDAY NIGHT...Mostly clear. Lows 73 to 78. Light winds. 
.FRIDAY...Sunny. Highs around 81. Light winds. 
.FRIDAY NIGHT...Mostly clear. Lows around 75. Light winds. 
.SATURDAY...Mostly sunny. Highs around 81. Light winds. 
.SATURDAY NIGHT...Mostly clear. Lows around 75. Light winds
becoming northeast around 10 mph after midnight. 
.SUNDAY...Sunny. Highs around 81. Northeast winds up to 10 mph. 
.SUNDAY NIGHT...Mostly clear. Lows 72 to 77. Northeast winds
around 10 mph in the evening becoming light. 
.MONDAY...Sunny. Highs around 80. Light winds. 

HIZ015-300715-
Lanai Mauka-
Including Lanai City
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 74 to 83. Light winds becoming south
around 10 mph in the afternoon. 
.TONIGHT...Partly cloudy with isolated showers in the evening,
then mostly cloudy with scattered showers after midnight. Lows
69 to 74. Southeast winds 10 to 15 mph. Chance of rain
30 percent. 
.WEDNESDAY...Mostly sunny with isolated showers. Highs 73 to 82.
South winds 10 to 15 mph. Chance of rain 20 percent. 
.WEDNESDAY NIGHT...Partly cloudy in the evening then becoming
mostly cloudy. Scattered showers. Lows 69 to 74. Southeast winds
around 10 mph. Chance of rain 40 percent. 
.THURSDAY...Partly sunny in the morning then becoming mostly
sunny. Scattered showers. Highs 73 to 82. Southeast winds up to
10 mph. Chance of rain 30 percent. 
.THURSDAY NIGHT...Mostly clear. Lows 68 to 73. Light winds. 
.FRIDAY...Sunny. Highs 72 to 82. Light winds. 
.FRIDAY NIGHT...Partly cloudy. Lows 68 to 73. Light winds
becoming northeast around 10 mph after midnight. 
.SATURDAY...Mostly sunny with isolated showers. Highs 72 to 81.
Northeast winds up to 10 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Mostly clear. Lows 68 to 73. Northeast winds
around 10 mph. 
.SUNDAY...Mostly sunny with isolated showers. Highs 72 to 82.
Northeast winds around 10 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly clear. Lows 68 to 73. Northeast winds
around 10 mph. 
.MONDAY...Sunny. Isolated showers in the afternoon. Highs 72 to
81. Light winds. Chance of rain 20 percent. 

HIZ016-300715-
Kahoolawe-
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Breezy. Highs 80 to 86. East winds 10 to
25 mph. 
.TONIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Breezy. Lows 72 to 77. East winds 10 to 20 mph. 
.WEDNESDAY...Sunny. Isolated showers in the afternoon. Highs
80 to 86. Southeast winds 10 to 15 mph. Chance of rain
20 percent. 
.WEDNESDAY NIGHT...Partly cloudy with isolated showers. Lows
72 to 77. East winds 10 to 15 mph. Chance of rain 20 percent. 
.THURSDAY...Sunny. Highs 79 to 85. East winds 10 to 15 mph. 
.THURSDAY NIGHT...Mostly clear. Lows 71 to 76. East winds 10 to
15 mph. 
.FRIDAY...Sunny. Highs 79 to 85. East winds 10 to 15 mph. 
.FRIDAY NIGHT...Mostly clear. Lows 71 to 76. East winds 10 to
15 mph. 
.SATURDAY...Sunny. Highs 79 to 85. East winds 10 to 15 mph. 
.SATURDAY NIGHT...Mostly clear. Lows 70 to 75. Northeast winds
10 to 15 mph. 
.SUNDAY...Sunny. Highs 79 to 85. Northeast winds around 10 mph. 
.SUNDAY NIGHT...Mostly clear. Lows 70 to 75. Northeast winds
around 10 mph. 
.MONDAY...Sunny. Highs 79 to 84. Light winds. 

HIZ017-300715-
Maui Windward West-
Including Wailuku
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Isolated showers in the afternoon. Highs
around 84 makai to around 66 mauka. Northwest winds up to 10 mph
shifting to the northeast in the afternoon. Chance of rain
20 percent. 
.TONIGHT...Partly cloudy. Lows 70 to 76 makai to around 60 mauka.
North winds up to 10 mph shifting to the south after midnight. 
.WEDNESDAY...Mostly sunny. Isolated showers in the morning, then
scattered showers in the afternoon. Highs around 83 makai to
around 65 mauka. Southeast winds up to 15 mph increasing to 10 to
15 mph in the afternoon. Chance of rain 30 percent. 
.WEDNESDAY NIGHT...Partly cloudy with isolated showers. Lows
60 to 76. Southeast winds up to 10 mph. Chance of rain
20 percent. 
.THURSDAY...Mostly sunny with isolated showers. Highs 64 to 86.
East winds up to 15 mph. Chance of rain 20 percent. 
.THURSDAY NIGHT...Partly cloudy. Isolated showers in the evening.
Lows 60 to 76. East winds up to 10 mph. Chance of rain
20 percent. 
.FRIDAY...Mostly sunny. Highs 64 to 85. East winds up to 15 mph. 
.FRIDAY NIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Scattered showers. Lows 59 to 75. East winds up to 15 mph
increasing to 10 to 15 mph after midnight. Chance of rain
40 percent. 
.SATURDAY...Mostly sunny with scattered showers. Highs 66 to 85.
Northeast winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Partly cloudy with scattered showers. Lows
59 to 75. Northeast winds 10 to 15 mph. Chance of rain
40 percent. 
.SUNDAY...Mostly sunny with scattered showers. Highs 63 to 85.
Northeast winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Partly cloudy. Isolated showers in the evening,
then scattered showers after midnight. Lows 59 to 75. Northeast
winds 10 to 15 mph. Chance of rain 40 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 62 to 84.
Northeast winds around 10 mph. Chance of rain 50 percent. 

HIZ018-300715-
Maui Leeward West-
Including Lahaina, Kaanapali
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 82 to 89. West winds up to 10 mph. 
.TONIGHT...Partly cloudy. Lows 72 to 79. Southwest winds up to
10 mph shifting to the southeast after midnight. 
.WEDNESDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 81 to 87. Southeast winds up to 10 mph. Chance of rain
20 percent. 
.WEDNESDAY NIGHT...Partly cloudy with isolated showers. Lows
71 to 78. Southeast winds around 10 mph. Chance of rain
20 percent. 
.THURSDAY...Mostly sunny with isolated showers. Highs 80 to 87.
East winds up to 10 mph. Chance of rain 20 percent. 
.THURSDAY NIGHT...Partly cloudy. Lows 71 to 77. East winds up to
10 mph. 
.FRIDAY...Mostly sunny. Highs 79 to 86. East winds up to 15 mph. 
.FRIDAY NIGHT...Partly cloudy with isolated showers. Lows 70 to
77. Northeast winds up to 10 mph. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs 79 to 86.
Northeast winds around 10 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy with isolated showers. Lows 70 to
76. Northeast winds around 10 mph. Chance of rain 20 percent. 
.SUNDAY...Mostly sunny with isolated showers. Highs 78 to 86.
Northeast winds around 10 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly clear with isolated showers. Lows 70 to
76. Northeast winds around 10 mph. Chance of rain 20 percent. 
.MONDAY...Mostly sunny with isolated showers. Highs 78 to 85.
Northeast winds around 10 mph. Chance of rain 20 percent. 

HIZ045-300715-
Maui Central Valley North-
Including Kahului
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 83 to 90. Southwest winds up to
10 mph shifting to the north around 10 mph in the afternoon. 
.TONIGHT...Partly cloudy. Lows around 74. Northwest winds up to
10 mph shifting to the east after midnight. 
.WEDNESDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 83 to 89. Southeast winds 10 to 15 mph. Chance of rain
20 percent. 
.WEDNESDAY NIGHT...Partly cloudy. Lows around 74. East winds
around 10 mph. 
.THURSDAY...Mostly sunny in the morning then becoming partly
sunny. Highs 82 to 88. East winds around 10 mph. 
.THURSDAY NIGHT...Partly cloudy. Lows around 73. East winds
around 10 mph. 
.FRIDAY...Mostly sunny. Highs 82 to 88. East winds 10 to 15 mph. 
.FRIDAY NIGHT...Partly cloudy with isolated showers. Lows 70 to
75. East winds around 10 mph. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs 82 to 88.
Northeast winds around 10 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Mostly clear with isolated showers. Lows around
73. Northeast winds around 10 mph. Chance of rain 20 percent. 
.SUNDAY...Sunny with isolated showers. Highs 81 to 88. Northeast
winds around 10 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly clear. Lows 70 to 75. Northeast winds
around 10 mph in the evening becoming light. 
.MONDAY...Mostly sunny with isolated showers. Highs 81 to 87.
Light winds. Chance of rain 20 percent. 

HIZ046-300715-
Maui Central Valley South-
Including Maalaea
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Highs 88 to 93. West winds up to 10 mph. 
.TONIGHT...Partly cloudy. Lows 73 to 81. North winds up to
10 mph. 
.WEDNESDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 87 to 92. Southeast winds 10 to 15 mph. Chance of rain
20 percent. 
.WEDNESDAY NIGHT...Partly cloudy. Lows 73 to 81. East winds 10 to
15 mph. 
.THURSDAY...Mostly sunny in the morning then becoming partly
sunny. Highs 86 to 91. East winds 10 to 15 mph decreasing to up
to 15 mph in the afternoon. 
.THURSDAY NIGHT...Partly cloudy. Lows 71 to 80. Northeast winds
up to 15 mph. 
.FRIDAY...Mostly sunny. Highs around 88. East winds up to 15 mph
increasing to 10 to 15 mph in the afternoon. 
.FRIDAY NIGHT...Partly cloudy. Lows 71 to 79. Northeast winds
10 to 15 mph. 
.SATURDAY...Mostly sunny. Highs around 88. Northeast winds 10 to
15 mph. 
.SATURDAY NIGHT...Mostly clear. Lows 71 to 79. Northeast winds
10 to 15 mph. 
.SUNDAY...Sunny. Highs around 88. Northeast winds 10 to 15 mph. 
.SUNDAY NIGHT...Mostly clear. Lows 71 to 79. North winds 10 to
15 mph. 
.MONDAY...Mostly sunny. Highs 85 to 90. North winds up to 15 mph.

HIZ047-300715-
Windward Haleakala-
Including Haiku, Makawao, Hana
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny with isolated showers. Highs 80 to 85 near
the shore to around 69 near 5000 feet. Southeast winds up to
15 mph shifting to the east in the afternoon. Chance of rain
20 percent. 
.TONIGHT...Mostly cloudy in the evening, then partly cloudy with
isolated showers after midnight. Lows around 74 near the shore to
around 58 near 5000 feet. Southeast winds up to 15 mph. Chance of
rain 20 percent. 
.WEDNESDAY...Mostly sunny with isolated showers in the morning,
then partly sunny with scattered showers in the afternoon. Highs
around 82 near the shore to around 69 near 5000 feet. Southeast
winds 10 to 15 mph decreasing to up to 15 mph in the afternoon.
Chance of rain 40 percent. 
.WEDNESDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Isolated showers. Lows 57 to 76. Southeast winds
up to 15 mph increasing to 10 to 15 mph after midnight. Chance of
rain 20 percent. 
.THURSDAY...Mostly sunny with isolated showers. Highs 67 to 84.
Southeast winds up to 15 mph. Chance of rain 20 percent. 
.THURSDAY NIGHT...Partly cloudy. Lows 56 to 76. Southeast winds
10 to 15 mph. 
.FRIDAY...Mostly sunny. Highs 66 to 83. East winds 10 to 15 mph. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 56 to
76. East winds around 10 mph. Chance of rain 40 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 66 to 83.
East winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
55 to 75. East winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 66 to 83.
Northeast winds around 10 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Partly cloudy. Isolated showers in the evening,
then scattered showers after midnight. Lows 55 to 75. Northeast
winds around 10 mph in the evening becoming light. Chance of rain
50 percent. 
.MONDAY...Mostly sunny with scattered showers. Highs 65 to 83.
Light winds. Chance of rain 40 percent. 

HIZ048-300715-
Kipahulu-
Including Hamoa
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny with scattered showers in the morning, then
partly sunny with isolated showers in the afternoon. Highs 70 to
84. East winds around 10 mph. Chance of rain 30 percent. 
.TONIGHT...Mostly cloudy. Isolated showers in the evening, then
scattered showers after midnight. Lows 65 to 77. East winds 10 to
15 mph. Chance of rain 30 percent. 
.WEDNESDAY...Mostly sunny with isolated showers in the morning,
then partly sunny with scattered showers in the afternoon. Highs
70 to 84. Southeast winds 10 to 15 mph. Chance of rain
40 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with isolated showers. Lows
65 to 76. East winds 10 to 15 mph. Chance of rain 20 percent. 
.THURSDAY...Partly sunny in the morning then becoming mostly
sunny. Isolated showers. Highs 69 to 84. East winds 10 to 15 mph.
Chance of rain 20 percent. 
.THURSDAY NIGHT...Partly cloudy. Lows 64 to 76. East winds 10 to
15 mph. 
.FRIDAY...Mostly sunny. Highs 69 to 83. East winds 10 to 15 mph. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 64 to
76. East winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 69 to 83.
East winds 10 to 15 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
64 to 76. Northeast winds 10 to 15 mph. Chance of rain
40 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 69 to 83.
Northeast winds 10 to 15 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 64 to
75. Northeast winds around 10 mph. Chance of rain 50 percent. 
.MONDAY...Partly sunny with scattered showers. Highs 68 to 83.
Northeast winds around 10 mph. Chance of rain 50 percent. 

HIZ049-300715-
South Maui/Upcountry-
Including Kihei, Makena, Pukalani, Kula, Ulupalakua
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Scattered showers in the afternoon. Highs
around 89 near the shore to around 78 near 4000 feet. Light winds
becoming west around 10 mph in the afternoon. Chance of rain
30 percent. 
.TONIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Lows around 74 near the shore to around 61 near
4000 feet. Northwest winds up to 10 mph shifting to the northeast
after midnight. 
.WEDNESDAY...Mostly sunny with isolated showers in the morning,
then partly sunny with scattered showers in the afternoon. Highs
86 to 91 near the shore to around 77 near 4000 feet. Southeast
winds up to 10 mph. Chance of rain 50 percent. 
.WEDNESDAY NIGHT...Partly cloudy. Isolated showers in the
evening. Lows 58 to 76. East winds up to 10 mph. Chance of rain
20 percent. 
.THURSDAY...Mostly sunny in the morning then becoming partly
sunny. Isolated showers. Highs 71 to 89. East winds up to 10 mph
in the morning becoming light. Chance of rain 20 percent. 
.THURSDAY NIGHT...Partly cloudy. Lows 57 to 76. Light winds
becoming east around 10 mph after midnight. 
.FRIDAY...Sunny in the morning, then partly sunny with isolated
showers in the afternoon. Highs 70 to 89. East winds up to
10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Lows 56 to 75. East winds around 10 mph. 
.SATURDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 70 to 89. Northeast
winds up to 15 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy. Lows 56 to 75. Northeast winds
10 to 15 mph. 
.SUNDAY...Sunny. Isolated showers in the afternoon. Highs 70 to
89. Northeast winds around 10 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly clear. Lows 55 to 74. Northeast winds
around 10 mph. 
.MONDAY...Mostly sunny. Isolated showers in the afternoon. Highs
70 to 89. Light winds. Chance of rain 20 percent. 

HIZ050-300715-
South Haleakala-
Including Kipahulu, Kaupo
341 AM HST Tue Sep 29 2026

.TODAY...Breezy. Mostly sunny with isolated showers. Highs 77 to
86. East winds 10 to 20 mph. Chance of rain 20 percent. 
.TONIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Breezy. Isolated showers. Lows 59 to 77. East winds 10 to
20 mph. Chance of rain 20 percent. 
.WEDNESDAY...Mostly sunny with isolated showers in the morning,
then partly sunny with scattered showers in the afternoon. Highs
77 to 86. East winds 10 to 15 mph shifting to the southeast in
the afternoon. Chance of rain 50 percent. 
.WEDNESDAY NIGHT...Partly cloudy with isolated showers. Lows
59 to 76. East winds up to 15 mph increasing to 10 to 15 mph
after midnight. Chance of rain 20 percent. 
.THURSDAY...Mostly sunny with isolated showers. Highs 76 to 85.
East winds 10 to 15 mph. Chance of rain 20 percent. 
.THURSDAY NIGHT...Partly cloudy. Lows 58 to 76. East winds 10 to
15 mph. 
.FRIDAY...Mostly sunny. Isolated showers in the afternoon. Highs
75 to 84. East winds 10 to 15 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with isolated showers. Lows 57 to
75. East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny with isolated showers. Highs 75 to 84.
East winds 10 to 15 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy with isolated showers. Lows 58 to
75. Northeast winds 10 to 15 mph. Chance of rain 20 percent. 
.SUNDAY...Mostly sunny with isolated showers. Highs 75 to 84.
Northeast winds around 10 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Partly cloudy with isolated showers. Lows 56 to
75. Northeast winds around 10 mph. Chance of rain 20 percent. 
.MONDAY...Mostly sunny with isolated showers. Highs 75 to 84.
Light winds. Chance of rain 20 percent. 

HIZ022-300715-
Haleakala Summit-
Including Haleakala National Park Above 6000 feet
341 AM HST Tue Sep 29 2026

.TODAY...Partly sunny with isolated showers. Highs 62 to 83.
Light winds. Chance of rain 20 percent. 
.TONIGHT...Mostly cloudy with isolated showers. Lows around 55 at
the visitor center to around 47 at the summit. South winds up to
10 mph. Chance of rain 20 percent. 
.WEDNESDAY...Mostly sunny in the morning then becoming partly
sunny. Isolated showers. Highs around 67 at the visitor center to
around 69 at the summit. Southwest winds up to 10 mph. Chance of
rain 20 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with isolated showers. Lows
49 to 66. Light winds. Chance of rain 20 percent. 
.THURSDAY...Partly sunny with isolated showers. Highs 61 to 81.
Light winds. Chance of rain 20 percent. 
.THURSDAY NIGHT...Mostly cloudy. Lows 48 to 64. Light winds
becoming east up to 10 mph after midnight. 
.FRIDAY...Mostly sunny in the morning then becoming partly sunny.
Highs 59 to 81. East winds up to 10 mph in the morning becoming
light. 
.FRIDAY NIGHT...Mostly cloudy with isolated showers. Lows 47 to
64. Light winds becoming northeast around 10 mph after midnight.
Chance of rain 20 percent. 
.SATURDAY...Partly sunny with isolated showers. Highs 59 to 81.
Northeast winds up to 10 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Breezy. Isolated showers. Lows 47 to 63. Northeast
winds 10 to 20 mph. Chance of rain 20 percent. 
.SUNDAY...Mostly sunny. Breezy. Scattered showers in the morning,
then isolated showers in the afternoon. Highs 61 to 81. Northeast
winds 10 to 20 mph. Chance of rain 40 percent. 
.SUNDAY NIGHT...Partly cloudy. Breezy. Scattered showers in the
evening, then isolated showers after midnight. Lows 47 to 63.
Northeast winds 10 to 20 mph. Chance of rain 40 percent. 
.MONDAY...Mostly sunny with isolated showers. Highs 60 to 80.
Northeast winds around 10 mph in the morning becoming light.
Chance of rain 20 percent. 

HIZ023-300715-
Kona-
Including Kailua-Kona, Kealakekua, Milolii
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 85 to 90 near the shore
to around 72 near 5000 feet. Light winds. Chance of rain
20 percent. 
.TONIGHT...Partly cloudy. Lows 69 to 76 near the shore to around
56 near 5000 feet. Light winds becoming east up to 10 mph after
midnight. 
.WEDNESDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 84 to 90 near the shore to around 71 near 5000 feet.
Southwest winds up to 10 mph. Chance of rain 20 percent. 
.WEDNESDAY NIGHT...Partly cloudy. Lows 54 to 79. Light winds. 
.THURSDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 68 to 89. Light winds.
Chance of rain 20 percent. 
.THURSDAY NIGHT...Mostly cloudy. Lows 55 to 78. Light winds. 
.FRIDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 67 to 89. North winds up
to 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy. Isolated showers in the evening.
Lows 54 to 78. Northwest winds up to 10 mph in the evening
becoming light. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 67 to 89. Light winds.
Chance of rain 20 percent. 
.SATURDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Lows 53 to 78. Light winds. 
.SUNDAY...Mostly sunny. Isolated showers in the afternoon. Highs
68 to 89. Light winds. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly cloudy with isolated showers in the
evening, then partly cloudy after midnight. Lows 53 to 78. Light
winds. Chance of rain 20 percent. 
.MONDAY...Mostly sunny. Isolated showers in the afternoon. Highs
68 to 89. Light winds. Chance of rain 20 percent. 

HIZ051-300715-
Big Island South-
Including Ocean View
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny. Breezy. Isolated showers in the afternoon.
Highs around 84 near the shore to around 70 near 5000 feet. East
winds up to 20 mph increasing to 10 to 20 mph in the afternoon.
Chance of rain 20 percent. 
.TONIGHT...Breezy. Partly cloudy with isolated showers. Lows
around 76 near the shore to around 60 near 5000 feet. East winds
up to 20 mph. Chance of rain 20 percent. 
.WEDNESDAY...Breezy. Mostly sunny with isolated showers in the
morning, then partly sunny with scattered showers in the
afternoon. Highs around 84 near the shore to around 70 near
5000 feet. East winds 10 to 20 mph. Chance of rain 40 percent. 
.WEDNESDAY NIGHT...Partly cloudy. Isolated showers in the
evening, then scattered showers after midnight. Lows 60 to 79.
East winds 10 to 15 mph. Chance of rain 30 percent. 
.THURSDAY...Mostly sunny in the morning then becoming partly
sunny. Scattered showers. Highs 68 to 85. East winds up to
15 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Lows 60 to 78. East winds up to 15 mph increasing
to 10 to 15 mph after midnight. 
.FRIDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 68 to 84. East winds
10 to 15 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy. Isolated showers in the evening.
Lows 59 to 78. East winds up to 15 mph. Chance of rain
20 percent. 
.SATURDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 68 to 85. East winds up
to 15 mph. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy. Lows 60 to 78. Northeast winds
up to 10 mph. 
.SUNDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 68 to 84. Light winds
becoming southeast up to 10 mph in the afternoon. Chance of rain
20 percent. 
.SUNDAY NIGHT...Mostly cloudy with isolated showers in the
evening, then partly cloudy after midnight. Lows 59 to 78. East
winds up to 10 mph in the evening becoming light. Chance of rain
20 percent. 
.MONDAY...Mostly sunny. Scattered showers in the afternoon. Highs
68 to 84. Light winds. Chance of rain 40 percent. 

HIZ052-300715-
Big Island Southeast-
Including South Point, Pahala
341 AM HST Tue Sep 29 2026

.TODAY...Partly sunny. Isolated showers in the afternoon. Highs
82 to 88 near the shore to 69 to 74 near 4000 feet. East winds up
to 10 mph. Chance of rain 20 percent. 
.TONIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Isolated showers. Lows 69 to 75 near the shore to around
60 near 4000 feet. East winds up to 10 mph. Chance of rain
20 percent. 
.WEDNESDAY...Partly sunny. Isolated showers in the morning, then
scattered showers in the afternoon. Highs 81 to 88 near the shore
to 69 to 74 near 4000 feet. East winds up to 10 mph. Chance of
rain 40 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with scattered showers. Lows
58 to 78. Light winds. Chance of rain 40 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 68 to 87.
East winds up to 10 mph. Chance of rain 50 percent. 
.THURSDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Lows 57 to 77. East winds up to 10 mph. 
.FRIDAY...Mostly sunny in the morning then becoming partly sunny.
Highs 68 to 88. East winds around 10 mph. 
.FRIDAY NIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Scattered showers. Lows 58 to 77. Northeast winds up to
10 mph. Chance of rain 40 percent. 
.SATURDAY...Mostly sunny in the morning then becoming partly
sunny. Isolated showers. Highs 68 to 88. East winds 10 to 15 mph.
Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy with scattered showers. Lows
57 to 77. Northeast winds up to 15 mph. Chance of rain
40 percent. 
.SUNDAY...Mostly sunny in the morning then becoming partly sunny.
Isolated showers. Highs 68 to 89. Northeast winds up to 15 mph.
Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Isolated showers. Lows 57 to 77. Northeast winds up to
10 mph. Chance of rain 20 percent. 
.MONDAY...Mostly sunny with isolated showers. Highs 69 to 88.
Light winds. Chance of rain 20 percent. 

HIZ053-300715-
Big Island East-
Including Hilo, Volcano, Pahoa, Mountain View, Laupahoehoe
341 AM HST Tue Sep 29 2026

.TODAY...Partly sunny. Isolated showers in the afternoon. Highs
around 84 near the shore to around 70 at 4000 feet. South winds
up to 10 mph shifting to the southeast in the afternoon. Chance
of rain 20 percent. 
.TONIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Isolated showers. Lows 68 to 74 near the shore to around
60 at 4000 feet. South winds up to 15 mph. Chance of rain
20 percent. 
.WEDNESDAY...Mostly sunny with isolated showers in the morning,
then partly sunny with scattered showers in the afternoon. Highs
around 83 near the shore to around 69 at 4000 feet. Southeast
winds up to 15 mph. Chance of rain 30 percent. 
.WEDNESDAY NIGHT...Mostly cloudy with isolated showers in the
evening, then partly cloudy with scattered showers after
midnight. Lows 57 to 78. Southeast winds up to 10 mph. Chance of
rain 30 percent. 
.THURSDAY...Partly sunny with scattered showers. Highs 66 to 84.
East winds up to 10 mph. Chance of rain 30 percent. 
.THURSDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Lows 56 to 77. Light winds becoming southeast up
to 10 mph after midnight. 
.FRIDAY...Mostly sunny in the morning then becoming partly sunny.
Highs 66 to 84. Southeast winds up to 10 mph. 
.FRIDAY NIGHT...Mostly cloudy with scattered showers. Lows 55 to
77. Light winds. Chance of rain 50 percent. 
.SATURDAY...Partly sunny with scattered showers. Highs 66 to 84.
Northeast winds up to 10 mph. Chance of rain 50 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
55 to 77. Northeast winds around 10 mph. Chance of rain
50 percent. 
.SUNDAY...Partly sunny with scattered showers. Highs 66 to 84.
Northeast winds up to 10 mph. Chance of rain 50 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 55 to
77. North winds up to 10 mph. Chance of rain 50 percent. 
.MONDAY...Partly sunny with scattered showers in the morning,
then mostly sunny with isolated showers in the afternoon. Highs
66 to 84. Northeast winds up to 10 mph. Chance of rain
50 percent. 

HIZ054-300715-
Big Island North-
Including Honokaa, Kamuela, Waipio Valley, Hawi
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny in the morning, then partly sunny with
scattered showers in the afternoon. Highs around 83 near the
shore to 72 to 81 near 3000 feet. East winds up to 15 mph. Chance
of rain 40 percent. 
.TONIGHT...Partly cloudy. Lows 68 to 75 near the shore to 62 to
69 near 3000 feet. Southeast winds up to 10 mph in the evening
becoming light. 
.WEDNESDAY...Sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs around 83 near the shore
to 72 to 81 near 3000 feet. Southeast winds up to 10 mph shifting
to the northeast in the afternoon. Chance of rain 20 percent. 
.WEDNESDAY NIGHT...Partly cloudy. Lows 56 to 76. Southeast winds
up to 10 mph. 
.THURSDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 65 to 84. East winds up to 10 mph. Chance of rain
20 percent. 
.THURSDAY NIGHT...Partly cloudy. Lows 54 to 75. East winds up to
10 mph. 
.FRIDAY...Mostly sunny. Isolated showers in the afternoon. Highs
65 to 83. East winds up to 10 mph. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Scattered showers. Lows 54 to 75. East winds up to
10 mph. Chance of rain 50 percent. 
.SATURDAY...Mostly sunny in the morning then becoming partly
sunny. Scattered showers. Highs 64 to 83. East winds up to
10 mph. Chance of rain 40 percent. 
.SATURDAY NIGHT...Mostly cloudy with scattered showers. Lows
53 to 74. East winds 10 to 15 mph. Chance of rain 50 percent. 
.SUNDAY...Partly sunny in the morning then becoming mostly sunny.
Scattered showers. Highs 64 to 84. Northeast winds 10 to 15 mph.
Chance of rain 40 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers. Lows 53 to
74. Light winds becoming east up to 10 mph after midnight. Chance
of rain 50 percent. 
.MONDAY...Mostly sunny. Scattered showers in the morning, then
isolated showers in the afternoon. Highs 64 to 83. Northeast
winds up to 10 mph in the morning becoming light. Chance of rain
40 percent. 

HIZ026-300715-
Kohala-
Including Kawaihae, Waikoloa, Waikii, Puuanahulu
341 AM HST Tue Sep 29 2026

.TODAY...Mostly sunny in the morning, then partly sunny with
scattered showers in the afternoon. Highs 85 to 91 near the shore
to 69 to 76 above 4000 feet. Northeast winds up to 10 mph
shifting to the northwest in the afternoon. Chance of rain
40 percent. 
.TONIGHT...Partly cloudy. Lows 72 to 77 near the shore to around
58 above 4000 feet. Light winds. 
.WEDNESDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 85 to 91 near the shore to 69 to 76 above 4000 feet.
Northwest winds up to 10 mph. Chance of rain 20 percent. 
.WEDNESDAY NIGHT...Partly cloudy. Lows 55 to 77. Light winds. 
.THURSDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 68 to 91. Light winds. Chance of rain 20 percent. 
.THURSDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Lows 55 to 77. Light winds. 
.FRIDAY...Mostly sunny. Isolated showers in the afternoon. Highs
67 to 90. Light winds. Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy with isolated showers in the
evening, then partly cloudy after midnight. Lows 54 to 76. Light
winds. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny. Isolated showers in the afternoon.
Highs 67 to 91. Light winds. Chance of rain 20 percent. 
.SATURDAY NIGHT...Partly cloudy. Lows 53 to 76. Light winds
becoming northeast up to 10 mph after midnight. 
.SUNDAY...Sunny with isolated showers. Highs 67 to 91. Northeast
winds up to 10 mph in the morning becoming light. Chance of rain
20 percent. 
.SUNDAY NIGHT...Partly cloudy. Isolated showers in the evening.
Lows 53 to 76. Light winds. Chance of rain 20 percent. 
.MONDAY...Sunny. Isolated showers in the afternoon. Highs 67 to
90. Light winds. Chance of rain 20 percent. 

HIZ027-300715-
Big Island Interior-
Including Bradshaw Field, Saddle Road Above 5000 feet
341 AM HST Tue Sep 29 2026

.TODAY...Mostly cloudy. Isolated showers in the afternoon. Highs
67 to 75 near 5000 feet to 62 to 68 near 8000 feet. West winds up
to 10 mph. Chance of rain 20 percent. 
.TONIGHT...Mostly cloudy in the evening then becoming partly
cloudy. Lows 52 to 60 near 5000 feet to 49 to 54 near 8000 feet.
Light winds becoming southwest up to 10 mph after midnight. 
.WEDNESDAY...Mostly sunny in the morning then becoming mostly
cloudy. Isolated showers. Highs 67 to 75 near 5000 feet to 61 to
68 near 8000 feet. West winds up to 10 mph. Chance of rain
20 percent. 
.WEDNESDAY NIGHT...Mostly cloudy. Isolated showers after
midnight. Lows 49 to 60. Light winds. Chance of rain 20 percent. 
.THURSDAY...Mostly sunny with scattered showers in the morning,
then mostly cloudy with isolated showers in the afternoon. Highs
60 to 74. Light winds. Chance of rain 40 percent. 
.THURSDAY NIGHT...Mostly cloudy. Lows 48 to 60. Light winds. 
.FRIDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 59 to 75. Light winds.
Chance of rain 20 percent. 
.FRIDAY NIGHT...Mostly cloudy. Isolated showers in the evening.
Lows 47 to 59. Light winds. Chance of rain 20 percent. 
.SATURDAY...Mostly sunny in the morning, then partly sunny with
isolated showers in the afternoon. Highs 60 to 75. Light winds.
Chance of rain 20 percent. 
.SATURDAY NIGHT...Mostly cloudy in the evening then becoming
partly cloudy. Lows 46 to 59. Northeast winds up to 10 mph. 
.SUNDAY...Sunny in the morning, then partly sunny with isolated
showers in the afternoon. Highs 60 to 76. Northeast winds up to
10 mph. Chance of rain 20 percent. 
.SUNDAY NIGHT...Mostly cloudy with scattered showers in the
evening, then partly cloudy after midnight. Lows 46 to 59.
Northeast winds up to 10 mph. Chance of rain 40 percent. 
.MONDAY...Mostly sunny. Isolated showers in the afternoon. Highs
60 to 75. Light winds. Chance of rain 20 percent. 

HIZ028-300715-
Big Island Summits-
Including Mauna Loa and Mauna Kea Above 8000 feet
341 AM HST Tue Sep 29 2026

.TODAY...Mostly cloudy. Isolated showers in the afternoon. Highs
around 60 at the visitor information station to around 50 near
the summits. West winds up to 10 mph. Chance of rain 20 percent. 
.TONIGHT...Mostly cloudy in the evening then becoming mostly
clear. Lows around 45 at the visitor information station to
around 39 near the summits. Southwest winds up to 10 mph. 
.WEDNESDAY...Mostly sunny in the morning, then mostly cloudy with
isolated showers in the afternoon. Highs around 61 at the visitor
information station to around 49 near the summits. West winds up
to 10 mph. Chance of rain 20 percent. 
.WEDNESDAY NIGHT...Mostly cloudy. Lows 39 to 55. Light winds. 
.THURSDAY...Mostly sunny in the morning then becoming mostly
cloudy. Highs 51 to 71. Light winds. 
.THURSDAY NIGHT...Mostly cloudy. Lows 39 to 53. Light winds. 
.FRIDAY...Mostly sunny in the morning then becoming partly sunny.
Highs 47 to 71. Light winds. 
.FRIDAY NIGHT...Mostly cloudy. Lows 41 to 53. Light winds. 
.SATURDAY...Sunny in the morning then becoming partly sunny.
Highs 48 to 71. Northeast winds 10 to 15 mph. 
.SATURDAY NIGHT...Partly cloudy. Breezy. Lows 42 to 52. Northeast
winds 10 to 20 mph. 
.SUNDAY...Sunny in the morning then becoming partly sunny.
Breezy. Highs 48 to 71. Northeast winds 10 to 20 mph. 
.SUNDAY NIGHT...Mostly cloudy in the evening then becoming mostly
clear. Breezy. Lows 41 to 52. Northeast winds 10 to 20 mph
decreasing to up to 15 mph after midnight. 
.MONDAY...Mostly sunny. Highs 49 to 71. Light winds.
```

---

### 2. AIRMETs

| Field | Value |
|---|---|
| **Resource ID** | wa0_airmets |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=WA0&issuedby=HI |
| **Collected** | 2026-09-29T05:48:03.861168-10:00 HST |

```text
837
WAHW31 PHFO 291532
WA0HI

HNLS WA 291600
AIRMET SIERRA UPDATE 2 FOR IFR VALID UNTIL 292200
.
NO SIGNIFICANT IFR EXP.

=HNLT WA 291600
AIRMET TANGO UPDATE 2 FOR TURB VALID UNTIL 292200
.
AIRMET TURB...HI
OVER AND IMT S THRU W OF MTN.
TEMPO MOD TURB BLW 090.
COND CONT BEYOND 2200Z.

=HNLZ WA 291600
AIRMET ZULU UPDATE 2 FOR ICE AND FZLVL VALID UNTIL 292200
.
NO SIGNIFICANT ICE EXP.
.
FZLVL...153 PHLI SLOPING TO 169 PHTO.
```

---

### 3. Area Forecast Discussion

| Field | Value |
|---|---|
| **Resource ID** | afd_area_forecast_discussion |
| **Official source** | https://api.weather.gov/products/types/AFD/locations/HFO |
| **Collected** | 2026-09-29T03:52:32.214050-10:00 HST |

```text
000
FXHW60 PHFO 291341
AFDHFO

Area Forecast Discussion
National Weather Service Honolulu HI
341 AM HST Tue Sep 29 2026

.SYNOPSIS...
Moderate to locally breezy trade winds will veer from the
southeasterly direction today with a gradual weakening trend for 
most islands except for Kauai and Niihau, where some increasing 
winds are expected to develop from this afternoon into the 
Wednesday as Nolo reaches the closest point of approach to both 
islands. Clouds and showers will increase into Thursday as Nolo 
passes to the west pulling up deep tropical moisture along the 
east side of the storm increasing showers over Niihau, Kauai and 
Oahu. Nolo moves away to the northwest by this weekend with drier 
easterly trade winds building back in across the Hawaii Region.

.DISCUSSION...
Comparing this mornings satellite imagery to the latest 11 PM HST
forecast from the National Hurricane Center, Hurricane Nolo 
remains on a northerly track, forecast to pass roughly 300 miles 
west of Kauai. Strong vertical wind shear continues to weaken 
Nolo, which is forecast to weaken down to tropical storm strength
over the next 36 to 48 hours. The main threats with Hurricane Nolo
over the next few days will remain the potential for locally heavy
rain bands that may develop, and high surf along south facing 
shores of Kauai County. 

Deep tropical moisture riding up the eastern flank of Nolo will
increase shower trends later today for Niihau and Kauai, even 
reaching Oahu by tonight. These showers may become heavy at times
and produce higher amounts of rainfall along south and southeast 
mountain slopes. At this time we are only expecting up to advisory
level flooding potential for Kauai County as Nolo passes west of 
the islands. However, we will continue to closely monitor any 
developing rain bands for local scale training or terrain 
anchoring features that could create localized flood warning 
concerns. Please continue to monitor weather conditions closely 
through Wednesday as local scale rainfall impacts may rapidly 
change over time.

Drier and more stable air returns to the western islands by Friday
as the upper level ridge builds back in and light to moderate easterly
trades return improving weather conditions statewide through 
Sunday. Brief passing showers are possibly, mainly during the 
overnight to early morning hours during this time period. 

By Monday a weak low pressure system drops into the region and deepens
several hundred miles northeast of the Big Island. Northeasterly 
winds along the western flank of the surface low will drive a 
convergence cloud band into the Hawaiian Islands from the north 
early next week. This cloud band will likely bring a several day
period of enhanced shower trends to all islands from Monday into 
Wednesday. These clouds and showers may linger near the Big
Island through the end of next week. Higher rainfall amounts will  
mainly impact the northeastern slopes of Mauna Kea, and include
the communities surrounding Hilo.

.AVIATION...
Moderate to locally breezy trade winds will continue to veer to 
the southeasterly direction today and continue gradual weakening.
Isolated showers are possible across windward and mountain areas 
tonight into the morning with brief MVFR conditions. Moisture 
will increase across Kauai and Oahu this afternoon into Wednesday
bringing an increased likelihood of showers. Showers are most 
likely across Kauai starting late morning today with shower 
chances gradually increasing for Oahu later today into Wednesday.

AIRMET Tango remains in effect for moderate turbulence below 
9,000 feet over and immediately downwind of island terrain. This 
AIRMET will likely be needed at least through Wednesday.

.MARINE...
Under the influence of Hurricane Nolo, now located several 
hundred nautical miles west of the Hawaiian Islands, winds have
shifted out of the southeast at moderate to fresh levels for much
of the marine area. Winds will be strong and possibly near gale in
the coastal zones closer to Nolo, especially as it tracks north
tonight and Wednesday. As a result, the Small Craft Advisory
remains in effect for the waters around Kauai through Wednesday. 
Winds remain southeasterly through Friday as Nolo creeps slowly 
westward away from the islands. Once it begins to accelerate away 
over the weekend, east to northeasterly trade winds return.

A moderate, medium-period southwest swell originating from Hurricane
Nolo will produce elevated surf for south and west facing shores
today. For Kauai and Niihau, best positioned to receive swell from 
the hurricane, some advisory level surf is still possible today along 
south-facing shores, for which a High Surf Advisory remains in
effect. There is considerable uncertainty with how long advisory
level surf will linger as Hurricane Nolo lifts north and becomes 
centered some 250 to 300 nautical miles west of Kauai by 
Wednesday. On this track, west shore surf will remain elevated, 
but likely remain below advisory criteria as south-facing shores 
see a gradual decline in surf through mid-week. For the latter 
half of the week, south shore surf will be primarily driven by a 
series of small, long to medium period south swells originating 
from near New Zealand. 

Surf along east shores slowly declines as trades veer southeast 
and diminish, then return as light to moderate easterlies this 
weekend. For north-facing shores, the existing small, medium-period 
swell fades through Wednesday. Multiple rounds of tiny swell 
originating out of the northwest quadrant will reach north and select 
west facing exposures next week as the storm track in the vicinity of 
the Aleutian Islands becomes increasingly active.

.FIRE WEATHER...
Wind speeds for most areas will decrease over the next 24 hours.
However, wind speeds for Kauai County will increase into the
breezy range with higher gusts through Wednesday as Hurricane Nolo
passes roughly 300 miles to the west of the islands. Nolo's
passage will boost humidity levels, decreasing critical fire
concerns. Subsidence inversion heights near Maui and the Big
Island today will remain between the 5,500 and 6,500 feet 
elevation level.

.HFO WATCHES/WARNINGS/ADVISORIES...
High Surf Advisory until 6 PM HST this evening for Kauai South-
Kauai Southwest-Niihau.

Small Craft Advisory until 6 PM HST Wednesday for Kauai Channel-
Kauai Leeward Waters-Kauai Northwest Waters-Kauai Windward 
Waters.

DISCUSSION...Bohlin
AVIATION...Pechacek 
MARINE...Quesada
FIRE WEATHER...Bohlin
```

---

### 4. Coastal Waters Forecast (within 40nm)

| Field | Value |
|---|---|
| **Resource ID** | cwf_coastal_waters |
| **Official source** | https://api.weather.gov/products/types/CWF/locations/HFO |
| **Collected** | 2026-09-29T03:35:32.307348-10:00 HST |

```text
000
FZHW50 PHFO 291332
CWFHFO

Coastal Waters Forecast
National Weather Service Honolulu HI
332 AM HST Tue Sep 29 2026

Hawaiian coastal waters within 40 nautical miles including the
Hawaiian Islands Humpback Whale National Marine Sanctuary.

PHZ100-300230-
332 AM HST Tue Sep 29 2026

.Synopsis for Hawaiian coastal waters...
Moderate to fresh southeast winds will prevail as Hurricane Nolo 
remains several hundred miles west of the Hawaiian Islands, 
tracking north. Strong to near gale force winds will be possible
near Kauai as Nolo becomes centered west of the island tonight
into Wednesday. Nolo is forecast to move farther away to the west
after this, allowing winds to diminish and back out of the east 
for the latter half of the week.

PHZ110-300230-
Kauai Northwest Waters-
332 AM HST Tue Sep 29 2026

...SMALL CRAFT ADVISORY IN EFFECT THROUGH WEDNESDAY AFTERNOON...

.TODAY...East southeast winds 20 to 25 knots. Seas 7 to 10 feet,
building to 9 to 12 feet this afternoon. Wave Detail: Southeast
9 feet at 7 seconds and southwest 6 feet at 11 seconds. Scattered
showers this morning, then frequent showers this afternoon. 
.TONIGHT...Southeast winds 25 to 30 knots. Seas 9 to 13 feet,
subsiding to 9 to 11 feet after midnight. Wave Detail: South
southeast 10 feet at 7 seconds and west southwest 6 feet at
11 seconds. Frequent showers with isolated thunderstorms. 
.WEDNESDAY...South southeast winds 20 to 25 knots. Seas 7 to
10 feet. Wave Detail: South southeast 9 feet at 7 seconds and
west southwest 5 feet at 11 seconds. Frequent showers. 
.WEDNESDAY NIGHT...South southeast winds 15 to 20 knots. Seas
7 to 9 feet, subsiding to 6 to 7 feet after midnight. Wave
Detail: South southeast 7 feet at 7 seconds and west southwest
5 feet at 11 seconds. Frequent showers. 
.THURSDAY...Southeast winds 15 to 20 knots. Seas 5 to 7 feet.
Wave Detail: Southeast 6 feet at 6 seconds and west southwest
4 feet at 11 seconds. Numerous showers. 
.THURSDAY NIGHT...Southeast winds 15 to 20 knots. Seas 5 to
6 feet. Wave Detail: Southeast 6 feet at 6 seconds, west
southwest 4 feet at 11 seconds and north northwest 3 feet at
10 seconds. Scattered showers. 
.FRIDAY...Southeast winds 10 to 15 knots. Seas 5 to 6 feet. Wave
Detail: East southeast 5 feet at 6 seconds, west southwest 4 feet
at 11 seconds and north northwest 3 feet at 9 seconds. Scattered
showers. 
.SATURDAY...East winds 10 to 15 knots. Seas 4 to 5 feet. Wave
Detail: Northwest 5 feet at 10 seconds, east southeast 4 feet at
6 seconds and west southwest 4 feet at 11 seconds. Scattered
showers.  

Winds and seas higher in and near tstms.

PHZ111-300230-
Kauai Windward Waters-
332 AM HST Tue Sep 29 2026

...SMALL CRAFT ADVISORY IN EFFECT THROUGH WEDNESDAY AFTERNOON...

.TODAY...East southeast winds 15 to 20 knots. Seas 6 to 9 feet.
Wave Detail: East 7 feet at 7 seconds and southwest 5 feet at
11 seconds. Scattered showers. 
.TONIGHT...East southeast winds 20 to 25 knots, becoming
southeast 25 to 30 knots after midnight. Seas 8 to 10 feet. Wave
Detail: South southeast 9 feet at 7 seconds and southwest 5 feet
at 11 seconds. Frequent showers. 
.WEDNESDAY...South southeast winds 20 to 25 knots. Seas 8 to
10 feet. Wave Detail: South southeast 9 feet at 7 seconds and
southwest 4 feet at 11 seconds. Frequent showers. 
.WEDNESDAY NIGHT...South southeast winds 15 to 20 knots. Seas
7 to 9 feet, subsiding to 6 feet after midnight. Wave Detail:
South southeast 8 feet at 7 seconds and southwest 4 feet at
11 seconds. Frequent showers. 
.THURSDAY...Southeast winds to 15 knots. Seas 5 to 6 feet. Wave
Detail: East southeast 6 feet at 6 seconds and southwest 3 feet
at 11 seconds. Numerous showers, mainly in the morning. 
.THURSDAY NIGHT...East southeast winds 15 to 20 knots. Seas 5 to
6 feet. Wave Detail: East southeast 6 feet at 6 seconds,
southwest 4 feet at 11 seconds and north northwest 3 feet at
10 seconds. Scattered showers. 
.FRIDAY...East southeast winds 10 to 15 knots. Seas 5 to 6 feet.
Wave Detail: East 5 feet at 6 seconds, southwest 4 feet at
11 seconds and north 3 feet at 9 seconds. Scattered showers. 
.SATURDAY...East winds to 15 knots, backing to east northeast.
Seas 4 to 5 feet. Wave Detail: West northwest 5 feet at
10 seconds and east southeast 4 feet at 5 seconds. Scattered
showers.  

PHZ112-300230-
Kauai Leeward Waters-
332 AM HST Tue Sep 29 2026

...SMALL CRAFT ADVISORY IN EFFECT THROUGH WEDNESDAY AFTERNOON...

.TODAY...East southeast winds 20 to 25 knots. Seas 9 to 13 feet.
Wave Detail: South southeast 10 feet at 7 seconds and west
southwest 7 feet at 11 seconds. Frequent showers. 
.TONIGHT...South southeast winds 25 to 30 knots. Seas 10 to
13 feet, subsiding to 9 to 10 feet after midnight. Wave Detail:
South southeast 10 feet at 7 seconds and west southwest 6 feet at
11 seconds. Frequent heavy showers. Isolated thunderstorms after
midnight. 
.WEDNESDAY...South winds 20 to 25 knots. Seas 8 to 10 feet. Wave
Detail: Southeast 9 feet at 7 seconds and west southwest 5 feet
at 11 seconds. Frequent showers. 
.WEDNESDAY NIGHT...South southeast winds 15 to 20 knots. Seas
8 to 9 feet, subsiding to 5 to 7 feet after midnight. Wave
Detail: Southeast 8 feet at 7 seconds and west southwest 4 feet
at 11 seconds. Frequent showers. 
.THURSDAY...South southeast winds 15 to 20 knots. Seas 5 to
6 feet. Wave Detail: Southeast 6 feet at 6 seconds, west
southwest 4 feet at 11 seconds and north northwest 3 feet at
10 seconds. Frequent showers. 
.THURSDAY NIGHT...Southeast winds to 15 knots. Seas 5 to 6 feet.
Wave Detail: South southeast 6 feet at 6 seconds, west southwest
4 feet at 11 seconds and north northwest 3 feet at 10 seconds.
Frequent showers. 
.FRIDAY...Southeast winds 10 to 15 knots. Seas 4 to 6 feet. Wave
Detail: Southeast 6 feet at 6 seconds, west southwest 4 feet at
11 seconds and north northwest 3 feet at 9 seconds. Numerous
showers, mainly in the morning. 
.SATURDAY...East winds 10 to 15 knots. Seas 4 to 5 feet. Wave
Detail: Northwest 5 feet at 10 seconds, southeast 4 feet at
6 seconds and south southwest 4 feet at 11 seconds. Scattered
showers.  

Winds and seas higher in and near tstms.

PHZ113-300230-
Kauai Channel-
332 AM HST Tue Sep 29 2026

...SMALL CRAFT ADVISORY IN EFFECT THROUGH WEDNESDAY AFTERNOON...

.TODAY...Southeast winds 15 to 20 knots. Seas 7 to 9 feet. Wave
Detail: East southeast 7 feet at 7 seconds and west southwest
6 feet at 11 seconds. Scattered showers this morning, then
numerous showers this afternoon. 
.TONIGHT...Southeast winds 20 to 25 knots, becoming south
southeast 25 to 30 knots after midnight. Seas 8 to 10 feet. Wave
Detail: South southeast 8 feet at 7 seconds and west southwest
5 feet at 11 seconds. Frequent showers. Isolated thunderstorms
after midnight. 
.WEDNESDAY...South southeast winds 20 to 25 knots. Seas 8 to
9 feet. Wave Detail: South southeast 8 feet at 7 seconds and west
southwest 4 feet at 11 seconds. Frequent showers. 
.WEDNESDAY NIGHT...South southeast winds to 15 knots. Seas 8 to
9 feet, subsiding to 5 to 6 feet after midnight. Wave Detail:
South southeast 8 feet at 7 seconds and west southwest 4 feet at
11 seconds. Frequent showers. 
.THURSDAY...South southeast winds to 15 knots. Seas 5 to 6 feet.
Wave Detail: Southeast 6 feet at 6 seconds and west southwest
4 feet at 11 seconds. Frequent showers. 
.THURSDAY NIGHT...Southeast winds 10 to 15 knots. Seas to 5 feet.
Wave Detail: Southeast 5 feet at 6 seconds, west southwest 4 feet
at 11 seconds and north northwest 3 feet at 10 seconds. Numerous
showers. 
.FRIDAY...Southeast winds 10 to 15 knots, backing to east
southeast 7 to 10 knots. Seas 4 to 5 feet. Wave Detail: East
southeast 5 feet at 6 seconds, southwest 4 feet at 11 seconds and
north 3 feet at 9 seconds. Scattered showers. 
.SATURDAY...East northeast winds 10 to 15 knots. Seas 4 to
5 feet. Wave Detail: East southeast 4 feet at 5 seconds,
northwest 3 feet at 9 seconds and south southwest 3 feet at
11 seconds. Scattered showers through the night. Isolated showers
in the evening, then scattered showers after midnight.  

Winds and seas higher in and near tstms.

PHZ114-300230-
Oahu Windward Waters-
332 AM HST Tue Sep 29 2026

.TODAY...East southeast winds 15 to 20 knots. Seas 5 to 8 feet.
Wave Detail: East 6 feet at 6 seconds and southwest 5 feet at
11 seconds. Isolated showers this morning. Scattered showers this
afternoon. 
.TONIGHT...East southeast winds to 20 knots. Seas 5 to 8 feet.
Wave Detail: East southeast 6 feet at 6 seconds and west
southwest 4 feet at 11 seconds. Scattered showers. 
.WEDNESDAY...Southeast winds 15 to 20 knots. Seas 5 to 7 feet.
Wave Detail: East southeast 6 feet at 6 seconds and west
southwest 4 feet at 11 seconds. Scattered showers in the morning,
then numerous showers in the afternoon. 
.WEDNESDAY NIGHT...Southeast winds 10 to 15 knots. Seas 5 to
7 feet. Wave Detail: East southeast 6 feet at 6 seconds and west
southwest 3 feet at 11 seconds. Numerous showers. 
.THURSDAY...East southeast winds to 15 knots. Seas 5 to 6 feet.
Wave Detail: East southeast 5 feet at 6 seconds and west
southwest 3 feet at 11 seconds. Numerous showers, mainly in the
morning. 
.THURSDAY NIGHT...East southeast winds to 15 knots. Seas to
5 feet. Wave Detail: East southeast 5 feet at 6 seconds, north
northwest 3 feet at 10 seconds and west southwest 3 feet at
11 seconds. Scattered showers. 
.FRIDAY...East southeast winds 10 to 15 knots. Seas to 5 feet.
Wave Detail: East 5 feet at 6 seconds, north 3 feet at 9 seconds
and west southwest 3 feet at 11 seconds. Isolated showers through
the night, then scattered showers through the day. 
.SATURDAY...East winds to 15 knots, backing to east northeast.
Seas 4 to 5 feet. Wave Detail: East southeast 4 feet at 5 seconds
and west northwest 4 feet at 10 seconds. Scattered showers.  

PHZ115-300230-
Oahu Leeward Waters-
332 AM HST Tue Sep 29 2026

.TODAY...Southeast winds 15 to 20 knots. Seas 6 to 8 feet. Wave
Detail: South southeast 6 feet at 6 seconds and west southwest
5 feet at 11 seconds. Scattered showers. 
.TONIGHT...Southeast winds 15 to 20 knots, becoming south
southeast 20 to 25 knots after midnight. Seas 6 to 8 feet. Wave
Detail: South southeast 7 feet at 6 seconds and west southwest
4 feet at 11 seconds. Numerous showers. 
.WEDNESDAY...South southeast winds 25 to 30 knots, easing to
20 knots in the afternoon. Seas 7 to 8 feet. Wave Detail: South
southeast 7 feet at 6 seconds and south southwest 4 feet at
11 seconds. Frequent showers. 
.WEDNESDAY NIGHT...South southeast winds to 15 knots. Seas 7 to
8 feet, subsiding to 5 to 6 feet after midnight. Wave Detail:
South southeast 6 feet at 6 seconds and south southwest 3 feet at
11 seconds. Frequent showers. 
.THURSDAY...South southeast winds 10 to 15 knots. Seas 4 to
5 feet. Wave Detail: South southeast 5 feet at 6 seconds and
south southwest 3 feet at 11 seconds. Numerous showers, mainly in
the morning. 
.THURSDAY NIGHT...Southeast winds 10 to 15 knots. Seas 4 to
5 feet. Wave Detail: South southeast 5 feet at 6 seconds, north
northwest 3 feet at 10 seconds and south southwest 3 feet at
11 seconds. Scattered showers. 
.FRIDAY...Southeast winds 10 to 15 knots, backing to east 7 to
10 knots after midnight. Seas 4 to 5 feet. Wave Detail: Southeast
4 feet at 5 seconds, north northwest 3 feet at 9 seconds and
south southwest 3 feet at 11 seconds. Scattered showers through
the night, then isolated showers in the evening. Scattered
showers after midnight. 
.SATURDAY...East northeast winds 10 to 15 knots. Seas 4 to
5 feet. Wave Detail: East southeast 4 feet at 5 seconds and west
northwest 3 feet at 9 seconds. Isolated showers.  

PHZ116-300230-
Kaiwi Channel-
332 AM HST Tue Sep 29 2026

.TODAY...East southeast winds 10 to 15 knots. Seas 6 to 7 feet.
Wave Detail: East southeast 5 feet at 6 seconds and west
southwest 5 feet at 11 seconds. Isolated showers this afternoon. 
.TONIGHT...Southeast winds 15 to 20 knots. Seas 5 to 6 feet. Wave
Detail: Southeast 5 feet at 6 seconds and southwest 4 feet at
11 seconds. Scattered showers. 
.WEDNESDAY...South southeast winds 15 to 20 knots. Seas 5 to
7 feet. Wave Detail: South southeast 6 feet at 6 seconds and
south southwest 4 feet at 11 seconds. Scattered showers in the
morning, then numerous showers in the afternoon. 
.WEDNESDAY NIGHT...South southeast winds 10 to 15 knots. Seas
5 to 7 feet, subsiding to 4 to 5 feet after midnight. Wave
Detail: South southeast 5 feet at 6 seconds and south southwest
3 feet at 11 seconds. Numerous showers. 
.THURSDAY...Southeast winds 10 to 15 knots. Seas 4 to 5 feet.
Wave Detail: Southeast 5 feet at 6 seconds and south southwest
3 feet at 11 seconds. Scattered showers. 
.THURSDAY NIGHT...East southeast winds 10 to 15 knots. Seas 4 to
5 feet. Wave Detail: Southeast 4 feet at 5 seconds, north
northwest 3 feet at 10 seconds and south southwest 3 feet at
11 seconds. Scattered showers. 
.FRIDAY...East southeast winds 10 to 15 knots. Seas 4 to 5 feet.
Wave Detail: East southeast 4 feet at 5 seconds, north northwest
3 feet at 9 seconds and south southwest 3 feet at 11 seconds.
Isolated showers through the night. Scattered showers through the
day. 
.SATURDAY...East northeast winds 10 to 15 knots. Seas 4 to
5 feet. Wave Detail: East northeast 5 feet at 6 seconds.
Scattered showers.  

PHZ117-300230-
Maui County Windward Waters-
332 AM HST Tue Sep 29 2026

.TODAY...East southeast winds 15 to 20 knots. Seas 5 to 7 feet.
Wave Detail: Southeast 6 feet at 6 seconds and north northwest
3 feet at 12 seconds. Isolated showers this morning. 
.TONIGHT...East southeast winds 20 to 25 knots, easing to 15 to
20 knots after midnight. Seas 4 to 5 feet. Wave Detail: Southeast
5 feet at 5 seconds. Isolated showers after midnight. 
.WEDNESDAY...East southeast winds 15 to 20 knots. Seas 4 to
6 feet. Wave Detail: Southeast 5 feet at 6 seconds. Isolated
showers in the morning. Scattered showers in the afternoon. 
.WEDNESDAY NIGHT...East southeast winds to 15 knots. Seas 4 to
5 feet. Wave Detail: East southeast 5 feet at 6 seconds.
Scattered showers. 
.THURSDAY...East southeast winds to 15 knots. Seas 4 to 5 feet.
Wave Detail: Southeast 5 feet at 5 seconds. Scattered showers in
the morning. Isolated showers in the afternoon. 
.THURSDAY NIGHT...East southeast winds to 15 knots. Seas 4 to
5 feet. Wave Detail: East southeast 5 feet at 5 seconds and north
northwest 3 feet at 10 seconds. Isolated showers. 
.FRIDAY...East southeast winds 15 to 20 knots, becoming east
10 to 15 knots after midnight. Seas to 5 feet. Wave Detail: East
5 feet at 5 seconds and north 3 feet at 9 seconds. Isolated
showers through the night. Scattered showers through the day. 
.SATURDAY...East winds 10 to 15 knots. Seas 4 to 5 feet. Wave
Detail: East 4 feet at 5 seconds and west northwest 4 feet at
10 seconds. Scattered showers.  

PHZ118-300230-
Maui County Leeward Waters-
332 AM HST Tue Sep 29 2026

.TODAY...East southeast winds 15 to 20 knots. Seas 5 to 7 feet.
Wave Detail: Southeast 5 feet at 6 seconds and west southwest
5 feet at 11 seconds. Isolated showers. 
.TONIGHT...Southeast winds 15 to 20 knots. Seas 5 to 6 feet. Wave
Detail: South southeast 5 feet at 6 seconds and south southwest
4 feet at 11 seconds. Scattered showers in the evening, then
numerous showers after midnight. 
.WEDNESDAY...South southeast winds 15 to 20 knots. Seas 5 to
7 feet. Wave Detail: South southeast 5 feet at 6 seconds and
south southwest 4 feet at 11 seconds. Scattered showers. 
.WEDNESDAY NIGHT...Southeast winds to 15 knots. Seas 5 to 7 feet,
subsiding to 3 to 5 feet after midnight. Wave Detail: South
southeast 5 feet at 6 seconds and south southwest 3 feet at
11 seconds. Scattered showers in the evening, then numerous
showers after midnight. 
.THURSDAY...Southeast winds 10 to 15 knots. Seas 3 to 5 feet.
Wave Detail: South southeast 4 feet at 5 seconds and south
southwest 3 feet at 11 seconds. Scattered showers. 
.THURSDAY NIGHT...East southeast winds 10 to 15 knots. Seas 3 to
5 feet. Wave Detail: Southeast 4 feet at 5 seconds and south
southwest 3 feet at 11 seconds. Scattered showers. 
.FRIDAY...East winds 7 to 10 knots. Seas 3 to 4 feet. Wave
Detail: Southeast 4 feet at 5 seconds and south southwest 3 feet
at 11 seconds. Scattered showers in the morning. Isolated
showers. 
.SATURDAY...East northeast winds 7 to 10 knots. Seas 3 to 4 feet.
Wave Detail: East southeast 3 feet at 4 seconds. Isolated showers
in the morning. Isolated showers after midnight.  

PHZ119-300230-
Maalaea Bay-
332 AM HST Tue Sep 29 2026

.TODAY...North northeast winds to 20 knots. Seas to 3 feet. Wave
Detail: West southwest 3 feet at 11 seconds. 
.TONIGHT...North northeast winds to 20 knots. Seas to 3 feet in
the evening, then to 2 feet or less. 
.WEDNESDAY...North northeast winds to 15 knots, veering to south
in the afternoon. Seas to 2 feet or less. Isolated showers in the
afternoon. 
.WEDNESDAY NIGHT...North northeast winds to 15 knots. Seas to
2 feet or less. 
.THURSDAY...North northeast winds to 15 knots. Seas to 2 feet or
less. 
.THURSDAY NIGHT...North northeast winds to 20 knots, easing to
15 knots after midnight. Seas to 2 feet or less. 
.FRIDAY...North northeast winds to 15 knots, rising to 20 knots.
Seas to 2 feet or less. 
.SATURDAY...North northeast winds to 20 knots. Seas to 2 feet or
less.  

PHZ120-300230-
Pailolo Channel-
332 AM HST Tue Sep 29 2026

.TODAY...East winds 15 to 20 knots. Seas 4 to 6 feet. Wave
Detail: East 4 feet at 6 seconds and west southwest 4 feet at
11 seconds. 
.TONIGHT...East southeast winds 15 to 20 knots. Seas 3 to 5 feet.
Wave Detail: East southeast 3 feet at 5 seconds and southwest
3 feet at 11 seconds. Isolated showers in the evening. Scattered
showers after midnight. 
.WEDNESDAY...South southeast winds 10 to 15 knots. Seas 3 to
5 feet. Wave Detail: East southeast 4 feet at 6 seconds. Isolated
showers in the morning, then scattered showers in the afternoon. 
.WEDNESDAY NIGHT...Southeast winds 10 to 15 knots. Seas 3 to
5 feet. Wave Detail: Southeast 4 feet at 6 seconds. Scattered
showers. 
.THURSDAY...East winds 10 to 15 knots. Seas to 3 feet. Wave
Detail: East southeast 3 feet at 5 seconds. Scattered showers. 
.THURSDAY NIGHT...East winds 15 to 20 knots, becoming east
northeast 10 to 15 knots after midnight. Seas to 3 feet. Wave
Detail: East southeast 3 feet at 5 seconds. Isolated showers. 
.FRIDAY...East winds 10 to 15 knots, becoming east northeast
15 to 20 knots. Seas to 3 feet. Wave Detail: East 3 feet at
5 seconds. Isolated showers through the night. Scattered showers
through the day. 
.SATURDAY...East northeast winds 15 to 20 knots. Seas to 3 feet.
Wave Detail: East northeast 3 feet at 4 seconds. Scattered
showers.  

PHZ121-300230-
Alenuihaha Channel-
332 AM HST Tue Sep 29 2026

.TODAY...East northeast winds 15 to 20 knots. Seas 5 to 7 feet.
Wave Detail: East 5 feet at 6 seconds and west southwest 4 feet
at 11 seconds. Isolated showers this afternoon. 
.TONIGHT...East winds 15 to 20 knots. Seas 4 to 6 feet. Wave
Detail: Southeast 4 feet at 5 seconds and south southwest 4 feet
at 11 seconds. Scattered showers. 
.WEDNESDAY...Southeast winds 15 to 20 knots. Seas 4 to 6 feet.
Wave Detail: Southeast 5 feet at 5 seconds and south southwest
3 feet at 11 seconds. Scattered showers. 
.WEDNESDAY NIGHT...East southeast winds 10 to 15 knots. Seas 4 to
6 feet. Wave Detail: Southeast 5 feet at 6 seconds and south
southwest 3 feet at 11 seconds. Scattered showers. 
.THURSDAY...East winds 10 to 15 knots. Seas 4 to 5 feet. Wave
Detail: East 4 feet at 5 seconds and south southwest 3 feet at
11 seconds. Scattered showers in the morning. Isolated showers in
the afternoon. 
.THURSDAY NIGHT...East winds 10 to 15 knots. Seas 4 to 5 feet.
Wave Detail: East northeast 4 feet at 5 seconds and south
southwest 3 feet at 11 seconds. Scattered showers. 
.FRIDAY...East winds 10 to 15 knots, becoming east northeast
15 to 20 knots. Seas 4 to 5 feet. Wave Detail: East northeast
4 feet at 5 seconds and south southwest 3 feet at 11 seconds.
Isolated showers in the morning. Isolated showers through the
day. 
.SATURDAY...East northeast winds 15 to 20 knots. Seas 4 to
5 feet. Wave Detail: East northeast 5 feet at 6 seconds. Isolated
showers.  

PHZ122-300230-
Big Island Windward Waters-
332 AM HST Tue Sep 29 2026

.TODAY...East southeast winds 20 to 25 knots, easing to 15 to
20 knots this afternoon. Seas 3 to 5 feet. Wave Detail: Southeast
4 feet at 4 seconds, south southwest 3 feet at 11 seconds and
north northwest 3 feet at 12 seconds. Isolated showers this
morning. 
.TONIGHT...East southeast winds 20 to 25 knots, becoming
southeast 15 to 20 knots after midnight. Seas 3 to 4 feet. Wave
Detail: South southeast 3 feet at 3 seconds and south southwest
3 feet at 11 seconds. Isolated showers. 
.WEDNESDAY...Southeast winds 15 to 20 knots. Seas 3 to 5 feet.
Wave Detail: South southeast 4 feet at 4 seconds and south
southwest 3 feet at 11 seconds. Isolated showers in the
afternoon. 
.WEDNESDAY NIGHT...East southeast winds 10 to 15 knots. Seas 3 to
5 feet. Wave Detail: Southeast 4 feet at 4 seconds. 
.THURSDAY...East southeast winds 10 to 15 knots. Seas to 5 feet.
Wave Detail: East southeast 3 feet at 4 seconds. 
.THURSDAY NIGHT...East southeast winds 10 to 15 knots. Seas 4 to
5 feet. Wave Detail: East southeast 3 feet at 4 seconds. 
.FRIDAY...East southeast winds 15 to 20 knots, becoming east
10 to 15 knots. Seas 4 to 5 feet. Wave Detail: East northeast
3 feet at 4 seconds. Scattered showers through the day. 
.SATURDAY...East northeast winds 10 to 15 knots. Seas 4 to
5 feet. Wave Detail: North northeast 4 feet at 6 seconds.
Scattered showers.  

PHZ123-300230-
Big Island Leeward Waters-
332 AM HST Tue Sep 29 2026

.TODAY...West of the Big Island, winds variable less than
10 knots, becoming west northwest 10 to 15 knots this afternoon.
Near South Point, east winds 20 to 25 knots. Seas 4 to 6 feet.
Wave Detail: Southeast 5 feet at 5 seconds and southwest 4 feet
at 11 seconds. Scattered showers this morning. Isolated showers
this afternoon. 
.TONIGHT...West of the Big Island, north winds 10 to 15 knots,
rising to 15 to 20 knots after midnight. Near South Point, east
winds 15 to 20 knots. Seas 4 to 6 feet. Wave Detail: Southeast
4 feet at 5 seconds and south southwest 4 feet at 11 seconds.
Isolated showers in the evening. Scattered showers after
midnight. 
.WEDNESDAY...West of the Big Island, east southeast winds 15 to
20 knots, becoming south southwest 20 to 25 knots in the
afternoon. Near Kawaihae, winds variable less than 10 knots,
becoming northwest 7 to 10 knots in the afternoon. Seas 4 to
6 feet. Wave Detail: Southeast 4 feet at 5 seconds and south
southwest 3 feet at 11 seconds. Isolated showers. 
.WEDNESDAY NIGHT...North northeast winds 7 to 10 knots west of
the Big Island...East southeast to 15 knots near South Point.
Seas 4 to 6 feet. Wave Detail: Southeast 4 feet at 5 seconds and
south southwest 3 feet at 11 seconds. Scattered showers. 
.THURSDAY...Winds variable less than 10 knots west of the Big
Island...East southeast to 15 knots near South Point. Seas 3 to
5 feet. Wave Detail: Southeast 4 feet at 5 seconds, west
northwest 3 feet at 9 seconds and south southwest 3 feet at
11 seconds. Isolated showers. 
.THURSDAY NIGHT...West of the Big Island, west southwest winds
7 to 10 knots in the evening, becoming variable less than
10 knots. Near South Point, east winds to 15 knots. Seas 3 to
5 feet. Wave Detail: Southeast 4 feet at 5 seconds, west
northwest 3 feet at 9 seconds and south southwest 3 feet at
11 seconds. Isolated showers. 
.FRIDAY...West of the Big Island, north northwest winds 7 to
10 knots, becoming variable less than 10 knots. Near South Point,
east winds 15 to 20 knots. Seas 3 to 5 feet. Wave Detail: East
southeast 4 feet at 5 seconds and south southwest 3 feet at
11 seconds. Isolated showers in the morning. Isolated showers
through the day. 
.SATURDAY...West of the Big Island, winds variable less than
10 knots, becoming west northwest 7 to 10 knots in the afternoon
and evening, then becoming variable less than 10 knots after
midnight. Near South Point, east northeast winds 10 to 15 knots.
Seas 3 to 5 feet. Wave Detail: Northeast 4 feet at 6 seconds,
northwest 3 feet at 10 seconds and south southwest 3 feet at
11 seconds. Scattered showers in the evening. Isolated showers
after midnight.  

PHZ124-300230-
Big Island Southeast Waters-
332 AM HST Tue Sep 29 2026

.TODAY...East winds 15 to 20 knots. Seas 4 to 6 feet. Wave
Detail: Southwest 4 feet at 11 seconds and east southeast 3 feet
at 4 seconds. Scattered showers. 
.TONIGHT...East southeast winds 10 to 15 knots. Seas 3 to 4 feet.
Wave Detail: South southwest 3 feet at 11 seconds. Isolated
showers in the evening, then scattered showers after midnight. 
.WEDNESDAY...East southeast winds 10 to 15 knots. Seas to 4 feet.
Wave Detail: East southeast 3 feet at 4 seconds and south
southwest 3 feet at 11 seconds. Isolated showers in the morning.
Scattered showers in the afternoon. 
.WEDNESDAY NIGHT...East winds 10 to 15 knots. Seas 4 to 5 feet.
Wave Detail: East southeast 3 feet at 4 seconds and south
southwest 3 feet at 11 seconds. Scattered showers. 
.THURSDAY...East winds 10 to 15 knots. Seas 4 to 5 feet. Wave
Detail: East 3 feet at 4 seconds, west northwest 3 feet at
9 seconds and south southwest 3 feet at 11 seconds. Isolated
showers. 
.THURSDAY NIGHT...East winds 10 to 15 knots. Seas 4 to 5 feet.
Wave Detail: East 3 feet at 4 seconds and west northwest 3 feet
at 9 seconds. Isolated showers. 
.FRIDAY...East winds 10 to 15 knots. Seas 4 to 5 feet. Wave
Detail: East 3 feet at 4 seconds. Isolated showers in the
morning. Scattered showers through the day. 
.SATURDAY...East northeast winds to 15 knots, rising to 20 knots
after midnight. Seas 4 to 5 feet. Wave Detail: East northeast
5 feet at 5 seconds. Scattered showers in the morning, then
isolated showers in the afternoon. Scattered showers through the
day.
```

---

### 5. Daily Climate Summary — HNL

| Field | Value |
|---|---|
| **Resource ID** | cli_daily_climate_summary_HNL |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=HNL |
| **Collected** | 2026-09-29T03:14:10.749231-10:00 HST |

```text
307
CDHW40 PHFO 291245
CLIHNL

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
245 AM HST TUE SEP 29 2026

...................................

...THE HONOLULU CLIMATE SUMMARY FOR SEPTEMBER 28 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1940 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 YESTERDAY
  MAXIMUM         90    300 PM  91    1988  88      2       89
                                      1995
                                      1997
  MINIMUM         78   1128 PM  68    1945  75      3       78
  AVERAGE         84                        81      3       84

PRECIPITATION (IN)
  YESTERDAY        0.00          0.79 1948   0.03  -0.03     0.00
  MONTH TO DATE    0.32                      0.83  -0.51     0.71
  SINCE SEP 1      0.32                      0.83  -0.51     0.71
  SINCE JAN 1     22.35                     10.42  11.93     9.59

DEGREE DAYS
 HEATING
  YESTERDAY        0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  YESTERDAY       19                        16      3       19
  MONTH TO DATE  510                       465     45      497
  SINCE SEP 1    510                       465     45      497
  SINCE JAN 1   3720                      3542    178     3982
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    24   HIGHEST WIND DIRECTION     E (70)
  HIGHEST GUST SPEED    33   HIGHEST GUST DIRECTION     E (80)
  AVERAGE WIND SPEED    13.6

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.3

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED YESTERDAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    74           600 AM
 LOWEST     48           300 PM
 AVERAGE    61

..........................................................

THE HONOLULU CLIMATE NORMALS FOR TODAY
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   88        93      1993
                                             2020
 MINIMUM TEMPERATURE (F)   75        66      1975

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   622 AM HST   SUNSET   621 PM HST
SEPTEMBER 30 2026.....SUNRISE   623 AM HST   SUNSET   620 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 6. Daily Climate Summary — ITO

| Field | Value |
|---|---|
| **Resource ID** | cli_daily_climate_summary_ITO |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=ITO |
| **Collected** | 2026-09-29T03:16:41.387126-10:00 HST |

```text
023
CDHW43 PHFO 291245
CLIITO

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
245 AM HST TUE SEP 29 2026

...................................

...THE HILO/GEN.LYMAN FLD CLIMATE SUMMARY FOR SEPTEMBER 28 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1949 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 YESTERDAY
  MAXIMUM         85   1230 PM  90    2019  83      2       84
  MINIMUM         67    631 AM  64    1956  70     -3       68
  AVERAGE         76                        76      0       76

PRECIPITATION (IN)
  YESTERDAY        0.00          1.78 1986   0.30  -0.30     0.01
  MONTH TO DATE   16.18                      8.12   8.06     2.74
  SINCE SEP 1     16.18                      8.12   8.06     2.74
  SINCE JAN 1    124.42                     83.11  41.31    38.12

DEGREE DAYS
 HEATING
  YESTERDAY        0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  YESTERDAY       11                        11      0       11
  MONTH TO DATE  365                       334     31      353
  SINCE SEP 1    365                       334     31      353
  SINCE JAN 1   2794                      2445    349     2854
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    15   HIGHEST WIND DIRECTION     E (110)
  HIGHEST GUST SPEED    25   HIGHEST GUST DIRECTION     E (80)
  AVERAGE WIND SPEED     8.7

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.1

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED YESTERDAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    85           900 PM
 LOWEST     57           800 AM
 AVERAGE    71

..........................................................

THE HILO/GEN.LYMAN FLD CLIMATE NORMALS FOR TODAY
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   83        89      1974
                                             2014
                                             2019
 MINIMUM TEMPERATURE (F)   70        64      1955

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   611 AM HST   SUNSET   610 PM HST
SEPTEMBER 30 2026.....SUNRISE   611 AM HST   SUNSET   609 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 7. Daily Climate Summary — LIH

| Field | Value |
|---|---|
| **Resource ID** | cli_daily_climate_summary_LIH |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=LIH |
| **Collected** | 2026-09-29T03:14:56.338513-10:00 HST |

```text
024
CDHW41 PHFO 291245
CLILIH

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
245 AM HST TUE SEP 29 2026

...................................

...THE LIHUE CLIMATE SUMMARY FOR SEPTEMBER 28 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1950 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 YESTERDAY
  MAXIMUM         85   1134 AM  89    1981  85      0       85
                                      2019
  MINIMUM         77    508 AM  66    1958  75      2       78
                                      1970
  AVERAGE         81                        80      1       82

PRECIPITATION (IN)
  YESTERDAY        T             1.31 1994   0.08  -0.08     0.01
  MONTH TO DATE    3.13                      2.01   1.12     3.50
  SINCE SEP 1      3.13                      2.01   1.12     3.50
  SINCE JAN 1     42.92                     24.11  18.81    14.96

DEGREE DAYS
 HEATING
  YESTERDAY        0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  YESTERDAY       16                        15      1       17
  MONTH TO DATE  424                       420      4      433
  SINCE SEP 1    424                       420      4      433
  SINCE JAN 1   3127                      3054     73     3371
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    22   HIGHEST WIND DIRECTION     E (90)
  HIGHEST GUST SPEED    29   HIGHEST GUST DIRECTION     E (80)
  AVERAGE WIND SPEED    17.1

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.5

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED YESTERDAY.
  LIGHT RAIN
  FOG
  HAZE

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    85           400 AM
 LOWEST     70           400 PM
 AVERAGE    78

..........................................................

THE LIHUE CLIMATE NORMALS FOR TODAY
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   85        88      1981
                                             2014
                                             2017
 MINIMUM TEMPERATURE (F)   75        65      1952

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   628 AM HST   SUNSET   627 PM HST
SEPTEMBER 30 2026.....SUNRISE   629 AM HST   SUNSET   626 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 8. Daily Climate Summary — OGG

| Field | Value |
|---|---|
| **Resource ID** | cli_daily_climate_summary_OGG |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=OGG |
| **Collected** | 2026-09-29T03:15:56.548164-10:00 HST |

```text
025
CDHW42 PHFO 291245
CLIOGG

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
245 AM HST TUE SEP 29 2026

...................................

...THE KAHULUI/MAUI CLIMATE SUMMARY FOR SEPTEMBER 28 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1954 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 YESTERDAY
  MAXIMUM         93R  1223 PM  93    2019  90      3       90
  MINIMUM         65    555 AM  63    1965  71     -6       76
                                      2010
  AVERAGE         79                        80     -1       83

PRECIPITATION (IN)
  YESTERDAY        0.00          0.09 1980   0.01  -0.01     0.00
  MONTH TO DATE    0.60                      0.42   0.18     0.04
  SINCE SEP 1      0.60                      0.42   0.18     0.04
  SINCE JAN 1     30.28                     10.74  19.54     6.61

DEGREE DAYS
 HEATING
  YESTERDAY        0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  YESTERDAY       14                        15     -1       18
  MONTH TO DATE  454                       442     12      443
  SINCE SEP 1    454                       442     12      443
  SINCE JAN 1   3238                      3289    -51     3298
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    26   HIGHEST WIND DIRECTION    NE (60)
  HIGHEST GUST SPEED    39   HIGHEST GUST DIRECTION    NE (50)
  AVERAGE WIND SPEED    10.6

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.1

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED YESTERDAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    84           600 AM
 LOWEST     38           200 PM
 AVERAGE    61

..........................................................

THE KAHULUI/MAUI CLIMATE NORMALS FOR TODAY
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   90        93      1996
 MINIMUM TEMPERATURE (F)   71        63      1974
                                             1975
                                             2002

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   616 AM HST   SUNSET   615 PM HST
SEPTEMBER 30 2026.....SUNRISE   617 AM HST   SUNSET   614 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 9. Hawaii Rainfall Summary direct product

| Field | Value |
|---|---|
| **Resource ID** | hfo_rra_direct |
| **Official source** | https://forecast.weather.gov/product.php?issuedby=HFO&product=RRA&site=hfo |
| **Collected** | 2026-09-29T06:30:46.833172-10:00 HST |

```text
490
SRHW80 PHFO 291546
RRAHFO

Hawaii Rainfall Summary
National Weather Service Honolulu HI
545 AM HST Tue Sep 29 2026

:
.B HFO  0929 H  DH05 /DRH-03/PPT/DRH-06/PPQ/DRH-12/PPK/DRH-24/PPD
:
:Automated rain gage reports from around the State of Hawaii.
:These are provisional reports that have not been quality
:controlled.
:
:T=Trace Rainfall, M=Missing Data
:
:Precipitation totals ending  5 AM HST
:
:Island of Kauai                                   Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward/Mauka Sites
MKAH1 : Makaha Ridge (RAWS)         :    0.00  /  0.00  /  0.00  /  0.00
PLRH1 : Puu Lua (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
WKRH1 : Waiakoali (USGS)            :    0.00  /  0.00  /  0.00  /  0.00
KLOH1 : Kilohana (USGS)             :    0.00  /  0.00  /  0.00  /  0.02
MCRH1 : Mohihi Crossing (USGS)      :    0.00  /  0.00  /  0.00  /  0.01
WLGH1 : Waialae (USGS)              :    0.00  /  0.00  /  0.01  /  0.03
LLMH1 : Lower Limahuli (UHM)        :    0.00  /  0.00  /  0.00  /  0.04
WNHH1 : Wainiha (12010)             :    0.00  /  0.00  /  0.00  /  0.01
WIPH1 : Waipa (UHM)                 :    0.00  /  0.00  /  0.00  /  0.13
HNIH1 : Hanalei (12009)             :    0.00  /  0.00  /  0.00  /  0.15
WLLH1 : Mount Waialeale (USGS)      :      M   /    M   /    M   /    M
PRIH1 : Princeville Airport (12011) :    0.00  /  0.00  /  0.01  /  0.13
CMGH1 : Common Ground (UHM)         :    0.00  /  0.00  /  0.00  /  0.34
HLIH1 : Hanalei (RAWS)              :    0.00  /  0.00  /  0.00  /  0.39
MLDH1 : Moloaa Dairy (RAWS)         :    0.00  /  0.00  /  0.00  /  0.00
ANHH1 : Anahola (12001)             :    0.00  /  0.00  /  0.00  /  0.18
KPIH1 : Kapahi (12003)              :    0.00  /  0.00  /  0.00  /  0.09
WLDH1 : N Wailua Ditch (USGS)       :    0.01  /  0.04  /  0.08  /  0.59
WUHH1 : Wailua (12005)              :    0.00  /  0.00  /  0.00  /  0.07
WIRH1 : Waiahi Rain Gage (USGS)     :    0.00  /  0.00  /  0.00  /  0.19
LIHH1 : Lihue Var. Stn. (12006)     :    0.00  /  0.00  /  0.00  /  0.09
HNMH1 : Hanamaulu (UHM)             :    0.00  /  0.00  /  0.00  /  0.16
HLI   : Lihue Airport (ASOS)        :    0.00  /  0.00  /  0.00  /  0.00
:       Leeward Sites
OMAH1 : Omao (12004)                :    0.00  /  0.00  /  0.00  /  0.01
LNTH1 : Lawai NTBG (UHM)            :    0.00  /  0.00  /  0.00  /  0.00
KHEH1 : Kalaheo (12008)             :    0.00  /  0.00  /  0.00  /  0.02
PAKH1 : Port Allen (HSOIS)          :    0.00  /  0.00  /  0.00  /  0.00
HNPH1 : Hanapepe (12002)            :    0.00  /  0.00  /  0.00  /  0.00
POPH1 : Puu Opae (RAWS)             :    0.00  /  0.00  /  0.00  /  0.00
WHGH1 : Waimea Heights (RAWS)       :    0.00  /  0.00  /  0.00  /  0.00
WMTH1 : Waimea Tank (12007)         :    0.00  /  0.00  /  0.00  /  0.00
MNRH1 : Mana (RAWS)                 :    0.00  /  0.00  /  0.00  /  0.00
:
:Island of Oahu                                    Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward/Mauka Sites
KAHH1 : Kahuku (13027)              :    0.00  /  0.00  /  0.00  /  0.00
KTAH1 : Kahuku Training Area (RAWS) :    0.00  /  0.00  /  0.00  /  0.00
KFWH1 : Kii (RAWS)                  :    0.00  /  0.00  /  0.00  /  0.00
PUNH1 : Punaluu Pump (13013)        :    0.00  /  0.00  /  0.00  /  0.01
PNSH1 : Punaluu Stream (USGS)       :    0.00  /  0.00  /  0.00  /  0.13
KNRH1 : Kahana (USGS)               :    0.00  /  0.00  /  0.00  /  0.05
HAKH1 : Hakipuu Mauka (13004)       :    0.00  /  0.00  /  0.00  /  0.03
WPPH1 : Waihee Pump (13002)         :    0.00  /  0.00  /  0.00  /  0.09
WHSH1 : Waiahole (USGS)             :    0.00  /  0.00  /  0.00  /  0.00
OFRH1 : Oahu Forest NWR (USFWS)     :    0.00  /  0.00  /  0.00  /  0.01
AHUH1 : Ahuimanu Loop (13005)       :    0.00  /  0.00  /  0.00  /  0.02
HRRH1 : Heeia NERR (NOAA/NOS)       :    0.00  /  0.00  /  0.00  /  0.01
LULH1 : Luluku (13016)              :    0.00  /  0.00  /  0.00  /  0.00
NRSH1 : Nuuanu Res No. 1 (UHM)      :    0.00  /  0.00  /  0.00  /  0.00
KWIH1 : Kalawahine (UHM)            :    0.00  /  0.00  /  0.00  /  0.01
LYOH1 : Lyon (UHM)                  :    0.00  /  0.00  /  0.00  /  0.00
MNLH1 : Manoa Lyon Arboretum (13023):    0.00  /  0.00  /  0.00  /  0.00
STVH1 : St. Stephens (13006)        :    0.00  /  0.00  /  0.00  /  0.01
MAUH1 : Maunawili (13008)           :      M   /    M   /    M   /    M
OFSH1 : Olomana Fire Station (13009):    0.00  /  0.00  /  0.00  /  0.02
WMLH1 : Waimanalo (13011)           :    0.00  /  0.00  /  0.00  /  0.00
BELH1 : Bellows AFS (HSOIS)         :    0.00  /  0.00  /  0.00  /  0.00
KMHH1 : Kamehame (13012)            :    0.00  /  0.00  /  0.00  /  0.00
HAJH1 : Hawaii Kai Golf Crse (13015):    0.00  /  0.00  /  0.00  /  0.00
:       Leeward/Central Sites
KUXH1 : Kaluanui (UHM)              :    0.00  /  0.00  /  0.00  /  0.00
NIUH1 : Niu Valley (13001)          :    0.00  /  0.00  /  0.00  /  0.00
PFSH1 : Palolo Fire Station (13010) :    0.00  /  0.00  /  0.00  /  0.00
HNL   : Honolulu Airport (ASOS)             See note at bottom  :
MOAH1 : Moanalua (13003)            :    0.00  /  0.00  /  0.00  /  0.01
MOGH1 : Moanalua RG (USGS)          :    0.00  /  0.00  /  0.00  /  0.07
TNLH1 : Tunnel RG (USGS)            :    0.00  /  0.00  /  0.00  /  0.10
PACH1 : Palisades (13020)           :    0.00  /  0.00  /  0.00  /  0.00
WAWH1 : Waiawa C.F. (13025)         :    0.00  /  0.00  /  0.00  /  0.01
MITH1 : Mililani (13022)            :    0.00  /  0.00  /  0.00  /  0.00
SCBH1 : Schofield Barracks (RAWS)   :    0.00  /  0.00  /  0.00  /  0.00
SCEH1 : Schofield East (RAWS)       :    0.00  /  0.00  /  0.00  /  0.00
WAFH1 : Wheeler Airfield            :    0.00  /  0.00  /  0.00  /  0.00
POAH1 : Poamoho (13018)             :    0.00  /  0.00  /  0.00  /  0.00
KRGH1 : Kalahee Ridge (UHM)         :    0.00  /  0.00  /  0.00  /  0.00
KMRH1 : Kamananui Stream (USGS)     :    0.00  /  0.00  /  0.00  /  0.01
PPRH1 : Pupukea Road (USGS)         :    0.00  /  0.00  /  0.00  /  0.01
PMHH1 : Poamoho RG 1 (USGS)         :    0.00  /  0.00  /  0.00  /  0.04
DLGH1 : Dillingham (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
AALH1 : Kaala (UHM)                 :    0.00  /  0.01  /  0.01  /  0.02
PECH1 : Waipio (13019)              :    0.00  /  0.00  /  0.00  /  0.00
KUNH1 : Kunia Substation (13021)    :    0.00  /  0.00  /  0.00  /  0.00
HOFH1 : Honouliuli (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
PTWH1 : Ewa Beach USGS (13024)      :    0.00  /  0.00  /  0.00  /  0.00
HJR   : Kalaeloa Airport (ASOS)             See note at bottom  :
PLHH1 : Palehua (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
LUAH1 : Lualualei (13017)           :    0.00  /  0.00  /  0.00  /  0.00
WNVH1 : Waianae Valley (RAWS)       :    0.00  /  0.00  /  0.00  /  0.00
WBHH1 : Waianae Boat Harbor (HSOIS) :    0.00  /  0.00  /  0.00  /  0.00
WAIH1 : Waianae (13014)             :      M   /    M   /    M   /    M
MKHH1 : Makaha Stream (USGS)        :    0.00  /  0.00  /  0.00  /  0.00
MKRH1 : Makua Range (RAWS)          :    0.00  /  0.00  /  0.00  /  0.00
KKRH1 : Kuaokala (RAWS)             :    0.00  /  0.00  /  0.00  /  0.00
:
:Island of Molokai                                 Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
KOPH1 : Keopukaloa (UHM)            :    0.00  /  0.00  /  0.00  /  0.00
HOMH1 : Honolimaloo (UHM)           :    0.00  /  0.00  /  0.00  /  0.00
KMLH1 : Kamalo (14013)              :    0.00  /  0.00  /  0.00  /  0.00
MKPH1 : Makapulapai (RAWS)          :    0.00  /  0.00  /  0.00  /  0.00
PAFH1 : Puu Alii (RAWS)             :    0.00  /  0.00  /  0.00  /  0.00
MLKH1 : Molokai 1 (RAWS)            :      M   /    M   /    M   /    M
KACH1 : Kaunakakai Mauka (14004)    :    0.00  /  0.00  /  0.00  /  0.00
HMK   : Molokai Airport (ASOS)      :    0.00  /  0.00  /  0.00  /  0.00
:
:Island of Lanai                                   Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
LANH1 : Lanai City (14012)          :    0.00  /  0.00  /  0.00  /  0.00
HNY   : Lanai Airport (ASOS)        :    0.00  /  0.00  /  0.00  /  0.00
LNIH1 : Lanai 1 (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
:
:Island of Kahoolawe                               Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
KAOH1 : Kaneloa (RAWS)              :      M   /    M   /    M   /    M
:
:Island of Maui                                    Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward Sites
HNAH1 : Hana Airport (HSOIS)        :      M   /    M   /    M   /    M
WWKH1 : West Wailuaiki (USGS)       :    0.00  /  0.00  /  0.00  /  0.01
EBYH1 : EMI Baseyard (UHM)          :    0.00  /  0.00  /  0.00  /  0.00
AIKH1 : Haiku (14001)               :    0.00  /  0.00  /  0.00  /  0.00
HOG   : Kahului Airport (ASOS)      :    0.00  /  0.00  /  0.00  /  0.00
WUKH1 : Wailuku (14007)             :    0.00  /  0.00  /  0.00  /  0.00
KHKH1 : Kahakuloa (14002)           :    0.00  /  0.00  /  0.00  /  0.00
PKKH1 : Puu Kukui (USGS)            :    0.00  /  0.00  /  0.00  /  0.00
:       Leeward/Upcountry Sites
NKUH1 : Na Kula (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
KPNH1 : Kepuni (USGS)               :    0.00  /  0.00  /  0.00  /  0.00
PILH1 : Piiholo (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
WKTH1 : Waikamoi Treeline (UHM)     :    0.00  /  0.00  /  0.00  /  0.00
PUKH1 : Pukalani (14006)            :    0.00  /  0.00  /  0.00  /  0.00
KBSH1 : Kula Branch Station (14008) :      M   /    M   /    M   /    M
KLGH1 : Kula Ag (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
PHQH1 : Park HQ (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
NNEH1 : Nene Nest (UHM)             :    0.00  /  0.00  /  0.00  /  0.00
SUMH1 : Summit (UHM)                :    0.00  /  0.00  /  0.00  /  0.00
KLFH1 : Kula 1 (RAWS)               :    0.00  /  0.00  /  0.00  /  0.00
KKNH1 : Kahikinui 1 (RAWS)          :    0.00  /  0.00  /  0.00  /  0.00
KMEH1 : Kamehamenui 1 (RAWS)        :    0.00  /  0.00  /  0.00  /  0.00
KKEH1 : Keokea (UHM)                :    0.00  /  0.00  /  0.00  /  0.00
ULUH1 : Ulupalakua (14003)          :    0.00  /  0.00  /  0.00  /  0.00
LPOH1 : Lipoa (UHM)                 :    0.00  /  0.00  /  0.00  /  0.00
KHIH1 : Kihei #2 (14009)            :      M   /    M   /    M   /  0.00
KPDH1 : Kealia Pond (USFWS)         :    0.00  /  0.00  /  0.00  /  0.00
WCCH1 : Waikapu Country Club (14005):    0.00  /  0.00  /  0.00  /  0.00
HULH1 : Hanaula (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
OLUH1 : Olowalu (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
LAHH1 : Lahainaluna (14011)         :    0.00  /  0.00  /  0.00  /  0.00
LWTH1 : Lahaina WTP (UHM)           :    0.00  /  0.00  /  0.00  /  0.00
HOOH1 : Honolua (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
:
:Island of Hawaii                                  Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward Sites
UPLH1 : Upolu Airport (HSOIS)       :    0.00  /  0.00  /  0.00  /  0.00
KMMH1 : Kaluamakani (UHM)           :    0.00  /  0.00  /  0.00  /  0.00
KWSH1 : Kawainui Stream (USGS)      :    0.00  /  0.00  /  0.00  /  0.00
KUUH1 : Kamuela Upper (15002)       :    0.00  /  0.00  /  0.00  /  0.00
KMUH1 : Kamuela (15005)             :    0.00  /  0.00  /  0.00  /  0.00
HNKH1 : Honokaa (15010)             :    0.00  /  0.00  /  0.00  /  0.00
PMLH1 : Puu Mali (RAWS)             :    0.00  /  0.00  /  0.00  /  0.00
WPNH1 : Waipunalei (UHM)            :      M   /    M   /    M   /  0.00
KNKH1 : Kanakaleonui (UHM)          :    0.00  /  0.00  /  0.00  /  0.00
LPHH1 : Laupahoehoe PD (15001)      :    0.00  /  0.00  /  0.00  /  0.00
LAUH1 : Laupahoehoe (UHM)           :    0.00  /  0.00  /  0.00  /  0.00
SPNH1 : Spencer (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
HKUH1 : Hakalau (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
KLXH1 : Kulaimano (UHM)             :    0.00  /  0.00  /  0.00  /  0.00
NLIH1 : Honolii Stream (USGS)       :    0.00  /  0.00  /  0.00  /  0.01
SDQH1 : Saddle Quarry (USGS)        :    0.00  /  0.00  /  0.00  /  0.00
PIOH1 : Piihonua (UHM)              :    0.00  /  0.00  /  0.00  /  0.00
PIIH1 : Piihonua (15016)            :    0.00  /  0.00  /  0.00  /  0.00
IPIH1 : IPIF (UHM)                  :    0.00  /  0.00  /  0.00  /  0.00
WKAH1 : Waiakea Uka (15017)         :    0.00  /  0.00  /  0.00  /  0.00
WEXH1 : Waiakea Exp Stn (NOAA/CRN)  :    0.00  /  0.00  /  0.00  /  0.00
HTO   : Hilo Airport (ASOS)         :    0.00  /  0.00  /  0.00  /  0.00
PHAH1 : Pahoa (15015)               :    0.00  /  0.00  /  0.00  /  0.00
PAOH1 : Pahoa (UHM)                 :    0.00  /  0.00  /  0.00  /  0.00
MTVH1 : Mountain View (15014)       :    0.00  /  0.00  /  0.00  /  0.00
GLNH1 : Glenwood (15013)            :    0.00  /  0.00  /  0.00  /  0.00
:       Leeward Sites
MOBH1 : Mauna Loa Ob Stn (NOAA/CRN) :    0.00  /  0.00  /  0.00  /  0.00
NHKH1 : Nahuku (UHM)                :    0.00  /  0.00  /  0.00  /  0.00
KKUH1 : Keaumo (RAWS)               :    0.00  /  0.00  /  0.00  /  0.00
KMOH1 : Kealakomo (RAWS)            :    0.00  /  0.00  /  0.00  /  0.00
PLIH1 : Pali 2 (RAWS)               :    0.00  /  0.00  /  0.00  /  0.00
KPRH1 : Kapapala (RAWS)             :    0.00  /  0.00  /  0.00  /  0.00
KAYH1 : Kapapala Ranch (15003)      :    0.00  /  0.01  /  0.01  /  0.01
PPLH1 : Pahala (15004)              :    0.00  /  0.00  /  0.00  /  0.00
KIOH1 : Kaiholena (UHM)             :      M   /    M   /    M   /    M
NENH1 : Nene Cabin (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
SOPH1 : South Point (HSOIS)         :    0.00  /  0.00  /  0.00  /  0.00
LKHH1 : Lower Kahuku (RAWS)         :    0.00  /  0.00  /  0.00  /  0.00
KRCH1 : Kahuku Ranch (RAWS)         :    0.00  /  0.00  /  0.00  /  0.00
KOMH1 : Kona Hema (UHM)             :    0.00  /  0.00  /  0.00  /  0.00
PHRH1 : Puho CS (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
HAUH1 : Honaunau (15007)            :    0.00  /  0.00  /  0.00  /  0.00
KLEH1 : Kealakekua (15008)          :    0.00  /  0.00  /  0.00  /  0.00
WIHH1 : Waiaha Stream (15009)       :    0.00  /  0.00  /  0.00  /  0.00
KOUH1 : Keahuolu (UHM)              :    0.00  /  0.00  /  0.00  /  0.00
KHOH1 : Kaloko-Honokohau (RAWS)     :    0.00  /  0.00  /  0.00  /  0.00
HKO   : Kona Intl Airport (ASOS)    :    0.00  /  0.00  /  0.00  /  0.00
PLMH1 : Palamanui (UHM)             :    0.00  /  0.00  /  0.00  /  0.00
KIRH1 : Kiholo RG (USGS)            :    0.00  /  0.00  /  0.00  /  0.00
KPLH1 : Kaupulehu (RAWS)            :    0.00  /  0.00  /  0.00  /  0.00
PULH1 : Puuanahulu (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
MMLH1 : Mamalahoa (UHM)             :    0.00  /  0.00  /  0.00  /  0.00
PWWH1 : Puu Waawaa (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
PWAH1 : Puu Waawaa (UHM)            :    0.00  /  0.00  /  0.00  /  0.00
KIUH1 : Kaiaulu Puu Waawaa (UHM)    :    0.00  /  0.00  /  0.00  /  0.00
PKAH1 : Pohakuloa Kipuka Alala RAWS :    0.00  /  0.00  /  0.00  /  0.00
PTRH1 : Pohakuloa Range 17 (RAWS)   :    0.00  /  0.00  /  0.00  /  0.00
PKWH1 : Pohakuloa West (RAWS)       :    0.00  /  0.00  /  0.00  /  0.00
PKMH1 : Pohakuloa Keamuku (RAWS)    :    0.00  /  0.00  /  0.00  /  0.00
AHMH1 : Ahumoa (RAWS)               :    0.00  /  0.00  /  0.00  /  0.00
WHIH1 : Waikii (15011)              :    0.00  /  0.00  /  0.00  /  0.00
LLAH1 : Lalamilo (UHM)              :    0.00  /  0.00  /  0.00  /  0.00
WKVH1 : Waikoloa (RAWS)             :    0.00  /  0.00  /  0.00  /  0.00
PERH1 : Puhe CS (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
KHRH1 : Kohala Ranch (RAWS)         :    0.00  /  0.00  /  0.00  /  0.00
KASH1 : Kahua Ranch (15006)         :    0.00  /  0.00  /  0.00  /  0.00
KEHH1 : Kehena (UHM)                :    0.01  /  0.01  /  0.01  /  0.01
PLAH1 : Puuloa (UHM)                :    0.00  /  0.00  /  0.00  /  0.00
.END

Service Note
Due to software decoder issues, rainfall totals for Honolulu Airport (PHNL)
and Kalaeloa Airport (PHJR) are temporarily unavailable.
Daily totals for both sites are available in the CF6 product on the web at
https://www.weather.gov/wrh/Climate?wfo=hfo
Select the Observed Weather tab and choose the Preliminary Monthly Climate Data
(CF6) product.
We apologize for the inconvenience and hope to have this issue resolved soon.

$$
```

---

### 10. HFO statewide surf observations direct page

| Field | Value |
|---|---|
| **Resource ID** | hfo_surf_reports_direct |
| **Official source** | https://www.weather.gov/hfo/surfreports |
| **Collected** | 2026-09-29T06:22:49.857082-10:00 HST |

```text
                        
325
SXHW80 PHFO 290115
OMRHFO

SURF OBSERVATIONS
NATIONAL WEATHER SERVICE HONOLULU HI
315 PM HST MON SEP 28 2026

FULL FACE SURF OBSERVATIONS ARE TAKEN BY COUNTY LIFE GUARDS AND
COOPERATIVE OBSERVERS AND RELAYED TO THE NATIONAL WEATHER SERVICE
FOR DISSEMINATION. THESE OBSERVATIONS ARE NOT QUALITY CONTROLLED.

HIZ003-004-029>031-290100-
KAUAI-

LOCATION        TIME   SURF HEIGHT DIR   PER                  REMARKS
KEE
HAENA        1230 PM           4-8  NE    10
HANALEI      1230 PM           3-5 NNE    10
ANAHOLA
KEALIA
LYDGATE
POIPU
SALT POND
KEKAHA
$$

HIZ006-007-009>011-032>036-290100-
OAHU-

LOCATION        TIME   SURF HEIGHT DIR PER         WIND      REMARKS
DIAMOND HEAD
SUNSET
WAIKIKI       123 PM           3-4             NE 15-20       CANOES
SANDY BEACH   123 PM           4-6             NE 20-25  SHORE BREAK
MAKAPUU       123 PM           3-5             NE 15-25
EHUKAI        123 PM           3-4             NE 10-15
MAKAHA        123 PM           2-3             NE 20-25
$$

HIZ015>018-022-045>050-290100-
MAUI-MOLOKAI-LANAI-KAHOOLAWE-

LOCATION        TIME   SURF HEIGHT   DIR         WIND      REMARKS
KANAHA        135 PM           2-3            E 15-25  PARTLY CLDY
BALDWIN SHOR  137 PM           2-4           NE 15-30 MOSTLY SUNNY
BALDWIN OUTE  137 PM           6-8           NE 15-30 MOSTLY SUNNY
HOOKIPA       151 PM          8-10        TRADE 15-20        SUNNY
KAMAOLE I     149 PM           2-4           VRB 5-10  PARTLY CLDY
KAMAOLE III   150 PM           2-4             S 5-10        SUNNY
HANAKAOO      153 PM           2-3     S        S 5-1  PARTLY CLDY
FLEMING
$$

HIZ023-026>028-051>054-290100-
BIG ISLAND OF HAWAII-

LOCATION        TIME   SURF HEIGHT   DIR         WIND      REMARKS
RICHARDSONS   127 PM           3-4            NE 5-10  PARTLY CLDY
HONOLII       129 PM           2-3           SE 10-20        SUNNY
PUNALU`U
ISAAC HALE    130 PM    4-5 CHOPPY           L/V 5-10        SUNNY
HAPUNA        131 PM           3-5            L/V 0-5        SUNNY
KAHALUU       132 PM           3-4           NW 10-15        SUNNY
MAGIC SANDS   133 PM    4-5 OCNL 6           NW 10-15 MOSTLY SUNNY
KUA BAY       134 PM           1-3               W 10 MOSTLY SUNNY
$$

LEGEND
   SURF HEIGHT              - Reported in feet
   WIND AND SWELL DIRECTION - Reported in 16 pt compass
   PERIOD /PER/             - Reported in seconds
   VISIBILITY /VIS/         - Reported in statute miles
   CLARITY                  - Water clarity
   TIME                     - Hawaiian Standard Time
   WIND SPEED               - Reported in miles per hour
   + /IN SURF HEIGHT/       - Occasionally higher sets
   0 /IN SURF HEIGHT/       - Flat

$$
```

---

### 11. High Seas Forecast N. Pacific

| Field | Value |
|---|---|
| **Resource ID** | hsf_high_seas_npac |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=HSF&issuedby=NP |
| **Collected** | 2026-09-29T05:13:18.281091-10:00 HST |

```text
676
FZPN40 PHFO 291501
HSFNP

HIGH SEAS FORECAST
NATIONAL WEATHER SERVICE HONOLULU HI
1700 UTC TUE SEP 29 2026

SUPERSEDED BY NEXT ISSUANCE IN 6 HOURS

SEAS GIVEN AS SIGNIFICANT WAVE HEIGHT...WHICH IS THE AVERAGE HEIGHT
OF THE HIGHEST 1/3 OF THE WAVES. INDIVIDUAL WAVES MAY BE MORE THAN
TWICE THE SIGNIFICANT WAVE HEIGHT.

THIS HIGH SEAS FORECAST USES 1-MINUTE AVERAGE WINDS WHICH MAY BE
HIGHER THAN 10-MINUTE AVERAGE WINDS.

SECURITE

NORTH PACIFIC EQUATOR TO 30N BETWEEN 140W AND 180W

SYNOPSIS VALID 1200 UTC SEP 29 2026.
24 HOUR FORECAST VALID 1200 UTC SEP 30 2026.
48 HOUR FORECAST VALID 1200 UTC OCT 01 2026.

.WARNINGS.

...HURRICANE WARNING...
.HURRICANE NOLO NEAR 20.5N 164.2W 964 MB AT 1500 UTC SEP 29
MOVING N OR 355 DEG AT 8 KT. MAXIMUM SUSTAINED WINDS 95 KT GUSTS
115 KT. TROPICAL STORM FORCE WINDS WITHIN 100 NM NW AND SE
QUADRANTS...120 NM NE QUADRANT AND 80 NM SW QUADRANT. SEAS 4 M
OR GREATER WITHIN 270 NM W SEMICIRCLE...240 NM NE QUADRANT AND
210 NM SE QUADRANT WITH SEAS TO 11 M. SEAS 2.5 TO 3.5 M ELSEWHERE
FROM 13N TO 27N E OF 178W. WINDS 20 TO 30 KT ELSEWHERE FROM 18N TO
24N BETWEEN 159W AND 167W. SCATTERED MODERATE TO STRONG TSTMS
WITHIN 90 NM OF CENTER.
.24 HOUR FORECAST HURRICANE NOLO NEAR 22.3N 164.5W. MAXIMUM
SUSTAINED WINDS 70 KT GUSTS 85 KT. TROPICAL STORM FORCE WINDS
WITHIN 120 NM NE QUADRANT...90 NM SE QUADRANT...80 NM SW
QUADRANT...AND 100 NM NW QUADRANT. SEAS 4 M OR GREATER FROM 20N
TO 26N BETWEEN 162W AND 169W WITH SEAS TO 11 M. SEAS 2.5 TO 3.5 M
ELSEWHERE FROM 18N TO 27N BETWEEN 158W AND 180W. WINDS 20 TO 30 KT
ELSEWHERE FROM 20N TO 26N BETWEEN 159W AND 168W.
.36 HOUR FORECAST TROPICAL STORM NOLO NEAR 22.2N 165.0W. MAXIMUM
SUSTAINED WINDS 60 KT GUSTS 75 KT.
.48 HOUR FORECAST TROPICAL STORM NOLO NEAR 22.0N 165.7W. MAXIMUM
SUSTAINED WINDS 55 KT GUSTS 65 KT. TROPICAL STORM FORCE WINDS
WITHIN 110 NM NE QUADRANT...80 NM SE QUADRANT...70 NM SW
QUADRANT...AND 100 NM NW QUADRANT. SEAS 4 M OR GREATER FROM 19N TO
25N BETWEEN 164W AND 169W WITH SEAS TO 11 M. SEAS 2.5 TO 3.5 M
ELSEWHERE FROM 16N TO 30N BETWEEN 160W AND 175W. WINDS 20 TO 30 KT
ELSEWHERE FROM 19N TO 27N BETWEEN 162W AND 171W.

FORECAST WINDS IN AND NEAR ACTIVE TROPICAL CYCLONES SHOULD BE
USED WITH CAUTION DUE TO UNCERTAINTY IN FORECAST TRACK...SIZE
AND INTENSITY.

.SYNOPSIS AND FORECAST.

.24 HOUR FORECAST NEW TROUGH 30N162W 28N168W 27N175W.
.48 HOUR FORECAST TROUGH ABSORBED BY FRONT DESCRIBED BELOW.

.48 HOUR FORECAST NEW FRONT 30N154W 28N157W THENCE TROUGH TO
26N163W.

.WINDS 20 KT OR LESS OVER REMAINDER OF FORECAST AREA.

.SEAS 2.5 M OR LOWER OVER REMAINDER OF FORECAST AREA.

.MONSOON TROUGH 13N140W 12N144W 10N149W 11N156W...AND 12N162W
08N180W. SCATTERED MODERATE TSTMS WITHIN 60 NM EITHER SIDE OF A
LINE 11N156W 06N177W. ISOLATED MODERATE TSTMS ELSEWHERE S OF
10N.

.FORECASTER TSAMOUS. HONOLULU HI.
```

---

### 12. Hourly Wind/Precip Observations

| Field | Value |
|---|---|
| **Resource ID** | oso_hourly_obs |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=OSO&issuedby=HFO |
| **Collected** | 2026-09-29T03:18:11.312271-10:00 HST |

```text
803
SXHW50 PHFO 291243
OSOHFO

Hawaii Wind Data
National Weather Service Honolulu HI
243 AM HST Tue Sep 29 2026

                            W I N D        D A T A
                            ----------------------
                                                                   IN KNOTS
 ID                Location              Date     Time     DIR    SPD   GUST
--------   -------------------------    -------  -(HST)-  ----   ----   ----
0000LLMH1  Lower Limahuli     Kauai     29Sep26   02:15    130      1      4
0000CMGH1  Common Ground      Kauai     29Sep26   02:15    130      5     12
0000HLIH1  Hanalei            Kauai     29Sep26   01:41    110      8     14
0000MLDH1  Moloaa Dairy       Kauai     29Sep26   01:45    120     10     18
0000HNMH1  Hanamaulu          Kauai     29Sep26   02:15     60      1      2
0000PHLI   Lihue              Kauai     29Sep26   02:00    100     13    MSG
0000NWWH1  Nawiliwili NOS     Kauai     29Sep26   02:30    100     11     13
0000POIH1  Poipu              Kauai                MSG    MSG    MSG    MSG
0000LNTH1  Lawai NTBG         Kauai     29Sep26   02:15     80      5      7
0000PAKH1  Port Allen         Kauai     29Sep26   02:00     90     12     15
0000MKAH1  Makaha Ridge       Kauai     29Sep26   02:11    200      3      7
0000MNRH1  Mana               Kauai     29Sep26   02:34    150      3      6
0000PHBK   Barking Sands      Kauai     29Sep26   02:00    150      9    MSG
0000PLRH1  Puu Lua            Kauai     29Sep26   02:35     80     10     16
0000POPH1  Puu Opae           Kauai     29Sep26   02:34    120      7     12
0000WHGH1  Waimea Heights     Kauai     29Sep26   02:35     30      7     14

0000KRGH1  Kalahee Ridge      Oahu      29Sep26   02:10     40      4      5
0000KAHH1  Kahuku             Oahu                 MSG    MSG    MSG    MSG
0000KTAH1  Kahuku Trng        Oahu      29Sep26   01:59    100      0      3
0000KFWH1  Kii                Oahu      29Sep26   01:45    100     11     18
0000OFRH1  Oahu Forest NWR    Oahu      29Sep26   02:36     90      5     10
0000KWMH1  Kaaawa Makai       Oahu      29Sep26   02:15     90      5      8
0000PHNG   Kaneohe MCBH       Oahu      29Sep26   02:00    120      7     16
0000MOKH1  Mokuoloe Is NOS    Oahu      29Sep26   02:30    200      3      4
0000BELH1  Bellows AFS        Oahu      29Sep26   02:15    100     10    MSG
0000KUXH1  Kaluanui           Oahu      29Sep26   02:15    150      1      4
0000LYOH1  Lyon               Oahu      29Sep26   02:05     10      1      2
0000NRSH1  Nuuanu Res No 1    Oahu      29Sep26   02:15     20      2      4
0000PHNL   Honolulu AP        Oahu      29Sep26   02:00     50      4    MSG
0000OOUH1  Honolulu Hbr NOS   Oahu      29Sep26   02:24     70      2      3
0000HOFH1  Honouliuli PHB     Oahu      29Sep26   02:41     20      3      4
0000SCBH1  Schofield Brks     Oahu      29Sep26   01:57    220      2      4
0000SCEH1  Schofield East     Oahu      29Sep26   01:58    100      2      5
0000HWLH1  HECO Wilikina      Oahu      29Sep26   02:30     60      2      2
0000PHJR   Kalaeloa           Oahu      29Sep26   02:00     40      5    MSG
0000HFHH1  HECO Farrington    Oahu      29Sep26   02:30     40      5     10
0000HPLH1  HECO Palehua       Oahu      29Sep26   02:30    100      4     10
0000HPDH1  HECO Palehua 2     Oahu      29Sep26   02:30     50      8     11
0000HPHH1  HECO Palehua 3     Oahu      29Sep26   02:30     60      5      9
0000HPRH1  HECO Paakea        Oahu      29Sep26   02:30     30      3      7
0000HLRH1  HECO Lualualei     Oahu      29Sep26   02:30     70      4      7
0000HWVH1  HECO Waianae Vly   Oahu                 MSG    MSG    MSG    MSG
0000PLHH1  Palehua            Oahu      29Sep26   02:36     60      0      0
0000WNVH1  Waianae Valley     Oahu      29Sep26   02:37     50      3      7
0000HHSH1  HECO Ala Hema St   Oahu      29Sep26   02:30     90      4      7
0000WBHH1  Waianae Harbor     Oahu                 MSG    MSG    MSG    MSG
0000HKRH1  HECO Kili Dr       Oahu      29Sep26   02:30     30      3      8
0000HMVH1  HECO Makaha Vly    Oahu      29Sep26   02:30    360      3      9
0000MKRH1  Makua Range        Oahu      29Sep26   01:58    120      4      8
0000KKRH1  Kuaokala           Oahu      29Sep26   02:36     30      4      7
0000AALH1  Kaala              Oahu      29Sep26   02:15    140      3      8
0000HFRH1  HECO Farrington2   Oahu      29Sep26   02:30     90      1      2
0000HFYH1  HECO Farrington3   Oahu      29Sep26   02:30    100      3      4
0000DLGH1  Dillingham         Oahu      29Sep26   01:49     90      0      3

0000MKPH1  Makapulapai        Molokai   29Sep26   02:15     90      9     15
0000PAFH1  Puu Alii           Molokai   29Sep26   02:22    140      3     10
0000HOMH1  Honolimaloo        Molokai   29Sep26   02:15    100      6     10
0000KOPH1  Keopukaloa         Molokai   29Sep26   02:15    130      8     13
0000MLKH1  Molokai 1          Molokai              MSG    MSG    MSG    MSG
0000MMPH1  MECO Makaena       Molokai   29Sep26   02:30     40      7      8
0000MKYH1  MECO Kalae Hwy     Molokai   29Sep26   02:30     10      5      6
0000PHMK   Molokai AP         Molokai   29Sep26   02:00    360      4    MSG
0000ANPH1  Anapuka            Molokai   29Sep26   02:15      0      0      0

0000LNIH1  Lanai 1            Lanai     29Sep26   02:37     30      0      0

0000KAOH1  Kaneloa            Kahoolawe            MSG    MSG    MSG    MSG

0000PHOG   Kahului AP         Maui      29Sep26   02:00    170      4    MSG
0000KLIH1  Kahului Hbr NOS    Maui      29Sep26   02:30    160      2      3
0000MHRH1  MECO Hansen Rd     Maui      29Sep26   02:30    150      2      4
0000MHKH1  MECO Haleakala Hwy Maui      29Sep26   02:30    140      3      5
0000MMKH1  MECO Makawao       Maui      29Sep26   02:30    180      5      7
0000MKTH1  MECO Kula 2        Maui      29Sep26   02:30    170      1      2
0000PILH1  Piiholo            Maui      29Sep26   02:15    170      3      4
0000EBYH1  EMI Baseyard       Maui      29Sep26   02:10    150      1      3
0000HNAH1  Hana               Maui                 MSG    MSG    MSG    MSG
0000NKUH1  Na Kula            Maui      29Sep26   02:35     70      5     19
0000AWAH1  Auwahi             Maui                 MSG    MSG    MSG    MSG
0000KLFH1  Kula 1             Maui      29Sep26   01:48     70      3      3
0000KKNH1  Kahikinui 1        Maui      29Sep26   02:34     20      5     10
0000KMEH1  Kamehamenui 1      Maui      29Sep26   01:48    140      2     10
0000SUMH1  Summit             Maui      29Sep26   02:15    140      8      8
0000NNEH1  Nene Nest          Maui      29Sep26   02:15    150      7     11
0000PHQH1  Park HQ            Maui      29Sep26   02:15    120      3      6
0000WKTH1  Waikamoi Treeline  Maui      29Sep26   02:15    170      6     10
0000MCTH1  MECO Crater Rd     Maui      29Sep26   02:30    170      3      5
0000KLGH1  Kula Ag            Maui      29Sep26   02:15    120      2      2
0000MWAH1  MECO Waipoli Rd    Maui      29Sep26   02:30     90      2      3
0000KKEH1  Keokea             Maui      29Sep26   02:15    130      2      2
0000MKUH1  MECO Kula          Maui      29Sep26   02:30     80      5      6
0000PHUH1  Pulehu             Maui      29Sep26   02:15    120      3      5
0000MNDH1  MECO Naalaea Rd    Maui      29Sep26   02:30    100      4      6
0000MURH1  MECO Ulupalakua    Maui      29Sep26   02:30     60      2      4
0000LPOH1  Lipoa              Maui      29Sep26   02:15    110      3      5
0000MVHH1  MECO Veterans Hwy  Maui      29Sep26   02:30     10      3      4
0000KPDH1  Kealia Pond        Maui      29Sep26   02:20     70      3      7
0000MMAH1  MECO Maalaea       Maui      29Sep26   02:30    350      2      3
00000P36   Maalaea Bay        Maui      29Sep26   02:15      0      0      0
0000HULH1  Hanaula            Maui      29Sep26   02:10     60      0      1
0000OLUH1  Olowalu            Maui      29Sep26   02:15     70      2      5
0000MMMH1  MECO Mamane Pl     Maui      29Sep26   02:30    180      0      2
0000MHOH1  MECO Honoapiilani  Maui      29Sep26   02:30    280      2      4
0000MHHH1  MECO Honoapiilani2 Maui      29Sep26   02:30    250      3      3
0000MKEH1  MECO Kealaloloa Rg Maui      29Sep26   02:30    290      8     10
0000MUGH1  MECO Ukumehame Gul Maui      29Sep26   02:30      0      7      9
0000MOOH1  MECO Olowalu       Maui      29Sep26   02:30     70      3      7
0000OLUH1  Olowalu            Maui      29Sep26   02:15     70      2      5
0000MLPH1  MECO Launiupoko    Maui      29Sep26   02:30     60      5      7
0000MLTH1  MECO Launiupoko 2  Maui      29Sep26   02:30     40      8     10
0000MLRH1  MECO Lahainaluna   Maui      29Sep26   02:30    100      4      6
0000LWTH1  Lahaina WTP        Maui      29Sep26   02:15    120      3      5
0000MKNH1  MECO Kaanapali     Maui      29Sep26   02:30    110      6      9
0000PHJH   Kapalua-W Maui     Maui                 MSG    MSG    MSG    MSG
0000HOOH1  Honolua            Maui      29Sep26   02:15    150      5      7

0000UPLH1  Upolu Airport      Hawaii    29Sep26   02:15    170      2      2
0000KMMH1  Kaluamakani        Hawaii    29Sep26   02:15    150      6      7
0000PMLH1  Puu Mali           Hawaii    29Sep26   02:00    200      5      9
0000KNKH1  Kanakaleonui       Hawaii    29Sep26   02:15    240      4      8
0000WPNH1  Waipunalei         Hawaii               MSG    MSG    MSG    MSG
0000LAUH1  Laupahoehoe        Hawaii    29Sep26   02:15    210      2      4
0000SPNH1  Spencer            Hawaii    29Sep26   02:15    190      5      9
0000HKUH1  Hakalau            Hawaii    29Sep26   01:45    220      4      9
0000KLXH1  Kulaimano          Hawaii    29Sep26   02:15    200      4      8
0000PIOH1  Piihonua           Hawaii    29Sep26   02:15    250      4      7
0000PHTO   Hilo AP            Hawaii    29Sep26   02:00    240      7    MSG
0000ILOH1  Hilo Hbr NOS       Hawaii    29Sep26   02:24    210      3      4
0000IPIH1  IPIF               Hawaii    29Sep26   02:15    240      3      6
0000WEXH1  Waiakea Exp Stn    Hawaii    29Sep26   02:00    MSG      0      1
0000KEUH1  Keaau              Hawaii    29Sep26   02:15      0      0      0
0000PAOH1  Pahoa              Hawaii    29Sep26   02:15      0      0      0
0000NHKH1  Nahuku             Hawaii    29Sep26   02:15    350      4      6
0000KKUH1  Keaumo             Hawaii    29Sep26   02:34    320      4      7
0000MOBH1  Mauna Loa Obs      Hawaii    29Sep26   02:00    MSG      5      8
0000PLIH1  Pali 2             Hawaii    29Sep26   02:01     20      6     10
0000KMOH1  Kealakomo          Hawaii    29Sep26   01:44     30      4     10
0000KPRH1  Kapapala           Hawaii    29Sep26   01:48     30      2      5
0000NENH1  Nene Cabin         Hawaii    29Sep26   02:23     20      4      7
0000KIOH1  Kaiholena          Hawaii    29Sep26   02:15    330      5      7
0000LKHH1  Lower Kahuku       Hawaii    29Sep26   02:23    340      2     10
0000SOPH1  South Point        Hawaii    29Sep26   02:00     60     11     17
0000KOMH1  Kona Hema          Hawaii    29Sep26   02:15     50      5      6
0000KRCH1  Kahuku Ranch       Hawaii    29Sep26   02:29    100      3      7
0000PHRH1  Puho CS            Hawaii    29Sep26   02:22     80      3      4
0000HLNH1  HELCO Lolo Ln      Hawaii    29Sep26   02:30     80      3      4
0000HHUH1  HELCO Hualalai Rd  Hawaii    29Sep26   02:30     50      3      5
0000KOUH1  Keahuolu           Hawaii    29Sep26   02:15     60      2      3
0000PHKO   Kona Intl AP       Hawaii    29Sep26   02:00    100      3    MSG
0000KHOH1  Kaloko-Honokohau   Hawaii    29Sep26   02:15     50      3      4
0000PLMH1  Palamanui          Hawaii    29Sep26   02:15     90      1      2
0000PWAH1  Puu Waawaa (UHM)   Hawaii    29Sep26   02:15    150      3      4
0000KIUH1  Kaiaulu Puu Waawaa Hawaii    29Sep26   02:15    310      2      3
0000KPLH1  Kaupulehu          Hawaii    29Sep26   02:36    160      4      6
0000PWWH1  Puu Waawaa         Hawaii    29Sep26   02:37    150      3      4
0000HMHH1  HELCO Mamalahoa 2  Hawaii    29Sep26   02:30    170      4      5
0000MMLH1  Mamalahoa          Hawaii    29Sep26   02:15      0      0      0
0000HMWH1  HELCO Mamalahoa 3  Hawaii    29Sep26   02:30    160      4      6
0000PULH1  Puuanahulu         Hawaii    29Sep26   02:37    170      3      6
0000AHMH1  Ahumoa             Hawaii    29Sep26   02:35    100      3      7
0000AIPH1  Aipaloa            Hawaii    29Sep26   02:15    150      8     10
0000HSRH1  HELCO Saddle Rd    Hawaii    29Sep26   02:30    100      5      7
0000HMYH1  HELCO Mamalahoa    Hawaii    29Sep26   02:30    130      6      7
0000HHCH1  HELCO Hokuloa UCC  Hawaii    29Sep26   02:30    140      3      5
0000HWRH1  HELCO Waikoloa Rd  Hawaii    29Sep26   02:30     90      8      9
0000HWXH1  HELCO Waikoloa 2   Hawaii    29Sep26   02:30    140      9     11
0000WKVH1  Waikoloa           Hawaii    29Sep26   02:35    130      5     10
0000HLOH1  HELCO Lalamilo     Hawaii    29Sep26   02:30     60     10     11
0000LLAH1  Lalamilo           Hawaii    29Sep26   02:15     70      1      2
0000HKWH1  HELCO Kawaihae Rd  Hawaii    29Sep26   02:30     80      4      6
0000PKAH1  PTA Kipuka Alala   Hawaii    29Sep26   01:55    100      3      5
0000PKWH1  PTA West           Hawaii    29Sep26   01:56    140      5      7
0000PKMH1  PTA Keamuku        Hawaii    29Sep26   01:50    170      0      0
0000PTRH1  PTA Range 17       Hawaii    29Sep26   01:49    150      9     15
0000PERH1  Puhe CS            Hawaii    29Sep26   02:24     90      4      7
0000KWHH1  Kawaihae NOS       Hawaii               MSG    MSG    MSG    MSG
0000HHKH1  HELCO Hulukupuna   Hawaii    29Sep26   02:30     80      6      9
0000PLAH1  Puuloa             Hawaii    29Sep26   02:15    300      4      5
0000HMLH1  HELCO Maluokalani  Hawaii               MSG    MSG    MSG    MSG
0000HKDH1  HELCO Ala Kahua    Hawaii    29Sep26   02:30    220      5      7
0000KHRH1  Kohala Ranch       Hawaii    29Sep26   02:35     70      3      6
0000KEHH1  Kehena             Hawaii    29Sep26   02:15     80      1      3
```

---

### 13. Monthly Climate Summary — HNL

| Field | Value |
|---|---|
| **Resource ID** | clm_monthly_climate_summary_HNL |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLM&issuedby=HNL |
| **Collected** | 2026-09-29T01:53:12.911878-10:00 HST |

```text
434
CXHW50 PHFO 011625
CLMHNL

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
625 AM HST TUE SEP 01 2026

...................................

...THE HONOLULU CLIMATE SUMMARY FOR THE MONTH OF AUGUST 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1940 TO 2026

WEATHER         OBSERVED          NORMAL  DEPART   LAST YEAR`S
                VALUE   DATE(S)   VALUE   FROM     VALUE DATE(S)
                                          NORMAL
................................................................
TEMPERATURE (F)
RECORD
 HIGH             95   08/31/2019
 LOW              25   08/02/2024
HIGHEST           90   08/09         89       1       92  08/11
                       08/11
                       08/22
LOWEST            74   08/19         75      -1       74  08/11
                       08/20
                                                          08/14
                                                          08/30
AVG. MAXIMUM    88.3               88.8    -0.5     89.2
AVG. MINIMUM    76.7               75.6     1.1     76.6
MEAN            82.5               82.2     0.3     82.9
DAYS MAX >= 93     0                                   0
DAYS MAX >= 90     6                                  13
DAYS MAX <= 80     0                                   0
DAYS MIN >= 72    31                                  31
DAYS MIN <= 60     0                                   0
DAYS MIN <= 55     0                                   0

PRECIPITATION (INCHES)
RECORD
 MAXIMUM        3.74   2004
 MINIMUM           T   2025
TOTALS          0.91               0.84    0.07        T
DAILY AVG.      0.03               0.03    0.00        T
DAYS >= .01        1                5.7    -4.7        0
DAYS >= .10        0                1.2    -1.2        0
DAYS >= .50        0                0.4    -0.4        0
DAYS >= 1.00       0                0.2    -0.2        0
GREATEST
 24 HR. TOTAL   0.86   08/15 TO 08/16                  T

DEGREE DAYS
HEATING TOTAL      0                  0       0        0
 SINCE 7/1         0                  0       0       MM
COOLING TOTAL    550                533      17      561
 SINCE 1/1      3210               3077     133       MM
................................................................

WIND (MPH)
AVERAGE WIND SPEED              12.5
HIGHEST WIND SPEED/DIRECTION    38/050    DATE  08/16
HIGHEST GUST SPEED/DIRECTION    53/060    DATE  08/16

SKY COVER
POSSIBLE SUNSHINE (PERCENT)   MM
AVERAGE SKY COVER           0.45
NUMBER OF DAYS FAIR           10
NUMBER OF DAYS PC             19
NUMBER OF DAYS CLOUDY          2

AVERAGE RH (PERCENT)     66

WEATHER CONDITIONS. NUMBER OF DAYS WITH
THUNDERSTORM             MM     MIXED PRECIP              MM
HEAVY RAIN                1     RAIN                       1
LIGHT RAIN               12     FREEZING RAIN             MM
LT FREEZING RAIN         MM     HAIL                      MM
HEAVY SNOW               MM     SNOW                      MM
LIGHT SNOW               MM     SLEET                     MM
FOG                       3     FOG W/VIS <= 1/4 MILE     MM
HAZE                     MM

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 14. Monthly Climate Summary — ITO

| Field | Value |
|---|---|
| **Resource ID** | clm_monthly_climate_summary_ITO |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLM&issuedby=ITO |
| **Collected** | 2026-09-29T01:53:57.677824-10:00 HST |

```text
433
CXHW53 PHFO 011625
CLMITO

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
625 AM HST TUE SEP 01 2026

...................................

...THE HILO/GEN.LYMAN FLD CLIMATE SUMMARY FOR THE MONTH OF AUGUST 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1949 TO 2026

WEATHER         OBSERVED          NORMAL  DEPART   LAST YEAR`S
                VALUE   DATE(S)   VALUE   FROM     VALUE DATE(S)
                                          NORMAL
................................................................
TEMPERATURE (F)
RECORD
 HIGH             93   08/15/1950
 LOW              63   08/01/1955
HIGHEST           87   08/21         83       4       88  08/11
LOWEST            70   08/30         69       1       67  08/24
AVG. MAXIMUM    83.7               82.9     0.8     84.9
AVG. MINIMUM    72.6               70.4     2.2     70.0
MEAN            78.2               76.6     1.6     77.5
DAYS MAX >= 93     0                                   0
DAYS MAX >= 90     0                                   0
DAYS MAX <= 80     2                                   2
DAYS MIN >= 72    20                                   6
DAYS MIN <= 60     0                                   0
DAYS MIN <= 55     0                                   0

PRECIPITATION (INCHES)
RECORD
 MAXIMUM       48.85   2018
 MINIMUM        2.06   2025
TOTALS         20.85              11.30    9.55     2.06
DAILY AVG.      0.67               0.36    0.31     0.05
DAYS >= .01       25               27.2    -2.2       19
DAYS >= .10       16               18.2    -2.2        5
DAYS >= .50        8                6.0     2.0        1
DAYS >= 1.00       3                2.2     0.8        0
GREATEST
 24 HR. TOTAL   9.24   08/15 TO 08/16               0.70

DEGREE DAYS
HEATING TOTAL      0                  0       0        0
 SINCE 7/1         0                  0       0       MM
COOLING TOTAL    416                361      55      393
 SINCE 1/1      2429               2111     318       MM
................................................................

WIND (MPH)
AVERAGE WIND SPEED              6.8
HIGHEST WIND SPEED/DIRECTION    39/090    DATE  08/15
HIGHEST GUST SPEED/DIRECTION    56/080    DATE  08/15

SKY COVER
POSSIBLE SUNSHINE (PERCENT)   MM
AVERAGE SKY COVER           0.78
NUMBER OF DAYS FAIR            1
NUMBER OF DAYS PC             11
NUMBER OF DAYS CLOUDY         19

AVERAGE RH (PERCENT)     81

WEATHER CONDITIONS. NUMBER OF DAYS WITH
THUNDERSTORM             MM     MIXED PRECIP              MM
HEAVY RAIN               15     RAIN                      15
LIGHT RAIN               27     FREEZING RAIN             MM
LT FREEZING RAIN         MM     HAIL                      MM
HEAVY SNOW               MM     SNOW                      MM
LIGHT SNOW               MM     SLEET                     MM
FOG                      25     FOG W/VIS <= 1/4 MILE     MM
HAZE                      8

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 15. Monthly Climate Summary — LIH

| Field | Value |
|---|---|
| **Resource ID** | clm_monthly_climate_summary_LIH |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLM&issuedby=LIH |
| **Collected** | 2026-09-29T01:53:27.741476-10:00 HST |

```text
436
CXHW51 PHFO 011625
CLMLIH

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
625 AM HST TUE SEP 01 2026

...................................

...THE LIHUE CLIMATE SUMMARY FOR THE MONTH OF AUGUST 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1950 TO 2026

WEATHER         OBSERVED          NORMAL  DEPART   LAST YEAR`S
                VALUE   DATE(S)   VALUE   FROM     VALUE DATE(S)
                                          NORMAL
................................................................
TEMPERATURE (F)
RECORD
 HIGH             91   08/31/2019
                       08/25/2019
                       09/19/1994
 LOW              59   08/27/2020
HIGHEST           87   08/13         85       2       88  08/16
LOWEST            72   08/07         75      -3       72  08/11
AVG. MAXIMUM    84.7               85.2    -0.5     86.6
AVG. MINIMUM    75.7               75.2     0.5     75.7
MEAN            80.2               80.2     0.0     81.2
DAYS MAX >= 93     0                                   0
DAYS MAX >= 90     0                                   0
DAYS MAX <= 80     1                                   0
DAYS MIN >= 72    31                                  31
DAYS MIN <= 60     0                                   0
DAYS MIN <= 55     0                                   0

PRECIPITATION (INCHES)
RECORD
 MAXIMUM        8.13   1959
 MINIMUM        0.44   2007
TOTALS          2.43               2.33    0.10     1.25
DAILY AVG.      0.08               0.08    0.00     0.04
DAYS >= .01       22               18.0     4.0       12
DAYS >= .10        4                5.3    -1.3        2
DAYS >= .50        1                0.9     0.1        1
DAYS >= 1.00       1                0.4     0.6        0
GREATEST
 24 HR. TOTAL   1.18   08/16 TO 08/17               0.83

DEGREE DAYS
HEATING TOTAL      0                  0       0        0
 SINCE 7/1         0                  0       0       MM
COOLING TOTAL    480                471       9      508
 SINCE 1/1      2703               2634      69       MM
................................................................

WIND (MPH)
AVERAGE WIND SPEED              14.6
HIGHEST WIND SPEED/DIRECTION    39/070    DATE  08/16
HIGHEST GUST SPEED/DIRECTION    53/070    DATE  08/16

SKY COVER
POSSIBLE SUNSHINE (PERCENT)   MM
AVERAGE SKY COVER           0.61
NUMBER OF DAYS FAIR            3
NUMBER OF DAYS PC             19
NUMBER OF DAYS CLOUDY          9

AVERAGE RH (PERCENT)     78

WEATHER CONDITIONS. NUMBER OF DAYS WITH
THUNDERSTORM             MM     MIXED PRECIP              MM
HEAVY RAIN                3     RAIN                       3
LIGHT RAIN               19     FREEZING RAIN             MM
LT FREEZING RAIN         MM     HAIL                      MM
HEAVY SNOW               MM     SNOW                      MM
LIGHT SNOW               MM     SLEET                     MM
FOG                      17     FOG W/VIS <= 1/4 MILE     MM
HAZE                     10

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 16. Monthly Climate Summary — OGG

| Field | Value |
|---|---|
| **Resource ID** | clm_monthly_climate_summary_OGG |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLM&issuedby=OGG |
| **Collected** | 2026-09-29T01:53:42.710549-10:00 HST |

```text
435
CXHW52 PHFO 011625
CLMOGG

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
625 AM HST TUE SEP 01 2026

...................................

...THE KAHULUI/MAUI CLIMATE SUMMARY FOR THE MONTH OF AUGUST 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1954 TO 2026

WEATHER         OBSERVED          NORMAL  DEPART   LAST YEAR`S
                VALUE   DATE(S)   VALUE   FROM     VALUE DATE(S)
                                          NORMAL
................................................................
TEMPERATURE (F)
RECORD
 HIGH             97   08/22/2015
                       08/31/1994
 LOW              60   08/30/2019
HIGHEST           90   08/11         88       2       92  08/16
                       08/21
                       08/24
                                                          08/23
                                                          08/27
LOWEST            70   08/20         71      -1       65  08/25
AVG. MAXIMUM    87.1               89.9    -2.8     89.5
AVG. MINIMUM    74.4               72.3     2.1     71.7
MEAN            80.8               81.1    -0.3     80.6
DAYS MAX >= 93     0                                   0
DAYS MAX >= 90     3                                  17
DAYS MAX <= 80     0                                   0
DAYS MIN >= 72    28                                  16
DAYS MIN <= 60     0                                   0
DAYS MIN <= 55     0                                   0

PRECIPITATION (INCHES)
RECORD
 MAXIMUM        1.93   2018
 MINIMUM        0.01   2025
TOTALS          1.47               0.53    0.94     0.01
DAILY AVG.      0.05               0.02    0.03     0.00
DAYS >= .01        5                7.4    -2.4        1
DAYS >= .10        3                1.3     1.7        0
DAYS >= .50        1                0.2     0.8        0
DAYS >= 1.00       0                0.0     0.0        0
GREATEST
 24 HR. TOTAL   1.20   08/15 TO 08/16               0.01

DEGREE DAYS
HEATING TOTAL      0                  0       0        0
 SINCE 7/1         0                  0       0       MM
COOLING TOTAL    400                499     -99      490
 SINCE 1/1      2784               2847     -63       MM
................................................................

WIND (MPH)
AVERAGE WIND SPEED              15.9
HIGHEST WIND SPEED/DIRECTION    38/050    DATE  08/15
HIGHEST GUST SPEED/DIRECTION    62/050    DATE  08/15

SKY COVER
POSSIBLE SUNSHINE (PERCENT)   MM
AVERAGE SKY COVER           0.40
NUMBER OF DAYS FAIR           15
NUMBER OF DAYS PC             14
NUMBER OF DAYS CLOUDY          2

AVERAGE RH (PERCENT)     73

WEATHER CONDITIONS. NUMBER OF DAYS WITH
THUNDERSTORM             MM     MIXED PRECIP              MM
HEAVY RAIN                1     RAIN                       2
LIGHT RAIN               15     FREEZING RAIN             MM
LT FREEZING RAIN         MM     HAIL                      MM
HEAVY SNOW               MM     SNOW                      MM
LIGHT SNOW               MM     SLEET                     MM
FOG                      12     FOG W/VIS <= 1/4 MILE     MM
HAZE                      2

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 17. NHC Atlantic Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_atlc_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays=2 |
| **Collected** | 2026-09-29T04:53:30.141159-10:00 HST |

```text
750 ACCA62 KNHC 291124TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT martes 29 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Fay, ubicada aloeste-suroeste de las Azores, y sobre la Tormenta Tropical Hanna,ubicada al este-noreste de las Bermudas.No se espera la formación de ciclones tropicales durante lospróximos 7 días.&&Las Advertencias Públicas sobre la Tormenta Tropical Hanna se emitenbajo el encabezado de la OMM WTNT33 KNHC y bajo el encabezado deAWIPS MIATCPAT3. Pronóstico/Advertencias sobre la Tormenta TropicalHanna se emiten bajo el encabezado de la OMM WTNT23 KNHC y bajo elencabezado de AWIPS MIATCMAT3.$$Pronosticador Kelly*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 18. NHC Atlantic Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_atlc_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays=7 |
| **Collected** | 2026-09-29T04:54:30.011241-10:00 HST |

```text
750 ACCA62 KNHC 291124TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT martes 29 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Fay, ubicada aloeste-suroeste de las Azores, y sobre la Tormenta Tropical Hanna,ubicada al este-noreste de las Bermudas.No se espera la formación de ciclones tropicales durante lospróximos 7 días.&&Las Advertencias Públicas sobre la Tormenta Tropical Hanna se emitenbajo el encabezado de la OMM WTNT33 KNHC y bajo el encabezado deAWIPS MIATCPAT3. Pronóstico/Advertencias sobre la Tormenta TropicalHanna se emiten bajo el encabezado de la OMM WTNT23 KNHC y bajo elencabezado de AWIPS MIATCMAT3.$$Pronosticador Kelly*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 19. NHC Central Pacific Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_cpac_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=2 |
| **Collected** | 2026-09-29T04:58:30.267593-10:00 HST |

```text
750 ACCA62 KNHC 291124TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT martes 29 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Fay, ubicada aloeste-suroeste de las Azores, y sobre la Tormenta Tropical Hanna,ubicada al este-noreste de las Bermudas.No se espera la formación de ciclones tropicales durante lospróximos 7 días.&&Las Advertencias Públicas sobre la Tormenta Tropical Hanna se emitenbajo el encabezado de la OMM WTNT33 KNHC y bajo el encabezado deAWIPS MIATCPAT3. Pronóstico/Advertencias sobre la Tormenta TropicalHanna se emiten bajo el encabezado de la OMM WTNT23 KNHC y bajo elencabezado de AWIPS MIATCMAT3.$$Pronosticador Kelly*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 20. NHC Central Pacific Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_cpac_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=7 |
| **Collected** | 2026-09-29T04:59:29.972482-10:00 HST |

```text
750 ACCA62 KNHC 291124TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT martes 29 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Fay, ubicada aloeste-suroeste de las Azores, y sobre la Tormenta Tropical Hanna,ubicada al este-noreste de las Bermudas.No se espera la formación de ciclones tropicales durante lospróximos 7 días.&&Las Advertencias Públicas sobre la Tormenta Tropical Hanna se emitenbajo el encabezado de la OMM WTNT33 KNHC y bajo el encabezado deAWIPS MIATCPAT3. Pronóstico/Advertencias sobre la Tormenta TropicalHanna se emiten bajo el encabezado de la OMM WTNT23 KNHC y bajo elencabezado de AWIPS MIATCMAT3.$$Pronosticador Kelly*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 21. NHC Eastern Pacific Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_epac_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=epac&fdays=2 |
| **Collected** | 2026-09-29T05:00:29.876710-10:00 HST |

```text
750 ACCA62 KNHC 291124TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT martes 29 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Fay, ubicada aloeste-suroeste de las Azores, y sobre la Tormenta Tropical Hanna,ubicada al este-noreste de las Bermudas.No se espera la formación de ciclones tropicales durante lospróximos 7 días.&&Las Advertencias Públicas sobre la Tormenta Tropical Hanna se emitenbajo el encabezado de la OMM WTNT33 KNHC y bajo el encabezado deAWIPS MIATCPAT3. Pronóstico/Advertencias sobre la Tormenta TropicalHanna se emiten bajo el encabezado de la OMM WTNT23 KNHC y bajo elencabezado de AWIPS MIATCMAT3.$$Pronosticador Kelly*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 22. NHC Eastern Pacific Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_epac_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=epac&fdays=7 |
| **Collected** | 2026-09-29T05:01:29.888230-10:00 HST |

```text
750 ACCA62 KNHC 291124TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT martes 29 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Fay, ubicada aloeste-suroeste de las Azores, y sobre la Tormenta Tropical Hanna,ubicada al este-noreste de las Bermudas.No se espera la formación de ciclones tropicales durante lospróximos 7 días.&&Las Advertencias Públicas sobre la Tormenta Tropical Hanna se emitenbajo el encabezado de la OMM WTNT33 KNHC y bajo el encabezado deAWIPS MIATCPAT3. Pronóstico/Advertencias sobre la Tormenta TropicalHanna se emiten bajo el encabezado de la OMM WTNT23 KNHC y bajo elencabezado de AWIPS MIATCMAT3.$$Pronosticador Kelly*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 23. NHC source index

| Field | Value |
|---|---|
| **Resource ID** | nhc_homepage |
| **Official source** | https://www.nhc.noaa.gov/ |
| **Collected** | 2026-09-29T06:37:29.990089-10:00 HST |

```text
Home

Mobile Site

Text Version

RSS

Local Forecast

NATIONAL HURRICANE CENTER and
CENTRAL PACIFIC HURRICANE CENTER

National Oceanic and Atmospheric Administration

Analysis & Forecasts

Tropical Cyclone Products

Tropical Weather Outlooks

Marine Products

Rip Currents Map

RSS Feeds

GIS Products

Alternate Formats

Tropical Cyclone Product Descriptions

Tropical Cyclone Product Examples

Marine Product Descriptions

Data & Tools

Satellite Imagery

Radar Imagery

Aircraft Reconnaissance

Tropical Analysis Tools

Experimental Products

Lat/Lon Distance Calculator

Blank Tracking Maps

Educational Resources

Be Prepared!
NWS Hurricane Prep Week

Outreach Documents

TC Videos

Rip Currents

Storm Surge

Watch/Warning Breakpoints

Climatology

Tropical Cyclone Names

Wind Scale

Records and Facts

Historical Hurricane Summaries

Forecast Models

NHC Publications

NHC Glossary

Acronyms

Frequent Questions

Archives

Tropical Cyclone Advisories

Tropical Weather Outlooks

Tropical Cyclone Reports and Season Summaries

Tropical Cyclone Forecast Verification

NHC News Archive

Other Archives: HURDAT, Track Maps, Marine Products, and more

About

National Hurricane Center

Central Pacific Hurricane Center

Library

Contact Us

Search

Search for

Search

Top News of the Day...
view past news

Last update Tue, 29 Sep 2026 16:30:35 UTC

NHC issuing advisories for the Atlantic on

TD Fay

and

TS Hanna

NHC issuing advisories for the Eastern Pacific on

Hurricane Polo

and

TS Rachel

and

TD Nineteen-E

NHC issuing advisories for the Central Pacific on

Hurricane Nolo

Marine warnings are in effect for the Eastern Pacific

Key messages regarding Hurricane Polo

(en Español: Mensajes Claves)

Key messages regarding Tropical Storm Rachel

(en Español: Mensajes Claves)

Graphical Tropical Weather Outlook (Static Images)

JavaScript is currently disabled in your browser or you are using an older browser that is incompatible with this map. To view the interactive map, please enable JavaScript or update your browser if possible. Direct links to the latest high-resolution forecast images are provided below:

View Atlantic 2-Day Outlook

View Atlantic 7-Day Outlook

View Eastern Pacific 2-Day Outlook

View Eastern Pacific 7-Day Outlook

View Central Pacific 2-Day Outlook

View Central Pacific 7-Day Outlook

Central Pacific

Pacific

Atlantic

2-Day Forecast

7-Day Forecast

Disturbances:

None

Disturbances:

None

Disturbances:

None

Disturbances:

None

Disturbances:

None

Disturbances:

None

View Full Graphical Tropical Weather Outlook
| Marine Products

Close (X)

View Storm Details

Eastern North Pacific
(East of 140°W)

Tropical Weather Outlook

(en Español*)

500 AM PDT Tue Sep 29 2026

Tropical Weather Discussion

1605 UTC Tue Sep 29 2026

Hurricane Polo

Satellite |
Buoys |
Grids |
Storm Archive

...POLO ABOUT TO MAKE LANDFALL NEAR GUAYMAS MEXICO...
...CONDITIONS DETERIORATING IN THE LANDFALL AREA...

8:00 AM MST Tue Sep 29

Location: 27.8°N 110.9°W

Moving: NE at 17 mph

Min pressure: 981 mb

Max sustained: 75 mph

Public

Advisory

#36

800 AM MST

Forecast

Advisory

#36

1500 UTC

Forecast

Discussion

#36

800 AM MST

Wind Speed

Probabilities

#36

1500 UTC

Productos en español:

(más información)

Aviso

Publico

Pronóstico

Discusión

Wind Speed
Probabilities

Arrival Time
of Winds

Wind
History

Interactive
Cone

Warnings/Cone
Static Images

Warnings/Cone
Interactive Map

Experimental Cone
Static Images

Experimental Cone
Interactive Map

Warnings and
Surface Wind

Key
Messages

Mensajes
Claves

Rip
Currents

Rainfall
Potential

Tropical Storm Rachel

Satellite |
Buoys |
Grids |
Storm Archive

...RACHEL SLIGHTLY STRONGER...

9:00 AM CST Tue Sep 29

Location: 15.3°N 105.0°W

Moving: WNW at 13 mph

Min pressure: 987 mb

Max sustained: 65 mph

Public

Advisory

#10

900 AM CST

Forecast

Advisory

#10

1500 UTC

Forecast

Discussion

#10

900 AM CST

Wind Speed

Probabilities

#10

1500 UTC

Productos en español:

(más información)

Aviso

Publico

Pronóstico

Discusión

Wind Speed
Probabilities

Arrival Time
of Winds

Wind
History

Interactive
Cone

Warnings/Cone
Static Images

Warnings/Cone
Interactive Map

Experimental Cone
Static Images

Experimental Cone
Interactive Map

Warnings and
Surface Wind

Key
Messages

Mensajes
Claves

Rip
Currents

Rainfall
Potential

Tropical Depression Nineteen-E

Satellite |
Buoys |
Grids |
Storm Archive

...NEW TROPICAL DEPRESSION EXPECTED TO BE SHORT-LIVED WELL OFFSHORE OF MEXICO...

8:00 AM PDT Tue Sep 29

Location: 14.4°N 131.6°W

Moving: E at 9 mph

Min pressure: 1004 mb

Max sustained: 35 mph

Public

Advisory

#1

800 AM PDT

Forecast

Advisory

#1

1500 UTC

Forecast

Discussion

#1

800 AM PDT

Wind Speed

Probabilities

#1

1500 UTC

Productos en español:

(más información)

Aviso

Publico

Pronóstico

Discusión

Wind Speed
Probabilities

Arrival Time
of Winds

Wind
History

Interactive
Cone

Warnings/Cone
Static Images

Warnings/Cone
Interactive Map

Experimental Cone
Static Images

Experimental Cone
Interactive Map

Warnings and
Surface Wind

Rip
Currents

Central North Pacific
(140°W to 180°)

Tropical Weather Outlook

(en Español*)

200 AM HST Tue Sep 29 2026

Hurricane Nolo

Satellite |
Buoys |
Grids |
Storm Archive

...NOLO IMPACTING THE PAPAHANAUMOKUAKEA MARINE NATIONAL MONUMENT...

5:00 AM HST Tue Sep 29

Location: 20.5°N 164.2°W

Moving: N at 9 mph

Min pressure: 964 mb

Max sustained: 110 mph

Public

Advisory

#36

500 AM HST

Forecast

Advisory

#36

1500 UTC

Forecast

Discussion

#36

500 AM HST

Wind Speed

Probabilities

#36

1500 UTC

Productos en español:

(más información)

Aviso

Publico

Pronóstico

Discusión

Wind Speed
Probabilities

Arrival Time
of Winds

Wind
History

Interactive
Cone

Warnings/Cone
Static Images

Warnings/Cone
Interactive Map

Experimental Cone
Static Images

Experimental Cone
Interactive Map

Warnings and
Surface Wind

Rainfall
Potential

Atlantic - Caribbean Sea - Gulf of America

Tropical Weather Outlook

(en Español*)

800 AM EDT Tue Sep 29 2026

Tropical Weather Discussion

1215 UTC Tue Sep 29 2026

Tropical Depression Fay

Satellite |
Buoys |
Grids |
Storm Archive

...FAY WEAKENS INTO A DEPRESSION...

11:00 AM AST Tue Sep 29

Location: 24.2°N 47.3°W

Moving: SW at 12 mph

Min pressure: 1010 mb

Max sustained: 35 mph

Public

Advisory

#38

1100 AM AST

Forecast

Advisory

#38

1500 UTC

Forecast

Discussion

#38

1100 AM AST

Wind Speed

Probabilities

#38

1500 UTC

Productos en español:

(más información)

Aviso

Publico

Pronóstico

Discusión

Wind Speed
Probabilities

Arrival Time
of Winds

Wind
History

Interactive
Cone

Warnings/Cone
Static Images

Warnings/Cone
Interactive Map

Experimental Cone
Static Images

Experimental Cone
Interactive Map

Warnings and
Surface Wind

Rip
Currents

Tropical Storm Hanna

Satellite |
Buoys |
Grids |
Storm Archive

...HANNA MOVING SOUTHEASTWARD AND SLIGHTLY WEAKER...

11:00 AM AST Tue Sep 29

Location: 34.6°N 45.5°W

Moving: SE at 12 mph

Min pressure: 1004 mb

Max sustained: 40 mph

Public

Advisory

#5

1100 AM AST

Forecast

Advisory

#5

1500 UTC

Forecast

Discussion

#5

1100 AM AST

Wind Speed

Probabilities

#5

1500 UTC

Productos en español:

(más información)

Aviso

Publico

Pronóstico

Discusión

Wind Speed
Probabilities

Arrival Time
of Winds

Wind
History

Interactive
Cone

Warnings/Cone
Static Images

Warnings/Cone
Interactive Map

Experimental Cone
Static Images

Experimental Cone
Interactive Map

Warnings and
Surface Wind

Rip
Currents

Building Your Hurricane Knowledge Kit

‹

National Hurricane Center Track Forecast Cone (2026)

Building Your Hurricane "Knowledge" Kit: Storm Surge Warning

Building Your Hurricane "Knowledge" Kit: Potential Tropical Cyclones

Tropical Cyclone Names

Tropical Waves

Artificial Intelligence (AI) in Hurricane Forecasting

Building Your Hurricane "Knowledge" Kit: Tropical Weather Outlook

Building Your Hurricane "Knowledge" Kit: Time of Arrival

Building Your Hurricane "Knowledge" Kit: Wind Speed Probabilities

Building Your Hurricane "Knowledge" Kit: Saffir-Simpson Hurricane Wind Scale

Building Your Hurricane "Knowledge" Kit: Storm Surge Watch

National Hurricane Preparedness Week Preview: Assembling Your Hurricane "Knowledge" Kit

›

Quick Links and Additional Resources

Tropical Cyclone Forecasts

Tropical Cyclone Advisories

Tropical Weather Outlook

Audio/Podcasts

About Advisories

Marine Forecasts

Offshore Waters Forecasts

Gridded Forecasts

Graphicast

About Marine

Social Media

NHC on Facebook

NHC on X

NHC on YouTube

NHC Blog:
"Inside the Eye"

Hurricane Preparedness

Preparedness Guide

Hurricane Hazards

Watches and Warnings

Marine Safety

Ready.gov Hurricanes

Weather-Ready Nation

Emergency Management Offices

Research and Development

NOAA Hurricane Research Division

Hurricane and Ocean Testbed

Hurricane Forecast Improvement Program

Other Resources

Q & A with NHC

NHC/AOML Library Branch

NOAA: Hurricane FAQs

National Hurricane Operations Plan

WX4NHC Amateur Radio

NWS Forecast Offices

Weather Prediction Center

Storm Prediction Center

Ocean Prediction Center

Local Forecast Offices

Worldwide Tropical Cyclone Centers

Canadian Hurricane Centre

Joint Typhoon Warning Center

Other Tropical Cyclone Centers

WMO Severe Weather Info Centre

US Dept of Commerce

National Oceanic and Atmospheric Administration

National Hurricane Center

11691 SW 17th Street

Miami, FL, 33165

nhcwebmaster@noaa.gov

Central Pacific Hurricane Center

2525 Correa Rd

Suite 250

Honolulu, HI 96822

W-HFO.webmaster@noaa.gov

Disclaimer

Information Quality

Help

Glossary
```

---

### 24. NOAA solar calculation table

| Field | Value |
|---|---|
| **Resource ID** | solar_calculation_table |
| **Official source** | https://gml.noaa.gov/grad/solcalc/table.php?lat=21.3&lon=-157.85&year=2026 |
| **Collected** | 2026-09-29T01:52:45.566726-10:00 HST |

```text
Solar Calculator - NOAA Global Monitoring Laboratory

Skip to main content

An official website of the United States government Here's how you know

Official websites use .gov

A .gov website belongs to an official government organization in the United States.

Secure .gov websites use HTTPS

A lock () or https:// means you’ve safely connected to the .gov website. Share sensitive information only on official, secure websites.

Search

Search GML:

Global Monitoring Laboratory

Menu

Home

About

About GML
Science Reviews
Safety Program

Employment
Visiting
Contact Us

Intranet

People

Organization
Staff
Employee Spotlight

Research

Research Overview
Carbon Cycle Greenhouse Gases
Greenhouse gases and Ozone-depleting Substances
Ozone and Water Vapor
Global Radiation, Aerosols and Clouds
Publications
Calibration Facilities
WMO Central Calibration Laboratory
Central UV Calibration Facility
Broadband Solar Calibration Facility
World Dobson Ozone Calibration Centre

Observing Networks

Overview
Observations Overview
Measurement Sites
Field Campaigns

Atmospheric Baseline Observatories
Observatory Operations
Barrow, Alaska
Mauna Loa, Hawaii
American Samoa
South Pole

Observing Networks
Greenhouse Gas Reference Network
Halocarbons and Trace Gases
Surface Radiation
Federated Aerosol Network
Ozone
Water Vapor

Data & Products

Data
Data & Products Portal
Data Finder
ObsPack Data Products
Measurement Sites

Visualization & Tools

Data Viewer
South Pole Ozone Hole
Mauna Loa Apparent Transmission
Barrow Snow Melt Dates

Products
Greenhouse Gas Index
Ozone Depletion Index
Trends in CO2, CH4, N2O, SF6
Modeling

Information

News
Seminars
Education/Outreach
Student Opportunities
FAQ's
Publications

Webcams
South Pole Webcam
Mauna Loa Webcams
Barrow Webcam

Global Monitoring Annual Conference
GMAC Conference

Search

Search GML:

PDF Format

Sunrise Table for 2026

Location: Latitude 21.30000 Longitude -157.85000

Time Zone Offset: Pacific/Honolulu -10.0

All times are in local time. Cells with light green color indicate when daylight saving time is in effect.

Day

Jan

Feb

Mar

Apr

May

Jun

Jul

Aug

Sep

Oct

Nov

Dec

1

07:09

07:09

06:52

06:24

06:00

05:49

05:53

06:05

06:15

06:23

06:34

06:53

2

07:09

07:08

06:51

06:23

06:00

05:49

05:53

06:05

06:15

06:23

06:35

06:53

3

07:10

07:08

06:50

06:22

05:59

05:49

05:54

06:06

06:16

06:23

06:36

06:54

4

07:10

07:07

06:49

06:21

05:59

05:49

05:54

06:06

06:16

06:24

06:36

06:55

5

07:10

07:07

06:48

06:21

05:58

05:49

05:54

06:07

06:16

06:24

06:37

06:55

6

07:10

07:06

06:48

06:20

05:57

05:49

05:55

06:07

06:16

06:24

06:37

06:56

7

07:11

07:06

06:47

06:19

05:57

05:49

05:55

06:07

06:17

06:24

06:38

06:56

8

07:11

07:06

06:46

06:18

05:56

05:49

05:56

06:08

06:17

06:25

06:38

06:57

9

07:11

07:05

06:45

06:17

05:56

05:49

05:56

06:08

06:17

06:25

06:39

06:58

10

07:11

07:05

06:44

06:16

05:55

05:49

05:56

06:08

06:17

06:25

06:39

06:58

11

07:11

07:04

06:43

06:15

05:55

05:49

05:57

06:09

06:18

06:26

06:40

06:59

12

07:11

07:03

06:42

06:15

05:54

05:49

05:57

06:09

06:18

06:26

06:41

07:00

13

07:11

07:03

06:41

06:14

05:54

05:49

05:57

06:09

06:18

06:26

06:41

07:00

14

07:11

07:02

06:41

06:13

05:54

05:49

05:58

06:10

06:18

06:27

06:42

07:01

15

07:11

07:02

06:40

06:12

05:53

05:49

05:58

06:10

06:19

06:27

06:42

07:01

16

07:11

07:01

06:39

06:11

05:53

05:49

05:59

06:10

06:19

06:28

06:43

07:02

17

07:11

07:00

06:38

06:10

05:52

05:50

05:59

06:11

06:19

06:28

06:44

07:02

18

07:11

07:00

06:37

06:10

05:52

05:50

05:59

06:11

06:19

06:28

06:44

07:03

19

07:11

06:59

06:36

06:09

05:52

05:50

06:00

06:11

06:20

06:29

06:45

07:04

20

07:11

06:58

06:35

06:08

05:51

05:50

06:00

06:12

06:20

06:29

06:45

07:04

21

07:11

06:58

06:34

06:07

05:51

05:50

06:01

06:12

06:20

06:29

06:46

07:05

22

07:11

06:57

06:33

06:07

05:51

05:51

06:01

06:12

06:20

06:30

06:47

07:05

23

07:11

06:56

06:32

06:06

05:50

05:51

06:01

06:12

06:21

06:30

06:47

07:06

24

07:11

06:56

06:31

06:05

05:50

05:51

06:02

06:13

06:21

06:31

06:48

07:06

25

07:11

06:55

06:31

06:04

05:50

05:51

06:02

06:13

06:21

06:31

06:49

07:06

26

07:10

06:54

06:30

06:04

05:50

05:52

06:03

06:13

06:21

06:32

06:49

07:07

27

07:10

06:53

06:29

06:03

05:50

05:52

06:03

06:14

06:22

06:32

06:50

07:07

28

07:10

06:52

06:28

06:02

05:49

05:52

06:03

06:14

06:22

06:33

06:51

07:08

29

07:10

06:27

06:02

05:49

05:52

06:04

06:14

06:22

06:33

06:51

07:08

30

07:09

06:26

06:01

05:49

05:53

06:04

06:14

06:22

06:33

06:52

07:08

31

07:09

06:25

05:49

06:05

06:15

06:34

07:09

Sunset Table for 2026

Location: Latitude 21.30000 Longitude -157.85000

Time Zone Offset: Pacific/Honolulu -10.0

All times are in local time. Cells with light green color indicate when daylight saving time is in effect.

Day

Jan

Feb

Mar

Apr

May

Jun

Jul

Aug

Sep

Oct

Nov

Dec

1

18:01

18:22

18:36

18:46

18:57

19:10

19:18

19:10

18:47

18:19

17:55

17:48

2

18:02

18:22

18:36

18:47

18:57

19:10

19:18

19:10

18:46

18:18

17:55

17:49

3

18:03

18:23

18:37

18:47

18:58

19:11

19:18

19:09

18:45

18:17

17:54

17:49

4

18:03

18:24

18:37

18:47

18:58

19:11

19:18

19:09

18:44

18:16

17:54

17:49

5

18:04

18:24

18:37

18:48

18:58

19:11

19:18

19:08

18:44

18:15

17:53

17:49

6

18:04

18:25

18:38

18:48

18:59

19:12

19:18

19:07

18:43

18:14

17:53

17:49

7

18:05

18:25

18:38

18:48

18:59

19:12

19:18

19:07

18:42

18:13

17:52

17:49

8

18:06

18:26

18:39

18:49

19:00

19:13

19:17

19:06

18:41

18:13

17:52

17:50

9

18:06

18:26

18:39

18:49

19:00

19:13

19:17

19:05

18:40

18:12

17:51

17:50

10

18:07

18:27

18:39

18:49

19:00

19:13

19:17

19:05

18:39

18:11

17:51

17:50

11

18:08

18:27

18:40

18:50

19:01

19:14

19:17

19:04

18:38

18:10

17:51

17:51

12

18:09

18:28

18:40

18:50

19:01

19:14

19:17

19:03

18:37

18:09

17:50

17:51

13

18:09

18:29

18:40

18:50

19:02

19:14

19:17

19:03

18:36

18:08

17:50

17:51

14

18:10

18:29

18:41

18:51

19:02

19:14

19:17

19:02

18:35

18:07

17:50

17:52

15

18:11

18:30

18:41

18:51

19:03

19:15

19:16

19:01

18:34

18:07

17:49

17:52

16

18:11

18:30

18:41

18:51

19:03

19:15

19:16

19:01

18:33

18:06

17:49

17:53

17

18:12

18:31

18:42

18:52

19:03

19:15

19:16

19:00

18:32

18:05

17:49

17:53

18

18:13

18:31

18:42

18:52

19:04

19:16

19:16

18:59

18:31

18:04

17:49

17:53

19

18:13

18:32

18:42

18:52

19:04

19:16

19:15

18:58

18:30

18:04

17:49

17:54

20

18:14

18:32

18:43

18:53

19:05

19:16

19:15

18:57

18:29

18:03

17:49

17:54

21

18:15

18:32

18:43

18:53

19:05

19:16

19:15

18:57

18:28

18:02

17:48

17:55

22

18:15

18:33

18:43

18:53

19:06

19:16

19:15

18:56

18:27

18:01

17:48

17:55

23

18:16

18:33

18:43

18:54

19:06

19:17

19:14

18:55

18:26

18:01

17:48

17:56

24

18:17

18:34

18:44

18:54

19:07

19:17

19:14

18:54

18:25

18:00

17:48

17:56

25

18:17

18:34

18:44

18:54

19:07

19:17

19:13

18:53

18:24

17:59

17:48

17:57

26

18:18

18:35

18:44

18:55

19:07

19:17

19:13

18:53

18:24

17:59

17:48

17:57

27

18:19

18:35

18:45

18:55

19:08

19:17

19:13

18:52

18:23

17:58

17:48

17:58

28

18:19

18:35

18:45

18:56

19:08

19:17

19:12

18:51

18:22

17:57

17:48

17:59

29

18:20

18:45

18:56

19:09

19:17

19:12

18:50

18:21

17:57

17:48

17:59

30

18:20

18:46

18:56

19:09

19:17

19:11

18:49

18:20

17:56

17:48

18:00

31

18:21

18:46

19:09

19:11

18:48

17:56

18:00

Solar Noon Table for 2026

Location: Latitude 21.30000 Longitude -157.85000

Time Zone Offset: Pacific/Honolulu -10.0

All times are in local time. Cells with light green color indicate when daylight saving time is in effect.

Day

Jan

Feb

Mar

Apr

May

Jun

Jul

Aug

Sep

Oct

Nov

Dec

1

12:34:56

12:44:58

12:43:43

12:35:15

12:28:31

12:29:15

12:35:18

12:37:46

12:31:26

12:21:06

12:14:56

12:20:24

2

12:35:24

12:45:06

12:43:31

12:34:57

12:28:24

12:29:25

12:35:29

12:37:42

12:31:07

12:20:46

12:14:55

12:20:47

3

12:35:52

12:45:13

12:43:19

12:34:40

12:28:18

12:29:35

12:35:40

12:37:37

12:30:48

12:20:27

12:14:54

12:21:10

4

12:36:19

12:45:19

12:43:06

12:34:22

12:28:12

12:29:45

12:35:51

12:37:32

12:30:28

12:20:09

12:14:55

12:21:34

5

12:36:46

12:45:24

12:42:52

12:34:05

12:28:07

12:29:55

12:36:01

12:37:26

12:30:08

12:19:50

12:14:56

12:21:59

6

12:37:13

12:45:28

12:42:38

12:33:48

12:28:02

12:30:06

12:36:12

12:37:19

12:29:48

12:19:32

12:14:58

12:22:24

7

12:37:39

12:45:32

12:42:24

12:33:31

12:27:58

12:30:17

12:36:21

12:37:12

12:29:28

12:19:15

12:15:01

12:22:50

8

12:38:04

12:45:34

12:42:10

12:33:15

12:27:54

12:30:29

12:36:31

12:37:05

12:29:07

12:18:57

12:15:05

12:23:16

9

12:38:29

12:45:36

12:41:55

12:32:58

12:27:52

12:30:40

12:36:40

12:36:56

12:28:46

12:18:41

12:15:10

12:23:43

10

12:38:54

12:45:37

12:41:39

12:32:42

12:27:49

12:30:52

12:36:48

12:36:47

12:28:25

12:18:24

12:15:16

12:24:10

11

12:39:18

12:45:38

12:41:23

12:32:27

12:27:47

12:31:04

12:36:57

12:36:38

12:28:04

12:18:09

12:15:22

12:24:37

12

12:39:41

12:45:37

12:41:07

12:32:11

12:27:46

12:31:17

12:37:04

12:36:28

12:27:43

12:17:53

12:15:29

12:25:05

13

12:40:04

12:45:36

12:40:51

12:31:56

12:27:46

12:31:29

12:37:12

12:36:18

12:27:22

12:17:38

12:15:38

12:25:33

14

12:40:26

12:45:34

12:40:35

12:31:41

12:27:46

12:31:42

12:37:18

12:36:06

12:27:01

12:17:24

12:15:47

12:26:02

15

12:40:47

12:45:31

12:40:18

12:31:26

12:27:46

12:31:55

12:37:25

12:35:55

12:26:39

12:17:10

12:15:56

12:26:30

16

12:41:08

12:45:28

12:40:01

12:31:12

12:27:47

12:32:07

12:37:30

12:35:43

12:26:18

12:16:57

12:16:07

12:26:59

17

12:41:28

12:45:24

12:39:44

12:30:58

12:27:49

12:32:20

12:37:36

12:35:30

12:25:56

12:16:44

12:16:19

12:27:29

18

12:41:47

12:45:19

12:39:26

12:30:45

12:27:51

12:32:33

12:37:40

12:35:17

12:25:35

12:16:32

12:16:31

12:27:58

19

12:42:06

12:45:13

12:39:09

12:30:32

12:27:54

12:32:47

12:37:44

12:35:03

12:25:14

12:16:21

12:16:44

12:28:27

20

12:42:24

12:45:07

12:38:51

12:30:19

12:27:57

12:33:00

12:37:48

12:34:49

12:24:52

12:16:10

12:16:59

12:28:57

21

12:42:41

12:45:00

12:38:33

12:30:07

12:28:01

12:33:13

12:37:51

12:34:34

12:24:31

12:16:00

12:17:13

12:29:27

22

12:42:58

12:44:53

12:38:15

12:29:55

12:28:05

12:33:26

12:37:54

12:34:19

12:24:10

12:15:51

12:17:29

12:29:57

23

12:43:13

12:44:44

12:37:57

12:29:44

12:28:10

12:33:39

12:37:56

12:34:04

12:23:49

12:15:42

12:17:46

12:30:26

24

12:43:28

12:44:36

12:37:39

12:29:33

12:28:15

12:33:52

12:37:57

12:33:48

12:23:28

12:15:34

12:18:03

12:30:56

25

12:43:42

12:44:26

12:37:21

12:29:23

12:28:21

12:34:04

12:37:58

12:33:31

12:23:07

12:15:26

12:18:21

12:31:26

26

12:43:56

12:44:16

12:37:03

12:29:13

12:28:28

12:34:17

12:37:58

12:33:15

12:22:46

12:15:20

12:18:40

12:31:55

27

12:44:08

12:44:06

12:36:45

12:29:03

12:28:34

12:34:30

12:37:57

12:32:57

12:22:26

12:15:14

12:18:59

12:32:25

28

12:44:20

12:43:55

12:36:27

12:28:54

12:28:42

12:34:42

12:37:56

12:32:40

12:22:05

12:15:09

12:19:19

12:32:54

29

12:44:31

12:36:09

12:28:46

12:28:50

12:34:54

12:37:55

12:32:22

12:21:45

12:15:04

12:19:40

12:33:23

30

12:44:41

12:35:51

12:28:38

12:28:58

12:35:06

12:37:52

12:32:04

12:21:25

12:15:01

12:20:02

12:33:52

31

12:44:50

12:35:33

12:29:06

12:37:49

12:31:45

12:14:58

12:34:21

Global Monitoring Laboratory

» U.S. Department of Commerce

» National Oceanic & Atmospheric Administration

» NOAA Research
```

---

### 25. Offshore Forecast (40-240nm)

| Field | Value |
|---|---|
| **Resource ID** | off_offshore_forecast |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=OFF&issuedby=HFO |
| **Collected** | 2026-09-29T05:30:03.082714-10:00 HST |

```text
895
FZHW60 PHFO 291516
OFFHFO

Offshore Waters Forecast for Hawaii
National Weather Service Honolulu HI
516 AM HST Tue Sep 29 2026

Hawaiian offshore waters beyond 40 nautical miles out to 240
nautical miles including the portion of the Papahanaumokuakea
Marine National Monument east of French Frigate Shoals

Seas given as significant wave height, which is the average height
of the highest 1/3 of the waves. Individual waves may be more than
twice the significant wave height.

PHZ105-292230-
516 AM HST Tue Sep 29 2026

.Synopsis for the Hawaiian offshore waters...
The center of Hurricane Nolo will track N along the W edge of the
offshore waters today. Strong high pressure N of the area will
maintain moderate to fresh E to SE winds outside of the Nolo wind
field during this time. Nolo will then turn W slowly on Wednesday
and exit the offshore waters by Thursday. Easterly trade winds
return by the end of the week.

AT 500 AM HST HURRICANE NOLO WAS CENTERED AT 20.5N 164.2W...MOVING N
AT 8 KT

NOLO FORECAST POSITIONS
200 PM HST TUESDAY 21.7N 164.3W
200 AM HST WEDNESDAY 22.3N 164.5W
200 PM HST WEDNESDAY 22.2N 165.0W
200 AM HST THURSDAY 22.0N 165.7W
200 PM HST THURSDAY 22.3N 166.5W
200 AM HST FRIDAY 22.6N 167.3W
200 AM HST SATURDAY 23.0N 169.4W
200 AM HST SUNDAY 23.9N 175.8W
200 AM HST MONDAY 25.8N 178.4E
200 AM HST TUESDAY 26.3N 172.7E

PHZ180-292230-
Hawaiian Offshore Waters-
516 AM HST Tue Sep 29 2026

...HURRICANE WARNING IN EFFECT...

.TODAY...Hurricane conditions expected S of 25N W of 162W.
Elsewhere NW half, E to SE winds 15 to 30 kt and seas 8 to 14 ft.
SE half, E to SE winds 10 to 20 kt and seas 6 to 8 ft. Isolated
thunderstorms near Hurricane Nolo.
.TONIGHT...Hurricane conditions expected N of 20N W of 162W.
Elsewhere NW half, SE to S winds 15 to 30 kt and seas 8 to 14 ft.
SE half, E to SE winds 10 to 20 kt and seas 6 to 8 ft. Isolated
thunderstorms near Hurricane Nolo.
.WEDNESDAY...Hurricane conditions expected W of 162W. Elsewhere
NW half, SE to S winds 15 to 30 kt and seas 8 to 12 ft. SE half, E
to SE winds 10 to 20 kt and seas 6 to 8 ft. Isolated
thunderstorms near Hurricane Nolo.
.WEDNESDAY NIGHT...Tropical storm conditions possible W of 163W.
Elsewhere NW half, SE to S winds 15 to 30 kt and seas 7 to 12 ft.
SE half, E to SE winds 10 to 15 kt and seas 6 ft. Isolated
thunderstorms near Hurricane Nolo.
.THURSDAY...W of 160W, SE to S winds 15 to 30 kt and seas 7 to 11
ft. Elsewhere, E to SE winds 10 to 15 kt and seas 5 to 7 ft.
.FRIDAY...NW half, SE winds 15 to 25 kt and seas 6 to 9 ft. SE
half, E to SE winds 10 to 15 kt and seas 6 ft or less.
.SATURDAY...NE to SE winds 10 to 20 kt. Seas 6 to 7 ft.
```

---

### 26. Radar status/outage text messages

| Field | Value |
|---|---|
| **Resource ID** | ftm_radar_status |
| **Official source** | https://www.weather.gov/hfo/FTM |
| **Collected** | 2026-09-29T01:50:24.670225-10:00 HST |

```text
Kauai Radar (PHKI/SOK)
No outage message at this time.

----

Molokai Radar (PHMO/HMO)
858
NOUS60 PHFO 242239
FTMHMO

WSR-88D NOTIFICATION
NATIONAL WEATHER SERVICE HONOLULU HI
1239 PM HST THU SEP 24 2026

WSR-88D PHMO/HMO MOLOKAI RADAR IS BACK IN SERVICE.

----

Upolu Point/North Kohala Radar (PHKM/UPP)
646
NOUS60 PHFO 252159
FTMHKM

WSR-88D NOTIFICATION
NATIONAL WEATHER SERVICE HONOLULU HI
1159 AM HST FRI SEP 25 2026

WSR-88D PHKM/UPP UPOLU POINT RADAR IS BACK IN SERVICE.

LF

----

Naalehu/South Hawaii (PHWA/HWC)
No outage message at this time.
```

---

### 27. State Forecast for Hawaii

| Field | Value |
|---|---|
| **Resource ID** | sfp_state_forecast |
| **Official source** | https://api.weather.gov/products/types/SFP/locations/HFO |
| **Collected** | 2026-09-29T03:48:32.081658-10:00 HST |

```text
000
FPHW60 PHFO 291342
SFPHFO

State Forecast for Hawaii
National Weather Service Honolulu HI
342 AM HST Tue Sep 29 2026

HIZ001-003-004-006-007-009>011-015>018-022-029>050-300415-
Kauai-Oahu-Maui-Molokai-Lanai-
342 AM HST Tue Sep 29 2026

...HIGH SURF ADVISORY FOR NIIHAU AND KAUAI...

.TODAY...Partly sunny. Breezy. Windward and mountains, isolated
showers. Leeward, numerous showers in the morning. Isolated
showers in the afternoon. Highs 86 to 91. Southeast winds 15 to
25 mph. 
.TONIGHT...Breezy. Frequent showers windward and mountains.
isolated showers leeward. Lows 74 to 79. Southeast winds 15 to
25 mph. 
.WEDNESDAY...Mostly cloudy. On Kauai, frequent showers during the
day, then scattered showers at night. Oahu and Maui County,
scattered showers. Highs 85 to 90. Lows 74 to 79. Southeast winds
15 to 20 mph. 
.THURSDAY...Mostly cloudy. Windward and mountains, scattered
showers. Leeward, scattered showers during the day, then isolated
showers at night. Highs 84 to 89. Lows 73 to 78. Southeast winds
around 15 mph. 
.FRIDAY...Partly cloudy. On Kauai, scattered showers. Oahu and
Maui County, isolated showers during the day. Scattered showers
at night. Highs 84 to 89. Lows 72 to 77. East winds around
15 mph. 
.SATURDAY...Partly cloudy. Scattered showers windward and
mountains. isolated showers leeward. Highs 84 to 89. Lows 72 to
77. East winds around 15 mph. 

HIZ023-026>028-051>054-300415-
Big Island of Hawaii-
342 AM HST Tue Sep 29 2026

.TODAY...Partly sunny. Isolated showers in the afternoon. Highs
85 to 90. Variable winds to 15 mph becoming southeast around
15 mph in the afternoon. 
.TONIGHT...Mostly cloudy in the evening then clearing. Isolated
showers. Lows 72 to 77. Variable winds to 15 mph becoming south
around 15 mph after midnight. 
.WEDNESDAY...Mostly cloudy. Leeward, isolated showers during the
day. Windward, isolated showers during the day. Scattered showers
at night. Highs 85 to 90. Lows 72 to 77. East winds around
15 mph. 
.THURSDAY...Mostly cloudy. Windward, scattered showers during the
day. Leeward, isolated showers during the day. Highs 84 to 89.
Lows 71 to 76. Variable winds to 15 mph. 
.FRIDAY...Mostly cloudy. Leeward, isolated showers. Windward,
scattered showers at night. Highs 83 to 88. Lows 71 to 76.
Variable winds to 15 mph. 
.SATURDAY...Partly cloudy. Leeward, isolated showers during the
day. Windward, scattered showers. Highs 84 to 89. Lows 71 to 76.
Northeast winds around 15 mph.
```

---

### 28. Statewide Surf Observations

| Field | Value |
|---|---|
| **Resource ID** | surfreports_statewide_observations |
| **Official source** | https://www.weather.gov/hfo/surfreports |
| **Collected** | Unknown HST |

```text
                        
325
SXHW80 PHFO 290115
OMRHFO

SURF OBSERVATIONS
NATIONAL WEATHER SERVICE HONOLULU HI
315 PM HST MON SEP 28 2026

FULL FACE SURF OBSERVATIONS ARE TAKEN BY COUNTY LIFE GUARDS AND
COOPERATIVE OBSERVERS AND RELAYED TO THE NATIONAL WEATHER SERVICE
FOR DISSEMINATION. THESE OBSERVATIONS ARE NOT QUALITY CONTROLLED.

HIZ003-004-029>031-290100-
KAUAI-

LOCATION        TIME   SURF HEIGHT DIR   PER                  REMARKS
KEE
HAENA        1230 PM           4-8  NE    10
HANALEI      1230 PM           3-5 NNE    10
ANAHOLA
KEALIA
LYDGATE
POIPU
SALT POND
KEKAHA
$$

HIZ006-007-009>011-032>036-290100-
OAHU-

LOCATION        TIME   SURF HEIGHT DIR PER         WIND      REMARKS
DIAMOND HEAD
SUNSET
WAIKIKI       123 PM           3-4             NE 15-20       CANOES
SANDY BEACH   123 PM           4-6             NE 20-25  SHORE BREAK
MAKAPUU       123 PM           3-5             NE 15-25
EHUKAI        123 PM           3-4             NE 10-15
MAKAHA        123 PM           2-3             NE 20-25
$$

HIZ015>018-022-045>050-290100-
MAUI-MOLOKAI-LANAI-KAHOOLAWE-

LOCATION        TIME   SURF HEIGHT   DIR         WIND      REMARKS
KANAHA        135 PM           2-3            E 15-25  PARTLY CLDY
BALDWIN SHOR  137 PM           2-4           NE 15-30 MOSTLY SUNNY
BALDWIN OUTE  137 PM           6-8           NE 15-30 MOSTLY SUNNY
HOOKIPA       151 PM          8-10        TRADE 15-20        SUNNY
KAMAOLE I     149 PM           2-4           VRB 5-10  PARTLY CLDY
KAMAOLE III   150 PM           2-4             S 5-10        SUNNY
HANAKAOO      153 PM           2-3     S        S 5-1  PARTLY CLDY
FLEMING
$$

HIZ023-026>028-051>054-290100-
BIG ISLAND OF HAWAII-

LOCATION        TIME   SURF HEIGHT   DIR         WIND      REMARKS
RICHARDSONS   127 PM           3-4            NE 5-10  PARTLY CLDY
HONOLII       129 PM           2-3           SE 10-20        SUNNY
PUNALU`U
ISAAC HALE    130 PM    4-5 CHOPPY           L/V 5-10        SUNNY
HAPUNA        131 PM           3-5            L/V 0-5        SUNNY
KAHALUU       132 PM           3-4           NW 10-15        SUNNY
MAGIC SANDS   133 PM    4-5 OCNL 6           NW 10-15 MOSTLY SUNNY
KUA BAY       134 PM           1-3               W 10 MOSTLY SUNNY
$$

LEGEND
   SURF HEIGHT              - Reported in feet
   WIND AND SWELL DIRECTION - Reported in 16 pt compass
   PERIOD /PER/             - Reported in seconds
   VISIBILITY /VIS/         - Reported in statute miles
   CLARITY                  - Water clarity
   TIME                     - Hawaiian Standard Time
   WIND SPEED               - Reported in miles per hour
   + /IN SURF HEIGHT/       - Occasionally higher sets
   0 /IN SURF HEIGHT/       - Flat

$$
```

---

### 29. Tsunami Bulletin product type reference

| Field | Value |
|---|---|
| **Resource ID** | hfo_tib_reference |
| **Official source** | https://forecast.weather.gov/product_types.php |
| **Collected** | 2026-09-29T06:30:31.471669-10:00 HST |

```text
National Weather Service

Toggle navigation

HOME

FORECAST

Local

Graphical

Aviation

Marine

Rivers and Lakes

Hurricanes

Severe Weather

Fire Weather

Sunrise/Sunset

Long Range Forecasts

Climate Prediction

Space Weather

PAST WEATHER

Past Weather

Astronomical Data

Certified Weather Data

SAFETY

INFORMATION

Wireless Emergency Alerts

Weather-Ready Nation

Brochures

Cooperative Observers

Daily Briefing

Damage/Fatality/Injury Statistics

Forecast Models

GIS Data Portal

NOAA Weather Radio

Publications

SKYWARN Storm Spotters

StormReady

TsunamiReady

Service Change Notices

EDUCATION

NEWS

SEARCH

Search For

NWS

All NOAA

ABOUT

About NWS

Organization

For NWS Employees

National Centers

Careers

Contact Us

Glossary

Social Media

NWS Transformation

NWS Weather Forecast Office Product Listing

Click on the product identifier or description to view products:

Product Identifier

Product Description

ABV

Rawinsonde Data Above 100 Millibars

ADA

Alarm/Alert Administrative Msg

ADM

Alert Administrative Message

ADR

NWS Administrative Message

ADV

Generic Space Environment Advisory

AFD

Area Forecast Discussion

AFM

Area Forecast Matrices

AFP

Area Forecast Product

AFW

Fire Weather Matrix

AGF

Agricultural Forecast

AGO

Agricultural Observations

ALT

Space Environment Alert

AQA

Air Quality Alert

AQI

Air Quality Index Statement

ASA

Air Stagnation Advisory

AVA

Avalanche Watch

AVG

Avalanche Weather Guidance

AVW

Avalanche Warning

AWO

Area Weather Outlook

AWS

Area Weather Summary

AWU

Area Weather Update

AWW

Airport Weather Warning

BLU

Blue Alert

BOY

Buoy Report

BRG

Coast Guard Observations

BRT

Hourly Roundup for Weather Radio

CAE

Child Abduction Emergency

CCF

Coded City Forecast

CDW

Civil Danger Warning

CEM

Civil Emergency Message

CF6

WFO Monthly/Daily Climate Data

CFP

Convective Forecast Product

CFW

Coastal Flood Warnings/Watches/Statements

CGR

Coast Guard Surface Report

CHG

Computer Hurricane Guidance

CLA

Climatological Report (Annual)

CLI

Climatological Report (Daily)

CLM

Climatological Report (Monthly)

CLQ

Climatological Report (Quarterly)

CLS

Climatological Report (Seasonal)

CLT

Climate Report

CMM

Coded Climatological Monthly Means

COD

Coded Analysis and Forecasts

CPF

Great Lakes Port Forecast

CUR

Routine Space Environment Products

CWA

Center (CWSU) Weather Advisory

CWF

Coastal Waters Forecast

CWS

Center (CWSU) Weather Statement

DAY

Routine Space Environment Product (Daily)

DDO

Daily Dispersion Outlook

DGT

Drought Information Statement

DMO

Practice/Demo Warning

DSA

Unnumbered Depression / Suspicious Area Advisory

DSM

ASOS Daily Summary

DSW

Dust Storm Warning and Dust Advisory

EFP

3 To 5 Day Extended Forecast

EOL

Average 6 To 10 Day Weather Outlook (Local)

EQI

Tsunami Bulletin

EQR

Earthquake Report

EQW

Earthquake Warning

ESF

Flood Potential Outlook

ESG

Extended Streamflow Guidance

ESP

Extended Streamflow Prediction

ESS

Water Supply Outlook

EVI

Evacuation Immediate

EWW

Extreme Wind Warning

FA0

Aviation Area Forecasts (Pacific)

FA1

Aviation Area Forecasts (Northeast)

FA2

Aviation Area Forecasts (Southeast)

FA3

Aviation Area Forecasts (North Central)

FA4

Aviation Area Forecasts (South Central)

FA5

Aviation Area Forecasts (Rocky Mountains)

FA6

Aviation Area Forecasts (West Coast)

FA7

Aviation Area Forecasts (Juneau, AK)

FA8

Aviation Area Forecasts (Anchorage, AK)

FA9

Aviation Area Forecasts (Fairbanks, AK)

FD0

24 Hr Fd Winds Aloft Fcst (45,000 and 53,000 Ft)

FD1

6 Hour Winds Aloft Forecast

FD2

12 Hour Winds Aloft Forecast

FD3

24 Hour Winds Aloft Forecast

FD4

Winds Aloft Forecast

FD5

Winds Aloft Forecast

FD6

Winds Aloft Forecast

FD7

Winds Aloft Forecast

FD8

6 Hour Fd Winds Aloft Fcst (45,000 and 53,000 Ft)

FD9

12 Hr Fd Winds Aloft Fcst (45,000 and 53,000 Ft)

FDI

Fire Danger Indices

FFA

Flash Flood Watch

FFG

Flash Flood Guidance

FFH

Headwater Guidance

FFS

Flash Flood Statement

FFW

Flash Flood Warning

FLN

National Flood Summary

FLS

Flood Statement

FLW

Flood Warning

FOF

Upper Wind Fallout Forecast

FRW

Fire Warning

FSH

Natl Marine Fisheries Administrative Service Message

FTM

WSR-88D Radar Outage Notification / Free Text Message

FTP

FOUS Prog Max/Min Temp/Pop Guidance

FWA

Fire Weather Administrative Message

FWD

Fire Weather Outlook Discussion

FWF

Routine Fire Wx Fcst (With/Without 6-10 Day Outlook)

FWL

Land Management Forecasts

FWM

Miscellaneous Fire Weather Product

FWN

Fire Weather Notification

FWO

Fire Weather Observation

FWS

Spot Forecast

FZL

Freezing Level Data (RADAT)

GLF

Great Lakes Forecast

GLS

Great Lakes Storm Summary

GRE

GREEN

HD1

RFC Derived QPF Data Product

HD2

RFC Derived QPF Data Product

HD3

RFC Derived QPF Data Product

HD4

RFC Derived QPF Data Product

HD7

RFC Derived QPF Data Product

HD8

RFC Derived QPF Data Product

HD9

RFC Derived QPF Data Product

HLS

Hurricane Local Statement

HMD

Hydrometeorological Discussion

HML

AHPS XML

HMW

Hazardous Materials Warning

HP1

RFC QPF Verification Product

HP2

RFC QPF Verification Product

HP3

RFC QPF Verification Product

HP4

RFC QPF Verification Product

HP5

RFC QPF Verification Product

HP6

RFC QPF Verification Product

HP7

RFC QPF Verification Product

HP8

RFC QPF Verification Product

HRR

Weather Roundup

HSF

High Seas Forecast

HWO

Hazardous Weather Outlook

HWR

Hourly Weather Roundup

HYD

Daily Hydrometeorological Products

HYM

Monthly Hydrometeorological Plain Language Product

ICE

Ice Forecast

IDM

Ice Drift Vectors

INI

ADMINISTR [NOUS51 KWBC]

IOB

Ice Observation

KPA

Keep Alive Message

LAE

Local Area Emergency

LCD

Preliminary Local Climatological Data

LCO

Local Cooperative Observation

LEW

Law Enforcement Warning

LFP

Local Forecast

LKE

Lake Stages

LLS

Low-Level Sounding

LOW

Low Temperatures

LSR

Local Storm Report

LTG

Lightning Data

MAN

Rawinsonde Observation Mandatory Levels

MAP

Mean Areal Precipitation

MAW

Amended Marine Forecast

MFM

Marine Forecast Matrix

MIM

Marine Interpretation Message

MIS

Miscellaneous Local Product

MOB

MOB Observations

MON

Routine Space Environment Product Issued Monthly

MRP

Techniques Development Laboratory Marine Product

MSM

ASOS Monthly Summary Message

MTR

METAR Formatted Surface Weather Observation

MTT

METAR Test Message

MVF

Marine Verification Coded Message

MWS

Marine Weather Statement

MWW

Marine Weather Message

NOU

Weather Reconnaisance Flights

NOW

Short Term Forecast

NOX

Data Mgt Message

NPW

Non-Precipitation Warnings / Watches / Advisories

NSH

Nearshore Marine Forecast

NUW

Nuclear Power Plant Warning

NWR

NOAA Weather Radio Forecast

OAV

Other Aviation Products

OBS

Observations

OFA

Offshore Aviation Area Forecast

OFF

Offshore Forecast

OMR

Other Marine Products

OPU

Other Public Products

OSO

Other Surface Observations

OSW

Ocean Surface Winds

OUA

Other Upper Air Data

OZF

Zone Forecast

PFM

Point Forecast Matrices

PFW

Fire Weather Point Forecast Matrices

PLS

Plain Language Ship Report

PMD

Prognostic Meteorological Discussion

PNS

Public Information Statement

POE

Probability of Exceed

PRB

Heat Index Forecast Tables

PRC

State Pilot Report Collective

PRE

Preliminary Forecasts

PSH

Post Storm Hurricane Report

PTS

Probabilistic Outlook Points

PWO

Public Severe Weather Outlook

PWS

Tropical Cyclone Probabilities

QPF

Quantitative Precipitation Forecast

QPS

Quantitative Precipitation Statement

RDF

Revised Digital Forecast

REC

Recreational Report

RER

Record Report

RET

EAS Activation Request

RFD

Rangeland Fire Danger Forecast

RFI

RFI Observation

RFR

Route Forecast

RFW

Red Flag Warning

RHW

Radiological Hazard Warning

RMT

Required Monthly Test

RNS

Rain Information Statement

RR1

Hydro-Met Data Report Part 1

RR2

Hydro-Met Data Report Part 2

RR3

Hydro-Met Data Report Part 3

RR4

Hydro-Met Data Report Part 4

RR5

Hydro-Met Data Report Part 5

RR6

Hydro-Met Data Report Part 6

RR7

Hydro-Met Data Report Part 7

RR8

Hydro-Met Data Report Part 8

RR9

Hydro-Met Data Report Part 9

RRA

Automated Hydrologic Observation Sta Report (AHOS)

RRM

Miscellaneous Hydrologic Data

RRS

HADS Data

RRY

ASOS SHEF Hourly Routine Test Message

RSD

Daily Snotel Data

RSM

Monthly Snotel Data

RTP

Regional Max/Min Temp and Precipitation Table

RVA

River Summary

RVD

Daily River Forecasts

RVF

River Forecast

RVI

River Ice Statement

RVM

Miscellaneous River Product

RVR

River Recreation Statement

RVS

River Statement

RWR

Regional Weather Roundup

RWS

Regional Weather Summary

RWT

Required Weekly Test

SAB

Special Avalanche Bulletin

SAF

Speci Agri Wx Fcst / Advisory / Flying Farmer Fcst Outlook

SAG

Snow Avalanche Guidance

SAT

APT Prediction

SAW

Prelim Notice of Watch & Cancellation Msg (Aviation)

SCC

Storm Summary

SCD

Supplementary Climatological Data (ASOS)

SCN

Soil Climate Analysis Network Data

SCP

Satellite Cloud Product

SCS

Selected Cities Summary

SDO

Supplementary Data Observation (ASOS)

SDS

Special Dispersion Statement

SEL

Severe Local Storm Watch and Watch Cancellation Msg

SEV

SPC Watch Point Information Message

SFP

State Forecast

SFT

Tabular State Forecast

SGL

Rawinsonde Observation Significant Levels

SHP

Surface Ship Report at Synoptic Time

SIG

International Sigmet / Convective Sigmet

SIM

Satellite Interpretation Message

SLS

Severe Local Storm Watch and Areal Outline

SMF

Smoke Management Weather Forecast

SMW

Special Marine Warning

SOO

SOO Product

SPE

Satellite Precipitation Estimates (TXUS20 KWBC)

SPF

Storm Strike Probability Bulletin (TPC)

SPS

Special Weather Statement

SPW

Shelter in Place Warning

SQW

Snow Squall Warning

SRD

Surf Discussion

SRF

Surf Forecast

SRG

Soaring Guidance

SSM

Main Synoptic Hour Surface Observation

STA

Network and Severe Weather Statistical Summaries

STD

Satellite Tropical Disturbance Summary

STO

Road Condition Reports (State Agencies)

STP

State Max/Min Temperature and Precipitation Table

STQ

Spot Forecast Request

SUM

Space Weather Message

SVR

Severe Thunderstorm Warning

SVS

Severe Weather Statement

SWO

Severe Storm Outlook Narrative (AC)

SWS

State Weather Summary

SYN

Regional Weather Synopsis

TAF

Terminal Aerodrome Forecast

TAP

Terminal Alerting Products

TAV

Travelers Forecast Table

TCA

Aviation Tropical Cyclone Advisory

TCD

Tropical Cyclone Discussion

TCE

Tropical Cyclone Position Estimate

TCM

Marine/Aviation Tropical Cyclone Advisory

TCP

Public Tropical Cyclone Advisory

TCS

Satellite Tropical Cyclone Summary

TCU

Tropical Cyclone Update

TCV

Tropical Cyclone Watch/Warning Break Points

TIB

Tsunami Bulletin

TID

Tide Report

TMA

Tsunami Tide/Seismic Message Acknowledgement

TOE

911 Telephone Outage Emergency

TOR

Tornado Warning

TPT

Temperature Precipitation Table (Natl and Intnl)

TSU

Tsunami Watch/Warning

TUV

Weather Bulletin

TVL

Travelers Forecast

TWB

Transcribed Weather Broadcast

TWD

Tropical Weather Discussion

TWO

Tropical Weather Outlook and Summary

TWS

Tropical Weather Summary

URN

Aircraft Reconnaissance

UVI

Ultraviolet Index

VAA

Volcanic Activity Advisory

VER

Forecast Verification Statistics

VFT

Terminal Aerodrome Forecast (TAF) Verification

VOW

Volcano Warning

WA0

Airmet (Pacific)

WA1

Airmet (Northeast)

WA2

Airmet (Southeast)

WA3

Airmet (North Central)

WA4

Airmet (South Central)

WA5

Airmet (Rocky Mountains)

WA6

Airmet (West Coast)

WA7

Airmet (Juneau, AK)

WA8

Airmet (Anchorage, AK)

WA9

Airmet (Fairbanks, AK)

WAR

Space Environment Warning

WAT

Space Environment Watch

WCN

Weather Watch Clearance Notification

WCR

Weekly Weather and Crop Report

WDA

Weekly Data for Agriculture

WDU

Warning Decision Update

WEK

Routine Space Environment Product Issued Weekly

WOU

Tornado/Severe Thunderstorm Watch

WS1

Sigmet (Northeast)

WS2

Sigmet (Southeast)

WS3

Sigmet (North Central)

WS4

Sigmet (South Central)

WS5

Sigmet (Rocky Mountains)

WS6

Sigmet (West Coast)

WST

Tropical Cyclone Sigmet

WSV

Volcanic Activity Sigmet

WSW

Winter Weather Warnings / Watches / Advisories

WWA

Watch Status Report

WWP

Severe Thunderstorm / Tornado Watch Probabilities

ZFP

Zone Forecast Product

US Dept of Commerce

National Oceanic and Atmospheric Administration

National Weather Service

1325 East West Highway

Silver Spring, MD 20910

Comments? Questions? Please Contact Us.

Disclaimer

Information Quality

Help

Glossary
```

---

_Generated automatically by the RootRecord weather reporting pipeline._
