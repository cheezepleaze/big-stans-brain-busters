from pathlib import Path
import datetime

import json

import polars as pl

import streamlit as st

from big_stans_brain_busters.engine import validate_chain, prep_game_data

# cache: load pre-computed calendar
@st.cache_resource
def load_calendar():
    with open("data/cleaned/2026_calendar.json", "r") as f:
        return json.load(f)

# load graph edges
@st.cache_resource
def load_graph():
    graph_path = Path("data/cleaned/game_data.parquet")
    edges_df, _ = prep_game_data(graph_path)
    
    return edges_df.collect() if isinstance(edges_df, pl.LazyFrame) else edges_df
    
calendar = load_calendar()
edges_df = load_graph()

# get today's puzzle
today = datetime.date.today()
today_key = today.strftime("%Y-%m-%d")

# fallback in case they visit on a date we haven't generated yet
if today_key not in calendar:
    st.error("No puzzle available. Dev needs to generate a new calendar.")
    st.stop()

today_puzzle = calendar[today_key]
actors = today_puzzle["clues"]
answers = today_puzzle["answers"]

# state mgmt: 6 attempts
if "won" not in st.session_state:
    st.session_state.won = False
if "lost" not in st.session_state:
        st.session_state.lost = False
if "attempts_left" not in st.session_state:
    st.session_state.attempts_left = 6

is_game_over = st.session_state.won or st.session_state.lost

# ui
st.title("Movie Chain")
st.write(f"**Daily Puzzle:** {today.strftime('%B %d, %Y')}")

st.markdown("Connect the actors. The **LAST** word of Movie 1 must be the **FIRST** word of Movie 2.")
st.subheader(f"Bacons: {st.session_state.attempts_left}")

st.divider()

# Layout using columns
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**Actor 1:**\n{actors[0]}")
    m1 = st.text_input("Movie 1", disabled = is_game_over)
with col2:
    st.info(f"**Actor 2:**\n{actors[1]}")
    m2 = st.text_input("Movie 2", disabled = is_game_over)
with col3:
    st.info(f"**Actor 3:**\n{actors[2]}")
    m3 = st.text_input("Movie 3", disabled = is_game_over)

# submission logic
if st.button("Submit Chain", type = "primary", disabled = is_game_over):
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
            # force ui refresh to disable text boxes
            st.rerun() 
        else:
            # decrement life counter on incorrect
            st.session_state.attempts_left -= 1

            if st.session_state.attempts_left <= 0:
                st.session_state.lost = True
            else:
                st.toast("Invalid chain! You lost a bacon.")

            st.rerun()

if st.session_state.won:
    st.success("Correct!")
    st.write("Come back tomorrow for a new puzzle!")

    if st.session_state.get("show_balloons", False):
        st.balloons()
        st.session_state.show_balloons = False

elif st.session_state.lost:
    st.error("Out of bacons! Game over.")
    st.write("Valid answer chain:")
    st.code(f"{answers[0]} > {answers[1]} > {answers[2]}")
    st.write("Try again tomorrow.")