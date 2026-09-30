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
| Honolulu | Cloudy | 81°F | 72°F | 74% | East 10 | 29.87F |
| Lihue | Rain | 79°F | 74°F | 84% | Southeast 22 gusts to 33 | 29.84F |
| Kahului | Partly cloudy | 71°F | 67°F | 87% | Calm | 29.88F |
| Hilo | Cloudy | 75°F | 69°F | 81% | Southwest 6 | 29.92F |
| Kona | Clear | 79°F | 67°F | 66% | East 6 | — |

_Source: locally collected NWS-HFO Regional Weather Roundup (RWR). Values are °F._

---

## 🌦️ Live Hawaiʻi Statewide Weather Report

> **Automatically regenerated from the latest locally collected official weather products.**

| Status | Coverage | Updated | Sections |
|---|---|---|---:|
| 🟢 Active | Hawaiʻi statewide | 2026-09-30T02:41:33-10:00 HST | 31 |

The report below is generated from the same current product sections as `Hawaii_State_Weather_Report_current.md`.

---

### 1. AIRMETs

| Field | Value |
|---|---|
| **Resource ID** | wa0_airmets |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=WA0&issuedby=HI |
| **Collected** | 2026-09-29T23:41:53.877770-10:00 HST |

```text
306
WAHW31 PHFO 300926
WA0HI

HNLS WA 301000
AIRMET SIERRA UPDATE 2 FOR IFR VALID UNTIL 301600
.
AIRMET MTN OBSC...KAUAI
ENTIRE AREA.
TEMPO MTN OBSC ABV 020 EXP DUE TO CLD AND SHRA.
COND CONT BEYOND 1600Z.
.
AIRMET MTN OBSC...OAHU
N THRU E SECTIONS.
TEMPO MTN OBSC ABV 020 EXP DUE TO CLD AND SHRA.
COND CONT BEYOND 1600Z.

=HNLT WA 301000
AIRMET TANGO UPDATE 2 FOR TURB VALID UNTIL 301600
.
AIRMET TURB...KAUAI
OVER AND IMT W THRU N OF MTN.
TEMPO MOD TURB BLW 080.
COND CONT BEYOND 1600Z.

=HNLZ WA 301000
AIRMET ZULU UPDATE 1 FOR ICE AND FZLVL VALID UNTIL 301600
.
NO SIGNIFICANT ICE EXP.
.
FZLVL...153 PHLI SLOPING TO 166 PHTO.
```

---

### 2. Area Forecast (FA)

| Field | Value |
|---|---|
| **Resource ID** | fa0_area_forecast |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=FA0&issuedby=HI |
| **Collected** | 2026-09-30T02:18:00.677388-10:00 HST |

```text
306
WAHW31 PHFO 300926
WA0HI

HNLS WA 301000
AIRMET SIERRA UPDATE 2 FOR IFR VALID UNTIL 301600
.
AIRMET MTN OBSC...KAUAI
ENTIRE AREA.
TEMPO MTN OBSC ABV 020 EXP DUE TO CLD AND SHRA.
COND CONT BEYOND 1600Z.
.
AIRMET MTN OBSC...OAHU
N THRU E SECTIONS.
TEMPO MTN OBSC ABV 020 EXP DUE TO CLD AND SHRA.
COND CONT BEYOND 1600Z.

=HNLT WA 301000
AIRMET TANGO UPDATE 2 FOR TURB VALID UNTIL 301600
.
AIRMET TURB...KAUAI
OVER AND IMT W THRU N OF MTN.
TEMPO MOD TURB BLW 080.
COND CONT BEYOND 1600Z.

=HNLZ WA 301000
AIRMET ZULU UPDATE 1 FOR ICE AND FZLVL VALID UNTIL 301600
.
NO SIGNIFICANT ICE EXP.
.
FZLVL...153 PHLI SLOPING TO 166 PHTO.
```

---

### 3. Area Forecast Discussion

| Field | Value |
|---|---|
| **Resource ID** | afd_area_forecast_discussion |
| **Official source** | https://api.weather.gov/products/types/AFD/locations/HFO |
| **Collected** | 2026-09-29T23:18:24.145993-10:00 HST |

```text
000
FXHW60 PHFO 300643
AFDHFO

Area Forecast Discussion
National Weather Service Honolulu HI
840 PM HST Tue Sep 29 2026

.SYNOPSIS...
Hurricane Nolo will slowly track north to the west of the islands
and remain over the Papahanaumokuakea Marine National Monument 
through Wednesday. Nolo will take a westerly turn and move away 
from the state Thursday, nearing the International Date Line as a
Category 1 or Tropical Storm Sunday. Bands of showers along Nolo's 
eastern flank will move up from the south and pass across the 
islands the next few days with Oahu and Kauai likely picking up 
the higher rain totals. Breezy southeast winds will persist 
through Wednesday, weaken through late week and then transition 
back to trades by early next week.

.SHORT TERM UPDATE...
Category 1 Hurricane Nolo, located approximately 250 nautical 
miles west of Barking Sands Beach, Kauai, is slowly tracking north 
this evening. Nolo's far eastern outer bands are providing brief 
periods of light to moderate rain as they quickly pass over Kauai 
and Oahu from the south. This evening's rainfall amounts have been 
low with no more than quarter of an inch per hour rates at many west 
and central Kauai sites. These low amounts are primarily attributed 
to these rain cells passing north at 25 mph. While the bulk of the 
heaviest precipitation stays over the nearshore waters west of 
Niihau and Kauai, Nolo's more north-than-west motion will keep 
return periods of rain in the forecast for mainly the western third 
of the state through early Friday. Due to the quick passage of this 
rain, most areas will not experience any significant flooding 
concerns. Nuisance flooding of lower lying areas and street ponding 
may occur, especially over Oahu and Kauai, the next couple of days 
in the event that rainfall becomes more orientated to the background 
southeast flow and exhibits more of a training nature.

.AVIATION...
Moderate to breezy southeast winds will persist through Wednesday
as Hurricane Nolo gradually slides off to the west, away from the
state. Outer rain bands associated with Nolo will bring showers 
into mainly Kauai and Oahu from the south over the next 24 hours, 
with Kauai expecting the most coverage. MVFR and even IFR 
conditions will be possible within these showers. 

AIRMET Sierra is in effect for Kauai due to the clouds and showers
moving over the island from the south. This AIRMET will likely be
needed through Wednesday and may need to be expanded to Oahu. 

AIRMET Tango is in effect for low level turbulence west through
north of the island terrain over Kauai. 

.PREV DISCUSSION...
Issued at 309 PM HST Tue Sep 29 2026
Hurricane Nolo is around 310 miles west of Lihue this afternoon 
tracking north at 8 mph. Nolo is expected to briefly stall west of
the state tonight, then begin to move away to the west northwest.
Breezy southeast winds will continue across the state into 
Wednesday as Nolo remains close to the area.

While Nolo will not make direct impacts to the state, rain bands
along the eastern periphery will move in the southeast flow and
bring showers across Kauai and Oahu through Thursday. Expecting 
to see 3 to 6 inches of additional rain on Kauai and Niihau, and 
up to 4 inches on Oahu. Not considering a Flood Watch with the 
anticipation these rainfall amounts will be spread out over 
several days and showers should be moving along quickly. However, 
southeast flow will direct showers across the populated areas of 
both islands. The rest of the state will be under a hybrid east
southeast flow pattern where the Big Island will partially block
Maui County resulting in localized nighttime land that will clear
skies out and daytime sea breezes that will bring interior cloud 
cover. Precipitation across Maui County and Big Island will be
minimal.

East southeasterly winds will continue, but gradually weaken, 
through the second half of the week as Nolo tracks away. Winds
will back to moderate trades by the weekend.

On Monday and Tuesday, a weak front will push across the islands 
and stall near the Big Island through the remainder of the week.
Winds will taper off behind this front as a second front
approaches much slower. Lingering clouds and showers near the Big
Island and light winds statewide next week will result in a
diurnal land and sea breeze weather pattern.

.MARINE...
Issued at 309 PM HST Tue Sep 29 2026
Moderate to fresh SE winds prevails over area waters. Strong to 
near-gale SE flow will develop tonight into Wednesday around Kauai
due to Hurricane Nolo's close proximity. The Small Craft Advisory
remains in effect for these waters. Moderate trades return early 
next week.

The moderate, medium period SW swell originating from Nolo has
eased slightly with the latest observations coming in below the
High Surf Advisory (HSA). The HSA has therefore been allowed to
expire. Surf along E shores has declined in response to emerging 
SE flow. Surf will remain small until moderate trades return early
next week providing a modest boost. Multiple rounds of tiny swell
originating out of the northwest quadrant will reach north and 
select west facing exposures next week as the storm track in the 
vicinity of the Aleutian Islands becomes increasingly active.

.FIRE WEATHER...
Issued at 309 PM HST Tue Sep 29 2026
Fire conditions improving through the remainder of the week to due
an increase in moisture across the state and breezy southeast
winds.

.HFO WATCHES/WARNINGS/ADVISORIES...
Small Craft Advisory until 6 PM HST Wednesday for Kauai Channel-
Kauai Leeward Waters-Kauai Northwest Waters-Kauai Windward 
Waters.

DISCUSSION...Foster
AVIATION...Farris
MARINE...JVC
```

---

### 4. Daily Climate Summary — HNL

| Field | Value |
|---|---|
| **Resource ID** | cli_daily_climate_summary_HNL |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=HNL |
| **Collected** | 2026-09-29T22:04:57.404884-10:00 HST |

```text
086
CDHW40 PHFO 300245
CLIHNL

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
445 PM HST TUE SEP 29 2026

...................................

...THE HONOLULU CLIMATE SUMMARY FOR SEPTEMBER 29 2026...
VALID TODAY AS OF 0425 PM LOCAL TIME.

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1940 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 TODAY
  MAXIMUM         89    128 PM  93    1993  88      1       89
                                      2020
  MINIMUM         73    630 AM  66    1975  75     -2       78
  AVERAGE         81                        81      0       84

PRECIPITATION (IN)
  TODAY            0.00          0.46 1960   0.03  -0.03      T
  MONTH TO DATE    0.32                      0.86  -0.54     0.71
  SINCE SEP 1      0.32                      0.86  -0.54     0.71
  SINCE JAN 1     22.35                     10.45  11.90     9.59

DEGREE DAYS
 HEATING
  TODAY            0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  TODAY           16                        16      0       19
  MONTH TO DATE  526                       481     45      516
  SINCE SEP 1    526                       481     45      516
  SINCE JAN 1   3736                      3558    178     4001
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    16   HIGHEST WIND DIRECTION    SE (140)
  HIGHEST GUST SPEED    22   HIGHEST GUST DIRECTION    SE (140)
  AVERAGE WIND SPEED     7.0

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.3

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED TODAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    82           700 AM
 LOWEST     45           100 PM
 AVERAGE    64

..........................................................

THE HONOLULU CLIMATE NORMALS FOR TOMORROW
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   88        92      1988
 MINIMUM TEMPERATURE (F)   75        67      1981

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   622 AM HST   SUNSET   621 PM HST
SEPTEMBER 30 2026.....SUNRISE   623 AM HST   SUNSET   620 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 5. Daily Climate Summary — ITO

| Field | Value |
|---|---|
| **Resource ID** | cli_daily_climate_summary_ITO |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=ITO |
| **Collected** | 2026-09-29T22:07:26.995902-10:00 HST |

```text
087
CDHW43 PHFO 300245
CLIITO

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
445 PM HST TUE SEP 29 2026

...................................

...THE HILO/GEN.LYMAN FLD CLIMATE SUMMARY FOR SEPTEMBER 29 2026...
VALID TODAY AS OF 0425 PM LOCAL TIME.

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1949 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 TODAY
  MAXIMUM         85   1249 PM  89    1974  83      2       85
                                      2014
                                      2019
  MINIMUM         69    616 AM  64    1955  70     -1       70
  AVERAGE         77                        76      1       78

PRECIPITATION (IN)
  TODAY            0.00          3.09 1963   0.30  -0.30     0.02
  MONTH TO DATE   16.18                      8.42   7.76     2.76
  SINCE SEP 1     16.18                      8.42   7.76     2.76
  SINCE JAN 1    124.42                     83.41  41.01    38.14

DEGREE DAYS
 HEATING
  TODAY            0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  TODAY           12                        11      1       13
  MONTH TO DATE  377                       345     32      366
  SINCE SEP 1    377                       345     32      366
  SINCE JAN 1   2806                      2456    350     2867
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    17   HIGHEST WIND DIRECTION     E (90)
  HIGHEST GUST SPEED    24   HIGHEST GUST DIRECTION     E (110)
  AVERAGE WIND SPEED     9.2

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.2

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED TODAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    82          1200 AM
 LOWEST     62           800 AM
 AVERAGE    72

..........................................................

THE HILO/GEN.LYMAN FLD CLIMATE NORMALS FOR TOMORROW
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   83        88      1976
                                             2018
                                             2020
 MINIMUM TEMPERATURE (F)   70        61      1970

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   611 AM HST   SUNSET   610 PM HST
SEPTEMBER 30 2026.....SUNRISE   611 AM HST   SUNSET   609 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 6. Daily Climate Summary — LIH

| Field | Value |
|---|---|
| **Resource ID** | cli_daily_climate_summary_LIH |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=LIH |
| **Collected** | 2026-09-29T22:05:42.241817-10:00 HST |

```text
088
CDHW41 PHFO 300245
CLILIH

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
445 PM HST TUE SEP 29 2026

...................................

...THE LIHUE CLIMATE SUMMARY FOR SEPTEMBER 29 2026...
VALID TODAY AS OF 0425 PM LOCAL TIME.

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1950 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 TODAY
  MAXIMUM         85   1158 AM  88    1981  85      0       84
                                      2014
                                      2017
  MINIMUM         78    708 AM  65    1952  75      3       74
  AVERAGE         82                        80      2       79

PRECIPITATION (IN)
  TODAY            0.00          0.88 1986   0.09  -0.09     0.12
  MONTH TO DATE    3.13                      2.10   1.03     3.62
  SINCE SEP 1      3.13                      2.10   1.03     3.62
  SINCE JAN 1     42.92                     24.20  18.72    15.08

DEGREE DAYS
 HEATING
  TODAY            0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  TODAY           17                        15      2       14
  MONTH TO DATE  441                       435      6      447
  SINCE SEP 1    441                       435      6      447
  SINCE JAN 1   3144                      3069     75     3385
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    18   HIGHEST WIND DIRECTION     E (100)
  HIGHEST GUST SPEED    23   HIGHEST GUST DIRECTION     E (110)
  AVERAGE WIND SPEED    11.9

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.4

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED TODAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    79          1200 AM
 LOWEST     65          1200 PM
 AVERAGE    72

..........................................................

THE LIHUE CLIMATE NORMALS FOR TOMORROW
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   85        88      1981
                                             2014
                                             2017
 MINIMUM TEMPERATURE (F)   75        65      1968

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   628 AM HST   SUNSET   627 PM HST
SEPTEMBER 30 2026.....SUNRISE   629 AM HST   SUNSET   626 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 7. Daily Climate Summary — OGG

| Field | Value |
|---|---|
| **Resource ID** | cli_daily_climate_summary_OGG |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLI&issuedby=OGG |
| **Collected** | 2026-09-29T22:06:41.940363-10:00 HST |

```text
089
CDHW42 PHFO 300245
CLIOGG

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
445 PM HST TUE SEP 29 2026

...................................

...THE KAHULUI/MAUI CLIMATE SUMMARY FOR SEPTEMBER 29 2026...
VALID TODAY AS OF 0425 PM LOCAL TIME.

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1954 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 TODAY
  MAXIMUM         92    126 PM  93    1996  90      2       89
  MINIMUM         65    520 AM  63    1974  71     -6       75
                                      1975
                                      2002
  AVERAGE         79                        80     -1       82

PRECIPITATION (IN)
  TODAY            0.00          0.17 1987   0.02  -0.02     0.00
  MONTH TO DATE    0.60                      0.44   0.16     0.04
  SINCE SEP 1      0.60                      0.44   0.16     0.04
  SINCE JAN 1     30.28                     10.76  19.52     6.61

DEGREE DAYS
 HEATING
  TODAY            0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  TODAY           14                        15     -1       17
  MONTH TO DATE  468                       457     11      460
  SINCE SEP 1    468                       457     11      460
  SINCE JAN 1   3252                      3304    -52     3315
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    20   HIGHEST WIND DIRECTION     N (20)
  HIGHEST GUST SPEED    26   HIGHEST GUST DIRECTION    NE (30)
  AVERAGE WIND SPEED     7.3

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.1

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED TODAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    87           600 AM
 LOWEST     48          1100 AM
 AVERAGE    68

..........................................................

THE KAHULUI/MAUI CLIMATE NORMALS FOR TOMORROW
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   90        94      2022
 MINIMUM TEMPERATURE (F)   71        62      1962

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   616 AM HST   SUNSET   615 PM HST
SEPTEMBER 30 2026.....SUNRISE   617 AM HST   SUNSET   614 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 8. Hawaii Rainfall Summary

| Field | Value |
|---|---|
| **Resource ID** | rra_hawaii_rainfall_summary |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=RRA&issuedby=HFO |
| **Collected** | 2026-09-30T02:28:44.595579-10:00 HST |

```text
297
SRHW80 PHFO 301146
RRAHFO

Hawaii Rainfall Summary
National Weather Service Honolulu HI
145 AM HST Wed Sep 30 2026

:
.B HFO  0930 H  DH01 /DRH-03/PPT/DRH-06/PPQ/DRH-12/PPK/DRH-24/PPD
:
:Automated rain gage reports from around the State of Hawaii.
:These are provisional reports that have not been quality
:controlled.
:
:T=Trace Rainfall, M=Missing Data
:
:Precipitation totals ending  1 AM HST
:
:Island of Kauai                                   Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward/Mauka Sites
MKAH1 : Makaha Ridge (RAWS)         :    0.34  /  0.47  /  0.52  /  0.52
PLRH1 : Puu Lua (RAWS)              :    0.78  /  0.91  /  1.18  /  1.18
WKRH1 : Waiakoali (USGS)            :    0.76  /  1.18  /  1.31  /  1.31
KLOH1 : Kilohana (USGS)             :    0.42  /  0.74  /  0.84  /  0.84
MCRH1 : Mohihi Crossing (USGS)      :    0.67  /  1.08  /  1.31  /  1.31
WLGH1 : Waialae (USGS)              :    0.57  /  1.22  /  1.31  /  1.31
LLMH1 : Lower Limahuli (UHM)        :    0.14  /  0.29  /  0.30  /  0.30
WNHH1 : Wainiha (12010)             :    0.02  /  0.17  /  0.28  /  0.28
WIPH1 : Waipa (UHM)                 :    0.21  /  0.55  /  0.63  /  0.63
HNIH1 : Hanalei (12009)             :    0.64  /  1.01  /  1.13  /  1.13
WLLH1 : Mount Waialeale (USGS)      :      M   /    M   /    M   /    M
PRIH1 : Princeville Airport (12011) :    0.09  /  0.38  /  0.63  /  0.63
CMGH1 : Common Ground (UHM)         :    0.22  /  0.48  /  0.72  /  0.72
HLIH1 : Hanalei (RAWS)              :    0.51  /  0.61  /  0.63  /  0.63
MLDH1 : Moloaa Dairy (RAWS)         :    0.00  /  0.00  /  0.00  /  0.00
ANHH1 : Anahola (12001)             :      M   /    M   /    M   /    M
KPIH1 : Kapahi (12003)              :    0.00  /  0.24  /  0.40  /  0.40
WLDH1 : N Wailua Ditch (USGS)       :    0.77  /  1.45  /  1.60  /  1.64
WUHH1 : Wailua (12005)              :    0.22  /  0.38  /  0.58  /  0.58
WIRH1 : Waiahi Rain Gage (USGS)     :    0.11  /  0.67  /  0.82  /  0.82
LIHH1 : Lihue Var. Stn. (12006)     :    0.05  /  0.16  /  0.24  /  0.24
HNMH1 : Hanamaulu (UHM)             :    0.21  /  1.02  /  1.10  /  1.10
HLI   : Lihue Airport (ASOS)        :    0.16  /  0.24  /  0.30  /  0.30
:       Leeward Sites
OMAH1 : Omao (12004)                :    0.28  /  0.31  /  0.38  /  0.38
LNTH1 : Lawai NTBG (UHM)            :    0.22  /  0.26  /  0.28  /  0.28
KHEH1 : Kalaheo (12008)             :    0.46  /  0.51  /  0.54  /  0.54
PAKH1 : Port Allen (HSOIS)          :    0.19  /  0.31  /  0.53  /  0.53
HNPH1 : Hanapepe (12002)            :    0.36  /  0.49  /  0.75  /  0.75
POPH1 : Puu Opae (RAWS)             :    0.70  /  0.89  /  1.10  /  1.10
WHGH1 : Waimea Heights (RAWS)       :    0.44  /  0.54  /  0.98  /  0.98
WMTH1 : Waimea Tank (12007)         :    0.45  /  0.51  /  0.96  /  0.96
MNRH1 : Mana (RAWS)                 :    0.52  /  0.53  /  0.73  /  0.73
:
:Island of Oahu                                    Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward/Mauka Sites
KAHH1 : Kahuku (13027)              :    0.47  /  0.47  /  0.47  /  0.47
KTAH1 : Kahuku Training Area (RAWS) :    0.00  /  0.00  /  0.01  /  0.01
KFWH1 : Kii (RAWS)                  :    0.00  /  0.00  /  0.00  /  0.00
PUNH1 : Punaluu Pump (13013)        :    0.17  /  0.18  /  0.18  /  0.18
PNSH1 : Punaluu Stream (USGS)       :    0.19  /  0.21  /  0.25  /  0.25
KNRH1 : Kahana (USGS)               :    0.01  /  0.01  /  0.01  /  0.01
HAKH1 : Hakipuu Mauka (13004)       :    0.00  /  0.00  /  0.00  /  0.00
WPPH1 : Waihee Pump (13002)         :    0.00  /  0.00  /  0.00  /  0.00
WHSH1 : Waiahole (USGS)             :    0.00  /  0.00  /  0.00  /  0.00
OFRH1 : Oahu Forest NWR (USFWS)     :    0.00  /  0.00  /  0.00  /  0.00
AHUH1 : Ahuimanu Loop (13005)       :    0.00  /  0.00  /  0.00  /  0.00
HRRH1 : Heeia NERR (NOAA/NOS)       :    0.01  /  0.01  /  0.01  /  0.01
LULH1 : Luluku (13016)              :    0.00  /  0.00  /  0.00  /  0.00
NRSH1 : Nuuanu Res No. 1 (UHM)      :    0.00  /  0.00  /  0.00  /  0.00
KWIH1 : Kalawahine (UHM)            :    0.00  /  0.00  /  0.00  /  0.00
LYOH1 : Lyon (UHM)                  :    0.00  /  0.00  /  0.00  /  0.00
MNLH1 : Manoa Lyon Arboretum (13023):    0.00  /  0.00  /  0.00  /  0.00
STVH1 : St. Stephens (13006)        :    0.00  /  0.00  /  0.00  /  0.00
MAUH1 : Maunawili (13008)           :      M   /    M   /    M   /    M
OFSH1 : Olomana Fire Station (13009):    0.00  /  0.00  /  0.00  /  0.00
WMLH1 : Waimanalo (13011)           :    0.00  /  0.00  /  0.00  /  0.00
BELH1 : Bellows AFS (HSOIS)         :    0.00  /  0.00  /  0.00  /  0.00
KMHH1 : Kamehame (13012)            :    0.00  /  0.00  /  0.00  /  0.00
HAJH1 : Hawaii Kai Golf Crse (13015):    0.00  /  0.00  /  0.00  /  0.00
:       Leeward/Central Sites
KUXH1 : Kaluanui (UHM)              :    0.00  /  0.00  /  0.00  /  0.00
NIUH1 : Niu Valley (13001)          :    0.00  /  0.00  /  0.00  /  0.00
PFSH1 : Palolo Fire Station (13010) :    0.00  /  0.00  /  0.00  /  0.00
HNL   : Honolulu Airport (ASOS)             See note at bottom  :
MOAH1 : Moanalua (13003)            :    0.00  /  0.00  /  0.00  /  0.00
MOGH1 : Moanalua RG (USGS)          :    0.00  /  0.00  /  0.00  /  0.00
TNLH1 : Tunnel RG (USGS)            :    0.00  /  0.00  /  0.00  /  0.00
PACH1 : Palisades (13020)           :    0.00  /  0.00  /  0.00  /  0.00
WAWH1 : Waiawa C.F. (13025)         :    0.00  /  0.00  /  0.00  /  0.00
MITH1 : Mililani (13022)            :    0.00  /  0.00  /  0.00  /  0.00
SCBH1 : Schofield Barracks (RAWS)   :    0.00  /  0.00  /  0.00  /  0.00
SCEH1 : Schofield East (RAWS)       :    0.00  /  0.00  /  0.00  /  0.00
WAFH1 : Wheeler Airfield            :    0.00  /  0.00  /  0.00  /  0.00
POAH1 : Poamoho (13018)             :    0.00  /  0.00  /  0.00  /  0.00
KRGH1 : Kalahee Ridge (UHM)         :    0.00  /  0.00  /  0.00  /  0.00
KMRH1 : Kamananui Stream (USGS)     :    0.00  /  0.00  /  0.00  /  0.00
PPRH1 : Pupukea Road (USGS)         :    0.00  /  0.00  /  0.00  /  0.00
PMHH1 : Poamoho RG 1 (USGS)         :    0.23  /  0.34  /  0.61  /  0.61
DLGH1 : Dillingham (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
AALH1 : Kaala (UHM)                 :    0.01  /  0.01  /  0.01  /  0.01
PECH1 : Waipio (13019)              :    0.00  /  0.00  /  0.00  /  0.00
KUNH1 : Kunia Substation (13021)    :    0.00  /  0.00  /  0.00  /  0.00
HOFH1 : Honouliuli (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
PTWH1 : Ewa Beach USGS (13024)      :    0.00  /  0.00  /  0.00  /  0.00
HJR   : Kalaeloa Airport (ASOS)             See note at bottom  :
PLHH1 : Palehua (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
LUAH1 : Lualualei (13017)           :    0.00  /  0.00  /  0.00  /  0.00
WNVH1 : Waianae Valley (RAWS)       :    0.00  /  0.00  /  0.00  /  0.00
WBHH1 : Waianae Boat Harbor (HSOIS) :    0.00  /  0.00  /  0.00  /  0.00
WAIH1 : Waianae (13014)             :    0.00  /  0.00  /  0.00  /  0.00
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
WWKH1 : West Wailuaiki (USGS)       :    0.00  /  0.00  /  0.00  /  0.00
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
KHIH1 : Kihei #2 (14009)            :      M   /    M   /    M   /    M
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
KWSH1 : Kawainui Stream (USGS)      :    0.00  /  0.00  /  0.00  /  0.01
KUUH1 : Kamuela Upper (15002)       :    0.00  /  0.00  /  0.00  /  0.00
KMUH1 : Kamuela (15005)             :    0.00  /  0.00  /  0.00  /  0.00
HNKH1 : Honokaa (15010)             :    0.00  /  0.00  /  0.00  /  0.00
PMLH1 : Puu Mali (RAWS)             :    0.00  /  0.00  /  0.00  /  0.00
WPNH1 : Waipunalei (UHM)            :      M   /    M   /    M   /  0.00
KNKH1 : Kanakaleonui (UHM)          :    0.00  /  0.00  /  0.01  /  0.01
LPHH1 : Laupahoehoe PD (15001)      :    0.00  /  0.00  /  0.00  /  0.00
LAUH1 : Laupahoehoe (UHM)           :    0.00  /  0.00  /  0.00  /  0.00
SPNH1 : Spencer (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
HKUH1 : Hakalau (RAWS)              :    0.01  /  0.01  /  0.01  /  0.01
KLXH1 : Kulaimano (UHM)             :    0.00  /  0.00  /  0.00  /  0.00
NLIH1 : Honolii Stream (USGS)       :    0.02  /  0.02  /  0.02  /  0.02
SDQH1 : Saddle Quarry (USGS)        :    0.02  /  0.10  /  0.23  /  0.23
PIOH1 : Piihonua (UHM)              :    0.00  /  0.04  /  0.14  /  0.14
PIIH1 : Piihonua (15016)            :    0.00  /  0.00  /  0.00  /  0.00
IPIH1 : IPIF (UHM)                  :    0.00  /  0.00  /  0.00  /  0.00
WKAH1 : Waiakea Uka (15017)         :    0.00  /  0.00  /  0.00  /  0.00
WEXH1 : Waiakea Exp Stn (NOAA/CRN)  :    0.00  /  0.00  /  0.00  /  0.00
HTO   : Hilo Airport (ASOS)         :    0.01  /  0.01  /  0.01  /  0.01
PHAH1 : Pahoa (15015)               :    0.01  /  0.01  /  0.01  /  0.01
PAOH1 : Pahoa (UHM)                 :    0.01  /  0.01  /  0.01  /  0.01
MTVH1 : Mountain View (15014)       :    0.04  /  0.04  /  0.04  /  0.04
GLNH1 : Glenwood (15013)            :    0.00  /  0.00  /  0.00  /  0.00
:       Leeward Sites
MOBH1 : Mauna Loa Ob Stn (NOAA/CRN) :    0.00  /  0.00  /  0.00  /  0.00
NHKH1 : Nahuku (UHM)                :    0.00  /  0.00  /  0.00  /  0.00
KKUH1 : Keaumo (RAWS)               :    0.01  /  0.04  /  0.16  /  0.16
KMOH1 : Kealakomo (RAWS)            :    0.00  /  0.00  /  0.00  /  0.00
PLIH1 : Pali 2 (RAWS)               :    0.02  /  0.02  /  0.02  /  0.02
KPRH1 : Kapapala (RAWS)             :    0.00  /  0.01  /  0.01  /  0.01
KAYH1 : Kapapala Ranch (15003)      :      M   /    M   /    M   /    M
PPLH1 : Pahala (15004)              :    0.00  /  0.08  /  0.08  /  0.08
KIOH1 : Kaiholena (UHM)             :      M   /    M   /    M   /    M
NENH1 : Nene Cabin (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
SOPH1 : South Point (HSOIS)         :    0.00  /  0.00  /  0.00  /  0.00
LKHH1 : Lower Kahuku (RAWS)         :    0.01  /  0.02  /  0.03  /  0.03
KRCH1 : Kahuku Ranch (RAWS)         :    0.00  /  0.01  /  0.02  /  0.02
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
KEHH1 : Kehena (UHM)                :    0.00  /  0.00  /  0.00  /  0.01
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
```

---

### 9. Hawaii Rainfall Summary direct product

| Field | Value |
|---|---|
| **Resource ID** | hfo_rra_direct |
| **Official source** | https://forecast.weather.gov/product.php?issuedby=HFO&product=RRA&site=hfo |
| **Collected** | 2026-09-30T02:34:49.650515-10:00 HST |

```text
297
SRHW80 PHFO 301146
RRAHFO

Hawaii Rainfall Summary
National Weather Service Honolulu HI
145 AM HST Wed Sep 30 2026

:
.B HFO  0930 H  DH01 /DRH-03/PPT/DRH-06/PPQ/DRH-12/PPK/DRH-24/PPD
:
:Automated rain gage reports from around the State of Hawaii.
:These are provisional reports that have not been quality
:controlled.
:
:T=Trace Rainfall, M=Missing Data
:
:Precipitation totals ending  1 AM HST
:
:Island of Kauai                                   Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward/Mauka Sites
MKAH1 : Makaha Ridge (RAWS)         :    0.34  /  0.47  /  0.52  /  0.52
PLRH1 : Puu Lua (RAWS)              :    0.78  /  0.91  /  1.18  /  1.18
WKRH1 : Waiakoali (USGS)            :    0.76  /  1.18  /  1.31  /  1.31
KLOH1 : Kilohana (USGS)             :    0.42  /  0.74  /  0.84  /  0.84
MCRH1 : Mohihi Crossing (USGS)      :    0.67  /  1.08  /  1.31  /  1.31
WLGH1 : Waialae (USGS)              :    0.57  /  1.22  /  1.31  /  1.31
LLMH1 : Lower Limahuli (UHM)        :    0.14  /  0.29  /  0.30  /  0.30
WNHH1 : Wainiha (12010)             :    0.02  /  0.17  /  0.28  /  0.28
WIPH1 : Waipa (UHM)                 :    0.21  /  0.55  /  0.63  /  0.63
HNIH1 : Hanalei (12009)             :    0.64  /  1.01  /  1.13  /  1.13
WLLH1 : Mount Waialeale (USGS)      :      M   /    M   /    M   /    M
PRIH1 : Princeville Airport (12011) :    0.09  /  0.38  /  0.63  /  0.63
CMGH1 : Common Ground (UHM)         :    0.22  /  0.48  /  0.72  /  0.72
HLIH1 : Hanalei (RAWS)              :    0.51  /  0.61  /  0.63  /  0.63
MLDH1 : Moloaa Dairy (RAWS)         :    0.00  /  0.00  /  0.00  /  0.00
ANHH1 : Anahola (12001)             :      M   /    M   /    M   /    M
KPIH1 : Kapahi (12003)              :    0.00  /  0.24  /  0.40  /  0.40
WLDH1 : N Wailua Ditch (USGS)       :    0.77  /  1.45  /  1.60  /  1.64
WUHH1 : Wailua (12005)              :    0.22  /  0.38  /  0.58  /  0.58
WIRH1 : Waiahi Rain Gage (USGS)     :    0.11  /  0.67  /  0.82  /  0.82
LIHH1 : Lihue Var. Stn. (12006)     :    0.05  /  0.16  /  0.24  /  0.24
HNMH1 : Hanamaulu (UHM)             :    0.21  /  1.02  /  1.10  /  1.10
HLI   : Lihue Airport (ASOS)        :    0.16  /  0.24  /  0.30  /  0.30
:       Leeward Sites
OMAH1 : Omao (12004)                :    0.28  /  0.31  /  0.38  /  0.38
LNTH1 : Lawai NTBG (UHM)            :    0.22  /  0.26  /  0.28  /  0.28
KHEH1 : Kalaheo (12008)             :    0.46  /  0.51  /  0.54  /  0.54
PAKH1 : Port Allen (HSOIS)          :    0.19  /  0.31  /  0.53  /  0.53
HNPH1 : Hanapepe (12002)            :    0.36  /  0.49  /  0.75  /  0.75
POPH1 : Puu Opae (RAWS)             :    0.70  /  0.89  /  1.10  /  1.10
WHGH1 : Waimea Heights (RAWS)       :    0.44  /  0.54  /  0.98  /  0.98
WMTH1 : Waimea Tank (12007)         :    0.45  /  0.51  /  0.96  /  0.96
MNRH1 : Mana (RAWS)                 :    0.52  /  0.53  /  0.73  /  0.73
:
:Island of Oahu                                    Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward/Mauka Sites
KAHH1 : Kahuku (13027)              :    0.47  /  0.47  /  0.47  /  0.47
KTAH1 : Kahuku Training Area (RAWS) :    0.00  /  0.00  /  0.01  /  0.01
KFWH1 : Kii (RAWS)                  :    0.00  /  0.00  /  0.00  /  0.00
PUNH1 : Punaluu Pump (13013)        :    0.17  /  0.18  /  0.18  /  0.18
PNSH1 : Punaluu Stream (USGS)       :    0.19  /  0.21  /  0.25  /  0.25
KNRH1 : Kahana (USGS)               :    0.01  /  0.01  /  0.01  /  0.01
HAKH1 : Hakipuu Mauka (13004)       :    0.00  /  0.00  /  0.00  /  0.00
WPPH1 : Waihee Pump (13002)         :    0.00  /  0.00  /  0.00  /  0.00
WHSH1 : Waiahole (USGS)             :    0.00  /  0.00  /  0.00  /  0.00
OFRH1 : Oahu Forest NWR (USFWS)     :    0.00  /  0.00  /  0.00  /  0.00
AHUH1 : Ahuimanu Loop (13005)       :    0.00  /  0.00  /  0.00  /  0.00
HRRH1 : Heeia NERR (NOAA/NOS)       :    0.01  /  0.01  /  0.01  /  0.01
LULH1 : Luluku (13016)              :    0.00  /  0.00  /  0.00  /  0.00
NRSH1 : Nuuanu Res No. 1 (UHM)      :    0.00  /  0.00  /  0.00  /  0.00
KWIH1 : Kalawahine (UHM)            :    0.00  /  0.00  /  0.00  /  0.00
LYOH1 : Lyon (UHM)                  :    0.00  /  0.00  /  0.00  /  0.00
MNLH1 : Manoa Lyon Arboretum (13023):    0.00  /  0.00  /  0.00  /  0.00
STVH1 : St. Stephens (13006)        :    0.00  /  0.00  /  0.00  /  0.00
MAUH1 : Maunawili (13008)           :      M   /    M   /    M   /    M
OFSH1 : Olomana Fire Station (13009):    0.00  /  0.00  /  0.00  /  0.00
WMLH1 : Waimanalo (13011)           :    0.00  /  0.00  /  0.00  /  0.00
BELH1 : Bellows AFS (HSOIS)         :    0.00  /  0.00  /  0.00  /  0.00
KMHH1 : Kamehame (13012)            :    0.00  /  0.00  /  0.00  /  0.00
HAJH1 : Hawaii Kai Golf Crse (13015):    0.00  /  0.00  /  0.00  /  0.00
:       Leeward/Central Sites
KUXH1 : Kaluanui (UHM)              :    0.00  /  0.00  /  0.00  /  0.00
NIUH1 : Niu Valley (13001)          :    0.00  /  0.00  /  0.00  /  0.00
PFSH1 : Palolo Fire Station (13010) :    0.00  /  0.00  /  0.00  /  0.00
HNL   : Honolulu Airport (ASOS)             See note at bottom  :
MOAH1 : Moanalua (13003)            :    0.00  /  0.00  /  0.00  /  0.00
MOGH1 : Moanalua RG (USGS)          :    0.00  /  0.00  /  0.00  /  0.00
TNLH1 : Tunnel RG (USGS)            :    0.00  /  0.00  /  0.00  /  0.00
PACH1 : Palisades (13020)           :    0.00  /  0.00  /  0.00  /  0.00
WAWH1 : Waiawa C.F. (13025)         :    0.00  /  0.00  /  0.00  /  0.00
MITH1 : Mililani (13022)            :    0.00  /  0.00  /  0.00  /  0.00
SCBH1 : Schofield Barracks (RAWS)   :    0.00  /  0.00  /  0.00  /  0.00
SCEH1 : Schofield East (RAWS)       :    0.00  /  0.00  /  0.00  /  0.00
WAFH1 : Wheeler Airfield            :    0.00  /  0.00  /  0.00  /  0.00
POAH1 : Poamoho (13018)             :    0.00  /  0.00  /  0.00  /  0.00
KRGH1 : Kalahee Ridge (UHM)         :    0.00  /  0.00  /  0.00  /  0.00
KMRH1 : Kamananui Stream (USGS)     :    0.00  /  0.00  /  0.00  /  0.00
PPRH1 : Pupukea Road (USGS)         :    0.00  /  0.00  /  0.00  /  0.00
PMHH1 : Poamoho RG 1 (USGS)         :    0.23  /  0.34  /  0.61  /  0.61
DLGH1 : Dillingham (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
AALH1 : Kaala (UHM)                 :    0.01  /  0.01  /  0.01  /  0.01
PECH1 : Waipio (13019)              :    0.00  /  0.00  /  0.00  /  0.00
KUNH1 : Kunia Substation (13021)    :    0.00  /  0.00  /  0.00  /  0.00
HOFH1 : Honouliuli (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
PTWH1 : Ewa Beach USGS (13024)      :    0.00  /  0.00  /  0.00  /  0.00
HJR   : Kalaeloa Airport (ASOS)             See note at bottom  :
PLHH1 : Palehua (RAWS)              :    0.00  /  0.00  /  0.00  /  0.00
LUAH1 : Lualualei (13017)           :    0.00  /  0.00  /  0.00  /  0.00
WNVH1 : Waianae Valley (RAWS)       :    0.00  /  0.00  /  0.00  /  0.00
WBHH1 : Waianae Boat Harbor (HSOIS) :    0.00  /  0.00  /  0.00  /  0.00
WAIH1 : Waianae (13014)             :    0.00  /  0.00  /  0.00  /  0.00
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
WWKH1 : West Wailuaiki (USGS)       :    0.00  /  0.00  /  0.00  /  0.00
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
KHIH1 : Kihei #2 (14009)            :      M   /    M   /    M   /    M
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
KWSH1 : Kawainui Stream (USGS)      :    0.00  /  0.00  /  0.00  /  0.01
KUUH1 : Kamuela Upper (15002)       :    0.00  /  0.00  /  0.00  /  0.00
KMUH1 : Kamuela (15005)             :    0.00  /  0.00  /  0.00  /  0.00
HNKH1 : Honokaa (15010)             :    0.00  /  0.00  /  0.00  /  0.00
PMLH1 : Puu Mali (RAWS)             :    0.00  /  0.00  /  0.00  /  0.00
WPNH1 : Waipunalei (UHM)            :      M   /    M   /    M   /  0.00
KNKH1 : Kanakaleonui (UHM)          :    0.00  /  0.00  /  0.01  /  0.01
LPHH1 : Laupahoehoe PD (15001)      :    0.00  /  0.00  /  0.00  /  0.00
LAUH1 : Laupahoehoe (UHM)           :    0.00  /  0.00  /  0.00  /  0.00
SPNH1 : Spencer (UHM)               :    0.00  /  0.00  /  0.00  /  0.00
HKUH1 : Hakalau (RAWS)              :    0.01  /  0.01  /  0.01  /  0.01
KLXH1 : Kulaimano (UHM)             :    0.00  /  0.00  /  0.00  /  0.00
NLIH1 : Honolii Stream (USGS)       :    0.02  /  0.02  /  0.02  /  0.02
SDQH1 : Saddle Quarry (USGS)        :    0.02  /  0.10  /  0.23  /  0.23
PIOH1 : Piihonua (UHM)              :    0.00  /  0.04  /  0.14  /  0.14
PIIH1 : Piihonua (15016)            :    0.00  /  0.00  /  0.00  /  0.00
IPIH1 : IPIF (UHM)                  :    0.00  /  0.00  /  0.00  /  0.00
WKAH1 : Waiakea Uka (15017)         :    0.00  /  0.00  /  0.00  /  0.00
WEXH1 : Waiakea Exp Stn (NOAA/CRN)  :    0.00  /  0.00  /  0.00  /  0.00
HTO   : Hilo Airport (ASOS)         :    0.01  /  0.01  /  0.01  /  0.01
PHAH1 : Pahoa (15015)               :    0.01  /  0.01  /  0.01  /  0.01
PAOH1 : Pahoa (UHM)                 :    0.01  /  0.01  /  0.01  /  0.01
MTVH1 : Mountain View (15014)       :    0.04  /  0.04  /  0.04  /  0.04
GLNH1 : Glenwood (15013)            :    0.00  /  0.00  /  0.00  /  0.00
:       Leeward Sites
MOBH1 : Mauna Loa Ob Stn (NOAA/CRN) :    0.00  /  0.00  /  0.00  /  0.00
NHKH1 : Nahuku (UHM)                :    0.00  /  0.00  /  0.00  /  0.00
KKUH1 : Keaumo (RAWS)               :    0.01  /  0.04  /  0.16  /  0.16
KMOH1 : Kealakomo (RAWS)            :    0.00  /  0.00  /  0.00  /  0.00
PLIH1 : Pali 2 (RAWS)               :    0.02  /  0.02  /  0.02  /  0.02
KPRH1 : Kapapala (RAWS)             :    0.00  /  0.01  /  0.01  /  0.01
KAYH1 : Kapapala Ranch (15003)      :      M   /    M   /    M   /    M
PPLH1 : Pahala (15004)              :    0.00  /  0.08  /  0.08  /  0.08
KIOH1 : Kaiholena (UHM)             :      M   /    M   /    M   /    M
NENH1 : Nene Cabin (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
SOPH1 : South Point (HSOIS)         :    0.00  /  0.00  /  0.00  /  0.00
LKHH1 : Lower Kahuku (RAWS)         :    0.01  /  0.02  /  0.03  /  0.03
KRCH1 : Kahuku Ranch (RAWS)         :    0.00  /  0.01  /  0.02  /  0.02
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
KEHH1 : Kehena (UHM)                :    0.00  /  0.00  /  0.00  /  0.01
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

### 10. Hawaii Temp/Precip Summary

| Field | Value |
|---|---|
| **Resource ID** | rtp_temp_precip_summary |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=RTP&issuedby=HI |
| **Collected** | 2026-09-30T02:29:14.530742-10:00 HST |

```text
CLIHNL
086
CDHW40 PHFO 300245
CLIHNL

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
445 PM HST TUE SEP 29 2026

...................................

...THE HONOLULU CLIMATE SUMMARY FOR SEPTEMBER 29 2026...
VALID TODAY AS OF 0425 PM LOCAL TIME.

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1940 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 TODAY
  MAXIMUM         89    128 PM  93    1993  88      1       89
                                      2020
  MINIMUM         73    630 AM  66    1975  75     -2       78
  AVERAGE         81                        81      0       84

PRECIPITATION (IN)
  TODAY            0.00          0.46 1960   0.03  -0.03      T
  MONTH TO DATE    0.32                      0.86  -0.54     0.71
  SINCE SEP 1      0.32                      0.86  -0.54     0.71
  SINCE JAN 1     22.35                     10.45  11.90     9.59

DEGREE DAYS
 HEATING
  TODAY            0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  TODAY           16                        16      0       19
  MONTH TO DATE  526                       481     45      516
  SINCE SEP 1    526                       481     45      516
  SINCE JAN 1   3736                      3558    178     4001
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    16   HIGHEST WIND DIRECTION    SE (140)
  HIGHEST GUST SPEED    22   HIGHEST GUST DIRECTION    SE (140)
  AVERAGE WIND SPEED     7.0

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.3

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED TODAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    82           700 AM
 LOWEST     45           100 PM
 AVERAGE    64

..........................................................

THE HONOLULU CLIMATE NORMALS FOR TOMORROW
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   88        92      1988
 MINIMUM TEMPERATURE (F)   75        67      1981

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   622 AM HST   SUNSET   621 PM HST
SEPTEMBER 30 2026.....SUNRISE   623 AM HST   SUNSET   620 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.

CLILIH
088
CDHW41 PHFO 300245
CLILIH

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
445 PM HST TUE SEP 29 2026

...................................

...THE LIHUE CLIMATE SUMMARY FOR SEPTEMBER 29 2026...
VALID TODAY AS OF 0425 PM LOCAL TIME.

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1950 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 TODAY
  MAXIMUM         85   1158 AM  88    1981  85      0       84
                                      2014
                                      2017
  MINIMUM         78    708 AM  65    1952  75      3       74
  AVERAGE         82                        80      2       79

PRECIPITATION (IN)
  TODAY            0.00          0.88 1986   0.09  -0.09     0.12
  MONTH TO DATE    3.13                      2.10   1.03     3.62
  SINCE SEP 1      3.13                      2.10   1.03     3.62
  SINCE JAN 1     42.92                     24.20  18.72    15.08

DEGREE DAYS
 HEATING
  TODAY            0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  TODAY           17                        15      2       14
  MONTH TO DATE  441                       435      6      447
  SINCE SEP 1    441                       435      6      447
  SINCE JAN 1   3144                      3069     75     3385
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    18   HIGHEST WIND DIRECTION     E (100)
  HIGHEST GUST SPEED    23   HIGHEST GUST DIRECTION     E (110)
  AVERAGE WIND SPEED    11.9

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.4

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED TODAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    79          1200 AM
 LOWEST     65          1200 PM
 AVERAGE    72

..........................................................

THE LIHUE CLIMATE NORMALS FOR TOMORROW
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   85        88      1981
                                             2014
                                             2017
 MINIMUM TEMPERATURE (F)   75        65      1968

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   628 AM HST   SUNSET   627 PM HST
SEPTEMBER 30 2026.....SUNRISE   629 AM HST   SUNSET   626 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.

CLIOGG
089
CDHW42 PHFO 300245
CLIOGG

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
445 PM HST TUE SEP 29 2026

...................................

...THE KAHULUI/MAUI CLIMATE SUMMARY FOR SEPTEMBER 29 2026...
VALID TODAY AS OF 0425 PM LOCAL TIME.

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1954 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 TODAY
  MAXIMUM         92    126 PM  93    1996  90      2       89
  MINIMUM         65    520 AM  63    1974  71     -6       75
                                      1975
                                      2002
  AVERAGE         79                        80     -1       82

PRECIPITATION (IN)
  TODAY            0.00          0.17 1987   0.02  -0.02     0.00
  MONTH TO DATE    0.60                      0.44   0.16     0.04
  SINCE SEP 1      0.60                      0.44   0.16     0.04
  SINCE JAN 1     30.28                     10.76  19.52     6.61

DEGREE DAYS
 HEATING
  TODAY            0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  TODAY           14                        15     -1       17
  MONTH TO DATE  468                       457     11      460
  SINCE SEP 1    468                       457     11      460
  SINCE JAN 1   3252                      3304    -52     3315
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    20   HIGHEST WIND DIRECTION     N (20)
  HIGHEST GUST SPEED    26   HIGHEST GUST DIRECTION    NE (30)
  AVERAGE WIND SPEED     7.3

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.1

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED TODAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    87           600 AM
 LOWEST     48          1100 AM
 AVERAGE    68

..........................................................

THE KAHULUI/MAUI CLIMATE NORMALS FOR TOMORROW
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   90        94      2022
 MINIMUM TEMPERATURE (F)   71        62      1962

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   616 AM HST   SUNSET   615 PM HST
SEPTEMBER 30 2026.....SUNRISE   617 AM HST   SUNSET   614 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.

CLIITO
087
CDHW43 PHFO 300245
CLIITO

CLIMATE REPORT
NATIONAL WEATHER SERVICE HONOLULU HI
445 PM HST TUE SEP 29 2026

...................................

...THE HILO/GEN.LYMAN FLD CLIMATE SUMMARY FOR SEPTEMBER 29 2026...
VALID TODAY AS OF 0425 PM LOCAL TIME.

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1949 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 TODAY
  MAXIMUM         85   1249 PM  89    1974  83      2       85
                                      2014
                                      2019
  MINIMUM         69    616 AM  64    1955  70     -1       70
  AVERAGE         77                        76      1       78

PRECIPITATION (IN)
  TODAY            0.00          3.09 1963   0.30  -0.30     0.02
  MONTH TO DATE   16.18                      8.42   7.76     2.76
  SINCE SEP 1     16.18                      8.42   7.76     2.76
  SINCE JAN 1    124.42                     83.41  41.01    38.14

DEGREE DAYS
 HEATING
  TODAY            0                         0      0        0
  MONTH TO DATE    0                         0      0        0
  SINCE SEP 1      0                         0      0        0
  SINCE JUL 1      0                         0      0        0

 COOLING
  TODAY           12                        11      1       13
  MONTH TO DATE  377                       345     32      366
  SINCE SEP 1    377                       345     32      366
  SINCE JAN 1   2806                      2456    350     2867
...................................................................

WIND (MPH)
  HIGHEST WIND SPEED    17   HIGHEST WIND DIRECTION     E (90)
  HIGHEST GUST SPEED    24   HIGHEST GUST DIRECTION     E (110)
  AVERAGE WIND SPEED     9.2

SKY COVER
  POSSIBLE SUNSHINE  MM
  AVERAGE SKY COVER 0.2

WEATHER CONDITIONS
THE FOLLOWING WEATHER WAS RECORDED TODAY.
  NO SIGNIFICANT WEATHER WAS OBSERVED.

RELATIVE HUMIDITY (PERCENT)
 HIGHEST    82          1200 AM
 LOWEST     62           800 AM
 AVERAGE    72

..........................................................

THE HILO/GEN.LYMAN FLD CLIMATE NORMALS FOR TOMORROW
                         NORMAL    RECORD    YEAR
 MAXIMUM TEMPERATURE (F)   83        88      1976
                                             2018
                                             2020
 MINIMUM TEMPERATURE (F)   70        61      1970

SUNRISE AND SUNSET
SEPTEMBER 29 2026.....SUNRISE   611 AM HST   SUNSET   610 PM HST
SEPTEMBER 30 2026.....SUNRISE   611 AM HST   SUNSET   609 PM HST

-  INDICATES NEGATIVE NUMBERS.
R  INDICATES RECORD WAS SET OR TIED.
MM INDICATES DATA IS MISSING.
T  INDICATES TRACE AMOUNT.
```

---

### 11. HFO statewide surf observations direct page

| Field | Value |
|---|---|
| **Resource ID** | hfo_surf_reports_direct |
| **Official source** | https://www.weather.gov/hfo/surfreports |
| **Collected** | 2026-09-30T02:27:31.993957-10:00 HST |

```text
                        
880
SXHW80 PHFO 300115
OMRHFO

SURF OBSERVATIONS
NATIONAL WEATHER SERVICE HONOLULU HI
315 PM HST TUE SEP 29 2026

FULL FACE SURF OBSERVATIONS ARE TAKEN BY COUNTY LIFE GUARDS AND
COOPERATIVE OBSERVERS AND RELAYED TO THE NATIONAL WEATHER SERVICE
FOR DISSEMINATION. THESE OBSERVATIONS ARE NOT QUALITY CONTROLLED.

HIZ003-004-029>031-300100-
KAUAI-

LOCATION        TIME   SURF HEIGHT DIR   PER                  REMARKS
KEE
HAENA        1000 AM           4-5  NW    11
HANALEI      1000 AM           2-3   N     9
ANAHOLA
KEALIA
LYDGATE
POIPU        1030 AM          6-8   SW    10
SALT POND    1030 AM           6-8  SW    10
KEKAHA       1030 AM           6-8  SW    10
$$

HIZ006-007-009>011-032>036-300100-
OAHU-

LOCATION        TIME   SURF HEIGHT DIR PER         WIND      REMARKS
DIAMOND HEAD
SUNSET
WAIKIKI      1118 AM           3-4              E 10-15       CANOES
SANDY BEACH  1118 AM           3-5              NE 5-15  SHORE BREAK
MAKAPUU      1118 AM           3-5             NE 10-15
EHUKAI       1118 AM           2-3              E 10-15
MAKAHA       1118 AM           2-3               E 5-10
$$

HIZ015>018-022-045>050-300100-
MAUI-MOLOKAI-LANAI-KAHOOLAWE-

LOCATION        TIME   SURF HEIGHT   DIR         WIND      REMARKS
KANAHA       1127 AM           1-3           VRB 5-10  PARTLY CLDY
BALDWIN SHOR 1128 AM           2-3           VRB 5-10        SUNNY
BALDWIN OUTE 1128 AM           4-6           VRB 5-10        SUNNY
HOOKIPA      1129 AM           6-8            E 20-25  PARTLY CLDY
KAMAOLE I    1133 AM           2-4            VRB 0-5  PARTLY CLDY
KAMAOLE III  1131 AM           2-3           VRB 5-10        SUNNY
HANAKAOO
FLEMING
$$

HIZ023-026>028-051>054-300100-
BIG ISLAND OF HAWAII-

LOCATION        TIME   SURF HEIGHT   DIR         WIND      REMARKS
RICHARDSONS  1120 AM           2-3           VRB 5-10        SUNNY
HONOLII      1121 AM           3-5             S 5-15 MOSTLY SUNNY
PUNALU`U
ISAAC HALE   1122 AM           3-5            E 10-15 MOSTLY SUNNY
HAPUNA
KAHALUU      1124 AM           5-6    SW      SW 5-10  PARTLY CLDY
MAGIC SANDS  1125 AM           3-4    SW      SW 5-10        SUNNY
KUA BAY      1126 AM           2-4           VRB 5-10 MOSTLY SUNNY
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

### 12. High Seas Forecast N. Pacific

| Field | Value |
|---|---|
| **Resource ID** | hsf_high_seas_npac |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=HSF&issuedby=NP |
| **Collected** | 2026-09-30T00:19:58.824087-10:00 HST |

```text
581
FZPN40 PHFO 301018
HSFNP

HIGH SEAS FORECAST
NATIONAL WEATHER SERVICE HONOLULU HI
1100 UTC WED SEP 30 2026

SUPERSEDED BY NEXT ISSUANCE IN 6 HOURS

SEAS GIVEN AS SIGNIFICANT WAVE HEIGHT...WHICH IS THE AVERAGE HEIGHT
OF THE HIGHEST 1/3 OF THE WAVES. INDIVIDUAL WAVES MAY BE MORE THAN
TWICE THE SIGNIFICANT WAVE HEIGHT.

THIS HIGH SEAS FORECAST USES 1-MINUTE AVERAGE WINDS WHICH MAY BE
HIGHER THAN 10-MINUTE AVERAGE WINDS.

SECURITE

NORTH PACIFIC EQUATOR TO 30N BETWEEN 140W AND 180W

SYNOPSIS VALID 0600 UTC SEP 30 2026.
24 HOUR FORECAST VALID 0600 UTC OCT 01 2026.
48 HOUR FORECAST VALID 0600 UTC OCT 02 2026.

.WARNINGS.

...TROPICAL STORM WARNING...
.TROPICAL STORM NOLO NEAR 22.4N 164.6W 987 MB AT 0900 UTC SEP 30
MOVING WNW OR 290 DEG AT 5 KT. MAXIMUM SUSTAINED WINDS 60 KT
GUSTS 75 KT. TROPICAL STORM FORCE WINDS WITHIN 120 NM NE
QUADRANT...90 NM SE QUADRANT...80 NM SW QUADRANT...AND 110 NM NW
QUADRANT. SEAS 4 M OR GREATER WITHIN 150 NM E SEMICIRCLE AND
240 NM W SEMICIRCLE WITH SEAS TO 10 M. SEAS 2.5 TO 3.5 M ELSEWHERE
FROM 16N TO 27N BETWEEN 159W AND 180W. WINDS 20 TO 30 KT ELSEWHERE
FROM 20N TO 26N BETWEEN 158W AND 169W. ISOLATED MODERATE TSTMS
WITHIN 90 NM OF CENTER.
.24 HOUR FORECAST TROPICAL STORM NOLO NEAR 22.7N 165.0W. MAXIMUM
SUSTAINED WINDS 50 KT GUSTS 60 KT. TROPICAL STORM FORCE WINDS
WITHIN 100 NM N SEMICIRCLE AND 70 NM S SEMICIRCLE. SEAS 4 M OR
GREATER FROM 20N TO 25N BETWEEN 163W AND 169W WITH SEAS TO 8 M.
SEAS 2.5 TO 3.5 M ELSEWHERE FROM 17N TO 30N BETWEEN 161W AND 178W.
WINDS 20 TO 30 KT ELSEWHERE FROM 20N TO 27N BETWEEN 161W AND 171W.
.48 HOUR FORECAST TROPICAL STORM NOLO NEAR 22.8N 166.5W. MAXIMUM
SUSTAINED WINDS 55 KT GUSTS 65 KT. TROPICAL STORM FORCE WINDS
WITHIN 100 NM NE QUADRANT...80 NM SE QUADRANT...70 NM SW
QUADRANT...AND 90 NM NW QUADRANT. SEAS 4 M OR GREATER FROM 21N TO
25N BETWEEN 163W AND 170W WITH SEAS TO 7 M. SEAS 2.5 TO 3.5 M
ELSEWHERE FROM 17N TO 29N BETWEEN 161W AND 176W. WINDS 20 TO 30 KT
ELSEWHERE FROM 20N TO 27N BETWEEN 161W AND 173W.

FORECAST WINDS IN AND NEAR ACTIVE TROPICAL CYCLONES SHOULD BE
USED WITH CAUTION DUE TO UNCERTAINTY IN FORECAST TRACK...SIZE
AND INTENSITY.

.SYNOPSIS AND FORECAST.

.FRONT 30N165W 28N169W 29N174W MOVING SE 15 KT.
.24 HOUR FORECAST 30N156W 28N160W THENCE TROUGH 28N162W.
.48 HOUR FORECAST FRONT 30N149W 29N150W 29N155W. TROUGH 30N165W
26N166W.

.WINDS 20 KT OR LESS OVER REMAINDER OF FORECAST AREA.

.SEAS 2.5 M OR LOWER OVER REMAINDER OF FORECAST AREA.

.MONSOON TROUGH 11N140W 09N146W 12N162W 09N180W. SCATTERED MODERATE
TSTMS S OF TROUGH W OF 155W. ISOLATED MODERATE TSTMS S OF
TROUGH E OF 155W.

.FORECASTER TSAMOUS. HONOLULU HI.
```

---

### 13. Hourly Wind/Precip Observations

| Field | Value |
|---|---|
| **Resource ID** | oso_hourly_obs |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=OSO&issuedby=HFO |
| **Collected** | 2026-09-30T02:29:00.262377-10:00 HST |

```text
657
SXHW50 PHFO 301225
OSOHFO

Hawaii Wind Data
National Weather Service Honolulu HI
225 AM HST Wed Sep 30 2026

                            W I N D        D A T A
                            ----------------------
                                                                   IN KNOTS
 ID                Location              Date     Time     DIR    SPD   GUST
--------   -------------------------    -------  -(HST)-  ----   ----   ----
0000LLMH1  Lower Limahuli     Kauai     30Sep26   02:00    140      1      3
0000CMGH1  Common Ground      Kauai     30Sep26   02:00    130      5     11
0000HLIH1  Hanalei            Kauai     30Sep26   01:41     90      3      7
0000MLDH1  Moloaa Dairy       Kauai     30Sep26   01:45    130     10     23
0000HNMH1  Hanamaulu          Kauai     30Sep26   02:00    160      5      9
0000PHLI   Lihue              Kauai     30Sep26   02:08    150     20     27
0000NWWH1  Nawiliwili NOS     Kauai     30Sep26   02:06    140     17     26
0000POIH1  Poipu              Kauai                MSG    MSG    MSG    MSG
0000LNTH1  Lawai NTBG         Kauai     30Sep26   02:00    110      2      6
0000PAKH1  Port Allen         Kauai     30Sep26   02:00    120     17     20
0000MKAH1  Makaha Ridge       Kauai     30Sep26   02:11    150     12     23
0000MNRH1  Mana               Kauai     30Sep26   01:34    130      8     17
0000PHBK   Barking Sands      Kauai     30Sep26   02:17    130     15     26
0000PLRH1  Puu Lua            Kauai     30Sep26   01:35     70     10     28
0000POPH1  Puu Opae           Kauai     30Sep26   01:34    140     12     25
0000WHGH1  Waimea Heights     Kauai     30Sep26   01:35     60     10     22

0000KRGH1  Kalahee Ridge      Oahu      30Sep26   01:55    110      2      4
0000KAHH1  Kahuku             Oahu                 MSG    MSG    MSG    MSG
0000KTAH1  Kahuku Trng        Oahu      30Sep26   01:59    200      0      3
0000KFWH1  Kii                Oahu      30Sep26   01:45    120     11     20
0000OFRH1  Oahu Forest NWR    Oahu      30Sep26   01:36     60      2      7
0000KWMH1  Kaaawa Makai       Oahu      30Sep26   02:00    120      4      8
0000PHNG   Kaneohe MCBH       Oahu      30Sep26   02:04    110      7     15
0000MOKH1  Mokuoloe Is NOS    Oahu      30Sep26   02:06    150      3      7
0000BELH1  Bellows AFS        Oahu      30Sep26   02:15    140      8    MSG
0000KUXH1  Kaluanui           Oahu      30Sep26   02:00    170      2      5
0000LYOH1  Lyon               Oahu      30Sep26   01:55    250      1      2
0000NRSH1  Nuuanu Res No 1    Oahu      30Sep26   02:00     40      1      3
0000PHNL   Honolulu AP        Oahu      30Sep26   02:00    120     11    MSG
0000OOUH1  Honolulu Hbr NOS   Oahu      30Sep26   02:00    130      4     10
0000HOFH1  Honouliuli PHB     Oahu      30Sep26   01:41    140      7     12
0000SCBH1  Schofield Brks     Oahu      30Sep26   01:57    160      4     10
0000SCEH1  Schofield East     Oahu      30Sep26   01:58    140      3      8
0000HWLH1  HECO Wilikina      Oahu      30Sep26   02:10    120      8     14
0000PHJR   Kalaeloa           Oahu      30Sep26   02:00    120      8     18
0000HFHH1  HECO Farrington    Oahu      30Sep26   02:10    100      9     14
0000HPLH1  HECO Palehua       Oahu      30Sep26   02:10     90      4     13
0000HPDH1  HECO Palehua 2     Oahu      30Sep26   02:10    140      7     11
0000HPHH1  HECO Palehua 3     Oahu      30Sep26   02:10    110     10     16
0000HPRH1  HECO Paakea        Oahu      30Sep26   02:10    150     12     22
0000HLRH1  HECO Lualualei     Oahu      30Sep26   02:10    140      6     12
0000HWVH1  HECO Waianae Vly   Oahu                 MSG    MSG    MSG    MSG
0000PLHH1  Palehua            Oahu      30Sep26   01:36    100      0      0
0000WNVH1  Waianae Valley     Oahu      30Sep26   01:37    140      6     13
0000HHSH1  HECO Ala Hema St   Oahu      30Sep26   02:10    110      6     13
0000WBHH1  Waianae Harbor     Oahu                 MSG    MSG    MSG    MSG
0000HKRH1  HECO Kili Dr       Oahu      30Sep26   02:10    100      7     14
0000HMVH1  HECO Makaha Vly    Oahu      30Sep26   02:10    240      9     17
0000MKRH1  Makua Range        Oahu      30Sep26   01:58    120      5     16
0000KKRH1  Kuaokala           Oahu      30Sep26   01:36     30      6     15
0000AALH1  Kaala              Oahu      30Sep26   02:00    160      4     10
0000HFRH1  HECO Farrington2   Oahu      30Sep26   02:10     90      4      8
0000HFYH1  HECO Farrington3   Oahu      30Sep26   02:10    110      5      7
0000DLGH1  Dillingham         Oahu      30Sep26   01:49    100      1      6

0000MKPH1  Makapulapai        Molokai   30Sep26   02:15    120      9     18
0000PAFH1  Puu Alii           Molokai   30Sep26   02:22    170      1      4
0000HOMH1  Honolimaloo        Molokai   30Sep26   02:00    140      6     12
0000KOPH1  Keopukaloa         Molokai   30Sep26   02:00    130     11     17
0000MLKH1  Molokai 1          Molokai              MSG    MSG    MSG    MSG
0000MMPH1  MECO Makaena       Molokai   30Sep26   02:10     20      4      6
0000MKYH1  MECO Kalae Hwy     Molokai   30Sep26   02:10     10      5      6
0000PHMK   Molokai AP         Molokai   30Sep26   02:00    350      4    MSG
0000ANPH1  Anapuka            Molokai   30Sep26   02:00    170      1      2

0000LNIH1  Lanai 1            Lanai     30Sep26   01:37     70      0      0

0000KAOH1  Kaneloa            Kahoolawe            MSG    MSG    MSG    MSG

0000PHOG   Kahului AP         Maui      30Sep26   02:00    140      5    MSG
0000KLIH1  Kahului Hbr NOS    Maui      30Sep26   02:06    240      2      3
0000MHRH1  MECO Hansen Rd     Maui      30Sep26   02:10    140      3      4
0000MHKH1  MECO Haleakala Hwy Maui      30Sep26   02:10    140      3      4
0000MMKH1  MECO Makawao       Maui      30Sep26   02:10    190      4      5
0000MKTH1  MECO Kula 2        Maui      30Sep26   02:10    170      2      3
0000PILH1  Piiholo            Maui      30Sep26   02:00    150      3      4
0000EBYH1  EMI Baseyard       Maui      30Sep26   02:00    150      2      5
0000HNAH1  Hana               Maui                 MSG    MSG    MSG    MSG
0000NKUH1  Na Kula            Maui      30Sep26   01:35     70      8     15
0000AWAH1  Auwahi             Maui                 MSG    MSG    MSG    MSG
0000KLFH1  Kula 1             Maui      30Sep26   01:48    140      4      7
0000KKNH1  Kahikinui 1        Maui      30Sep26   01:34    340      1      4
0000KMEH1  Kamehamenui 1      Maui      30Sep26   01:48    170      4      7
0000SUMH1  Summit             Maui      30Sep26   02:00    190      5      9
0000NNEH1  Nene Nest          Maui      30Sep26   02:00    170      2      4
0000PHQH1  Park HQ            Maui      30Sep26   01:30    150      3      5
0000WKTH1  Waikamoi Treeline  Maui      30Sep26   02:00    210      5      6
0000MCTH1  MECO Crater Rd     Maui      30Sep26   02:10    110      6      7
0000KLGH1  Kula Ag            Maui      30Sep26   02:00    100      1      2
0000MWAH1  MECO Waipoli Rd    Maui      30Sep26   02:10    100      2      3
0000KKEH1  Keokea             Maui      30Sep26   02:00    140      3      3
0000MKUH1  MECO Kula          Maui      30Sep26   02:10     60      4      6
0000PHUH1  Pulehu             Maui      30Sep26   02:00    120      3      4
0000MNDH1  MECO Naalaea Rd    Maui      30Sep26   02:10    100      3      5
0000MURH1  MECO Ulupalakua    Maui      30Sep26   02:10     60      3      4
0000LPOH1  Lipoa              Maui      30Sep26   02:00     80      3      4
0000MVHH1  MECO Veterans Hwy  Maui      30Sep26   02:10     70      2      4
0000KPDH1  Kealia Pond        Maui      30Sep26   02:20     90      1      4
0000MMAH1  MECO Maalaea       Maui      30Sep26   02:10     10      1      2
00000P36   Maalaea Bay        Maui      30Sep26   01:15      0      0      0
0000HULH1  Hanaula            Maui      30Sep26   01:55    260      2      5
0000OLUH1  Olowalu            Maui      30Sep26   02:00     70      2      6
0000MMMH1  MECO Mamane Pl     Maui      30Sep26   02:10    220      1      3
0000MHOH1  MECO Honoapiilani  Maui      30Sep26   02:10    330      2      4
0000MHHH1  MECO Honoapiilani2 Maui      30Sep26   02:10    260      1      3
0000MKEH1  MECO Kealaloloa Rg Maui      30Sep26   02:10     30      2      3
0000MUGH1  MECO Ukumehame Gul Maui      30Sep26   02:10     10      5      7
0000MOOH1  MECO Olowalu       Maui      30Sep26   02:10     80      4      8
0000OLUH1  Olowalu            Maui      30Sep26   02:00     70      2      6
0000MLPH1  MECO Launiupoko    Maui      30Sep26   02:10     20      2      7
0000MLTH1  MECO Launiupoko 2  Maui      30Sep26   02:10     40      3      4
0000MLRH1  MECO Lahainaluna   Maui      30Sep26   02:10     40      6      7
0000LWTH1  Lahaina WTP        Maui      30Sep26   02:00     80      4      7
0000MKNH1  MECO Kaanapali     Maui      30Sep26   02:10     70      6      8
0000PHJH   Kapalua-W Maui     Maui      30Sep26   02:00      0      0    MSG
0000HOOH1  Honolua            Maui      30Sep26   02:00    190      4      6

0000UPLH1  Upolu Airport      Hawaii    30Sep26   01:15    210      0      0
0000KMMH1  Kaluamakani        Hawaii    30Sep26   02:00    150      5      5
0000PMLH1  Puu Mali           Hawaii    30Sep26   02:00    200      3      6
0000KNKH1  Kanakaleonui       Hawaii    30Sep26   02:00    270      4      6
0000WPNH1  Waipunalei         Hawaii               MSG    MSG    MSG    MSG
0000LAUH1  Laupahoehoe        Hawaii    30Sep26   02:00    200      3      5
0000SPNH1  Spencer            Hawaii    30Sep26   02:00    210      0      1
0000HKUH1  Hakalau            Hawaii    30Sep26   01:45    250      2      4
0000KLXH1  Kulaimano          Hawaii    30Sep26   02:00    200      6     11
0000PIOH1  Piihonua           Hawaii    30Sep26   02:00    250      2      3
0000PHTO   Hilo AP            Hawaii    30Sep26   02:00    220      6    MSG
0000ILOH1  Hilo Hbr NOS       Hawaii    30Sep26   02:06    230      2      4
0000IPIH1  IPIF               Hawaii    30Sep26   02:00    230      2      4
0000WEXH1  Waiakea Exp Stn    Hawaii    30Sep26   02:00    MSG      1      4
0000KEUH1  Keaau              Hawaii    30Sep26   02:00      0      0      0
0000PAOH1  Pahoa              Hawaii    30Sep26   02:00    160      1      2
0000NHKH1  Nahuku             Hawaii    30Sep26   02:00    150      3      4
0000KKUH1  Keaumo             Hawaii    30Sep26   01:34    250      3      8
0000MOBH1  Mauna Loa Obs      Hawaii    30Sep26   02:00    MSG      7     10
0000PLIH1  Pali 2             Hawaii    30Sep26   02:01     60      3      4
0000KMOH1  Kealakomo          Hawaii    30Sep26   01:44    110      6      9
0000KPRH1  Kapapala           Hawaii    30Sep26   01:48     40      0      0
0000NENH1  Nene Cabin         Hawaii    30Sep26   02:23     10      3      6
0000KIOH1  Kaiholena          Hawaii    30Sep26   02:00    300      4      5
0000LKHH1  Lower Kahuku       Hawaii    30Sep26   02:23    350      1      6
0000SOPH1  South Point        Hawaii    30Sep26   02:00     40     10     16
0000KOMH1  Kona Hema          Hawaii    30Sep26   02:00     50      5      6
0000KRCH1  Kahuku Ranch       Hawaii    30Sep26   01:29     90      3      5
0000PHRH1  Puho CS            Hawaii    30Sep26   02:22     80      3      5
0000HLNH1  HELCO Lolo Ln      Hawaii    30Sep26   02:10     80      3      4
0000HHUH1  HELCO Hualalai Rd  Hawaii    30Sep26   02:10     50      4      6
0000KOUH1  Keahuolu           Hawaii    30Sep26   02:00     60      3      4
0000PHKO   Kona Intl AP       Hawaii    30Sep26   02:00     60      6    MSG
0000KHOH1  Kaloko-Honokohau   Hawaii    30Sep26   02:15     20      4      6
0000PLMH1  Palamanui          Hawaii    30Sep26   02:00     50      2      4
0000PWAH1  Puu Waawaa (UHM)   Hawaii    30Sep26   02:00    180      2      2
0000KIUH1  Kaiaulu Puu Waawaa Hawaii    30Sep26   02:00    230      2      2
0000KPLH1  Kaupulehu          Hawaii    30Sep26   01:36    130      5      6
0000PWWH1  Puu Waawaa         Hawaii    30Sep26   01:37    130      3      4
0000HMHH1  HELCO Mamalahoa 2  Hawaii    30Sep26   02:10    170      6      8
0000MMLH1  Mamalahoa          Hawaii    30Sep26   02:00     90      0      1
0000HMWH1  HELCO Mamalahoa 3  Hawaii    30Sep26   02:10    140      4      5
0000PULH1  Puuanahulu         Hawaii    30Sep26   01:37    140      3      4
0000AHMH1  Ahumoa             Hawaii    30Sep26   01:35    140      3      5
0000AIPH1  Aipaloa            Hawaii    30Sep26   02:00    170      6      8
0000HSRH1  HELCO Saddle Rd    Hawaii    30Sep26   02:10    110      5      6
0000HMYH1  HELCO Mamalahoa    Hawaii    30Sep26   02:10     90      3      4
0000HHCH1  HELCO Hokuloa UCC  Hawaii    30Sep26   02:10    140      4      5
0000HWRH1  HELCO Waikoloa Rd  Hawaii    30Sep26   02:10     90      7      9
0000HWXH1  HELCO Waikoloa 2   Hawaii    30Sep26   02:10    120      7      8
0000WKVH1  Waikoloa           Hawaii    30Sep26   01:35    100      4      6
0000HLOH1  HELCO Lalamilo     Hawaii    30Sep26   02:10     50      7      8
0000LLAH1  Lalamilo           Hawaii    30Sep26   02:00     50      2      2
0000HKWH1  HELCO Kawaihae Rd  Hawaii    30Sep26   02:10     90      6      7
0000PKAH1  PTA Kipuka Alala   Hawaii    30Sep26   01:55    140      3      4
0000PKWH1  PTA West           Hawaii    30Sep26   01:56    130      4      6
0000PKMH1  PTA Keamuku        Hawaii    30Sep26   01:50    160      0      0
0000PTRH1  PTA Range 17       Hawaii    30Sep26   01:49     40      0      7
0000PERH1  Puhe CS            Hawaii    30Sep26   01:24     40      3      6
0000KWHH1  Kawaihae NOS       Hawaii               MSG    MSG    MSG    MSG
0000HHKH1  HELCO Hulukupuna   Hawaii    30Sep26   02:10     40      5      6
0000PLAH1  Puuloa             Hawaii    30Sep26   02:00    290      4      7
0000HMLH1  HELCO Maluokalani  Hawaii               MSG    MSG    MSG    MSG
0000HKDH1  HELCO Ala Kahua    Hawaii    30Sep26   02:10    210      6      8
0000KHRH1  Kohala Ranch       Hawaii    30Sep26   01:35     60      5      7
0000KEHH1  Kehena             Hawaii    30Sep26   02:00    200      3      5
```

---

### 14. Marine Forecast Matrix (Hawaiian Waters)

| Field | Value |
|---|---|
| **Resource ID** | mfm_marine_forecast_matrix |
| **Official source** | https://www.weather.gov/hfo/MFM |
| **Collected** | 2026-09-30T02:26:06.082215-10:00 HST |

```text
612

FXHW40 PHFO 300101

MFMHFO

MARINE FORECAST MATRICES

NATIONAL WEATHER SERVICE HONOLULU HI

301 PM HST TUE SEP 29 2026

THE INFORMATION PRESENTED IN THIS PRODUCT REFLECTS A

FORECAST...RATHER THAN CURRENT INFORMATION. MARINE USERS SEEKING

CURRENT INFORMATION SHOULD CHECK THE LATEST COASTAL WIND AND BUOY

REPORTS.

PHZ112-301400-

CK FAD BUOY MAKAHUENA PT KAUAI

21.80N 159.35W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE  S  S  S  S  S SE SE SE SE SE SE SE SE SE SE SE SE SE

WIND SPD         21 21 24 20 23 21 21 21 13 13 10 10 10 10 10 10 10 10 10 10 11

WIND GUST        27 27 31 26 30 27 27 27 14 14 11 11 10 10 11 11 11 11 11 11 12

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  W  W  W  W  W  W  W  W  W SW  S  W  W  W  W

WAVE HGT          5  4  4  4  4  4  4  4  4  4  4  4  3  4  4  4  4  4  4  4  4

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                             N  N  N  N

WAVE HGT                                                             1  1  1  1

PERIOD                                                              10 10 10 10

-------------------------------------------------------------------------------

WAVE DIR          E  E  S  S  S  E  S SE  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          8  8  9  9  8  8  8  8  5  5  5  5  5  5  5  5  5  5  5  5  5

PERIOD            7  7  7  7  7  7  7  7  6  6  5  6  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      9  9 10 10  9  9  9  9  6  6  6  6  6  6  6  6  6  6  6  6  6

CLOUDS           BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK SC

POP 12HR                    100          90          90          90          80

RAIN SHWRS        O  O  O  O  O  O  O  O  O  O  O  O  O  O  L  L  O  O  O  O  L

TSTMS                   S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE SE  E    E  E  E NE   NE NE NE NE   NE

WIND SPD      11 10  7    8 12 14 15   14 15 16 15   13

WIND GUST     12 10  7    8 14 16 18   16 18 18 18   15

-------------------------------------------------------------------------------

WAVE DIR       W  W  W   SW  S  S  S    S  S  S  S    S

WAVE HGT       4  4  4    4  4  3  3    2  1  1  1    1

PERIOD        11 11 11   11 11 10 11   17 17 18 18   17

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N  N  N    N

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        10 10  9    9  9  9  8    8  8  8  8    8

-------------------------------------------------------------------------------

SIG WAVE HGT   6  6  6    6  5  4  4    4  4  4  4    4

CLOUDS        SC SC FW   FW FW FW FW   FW FW FW FW   FW

POP 12HR         60      30    20      20    20

PHZ111-301400-

EK FAD BUOY HANALEI KAUAI

22.30N 159.43W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE SE SE SE SE SE SE SE SE SE SE SE SE SE SE SE SE

WIND SPD         24 25 30 21 18 18 15 13 13 13 11 11 12 12 12 12 12 12 12 12 12

WIND GUST        31 32 39 27 23 23 19 16 14 14 13 13 13 13 13 13 13 13 14 14 13

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W

WAVE HGT          1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  3  3  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          6  6  7  7  7  6  6  6  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD            7  7  7  7  7  7  7  7  6 14 14 14 13 13 13 13 13 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  7  7  7  6  6  6  4  4  4  4  4  5  5  5  5  5  5  5  5

CLOUDS           BK BK BK BK BK BK SC SC SC SC SC SC SC SC SC SC SC SC FW FW FW

POP 12HR                     70          60          40          40          30

RAIN SHWRS        L  L  L  L  L  L  C  C  C  C  C  C  C  C  C  C  C  C  C  C  C

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE SE SE    E  E  E  E    E  E  E NE   NE

WIND SPD      12 11 11   10 12 14 13   11 13 11  9    8

WIND GUST     13 13 12   11 13 16 15   13 14 12 10    9

-------------------------------------------------------------------------------

WAVE DIR       W  W  W    W  W  W

WAVE HGT       1  1  1    1  1  1

PERIOD        11 11 11   11 11  8  8    7  7  7  7   17

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N  N  N    N

WAVE HGT       3  3  3    3  3  3  2    2  2  2  3    3

PERIOD         9  9  9    9  9  9  8    8 11 11 13   13

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  4    4  4  4  4    4  4  4  5    5

CLOUDS        FW FW SC   SC SC FW FW   FW FW FW SC   SC

POP 12HR         30      30    20      20    30

PHZ112-301400-

KK FAD BUOY WAIMEA KAUAI

21.85N 159.72W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE  S  S  S  S  S SE SE SE SE SE SE SE SE SE SE SE SE SE

WIND SPD         23 23 21 21 22 29 20 18 13 13 12 12 13 13 13 13 12 12 12 12 13

WIND GUST        30 30 27 27 28 38 26 23 15 15 13 13 14 14 15 15 13 13 14 14 14

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W

WAVE HGT          5  4  5  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                         NW NW NW NW NW

WAVE HGT                                                          2  2  2  2  2

PERIOD                                                            9  9  9  9  9

-------------------------------------------------------------------------------

WAVE DIR          S SE  S SE  S  S  S  S  E  E  E SE  E SE SE SE SE SE SE SE SE

WAVE HGT          8  8  8  8  8  8  8  7  5  4  5  4  4  4  4  4  4  4  4  4  4

PERIOD            7  7  7  7  7  7  7  7  6  6  5  6  5  6  5  6  5  6  6  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      9  9  9  9  9  9  9  8  6  6  6  6  6  6  6  6  6  6  6  6  6

CLOUDS           OV OV OV OV BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK SC

POP 12HR                     90          80          80          80          60

RAIN SHWRS        O  O  O  O  O  O  O  O  O  O  O  O  O  O  L  L  L  L  L  L  C

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE SE SE    E  E  E  E    E NE NE NE   NE

WIND SPD      13 12 10    8  9  9 10   10  7  6  7    7

WIND GUST     14 14 10    8 10  9 10   11  7  7  7    7

-------------------------------------------------------------------------------

WAVE DIR       W  W  W    W  W SW  S    S  S  S  S    S

WAVE HGT       4  4  4    4  4  3  3    2  2  1  1    1

PERIOD        11 11 11   11 11  9  9   17 17 18 18   17

-------------------------------------------------------------------------------

WAVE DIR      NW NW NW    N  N NW NW   NW NW NW NW   NW

WAVE HGT       2  1  1    1  1  1  1    1  1  1  2    2

PERIOD         9  9  9    9  9 14 14   13 12 11 13   13

-------------------------------------------------------------------------------

SIG WAVE HGT   6  6  6    6  5  4  3    3  4  4  4    4

CLOUDS        SC SC SC   FW FW SC FW   FW FW FW FW   FW

POP 12HR         50      30    10      10    10

PHZ112-301400-

PP FAD BUOY KOLOA KAUAI

21.79N 159.57W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE  S  S  S  S  S  S SE SE SE SE SE SE SE SE SE SE SE SE SE

WIND SPD         19 21 23 20 21 25 21 21 13 13 10 10 10 10 11 11 11 11 11 11 12

WIND GUST        24 27 30 26 27 32 27 27 15 15 10 10 11 11 12 12 12 12 12 12 13

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W

WAVE HGT          5  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                         NW NW NW NW NW

WAVE HGT                                                          1  1  1  1  1

PERIOD                                                            9  9  9  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E SE SE  S  S  S  S  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          8  9  9  8  8  8  8  8  5  5  5  5  5  5  5  5  5  5  5  5  5

PERIOD            7  7  7  7  7  7  7  7  6  6  5  6  6  6  6  6  6  6  6  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      9 10 10  9  9  9  9  9  6  6  6  6  6  6  6  6  6  6  6  6  6

CLOUDS           OV OV BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK SC

POP 12HR                     90          90          90          80          70

RAIN SHWRS        O  O  O  O  O  O  O  O  O  O  O  O  O  O  L  L  L  L  L  L  L

TSTMS                   S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE SE SE    E  E  E  E   NE NE NE NE   NE

WIND SPD      12 11  9    9 12 14 15   15 14 14 13   11

WIND GUST     13 12  9    9 13 16 18   17 16 17 14   12

-------------------------------------------------------------------------------

WAVE DIR       W  W  W    W SW  S  S    S  S  S  S    S

WAVE HGT       4  4  4    4  4  3  3    2  2  1  1    1

PERIOD        11 11 11   11 11  9 11   17 17 18 18   17

-------------------------------------------------------------------------------

WAVE DIR      NW NW NW            NW   NW NW NW NW   NW

WAVE HGT       1  1  1             1    1  1  1  1    1

PERIOD         9  9  9            13   13 12 11 13   13

-------------------------------------------------------------------------------

SIG WAVE HGT   6  6  6    6  5  4  4    4  4  4  4    4

CLOUDS        SC SC FW   FW FW SC FW   FW FW FW FW   FW

POP 12HR         60      30    20      10    10

PHZ111-301400-

WK FAD BUOY WAILUA KAUAI

22.02N 159.22W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE  S  S  S  S  S  S  S  S  S  S  S  S  S SE SE SE SE SE

WIND SPD         20 22 24 25 22 22 22 22 13 13  8  8  9  9 11 11  9  9  9  9  9

WIND GUST        26 28 31 32 28 28 28 28 14 14  8  8  9  9 12 12  9  9  9  9 10

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          3  3  3  2  2  2  2  2  1  1  1  1  1  1  1  1  2  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          1  2  2  2  2

PERIOD                                                           10 10 10 10 10

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  S  S  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          7  8  9  9  9  8  8  8  5  5  5  5  5  5  5  5  5  5  5  5  5

PERIOD            7  7  7  7  7  7  7  7  6  6  6  6  6  6  6  6  6  6  6  6  6

-------------------------------------------------------------------------------

SIG WAVE HGT      8  9 10  9  9  8  8  8  5  5  5  5  5  5  5  5  5  6  6  6  6

CLOUDS           BK BK OV OV BK BK BK BK BK BK BK BK BK BK BK BK SC SC SC SC SC

POP 12HR                     90          80          90          80          70

RAIN SHWRS        L  L  O  O  O  O  O  O  O  O  O  O  O  O  L  L  L  L  L  L  C

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE SE  E    E  E  E NE   NE NE NE NE   NE

WIND SPD       9  9  8   10 11 13 14   12 13 13 12   11

WIND GUST     10 10  8   10 12 15 16   13 15 14 14   12

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       3  3  2    2  1  1  1    1  1  1  1    1

PERIOD        11 11 11   11 11 12 12   11 18 18 18   17

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N  N  N    N

WAVE HGT       2  3  3    3  2  2  2    2  2  2  2    2

PERIOD        10  9  9    9  9  9  8    8  8  8  8    8

-------------------------------------------------------------------------------

SIG WAVE HGT   6  6  5    5  5  4  4    4  4  4  5    5

CLOUDS        SC FW SC   SC SC FW FW   FW FW FW SC   SC

POP 12HR         50      30    20      20    20

PHZ113-301400-

MID POINT KAUAI CHANNEL

21.77N 158.82W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE  S  S  S SE SE SE SE SE SE SE SE SE SE SE SE SE

WIND SPD         18 20 22 20 22 22 22 21 16 16 15 15 15 15 14 14 11 11 11 11 10

WIND GUST        23 26 28 26 28 28 28 27 19 19 17 17 18 18 16 16 12 12 12 12 10

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  S  S  S SW SW  S  S  S  S  S  S  S  S  W  W

WAVE HGT          4  4  4  4  4  4  4  4  4  3  3  3  3  3  3  3  4  4  4  4  4

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  3  3  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          6  7  8  8  8  8  8  8  5  5  5  5  5  5  5  5  5  5  5  5  5

PERIOD            6  6  6  7  7  6  7  7  6  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      7  8  9  9  9  9  9  9  6  6  6  6  6  6  6  6  7  7  7  7  7

CLOUDS           BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK BK SC

POP 12HR                     80          90          90          80          70

RAIN SHWRS        L  L  O  O  O  O  O  O  O  O  O  O  O  O  L  L  L  L  L  L  C

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE SE  E    E  E  E  E    E NE NE NE   NE

WIND SPD      10  8  8   11 13 16 18   15 15 16 16   15

WIND GUST     10  8  8   13 15 19 21   17 18 18 19   17

-------------------------------------------------------------------------------

WAVE DIR       W SW  S    S  S  S  S    S  S  S  S    S

WAVE HGT       4  4  4    4  3  3  2    2  1  1  1    1

PERIOD        11 11 11   11 11 12 12   17 17 18 18   17

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N  N  N    N

WAVE HGT       3  3  3    3  3  3  2    2  2  2  2    3

PERIOD         9  9  9    9  9  9  8    8 11 11 10   12

-------------------------------------------------------------------------------

SIG WAVE HGT   7  6  6    6  6  5  5    5  5  5  5    5

CLOUDS        SC SC SC   SC FW FW FW   FW FW FW FW   SC

POP 12HR         40      30    20      20    20

PHZ115-301400-

MAMALA BAY OAHU

21.27N 157.86W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE SE  S  S SE SE SE SE SE SE SE SE  E  E  E  E  E

WIND SPD         11 11 14 17 20 18 17 16 10 10 10 10  9  9  9  9  6  6  6  6  7

WIND GUST        13 13 17 21 26 23 21 20 10 10 11 11  9  9  9  9  7  7  7  7  7

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          4  4  3  3  3  3  3  3  3  3  3  2  2  2  2  2  3  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S SW SW

WAVE HGT          3  4  4  4  4  5  5  5  3  3  3  3  3  3  3  3  3  3  3  3  3

PERIOD            6  6  6  6  6  6  6  6  5  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      5  6  5  5  5  6  6  6  4  4  4  4  4  4  4  4  4  4  4  4  4

CLOUDS           SC SC BK BK BK BK SC SC BK BK BK BK SC SC SC SC SC SC SC SC FW

POP 12HR                     70          70          70          60          30

RAIN SHWRS        C  C  L  L  L  L  L  L  L  L  L  L  L  L  C  C  C  C  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E NE   NE NE NE NE   NE

WIND SPD       7  7  7    9 10 13 13   12 13 14 13   11

WIND GUST      7  7  7    9 11 15 15   14 15 17 15   13

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       3  3  3    3  2  2  1    1  1  1  1    1

PERIOD        11 11 11   11 12 12 12   12 18 18 18   18

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    4  4  4  4    4  4  4  4    4

CLOUDS        FW FW FW   FW FW FW FW   FW FW FW FW   FW

POP 12HR         20      10    10      10    10

PHZ118-301400-

P FAD BUOY PENGUIN BANK OAHU

20.77N 157.82W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE SE  S  S SE SE SE SE SE SE SE SE SE SE SE SE SE

WIND SPD         14 14 16 19 21 21 19 19 15 15 14 14 13 13 11 11 12 12 11 11  9

WIND GUST        17 17 20 24 27 27 24 24 18 18 17 17 15 15 12 12 13 13 13 13  9

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          4  4  3  3  3  3  3  3  3  3  3  2  2  2  2  2  3  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          W NW NW NW NW

WAVE HGT                                                          1  1  1  1  1

PERIOD                                                            9  9  9  9  9

-------------------------------------------------------------------------------

WAVE DIR         SE SE SE SE SE SE SE SE SE  S  S  S  S  S  S  S  S  S  S SE SE

WAVE HGT          4  5  5  5  5  6  6  6  4  4  4  4  4  4  4  4  4  4  4  3  3

PERIOD            6  6  6  6  6  6  6  6  5  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  6  7  7  7  7  7  5  5  5  5  5  5  5  5  5  5  5  4  4

CLOUDS           BK BK BK BK BK BK SC SC BK BK BK BK SC SC SC SC SC SC SC SC FW

POP 12HR                     70          70          80          70          50

RAIN SHWRS        C  C  L  L  L  L  L  L  L  L  O  O  L  L  C  C  C  C  C  C  C

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE  E  E    E NE NE NE   NE NE NE NE   NE

WIND SPD       9  6  6    6  8  9 16   13 14 15 19   18

WIND GUST      9  7  7    7  8  9 19   15 16 18 23   22

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       3  3  3    3  2  2  1    1  1  1  1    2

PERIOD        11 11 11   11 12 12 12   12 18 18 18   18

-------------------------------------------------------------------------------

WAVE DIR      NW NW SW   NE  N NE NW   NW NW NW NW   NW

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    2

PERIOD         9  9  9    9  9  9  9   12 12 11 10   12

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    4  4  4  4    4  4  4  5    5

CLOUDS        FW FW FW   SC FW FW FW   FW FW FW FW   SC

POP 12HR         30      30    20      20    10

PHZ115-301400-

R FAD BUOY MAKAHA OAHU

21.46N 158.28W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE SE  S  S SE SE SE SE SE SE SE SE SE SE SE SE SE

WIND SPD         18 17 20 21 22 21 23 21 12 12 12 12 12 12 12 12  8  8  7  7  6

WIND GUST        23 21 26 27 28 27 30 27 14 14 13 13 13 13 14 14  9  9  7  7  7

-------------------------------------------------------------------------------

WAVE DIR          W  W  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          4  4  4  4  3  3  3  3  3  3  3  3  3  3  3  3  3  4  4  4  4

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                         NW NW NW  N  N

WAVE HGT                                                          2  2  2  2  2

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S SW SW

WAVE HGT          4  4  5  6  6  6  6  6  4  4  4  3  3  3  4  3  3  3  3  3  3

PERIOD            6  6  6  6  6  6  6  6  5  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  7  7  7  7  7  7  5  5  5  4  4  4  5  5  5  5  5  5  5

CLOUDS           SC SC BK BK SC SC BK BK BK BK BK BK SC SC SC SC SC SC SC SC FW

POP 12HR                     60          50          60          40          30

RAIN SHWRS        C  C  L  L  C  C  C  C  C  C  L  L  C  C  C  C  C  C  C  C

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE  S  E    E  E NE NE   NE NE NE NE   NE

WIND SPD       6  4  4    5  6  4  9    7  8 13 11   11

WIND GUST      7  7  7    7  7  7  9    7  8 14 13   12

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       4  4  3    3  3  2  2    1  1  1  1    2

PERIOD        11 11 11   11 12 12 12   17 17 18 18   17

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N   NW NW NW NW   NW

WAVE HGT       2  2  2    2  2  1  1    2  2  2  2    2

PERIOD         9  9  9    9  9  9 13   13 12 11 10   12

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  5    5  4  4  3    3  3  4  4    4

CLOUDS        FW SC SC   FW FW FW FW   FW FW FW FW   FW

POP 12HR         10      10     5      10     5

PHZ114-301400-

U FAD BUOY KANEOHE OAHU

21.58N 157.69W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E SE  S SE  S  S  S SE SE SE SE SE SE SE SE  E  E  E  E  E

WIND SPD         17 17 15 15 18 20 20 19 11 11 10 10 12 12 12 12 13 13 13 13 13

WIND GUST        21 21 19 19 23 26 26 24 12 12 11 11 13 13 14 14 15 15 14 14 15

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  3  3  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          6  6  6  6  6  6  6  6  5  5  4  4  4  4  4  4  4  4  4  4  4

PERIOD            7  6  6  6  6  6  6  6 12 14 14 14 13 13 13 13 13 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  6  6  6  6  6  6  5  5  4  4  4  4  4  4  4  5  5  5  5

CLOUDS           SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC FW

POP 12HR                     40          70          70          50          30

RAIN SHWRS        C  C  C  C  C  C  L  L  L  L  L  L  C  C  C  C  C  C  C  C  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E  E    E  E NE NE   NE

WIND SPD      13 13 14   11 12 14 14   13 14 12 13   12

WIND GUST     15 14 16   12 13 16 16   15 16 14 15   14

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N NW NW   NW

WAVE HGT       3  3  3    3  3  2  2    2  2  2  2    3

PERIOD         9  9  9    9  9  9  8   12 12 11 11   12

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  5    5  4  4  4    4  4  4  5    5

CLOUDS        FW FW FW   SC FW FW FW   FW FW FW FW   SC

POP 12HR         20      30    20      30    30

PHZ114-301400-

II FAD BUOY HALEIWA OAHU

21.74N 158.22W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E SE SE SE SE  S  S SE SE SE SE SE SE SE SE  E  E  E  E  E

WIND SPD         17 16 12 12 12 11 17 20 10 10  9  9  8  8  7  7 10 10 11 11 11

WIND GUST        21 20 15 15 15 13 21 26 11 11  9  9  9  9  7  7 11 11 12 12 12

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W

WAVE HGT          4  4  3  3  3  3  3  3  2  2  2  2  2  2  2  2  3  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  3  3  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          5  5  5  5  5  5  5  5  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD            7  7  7  6  6  6  6  6  6  5  6  8  6  5  6  6  6  5  5  8  8

-------------------------------------------------------------------------------

SIG WAVE HGT      7  7  6  6  6  6  6  6  5  5  5  5  5  5  5  5  5  6  6  6  6

CLOUDS           SC SC BK BK BK BK BK BK SC SC SC SC SC SC BK BK FW FW FW FW FW

POP 12HR                     50          70          60          60          40

RAIN SHWRS        C  C  C  C  L  L  L  L  L  L  C  C  L  L  L  L  C  C  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E  E    E  E NE NE   NE

WIND SPD      11 10 12   12 13 17 17   15 17 15 16   14

WIND GUST     12 10 14   13 15 20 21   18 20 18 19   16

-------------------------------------------------------------------------------

WAVE DIR       W SW SW   SW SW SW SW   SW SW SW SW   SW

WAVE HGT       3  3  3    2  2  1  1    1  1  1  1    1

PERIOD        11 11 11   11 11 12 12   16 17 18 18   17

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N  N NW   NW

WAVE HGT       3  3  3    3  3  2  2    2  2  2  3    3

PERIOD         9  9  9    9  9  9  8   12 12 11 11   12

-------------------------------------------------------------------------------

SIG WAVE HGT   6  6  5    5  4  4  4    4  4  4  4    5

CLOUDS        FW FW SC   FW FW FW FW   FW FW FW FW   FW

POP 12HR         20      20    10      20    20

PHZ114-301400-

LL FAD BUOY HAUULA OAHU

21.75N 157.76W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E SE SE SE SE SE SE SE SE SE SE SE SE SE SE SE  E  E SE SE  E

WIND SPD         19 17 19 19 17 18 20 19 14 14 13 13 14 14 14 14 15 15 15 15 15

WIND GUST        24 21 24 24 21 23 26 24 16 16 15 15 16 16 16 16 17 17 18 18 17

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  W  W  W  W  W  W  W  W        W  W  W  W  W

WAVE HGT          1  1  1  1  1  1  1  1  1  1  1  1  1  1        1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  3  3  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          6  6  6  6  6  6  6  6  5  5  5  5  4  4  4  4  4  4  4  4  4

PERIOD            7  6  6  6  6  6  6  6  6 14 14 14 13 13 13 13 13 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  6  6  6  6  6  6  5  5  5  5  4  4  4  4  5  5  5  5  5

CLOUDS           SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC FW FW FW FW FW

POP 12HR                     50          70          70          60          30

RAIN SHWRS        C  C  C  C  C  C  L  L  L  L  L  L  L  L  C  C  C  C  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E  E    E  E NE NE   NE

WIND SPD      15 15 15   13 13 15 15   15 16 12 14   13

WIND GUST     17 17 17   14 15 18 18   18 19 14 15   14

-------------------------------------------------------------------------------

WAVE DIR       W  W  W

WAVE HGT       1  1  1

PERIOD        11 11 11   11 13 13 12   20 20 20 18   18

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N NE  N NW   NW

WAVE HGT       3  3  3    3  3  2  2    2  2  2  2    3

PERIOD         9  9  9    9  9  9  8   12 12 11 11   12

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  5    5  4  4  4    4  4  4  5    5

CLOUDS        FW FW FW   FW FW FW FW   FW FW FW FW   SC

POP 12HR         20      30    20      30    30

PHZ114-301400-

UH WAIMEA BUOY OAHU

21.67N 158.12W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E  E  E  E SE  S  S SE SE SE SE SE SE SE SE  E  E  E  E  E

WIND SPD         10 11  7  8  9 12 17 14 10 10  9  9  9  9  8  8  9  9 10 10 10

WIND GUST        12 13  8  9 11 15 21 17 11 11  9  9  9  9  8  8  9  9 11 11 10

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W  W

WAVE HGT          3  2  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  2  2  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          3  3  3  3  3  3  3  3  2  2  2  2  2  2  2  2  2  2  2  2  2

PERIOD            7  7  7  7  7  7  7  7  5  5 14 14 13  9 13 13  9  9  9 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      5  4  4  4  4  3  3  3  2  2  2  2  2  2  3  3  3  3  3  4  4

CLOUDS           SC SC SC SC SC SC BK BK SC SC SC SC SC SC SC SC FW FW FW FW FW

POP 12HR                     50          60          50          50          30

RAIN SHWRS        C  C  C  C  C  C  L  L  C  C  C  C  C  C  C  C  C  C  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E  E    E  E NE NE   NE

WIND SPD      10  8 10   10 11 13 13   11 13 14 13   12

WIND GUST     10  9 10   10 12 14 15   12 15 16 14   13

-------------------------------------------------------------------------------

WAVE DIR       W  W  W    W  W  W  W    W  W  W  W    W

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        11 11 11   11 11  7  7   17 17 18 18   17

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N  N NW   NW

WAVE HGT       3  3  3    3  3  2  2    2  2  2  3    3

PERIOD         9  9  9    9  9  9  8   12 12 11 11   12

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    4  3  3  3    3  3  3  3    4

CLOUDS        FW SC SC   FW FW FW FW   FW FW FW FW   FW

POP 12HR         20      20    20      20    20

PHZ116-301400-

MID POINT KAIWI CHANNEL

21.21N 157.50W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE  S SE  S SE SE  S  S SE SE SE SE SE SE SE SE  E  E  E  E  E

WIND SPD          6 11 12 14 19 20 18 18 11 11 12 12  7  7  7  7  7  7  7  7  7

WIND GUST         7 13 15 17 24 26 23 23 12 12 13 13  7  7  7  7  7  7  7  7  7

-------------------------------------------------------------------------------

WAVE DIR          W  W  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S SW SW SW SW

WAVE HGT          4  4  3  3  3  3  3  3  3  3  3  2  2  2  2  2  3  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  2  2  3  3

PERIOD                                                           10 10 10 10 10

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E SE SE  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          5  5  5  5  5  6  6  6  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD            6  6  6  6  6  6  6  6  5  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  6  6  6  7  7  7  5  5  5  5  5  5  5  5  5  5  5  6  6

CLOUDS           SC SC SC SC SC SC SC SC SC SC BK BK SC SC FW FW SC SC FW FW FW

POP 12HR                     50          60          60          50          30

RAIN SHWRS        C  C  C  C  C  C  L  L  L  L  L  L  C  C  C  C  C  C  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E NE NE    E  E NE NE   NE

WIND SPD       7  8  9   11 12 17 17   16 16 17 17   17

WIND GUST      7  8  9   12 14 20 21   19 19 20 20   20

-------------------------------------------------------------------------------

WAVE DIR      SW SW SW    S  S  S  S    S  S  S  S    S

WAVE HGT       3  3  3    3  3  2  2    1  1  1  1    2

PERIOD        11 11 11   11 12 12 12   12 18 18 18   18

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N NW NW    N

WAVE HGT       3  3  3    3  2  2  2    2  2  2  2    2

PERIOD        10  9  9    9  9  9  8    8  8 10 10   11

-------------------------------------------------------------------------------

SIG WAVE HGT   6  6  6    5  4  4  4    4  4  4  4    4

CLOUDS        FW FW FW   FW FW FW FW   FW FW FW FW   SC

POP 12HR         10      20    10      10    10

PHZ117-301400-

O FAD BUOY KALAUPAPA MOLOKAI

21.30N 157.05W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E  E  E  E  E  E  E SE SE  E  E  E  E  E  E  E  E  E  E  E

WIND SPD         19 19 14 15 17  8 14 13 10 10  8  8 12 12 12 12 13 13 12 12 14

WIND GUST        24 24 17 19 21  9 17 16 10 10  8  8 14 14 14 14 15 15 14 14 16

-------------------------------------------------------------------------------

WAVE DIR          W  W  W  W  W  W  W  W  W  W  W                 W  W  W  W  W

WAVE HGT          1  1  1  1  1  1  1  1  1  1  1                 1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  3  3  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          6  6  6  5  5  5  5  5  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD            6  6  6  6  6  6  6  6 12 14 14 14 13 13 13 13 13 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  6  5  5  5  5  5  4  4  4  4  4  4  4  4  5  5  5  5  5

CLOUDS           SC SC SC SC SC SC SC SC SC SC SC SC FW FW FW FW FW FW FW FW SC

POP 12HR                     20          50          40          30          20

RAIN SHWRS              S  S  C  C  C  C  C  C  C  C  C  C  C  C  S  S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E  E    E  E  E NE   NE

WIND SPD      14 14 13   13 14 18 17   16 18 17 16   15

WIND GUST     16 16 15   15 16 22 21   19 21 20 19   18

-------------------------------------------------------------------------------

WAVE DIR       W  W

WAVE HGT       1  1

PERIOD        11 11 11   11 11 15 15   17 17 18 18   18

-------------------------------------------------------------------------------

WAVE DIR       N  N  W    N  N  N  N    N  N NW NW   NW

WAVE HGT       3  3  3    3  2  2  2    2  2  2  2    3

PERIOD         9  9  9    9  9  9  8   12 12 11 11   12

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  5    4  4  4  4    4  4  5  5    5

CLOUDS        SC SC FW   FW FW FW FW   FW FW FW FW   FW

POP 12HR         20      20    20      20    20

PHZ120-301400-

MID POINT PAILOLO CHANNEL

21.05N 156.72W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E  E  E  S  E SW  S  E  E  E  E  E  E  E  E  E  E  E  E  E

WIND SPD         17 14 14 15 12 12 13 12 14 14 13 13 14 14 15 15 15 15 14 14 15

WIND GUST        22 17 17 19 14 14 17 14 15 15 14 14 16 16 17 17 17 17 16 16 17

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          S SE SE SE SE

WAVE HGT                                                          1  1  1  1  1

PERIOD                                                           10 11 11 10 10

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          5  5  5  5  4  4  4  4  4  4  4  4  4  3  4  3  3  3  3  3  3

PERIOD            6  6  6  6  6  6  6  6 12 11 14 14 13 13 13 13 13 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      5  5  5  5  4  4  4  4  4  4  4  4  4  3  4  3  3  3  3  3  3

CLOUDS           FW FW SC SC SC SC SC SC SC SC SC SC FW FW FW FW FW FW FW FW FW

POP 12HR                     10          30          30          20          20

RAIN SHWRS                    S  S  C  C  C  C  C  C  S  S  S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E NE NE    E  E NE NE   NE

WIND SPD      15 15 15   14 16 18 17   17 18 17 17   16

WIND GUST     17 18 17   16 19 21 21   20 21 21 20   18

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        11 11 11   11 12 12 12   11 11 12 18   18

-------------------------------------------------------------------------------

WAVE DIR      SE NE  N    N  N  N  N    N  N  N  N    N

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        10 10 10    9  9  9  9    8  8  8  8    9

-------------------------------------------------------------------------------

SIG WAVE HGT   3  3  3    3  3  3  3    3  3  3  3    3

CLOUDS        FW SC FW   FW FW FW SC   FW FW FW FW   FW

POP 12HR         20      20    20      20    20

PHZ118-301400-

CC FAD BUOY KAENA PT LANAI

20.85N 157.14W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE  S  S  S SE SE SE SE SE SE SE SE  E  E  E  E  E

WIND SPD         15 13 14 14 15 16 17 16 12 12 11 11  8  8  8  8  7  7  5  5  4

WIND GUST        19 16 17 17 19 20 21 20 13 13 12 12  8  8  9  9  7  7  7  7  7

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          4  3  3  3  3  3  3  3  3  3  2  2  2  2  2  2  2  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                         NW NW NW NW NW

WAVE HGT                                                          1  1  1  1  1

PERIOD                                                            9 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR         SE SE  S  S  S  S  S  S  S SW  S  S  S SW  S SW SW SW SW  W  W

WAVE HGT          3  4  4  4  4  4  4  4  3  3  3  3  3  3  3  3  3  3  3  3  3

PERIOD            5  5  5  6  5  6  5  6  5  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      5  5  5  5  5  5  5  5  5  4  4  4  4  4  4  4  4  4  4  4  4

CLOUDS           SC SC SC SC SC SC SC SC SC SC SC SC SC SC FW FW FW FW FW FW FW

POP 12HR                     30          30          40          30          10

RAIN SHWRS        S  S  C  C  C  C  C  C  C  C  C  C  C  C  C  C

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E SE  E   NE  E  E NE   NE  E NE NE   NE

WIND SPD       4  6  6    5  6  7 11    9  9 10 12   10

WIND GUST      7  7  7    7  7  7 13    9  9 11 13   11

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       3  3  3    3  2  2  2    1  1  1  2    2

PERIOD        11 11 11   11 12 12 12   12 20 20 18   18

-------------------------------------------------------------------------------

WAVE DIR      NW NW NW    N NW NW NW   NW NW NW NW   NW

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD         9  9  9    9  9  9 13   13 12 11 11   12

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    4  3  3  3    3  3  3  3    3

CLOUDS        FW FW SC   FW FW FW FW   FW FW CL CL   FW

POP 12HR          5       5     5       5     0

PHZ118-301400-

KAUMALAPAU HARBOR

20.79N 157.00W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE SE  S  S SE SE SE SE SE SE SE SE  E  E NE NE SE

WIND SPD         14 13 14 12 14 14 14 14 11 11  9  9  7  7  8  8  5  5  3  3  3

WIND GUST        17 16 17 16 17 17 17 17 13 13 10 10  7  7  7  7  7  7  7  7  7

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S SW  S SW  S SW SW SW SW SW SW  W  W

WAVE HGT          3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  2  2

PERIOD            5  5  5  6  5  6  5  5  5  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  2  2

CLOUDS           SC SC SC SC FW FW SC SC FW FW SC SC SC SC SC SC SC SC FW FW FW

POP 12HR                     30          20          30          30          20

RAIN SHWRS        S  S  C  C  S  S  S  S  C  C  C  C  C  C  C  C  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE SE SE   NE NE  E NE    E  E  E NE   NE

WIND SPD       3  5  4    4  4  3  9    5  4  5  9    8

WIND GUST      7  7  7    7  7  7  9    7  7  7  9    8

-------------------------------------------------------------------------------

SIG WAVE HGT   2  2  2    2  2  1  0    0  0  0  0    0

CLOUDS        FW SC SC   FW FW FW FW   FW FW FW CL   FW

POP 12HR         10      10    10      10    10

PHZ117-301400-

DD FAD BUOY OPANA PT MAUI

21.03N 156.25W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E SE SE SE SE SE SE SE  E  E  E  E  E  E  E  E  E  E  E  E  E

WIND SPD         23 23 20 19 18 17 17 19 17 17 14 14 17 17 19 19 17 17 15 15 17

WIND GUST        30 30 26 24 23 21 21 24 20 20 17 17 21 21 22 22 20 20 18 18 20

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  3  3  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          6  6  6  6  5  5  5  5  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD           13 13  6 12 12  6  6  6 12 13 14 14 13 13 13 13 13 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  6  6  5  5  5  5  4  4  4  4  4  4  4  4  4  5  5  5  5

CLOUDS           FW FW SC SC SC SC SC SC SC SC SC SC FW FW FW FW FW FW FW FW FW

POP 12HR                      5          30          20          20          10

RAIN SHWRS                    S  S  C  C  S  S  S  S  S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E  E    E  E  E  E   NE

WIND SPD      17 18 16   14 15 17 15   16 17 13 12   11

WIND GUST     20 21 19   16 18 20 17   19 21 15 14   12

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N NW NW   NW

WAVE HGT       3  3  3    2  2  2  2    2  2  2  3    3

PERIOD         9  9  9    9  9  9  8   13 13 12 11   12

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  4    4  4  4  4    4  4  4  4    4

CLOUDS        FW FW FW   FW FW FW SC   SC FW FW FW   FW

POP 12HR         10      10    20      20    20

PHZ117-301400-

FF FAD BUOY PUKAULUA PT MAUI

20.84N 155.73W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE  E SE SE SE SE SE SE SE SE SE SE  E  E  E  E  E  E  E  E  E

WIND SPD         16 17 17 16 17 18 18 18 14 14 14 14 15 15 13 13 13 13 14 14 15

WIND GUST        20 21 21 20 21 23 23 23 16 16 17 17 17 17 15 15 15 15 16 16 17

-------------------------------------------------------------------------------

WAVE DIR         SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW

WAVE HGT          2  2  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  3  3  3  3

PERIOD                                                           10 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          5  5  6  5  5  6  5  5  5  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD           13 13  7 12 12  6  5  6 12 13 14 14 13 13 13 13 13 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  6  5  5  6  5  5  5  4  4  4  4  4  5  5  5  5  5  5  5

CLOUDS           FW FW SC SC FW FW FW FW SC SC SC SC FW FW FW FW FW FW SC SC SC

POP 12HR                      5           5          10           5           5

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E  E    E  E NE NE   NE

WIND SPD      15 14 13   12 12 13 13   13 13 10 10   12

WIND GUST     17 16 15   13 13 14 14   15 14 11 11   13

-------------------------------------------------------------------------------

WAVE DIR      SW SW SW   SW SW SW SW   SW SW SW SW   SW

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        11 11 11   11 12 12 12   12 11 18 18   18

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N NW NW   NW

WAVE HGT       3  3  3    2  2  2  2    2  2  2  3    3

PERIOD         9  9  9    9  9  9  8   13 13 12 11   12

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  5    4  4  4  4    4  4  4  5    5

CLOUDS        SC FW FW   FW FW FW SC   FW FW FW FW   SC

POP 12HR          5      10    10      20    20

PHZ118-301400-

LA FAD BUOY LAHAINA MAUI

20.68N 156.71W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE SE  S SW SE SE  E  E  E  E SE SE  E  E NE NE  E

WIND SPD         18 20 20 11 12 10  9  9 10 10  8  8  7  7  8  8  7  7  5  5  5

WIND GUST        23 26 26 16 16 12 11 11 11 11  8  8  7  7  8  8  7  7  7  7  7

-------------------------------------------------------------------------------

WAVE DIR         SW SW SW SW SW SW SW SW  S  S  S  S  S  S  S  S  S  S  S SW SW

WAVE HGT          3  3  3  3  3  3  3  3  3  3  2  2  2  2  2  2  2  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          W  W  W  W  W

WAVE HGT                                                          1  1  1  1  1

PERIOD                                                            9 10 10 10 10

-------------------------------------------------------------------------------

WAVE DIR          E  E  E SE  S  S SW  S SW SW SW SW  W SW  W  W  W SW SW  W  W

WAVE HGT          3  4  4  3  3  3  3  3  2  2  2  2  2  2  2  2  2  2  2  2  2

PERIOD            4  4  4  6  5  6  5  5  5  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      4  5  5  5  5  4  4  4  4  4  3  3  3  3  3  3  3  4  4  4  4

CLOUDS           SC SC SC SC FW FW SC SC FW FW FW FW FW FW FW FW FW FW FW FW FW

POP 12HR                     10          10          20          10           5

RAIN SHWRS                                S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E   NE NE  E NE   NE  E  E  N    N

WIND SPD       5  8  6    5  5  6  8    5  2  5  7    7

WIND GUST      7  7  7    7  7  7  8    7  7  7  7    7

-------------------------------------------------------------------------------

WAVE DIR      SW  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       3  3  3    3  2  2  2    1  1  2  2    3

PERIOD        11 11 11   11 12 12 12   12 14 18 18   18

-------------------------------------------------------------------------------

WAVE DIR      SW  S SE   SE SE SE SE   SE SE SE

WAVE HGT       1  1  1    1  1  1  1    1  1  1

PERIOD        10 10 10    9  9  9  9    9  8  8  9   13

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    3  3  2  2    2  2  3  3    2

CLOUDS        FW FW FW   FW FW FW FW   FW FW FW FW   FW

POP 12HR          0       5     0       0     0

PHZ119-301400-

MAALAEA BAY

20.77N 156.49W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          N  N  N  N  N  N  N  S  N  N  N  N  N  N  N  N  N  N  N  N  N

WIND SPD         18 18 18 18 16 16 16  9 17 17 17 17 17 17 17 17 17 17 17 17 17

WIND GUST        23 23 23 23 20 20 20 13 20 20 20 20 20 20 20 20 20 20 20 20 20

-------------------------------------------------------------------------------

WAVE DIR         NW NW NW NW NW NW NW NW NW NW NW NW NW NW NW NW NW NW NW NW NW

WAVE HGT          1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E NW NW NW NW NW NW NW NW NW NW NW NW NW

WAVE HGT          2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2

PERIOD            5  5  5  6  6  6  5  6  5  5  5  5  5  5  5  5  5  5  5  5  5

-------------------------------------------------------------------------------

SIG WAVE HGT      1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1

CLOUDS           SC SC SC SC FW FW SC SC SC SC SC SC FW FW SC SC SC SC FW FW FW

POP 12HR                      0          10           5          10           5

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       N  N  N    N  N  N  N    N  N  N  N    N

WIND SPD      17 17 17   17 19 19 19   19 19 19 19   17

WIND GUST     20 20 20   20 23 23 23   23 23 23 23   20

-------------------------------------------------------------------------------

WAVE DIR      NW NW NW    W  W  W  W    W  W  W  W    W

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        11 11 11   11 12 12 12   13 20 20 18   18

-------------------------------------------------------------------------------

SIG WAVE HGT   1  1  1    1  1  2  2    2  2  2  2    2

CLOUDS        FW SC SC   FW FW FW SC   FW FW FW FW   FW

POP 12HR          5       5     5       5     5

PHZ121-301400-

NL FAD BUOY NUU LANDING MAUI

20.55N 156.16W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E NE  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WIND SPD         16 16 15 13 11  9  6  5 13 13 14 14 15 15 13 13 14 14 14 14 14

WIND GUST        20 20 19 16 13 11  7  7 15 15 16 16 17 17 15 15 15 15 16 16 16

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          3  3  3  3  3  3  3  3  3  3  3  3  2  2  2  2  2  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          5  5  5  5  5  5  5  5  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD           10  6  6  6  6  6  6  6 12 13 14 14 13 13 13 13 13 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      6  6  6  6  6  6  6  6  5  5  5  5  4  4  4  4  4  5  5  5  5

CLOUDS           SC SC SC SC SC SC SC SC SC SC SC SC SC SC FW FW FW FW FW FW FW

POP 12HR                     10          30          20          10          10

RAIN SHWRS                          C  C  S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E  E  E    E  E  E  E    E

WIND SPD      14 14 14   13 14 16 15   17 18 16 13   12

WIND GUST     16 16 16   15 16 19 18   20 21 19 15   13

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       3  3  3    3  3  2  2    2  2  3  3    3

PERIOD        11 11 11   11 12 12 12   12 20 20 18   18

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  5    4  4  4  4    4  4  4  4    4

CLOUDS        FW FW FW   FW FW FW SC   FW FW FW FW   FW

POP 12HR          5       5     5       5     5

PHZ121-301400-

MID POINT ALENUIHAHA CHANNEL

20.27N 156.47W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E NE NE NE  E  S  S  E  E  E  E  E  E  E  E  E  E  E  E  E

WIND SPD         15 15 15 11  6  4  2 10  6  6  8  8 14 14 16 16 17 17 18 18 17

WIND GUST        19 19 19 13  7  7  7 12  7  7  8  8 16 16 19 19 20 20 21 21 20

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          3  3  3  3  3  3  3  3  3  3  3  3  3  2  2  2  2  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          W  W  W  W  W

WAVE HGT                                                          1  1  1  1  1

PERIOD                                                            9 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          4  5  5  5  5  4  4  5  4  4  4  4  4  4  4  4  4  4  4  4  4

PERIOD           10  6  6  6  6  6  6  6 12 13 14 14 14 13 13 13 13 13 13 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      5  6  6  7  7  5  5  6  5  5  5  5  5  5  5  5  5  5  5  5  5

CLOUDS           FW FW SC SC FW FW FW FW FW FW SC SC FW FW FW FW FW FW FW FW FW

POP 12HR                     10          20          30          20          10

RAIN SHWRS                          S  S  S  S  C  C  S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E NE NE    E  E  E NE   NE

WIND SPD      17 16 17   18 19 20 19   19 21 20 19   15

WIND GUST     20 19 20   21 22 24 23   23 26 25 23   17

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       3  3  3    3  3  2  2    2  2  2  3    3

PERIOD        11 11 11   11 12 12 12   12 20 20 18   18

-------------------------------------------------------------------------------

WAVE DIR       W  W  W    W  W  W  W    W  W  W  W    W

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        10 10 10   10  9  9  9    9  9 14 14   14

-------------------------------------------------------------------------------

SIG WAVE HGT   5  5  5    5  5  5  5    5  5  5  5    5

CLOUDS        FW FW FW   FW FW FW FW   FW FW FW FW   FW

POP 12HR          5       5     0       5     5

PHZ124-301400-

A FAD BUOY SOUTH PT HAWAII

18.96N 155.56W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E NE NE  E NE NE  E  E  E  E  E  E  E  E  E  E  E NE NE  E

WIND SPD         11 12 11  8  8 11 12  9  9  9  9  9 11 11 11 11 12 12 10 10 12

WIND GUST        13 15 13  9  9 13 15 11  9  9 10 10 12 12 12 12 13 13 11 11 14

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          2  2  2  2  2  2  2  2  2  2  1  1  1  1  1  1  1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          4  4  4  4  4  4  4  4  4  3  3  3  3  3  3  3  3  3  3  3  3

PERIOD           13 13 12 12 12 12 11 11 11 13 14 14 13 13 13 13 12 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      4  4  4  4  4  4  4  4  4  4  3  3  3  3  3  3  3  3  3  3  3

CLOUDS           SC SC SC SC SC SC FW FW SC SC SC SC SC SC SC SC SC SC FW FW FW

POP 12HR                     20          30          40          30          20

RAIN SHWRS        S  S  S  S  S  S  C  C  C  C  C  C  C  C  S  S  S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E NE   NE  E  E  E    E  E  E  E    E

WIND SPD      12 12 11   11 14 17 16   15 17 15 13    9

WIND GUST     14 13 12   13 16 20 19   18 20 17 15   10

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       2  2  2    2  1  1  1    1  1  1  1    2

PERIOD        11 11 11   11 12 12 12   12 20 20 18   18

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    3  3  4  4    4  4  5  5    5

CLOUDS        FW SC SC   SC FW FW FW   FW FW FW FW   FW

POP 12HR         10      20    10      20    20

PHZ123-301400-

B FAD BUOY MILOLII HAWAII

19.19N 155.94W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          N  E SE SE SE SE SE  S  E  E  E  E SE SE SE SE  E  E  E  E  E

WIND SPD          4  1  1  5  8  7  6 13  7  7  6  6  6  6  6  6  6  6  6  6  6

WIND GUST         7  7  7  7  9  8  7 16  7  7  7  7  7  7  7  7  7  7  7  7  7

-------------------------------------------------------------------------------

WAVE DIR         SW SW SW SW  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          3  3  3  3  3  3  3  3  3  3  3  3  3  3  2  2  2  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          W  W  W  W  W

WAVE HGT                                                          2  2  2  1  1

PERIOD                                                            9 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  W SW  W  S  W  S  W SW SW  W  W  S  S

WAVE HGT          2  2  2  2  2  2  2  2  1  1  1  1  1  1  1  1  1  1  1  1  1

PERIOD            4  4  4  4  4  4  4  4  3  3  3  3  3  3  3  3  3  3  3  3  3

-------------------------------------------------------------------------------

SIG WAVE HGT      4  5  5  5  5  5  5  5  4  4  4  4  4  4  3  3  3  4  4  3  3

CLOUDS           FW FW SC SC FW FW FW FW SC SC FW FW FW FW SC SC SC SC SC SC SC

POP 12HR                      0          10           5          10          10

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E NE    E  E  E  E    E SE  S SE    N

WIND SPD       6  5  6    4  4  4  5    5  4  2  3    4

WIND GUST      7  7  7    7  7  7  7    7  7  7  7    7

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S SW SW   SW SW SW  S    S

WAVE HGT       3  3  3    3  3  3  2    2  2  2  3    3

PERIOD        11 11 11   11 12 12 12   12 20 20 18   18

-------------------------------------------------------------------------------

WAVE DIR       W  W  W    W  W  W  W    W  W  W  W   NW

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        10 10 10   10  9  9  9    9  9 10 14   14

-------------------------------------------------------------------------------

SIG WAVE HGT   3  3  3    3  3  3  3    3  3  3  3    3

CLOUDS        SC SC BK   BK SC SC SC   SC SC FW SC   SC

POP 12HR         10      10    10      10    10

PHZ122-301400-

D FAD BUOY CAPE KUMUKAHI HAWAII

19.63N 154.78W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR         SE SE SE SE SE SE SE SE SE SE SE SE  E  E  E  E  E  E  E  E  E

WIND SPD         10 10 12 13 13 11 12 12 10 10  9  9 10 10  9  9  7  7  7  7 10

WIND GUST        12 12 15 16 16 13 15 15 10 10 10 10 11 11  9  9  7  7  7  7 10

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1  1

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          N  N  N  N  N

WAVE HGT                                                          2  2  2  2  2

PERIOD                                                           10 10 10 10 10

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          4  4  4  4  4  4  4  4  4  4  3  3  3  3  3  3  3  3  3  3  3

PERIOD           13 13 12 12 12 12 11 11 11 13 14 14 13 13 13 13 12 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      5  5  5  5  5  5  4  4  4  4  3  3  3  3  3  3  4  4  4  4  4

CLOUDS           SC SC SC SC SC SC SC SC SC SC SC SC SC SC FW FW SC SC SC SC SC

POP 12HR                     10          10          20          20          20

RAIN SHWRS                                      S  S  S  S              S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E    E  E NE NE   NE NE  N  N    N

WIND SPD      10 10  8    7  7 12 12   13 12 11 12   11

WIND GUST     10 10  7    7  7 14 14   15 13 12 13   13

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        11 11 11   11 12 12 12   12 20 20 18   18

-------------------------------------------------------------------------------

WAVE DIR       N  N  N    N  N  N  N    N  N  N  N   NW

WAVE HGT       2  2  2    2  2  2  2    2  2  2  2    2

PERIOD        10  9  9    9  9  9  9   13 13 12 11   10

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    4  4  5  5    5  5  5  5    5

CLOUDS        SC FW FW   SC FW FW SC   SC FW FW SC   SC

POP 12HR         20      20    20      30    30

PHZ123-301400-

F FAD BUOY KAILUA-KONA HAWAII

19.51N 156.16W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          N  N NW NE  E  S  S  S  E  E  E  E SW SW SW SW NW NW  W  W  W

WIND SPD          5  3  2  2  1  5  8 17  3  3  2  2  2  2  3  3  3  3  4  4  4

WIND GUST         7  7  7  7  7  7  9 21  7  7  7  7  7  7  7  7  7  7  7  7  7

-------------------------------------------------------------------------------

WAVE DIR         SW SW SW SW SW SW SW SW SW SW SW  S  S  S  S  S  S  S  S SW SW

WAVE HGT          3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          W  W  W  W  W

WAVE HGT                                                          2  2  2  1  1

PERIOD                                                            9 10 10  9  9

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  W  W  W  W  W  W  W  W  W

WAVE HGT          2  2  2  2  2  3  3  3  2  2  2  2  2  2  2  2  2  2  2  2  2

PERIOD            5  5  5  5  5  5  5  5  4  4  4  4  4  4  4  4  4  4  4  4  4

-------------------------------------------------------------------------------

SIG WAVE HGT      4  4  5  5  5  5  5  5  5  4  4  4  4  4  4  4  4  4  4  4  4

CLOUDS           FW FW SC SC FW FW FW FW SC SC FW FW FW FW FW FW SC SC SC SC SC

POP 12HR                      5          10          10          10          20

RAIN SHWRS                                                        S  S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       W NW NW    N  W  S  S   NE NE  W  S    W

WIND SPD       4  4  6    4  5  5  2    3  3  2  4    3

WIND GUST      7  7  7    7  7  7  7    7  7  7  7    7

-------------------------------------------------------------------------------

WAVE DIR      SW  S  S   SW SW SW SW   SW SW SW  S    S

WAVE HGT       3  3  3    3  3  3  2    2  2  3  3    3

PERIOD        11 11 11   11 12 12 12   12 20 20 18   18

-------------------------------------------------------------------------------

WAVE DIR       W  W  W    W  W  W  W    W SW SE SE    E

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        10 10 10   10  9  9  9    9  9  8 14   14

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    4  4  3  3    3  3  4  4    4

CLOUDS        SC FW SC   SC SC FW FW   SC FW FW FW   SC

POP 12HR         20      20    10      20    10

PHZ122-301400-

SS FAD BUOY APUA PT HAWAII

19.19N 155.22W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          E  E NE  E  N SE  E SE  E  E  E  E  E  E  E  E  E  E NE NE  E

WIND SPD          7  7  3  4  5  7  7  6  7  7  8  8  9  9 10 10  9  9  7  7  9

WIND GUST         8  8  7  7  7  9  8  7  7  7  8  8  9  9 10 10  9  9  7  7 10

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S  S

WAVE HGT          3  3  3  3  3  3  3  2  2  2  2  2  2  1  1  1  1  1  1  2  2

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR          E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E

WAVE HGT          4  4  4  4  4  4  4  4  3  3  3  3  3  3  3  3  3  3  3  3  3

PERIOD           13 13 12 12 12 12 11 11 11 13 14 14 13 13 13 13 12 12 12 12 12

-------------------------------------------------------------------------------

SIG WAVE HGT      5  5  5  5  5  5  5  4  4  4  4  4  4  3  3  3  3  3  3  4  4

CLOUDS           SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC SC FW FW FW FW FW

POP 12HR                     30          30          40          30          20

RAIN SHWRS        S  S  C  C  S  S  C  C  C  C  C  C  C  C  S  S  S  S  S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR       E  E  E   NE NE  E NE   NE NE  E NE   NE

WIND SPD       9 10  9    9 11 16 14   12 14 16 13   10

WIND GUST     10 11  9   10 12 19 16   14 16 18 15   10

-------------------------------------------------------------------------------

WAVE DIR       S  S  S    S  S  S  S    S  S  S  S    S

WAVE HGT       2  2  2    2  2  1  1    1  1  1  2    2

PERIOD        11 11 11   11 12 12 12   12 20 20 18   18

-------------------------------------------------------------------------------

SIG WAVE HGT   4  4  4    4  3  4  4    4  4  4  4    4

CLOUDS        FW SC SC   FW FW FW FW   FW FW FW FW   FW

POP 12HR         10      20    10      20    10

PHZ122-301400-

XX FAD BUOY PUAKO HAWAII

20.02N 156.02W

301 PM HST TUE SEP 29 2026

DATE           09/29/26      WED 09/30/26            THU 10/01/26            FRI

HST 3HRLY     15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06

UTC 3HRLY     01 04 07 10 13 16 19 22 01 04 07 10 13 16 19 22 01 04 07 10 13 16

WIND DIR          W  W  W  W  W  S NW NW  E  E SE SE SE SE SW SW SE SE SE SE SE

WIND SPD          4  3  3  4  2  0  6  8  3  3  3  3  1  1  3  3  3  3  5  5  4

WIND GUST         7  7  7  7  7  7  7  9  7  7  7  7  7  7  7  7  7  7  7  7  7

-------------------------------------------------------------------------------

WAVE DIR         SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW SW

WAVE HGT          3  3  3  3  3  3  3  3  3  3  2  2  2  2  2  2  2  2  2  3  3

PERIOD           11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11 11

-------------------------------------------------------------------------------

WAVE DIR                                                          W  W  W  W  W

WAVE HGT                                                          1  1  1  1  1

PERIOD                                                            9 10 10 10 10

-------------------------------------------------------------------------------

WAVE DIR          S  S  S  W  W SW SW SW  W  W  W  W  W  W  W  W  W  W  W  W  W

WAVE HGT          2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2  2

PERIOD            4  4  4  4  4  5  5  6  4  5  4  5  4  5  4  5  4  5  5  4  4

-------------------------------------------------------------------------------

SIG WAVE HGT      4  4  5  5  5  4  4  4  4  4  3  3  3  3  3  3  3  3  3  4  4

CLOUDS           FW FW SC SC FW FW FW FW FW FW SC SC FW FW FW FW SC SC FW FW FW

POP 12HR                      5          10          20          10          20

RAIN SHWRS                                      S  S                    S  S

DATE           10/02/26  SAT 10/03/26  SUN 10/04/26  MON

HST 6HRLY     12 18 00   06 12 18 00   06 12 18 00   06

UTC 6HRLY     22 04 10   16 22 04 10   16 22 04 10   16

WIND DIR      SE  S  E    E NE  W NE   NE NE NE NE   NE

WIND SPD       4  3  3    5  4  2  5    6  5  9  8    6

WIND GUST      7  7  7    7  7  7  7    7  7  9  8    7

-------------------------------------------------------------------------------

WAVE DIR      SW SW SW   SW SW SW SW   SW SW SW SW   SW

WAVE HGT       3  3  2    2  2  2  2    1  1  2  2    3

PERIOD        11 11 11   11 12 12 12   12 11 18 18   18

-------------------------------------------------------------------------------

WAVE DIR       W  N  N    N  N  N  N    N  N  N  N    N

WAVE HGT       1  1  1    1  1  1  1    1  1  1  1    1

PERIOD        10 10 10   10  9  9  9    9  8  8  8    8

-------------------------------------------------------------------------------

SIG WAVE HGT   4  3  3    3  3  3  3    3  3  3  3    3

CLOUDS        FW FW FW   FW FW FW FW   FW FW FW FW   FW

POP 12HR         10       5     5       0     0
```

---

### 15. Marine Weather Message

| Field | Value |
|---|---|
| **Resource ID** | mww_marine_weather_message |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=MWW&site=hfo |
| **Collected** | 2026-09-30T02:18:15.685491-10:00 HST |

```text
502
WHHW70 PHFO 292350
MWWHFO

URGENT - MARINE WEATHER MESSAGE
National Weather Service Honolulu HI
150 PM HST Tue Sep 29 2026

PHZ110>113-010330-
/O.CON.PHFO.SC.Y.0038.000000T0000Z-261001T0400Z/
Kauai Northwest Waters-Kauai Windward Waters-Kauai Leeward Waters-
Kauai Channel-
150 PM HST Tue Sep 29 2026

...SMALL CRAFT ADVISORY REMAINS IN EFFECT UNTIL 6 PM HST
WEDNESDAY...

* WHAT...Southeast winds up to 30 kt and seas up to 13 feet.

* WHERE...Kauai Northwest Waters and Kauai Leeward Waters.

* WHEN...Until 6 PM HST Wednesday.

* IMPACTS...Conditions will be hazardous to small craft.

PRECAUTIONARY/PREPAREDNESS ACTIONS...

Inexperienced mariners, especially those operating smaller
vessels, should avoid navigating in these conditions.
```

---

### 16. Monthly Climate Summary — HNL

| Field | Value |
|---|---|
| **Resource ID** | clm_monthly_climate_summary_HNL |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLM&issuedby=HNL |
| **Collected** | 2026-09-30T02:27:45.101757-10:00 HST |

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
DAYS MAX = 72    31                                  31
DAYS MIN = .01        1                5.7    -4.7        0
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

### 17. Monthly Climate Summary — ITO

| Field | Value |
|---|---|
| **Resource ID** | clm_monthly_climate_summary_ITO |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLM&issuedby=ITO |
| **Collected** | 2026-09-30T02:28:29.953757-10:00 HST |

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
DAYS MAX = 72    20                                   6
DAYS MIN = .01       25               27.2    -2.2       19
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

### 18. Monthly Climate Summary — LIH

| Field | Value |
|---|---|
| **Resource ID** | clm_monthly_climate_summary_LIH |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLM&issuedby=LIH |
| **Collected** | 2026-09-30T02:27:59.948834-10:00 HST |

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
DAYS MAX = 72    31                                  31
DAYS MIN = .01       22               18.0     4.0       12
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

### 19. Monthly Climate Summary — OGG

| Field | Value |
|---|---|
| **Resource ID** | clm_monthly_climate_summary_OGG |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=CLM&issuedby=OGG |
| **Collected** | 2026-09-30T02:28:14.943758-10:00 HST |

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
DAYS MAX = 72    28                                  16
DAYS MIN = .01        5                7.4    -2.4        1
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

### 20. NHC Atlantic Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_atlc_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays=2 |
| **Collected** | 2026-09-30T01:49:59.292121-10:00 HST |

```text
094 ACCA62 KNHC 301142TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Adams*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 21. NHC Atlantic Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_atlc_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays=7 |
| **Collected** | 2026-09-30T01:50:58.448597-10:00 HST |

```text
094 ACCA62 KNHC 301142TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Adams*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 22. NHC Central Pacific Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_cpac_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=2 |
| **Collected** | 2026-09-30T01:53:58.198212-10:00 HST |

```text
094 ACCA62 KNHC 301142TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Adams*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 23. NHC Central Pacific Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_cpac_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=7 |
| **Collected** | 2026-09-30T01:54:58.824446-10:00 HST |

```text
094 ACCA62 KNHC 301142TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Adams*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 24. NHC Eastern Pacific Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_epac_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=epac&fdays=2 |
| **Collected** | 2026-09-30T01:55:58.664264-10:00 HST |

```text
094 ACCA62 KNHC 301142TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Adams*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 25. NHC Eastern Pacific Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_epac_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=epac&fdays=7 |
| **Collected** | 2026-09-30T01:56:58.214559-10:00 HST |

```text
094 ACCA62 KNHC 301142TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL800 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Adams*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 26. NHC source index

| Field | Value |
|---|---|
| **Resource ID** | nhc_homepage |
| **Official source** | https://www.nhc.noaa.gov/ |
| **Collected** | 2026-09-30T02:41:32.704393-10:00 HST |

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

Last update Wed, 30 Sep 2026 12:40:07 UTC

NHC issuing advisories for the Atlantic on

TS Hanna

NHC issuing advisories for the Eastern Pacific on

Hurricane Rachel

and

TD Nineteen-E

NHC issuing advisories for the Central Pacific on

TS Nolo

Marine warnings are in effect for the Eastern Pacific

Key messages regarding Hurricane Rachel

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

ALL

1

Disturbances:

ALL

1

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

500 AM PDT Wed Sep 30 2026

Tropical Weather Discussion

1005 UTC Wed Sep 30 2026

Hurricane Rachel

Satellite |
Buoys |
Grids |
Storm Archive

...RACHEL CONTINUES MOVING NORTHWESTWARD...
...COULD BECOME A MAJOR HURRICANE IN A DAY OR SO...

5:00 AM MST Wed Sep 30

Location: 17.8°N 107.6°W

Moving: NW at 10 mph

Min pressure: 979 mb

Max sustained: 85 mph

Public

Advisory

#13A

500 AM MST

Forecast

Advisory

#13

0900 UTC

Forecast

Discussion

#13

200 AM MST

Wind Speed

Probabilities

#13

0900 UTC

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

...TROPICAL DEPRESSION NINETEEN HOLDS STEADY SHIFTING EAST-SOUTHEASTWARD...

2:00 AM PDT Wed Sep 30

Location: 13.6°N 129.4°W

Moving: ESE at 9 mph

Min pressure: 1006 mb

Max sustained: 30 mph

Public

Advisory

#4

200 AM PDT

Forecast

Advisory

#4

0900 UTC

Forecast

Discussion

#4

200 AM PDT

Wind Speed

Probabilities

#4

0900 UTC

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

200 AM HST Wed Sep 30 2026

Tropical Storm Nolo

Satellite |
Buoys |
Grids |
Storm Archive

...NOLO CONTINUES TO BRING DANGEROUS CONDITIONS TO PORTIONS OF THE PAPAHANAUMOKUAKEA MARINE NATIONAL MONUMENT...
...NOLO REMAINS A STRONG TROPICAL STORM...

2:00 AM HST Wed Sep 30

Location: 22.2°N 164.8°W

Moving: W at 6 mph

Min pressure: 991 mb

Max sustained: 65 mph

Public

Advisory

#39A

200 AM HST

Forecast

Advisory

#39

0900 UTC

Forecast

Discussion

#39

1100 PM HST

Wind Speed

Probabilities

#39

0900 UTC

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

800 AM EDT Wed Sep 30 2026

Tropical Weather Discussion

1215 UTC Wed Sep 30 2026

Tropical Storm Hanna

Satellite |
Buoys |
Grids |
Storm Archive

...HANNA EXPECTED TO BECOME A REMNANT LOW BY TONIGHT...

9:00 AM GMT Wed Sep 30

Location: 33.5°N 43.9°W

Moving: ESE at 5 mph

Min pressure: 1006 mb

Max sustained: 40 mph

Public

Advisory

#8

900 AM GMT

Forecast

Advisory

#8

0900 UTC

Forecast

Discussion

#8

900 AM GMT

Wind Speed

Probabilities

#8

0900 UTC

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

### 27. NOAA source index

| Field | Value |
|---|---|
| **Resource ID** | noaa_homepage |
| **Official source** | https://www.noaa.gov/ |
| **Collected** | 2026-09-30T02:41:33.205193-10:00 HST |

```text
National Oceanic and Atmospheric Administration Home

Skip to main content

Main Menu

Home

Weather

Climate

Ocean & Coasts

Fisheries

Satellites

Research

Marine & Aviation

Charting

Sanctuaries

Education

News and features

Our data

Tools & resources

About our agency

An official website of the United States government

Here’s how you know

Here’s how you know

Official websites use .gov

A .gov website belongs to an official government organization in the United States.

Secure .gov websites use HTTPS

A lock (LockA locked padlock) or https:// means you’ve safely connected to the .gov website. Share sensitive information only on official, secure websites.

Find your local weather

Change location:

Enter City, State or ZIP code

News

Data

Tools

About

National Oceanic and Atmospheric Administration

U.S. Department of Commerce

Enter Search Terms

NOAA’s flood mapping tool now covers nearly 100% of U.S.

Experimental Flood Inundation Mapping provides valuable guidance for decision-makers and public

Scott Olson/Getty Images

Explore NOAA //

NOAA announces 2026 federal recreational red snapper season, exempted fishing permits in South Atlantic

Get the latest tropical storm forecasts from NOAA's National Hurricane Center

NOAA selects Tomorrow.io to help advance U.S. weather forecasting

More NOAA news and features

WEATHER HISTORY | BIG STORMS

Weather

Research

The Great Miami Hurricane of 1926: A century of science advancing warnings from hours to days

FISHERIES | FEEL-GOOD FEATURE STORY

Fisheries

Knocking for help: A pelican’s unlikely rescue

NOAA EDUCATION | ATTENTION UNDERGRADS!

The 2027 NOAA Hollings Scholarship application is now open!

NOAA Home

Science. Service. Stewardship.

News

Tools

About

Resources for Tribal & Indigenous Communities

Bipartisan Infrastructure Law (BIL)

Inflation Reduction Act (IRA)

Protecting Your Privacy

FOIA

Information Quality

Accessibility

Guidance

Budget & Performance

Disclaimer

EEO

No-Fear Act
```

---

### 28. Offshore Forecast (40-240nm)

| Field | Value |
|---|---|
| **Resource ID** | off_offshore_forecast |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=OFF&issuedby=HFO |
| **Collected** | 2026-09-29T23:57:54.620129-10:00 HST |

```text
457
FZHW60 PHFO 300949 CCA
OFFHFO

Offshore Waters Forecast for Hawaii...CORRECTED
National Weather Service Honolulu HI
1149 PM HST Tue Sep 29 2026

Hawaiian offshore waters beyond 40 nautical miles out to 240
nautical miles including the portion of the Papahanaumokuakea
Marine National Monument east of French Frigate Shoals

Seas given as significant wave height, which is the average height
of the highest 1/3 of the waves. Individual waves may be more than
twice the significant wave height.

PHZ105-301630-
1149 PM HST Tue Sep 29 2026

.Synopsis for the Hawaiian offshore waters...
Corrected Tropical Storm Nolo forecast position dates.

The center of Tropical Storm Nolo is tracking W along the W edge
of the offshore waters. Nolo will continue to move slowly W with
tropical storm force winds exiting the far W Hawaiian Offshore
Waters by Thursday.

AT 1100 PM HST TROPICAL STORM NOLO WAS CENTERED AT 22.4N
164.6W...MOVING WNW AT 5 KT

NOLO FORECAST POSITIONS
800 AM HST WEDNESDAY 22.6N 164.6W
800 PM HST WEDNESDAY 22.7N 165.0W
800 AM HST THURSDAY 22.6N 165.6W
800 PM HST THURSDAY 22.8N 166.5W
800 AM HST FRIDAY 23.1N 167.4W
800 PM HST FRIDAY 23.4N 168.8W
800 PM HST SATURDAY 24.1N 174.5W
800 PM HST SUNDAY 26.1N 178.7E

PHZ180-301630-
Hawaiian Offshore Waters-
1149 PM HST Tue Sep 29 2026

...TROPICAL STORM WARNING IN EFFECT...

.REST OF TONIGHT...Tropical storm conditions expected S of 25N, N
of 20N, and W of 162W. SE to S winds 15 to 25 kt. Seas 6 to 10
ft. Isolated thunderstorms far W waters.
.WEDNESDAY AND WEDNESDAY NIGHT...Tropical storm conditions
expected S of 25N, N of 20N, and W of 162W. SE to S winds 15 to 25
kt. Seas 6 to 10 ft. Isolated thunderstorms far W waters.
.THURSDAY AND THURSDAY NIGHT...W of 160W, SE to S winds 15 to 30
kt. Elsewhere, E to SE winds 10 to 20 kt. Seas 5 to 10 ft, highest
far W waters. Isolated thunderstorms far W waters.
.FRIDAY...E to SE winds 10 to 20 kt. Seas 5 to 8 ft.
.SATURDAY...E winds 10 to 20 kt. Seas 5 to 7 ft.
.SUNDAY...NE to E winds 15 to 25 kt. Seas 5 to 7 ft.
```

---

### 29. Statewide Surf Forecast (+discussion)

| Field | Value |
|---|---|
| **Resource ID** | srf_statewide_surf_forecast |
| **Official source** | https://www.weather.gov/hfo/SRF |
| **Collected** | 2026-09-30T02:26:11.810601-10:00 HST |

```text
454
FZHW52 PHFO 300100
SRFHFO

Surf Zone Forecast for Hawaii
National Weather Service Honolulu HI
300 PM HST Tue Sep 29 2026

.DISCUSSION...The moderate, medium period SW swell originating from
Nolo has eased slightly with the latest observations coming in below
the High Surf Advisory (HSA). The HSA has therefore been allowed to
expire. Surf along E shores has declined in response to emerging SE
flow. Surf will remain small until moderate trades return early next
week providing a modest boost. Multiple rounds of tiny swell
originating out of the northwest quadrant will reach north and select
west facing exposures next week as the storm track in the vicinity of
the Aleutian Islands becomes increasingly active.

HIZ003-029>031-010200-
Kauai-
300 PM HST Tue Sep 29 2026

__________________________________________________________________
                      Tonight                    Wednesday

Shores                  Surf                       Surf
                     PM     AM                  AM     PM
__________________________________________________________________

North Facing         2-4    1-3                 1-3    1-3
West Facing          5-7    5-7                 5-7    5-7
South Facing         4-6    4-6                 3-5    3-5
East Facing          4-6    3-5                 3-5    3-5

.TONIGHT...
Weather.....................Mostly cloudy. Frequent showers.
Low Temperature.............In the mid 70s.
Winds.......................Southeast winds 15 to 20 mph.
Tides...
   Hanalei Bay..............High 1.1 feet 03:35 PM HST.
                            Low 0.0 feet 09:28 PM HST.
                            High 2.3 feet 05:34 AM HST.
   Nawiliwili...............High 1.1 feet 04:36 PM HST.
                            Low 0.0 feet 10:50 PM HST.

.WEDNESDAY...
Weather.....................Mostly cloudy. Numerous showers.
High Temperature............In the mid 80s.
Winds.......................South winds around 15 mph.
Tides...
   Hanalei Bay..............Low 0.8 feet 12:26 PM HST.
                            High 1.0 feet 03:44 PM HST.
   Nawiliwili...............High 2.1 feet 06:35 AM HST.
                            Low 0.8 feet 01:48 PM HST.
                            High 0.9 feet 04:45 PM HST.
Sunrise.....................6:28 AM HST.
Sunset......................6:27 PM HST.

HIZ006-007-009-032>035-010200-
Oahu-
300 PM HST Tue Sep 29 2026

__________________________________________________________________
                      Tonight                    Wednesday

Shores                  Surf                       Surf
                     PM     AM                  AM     PM
__________________________________________________________________

North Facing         2-4    1-3                 1-3    1-3
West Facing          4-6    4-6                 4-6    4-6
South Facing         4-6    4-6                 4-6    4-6
East Facing          4-6    3-5                 3-5    3-5

.TONIGHT...
Weather.....................Mostly cloudy. Scattered showers.
Low Temperature.............In the upper 70s.
Winds.......................Southeast winds around 15 mph.
Tides...
   Honolulu.................High 1.0 feet 05:19 PM HST.
                            Low 0.1 feet 11:14 PM HST.
   Waianae..................Low 0.6 feet 01:05 PM HST.
                            High 1.0 feet 05:39 PM HST.
                            Low 0.1 feet 11:32 PM HST.
   Haleiwa..................High 0.8 feet 04:17 PM HST.
                            Low 0.0 feet 09:09 PM HST.
                            High 1.7 feet 05:48 AM HST.
   Mokuoloe.................High 1.6 feet 02:52 PM HST.
                            Low -0.1 feet 09:51 PM HST.
                            High 2.3 feet 05:30 AM HST.

.WEDNESDAY...
UV Index....................Very High.
Weather.....................Partly sunny. Numerous showers.
High Temperature............In the mid 80s.
Winds.......................Southeast winds around 20 mph.
Tides...
   Honolulu.................High 2.2 feet 06:50 AM HST.
                            Low 0.6 feet 02:13 PM HST.
                            High 0.8 feet 05:57 PM HST.
   Waianae..................High 2.0 feet 07:10 AM HST.
                            Low 0.6 feet 02:31 PM HST.
   Haleiwa..................Low 0.5 feet 12:08 PM HST.
                            High 0.7 feet 04:55 PM HST.
   Mokuoloe.................Low 1.3 feet 11:39 AM HST.
                            High 1.5 feet 02:50 PM HST.
Sunrise.....................6:22 AM HST.
Sunset......................6:22 PM HST.

HIZ017-018-045>050-010200-
Maui-
300 PM HST Tue Sep 29 2026

__________________________________________________________________
                      Tonight                    Wednesday

Shores                  Surf                       Surf
                     PM     AM                  AM     PM
__________________________________________________________________

North Facing         2-4    1-3                 1-3    1-3
West Facing          3-5    3-5                 3-5    3-5
South Facing         4-6    4-6                 4-6    4-6
East Facing          4-6    3-5                 3-5    3-5

.TONIGHT...
Weather.....................Sunny until 6 PM, then partly cloudy.
Low Temperature.............In the mid 70s.
Winds.......................East winds 10 to 15 mph.
Tides...
   Kahului..................High 1.8 feet 03:02 PM HST.
                            Low -0.1 feet 09:43 PM HST.
                            High 2.4 feet 05:02 AM HST.

.WEDNESDAY...
Weather.....................Mostly sunny. Scattered showers.
High Temperature............In the mid 80s.
Winds.......................Southeast winds 10 to 15 mph.
Tides...
   Kahului..................Low 1.3 feet 11:08 AM HST.
                            High 1.6 feet 03:10 PM HST.
Sunrise.....................6:16 AM HST.
Sunset......................6:16 PM HST.

HIZ052>054-010200-
Big Island Windward and Southeast-
300 PM HST Tue Sep 29 2026

__________________________________________________________________
                      Tonight                    Wednesday

Shores                  Surf                       Surf
                     PM     AM                  AM     PM
__________________________________________________________________

North Facing         1-3    1-3                 1-3    1-3
East Facing          4-6    4-6                 4-6    4-6
South Facing         4-6    4-6                 4-6    4-6

.TONIGHT...
Weather.....................Mostly sunny until 6 PM, then mostly
                            cloudy. Isolated showers.
Low Temperature.............In the lower 70s.
Winds.......................Southeast winds around 10 mph.
Tides...
   Hilo Bay.................High 1.8 feet 04:09 PM HST.
                            Low -0.1 feet 10:35 PM HST.
                            High 2.7 feet 05:47 AM HST.

.WEDNESDAY...
Weather.....................Mostly sunny. Scattered showers.
High Temperature............In the lower 80s.
Winds.......................Southeast winds 10 to 15 mph.
Tides...
   Hilo Bay.................Low 1.1 feet 12:16 PM HST.
                            High 1.6 feet 04:33 PM HST.
Sunrise.....................6:11 AM HST.
Sunset......................6:10 PM HST.

HIZ023-026-051-010200-
Big Island Leeward-
300 PM HST Tue Sep 29 2026

__________________________________________________________________
                      Tonight                    Wednesday

Shores                  Surf                       Surf
                     PM     AM                  AM     PM
__________________________________________________________________

West Facing          4-6    4-6                 4-6    4-6
South Facing         4-6    4-6                 4-6    4-6

.TONIGHT...
Weather.....................Partly cloudy. Isolated showers.
Low Temperature.............In the lower 70s.
Winds.......................Northwest winds around 5 mph, becoming
                            northeast after midnight.
Tides...
   Kona.....................High 1.4 feet 04:47 PM HST.
                            Low -0.1 feet 11:12 PM HST.
   Kawaihae.................High 1.3 feet 05:28 PM HST.
                            Low 0.0 feet 11:23 PM HST.

.WEDNESDAY...
Weather.....................Mostly sunny. Isolated showers.
High Temperature............In the upper 80s.
Winds.......................West winds 5 to 10 mph.
Tides...
   Kona.....................High 2.1 feet 06:25 AM HST.
                            Low 0.7 feet 12:53 PM HST.
                            High 1.3 feet 05:11 PM HST.
   Kawaihae.................High 2.4 feet 06:39 AM HST.
                            Low 0.6 feet 01:45 PM HST.
Sunrise.....................6:15 AM HST.
Sunset......................6:14 PM HST.

__________________________________________________________________

Product Legend:

Surf:        Height of the surf from trough to crest (face value)
             in feet.

Tides:       Heights displayed are relative to the Mean Lower Low
             Water (MLLW) datum in feet.

Surf heights can vary significantly from beach to beach along a
coastline. Surf larger than the upper end of the range provided in
the forecast will occur periodically, sometimes up to a few hours
apart. Expect to encounter rip currents in or near the surf zone,
with rip current strength increasing with surf size. Swimmers are
urged to exercise caution at all times and enter the water near a
lifeguard.

For the latest beach hazard and safety information at individual
beaches in Hawaii refer to:

https://hawaiibeachsafety.com

__________________________________________________________________
```

---

### 30. Statewide Surf Observations

| Field | Value |
|---|---|
| **Resource ID** | surfreports_statewide_observations |
| **Official source** | https://www.weather.gov/hfo/surfreports |
| **Collected** | 2026-09-30T02:26:17.978041-10:00 HST |

```text
                        
880
SXHW80 PHFO 300115
OMRHFO

SURF OBSERVATIONS
NATIONAL WEATHER SERVICE HONOLULU HI
315 PM HST TUE SEP 29 2026

FULL FACE SURF OBSERVATIONS ARE TAKEN BY COUNTY LIFE GUARDS AND
COOPERATIVE OBSERVERS AND RELAYED TO THE NATIONAL WEATHER SERVICE
FOR DISSEMINATION. THESE OBSERVATIONS ARE NOT QUALITY CONTROLLED.

HIZ003-004-029>031-300100-
KAUAI-

LOCATION        TIME   SURF HEIGHT DIR   PER                  REMARKS
KEE
HAENA        1000 AM           4-5  NW    11
HANALEI      1000 AM           2-3   N     9
ANAHOLA
KEALIA
LYDGATE
POIPU        1030 AM          6-8   SW    10
SALT POND    1030 AM           6-8  SW    10
KEKAHA       1030 AM           6-8  SW    10
$$

HIZ006-007-009>011-032>036-300100-
OAHU-

LOCATION        TIME   SURF HEIGHT DIR PER         WIND      REMARKS
DIAMOND HEAD
SUNSET
WAIKIKI      1118 AM           3-4              E 10-15       CANOES
SANDY BEACH  1118 AM           3-5              NE 5-15  SHORE BREAK
MAKAPUU      1118 AM           3-5             NE 10-15
EHUKAI       1118 AM           2-3              E 10-15
MAKAHA       1118 AM           2-3               E 5-10
$$

HIZ015>018-022-045>050-300100-
MAUI-MOLOKAI-LANAI-KAHOOLAWE-

LOCATION        TIME   SURF HEIGHT   DIR         WIND      REMARKS
KANAHA       1127 AM           1-3           VRB 5-10  PARTLY CLDY
BALDWIN SHOR 1128 AM           2-3           VRB 5-10        SUNNY
BALDWIN OUTE 1128 AM           4-6           VRB 5-10        SUNNY
HOOKIPA      1129 AM           6-8            E 20-25  PARTLY CLDY
KAMAOLE I    1133 AM           2-4            VRB 0-5  PARTLY CLDY
KAMAOLE III  1131 AM           2-3           VRB 5-10        SUNNY
HANAKAOO
FLEMING
$$

HIZ023-026>028-051>054-300100-
BIG ISLAND OF HAWAII-

LOCATION        TIME   SURF HEIGHT   DIR         WIND      REMARKS
RICHARDSONS  1120 AM           2-3           VRB 5-10        SUNNY
HONOLII      1121 AM           3-5             S 5-15 MOSTLY SUNNY
PUNALU`U
ISAAC HALE   1122 AM           3-5            E 10-15 MOSTLY SUNNY
HAPUNA
KAHALUU      1124 AM           5-6    SW      SW 5-10  PARTLY CLDY
MAGIC SANDS  1125 AM           3-4    SW      SW 5-10        SUNNY
KUA BAY      1126 AM           2-4           VRB 5-10 MOSTLY SUNNY
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

### 31. Tsunami Bulletin product type reference

| Field | Value |
|---|---|
| **Resource ID** | hfo_tib_reference |
| **Official source** | https://forecast.weather.gov/product_types.php |
| **Collected** | 2026-09-30T02:34:34.700279-10:00 HST |

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
