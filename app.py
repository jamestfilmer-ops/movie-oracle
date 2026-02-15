from datetime import datetime
import time
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
# Keyword/tag mappings for soft matching (expand as needed)
match_keywords = {
    "MOOD": {
        "Uplifting": ["inspiring", "heartwarming", "joy", "hope", "feel good", "positive"],
        "Cynical": ["dark", "sarcastic", "bitter", "nihilistic", "cynical"],
        "Reflective": ["introspective", "thought-provoking", "philosophical", "meditation", "existential"],
        "Tense": ["suspenseful", "thrilling", "nerve-wracking", "anxious", "edge-of-seat"]
    },
    "PACING": {
        "Fast": ["fast-paced", "action-packed", "rapid", "high-octane"],
        "Balanced": ["well-paced", "steady"],
        "Slow Burn": ["slow", "deliberate", "atmospheric", "methodical", "builds gradually"]
    },
    "VISUALS": {
        "Vibrant": ["colorful", "vivid", "bright", "saturated"],
        "Gritty": ["raw", "realistic", "dirty", "grimy", "handheld"],
        "Neon": ["cyberpunk", "synthwave", "neon-lit", "retro-futuristic"],
        "Noir": ["shadowy", "black and white", "monochrome", "venetian blinds", "femme fatale"]
    },
    "DEPTH": {
        "Linear": ["straightforward", "simple plot"],
        "Engaging": ["twists", "layered"],
        "Mind-Bending": ["complex", "puzzle", "non-linear", "mindfuck", " Inception-like", "philosophical"]
    },
    "HEART": {
        "Heavy": ["emotional", "heartbreaking", "tragic", "trauma"],
        "Light": ["fun", "breezy", "feel-good"],
        "Neutral": []
    },
    "THEME": {
        "Growth": ["coming-of-age", "self-discovery", "redemption", "personal growth"],
        "Power": ["ambition", "corruption", "dominance", "control"],
        "Justice": ["revenge", "moral", "right vs wrong", "law"],
        "Connection": ["love", "friendship", "family", "relationship", "human bond"]
    },
    # Hard-ish filters (used with higher weight or exact match)
    "ERA": {
        "Classic": lambda y: y <= 1960,
        "Golden Age": lambda y: 1960 < y <= 1980,
        "Modern": lambda y: 1980 < y <= 2000,
        "Contemporary": lambda y: y > 2000
    },
    "RUNTIME": {
        "Short": lambda r: r <= 90,
        "Standard": lambda r: 90 < r <= 130,
        "Epic": lambda r: r > 130
    },
    "RATING": {  # Maturity (approximate via certification)
        "Family": ["G", "PG", "TV-G", "TV-Y"],
        "Teen": ["PG-13", "TV-14", "12"],
        "Adult": ["R", "NC-17", "TV-MA", "18"]
    }
}

# Genre mapping (your GENRE answers → TMDB genre names/ids)
genre_map = {
    "Sci-Fi": ["Science Fiction", "sci-fi"],
    "Drama": ["Drama"],
    "Comedy": ["Comedy"],
    "Thriller": ["Thriller", "Mystery", "Crime"]
}
st.set_page_config(page_title="Oracle", layout="wide")
style = "<style>header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;} .stApp {background-color: #000000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;} .block-container {display: flex; justify-content: center; align-items: center; height: 100vh; max-width: 1000px !important; margin: auto;} .apple-card {background: #1c1c1e; border-radius: 32px; padding: 60px; text-align: center; box-shadow: 0 30px 60px rgba(0,0,0,0.5); border: 1px solid #3a3a3c; width: 100%;} h1 {color: #ffffff !important; font-size: 48px !important; font-weight: 700 !important; letter-spacing: -1.5px !important; margin-bottom: 10px !important;} h2 {color: #86868b !important; font-size: 24px !important; font-weight: 500 !important; margin-bottom: 40px !important;} .stButton>button {background: #ffffff; color: #000000; border-radius: 980px; padding: 12px 30px; font-size: 18px; font-weight: 600; border: none; width: 220px; margin-top: 20px;} .result-card {background: #1c1c1e; border-radius: 24px; padding: 30px; margin-bottom: 20px; border: 1px solid #3a3a3c; text-align: left;}</style>"
st.markdown(style, unsafe_allow_html=True)

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
    
    answers = st.session_state.answers
    
    try:
        df = pd.read_csv(CSV_FILE)
        # Assume columns: 'Name', 'Year' (rename if needed, e.g. df = df.rename(columns={'Title': 'Name'}))
        # Optional: if 'Rating' in df, can use it for tie-breaking
        
        candidates = []
        progress = st.progress(0)
        status_text = st.empty()
        
        for idx, row in df.iterrows():
            name = row['Name']
            year = int(row['Year']) if pd.notna(row['Year']) else None
            progress.progress((idx + 1) / len(df))
            status_text.text(f"Analyzing: {name} ({year})")
            
            meta = get_clean_meta(name, year)
            if not meta:
                continue
                
            score = 0
            match_explain = []
            
            # Hard filters / high-weight matches
            if "GENRE" in answers:
                target_genres = genre_map.get(answers["GENRE"], [])
                movie_genres = [g['name'] for g in meta.get('genres', [])]
                if any(g in movie_genres or g.lower() in ' '.join(movie_genres).lower() for g in target_genres):
                    score += 3  # strong weight
                    match_explain.append("Genre match")
            
            if "ERA" in answers and year:
                era_check = match_keywords["ERA"].get(answers["ERA"])
                if era_check and era_check(year):
                    score += 3
                    match_explain.append("Era match")
            
            if "RUNTIME" in answers and 'runtime' in meta:
                rt_check = match_keywords["RUNTIME"].get(answers["RUNTIME"])
                if rt_check and rt_check(meta['runtime']):
                    score += 2
                    match_explain.append("Runtime match")
            
            if "LANG" in answers and answers["LANG"] == "English":
                if meta.get('original_language') == 'en':
                    score += 2
                    match_explain.append("English language")
            
            if "RATING" in answers and 'release_dates' in meta:
                # Rough cert check (US first)
                certs = [r['certification'] for r in meta['release_dates'].get('results', []) if r['iso_3166_1'] == 'US']
                target_certs = match_keywords["RATING"].get(answers["RATING"], [])
                if any(c in target_certs for c in certs):
                    score += 2
                    match_explain.append("Maturity match")
            
            # Platform check
            if "APP" in answers and 'watch/providers' in meta:
                prov = meta['watch/providers'].get('results', {}).get('US', {}).get('flatrate', [])
                plat_map = {"Netflix": "netflix", "Prime": "amazon", "Max": "hbo", "Apple TV": "apple"}
                target = plat_map.get(answers["APP"], "").lower()
                if any(target in p.get('provider_name', '').lower() for p in prov):
                    score += 1
                    match_explain.append("Available on " + answers["APP"])
            
            # Soft keyword matches (mood, visuals, etc.)
            text_fields = ' '.join([
                meta.get('title', ''),
                meta.get('overview', ''),
                meta.get('tagline', '')
            ]).lower()
            
            for q in ["MOOD", "PACING", "VISUALS", "DEPTH", "HEART", "THEME", "SOUND", "STYLE"]:
                if q in answers:
                    kws = match_keywords.get(q, {}).get(answers[q], [])
                    matched = sum(1 for kw in kws if kw in text_fields)
                    if matched > 0:
                        score += 1
                        match_explain.append(f"{q}: {answers[q]} keyword hit")
            
            # Energy / Env / Filter as tie-breakers or minor boosts
            if "ENERGY" in answers and answers["ENERGY"] == "Low" and meta.get('runtime', 0) < 100:
                score += 1
            if "ENV" in answers and answers["ENV"] == "Group" and "Comedy" in [g['name'] for g in meta.get('genres', [])]:
                score += 1
            
            # Discovery mode
            vote_count = meta.get('vote_count', 0)
            if answers.get("FILTER") == "Hidden Gems" and 1000 < vote_count < 20000:
                score += 2
            elif answers.get("FILTER") == "Cult" and vote_count < 5000:
                score += 2
            # "Hits" = default, no penalty
            
            # "Apply Memory" — if CSV has ratings, prefer higher-rated
            if answers.get("AI") == "Apply Memory" and 'Rating' in row and pd.notna(row['Rating']):
                score += row['Rating'] / 2  # e.g. 4.0 → +2.0 bonus
            
            if score > 5:  # minimum threshold to avoid bad matches
                candidates.append({
                    'meta': meta,
                    'score': score,
                    'explain': match_explain,
                    'orig_row': row
                })
            
            time.sleep(0.15)  # gentle TMDB rate limit
        
        progress.empty()
        status_text.empty()
        
        if not candidates:
            st.error("No strong matches found. Try a Fresh Start or fewer strict filters.")
        else:
            # Sort: highest score first, then randomize within same score for variety
            candidates.sort(key=lambda x: (-x['score'], random.random()))
            top = candidates[:3]  # or 4/5 if you prefer
            
            for cand in top:
                data = cand['meta']
                score_pct = min(99, 70 + int(cand['score'] * 1.8))  # rough 75–99% range
                
                st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                col1, col2 = st.columns([1, 3])
                with col1:
                    posters = data.get('images', {}).get('posters', [])
                    path = posters[0]['file_path'] if posters else data.get('poster_path')
                    if path:
                        st.image(f"https://image.tmdb.org/t/p/w500{path}")
                    else:
                        st.write("(No poster)")
                with col2:
                    st.markdown(f"<h3 style='color:white; margin:0;'>{data['title']} ({data.get('release_date', '????')[:4]})</h3>", unsafe_allow_html=True)
                    overview = data.get('overview', 'No overview available.')
                    st.write(overview[:280] + "..." if len(overview) > 280 else overview)
                    st.markdown(f"<p style='color:#00ff88; font-weight:bold;'>Neural Match: {score_pct}%</p>", unsafe_allow_html=True)
                    if cand['explain']:
                        with st.expander("Why this match?"):
                            st.write(" • " + "\n • ".join(cand['explain']))
                st.markdown("</div>", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error during recommendation: {str(e)}")
    
    if st.button("Restart Diagnostic"):
        st.session_state.step = 0
        st.session_state.answers = {}
        st.rerun()
    except:
        st.error("CSV error.")

    if st.button("Restart"):
        st.session_state.step = 0
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
