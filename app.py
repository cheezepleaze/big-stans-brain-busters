from pathlib import Path
import datetime

import json

import streamlit as st

from big_stans_brain_busters.engine import prep_game_data, generate_puzzle, validate_chain

# cache: load pre-computed calendar
@st.cache_resource
def load_calendar():
    with open("data/cleaned/2026_calendar.json", "r") as f:
        return json.load(f)
calendar = load_calendar()

# get today's puzzle
today = datetime.date.today().strftime("%Y-%m-%d")

# fallback in case they visit on a date we haven't generated yet
if today not in calendar:
    st.error("No puzzle available. Dev needs to generate a new calendar.")
    st.stop()

today_puzzle = calendar[today]
actors = today_puzzle["clues"]
answers = today_puzzle["answers"]

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
            st.error("Incorrect: Chain is invalid. Try again.")

if st.session_state.won:
    st.success("Correct!")
    st.write("Come back tomorrow for a new puzzle!")

    if st.session_state.get("show_balloons", False):
        st.balloons()
        st.session_state.show_balloons = False