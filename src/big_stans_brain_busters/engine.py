from pathlib import Path

import polars as pl


# model: data prep and graph build

def prep_game_data(parquet_path: Path) -> pl.DataFrame:
    """
    Loads the movies dataset and builds 3-movie puzzle graph.
    """

    movies_df = pl.read_parquet(parquet_path)

    # clean titles and extract edge words
    words_df = movies_df.with_columns([
        pl.col("movie_title")
        .str.to_lowercase()
        .str.replace_all(r"[^a-z0-9\s]", "")
        .str.strip_chars()
        .str.split(" ")
        .alias("words")
    ]).filter(
        pl.col("words").list.len() > 1 # only movies containing at least 2 words
    )

    edges_df = words_df.with_columns([
        pl.col("words").list.first().alias("first_word"),
        pl.col("words").list.last().alias("last_word"),
        pl.col("words").list.join(" ").alias("clean_title")
    ]).drop("words")

    # build unique movie pool
    unique_movies = edges_df.select(["movie_title", "first_word", "last_word"]).unique()

    # self-join: 2-movie chains
    chains_2 = unique_movies.join(
        unique_movies, left_on = "last_word", right_on = "first_word", how = "inner", suffix = "_2"
    ).select([
        pl.col("movie_title").alias("movie_1"),
        pl.col("last_word").alias("match_1"),
        pl.col("movie_title_2").alias("movie_2"),
        pl.col("last_word_2").alias("match_2")
    ]).filter(pl.col("movie_1") != pl.col("movie_2"))

    # master graph: 3-movie chains
    graph_df = chains_2.join(
        unique_movies,
        left_on = "match_2",
        right_on = "first_word",
        how = "inner"
    ).select([
        pl.col("movie_1"),
        pl.col("movie_2"),
        pl.col("movie_title").alias("movie_3")
    ]).filter( 
        (pl.col("movie_3") != pl.col("movie_2")) & 
        (pl.col("movie_3") != pl.col("movie_1")) # ensure no loops
    )

    return edges_df, graph_df

# controller: game logic

def generate_puzzle(graph_df: pl.DataFrame, edges_df: pl.DataFrame, seed: int = None) -> dict:
    """
    Samples a 3-movie chain and takes one random actor per movie.
    """

    # sample a valid movie chain with seed as today's date
    chain = graph_df.sample(n = 1, seed = seed)

    m1 = chain.get_column("movie_1").item()
    m2 = chain.get_column("movie_2").item()
    m3 = chain.get_column("movie_3").item()

    def get_random_actor(movie_title: str) -> str:
        actor = edges_df.filter(
            pl.col("movie_title") == movie_title
        ).get_column("actor_name").sample(n = 1).item()

        return actor

    return {
        "clues": [get_random_actor(m1), get_random_actor(m2), get_random_actor(m3)],
        "answers": [m1, m2, m3]
    }

# validation: check for alternate chains

def validate_chain(actors: list[str], user_movies: list[str], edges_df: pl.DataFrame) -> bool:
    """
    Validates movie chain if it obeys all rules.
    """

    # does each movie belong to the actor?
    for actor, user_movie in zip(actors, user_movies):
        actor_filmography = (
            edges_df.filter(pl.col("actor_name") == actor)
            .get_column("clean_title")
            .to_list()
        )
        if user_movie not in actor_filmography:
            return False

    # do the titles connect?
    m1_words = user_movies[0].split()
    m2_words = user_movies[1].split()
    m3_words = user_movies[2].split()

    if m1_words[-1] != m2_words[0]:
        return False
    if m2_words[-1] != m3_words[0]:
        return False

    return True

# view: user interface (cli)

def play_game():
    """
    CLI for trivia game. 

    Name a separate film each actor has been in. 
    The last word of the 1st title is the 1st word of the 2nd movie, etc.

    version: v0.2.0.
    """

    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "cleaned" / "game_data.parquet"

    print("Loading trivia game graph...")
    edges_df, graph_df = prep_game_data(data_path)
    print("Graph loaded! Type 'quit' at any time to exit.\n")

    while True:
        game = generate_puzzle(graph_df, edges_df)
        actors = game["clues"]
        answers = game["answers"]

        print(f"Actors: {actors[0]} > {actors[1]} > {actors[2]}")
        print("-" * 50)

        user_m1 = input(f"Movie for {actors[0]}: ").strip().lower()
        if user_m1.lower() == "quit": break

        user_m2 = input(f"Movie for {actors[1]}: ").strip().lower()
        if user_m2.lower() == "quit": break

        user_m3 = input(f"Movie for {actors[2]}: ").strip().lower()
        if user_m3.lower() == "quit": break

        # check answers
        def clean_answer(text):
            cleaned = "".join(char for char in text.lower() if char.isalnum() or char.isspace())
            return " ".join(cleaned.split())

        clean_users = [clean_answer(user_m1), clean_answer(user_m2), clean_answer(user_m3)]
        clean_reals = [clean_answer(a) for a in answers]

        if validate_chain(actors, clean_users, edges_df):
            print("\nCorrect!")
        else:
            retry = input("\nIncorrect! Try again? (y/n): ").strip().lower()
            if retry == "y":
                continue
            else:
                print(f"\nCorrect chain:\n     {answers[0]} -> {answers[1]} -> {answers[2]}")
        
        play_again = input("\nPlay another round? (y/n): ").strip().lower()
        if play_again != 'y': break

if __name__ == "__main__":
    play_game()