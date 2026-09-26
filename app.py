import datetime
from pathlib import Path

import streamlit as st

from big_stans_brain_busters.engine import prep_game_data, generate_puzzle, validate_chain

# cache: only load the parquet once per server start vs on click
@st.cache_resource
def load_data():
    data_path = Path("data/cleaned/game_data.parquet")
    return prep_game_data(data_path)

edges_df, chains_df = load_data()

# determinism: generate today's unique seed
today = datetime.date.today()
daily_seed = int(today.strftime("%Y%m%d"))


# state mgmt: remember if user has won across page reloads
if "won" not in st.session_state:
    st.session_state.won = False

# generate puzzle only once per session into mem
if "puzzle" not in st.session_state:
    st.session_state.puzzle = generate_puzzle(chains_df, edges_df, seed = daily_seed)

actors = st.session_state.puzzle["clues"]
answers = st.session_state.puzzle["answers"]

# ui
st.title("Movie Chain")
st.write(f"**Daily Puzzle:** {today.strftime('%B %d, %Y')}")
st.markdown("Connect the actors. The **LAST** word of Movie 1 must be the **FIRST** word of Movie 2.")

st.divider()

# Layout using columns
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**Actor 1:**\n{actors[0]}")
    m1 = st.text_input("Movie 1", disabled = st.session_state.won)
with col2:
    st.info(f"**Actor 2:**\n{actors[1]}")
    m2 = st.text_input("Movie 2", disabled = st.session_state.won)
with col3:
    st.info(f"**Actor 3:**\n{actors[2]}")
    m3 = st.text_input("Movie 3", disabled = st.session_state.won)

# submission logic
if st.button("Submit Chain", type="primary", disabled = st.session_state.won):
    if not (m1 and m2 and m3):
        st.warning("Please fill in all three movies!")
    else:
        def clean_answer(text):
            cleaned = ''.join(char for char in text.lower() if char.isalnum() or char.isspace())
            return " ".join(cleaned.split())
            
        clean_users = [clean_answer(m1), clean_answer(m2), clean_answer(m3)]
        
        if validate_chain(actors, clean_users, edges_df):
            st.session_state.won = True
            st.session_state.show_balloons = True
            st.rerun() # force ui refresh to disable text boxes
        else:
            st.error("Not quite! That chain is invalid or breaks the rules. Try again.")

if st.session_state.won:
    st.success("Correct! Solved!")
    st.write("Come back tomorrow for a new puzzle!")

    if st.session_state.get("show_balloons", False):
        st.balloons()
        st.session_state.show_balloons = False