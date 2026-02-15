import streamlit as st
import pandas as pd
import requests
import random

# --- CONFIG ---
TMDB_API_KEY = "a20688a723e8c7dd1bef2c2cf21ea3eb"
CSV_FILE = "watchlist-isaaclindell-2026-02-14-15-55-utc.csv"

# --- THE 18-POINT DIAGNOSTIC DATA ---
questions = [
    ("ERA", "Which era should we explore?", ["Classic", "Golden Age", "Modern", "Contemporary"]),
    ("MOOD", "Define the emotional tone.", ["Uplifting", "Cynical", "Reflective", "Tense"]),
    ("PACING", "Select narrative velocity.", ["Fast", "Balanced", "Slow Burn"]),
    ("VISUALS", "Visual aesthetic.", ["Vibrant", "Gritty", "Neon", "Noir"]),
    ("DEPTH", "Complexity level.", ["Linear", "Engaging", "Mind-Bending"]),
    ("HEART", "Emotional weight.", ["Heavy", "Light", "Neutral"]),
    ("RUNTIME", "Temporal commitment.", ["Short", "Standard", "Epic"]),
    ("LANG", "Linguistic scope.", ["English", "International"]),
    ("GENRE", "Primary genre.", ["Sci-Fi", "Drama", "Comedy", "Thriller"]),
    ("STYLE", "Directorial style.", ["Polished", "Indie", "Experimental"]),
    ("SOUND", "Audio priority.", ["Dialogue", "Score", "Atmospheric"]),
    ("RATING", "Maturity rating.", ["Family", "Teen", "Adult"]),
    ("ENV", "Viewing environment.", ["Solo", "Partner", "Group"]),
    ("ENERGY", "Your energy level.", ["Low", "Medium", "High"]),
    ("FILTER", "Discovery mode.", ["Hits", "Hidden Gems", "Cult"]),
    ("THEME", "Central theme.", ["Growth", "Power", "Justice", "Connection"]),
    ("APP", "Primary platform.", ["Netflix", "Prime", "Max", "Apple TV"]),
    ("AI", "Logic mode.", ["Apply Memory", "Fresh Start"])
]

# --- APPLE DESIGN SYSTEM (STRICT FORMATTING) ---
st.set_page_config(page_title="Oracle", layout="wide")

# This style block is now condensed into a single safe line
style = "<style>header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;} .stApp {background-color: #000000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;} .block-container {display: flex; justify-content: center; align-items: center; height: 100vh; max-width: 1000px !important; margin: auto;} .apple-card {background: #1c1c1e; border-radius: 32px; padding: 60px; text-align: center; box-shadow: 0 30px 60px rgba(0,0,0,0.5); border: 1px solid #3a3a3c; width: 100%;} h1 {color: #ffffff !important; font-size: 48px !important; font-weight: 700 !important; letter-spacing: -1.5px !important; margin-bottom: 10px !important;} h2 {color: #86868b !important; font-size: 24px !important; font-weight: 500 !important; margin-bottom: 40px !important;} .stButton>button {background: #ffffff; color: #000000; border-radius: 980px; padding: 12px 30px; font-size: 18px; font-weight: 600; border: none; width: 220px; margin-top: 20px;} .result-card {background: #1c1c1e; border-radius: 24px; padding: 30px; margin-bottom: 20px; border: 1px solid #3a3a3c; text-align: left;}</style>"
st.markdown(style, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_clean_meta(name, year):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={name}&year={year}"
    try:
        res = requests.get(url).json()
        if res.get('results'):
            m_id = res['results'][0]['id']
            full_url = f"https://api.themoviedb.org/3/movie/{m_id}?api
