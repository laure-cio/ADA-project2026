# The city's heartbeat: bikeshare as a social sensor

## Abstract

Cities are dynamic systems whose daily rhythms reflect the collective behavior of their inhabitants. These rhythms are shaped by daily routines, seasons, and weather, while also being disrupted by unexpected events such as severe weather, public gatherings and transportation disruptions.
Detecting and understanding these changes requires contextual information about when and where events occur. Urban mobility data offers an opportunity to study these patterns and gain insight into unusual changes in city activity. Bike-sharing data could help us monitor these changes through timestamped and geolocated trip records. When aggregated across time and space, these observations can be used to characterize normal urban activity, detect deviations from expected patterns, and investigate their associations with real-world events.
Our project aims to explore whether bike-sharing data can serve as a distributed sensor of urban activity, helping detect unusual changes, locate their impact, and determine whether their spatiotemporal patterns can distinguish between different types of events.

## Research Questions

1. Can we model Chicago’s normal bike-sharing patterns and automatically detect significant deviations from expected activity?
2. To what extent can detected anomalies be associated with real-world events, such as extreme weather, public gatherings, or transportation disruptions?
3. Can the spatial and temporal patterns of anomalies help distinguish between different types of urban events?

## Hypotheses

1. Bike-share usage follows predictable temporal patterns after accounting for seasonality, day of the week, time of day, and weather.
2. Urban events and disruptions are associated with statistically detectable deviations from expected bike-share activity.
3. Different types of urban events generate distinct spatiotemporal patterns in bike-share anomalies.

## Proposed additional datasets

- [Chicago Weather dataset](https://data.cityofchicago.org/Parks-Recreation/Chicago_Weather/4z7n-5k6z/about_data) from Chicago Data Portal
- [Public Health Department Events](https://data.cityofchicago.org/Events/Public-Health-Department-Events/38sz-xyf4/data_preview) from Chicago Data Portal

## Methods

**RQ1. Detecting anomalies**

- Exploratory time-series analysis: trips per hour, day and station in order to identify the usual rhythm of the city.
- Statistical baseline model: Poisson or negative binomial regression to predict the expected number of trips from different predictors such as hour, day, weather, etc.
- Residual-based anomaly detection: Compare the predicted and observed trips to detect unusual patterns using standard residues and prediction intervals.

**RQ2. Explaining anomalies**

- Event–anomaly matching: Match detected anomalies to documented events in the integrated dataset based on temporal and spatial proximity.
- Comparison with control periods: Compare the frequency and magnitude of anomalies during event periods (treatment) with those observed during comparable periods without documented events (controls).
- Statistical analysis: Estimate effect sizes and confidence intervals to assess whether anomalies are more frequent or pronounced during event periods than during control periods.

**RQ3. Characterizing anomalies**

## Proposed timeline

## Questions for TAs

##  Quickstart

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
