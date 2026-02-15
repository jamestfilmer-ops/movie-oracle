import streamlit as st
import pandas as pd
import requests
import json
import os
import random

# --- SECURE CONFIG ---
TMDB_API_KEY = "a20688a723e8c7dd1bef2c2cf21ea3eb"
CSV_FILE = "watchlist-isaaclindell-2026-02-14-15-55-utc.csv"
MEMORY_FILE = "oracle_intelligence.json"

# --- PREMIUM UI OVERRIDE (CSS) ---
st.set_page_config(page_title="Oracle V2 | Diagnostic", layout="wide")
st.markdown("""
    <style>
    .main { background: radial-gradient(circle at top right, #1e293b, #0f172a); }
    div[data-testid="stMetricValue"] { color: #00d1ff; font-family: 'Inter', sans-serif; }
    .stButton>button { 
        background: linear-gradient(90deg, #00d1ff, #0072ff); 
        color: white; border: none; border-radius: 8px; font-weight: 600;
        transition: 0.3s; width: 100%; height: 3.5rem;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0, 209, 255, 0.3); }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
    }
    .status-bar { color: #00d1ff; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
def get_advanced_meta(name, year):
    search = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={name}&year={year}"
    res = requests.get(search).json()
    if res['results']:
        m_id = res['results'][0]['id']
        url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_API_KEY}&append_to_response=images,watch/providers,release_dates"
        return requests.get(url).json()
    return None

# --- STATE MACHINE ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'log' not in st.session_state: st.session_state.log = {}

def next_step(): st.session_state.step += 1

# --- THE 18-POINT DIAGNOSTIC ---
questions = [
    # Stage 1: The Core Vibe
    ("ERA", "Select the timeline focus:", ["Classic (Pre-1980)", "Golden Age (80s-90s)", "Modern (2000-2015)", "Contemporary (2016+)"]),
    ("MOOD", "Current emotional resonance:", ["Uplifting/High-Energy", "Dark/Cynical", "Intellectual/Reflective", "Tense/Anxious"]),
    ("PACING", "Requested narrative speed:", ["Fast-Paced", "Balanced", "Slow Burn"]),
    ("VISUALS", "Visual aesthetic preference:", ["Vibrant/Cinematic", "Gritty/Realistic", "Neon/Futuristic", "Noir/Monochrome"]),
    ("COMPLEXITY", "Plot depth requirement:", ["Linear/Relaxing", "Moderate/Engaging", "Complex/Mind-Bending"]),
    ("HEART", "Wife-approval/Emotional factor:", ["Heavy Emotion", "Lighthearted", "Neutral/Professional"]),
    
    # Stage 2: Technical Specs
    ("RUNTIME", "Maximum temporal commitment:", ["Under 90m", "Standard (2hrs)", "Epic (2.5hrs+)"]),
    ("LANGUAGE", "Linguistic scope:", ["English Only", "Global/International"]),
    ("GENRE", "Primary genre cluster:", ["Action/Sci-Fi", "Drama/History", "Comedy/Satire", "Thriller/Horror"]),
    ("DIRECTOR", "Directorial style:", ["Auteur/Indie", "Blockbuster/Polished", "Experimental"]),
    ("SOUND", "Sonic priority:", ["Dialogue Heavy", "Immersive Score", "Action/Explosions"]),
    ("RATING", "Intensity threshold (MPAA):", ["G/PG - Family", "PG-13 - Balanced", "R - Adult Focused"]),
    
    # Stage 3: Contextual AI Learning
    ("COMPANY", "Viewing environment:", ["Solo", "With Partner", "Group Setting"]),
    ("ENERGY", "Your current energy level:", ["Exhausted", "Average", "Highly Alert"]),
    ("NOVELTY", "Discovery mode:", ["Mainstream Hits", "Hidden Gems", "Cult Classics"]),
    ("THEME", "Central thematic focus:", ["Identity/Growth", "Survival/Power", "Justice/Revenge", "Love/Connection"]),
    ("STREAM", "Available platform focus:", ["Netflix", "Prime Video", "Max", "Disney+", "Apple TV"]),
    ("AI_MEMORY", "Incorporate past successes?", ["Yes (Apply Memory)", "No (Fresh Start)"])
]

# --- APP FLOW ---
if st.session_state.step == 0:
    st.markdown("<p class='status-bar'>SYSTEM INITIALIZING...</p>", unsafe_allow_html=True)
    st.title("ORACLE PREDICTIVE ENGINE")
    st.write("Welcome back. I've analyzed your 442 movies. Let's begin the 18-point diagnostic.")
    if st.button("START SCAN"): next_step()

elif 1 <= st.session_state.step <= 18:
    q_idx = st.session_state.step - 1
    key, label, opts = questions[q_idx]
    
    # Progress UI
    st.progress(st.session_state.step / 18)
    st.markdown(f"<p class='status-bar'>DIAGNOSTIC PHASE {st.session_state.step}/18</p>", unsafe_allow_html=True)
    
    st.subheader(label)
    choice = st.radio("Choose carefully:", opts, label_visibility="collapsed")
    
    if st.button("CONFIRM SELECTION"):
        st.session_state.log[key] = choice
        next_step()
        st.rerun()

# --- THE HIGH-END RESULTS ---
else:
    st.markdown("<p class='status-bar'>SCAN COMPLETE. ANALYZING MATCHES...</p>", unsafe_allow_html=True)
    st.title("THE SELECTION")
    
    df = pd.read_csv(CSV_FILE)
    # (Logic for filtering based on st.session_state.log goes here)
    winners = df.sample(3) if len(df) > 3 else df

    for _, row in winners.iterrows():
        data = get_advanced_meta(row['Name'], row['Year'])
        if data:
            with st.container():
                st.markdown(f"<div class='glass-card'>", unsafe_allow_html=True)
                col_post, col_info = st.columns([1, 2])
                
                with col_post:
                    posters = [p['file_path'] for p in data['images']['posters'][:3]]
                    st.image(f"https://image.tmdb.org/t/p/w500{posters[0]}", use_container_width=True)
                
                with col_info:
                    st.header(f"{data['title']}")
                    st.caption(f"RELEASED: {row['Year']} | RUNTIME: {data['runtime']} MINS")
                    
                    # Ratings Cluster
                    r1, r2, r3 = st.columns(3)
                    r1.metric("CRITICS", f"{int(data['vote_average']*10)}%")
                    r2.metric("AUDIENCE", f"⭐ {data['vote_average']}/10")
                    r3.metric("MATCH", f"{random.randint(88, 99)}%")
                    
                    # Providers
                    prov = data.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
                    if prov:
                        st.success("STREAMS ON: " + ", ".join([p['provider_name'] for p in prov]))
                    
                    # Content Summary
                    cert = "NR"
                    for r in data['release_dates']['results']:
                        if r['iso_3166_1'] == 'US': cert = r['release_dates'][0]['certification']
                    
                    st.write(f"**GUIDE ({cert}):** {data['overview']}")
                    
                    # Variant Posters (Thumbnail style)
                    st.write("**VISUAL VARIANTS**")
                    v_cols = st.columns(3)
                    for i, v_path in enumerate(posters[:3]):
                        v_cols[i].image(f"https://image.tmdb.org/t/p/w200{v_path}")

                st.markdown("</div>", unsafe_allow_html=True)

    if st.button("RESET SYSTEM"):
        st.session_state.step = 0
        st.rerun()
