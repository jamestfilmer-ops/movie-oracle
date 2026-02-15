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

# --- APPLE DESIGN SYSTEM (CSS) ---
st.set_page_config(page_title="Oracle", layout="wide")

st.markdown("""
    <style>
    /* Hide all Streamlit default UI elements (The "Blank Banners") */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Background and Centering */
    .stApp {
        background-color: #000000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .block-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        max-width: 1000px !important;
        margin: auto;
    }

    /* Apple-style Card */
    .apple-card {
        background: #1c1c1e;
        border-radius: 32px;
        padding: 60px;
        text-align: center;
        box-shadow: 0 30px 6
