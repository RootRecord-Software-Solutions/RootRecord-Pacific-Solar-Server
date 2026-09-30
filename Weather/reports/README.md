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
| 🟢 Active | Hawaiʻi statewide | 2026-09-30T01:18:24-10:00 HST | 20 |

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

### 2. Area Forecast Discussion

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

### 3. Daily Climate Summary — HNL

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

### 4. Daily Climate Summary — ITO

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

### 5. Daily Climate Summary — LIH

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

### 6. Daily Climate Summary — OGG

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

### 7. Hawaii Rainfall Summary direct product

| Field | Value |
|---|---|
| **Resource ID** | hfo_rra_direct |
| **Official source** | https://forecast.weather.gov/product.php?issuedby=HFO&product=RRA&site=hfo |
| **Collected** | 2026-09-30T01:11:55.106586-10:00 HST |

```text
330
SRHW80 PHFO 301046
RRAHFO

Hawaii Rainfall Summary
National Weather Service Honolulu HI
1245 AM HST Wed Sep 30 2026

:
.B HFO  0930 H  DH00 /DRH-03/PPT/DRH-06/PPQ/DRH-12/PPK/DRH-24/PPD
:
:Automated rain gage reports from around the State of Hawaii.
:These are provisional reports that have not been quality
:controlled.
:
:T=Trace Rainfall, M=Missing Data
:
:Precipitation totals ending  12 AM HST
:
:Island of Kauai                                   Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward/Mauka Sites
MKAH1 : Makaha Ridge (RAWS)         :    0.22  /  0.31  /  0.31  /  0.31
PLRH1 : Puu Lua (RAWS)              :    0.48  /  0.76  /  0.80  /  0.80
WKRH1 : Waiakoali (USGS)            :    0.55  /  0.92  /  0.94  /  0.94
KLOH1 : Kilohana (USGS)             :    0.39  /  0.65  /  0.67  /  0.67
MCRH1 : Mohihi Crossing (USGS)      :    0.58  /  0.99  /  1.03  /  1.03
WLGH1 : Waialae (USGS)              :    0.56  /  1.07  /  1.11  /  1.11
LLMH1 : Lower Limahuli (UHM)        :    0.12  /  0.27  /  0.28  /  0.28
WNHH1 : Wainiha (12010)             :    0.14  /  0.28  /  0.28  /  0.28
WIPH1 : Waipa (UHM)                 :    0.34  /  0.56  /  0.60  /  0.60
HNIH1 : Hanalei (12009)             :    0.31  /  0.52  /  0.57  /  0.57
WLLH1 : Mount Waialeale (USGS)      :      M   /    M   /    M   /    M
PRIH1 : Princeville Airport (12011) :    0.21  /  0.40  /  0.60  /  0.60
CMGH1 : Common Ground (UHM)         :    0.23  /  0.70  /  0.71  /  0.71
HLIH1 : Hanalei (RAWS)              :    0.41  /  0.50  /  0.50  /  0.50
MLDH1 : Moloaa Dairy (RAWS)         :    0.00  /  0.00  /  0.00  /  0.00
ANHH1 : Anahola (12001)             :      M   /    M   /    M   /    M
KPIH1 : Kapahi (12003)              :    0.12  /  0.33  /  0.40  /  0.40
WLDH1 : N Wailua Ditch (USGS)       :    0.96  /  1.55  /  1.58  /  1.62
WUHH1 : Wailua (12005)              :    0.11  /  0.24  /  0.36  /  0.36
WIRH1 : Waiahi Rain Gage (USGS)     :    0.35  /  0.76  /  0.79  /  0.79
LIHH1 : Lihue Var. Stn. (12006)     :    0.09  /  0.13  /  0.19  /  0.19
HNMH1 : Hanamaulu (UHM)             :    0.41  /  0.94  /  1.00  /  1.00
HLI   : Lihue Airport (ASOS)        :      T   /  0.11  /  0.14  /  0.14
:       Leeward Sites
OMAH1 : Omao (12004)                :    0.15  /  0.18  /  0.25  /  0.25
LNTH1 : Lawai NTBG (UHM)            :    0.03  /  0.07  /  0.07  /  0.07
KHEH1 : Kalaheo (12008)             :    0.03  /  0.09  /  0.11  /  0.11
PAKH1 : Port Allen (HSOIS)          :    0.17  /  0.40  /  0.40  /  0.40
HNPH1 : Hanapepe (12002)            :    0.06  /  0.20  /  0.45  /  0.45
POPH1 : Puu Opae (RAWS)             :    0.55  /  0.84  /  0.88  /  0.88
WHGH1 : Waimea Heights (RAWS)       :    0.38  /  0.79  /  0.92  /  0.92
WMTH1 : Waimea Tank (12007)         :    0.41  /  0.58  /  0.92  /  0.92
MNRH1 : Mana (RAWS)                 :    0.43  /  0.62  /  0.63  /  0.63
:
:Island of Oahu                                    Inches
:ID     Location                         3-Hr    6-Hr   12-Hr   24-Hr
:       Windward/Mauka Sites
KAHH1 : Kahuku (13027)              :    0.17  /  0.17  /  0.17  /  0.17
KTAH1 : Kahuku Training Area (RAWS) :    0.00  /  0.01  /  0.01  /  0.01
KFWH1 : Kii (RAWS)                  :    0.00  /  0.00  /  0.00  /  0.00
PUNH1 : Punaluu Pump (13013)        :    0.09  /  0.10  /  0.10  /  0.10
PNSH1 : Punaluu Stream (USGS)       :    0.06  /  0.08  /  0.12  /  0.12
KNRH1 : Kahana (USGS)               :    0.00  /  0.00  /  0.00  /  0.00
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
PMHH1 : Poamoho RG 1 (USGS)         :    0.28  /  0.47  /  0.60  /  0.60
DLGH1 : Dillingham (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
AALH1 : Kaala (UHM)                 :    0.01  /  0.01  /  0.01  /  0.02
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
SDQH1 : Saddle Quarry (USGS)        :    0.03  /  0.13  /  0.23  /  0.23
PIOH1 : Piihonua (UHM)              :    0.00  /  0.05  /  0.14  /  0.14
PIIH1 : Piihonua (15016)            :    0.00  /  0.00  /  0.00  /  0.00
IPIH1 : IPIF (UHM)                  :    0.00  /  0.00  /  0.00  /  0.00
WKAH1 : Waiakea Uka (15017)         :    0.00  /  0.00  /  0.00  /  0.00
WEXH1 : Waiakea Exp Stn (NOAA/CRN)  :    0.00  /  0.00  /  0.00  /  0.00
HTO   : Hilo Airport (ASOS)         :    0.01  /  0.01  /  0.01  /  0.01
PHAH1 : Pahoa (15015)               :    0.01  /  0.01  /  0.01  /  0.01
PAOH1 : Pahoa (UHM)                 :    0.01  /  0.01  /  0.01  /  0.01
MTVH1 : Mountain View (15014)       :    0.00  /  0.00  /  0.00  /  0.00
GLNH1 : Glenwood (15013)            :    0.00  /  0.00  /  0.00  /  0.00
:       Leeward Sites
MOBH1 : Mauna Loa Ob Stn (NOAA/CRN) :    0.00  /  0.00  /  0.00  /  0.00
NHKH1 : Nahuku (UHM)                :    0.00  /  0.00  /  0.00  /  0.00
KKUH1 : Keaumo (RAWS)               :    0.02  /  0.04  /  0.16  /  0.16
KMOH1 : Kealakomo (RAWS)            :    0.00  /  0.00  /  0.00  /  0.00
PLIH1 : Pali 2 (RAWS)               :    0.01  /  0.01  /  0.01  /  0.01
KPRH1 : Kapapala (RAWS)             :    0.00  /  0.01  /  0.01  /  0.01
KAYH1 : Kapapala Ranch (15003)      :    0.00  /  0.00  /  0.07  /  0.07
PPLH1 : Pahala (15004)              :    0.01  /  0.08  /  0.08  /  0.08
KIOH1 : Kaiholena (UHM)             :      M   /    M   /    M   /    M
NENH1 : Nene Cabin (RAWS)           :    0.00  /  0.00  /  0.00  /  0.00
SOPH1 : South Point (HSOIS)         :    0.00  /  0.00  /  0.00  /  0.00
LKHH1 : Lower Kahuku (RAWS)         :    0.01  /  0.03  /  0.03  /  0.03
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

### 8. HFO statewide surf observations direct page

| Field | Value |
|---|---|
| **Resource ID** | hfo_surf_reports_direct |
| **Official source** | https://www.weather.gov/hfo/surfreports |
| **Collected** | 2026-09-30T01:11:57.552108-10:00 HST |

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

### 9. High Seas Forecast N. Pacific

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

### 10. Hourly Wind/Precip Observations

| Field | Value |
|---|---|
| **Resource ID** | oso_hourly_obs |
| **Official source** | https://forecast.weather.gov/product.php?site=HFO&product=OSO&issuedby=HFO |
| **Collected** | 2026-09-30T01:13:40.122542-10:00 HST |

```text
454
SXHW50 PHFO 301043
OSOHFO

Hawaii Wind Data
National Weather Service Honolulu HI
1243 AM HST Wed Sep 30 2026

                            W I N D        D A T A
                            ----------------------
                                                                   IN KNOTS
 ID                Location              Date     Time     DIR    SPD   GUST
--------   -------------------------    -------  -(HST)-  ----   ----   ----
0000LLMH1  Lower Limahuli     Kauai     30Sep26   00:15    200      3      6
0000CMGH1  Common Ground      Kauai     30Sep26   00:15    140      5     10
0000HLIH1  Hanalei            Kauai     29Sep26   23:41    110      3     19
0000MLDH1  Moloaa Dairy       Kauai     29Sep26   23:45    130      9     21
0000HNMH1  Hanamaulu          Kauai     30Sep26   00:15    150      6     10
0000PHLI   Lihue              Kauai     30Sep26   00:00    140     20     24
0000NWWH1  Nawiliwili NOS     Kauai     30Sep26   00:30    120     17     23
0000POIH1  Poipu              Kauai                MSG    MSG    MSG    MSG
0000LNTH1  Lawai NTBG         Kauai     30Sep26   00:15    110      3     10
0000PAKH1  Port Allen         Kauai     30Sep26   00:00    140     20     26
0000MKAH1  Makaha Ridge       Kauai     30Sep26   00:11    160      6     25
0000MNRH1  Mana               Kauai     30Sep26   00:34    140      6     16
0000PHBK   Barking Sands      Kauai     30Sep26   00:35    150     18     29
0000PLRH1  Puu Lua            Kauai     30Sep26   00:35     70     15     31
0000POPH1  Puu Opae           Kauai     30Sep26   00:34    130     12     24
0000WHGH1  Waimea Heights     Kauai     30Sep26   00:35     50     10     18

0000KRGH1  Kalahee Ridge      Oahu      30Sep26   00:10     90      2      5
0000KAHH1  Kahuku             Oahu                 MSG    MSG    MSG    MSG
0000KTAH1  Kahuku Trng        Oahu      29Sep26   23:59    100      0      3
0000KFWH1  Kii                Oahu      29Sep26   23:45    120     12     21
0000OFRH1  Oahu Forest NWR    Oahu      30Sep26   00:36     80      3      7
0000KWMH1  Kaaawa Makai       Oahu      30Sep26   00:15    110      6     12
0000PHNG   Kaneohe MCBH       Oahu      30Sep26   00:00    120      8     15
0000MOKH1  Mokuoloe Is NOS    Oahu      30Sep26   00:30    140      6     11
0000BELH1  Bellows AFS        Oahu      30Sep26   00:15    110     14    MSG
0000KUXH1  Kaluanui           Oahu      30Sep26   00:15    170      2      7
0000LYOH1  Lyon               Oahu      29Sep26   23:55    320      0      2
0000NRSH1  Nuuanu Res No 1    Oahu      30Sep26   00:15    350      2      4
0000PHNL   Honolulu AP        Oahu      30Sep26   00:00    110      9    MSG
0000OOUH1  Honolulu Hbr NOS   Oahu      30Sep26   00:24     90      3      6
0000HOFH1  Honouliuli PHB     Oahu      30Sep26   00:41    130      6     11
0000SCBH1  Schofield Brks     Oahu      29Sep26   23:57    170      3     10
0000SCEH1  Schofield East     Oahu      29Sep26   23:58    120      3      7
0000HWLH1  HECO Wilikina      Oahu      30Sep26   00:30    120      5      8
0000PHJR   Kalaeloa           Oahu      30Sep26   00:00    120      7     17
0000HFHH1  HECO Farrington    Oahu      30Sep26   00:30    100      7     13
0000HPLH1  HECO Palehua       Oahu      30Sep26   00:30     90      5     13
0000HPDH1  HECO Palehua 2     Oahu      30Sep26   00:30    110      4      7
0000HPHH1  HECO Palehua 3     Oahu      30Sep26   00:30    100      5     12
0000HPRH1  HECO Paakea        Oahu      30Sep26   00:30    190      5     20
0000HLRH1  HECO Lualualei     Oahu      30Sep26   00:30    120      7     15
0000HWVH1  HECO Waianae Vly   Oahu                 MSG    MSG    MSG    MSG
0000PLHH1  Palehua            Oahu      30Sep26   00:36    100      0      0
0000WNVH1  Waianae Valley     Oahu      30Sep26   00:37    150      4     15
0000HHSH1  HECO Ala Hema St   Oahu      30Sep26   00:30    100      6     10
0000WBHH1  Waianae Harbor     Oahu                 MSG    MSG    MSG    MSG
0000HKRH1  HECO Kili Dr       Oahu      30Sep26   00:30     80      6     14
0000HMVH1  HECO Makaha Vly    Oahu      30Sep26   00:30    250      6     18
0000MKRH1  Makua Range        Oahu      29Sep26   23:58    140      5     17
0000KKRH1  Kuaokala           Oahu      30Sep26   00:36     30      5     14
0000AALH1  Kaala              Oahu      30Sep26   00:15    170      3     11
0000HFRH1  HECO Farrington2   Oahu      30Sep26   00:30     90      5     11
0000HFYH1  HECO Farrington3   Oahu      30Sep26   00:30    100      4      5
0000DLGH1  Dillingham         Oahu      29Sep26   23:49    100      4     10

0000MKPH1  Makapulapai        Molokai   30Sep26   00:15    100     10     16
0000PAFH1  Puu Alii           Molokai   30Sep26   00:22    150      1      4
0000HOMH1  Honolimaloo        Molokai   30Sep26   00:15    120      6     12
0000KOPH1  Keopukaloa         Molokai   30Sep26   00:15    130      9     13
0000MLKH1  Molokai 1          Molokai              MSG    MSG    MSG    MSG
0000MMPH1  MECO Makaena       Molokai   30Sep26   00:30     20      2      3
0000MKYH1  MECO Kalae Hwy     Molokai   30Sep26   00:30    340      1      2
0000PHMK   Molokai AP         Molokai   30Sep26   00:00      0      0    MSG
0000ANPH1  Anapuka            Molokai   30Sep26   00:15      0      0      0

0000LNIH1  Lanai 1            Lanai     30Sep26   00:37     30      0      0

0000KAOH1  Kaneloa            Kahoolawe            MSG    MSG    MSG    MSG

0000PHOG   Kahului AP         Maui      30Sep26   00:00      0      0    MSG
0000KLIH1  Kahului Hbr NOS    Maui      30Sep26   00:24    360      9     10
0000MHRH1  MECO Hansen Rd     Maui      30Sep26   00:30    290      1      6
0000MHKH1  MECO Haleakala Hwy Maui      30Sep26   00:30    150      3      4
0000MMKH1  MECO Makawao       Maui      30Sep26   00:30    180      6      6
0000MKTH1  MECO Kula 2        Maui      29Sep26   22:50    170      1      2
0000PILH1  Piiholo            Maui      30Sep26   00:15    160      4      5
0000EBYH1  EMI Baseyard       Maui      30Sep26   00:10    140      1      5
0000HNAH1  Hana               Maui                 MSG    MSG    MSG    MSG
0000NKUH1  Na Kula            Maui      30Sep26   00:35     70      9     15
0000AWAH1  Auwahi             Maui                 MSG    MSG    MSG    MSG
0000KLFH1  Kula 1             Maui      29Sep26   23:48    100      3      5
0000KKNH1  Kahikinui 1        Maui      30Sep26   00:34     40      3      6
0000KMEH1  Kamehamenui 1      Maui      29Sep26   23:48    140      5      8
0000SUMH1  Summit             Maui      30Sep26   00:15    180      4      7
0000NNEH1  Nene Nest          Maui      30Sep26   00:15    160      2      2
0000PHQH1  Park HQ            Maui      30Sep26   00:00    150      3      4
0000WKTH1  Waikamoi Treeline  Maui      30Sep26   00:15    200      4      5
0000MCTH1  MECO Crater Rd     Maui      30Sep26   00:30    110      4      5
0000KLGH1  Kula Ag            Maui      30Sep26   00:15    110      1      2
0000MWAH1  MECO Waipoli Rd    Maui      30Sep26   00:30    100      3      3
0000KKEH1  Keokea             Maui      30Sep26   00:15    120      1      2
0000MKUH1  MECO Kula          Maui      30Sep26   00:30     60      5      7
0000PHUH1  Pulehu             Maui      30Sep26   00:15    130      2      4
0000MNDH1  MECO Naalaea Rd    Maui      30Sep26   00:30    100      3      5
0000MURH1  MECO Ulupalakua    Maui      30Sep26   00:30     80      2      4
0000LPOH1  Lipoa              Maui      30Sep26   00:15    340      1      2
0000MVHH1  MECO Veterans Hwy  Maui      30Sep26   00:30     50      3      4
0000KPDH1  Kealia Pond        Maui      30Sep26   00:20     80      3      4
0000MMAH1  MECO Maalaea       Maui      30Sep26   00:30     10      2      3
00000P36   Maalaea Bay        Maui      30Sep26   00:15      0      0      0
0000HULH1  Hanaula            Maui      30Sep26   00:10    280      0      2
0000OLUH1  Olowalu            Maui      30Sep26   00:15     60      2      6
0000MMMH1  MECO Mamane Pl     Maui      30Sep26   00:30    290      4      7
0000MHOH1  MECO Honoapiilani  Maui      30Sep26   00:30    350      5      7
0000MHHH1  MECO Honoapiilani2 Maui      30Sep26   00:30    300      5      6
0000MKEH1  MECO Kealaloloa Rg Maui      30Sep26   00:30    290      1      4
0000MUGH1  MECO Ukumehame Gul Maui      30Sep26   00:30     10      5      7
0000MOOH1  MECO Olowalu       Maui      30Sep26   00:30     90      3      5
0000OLUH1  Olowalu            Maui      30Sep26   00:15     60      2      6
0000MLPH1  MECO Launiupoko    Maui      30Sep26   00:30     30      4      5
0000MLTH1  MECO Launiupoko 2  Maui      30Sep26   00:30     20      4      7
0000MLRH1  MECO Lahainaluna   Maui      30Sep26   00:30     40      6      8
0000LWTH1  Lahaina WTP        Maui      30Sep26   00:15     60      2      6
0000MKNH1  MECO Kaanapali     Maui      30Sep26   00:30     70      8      9
0000PHJH   Kapalua-W Maui     Maui      30Sep26   00:00      0      0    MSG
0000HOOH1  Honolua            Maui      30Sep26   00:15    150      7     11

0000UPLH1  Upolu Airport      Hawaii    30Sep26   00:15    160      3      4
0000KMMH1  Kaluamakani        Hawaii    30Sep26   00:15    130      3      5
0000PMLH1  Puu Mali           Hawaii    30Sep26   00:00    210      3      5
0000KNKH1  Kanakaleonui       Hawaii    30Sep26   00:15    230      2      3
0000WPNH1  Waipunalei         Hawaii               MSG    MSG    MSG    MSG
0000LAUH1  Laupahoehoe        Hawaii    30Sep26   00:15    200      4      5
0000SPNH1  Spencer            Hawaii    30Sep26   00:15    170      4     10
0000HKUH1  Hakalau            Hawaii    29Sep26   23:45    250      2      7
0000KLXH1  Kulaimano          Hawaii    30Sep26   00:15    180      4      7
0000PIOH1  Piihonua           Hawaii    30Sep26   00:15    260      1      2
0000PHTO   Hilo AP            Hawaii    30Sep26   00:00    200      5    MSG
0000ILOH1  Hilo Hbr NOS       Hawaii    30Sep26   00:24    200      3      4
0000IPIH1  IPIF               Hawaii    30Sep26   00:15    190      1      2
0000WEXH1  Waiakea Exp Stn    Hawaii    30Sep26   00:00    MSG      1      4
0000KEUH1  Keaau              Hawaii    30Sep26   00:15      0      0      0
0000PAOH1  Pahoa              Hawaii    30Sep26   00:15      0      0      0
0000NHKH1  Nahuku             Hawaii    30Sep26   00:15      0      0      0
0000KKUH1  Keaumo             Hawaii    30Sep26   00:34    240      3      6
0000MOBH1  Mauna Loa Obs      Hawaii    30Sep26   00:00    MSG      6      8
0000PLIH1  Pali 2             Hawaii    30Sep26   00:01     30      3      7
0000KMOH1  Kealakomo          Hawaii    29Sep26   23:44    110      7     10
0000KPRH1  Kapapala           Hawaii    29Sep26   23:48    340      3      5
0000NENH1  Nene Cabin         Hawaii    30Sep26   00:23     50      3      6
0000KIOH1  Kaiholena          Hawaii    30Sep26   00:15    300      4      7
0000LKHH1  Lower Kahuku       Hawaii    30Sep26   00:23    350      2     10
0000SOPH1  South Point        Hawaii    30Sep26   00:00     40     12     16
0000KOMH1  Kona Hema          Hawaii    30Sep26   00:15     50      4      5
0000KRCH1  Kahuku Ranch       Hawaii    30Sep26   00:29    180      1      5
0000PHRH1  Puho CS            Hawaii    30Sep26   00:22     80      3      5
0000HLNH1  HELCO Lolo Ln      Hawaii    30Sep26   00:30     70      4      4
0000HHUH1  HELCO Hualalai Rd  Hawaii    30Sep26   00:30     50      4      6
0000KOUH1  Keahuolu           Hawaii    30Sep26   00:15     50      2      4
0000PHKO   Kona Intl AP       Hawaii    30Sep26   00:00    100      4    MSG
0000KHOH1  Kaloko-Honokohau   Hawaii    30Sep26   00:15     50      4      7
0000PLMH1  Palamanui          Hawaii    30Sep26   00:15     80      2      4
0000PWAH1  Puu Waawaa (UHM)   Hawaii    30Sep26   00:15    120      2      3
0000KIUH1  Kaiaulu Puu Waawaa Hawaii    30Sep26   00:15     50      1      1
0000KPLH1  Kaupulehu          Hawaii    30Sep26   00:36    130      3      5
0000PWWH1  Puu Waawaa         Hawaii    30Sep26   00:37    150      3      4
0000HMHH1  HELCO Mamalahoa 2  Hawaii    30Sep26   00:30    170      7      8
0000MMLH1  Mamalahoa          Hawaii    30Sep26   00:15     90      0      1
0000HMWH1  HELCO Mamalahoa 3  Hawaii    30Sep26   00:30    160      3      4
0000PULH1  Puuanahulu         Hawaii    30Sep26   00:37    180      1      2
0000AHMH1  Ahumoa             Hawaii    30Sep26   00:35     80      3      5
0000AIPH1  Aipaloa            Hawaii    30Sep26   00:15    140      6      8
0000HSRH1  HELCO Saddle Rd    Hawaii    30Sep26   00:30    120      3      5
0000HMYH1  HELCO Mamalahoa    Hawaii    30Sep26   00:30    110      2      3
0000HHCH1  HELCO Hokuloa UCC  Hawaii    30Sep26   00:30    140      4      5
0000HWRH1  HELCO Waikoloa Rd  Hawaii    30Sep26   00:30     90      8     10
0000HWXH1  HELCO Waikoloa 2   Hawaii    30Sep26   00:30    130      8      9
0000WKVH1  Waikoloa           Hawaii    30Sep26   00:35    110      3      6
0000HLOH1  HELCO Lalamilo     Hawaii    30Sep26   00:30     40      9     10
0000LLAH1  Lalamilo           Hawaii    30Sep26   00:15     70      2      2
0000HKWH1  HELCO Kawaihae Rd  Hawaii    30Sep26   00:30     50      2      3
0000PKAH1  PTA Kipuka Alala   Hawaii    29Sep26   23:55    130      3      3
0000PKWH1  PTA West           Hawaii    29Sep26   23:56    140      5      9
0000PKMH1  PTA Keamuku        Hawaii    29Sep26   23:50    130      0      0
0000PTRH1  PTA Range 17       Hawaii    29Sep26   23:49    130      3      5
0000PERH1  Puhe CS            Hawaii    30Sep26   00:24     50      3      6
0000KWHH1  Kawaihae NOS       Hawaii               MSG    MSG    MSG    MSG
0000HHKH1  HELCO Hulukupuna   Hawaii    30Sep26   00:30      0      5      7
0000PLAH1  Puuloa             Hawaii    30Sep26   00:15    290      4      4
0000HMLH1  HELCO Maluokalani  Hawaii               MSG    MSG    MSG    MSG
0000HKDH1  HELCO Ala Kahua    Hawaii    30Sep26   00:30    210      6      9
0000KHRH1  Kohala Ranch       Hawaii    30Sep26   00:35     50      3      7
0000KEHH1  Kehena             Hawaii    30Sep26   00:15    200      3      3
```

---

### 11. NHC Atlantic Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_atlc_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays=2 |
| **Collected** | 2026-09-30T00:43:11.322646-10:00 HST |

```text
277 ACCA62 KNHC 300549TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL200 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Roberts*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 12. NHC Atlantic Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_atlc_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays=7 |
| **Collected** | 2026-09-30T00:44:11.032875-10:00 HST |

```text
277 ACCA62 KNHC 300549TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL200 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Roberts*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 13. NHC Central Pacific Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_cpac_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=2 |
| **Collected** | 2026-09-30T00:47:11.404375-10:00 HST |

```text
277 ACCA62 KNHC 300549TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL200 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Roberts*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 14. NHC Central Pacific Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_cpac_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=7 |
| **Collected** | 2026-09-30T00:48:11.273195-10:00 HST |

```text
277 ACCA62 KNHC 300549TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL200 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Roberts*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 15. NHC Eastern Pacific Tropical Weather Outlook — 2 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_epac_2day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=epac&fdays=2 |
| **Collected** | 2026-09-30T00:41:11.461348-10:00 HST |

```text
277 ACCA62 KNHC 300549TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL200 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Roberts*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 16. NHC Eastern Pacific Tropical Weather Outlook — 7 day

| Field | Value |
|---|---|
| **Resource ID** | nhc_gtwo_epac_7day |
| **Official source** | https://www.nhc.noaa.gov/gtwo.php?basin=epac&fdays=7 |
| **Collected** | 2026-09-30T00:42:11.349070-10:00 HST |

```text
277 ACCA62 KNHC 300549TWOSATPerspectiva de tiempo tropicalCentro Nacional de Huracanes del SNM Miami FL200 AM EDT miércoles 30 de septiembre de 2026Para el Atlántico Norte...Mar Caribe y el Golfo de AméricaSistemas activos: El Centro Nacional de Huracanes está emitiendoadvertencias sobre la Tormenta Tropical Hanna, ubicada sobre elAtlántico subtropical central.No se espera la formación de ciclones tropicales durante lospróximos 7 días.$$Pronosticador Roberts*** Este producto ha sido procesado automáticamente utilizando unprograma de traducción y puede contener omisiones y errores. ElServicio Nacional de Meteorología no puede garantizar la precisióndel texto convertido. De haber alguna duda, el texto en inglés essiempre la versión autorizada. ***
```

---

### 17. NHC source index

| Field | Value |
|---|---|
| **Resource ID** | nhc_homepage |
| **Official source** | https://www.nhc.noaa.gov/ |
| **Collected** | 2026-09-30T01:17:58.657719-10:00 HST |

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

Last update Wed, 30 Sep 2026 11:10:21 UTC

NHC issuing advisories for the Atlantic on

TS Hanna

NHC issuing advisories for the Eastern Pacific on

Hurricane Rachel

and

TD Nineteen-E

NHC issuing advisories for the Central Pacific on

TS Nolo

Last advisory issued on
Polo

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

1100 PM PDT Tue Sep 29 2026

Tropical Weather Discussion

1005 UTC Wed Sep 30 2026

Remnants of Polo

Satellite |
Buoys |
Grids |
Storm Archive

...POLO DISSIPATES OVER NORTHWESTERN MEXICO...

8:00 PM MST Tue Sep 29

Location: 30.5°N 108.0°W

Moving: NE at 23 mph

Min pressure: 996 mb

Max sustained: 35 mph

Public

Advisory

#38

800 PM MST

Forecast

Advisory

#38

0300 UTC

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

Rainfall
Potential

Hurricane Rachel

Satellite |
Buoys |
Grids |
Storm Archive

...RACHEL IS STRENGTHENING...
...COULD BECOME A MAJOR HURRICANE IN A DAY OR SO...

2:00 AM MST Wed Sep 30

Location: 17.6°N 107.2°W

Moving: NW at 10 mph

Min pressure: 979 mb

Max sustained: 85 mph

Public

Advisory

#13

200 AM MST

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

800 PM HST Tue Sep 29 2026

Tropical Storm Nolo

Satellite |
Buoys |
Grids |
Storm Archive

...NOLO CONTINUES TO BRING DANGEROUS CONDITIONS TO PORTIONS OF THE PAPAHANAUMOKUAKEA MARINE NATIONAL MONUMENT...
...NOLO NOW TURNING WEST-NORTHWESTWARD...

11:00 PM HST Tue Sep 29

Location: 22.4°N 164.6°W

Moving: WNW at 6 mph

Min pressure: 987 mb

Max sustained: 70 mph

Public

Advisory

#39

1100 PM HST

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

200 AM EDT Wed Sep 30 2026

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

### 18. Offshore Forecast (40-240nm)

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

### 19. Statewide Surf Observations

| Field | Value |
|---|---|
| **Resource ID** | surfreports_statewide_observations |
| **Official source** | https://www.weather.gov/hfo/surfreports |
| **Collected** | Unknown HST |

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

### 20. Tsunami Bulletin product type reference

| Field | Value |
|---|---|
| **Resource ID** | hfo_tib_reference |
| **Official source** | https://forecast.weather.gov/product_types.php |
| **Collected** | 2026-09-30T01:03:12.076164-10:00 HST |

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

Brochures

Weather-Ready Nation

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
