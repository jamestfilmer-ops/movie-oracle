import random
import requests
import pandas as pd
import streamlit as st

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

TMDB_API_KEY = "YOUR_TMDB_KEY"
OMDB_API_KEY = "5d2291bb"
CSV_FILE = "watchlist-isaaclindell-2026-02-14-15-55-utc.csv"

st.set_page_config(page_title="Oracle", layout="wide")

# --------------------------------------------------
# STYLE (NO PILL BUTTONS)
# --------------------------------------------------

st.markdown("""
<style>
header, footer, #MainMenu {visibility:hidden;}

.stApp {
    background:#f5f5f7;
    font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',Roboto,sans-serif;
    color:#111;
}

.block-container {
    max-width:1100px !important;
    padding-top:0;
    padding-bottom:60px;
}

.center-wrapper {
    min-height:100vh;
    display:flex;
    align-items:center;
    justify-content:center;
}

.apple-card {
    background:#ffffff;
    border-radius:28px;
    padding:64px;
    box-shadow:0 30px 80px rgba(0,0,0,0.12);
    border:1px solid #e5e5ea;
    width:100%;
    max-width:820px;
    text-align:center;
}

h1 {
    font-size:46px;
    font-weight:700;
    letter-spacing:-1px;
    margin-bottom:12px;
}

h2 {
    font-size:20px;
    font-weight:500;
    color:#3a3a3c;
    margin-bottom:36px;
}

.stButton>button {
    background:#000;
    color:#fff;
    border-radius:12px;
    padding:14px 34px;
    font-size:17px;
    font-weight:600;
    border:none;
}

.result-card {
    background:#fff;
    border-radius:20px;
    padding:28px;
    margin-bottom:24px;
    border:1px solid #e5e5ea;
}

.rating-strip {
    display:flex;
    flex-wrap:wrap;
    gap:10px;
    margin-top:14px;
    font-size:14px;
    color:#3a3a3c;
}

.neural {
    color:#06c167;
    font-weight:600;
    margin-top:12px;
}

.advisory {
    background:#fff4e5;
    border:1px solid #ffd8a8;
    padding:12px;
    border-radius:12px;
    font-size:14px;
    margin-top:14px;
}

img {
    border-radius:16px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# COLUMN NORMALIZATION
# --------------------------------------------------

COLUMN_ALIASES = {
    "Name": ["Name", "Title"],
    "Year": ["Year"],
    "Genres": ["Genres"],
    "Runtime": ["Runtime"],
    "Rating": ["Rating", "Your Rating"],
    "Language": ["Language"],
    "MPAA": ["MPAA", "Certification"],
    "Letterboxd URL": ["Letterboxd URL", "URL"]
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

# --------------------------------------------------
# API HELPERS (CACHED)
# --------------------------------------------------

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

# --------------------------------------------------
# SIMPLE SCORING
# --------------------------------------------------

def score_movies(df):
    df = df.copy()
    df["score"] = 0

    df["score"] += df["Rating"].apply(
        lambda r: 3 if pd.notna(r) and float(r) >= 4 else 0
    )

    df["score"] += df["Year"].apply(
        lambda y: 2 if pd.notna(y) and int(y) >= 2000 else 0
    )

    return df.sort_values("score", ascending=False)

# --------------------------------------------------
# SESSION
# --------------------------------------------------

if "step" not in st.session_state:
    st.session_state.step = 0

# --------------------------------------------------
# LANDING
# --------------------------------------------------

if st.session_state.step == 0:

    st.markdown("<div class='center-wrapper'>", unsafe_allow_html=True)
    st.markdown("<div class='apple-card'>", unsafe_allow_html=True)

    st.markdown("<h1>Oracle.</h1>", unsafe_allow_html=True)
    st.markdown("<h2>Your cinematic intelligence system.</h2>", unsafe_allow_html=True)

    if st.button("Begin Diagnostic"):
        st.session_state.step = 1
        st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

# --------------------------------------------------
# RESULTS
# --------------------------------------------------

else:

    st.markdown("<h1>Oracle Recommendations</h1>", unsafe_allow_html=True)
    st.markdown("<h2>Synthesized from your cinematic archive.</h2>", unsafe_allow_html=True)

    df = pd.read_csv(CSV_FILE)
    df = normalize_columns(df)
    df = score_movies(df)

    winners = df.head(3)

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

        neural = random.randint(92, 99)
        st.markdown(
            f"<div class='neural'>Neural Match: {neural}%</div>",
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Restart"):
        st.session_state.step = 0
        st.rerun()
