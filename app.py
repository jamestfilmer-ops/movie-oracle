import streamlit as st
import pandas as pd
import requests
import numpy as np

# ==========================
# CONFIG
# ==========================

st.set_page_config(
    page_title="The Lindell Movie Selector",
    page_icon="🎬",
    layout="wide"
)

TMDB_API_KEY = "a20688a723e8c7dd1bef2c2cf21ea3eb"
OMDB_API_KEY = "5d2291bb"

# ==========================
# CLEAN CSS (NO PILL BOTTLE)
# ==========================

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
img {
    border-radius:18px;
}
.rating-pill {
    display:inline-block;
    padding:6px 12px;
    margin:4px 6px 4px 0;
    border-radius:20px;
    background:#111;
    color:white;
    font-size:13px;
}
.advisory {
    background:#fff4e5;
    border:1px solid #ffd8a8;
    padding:12px;
    border-radius:14px;
    font-size:14px;
    margin-top:10px;
}
h1 {
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)

# ==========================
# API FUNCTIONS
# ==========================

@st.cache_data(show_spinner=False)
def get_tmdb_meta(title, year):
    try:
        search = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": title,
                "year": year
            },
            timeout=6
        ).json()

        if not search.get("results"):
            return None

        movie_id = search["results"][0]["id"]

        details = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={
                "api_key": TMDB_API_KEY,
                "append_to_response": "images"
            },
            timeout=6
        ).json()

        return details
    except:
        return None


@st.cache_data(show_spinner=False)
def get_omdb_data(title, year):
    try:
        r = requests.get(
            "http://www.omdbapi.com/",
            params={
                "apikey": OMDB_API_KEY,
                "t": title,
                "y": year
            },
            timeout=6
        )
        data = r.json()
        if data.get("Response") == "True":
            return data
        return None
    except:
        return None


# ==========================
# SAMPLE MOVIE DATA
# ==========================

movies = [
    {"title": "The Dark Knight", "year": 2008},
    {"title": "La La Land", "year": 2016},
    {"title": "Prisoners", "year": 2013},
    {"title": "Knives Out", "year": 2019},
    {"title": "The Social Network", "year": 2010},
    {"title": "Interstellar", "year": 2014},
    {"title": "Parasite", "year": 2019},
    {"title": "The Prestige", "year": 2006},
]

# ==========================
# HEADER
# ==========================

st.title("🎬 The Lindell Movie Selector")
st.write("Answer 18 quick questions and get your perfect movie.")

# ==========================
# QUESTIONS
# ==========================

questions = {
    "Mood": ["Light", "Intense", "Thought-provoking", "Romantic"],
    "Pacing": ["Slow burn", "Balanced", "Fast"],
    "Genre Lean": ["Drama", "Comedy", "Thriller", "Sci-Fi"],
    "Darkness Level": ["Low", "Medium", "High"],
    "Foreign Film OK?": ["Yes", "No"],
    "Oscar Vibes": ["Yes", "No"],
    "Rewatchable?": ["Yes", "No"],
    "Plot Twist Desired?": ["Yes", "No"],
    "Runtime": ["Under 2h", "Over 2h"],
    "Music Important?": ["Yes", "No"],
    "Based on True Story?": ["Yes", "No"],
    "Big Cast?": ["Yes", "No"],
    "Action Level": ["Low", "Medium", "High"],
    "Family Friendly?": ["Yes", "No"],
    "Year Range": ["2000s", "2010s", "2020s"],
    "Dialogue Heavy?": ["Yes", "No"],
    "Cinematography Important?": ["Yes", "No"],
    "Indie Feel?": ["Yes", "No"]
}

answers = {}

with st.form("movie_form"):
    for q, opts in questions.items():
        answers[q] = st.radio(q, opts)

    submitted = st.form_submit_button("Find My Movie")

# ==========================
# RESULTS
# ==========================

if submitted:
    st.divider()
    st.subheader("Your Top Picks")

    selected_movies = np.random.choice(movies, 3, replace=False)

    for movie in selected_movies:
        title = movie["title"]
        year = movie["year"]

        data = get_tmdb_meta(title, year)
        omdb = get_omdb_data(title, year)

        st.markdown(f"## {title} ({year})")

        # Posters
        if data and data.get("images", {}).get("posters"):
            posters = data["images"]["posters"][:3]
            cols = st.columns(len(posters))
            for i, poster in enumerate(posters):
                with cols[i]:
                    st.image(
                        f"https://image.tmdb.org/t/p/w500{poster['file_path']}"
                    )

        # Ratings
        rating_bits = []

        if omdb:
            imdb_rating = omdb.get("imdbRating")
            rated = omdb.get("Rated")

            if imdb_rating and imdb_rating != "N/A":
                rating_bits.append(
                    f"<span class='rating-pill'>IMDb {imdb_rating}</span>"
                )

            for source in omdb.get("Ratings", []):
                if source["Source"] == "Rotten Tomatoes":
                    rating_bits.append(
                        f"<span class='rating-pill'>Rotten Tomatoes {source['Value']}</span>"
                    )

            if rated and rated != "N/A":
                rating_bits.append(
                    f"<span class='rating-pill'>{rated}</span>"
                )

        if rating_bits:
            st.markdown("".join(rating_bits), unsafe_allow_html=True)

        # Advisory
        if omdb:
            runtime = omdb.get("Runtime")
            awards = omdb.get("Awards")

            advisory_lines = []

            if runtime and runtime != "N/A":
                advisory_lines.append(runtime)

            if awards and awards != "N/A":
                advisory_lines.append(awards)

            if advisory_lines:
                st.markdown(
                    f"<div class='advisory'>{' • '.join(advisory_lines)}</div>",
                    unsafe_allow_html=True
                )

        st.divider()
