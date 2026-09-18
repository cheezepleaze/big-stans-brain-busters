from pathlib import Path

import polars as pl


def prep_game_data(parquet_path: Path) -> pl.DataFrame:
    """
    Loads the game graph and creates the cleaned first + last word columns.
    """

    graph_df = pl.read_parquet(parquet_path)

    # clean titles and extract edge words
    words_df = graph_df.with_columns([
        pl.col("movie_title")
        .str.to_lowercase()
        .str.replace_all(r"[^a-z0-9\s]", "")
        .str.strip_chars()
        .str.split(" ")
        .alias("words")
    ])

    edges_df = words_df.with_columns([
        pl.col("words").list.first().alias("first_word"),
        pl.col("words").list.last().alias("last_word")
    ]).drop("words")

    return edges_df

def find_connections(actor1: str, actor2: str, actor3: str, edges_df: pl.DataFrame) -> pl.DataFrame:
    """
    Finds valid 3-movie chains connecting the three actors.
    """

    movies1 = edges_df.filter(pl.col("actor_name") == actor1).select([
        pl.col("movie_title").alias("movie_1"),
        pl.col("last_word").alias("match_word_1")
    ])

    movies2 = edges_df.filter(pl.col("actor_name") == actor2).select([
        pl.col("movie_title").alias("movie_2"),
        pl.col("first_word").alias("match_word_1"),
        pl.col("last_word").alias("match_word_2")
    ])

    movies3 = edges_df.filter(pl.col("actor_name") == actor3).select([
        pl.col("movie_title").alias("movie_3"),
        pl.col("first_word").alias("match_word_2")
    ])

    # inner joins
    connections_1_to_2 = movies1.join(movies2, on = "match_word_1", how = "inner")
    final_connections = connections_1_to_2.join(movies3, on = "match_word_2", how = "inner")

    return final_connections

def play_game():
    """
    CLI for trivia game. Name 3 actors, returns if there is a connection.

    version: v0.1.0.
    """

    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "cleaned" / "game_data.parquet"

    print("Loading trivia game graph...")
    game_df = prep_game_data(data_path)
    print("Graph loaded! Type 'quit' at any time to exit.\n")

    while True:
        a1 = input("Enter Actor 1: ").strip()
        if a1.lower() == "quit": break

        a2 = input("Enter Actor 2: ").strip()
        if a2.lower() == "quit": break

        a3 = input("Enter Actor 3: ").strip()
        if a3.lower() == "quit": break

        print(f"\nSearching for connections between {a1}, {a2}, {a3}...\n")

        results = find_connections(a1, a2, a3, game_df)

        if results.height == 0:
            print("No connectiond found. Try different actors.\n")
        else:
            print(f"Found{results.height} connection(s).")
            for row in results.iter_rows(named = True):
                print(f"    {row["movie_1"]} -> {row["movie_2"]} -> {row["movie_3"]}")
            print("\n")

if __name__ == "__main__":
    play_game()