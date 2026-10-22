
# The City's Heartbeat: Bike-Share as a Social Sensor

Abstract
<!-- ~150 words. To write together: motivation, story, why it matters. -->

## Research Questions

1. What does a “normal” day look like in Chicago, and which factors (season, weekday, weather, network size) explain it?
2. Which days deviate significantly from this normal, and how long do these deviations last (a one-day shock like a storm vs. a lasting one like COVID)?
3. Can these anomalies be linked to real events, and which types of events leave the strongest trace?
4. Does the spatial footprint of an anomaly (which zones deviate) reveal what kind of event it was?
5. (optional) Has the city’s normal rhythm itself changed over time (pre/post COVID, e-bikes)?

## Proposed additional datasets

- Weather data: Daily temperature, precipitation, snowfall
- Holidays data :
- Event data: Used only after detection, to explain anomalies, not to define them.
- Chicago community areas: Used to assign each trip start to a zone.

## Methods

Step 1 — Data cleaning and harmonisation (done)

- Inventory: 96 zip files, 116 CSVs, 6 different formats (2013 → 2026). All months from June 2013 to September 2026 are present. Periods are identified by the dates inside the files, not by file names (one file is misnamed).
- Common format: every trip file is converted to the same 14 columns, with dates parsed using explicit formats (0 failures on 58.2 M trips) and durations computed for all years. Data is stored as Parquet.
- Station coordinates: trips before 2020 only have a station ID. Positions come from Divvy's station files; for the 41 stations created in 2018–2019 (no station file), we use the median GPS position of their 2020 trips. This method was validated on 571 known stations (median distance 0 m).
- Cleaning rules: we remove trips shorter than 60 s or longer than 24 h, trips at technical stations (testing, repair, warehouse), trips without a position or outside Chicago, and duplicates (within and between files). 1.5% of trips are removed; 57.3 M are kept.
- Why it matters: the same rules are applied to every year, so there is no artificial break in 2020 (Divvy stopped filtering false starts in its newer files). We checked that the share removed per day stays low and stable, so cleaning does not create fake anomalies.

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
