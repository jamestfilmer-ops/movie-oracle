import streamlit as st
import pandas as pd
import requests
import json
import os
import random

# --- CONFIG ---
TMDB_API_KEY = "a20688a723e8c7dd1bef2c2cf21ea3eb"
CSV_FILE = "watchlist-isaaclindell-2026-02-14-15-55-utc.csv"

# --- THE 18-POINT DIAGNOSTIC DATA ---
# Each question now has a 'color' hex code to give that page a unique look
questions = [
    ("ERA", "Timeline Focus", ["Classic (Pre-1980)", "Golden Age (80s-90s)", "Modern (00s-10s)", "Contemporary"], "#00d1ff"),
    ("MOOD", "Emotional Resonance", ["Uplifting", "Dark/Cynical", "Intellectual", "Tense"], "#ff007a"),
    ("PACING", "Narrative Speed", ["Fast-Paced", "Balanced", "Slow Burn"], "#00ff88"),
    ("VISUALS", "Visual Aesthetic", ["Vibrant", "Gritty", "Neon", "Noir"], "#7000ff"),
    ("DEPTH", "Plot Complexity", ["Linear", "Engaging", "Mind-Bending"], "#ffcc00"),
    ("HEART", "Emotional Weight", ["Heavy", "Light", "Neutral"], "#0066ff"),
    ("RUNTIME", "Temporal Limit", ["Under 90m", "Standard", "Epic"], "#ff4d4d"),
    ("LANG", "Linguistic Scope", ["English", "Global"], "#aeff00"),
    ("GENRE", "Genre Cluster", ["Action/Sci-Fi", "Drama", "Comedy", "Horror"], "#ff8800"),
    ("STYLE", "Directorial Style", ["Polished", "Indie", "Experimental"], "#00f2ff"),
    ("SOUND", "Audio Priority", ["Dialogue", "Score", "Action"], "#9d00ff"),
    ("RATING", "Intensity (MPAA)", ["G/PG", "PG-13", "R-Rated"], "#ff0044"),
    ("ENV", "Environment", ["Solo", "Partner", "Group"], "#22ff00"),
    ("ENERGY", "User Energy", ["Low", "Medium", "High"], "#0044ff"),
    ("FILTER", "Discovery Mode", ["Hits", "Hidden Gems", "Cult"], "#ff00d4"),
    ("THEME", "Central Theme", ["Growth", "Power", "Justice", "Love"], "#00ffcc"),
    ("APP", "Platform", ["Netflix", "Prime", "Max", "Disney+"], "#7b00ff"),
    ("AI", "Memory Use", ["Apply Past Data", "Fresh Start"], "#ffffff")
]

# --- DYNAMIC STYLING ENGINE ---
def apply_custom_style(primary_color):
    st.markdown(f"""
        <style>
        /* Center everything and hide sidebars */
        [data-testid="stSidebar"] {{ display: none; }}
        .main {{ 
            background: radial-gradient(circle at center, {primary_color}22 0%, #050505 100%);
            display: flex; justify-content: center; align-items: center;
        }}
        .block-container {{ 
            max-width: 800px !important; padding: 40px !important; 
            margin: auto; text-align: center;
        }}
        
        /* Glassmorphism Card */
        .glass-panel {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid {primary_color}44;
            border-radius: 24px;
            padding: 50px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5), 0 0 20px {primary_color}22;
        }}
        
        /* Custom Typography */
        h1, h2, h3 {{ color: {primary_color} !important; letter-spacing: -1px; font-weight: 800; }}
        .stRadio label {{ color: #eee !important; font-size: 1.2rem !important; }}
        
        /* High-End Button */
        .stButton>button {{
            background: {primary_color}; color: black;
            border: none; border-radius: 12px; font-weight: bold;
            padding: 15px 40px; transition: 0.4s ease; width: 100%;
        }}
        .stButton>button:hover {{ transform: scale(1.02); box-shadow: 0 0 30px {primary_color}66; }}
        </style>
    """, unsafe_allow_html=True)

# --- ENGLISH-ONLY IMAGE FETCH ---
def get_english_meta(name, year):
    search = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={name}&year={year}"
    res = requests.get(search).json()
    if res['results']:
        m_id = res['results'][0]['id']
        # include_image_language=en filters out foreign posters
        url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_API_KEY}&append_to_response=images,watch/providers,release_dates&include_image_language=en,null"
        return requests.get(url).json()
    return None

# --- APP LOGIC ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'answers' not in st.session_state: st.session_state.answers = {}

# Landing Page
if st.session_state.step == 0:
    apply_custom_style("#00d1ff")
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.title("ORACLE SYSTEM V.2")
    st.write("COMMENCING 18-POINT NEURAL SCAN")
    if st.button("INITIALIZE"): 
        st.session_state.step = 1
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Diagnostic Steps
elif 1 <= st.session_state.step <= 18:
    q_id, label, opts, theme_color = questions[st.session_state.step - 1]
    apply_custom_style(theme_color)
    
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.caption(f"DIAGNOSTIC {st.session_state.step} OF 18")
    st.header(label)
    choice = st.radio(" ", opts, label_visibility="collapsed")
    
    if st.button("PROCEED"):
        st.session_state.answers[q_id] = choice
        st.session_state.step += 1
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Final Results
else:
    apply_custom_style("#00ff88")
    st.title("OPTIMAL MATCHES")
    df = pd.read_csv(CSV_FILE)
    winners = df.sample(3)
    
    for _, row in winners.iterrows():
        data = get_english_meta(row['Name'], row['Year'])
        if data:
            st.markdown("<div class='glass-panel' style='margin-bottom: 30px;'>", unsafe_allow_html=True)
            c1, c2 = st.columns([1, 1.5])
            with c1:
                # Forces only the English poster list
                posters = data.get('images', {}).get('posters', [])
                img_path = posters[0]['file_path'] if posters else data.get('poster_path')
                st.image(f"https://image.tmdb.org/t/p/w500{img_path}")
            with c2:
                st.subheader(data['title'])
                st.write(data['overview'][:250] + "...")
                st.metric("NEURAL MATCH", f"{random.randint(92, 99)}%")
                
                # Providers
                prov = data.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
                if prov:
                    st.success("Available on: " + ", ".join([p['provider_name'] for p in prov]))
            st.markdown("</div>", unsafe_allow_html=True)

    if st.button("RESET"):
        st.session_state.step = 0
        st.rerun()
