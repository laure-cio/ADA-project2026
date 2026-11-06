# The city's heartbeat: bikeshare as a social sensor

## Abstract

Cities are dynamic systems whose daily rhythms reflect the collective behavior of their inhabitants. These rhythms are shaped by daily routines, seasons, and weather, while also being disrupted by unexpected events such as severe weather, public gatherings.

Detecting and understanding these changes requires contextual information about when and where events occur. Urban mobility data offers an opportunity to study these patterns and gain insight into unusual changes in city activity. Bike-sharing data could help us monitor these changes through timestamped and geolocated trip records. When aggregated across time and space, these observations can be used to characterize normal urban activity, detect deviations from expected patterns, and investigate their associations with real-world events.

Our project aims to explore whether bike-sharing data can serve as a distributed sensor of urban activity, helping detect unusual changes, locate their impact, and determine whether their spatiotemporal patterns can distinguish between different types of events.

## Research Questions

1. Can we model Chicago’s normal bike-sharing patterns and with which factors (season, weekday, weather, public holidays)?
2. To what extent can detected anomalies be associated with real-world events, such as extreme weather, public gatherings?
3. Can the spatial patterns of anomalies help distinguish between different types of urban events?
4. Do events belonging to the same category produce mobility patterns that are more similar to one another than events from different categories?

## Proposed additional datasets

All cover 2022–2025 and are small CSV files.

| Dataset | Source | Size |
| --- | --- | --- |
| Calendar (holidays, school breaks, eves, long weekends) | Built by us: `holidays` Python package + official CPS calendars | 1,461 days |
| Weather (temperature, rain, snow, wind, daylight) | Open-Meteo API | 1,461 days |
| Home games (7 teams) | MLB Stats API, ESPN | 1,160 games |
| Festivals, parades, races, concerts, protests, DNC | Collected by hand | 142 events |
| Concerts | Showspace, geocoded | 616 shows |
| Storm events | NOAA | 305 events |
| CTA daily ridership | Chicago Data Portal | 1,461 days |

**Use:** Calendar and weather will be joined to the daily trips by date and enter the model, so that regular changes are not mistaken for anomalies. Events are joined by date and cell, and only explain anomalies, never define them. CTA ridership could be a second indicator of city activity.

**Feasibility.**

- **Calendar:** holidays have clear effects (e.g. Christmas −75 %, Labor Day +13 %).
- **Weather:** temperature is strongly linked to daily trips, but partly through the season, so its effect must be measured inside the model.
- **Events:** almost half of the strongest anomalies fall on a known event in their cell (three times more than by chance). Big events are clearly visible in quiet cells but diluted in busy ones (Riot Fest vs Lollapalooza).
  
**Limitations:** Each holiday occurs only 4 times in 2022–2025, so some calendar effects are uncertain. Event lists are incomplete (collected by hand or from a single website), and each event is placed in a single cell, so events along a route, such as marathons or parades, are only partly captured.

## Methods

**Data cleaning.** 116 CSVs in 6 formats (2013–2026) are harmonised to 14 common columns and stored as Parquet. Trips before 2020 only have a station ID: positions come from Divvy’s station files, or for 41 newer stations from the median GPS position of their 2020 trips (validated on 571 stations). We remove trips under 60 s or over 24 h, technical stations, trips outside Chicago and duplicates (1.5 %, 57.3 M kept). The same rules apply to every year, so cleaning creates no fake anomalies.

**Reference period: 2022–2025.** Before 2022 the network grows fast and COVID changes how people ride. Over 2022–2025, yearly trips stay within ±3 %, the rider mix and the weekly and seasonal rhythms are stable, and e-bikes replace classic bikes rather than adding trips.

**Time resolution: daily counts on 37 cells.** Hourly counts are too sparse (92 % of area-hours under 20 trips) and almost pure noise, and many events are local: we count trips per cell per day. The 77 community areas are very unequal, so neighbouring quiet areas are merged until each cell has ≥ 20 trips on ≥ 90 % of April–October days: 37 fixed cells (cell-days with ≥ 20 trips: 38 % → 85 %).

**Model of a normal day (4.1, 5).** Counts are overdispersed, so we use a negative binomial model with a log link: weekday, weekend × season, smooth annual wave, holiday flags and one level per year. Terms are added step by step (AIC, likelihood-ratio test, out-of-sample error). For P2 the model is fitted on the whole city (Model A); for P3 we add weather (Model B), compare A and B, then fit it per cell.

**Anomalies and events.** For now, an event’s effect is measured by comparing its cell with the same weekday in the weeks around it, corrected by the change in the whole city. In P3, anomalies will come from the cell model, be located by zooming into the areas and stations of a flagged cell, and be matched with known events (RQ2) and compared between event types (RQ3).

## Proposed timeline an Organization within the team

| Week | Goal | Member |
| --- | --- | --- |
| 9–15 Nov | City model A and B (calendar + weather) - Label the data for classification. | Laure + Beth
| 16–22 Nov | Cell model | Laure + Jeanne
| 23–29 Nov | Anomaly detection and validation on known cases | Sophie + Gresi
| 30 Nov–6 Dec | Link with events (RQ2) and spatial patterns (RQ3) | Sophie + Gresi
| 7–13 Dec | Data story website and final notebook | Jeanne + Beth
| 14–18 Dec | Review: README, notebook, website | Everyone

## Questions for TAs

1. Is it reasonable to detect anomalies on the 37 cells, then zoom into flagged cells (areas, stations) to locate events?
2. Should members and casual riders be modelled separately? They have different daily rhythms and react in opposite directions on holidays.
3. Should normal weather conditions be included in the baseline model, while extreme weather events will be treated separately as potential anomalies?
4. Should we have more parameter, and correlation? Or would it overfit the model? Some idea: holidays x rider type? daily rhythm x rider_type?
5. Since home games increase bike-share trips in their respective cells by approximately 14% should home games be included as predictors in the baseline model?
6. To train our model, would it make sense to have a broader classification of events? Because it would be hard to distinguish between the effect of a concert and a baseball game, since we could expect both to increase bike usage, while a marathon or street closure might have the same impact on lowering the cycling rate in each cell.

## Project Structure

```
├── data
│
├── src
│   ├── data
│   ├── models
│   ├── utils
│   ├── scripts
│
├── tests
│
├── results.ipynb
│
├── .gitignore
├── pip_requirements.txt
└── README.md
```

**Use of AI tools:** AI tools were used to clarify the use of Python libraries and assist with selected grammatical corrections in the report. All AI-generated suggestions were reviewed and adapted by the group.
