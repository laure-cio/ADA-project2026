
# The City's Heartbeat: Bike-Share as a Social Sensor
Abstract
<!-- ~150 words. To write together: motivation, story, why it matters. This is a first draft -->

Every day, thousands of Chicagoans take a Divvy bike. Taken together, these trips form a pulse of the city: they rise with summer, fall with winter, and follow the daily rhythm of work and leisure. But some days break the rhythm: a snowstorm, a heat wave, a pandemic, a major concert or a protest. Our idea is to use 13 years of bike-share data (2013–2026, 57 million trips) as a sensor of city life. We first model what a "normal" day looks like, taking into account season, weekday, weather and the growth of the network. Then we detect the days and neighbourhoods that deviate from this normal, and try to explain them with real events. [Story / why it matters: TO COMPLETE]

## Research Questions

1. What does a “normal” day look like in Chicago, and which factors (season, weekday, weather, network size) explain it?
2. Which days deviate significantly from this normal, and how long do these deviations last (a one-day shock like a storm vs. a lasting one like COVID)?
3. Can these anomalies be linked to real events, and which types of events leave the strongest trace?
4. Does the spatial footprint of an anomaly (which zones deviate) reveal what kind of event it was?
5. (optional) Has the city’s normal rhythm itself changed over time (pre/post COVID, e-bikes)?
 
## Proposed additional datasets
- Weather data: (Daily temperature, precipitation, snowfall)
- Holidays data :
- Event data: (big events local, national, mondial, festivals, storms, COVID, transit closures) Used only after detection, to explain anomalies, not to define them.
- Chicago community areas: Used to assign each trip start to a zone.

## Methods

Step 1 — Data cleaning and harmonisation (done)
- Inventory: 96 zip files, 116 CSVs, 6 different formats (2013 → 2026). All months from June 2013 to September 2026 are present. Periods are identified by the dates inside the files, not by file names (one file is misnamed).
- Common format: every trip file is converted to the same 14 columns, with dates parsed using explicit formats (0 failures on 58.2 M trips) and durations computed for all years. Data is stored as Parquet.
- Station coordinates: trips before 2020 only have a station ID. Positions come from Divvy's station files; for the 41 stations created in 2018–2019 (no station file), we use the median GPS position of their 2020 trips. This method was validated on 571 known stations (median distance 0 m).
- Cleaning rules: we remove trips shorter than 60 s or longer than 24 h, trips at technical stations (testing, repair, warehouse), trips without a position or outside Chicago, and duplicates (within and between files). 1.5% of trips are removed; 57.3 M are kept.
- Why it matters: the same rules are applied to every year, so there is no artificial break in 2020 (Divvy stopped filtering false starts in its newer files). We checked that the share removed per day stays low and stable, so cleaning does not create fake anomalies.

## Proposed timeline
 
| Week | Dates | Tasks |
|---|---|---|
| P2 | until 13 Oct | Read each other's project ideas, meet, discuss and choose a project |
| P2 | 14 – 27 Oct | Data cleaning, descriptive statistics, define research questions, organize the team, find and propose additional datasets, propose timeline |
| P2 | 28 Oct – 6 Nov |  |
| P2 | until 6 Nov | |
| 1 | 7 – 13 Nov | |
| 2 | 14 – 20 Nov |  |
| 3 | 21 – 27 Nov |  |
| 4 | 28 Nov – 4 Dec | |
| 5 | 5 – 11 Dec |  |
| 6 | 12 – 18 Dec (P3) |  |


 ## Organization within the team
 
| Member | Main tasks |
|---|---|
| Jeanne |  |
| Gresi |  |
| Laure | |
| Beth | |
| Sophie |  |
| All | |

## Previous example readme 

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

