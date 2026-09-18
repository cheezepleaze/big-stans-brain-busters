from pathlib import Path
import logging

import polars as pl

logging.basicConfig(level = logging.INFO, 
                    format = "%(asctime)s - %(levelname)s - %(message)s")

def build_game_data():
    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"
    cleaned_dir = project_root / "data" / "cleaned"
    cleaned_dir.mkdir(exist_ok = True)

    # read args for repeated scans
    read_kwargs = {
        "separator": "\t",
        "null_values": ["\\N"],
        "quote_char": None,
        "ignore_errors": True
    }

    logging.info("Scanning and filtering datasets...")

    # titles > movies + non-adult + drop nulls
    titles = pl.scan_csv(raw_dir / "title.basics.tsv.gz", **read_kwargs).filter(
        (pl.col("titleType") == "movie") & (pl.col("isAdult") == 0)
    ).select(["tconst", "primaryTitle"]).drop_nulls()

    # ratings > filter only widly-known movies with >= 5000 votes (95%-ile of movie votes is 5910 as of Aug'26)
    ratings = pl.scan_csv(raw_dir / "title.ratings.tsv.gz", **read_kwargs).filter(
        pl.col("numVotes") >= 5000
    ).select(["tconst"])

    # principals > actors + actresses
    principals = pl.scan_csv(raw_dir / "title.principals.tsv.gz", **read_kwargs).filter(
        pl.col("category").is_in(["actor", "actress"])
    ).select(["tconst", "nconst"])

    # names > IDs + names
    names = pl.scan_csv(raw_dir / "name.basics.tsv.gz", **read_kwargs).select(
        ["nconst", "primaryName"]
    ).drop_nulls()

    logging.info("Joining...")

    # join for movie + actor connection (no ID)
    game_data = (
        titles
        .join(ratings, on = "tconst", how = "inner")
        .join(principals, on = "tconst", how = "inner")
        .join(names, on = "nconst", how = "inner")
        .select([
            pl.col("primaryName").alias("actor_name"),
            pl.col("primaryTitle").alias("movie_title")
        ]).unique()
    )

    logging.info("Running pipeline > Writing to Parquet...")

    game_data.sink_parquet(cleaned_dir / "game_data.parquet")

    logging.info(f"Game data table saved to {cleaned_dir}")

if __name__ == "__main__":
    build_game_data()