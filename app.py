import math
import random
import requests
import pandas as pd
import streamlit as st

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

# --- STREAMLIT PAGE CONFIG & CSS ---
st.set_page_config(page_title="Oracle", layout="wide")

style = """
<style>
header {visibility: hidden;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
.stApp {
    background-color: #000000;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.block-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    max-width: 1000px !important;
    margin: auto;
}
.apple-card {
    background: #1c1c1e;
    border-radius: 32px;
    padding: 60px;
    text-align: center;
    box-shadow: 0 30px 60px rgba(0,0,0,0.5);
    border: 1px solid #3a3a3c;
    width: 100%;
}
h1 {
    color: #ffffff !important;
    font-size: 48px !important;
    font-weight: 700 !important;
    letter-spacing: -1.5px !important;
    margin-bottom: 10px !important;
}
h2 {
    color: #86868b !important;
    font-size: 24px !important;
    font-weight: 500 !important;
    margin-bottom: 40px !important;
}
.stButton>button {
    background: #ffffff;
    color: #000000;
    border-radius: 980px;
    padding: 12px 30px;
    font-size: 18px;
    font-weight: 600;
    border: none;
    width: 220px;
    margin-top: 20px;
}
.result-card {
    background: #1c1c1e;
    border-radius: 24px;
    padding: 30px;
    margin-bottom: 20px;
    border: 1px solid #3a3a3c;
    text-align: left;
}
</style>
"""
st.markdown(style, unsafe_allow_html=True)

# --- TMDB HELPERS ---
def get_clean_meta(name, year):
    # Falls back gracefully if TMDB is unreachable
    base_search = "https://api.themoviedb.org/3/search/movie"
    base_movie = "https://api.themoviedb.org/3/movie"
    try:
        search_params = {
            "api_key": TMDB_API_KEY,
            "query": str(name),
            "year": int(year) if not pd.isna(year) else ""
        }
        res = requests.get(base_search, params=search_params, timeout=8)
        res_json = res.json()
        if res_json.get("results"):
            m_id = res_json["results"][0]["id"]
            movie_params = {
                "api_key": TMDB_API_KEY,
                "append_to_response": "images,watch/providers,release_dates",
                "include_image_language": "en,null"
            }
            full = requests.get(f"{base_movie}/{m_id}", params=movie_params, timeout=8)
            return full.json()
    except Exception:
        return None
    return None

# --- SCORING HELPERS ---
def safe_get(row, col):
    # small guard to avoid KeyError
    try:
        return row[col]
    except Exception:
        return None

def map_era(year, era_choice):
    try:
        if pd.isna(year):
            return 0
        year = int(year)
    except Exception:
        return 0
    if era_choice == "Classic":
        return 1 if year < 1960 else 0
    if era_choice == "Golden Age":
        return 1 if 1960 <= year < 1985 else 0
    if era_choice == "Modern":
        return 1 if 1985 <= year < 2010 else 0
    if era_choice == "Contemporary":
        return 1 if year >= 2010 else 0
    return 0

def map_runtime(runtime, rt_choice):
    try:
        if pd.isna(runtime):
            return 0
        runtime = float(runtime)
    except Exception:
        return 0
    if rt_choice == "Short":
        return 1 if runtime < 95 else 0
    if rt_choice == "Standard":
        return 1 if 95 <= runtime <= 130 else 0
    if rt_choice == "Epic":
        return 1 if runtime > 130 else 0
    return 0

def map_language(lang_field, lang_choice):
    if not isinstance(lang_field, str):
        return 0
    lang = lang_field.lower()
    if lang_choice == "English":
        return 1 if "english" in lang or lang in ("en", "eng") else 0
    if lang_choice == "International":
        return 0 if "english" in lang or lang in ("en", "eng") else 1
    return 0

def map_genre(genres_field, genre_choice):
    if not isinstance(genres_field, str):
        return 0
    genres = [g.strip().lower() for g in genres_field.split(",")]
    return 1 if genre_choice.lower() in genres else 0

def map_filter_mode(row, filter_choice):
    rating = safe_get(row, "Rating")
    try:
        rating_value = float(rating)
    except Exception:
        rating_value = None

    if filter_choice == "Hits":
        if rating_value is not None:
            return 1 if rating_value >= 4.0 else 0
        return 0

    if filter_choice == "Hidden Gems":
        if rating_value is not None:
            return 1 if 3.0 <= rating_value < 4.0 else 0
        return 0

    if filter_choice == "Cult":
        if rating_value is None:
            return 1
        if rating_value == 5.0 or rating_value <= 2.5:
            return 1
        return 0

    return 0

def map_energy_penalty(runtime, energy_choice):
    try:
        if pd.isna(runtime):
            return 0
        runtime = float(runtime)
    except Exception:
        return 0
    if energy_choice == "Low":
        return -1 if runtime > 140 else 0
    if energy_choice == "High":
        return 1 if runtime < 110 else 0
    return 0

def score_movies(df, answers):
    df = df.copy()
    df["score"] = 0

    era_choice = answers.get("ERA")
    if era_choice and "Year" in df.columns:
        df["score"] += df["Year"].apply(lambda y: map_era(y, era_choice))

    rt_choice = answers.get("RUNTIME")
    if rt_choice and "Runtime" in df.columns:
        df["score"] += df["Runtime"].apply(lambda r: map_runtime(r, rt_choice))

    lang_choice = answers.get("LANG")
    if lang_choice and "Language" in df.columns:
        df["score"] += df["Language"].apply(lambda l: map_language(l, lang_choice))

    genre_choice = answers.get("GENRE")
    if genre_choice and "Genres" in df.columns:
        df["score"] += df["Genres"].apply(lambda g: map_genre(g, genre_choice))

    filter_choice = answers.get("FILTER")
    if filter_choice:
        df["score"] += df.apply(lambda row: map_filter_mode(row, filter_choice), axis=1)

    energy_choice = answers.get("ENERGY")
    if energy_choice and "Runtime" in df.columns:
        df["score"] += df["Runtime"].apply(lambda r: map_energy_penalty(r, energy_choice))

    # Soft bonus: if MOOD is "Uplifting", lightly reward comedies
    mood_choice = answers.get("MOOD")
    if mood_choice == "Uplifting" and "Genres" in df.columns:
        df["score"] += df["Genres"].apply(
            lambda g: 1 if isinstance(g, str) and "comedy" in g.lower() else 0
        )

    # Drop movies with zero score to keep results targeted
    df = df[df["score"] > 0]

    return df

# --- SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}

# --- MAIN UI WRAPPER ---
st.markdown("<div class='apple-card'>", unsafe_allow_html=True)

# --- STEP 0: LANDING PAGE ---
if st.session_state.step == 0:
    st.markdown("<h1>Oracle.</h1>", unsafe_allow_html=True)
    st.markdown("<h2>The future of your movie night.</h2>", unsafe_allow_html=True)
    if st.button("Begin Diagnostic"):
        st.session_state.step = 1
        st.rerun()

# --- STEPS 1–18: QUESTIONS ---
elif 1 <= st.session_state.step <= 18:
    q_id, label, opts = questions[st.session_state.step - 1]
    st.markdown(f"<h1>{label}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2>Requirement {st.session_state.step} of 18</h2>", unsafe_allow_html=True)

    choice = st.radio(" ", opts, index=0, label_visibility="collapsed")

    if st.button("Continue"):
        st.session_state.answers[q_id] = choice
        st.session_state.step += 1
        st.rerun()

# --- FINAL STEP: RESULTS ---
else:
    st.markdown("<h1>Your Selection.</h1>", unsafe_allow_html=True)

    try:
        df = pd.read_csv(CSV_FILE)

        # Score movies based on diagnostic answers
        scored = score_movies(df, st.session_state.answers)

        if scored.empty:
            # Fallback: if nothing fits, use full list with neutral scores
            scored = df.copy()
            scored["score"] = 0

        scored = scored.sort_values("score", ascending=False)

        # Top N pool, then randomize within that pool
        top_n = min(30, len(scored))
        candidates = scored.head(top_n)
        winners = candidates.sample(min(3, len(candidates))) if top_n > 0 else pd.DataFrame()

        max_score = scored["score"].max() if not scored.empty else 1
        if max_score == 0:
            max_score = 1  # avoid division by zero

        for _, row in winners.iterrows():
            name = safe_get(row, "Name")
            year = safe_get(row, "Year")

            data = get_clean_meta(name, year)

            if not data:
                continue

            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])

            with col1:
                posters = data.get("images", {}).get("posters", [])
                path = None
                if posters:
                    path = posters[0].get("file_path")
                if not path:
                    path = data.get("poster_path")
                if path:
                    st.image(f"https://image.tmdb.org/t/p/w500{path}")

            with col2:
                title = data.get("title") or name or "Untitled"
                st.markdown(
                    f"<h3 style='color:white; margin:0;'>{title}</h3>",
                    unsafe_allow_html=True
                )

                overview = data.get("overview") or ""
                overview = overview.strip()
                if overview:
                    preview = overview[:200]
                    if len(overview) > 200:
                        preview += "..."
                    st.write(preview)

                # Neural Match score based on relative score
                row_score = row.get("score", 0)
                try:
                    normalized = float(row_score) / float(max_score)
                except Exception:
                    normalized = 0.0
                normalized = max(0.0, min(1.0, normalized))
                neural_match = int(90 + normalized * 10)  # 90–100%

                st.markdown(
                    f"<p style='color:#00ff88; font-weight:bold;'>Neural Match: {neural_match}%</p>",
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"CSV error: {e}")

    if st.button("Restart"):
        st.session_state.step = 0
        st.session_state.answers = {}
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
