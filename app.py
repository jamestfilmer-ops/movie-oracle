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

# White-majority, black accents, Apple-like
style = """
<style>
header {visibility: hidden;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

.stApp {
    background-color: #f5f5f7; /* Apple grey-white */
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif;
    color: #111111;
}

/* Container: centered but not full-height so page can scroll */
.block-container {
    max-width: 1000px !important;
    margin-left: auto;
    margin-right: auto;
    padding-top: 60px;
    padding-bottom: 60px;
}

/* Main card */
.apple-card {
    background: #ffffff;
    border-radius: 32px;
    padding: 60px;
    text-align: center;
    box-shadow: 0 24px 60px rgba(0,0,0,0.12);
    border: 1px solid #e5e5ea;
    width: 100%;
}

/* Headings */
h1 {
    color: #000000 !important;
    font-size: 44px !important;
    font-weight: 700 !important;
    letter-spacing: -1.2px !important;
    margin-bottom: 10px !important;
}
h2 {
    color: #3a3a3c !important;
    font-size: 20px !important;
    font-weight: 500 !important;
    margin-bottom: 36px !important;
}

/* Buttons: black accent, soft radius */
.stButton>button {
    background: #000000;
    color: #ffffff;
    border-radius: 999px;
    padding: 12px 32px;
    font-size: 17px;
    font-weight: 600;
    border: none;
    width: 220px;
    margin-top: 24px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.25);
    cursor: pointer;
}
.stButton>button:hover {
    background: #1c1c1e;
}

/* Radios and labels */
[data-testid="stWidgetLabel"] p {
    color: #111111 !important;
    font-size: 16px !important;
}
label, .stRadio, .stSelectbox, .stText, .stMarkdown {
    color: #111111 !important;
}

/* Radio options spacing */
[data-baseweb="radio"] > div {
    gap: 6px;
}

/* Result cards section */
.result-card {
    background: #ffffff;
    border-radius: 24px;
    padding: 24px;
    margin-bottom: 20px;
    border: 1px solid #e5e5ea;
    text-align: left;
    color: #111111;
}

/* Result title */
.result-card h3 {
    font-size: 22px;
    margin-bottom: 8px;
}

/* Ratings row */
.rating-row {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    font-size: 14px;
    color: #3a3a3c;
}

.rating-pill {
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid #d2d2d7;
    background: #f5f5f7;
}

/* Neural Match green text */
.neural {
    color: #06c167;
    font-weight: 600;
    font-size: 16px;
    margin-top: 8px;
}
</style>
"""
st.markdown(style, unsafe_allow_html=True)

# --- TMDB HELPERS ---
def get_clean_meta(name, year):
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
                "append_to_response": "images,watch/providers,release_dates,external_ids",
                "include_image_language": "en,null"
            }
            full = requests.get(f"{base_movie}/{m_id}", params=movie_params, timeout=8)
            return full.json()
    except Exception:
        return None
    return None

# --- SCORING HELPERS ---
def safe_get(row, col):
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

    mood_choice = answers.get("MOOD")
    if mood_choice == "Uplifting" and "Genres" in df.columns:
        df["score"] += df["Genres"].apply(
            lambda g: 1 if isinstance(g, str) and "comedy" in g.lower() else 0
        )

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
    st.markdown("<h2>Curated from your Letterboxd universe.</h2>", unsafe_allow_html=True)

    try:
        df = pd.read_csv(CSV_FILE)

        scored = score_movies(df, st.session_state.answers)

        if scored.empty:
            scored = df.copy()
            scored["score"] = 0

        scored = scored.sort_values("score", ascending=False)

        top_n = min(30, len(scored))
        candidates = scored.head(top_n)
        winners = candidates.sample(min(3, len(candidates))) if top_n > 0 else pd.DataFrame()

        max_score = scored["score"].max() if not scored.empty else 1
        if max_score == 0:
            max_score = 1

        for _, row in winners.iterrows():
            name = safe_get(row, "Name")
            year = safe_get(row, "Year")
            lb_rating = safe_get(row, "Rating")  # Letterboxd rating, if present
            imdb_rating = safe_get(row, "IMDb Rating")  # Optional column in your CSV
            mpaa = safe_get(row, "MPAA")  # Optional content rating

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
                    f"<h3 style='margin:0;'>{title}</h3>",
                    unsafe_allow_html=True
                )

                overview = (data.get("overview") or "").strip()
                if overview:
                    preview = overview[:260]
                    if len(overview) > 260:
                        preview += "..."
                    st.write(preview)

                # Ratings row: Letterboxd, IMDb, content rating, year
                rating_bits = []

                if lb_rating not in (None, "", float("nan")):
                    rating_bits.append(f"<span class='rating-pill'>Letterboxd {lb_rating}★</span>")

                # If your CSV has explicit IMDb rating, show it
                if imdb_rating not in (None, "", float("nan")):
                    rating_bits.append(f"<span class='rating-pill'>IMDb {imdb_rating}</span>")

                # Basic rating from TMDB if nothing else
                if not rating_bits:
                    tmdb_vote = data.get("vote_average")
                    if tmdb_vote:
                        rating_bits.append(f"<span class='rating-pill'>TMDB {tmdb_vote:.1f}</span>")

                if mpaa:
                    rating_bits.append(f"<span class='rating-pill'>{mpaa}</span>")

                if year:
                    rating_bits.append(f"<span class='rating-pill'>{int(year)}</span>")

                # External links (Letterboxd / IMDb) – placeholders if you have IDs in CSV
                lb_url = safe_get(row, "Letterboxd URL")
                imdb_id = data.get("imdb_id")  # from TMDB external_ids

                link_bits = []
                if lb_url:
                    link_bits.append(f"<span class='rating-pill'><a href='{lb_url}' target='_blank' style='color:#111111;text-decoration:none;'>Letterboxd</a></span>")
                if imdb_id:
                    imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
                    link_bits.append(f"<span class='rating-pill'><a href='{imdb_url}' target='_blank' style='color:#111111;text-decoration:none;'>IMDb</a></span>")

                row_html = ""
                if rating_bits:
                    row_html += "".join(rating_bits)
                if link_bits:
                    row_html += "".join(link_bits)

                if row_html:
                    st.markdown(f"<div class='rating-row'>{row_html}</div>", unsafe_allow_html=True)

                # Neural Match
                row_score = row.get("score", 0)
                try:
                    normalized = float(row_score) / float(max_score)
                except Exception:
                    normalized = 0.0
                normalized = max(0.0, min(1.0, normalized))
                neural_match = int(90 + normalized * 10)

                st.markdown(
                    f"<div class='neural'>Neural Match: {neural_match}%</div>",
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
