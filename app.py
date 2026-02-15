import random
import requests
import pandas as pd
import streamlit as st

# ----------------------------------------
# CONFIG
# ----------------------------------------

TMDB_API_KEY = "YOUR_TMDB_KEY"
OMDB_API_KEY = "5d2291bb"
CSV_FILE = "watchlist-isaaclindell-2026-02-14-15-55-utc.csv"

st.set_page_config(page_title="The Lindell Movie Selector", layout="wide")

# ----------------------------------------
# CLEAN MINIMAL STYLING
# ----------------------------------------

st.markdown("""
<style>
header, footer, #MainMenu {visibility:hidden;}

.stApp {
    background:#f5f5f7;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    color:#111;
}

.block-container {
    max-width:1000px !important;
    padding-top:40px;
}

h1 {
    font-size:40px;
    font-weight:700;
    margin-bottom:4px;
}

.subtitle {
    font-size:18px;
    color:#555;
    margin-bottom:30px;
}

.stButton>button {
    background:#000;
    color:#fff;
    border-radius:8px;
    padding:10px 24px;
    font-size:15px;
    font-weight:600;
    border:none;
}

.result-card {
    background:#fff;
    border-radius:16px;
    padding:24px;
    margin-bottom:24px;
    border:1px solid #e5e5ea;
}

.rating-strip {
    margin-top:12px;
    font-size:14px;
    color:#444;
}

.advisory {
    background:#fafafa;
    border:1px solid #e5e5ea;
    padding:10px;
    border-radius:10px;
    font-size:14px;
    margin-top:10px;
}

img {
    border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------
# NORMALIZE LETTERBOXD EXPORT
# ----------------------------------------

COLUMN_ALIASES = {
    "Name": ["Name", "Title"],
    "Year": ["Year"],
    "Genres": ["Genres"],
    "Runtime": ["Runtime"],
    "Rating": ["Rating", "Your Rating"],
}

def normalize_columns(df):
    for standard, aliases in COLUMN_ALIASES.items():
        for col in aliases:
            if col in df.columns:
                df[standard] = df[col]
                break
        if standard not in df.columns:
            df[standard] = None
    return df

# ----------------------------------------
# API HELPERS
# ----------------------------------------

@st.cache_data(show_spinner=False)
def get_tmdb_meta(title, year):
    try:
        r = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": title, "year": year},
            timeout=6,
        )
        data = r.json()
        if not data.get("results"):
            return None

        movie_id = data["results"][0]["id"]

        full = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={
                "api_key": TMDB_API_KEY,
                "append_to_response": "images",
                "include_image_language": "en,null"
            },
            timeout=6,
        )
        return full.json()
    except:
        return None


@st.cache_data(show_spinner=False)
def get_omdb_data(title, year):
    try:
        r = requests.get(
            "http://www.omdbapi.com/",
            params={"apikey": OMDB_API_KEY, "t": title, "y": year},
            timeout=6,
        )
        data = r.json()
        if data.get("Response") == "True":
            return data
        return None
    except:
        return None

# ----------------------------------------
# SIMPLE PERSONAL SCORING
# ----------------------------------------

def score_movies(df):
    df = df.copy()
    df["score"] = 0

    # Favor your highly rated films
    df["score"] += df["Rating"].apply(
        lambda r: 3 if pd.notna(r) and float(r) >= 4 else 0
    )

    # Slight modern bias
    df["score"] += df["Year"].apply(
        lambda y: 1 if pd.notna(y) and int(y) >= 2000 else 0
    )

    return df.sort_values("score", ascending=False)

# ----------------------------------------
# PAGE HEADER
# ----------------------------------------

st.markdown("<h1>The Lindell Movie Selector</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtitle'>Hand-picked from your personal Letterboxd archive.</div>",
    unsafe_allow_html=True
)

# ----------------------------------------
# LOAD DATA
# ----------------------------------------

df = pd.read_csv(CSV_FILE)
df = normalize_columns(df)
df = score_movies(df)

winners = df.head(3)

# ----------------------------------------
# DISPLAY RESULTS
# ----------------------------------------

for _, row in winners.iterrows():

    title = row["Name"]
    year = row["Year"]
    lb_rating = row["Rating"]

    tmdb = get_tmdb_meta(title, year)
    omdb = get_omdb_data(title, year)

    st.markdown("<div class='result-card'>", unsafe_allow_html=True)

    if tmdb and tmdb.get("images", {}).get("posters"):
        posters = tmdb["images"]["posters"][:3]
        cols = st.columns(len(posters))
        for i in range(len(posters)):
            with cols[i]:
                st.image(
                    f"https://image.tmdb.org/t/p/w500{posters[i]['file_path']}"
                )

    st.markdown(f"### {title}")

    rating_line = []

    if pd.notna(lb_rating):
        rating_line.append(f"Letterboxd {lb_rating}★")

    if omdb:
        imdb = omdb.get("imdbRating")
        rated = omdb.get("Rated")

        if imdb and imdb != "N/A":
            rating_line.append(f"IMDb {imdb}")

        for r in omdb.get("Ratings", []):
            if r["Source"] == "Rotten Tomatoes":
                rating_line.append(f"Rotten Tomatoes {r['Value']}")

        if rated and rated != "N/A":
            rating_line.append(rated)

    if year:
        rating_line.append(str(int(year)))

    st.markdown(
        f"<div class='rating-strip'>{' • '.join(rating_line)}</div>",
        unsafe_allow_html=True
    )

    if omdb and omdb.get("Rated"):
        st.markdown(
            f"<div class='advisory'>Rated {omdb.get('Rated')} • {omdb.get('Runtime')}</div>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)
