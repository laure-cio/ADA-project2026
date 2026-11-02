"""Download the external datasets and build the events table (2022-2025).

Run from the repository root:  python -m src.scripts.download_external_data
The hand-made lists (big_events.csv, more_events.csv) and Gresi's concert
list are not downloaded: they are already in data/.
"""
from src.data.events import build_events_table
from src.data.external import (baseball_home_games, cta_daily_ridership, pro_sports_home_games,
                               storm_events, storms_in_chicago)

OUT = "data/external/"


def main():
    storms_in_chicago(storm_events()).to_csv(OUT + "storm_events_chicago.csv", index=False)
    baseball_home_games().to_csv(OUT + "baseball_home_games.csv", index=False)
    pro_sports_home_games().to_csv(OUT + "pro_sports_home_games.csv", index=False)
    cta_daily_ridership().to_csv(OUT + "cta_daily_ridership.csv", index=False)
    build_events_table().to_csv(OUT + "events.csv", index=False)
    print("done: storms, games, CTA ridership and events table saved in", OUT)


if __name__ == "__main__":
    main()
