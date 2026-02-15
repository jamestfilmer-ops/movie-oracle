import requests
import pandas as pd
import streamlit as st
import random

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

TMDB_API_KEY = "YOUR_TMDB_KEY"
OMDB_API_KEY = "5d2291bb"
CSV_FILE = "watchlist-isaaclindell-2026-02-14-15-55-utc.csv"

st.set_page_config(page_title="The Lindell Movie Selector", layout="wide")

# -------------------------------------------------
# CLEAN UI
# -------------------------------------------------

st.markdown("""
<style>
header, footer, #MainMenu {visibility:hidden;}

.stApp {
    background:#f5f5f7;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
}

.block-container {
    max-width:900px !important;
}

h1 {
    font-size:40px;
    font-weight:700;
    margin-bottom:0;
}

.subtitle {
    color:#555;
    margin-bottom:30px;
}

.stButton>button {
    background:#000;
    color:white;
    border-radius:8px;
    padding:10px 24px;
    font-weight:600;
    border:none;
}

.question-card {
    background:#fff;
    padding:32px;
    border-radius:18px;
    border:1px solid #e5e5ea;
    margin-top:20px;
}

.result-card {
    background:#fff;
    padding:24px;
    border-radius:16px;
    border:1px solid #e5e5ea;
    margin-bottom:24px;
}

.rating-strip {
    font-size:14px;
    color:#444;
    margin-top:10px;
}

.advisory {
    background:#fafafa;
    border:1px solid #e5e5ea;
    padding:10px;
    border-radius:10px;
    margin-top:10px;
    font-size:14px;
}

img {
    border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 18 QUESTIONS
# -------------------------------------------------

questions = [
    ("ERA", "Pick a time period", ["Pre-1970", "70s-90s", "2000-2015", "Modern"]),
    ("GENRE", "Choose a vibe", ["Drama", "Comedy", "Thriller", "Sci-Fi"]),
    ("RUNTIME", "How long?", ["Under 100 min", "100-130 min", "Epic"]),
    ("MOOD", "Tonight feels...", ["Light", "Serious", "Intense"]),
    ("LANG", "Language?", ["English", "International"]),
    ("ENERGY", "Your energy level?", ["Low", "Medium", "High"]),
    ("DISCOVERY", "What are we doing?", ["Favorites", "Hidden Gems", "Wildcard"]),
    ("DEPTH", "Story complexity?", ["Simple", "Layered"]),
    ("YEAR_BIAS", "Newer or older?", ["Newer", "Older", "No Preference"]),
    ("REWATCH", "Rewatchable?", ["Yes", "Doesn't matter"]),
    ("VISUAL", "Visual style?", ["Clean", "Gritty", "Colorful"]),
    ("PACING", "Pacing?", ["Fast", "Slow", "Balanced"]),
    ("GROUP", "Watching with?", ["Solo", "Partner", "Group"]),
    ("INTENSITY", "Violence tolerance?", ["Low", "Medium", "High"]),
    ("AWARDS", "Award winners?", ["Yes", "No Preference"]),
    ("RATING", "MPAA preference?", ["Family", "PG-13", "R", "No Preference"]),
    ("NOSTALGIA", "Feel nostalgic?", ["Yes", "No"]),
    ("SURPRISE", "Take a risk?", ["Yes", "No"])
]

# -------------------------------------------------
# DATA NORMALIZATION
# -------------------------------------------------

def normalize_columns(df):
    mapping = {
        "Name": ["Name", "Title"],
        "Year": ["Year"],
        "Genres": ["Genres"],
        "Runtime": ["Runtime"],
        "Rating": ["Rating", "Your Rating"]
    }
    for standard, aliases in mapping.items():
        for col in aliases:
            if col in df.columns:
                df[standard] = df[col]
                break
        if standard not in df.columns:
            df[standard] = None
    return df

# -------------------------------------------------
# API HELPERS
# -------------------------------------------------

@st.cache_data(show_spinner=False)
def get_tmdb(title, year):
    try:
        r = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": title, "year": year},
            timeout=6
        )
        data = r.json()
        if not data.get("results"):
            return None

        movie_id = data["results"][0]["id"]

        full = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY, "append_to_response": "images"},
            timeout=6
        )
        return full.json()
    except:
        return None


@st.cache_data(show_spinner=False)
def get_omdb(title, year):
    try:
        r = requests.get(
            "http://www.omdbapi.com/",
            params={"apikey": OMDB_API_KEY, "t": title, "y": year},
            timeout=6
        )
        data = r.json()
        if data.get("Response") == "True":
            return data
        return None
    except:
        return None

# -------------------------------------------------
# SCORING ENGINE
# -------------------------------------------------

def score_movies(df, answers):

    df = df.copy()
    df["score"] = 0

    if answers.get("GENRE"):
        genre = answers["GENRE"].lower()
        df["score"] += df["Genres"].apply(
            lambda g: 4 if isinstance(g,str) and genre in g.lower() else 0
        )

    if answers.get("RUNTIME"):
        choice = answers["RUNTIME"]
        df["score"] += df["Runtime"].apply(
            lambda r: 2 if pd.notna(r) and (
                (choice=="Under 100 min" and float(r)<100) or
                (choice=="100-130 min" and 100<=float(r)<=130) or
                (choice=="Epic" and float(r)>130)
            ) else 0
        )

    if answers.get("DISCOVERY") == "Favorites":
        df["score"] += df["Rating"].apply(
            lambda r: 3 if pd.notna(r) and float(r)>=4 else 0
        )

    if answers.get("DISCOVERY") == "Hidden Gems":
        df["score"] += df["Rating"].apply(
            lambda r: 2 if pd.notna(r) and 3<=float(r)<4 else 0
        )

    if answers.get("SURPRISE") == "Yes":
        df["score"] += df["Rating"].apply(
            lambda r: 1 if pd.isna(r) else 0
        )

    return df.sort_values("score", ascending=False)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------

if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown("<h1>The Lindell Movie Selector</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Answer a few questions and we’ll find something great.</div>", unsafe_allow_html=True)

# -------------------------------------------------
# QUESTION FLOW
# -------------------------------------------------

if st.session_state.step < len(questions):

    q_id, label, options = questions[st.session_state.step]

    st.markdown("<div class='question-card'>", unsafe_allow_html=True)
    st.markdown(f"### {label}")
    choice = st.radio("", options)

    if st.button("Next"):
        st.session_state.answers[q_id] = choice
        st.session_state.step += 1
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

else:

    df = pd.read_csv(CSV_FILE)
    df = normalize_columns(df)
    df = score_movies(df, st.session_state.answers)

    winners = df.head(3)

    for _, row in winners.iterrows():

        title = row["Name"]
        year = row["Year"]
        lb_rating = row["Rating"]

        tmdb = get_tmdb(title, year)
        omdb = get_omdb(title, year)

        st.markdown("<div class='result-card'>", unsafe_allow_html=True)

        if tmdb and tmdb.get("images", {}).get("posters"):
            posters = tmdb["images"]["posters"][:3]
            cols = st.columns(len(posters))
            for i in range(len(posters)):
                with cols[i]:
                    st.image(f"https://image.tmdb.org/t/p/w500{posters[i]['file_path']}")

        st.markdown(f"### {title}")

        rating_line = []

        if pd.notna(lb_rating):
            rating_line.append(f"Letterboxd {lb_rating}★")

        if omdb:
            if omdb.get("imdbRating") != "N/A":
                rating_line.append(f"IMDb {omdb.get('imdbRating')}")

            for r in omdb.get("Ratings", []):
                if r["Source"] == "Rotten Tomatoes":
                    rating_line.append(f"Rotten Tomatoes {r['Value']}")

            if omdb.get("Rated") != "N/A":
                rating_line.append(omdb.get("Rated"))

        if year:
            rating_line.append(str(int(year)))

        st.markdown(
            f"<div class='rating-strip'>{' • '.join(rating_line)}</div>",
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Start Over"):
        st.session_state.step = 0
        st.session_state.answers = {}
        st.rerun()
