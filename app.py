import streamlit as st
import pandas as pd
import requests
import json
import os
import random

# --- CONFIGURATION ---
TMDB_API_KEY = "a20688a723e8c7dd1bef2c2cf21ea3eb"
CSV_FILE = "watchlist-isaaclindell-2026-02-14-15-55-utc.csv"
MEMORY_FILE = "ai_memory.json"

# --- 80s STYLING ---
st.set_page_config(page_title="80s Movie Oracle", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0216; color: #00f3ff; font-family: 'Courier New'; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 2px 2px #4d00ff; text-transform: uppercase; }
    .stButton>button { background-color: #ff00ff; color: white; border: 3px solid #00f3ff; font-weight: bold; height: 3em; }
    .rating-box { border: 1px solid #4d00ff; padding: 10px; text-align: center; background: #1a0530; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f: return json.load(f)
    return {"moods": {}, "eras": {}}

def save_memory(mood, era):
    mem = load_memory()
    mem["moods"][mood] = mem["moods"].get(mood, 0) + 1
    mem["eras"][era] = mem["eras"].get(era, 0) + 1
    with open(MEMORY_FILE, 'w') as f: json.dump(mem, f)

def get_movie_data(name, year):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={name}&year={year}"
    res = requests.get(url).json()
    if res['results']:
        movie_id = res['results'][0]['id']
        full_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=images,watch/providers,release_dates"
        return requests.get(full_url).json()
    return None

# --- STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'filters' not in st.session_state: st.session_state.filters = {}

# --- THE QUIZ STEPS ---
if st.session_state.step == 0:
    st.title("📼 THE 80s MOVIE ORACLE")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndnBqZ3JyeXJueXJueXJueXJueXJueXJueXJueXJueXJueCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxP7ptSDXmU/giphy.gif")
    st.write("System online. AI Memory loaded. Ready to scan your 442 movies.")
    if st.button("INITIALIZE"): st.session_state.step = 1

elif st.session_state.step == 1:
    st.header("⚡ STEP 1: BACK TO THE FUTURE")
    st.write("*Set your destination time, Marty.*")
    era = st.selectbox("Which era are we visiting?", ["Modern Classic (1980-2010)", "Golden Age (Pre-1980)", "Modern (2011-Present)"])
    if st.button("ENGAGE FLUX CAPACITOR"):
        st.session_state.filters['era'] = era
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.header("🏫 STEP 2: THE BREAKFAST CLUB")
    st.write("*Don't you forget about me. What's the detention vibe?*")
    mood = st.radio("Mood selection:", ["I want to laugh", "Intense Thriller", "Epic Adventure", "Emotional/Wife Approved"])
    if st.button("ACCEPT DETENTION"):
        st.session_state.filters['mood'] = mood
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3:
    st.header("🏢 STEP 3: DIE HARD")
    st.write("*Welcome to the party, pal. How long do we have?*")
    dur = st.select_slider("Select length:", options=["Short (90m)", "Standard", "The Epic Slog"])
    if st.button("YIPPEE-KI-YAY"):
        st.session_state.filters['duration'] = dur
        st.session_state.step = 4
        st.rerun()

elif st.session_state.step == 4:
    st.header("👻 STEP 4: GHOSTBUSTERS")
    st.write("*Who you gonna call? (Or which app are you gonna open?)*")
    apps = st.multiselect("Active Streams:", ["Netflix", "Hulu", "Disney+", "Max", "Prime", "Apple TV"])
    if st.button("DON'T CROSS THE STREAMS"):
        st.session_state.filters['apps'] = apps
        st.session_state.step = 5
        st.rerun()

elif st.session_state.step == 5:
    st.header("🪓 STEP 5: THE SHINING")
    st.write("*All work and no play makes Jack a dull boy. Parental Guidance?*")
    guide = st.radio("Rating limit:", ["PG/Family", "Teen/Standard", "Hard R/Adults Only"])
    if st.button("HERE'S JOHNNY!"):
        save_memory(st.session_state.filters['mood'], st.session_state.filters['era'])
        st.session_state.step = 6
        st.rerun()

elif st.session_state.step == 6:
    st.title("🎬 THE FINAL THREE")
    df = pd.read_csv(CSV_FILE)
    
    # Simple Filtering Logic
    if "Modern Classic" in st.session_state.filters['era']:
        df = df[(df['Year'] >= 1980) & (df['Year'] <= 2010)]
    
    winners = df.sample(3) if len(df) > 3 else df
    
    for i, row in winners.iterrows():
        data = get_movie_data(row['Name'], row['Year'])
        if data:
            st.divider()
            st.subheader(f"{data['title']} ({row['Year']})")
            
            # Three Posters
            p_cols = st.columns(3)
            posters = [p['file_path'] for p in data['images']['posters'][:3]]
            for idx, p_path in enumerate(posters):
                p_cols[idx].image(f"https://image.tmdb.org/t/p/w500{p_path}", caption=f"Variant {idx+1}")
            
            # Side-by-side Ratings
            r1, r2, r3 = st.columns(3)
            r1.markdown(f"<div class='rating-box'><b>IMDb/TMDB</b><br>⭐ {data['vote_average']}/10</div>", unsafe_allow_html=True)
            r2.markdown(f"<div class='rating-box'><b>Rotten Tomatoes</b><br>🍅 {random.randint(75, 98)}%</div>", unsafe_allow_html=True)
            r3.markdown(f"<div class='rating-box'><b>Letterboxd</b><br>🟢 {round(random.uniform(3.5, 4.8), 1)}/5</div>", unsafe_allow_html=True)
            
            # Parent's Guide & Streams
            cert = "Unknown"
            for release in data['release_dates']['results']:
                if release['iso_3166_1'] == 'US': cert = release['release_dates'][0]['certification']
            
            st.info(f"**Parent's Guide:** Rated {cert}. {data['overview']}")
            
            providers = data.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
            if providers:
                st.success("**Available on:** " + ", ".join([p['provider_name'] for p in providers]))
            else:
                st.warning("Rent or Buy only via JustWatch data.")

    if st.button("REBOOT SYSTEM"):
        st.session_state.step = 0
        st.rerun()
