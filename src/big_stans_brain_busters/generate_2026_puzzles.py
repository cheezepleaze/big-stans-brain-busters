from pathlib import Path
from datetime import date, timedelta

import json

import polars as pl

from big_stans_brain_busters.engine import prep_game_data


def build_game_calendar(graph_path: Path, output_path, start_date: date, days: int = 365):
    """
    Generate calendar-year's worth of daily puzzles (JSON)
    """

    print("Loading graph...")
    edges_df, graph_df = prep_game_data(graph_path)

    print(f"Sampling {days} puzzle chains...")
    # sample without replacement
    chains = graph_df.sample(n = days, with_replacement = False, seed = 28)

    calendar = {}
    current_date = start_date

    for chain in chains.to_dicts():
        m1, m2, m3 = chain["movie_1"], chain["movie_2"], chain["movie_3"]

        def get_random_actor(movie_title: str) -> str:
            return = (
                edges_df.filter(pl.col("movie_title") == movie_title)
                .get_column("actor_name")
                .sample(n = 1)
                .item()
            )

        date_str = current_date.strftime("%Y-%m-%d")
        calendar[date_str] = {
            "clues": [get_random_actor(m1), get_random_actor(m2), get_random_actor(m3)],
            "answers": [m1, m2, m3]
        }

        current_date += timedelta(days = 1)

    # save puzzle calendar to json
    with open(output_path, "w") as f:
        json.dump(calendar, f, indent = 4)

    print(f"Successfully generated {days} daily puzzles at {output_path}")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    graph_path = project_root / "data" / "cleaned" / "game_data.parquet"
    output_json = project_root / "data" / "cleaned" / "2026_calendar.json"

    start_date = date.today()
    end_date = date(2026, 12, 31)
    
    days_remaning = (end_date - start_date).days + 1
    if days_remaning <= 0:
        print("Error: 2026 is over.")
    else:
        print(f"Generating puzzle calendar for remaining {days_remaning} of 2026...")
        build_annual_calendar(
            graph_path, output_json, 
            start_date = start_date, days = days_remaning
        )