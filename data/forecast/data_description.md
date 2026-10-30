# Weather data

## Data Source

This dataset is a potential source of external information to integrate into our project. The data was obtained from the [Open-Meteo Historical Forecast API](https://open-meteo.com/en/docs/gfs-api?timezone=America%2FChicago&latitude=41.85&longitude=-87.65&time_mode=time_interval&start_date=2026-01-01&end_date=2026-10-21&api_mode=historical_forecast&hourly=&minutely_15=rain,temperature_2m,snowfall,sunshine_duration,weather_code,is_day&daily=weather_code), using weather data for Chicago.

From this website, we were able to download weather data from 2022 to 2025, using Chicago's coordinates: latitude: 41.85 and longitud: -87.65
From the available forecast variables we have:

- time: date (dd/mm/yyyy)
- weather_code (wmo code): Weather code is calculated from cloud cover analysis, precipitation, snowfall, cape, lifted index and gusts. The weather code per day is the most severe weather condition on a given day.
- temperature_2m_max (°C): Maximum daily air temperature at 2 meters above ground
- temperature_2m_min (°C): Minimum daily air temperature at 2 meters above ground
- rain_sum (mm): Sum of daily rain
- snowfall_sum (cm): Sum of daily snowfall
- showers_sum (mm):
- wind_speed_10m_max (km/h): Wind speed
- precipitation_sum (mm): Sum of daily precipitation (including rain, showers and snowfall)
- sunrise (iso8601): Sun rise time
- sunset (iso8601): Sun set time
- daylight_duration (s): Number of seconds of daylight per day

Weather code: Computed from cloud cover, precipitation, snowfall, showers, CAPE, wind gusts, visibility, lifted index, convective inhibition and categorical freezing rain. AIGFS and HGEFS only have cloud and precipitation inputs, so no thunderstorm or fog codes.
