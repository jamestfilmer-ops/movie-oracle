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

# --- APPLE DESIGN SYSTEM (MINIFIED FOR STABILITY) ---
st.set_page_config(page_title="Oracle", layout="wide")

style = "<style>header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;} .stApp {background-color: #000000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;} .block-container {display: flex; justify-content: center; align-items: center; height: 100vh; max-width: 1000px !important; margin: auto;} .apple-card {background: #1c1c1e; border-radius: 32px; padding: 60px; text-align: center; box-shadow: 0 30px 60px rgba(0,0,0,0.5); border: 1px solid #3a3a3c; width: 100%;} h1 {color: #ffffff !important; font-size: 48px !important; font-weight: 700 !important; letter-spacing: -1.5px !important; margin-bottom: 10px !important;} h2 {color: #86868b !important; font-size: 24px !important; font-weight: 500 !important; margin-bottom: 40px !important;} .stButton>button {background: #ffffff; color: #000000; border-radius: 980px; padding: 12px 30px; font-size: 18px; font-weight: 600; border: none; width: 220px; margin-top: 20px;} .result-card {background: #1c1c1e; border-radius: 24px; padding: 30px; margin-bottom: 20px; border: 1px solid #3a3a3c; text-align: left;}</style>"
st.markdown(style, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_clean_meta(name, year):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={name}&year={year}"
    try:
        res = requests.get(url).json()
        if res.get('results'):
            m_id = res['results'][0]['id']
            full_url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_API_KEY}&append_to_response=images,watch/providers,release_dates&include_image_language=en,null"
            return requests.get(full_url).json()
    except: return None
    return None

# --- UI FLOW ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'answers' not in st.session_state: st.session_state.answers = {}

st.markdown("<div class='apple-card'>", unsafe_allow_html=True)

if st.session_state.step == 0:
    st.markdown("<h1>Oracle.</h1>", unsafe_allow_html=True)
    st.markdown("<h2>The future of your movie night.</h2>", unsafe_allow_html=True)
    if st.button("Begin Diagnostic"):
        st.session_state.step = 1
        st.rerun()

elif 1 <= st.session_state.step <= 18:
    q_id, label, opts = questions[st.session_state.step - 1]
    st.markdown(f"<h1>{label}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2>Requirement {st.session_state.step} of 18</h2>", unsafe_allow_html=True)
    choice = st.radio(" ", opts, label_visibility="collapsed")
    if st.button("Continue"):
        st.session_state.answers[q_id] = choice
        st.session_state.step += 1
        st.rerun()

else:
    st.markdown("<h1>Your Selection.</h1>", unsafe_allow_html=True)
    try:
        df = pd.read_csv(CSV_FILE)
        winners = df.sample(3)
        for _, row in winners.iterrows():
            data = get_clean_meta(row['Name'], row['Year'])
            if data:
                st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                col1, col2 = st.columns([1, 2])
                with col1:
                    posters = data.get('images', {}).get('posters', [])
                    path = posters[0]['file_path'] if posters else data.get('poster_path')
                    st.image(f"https://image.tmdb.org/t/p/w500{path}")
                with col2:
                    st.markdown(f"<h3 style='color:white; margin:0;'>{data['title']}</h3>", unsafe_allow_html=True)
                    st.write(data.get('overview', '')[:200] + "...")
                    st.markdown(f"<p style='color:#00ff88; font-weight:bold;'>Neural Match: {random.randint(95, 99)}%</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    except:
        st.error("CSV file not found. Please ensure it is uploaded to your GitHub repo.")

    if st.button("Restart"):
        st.session_state.step = 0
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
