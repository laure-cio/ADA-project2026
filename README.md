
# The City's Heartbeat: Bike-Share as a Social Sensor

**Abstract**
Cities are dynamic systems whose daily rhythms reflect the collective behavior of their inhabitants. These rhythms are shaped by daily routines, seasons, and weather, while also being disrupted by unexpected events such as public gatherings, transportation disruptions, or health crisis events such as COVID-19 pandemic.
Detecting and understanding these changes requires contextual information about when and where events occur. Urban mobility data offers an opportunity to study these patterns and gain insight into unusual changes in city activity. Bike-sharing data could help us monitor these changes through timestamped and geolocated trip records. When aggregated across time and space, these observations can be used to characterize normal urban activity, detect deviations from expected patterns, and investigate their associations with real-world events.
Our project aims to explore whether bike-sharing data can serve as a distributed sensor of urban activity, helping detect unusual changes, locate their impact, and determine whether their spatiotemporal patterns can distinguish between different types of events.

## Research Questions

1. What does a “normal” day look like in Chicago, and which factors (season, weekday, weather, network size) explain it?
2. Which days deviate significantly from this normal, and how long do these deviations last (a one-day shock like a storm vs. a lasting one like COVID)?
3. Can these anomalies be linked to real events, and which types of events leave the strongest trace?
4. Does the spatial footprint of an anomaly (which zones deviate) reveal what kind of event it was?
5. (optional) Has the city’s normal rhythm itself changed over time (pre/post COVID, e-bikes)?

6. Can we model Chicago’s normal bike-sharing patterns and automatically detect significant deviations from expected activity?
7. To what extent can detected anomalies be associated with real-world events, such as extreme weather, public gatherings, or transportation disruptions?
8. Can the spatial and temporal patterns of anomalies help distinguish between different types of urban events?

## Hypotheses

1. Bike-share usage follows predictable temporal patterns after accounting for seasonality, day of the week, time of day, and weather.
2. Urban events and disruptions are associated with statistically detectable deviations from expected bike-share activity.
3. Different types of urban events generate distinct spatiotemporal patterns in bike-share anomalies.

## Proposed additional datasets

All cover 2022–2025 and are small (CSV files under 300 KB; the community areas are a 2 MB GeoJSON). Storms, games and CTA ridership come from `python -m src.scripts.download_external_data`, the hand-made lists and the concert list are already in `data/`, and the weather, calendar and community areas are prepared in `results.ipynb` (sections 3 and 4). They are joined to the trips by date, and by cell for events.

| Dataset | Use | Source | Size |
|---|---|---|---|
| Weather | normal-day variables | [Open-Meteo API](https://open-meteo.com/en/docs/historical-forecast-api) | 1,461 days |
| Holidays, school breaks | normal-day variables | `holidays` package, school calendar | 1,461 days |
| Community areas | the 37 cells | Chicago Data Portal | 77 areas |
| Home games of 7 teams | known events | [MLB Stats API](https://statsapi.mlb.com), ESPN API | 1,160 games |
| Festivals, parades, races, stadium concerts, protests of 10,000+, DNC | known events | by hand, one news or official link per date | 142 events |
| Concerts | known events | [showspace.org](https://app.showspace.org/decade/2020?location=chicago-illinois&tab=sheet), geocoded | 616 shows |
| Storm Events | city-wide drops | [NOAA](https://www.ncei.noaa.gov/stormevents/) | 305 events |
| CTA daily ridership | second sensor | [Chicago Data Portal API](https://data.cityofchicago.org/d/6iiy-9s97) | 1,461 days |

**Processing.** Each event place gets coordinates and its cell; all lists form one table, one row per event and day (`data/external/events.csv`, 1,931 rows). Events only explain anomalies, never define them. The docs warned us about playoff game types, "home" games played abroad and NOAA events without coordinates; we handle all three.

**Feasibility (`results.ipynb`, section 4.3).** Big events in quiet cells are clearly visible (Riot Fest: 7.7× the cell's normal trips), the same crowd in the busy Loop much less (Lollapalooza: +19%). 46% of the 50 strongest anomalies fall on a known event in their cell (16% by chance). Similar work: Luo et al. 2020 (Citi Bike), Zhang et al. 2016 (Divvy).

**Limits.** The lists are incomplete (one concert website, few protests or street fairs) and routes (Marathon, parades) cover several cells.

## Methods

Step 1 — Data cleaning and harmonisation (done)

- Inventory: 96 zip files, 116 CSVs, 6 different formats (2013 → 2026). All months from June 2013 to September 2026 are present. Periods are identified by the dates inside the files, not by file names (one file is misnamed).
- Common format: every trip file is converted to the same 14 columns, with dates parsed using explicit formats (0 failures on 58.2 M trips) and durations computed for all years. Data is stored as Parquet.
- Station coordinates: trips before 2020 only have a station ID. Positions come from Divvy's station files; for the 41 stations created in 2018–2019 (no station file), we use the median GPS position of their 2020 trips. This method was validated on 571 known stations (median distance 0 m).
- Cleaning rules: we remove trips shorter than 60 s or longer than 24 h, trips at technical stations (testing, repair, warehouse), trips without a position or outside Chicago, and duplicates (within and between files). 1.5% of trips are removed; 57.3 M are kept.
- Why it matters: the same rules are applied to every year, so there is no artificial break in 2020 (Divvy stopped filtering false starts in its newer files). We checked that the share removed per day stays low and stable, so cleaning does not create fake anomalies.

**RQ1. Detecting anomalies**

- Exploratory time-series analysis: trips per hour, day and station in order to identify the usual rhythm of the city.
- Statistical baseline model: Poisson or negative binomial regression to predict the expected number of trips from different predictors such as hour, day, weather, etc.
- Residual-based anomaly detection: Compare the predicted and observed trips to detect unusual patterns using standard residues and prediction intervals.

**RQ2. Explaining anomalies**

- Event–anomaly matching: Match detected anomalies to documented events in the integrated dataset based on temporal and spatial proximity.
- Comparison with control periods: Compare the frequency and magnitude of anomalies during event periods (treatment) with those observed during comparable periods without documented events (controls).
- Statistical analysis: Estimate effect sizes and confidence intervals to assess whether anomalies are more frequent or pronounced during event periods than during control periods.

**RQ3. Characterizing anomalies**

## Questions for TAs

Cubs and White Sox home games are regularly scheduled and known in advance, with about 80 a year at each stadium. They raise the trips of their cells (Lake View and Armour Square) by about 14%. Since they are part of the regular rhythm of these cells, should they be variables of the "normal day" model, or anomalies that we try to detect?

## Use of AI tools

Events part: we used an AI assistant (Claude) to help write code, search for event dates and edit text. Each date in the hand-made lists has its own source link.

##  Previous example readme

```bash
# clone project
git clone <project link>
cd <project repo>

# [OPTIONAL] create conda environment
conda create -n <env_name> python=3.11 or ...
conda activate <env_name>


# install requirements
pip install -r pip_requirements.txt
```

### How to use the library

Tell us how the code is arranged, any explanations goes here.

## Project Structure

The directory structure of new project looks like this:

```
├── data                        <- Project data files
│
├── src                         <- Source code
│   ├── data                            <- Data directory
│   ├── models                          <- Model directory
│   ├── utils                           <- Utility directory
│   ├── scripts                         <- Shell scripts
│
├── tests                       <- Tests of any kind
│
├── results.ipynb               <- a well-structured notebook showing the results
│
├── .gitignore                  <- List of files ignored by git
├── pip_requirements.txt        <- File for installing python dependencies
└── README.md
```
