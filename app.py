import streamlit as st
import requests
import pandas as pd
import time
import math
import json
from io import StringIO

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="Lindell Movie Picker",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# API keys — from Streamlit secrets (Cloud) or hardcoded fallback (local dev)
TMDB_KEY = st.secrets.get("TMDB_API_KEY", "a20688a723e8c7dd1bef2c2cf21ea3eb")
OMDB_KEY = st.secrets.get("OMDB_API_KEY", "5d2291bb")
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
}

# Map quiz genre answers → TMDB genre IDs
GENRE_MAP = {
    "action": [28, 12], "drama": [18], "comedy": [35],
    "thriller": [53, 9648, 80], "scifi": [878, 14],
    "war_history": [10752, 36], "horror": [27], "romance": [10749],
    "bio": [36, 99], "western": [37], "skip": [],
}

# Streaming provider IDs (TMDB uses JustWatch data)
PROVIDER_MAP = {
    "netflix": [8], "prime": [9, 119], "apple": [2, 350],
    "hulu": [15], "max": [384, 1899], "disney": [337],
    "peacock": [386, 387], "paramount": [531],
}
PROVIDER_NAMES = {
    8: "Netflix", 9: "Prime Video", 119: "Prime Video", 2: "Apple TV+",
    350: "Apple TV+", 15: "Hulu", 384: "Max", 1899: "Max",
    337: "Disney+", 386: "Peacock", 387: "Peacock", 531: "Paramount+",
}

CONTENT_BY_RATING = {
    "G":     {"violence": "None to minimal", "language": "Clean", "sexual": "None", "intense": "Mild at most"},
    "PG":    {"violence": "Mild — some action or peril", "language": "Mild", "sexual": "None to very mild", "intense": "Mild"},
    "PG-13": {"violence": "Moderate — action sequences, some blood", "language": "Moderate — some strong words", "sexual": "Mild — brief or implied at most", "intense": "Moderate"},
    "R":     {"violence": "Strong — graphic scenes possible", "language": "Strong — frequent profanity likely", "sexual": "⚠️ Check Parents Guide before watching", "intense": "Strong"},
    "NC-17": {"violence": "Severe", "language": "Strong", "sexual": "🚫 Likely explicit — NOT RECOMMENDED", "intense": "Severe"},
    "NR":    {"violence": "Unrated — varies", "language": "Unrated — varies", "sexual": "⚠️ Unrated — check Parents Guide", "intense": "Varies"},
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CUSTOM CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@400;500;600;700;800&display=swap');

/* Global */
.stApp { background: linear-gradient(180deg, #FEF9EF 0%, #F3EDDA 100%); }
h1, h2, h3 { font-family: 'Fredoka', sans-serif !important; }
p, li, span, div { font-family: 'Nunito', sans-serif !important; }

/* Header */
.main-header { text-align: center; padding: 1rem 0 0.5rem; }
.main-header h1 { font-size: 2.6rem; color: #2D2A26; margin: 0; }
.main-header .subtitle { color: #9E9890; font-size: 1rem; margin-top: 0.3rem; }
.brand-badge {
    display: inline-block; padding: 4px 16px; margin-top: 8px;
    background: #E8F5E9; border-radius: 99px;
    color: #3BA55D; font-weight: 700; font-size: 0.8rem;
    letter-spacing: 1.5px; text-transform: uppercase;
}

/* Movie cards */
.movie-card {
    background: #FFFFFF; border-radius: 18px; padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06); margin-bottom: 20px;
    border: 2px solid transparent;
}
.movie-card.gold { border-color: #3BA55D; box-shadow: 0 6px 30px rgba(59,165,93,0.12); }
.movie-card.silver { border-color: #F4A236; }
.movie-card.bronze { border-color: #4A90D9; }

.medal { font-size: 1.8rem; margin-right: 8px; }
.movie-title { font-size: 1.5rem; font-weight: 700; color: #2D2A26; line-height: 1.3; }
.movie-meta { color: #9E9890; font-size: 0.85rem; margin-top: 4px; }

.genre-tag {
    display: inline-block; padding: 3px 12px; margin: 2px 4px 2px 0;
    border-radius: 99px; font-size: 0.75rem; font-weight: 700;
}
.genre-tag.green { background: #E8F5E9; color: #3BA55D; }
.genre-tag.orange { background: #FFF3E0; color: #F4A236; }
.genre-tag.blue { background: #E3F2FD; color: #4A90D9; }

.rating-row { display: flex; flex-wrap: wrap; gap: 12px; margin: 12px 0; align-items: center; }
.rating-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 12px; border-radius: 8px; font-weight: 700; font-size: 0.85rem;
}
.rating-imdb { background: #FFF8E1; color: #F5C518; }
.rating-rt { background: #FFF0F0; color: #FA320A; }
.rating-meta { background: #E8F5E9; color: #66CC33; }
.rating-tmdb { background: #E3F2FD; color: #01B4E4; }

.streaming-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px; margin: 8px 0; border-radius: 99px;
    font-weight: 700; font-size: 0.85rem;
}
.streaming-badge.available { background: #E8F5E9; color: #2E7D32; }
.streaming-badge.rent { background: #FFF8E1; color: #F57F17; }
.streaming-badge.unavailable { background: #F5F5F5; color: #9E9890; }

.content-box {
    padding: 12px 16px; margin-top: 12px; border-radius: 12px;
    font-size: 0.85rem; line-height: 1.6;
    border-left: 3px solid;
}
.content-box.advisory { background: #FAFAF5; border-color: #ddd; color: #6B6560; }
.content-box.wife { background: #FFF8F0; border-color: #F4A236; color: #6B6560; }

.section-label {
    font-size: 0.75rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #9E9890; margin-bottom: 4px;
}

.pick-reason { font-size: 1rem; line-height: 1.7; color: #4a4540; margin: 10px 0; }

.links-row { display: flex; gap: 12px; margin-top: 12px; flex-wrap: wrap; }
.links-row a {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 4px 12px; border-radius: 8px; font-size: 0.78rem;
    font-weight: 700; text-decoration: none;
    background: #F5EFE0; color: #6B6560;
}
.links-row a:hover { background: #EDE7D5; }

/* Quiz styling */
.quiz-section {
    background: #FFFFFF; border-radius: 18px; padding: 28px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04); margin-bottom: 16px;
}
.quiz-header { color: #3BA55D; font-size: 0.75rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }

/* Buttons */
.stButton > button {
    font-family: 'Fredoka', sans-serif !important;
    border-radius: 99px !important;
    font-weight: 600 !important;
    padding: 0.6rem 2rem !important;
}

/* Footer */
.footer {
    text-align: center; padding: 2rem 0; color: #C5BFB5;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_data(ttl=86400, show_spinner=False)
def tmdb_search(title, year):
    """Search TMDB for a movie. Returns basic data."""
    try:
        params = {"api_key": TMDB_KEY, "query": title, "year": year}
        r = requests.get(f"{TMDB_BASE}/search/movie", params=params, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                m = results[0]
                return {
                    "tmdb_id": m["id"],
                    "genre_ids": m.get("genre_ids", []),
                    "overview": m.get("overview", ""),
                    "poster_path": m.get("poster_path", ""),
                    "vote_average": m.get("vote_average", 0),
                    "vote_count": m.get("vote_count", 0),
                    "popularity": m.get("popularity", 0),
                    "original_language": m.get("original_language", "en"),
                    "release_date": m.get("release_date", ""),
                }
        return None
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def tmdb_full(tmdb_id):
    """Get full TMDB details: runtime, watch providers, certification."""
    try:
        params = {"api_key": TMDB_KEY, "append_to_response": "watch/providers,release_dates"}
        r = requests.get(f"{TMDB_BASE}/movie/{tmdb_id}", params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Extract US certification
            cert = ""
            for country in data.get("release_dates", {}).get("results", []):
                if country.get("iso_3166_1") == "US":
                    for rd in country.get("release_dates", []):
                        if rd.get("certification"):
                            cert = rd["certification"]
                            break
                    break

            # Extract US watch providers
            us_providers = data.get("watch/providers", {}).get("results", {}).get("US", {})
            flatrate = us_providers.get("flatrate", [])
            rent = us_providers.get("rent", [])
            buy = us_providers.get("buy", [])
            jw_link = us_providers.get("link", "")

            return {
                "runtime": data.get("runtime", 0),
                "certification": cert,
                "tagline": data.get("tagline", ""),
                "imdb_id": data.get("imdb_id", ""),
                "flatrate_providers": [{"id": p["provider_id"], "name": p["provider_name"],
                                        "logo": p.get("logo_path", "")} for p in flatrate],
                "rent_providers": [{"id": p["provider_id"], "name": p["provider_name"],
                                    "logo": p.get("logo_path", "")} for p in rent],
                "buy_providers": [{"id": p["provider_id"], "name": p["provider_name"],
                                   "logo": p.get("logo_path", "")} for p in buy],
                "jw_link": jw_link,
                "budget": data.get("budget", 0),
                "revenue": data.get("revenue", 0),
                "genres_full": [g["name"] for g in data.get("genres", [])],
            }
        return None
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def omdb_lookup(title, year):
    """Get OMDB data: IMDb rating, RT score, Metascore, IMDb ID."""
    try:
        params = {"t": title, "y": year, "apikey": OMDB_KEY}
        r = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("Response") == "True":
                ratings = {}
                for rat in data.get("Ratings", []):
                    if "Internet Movie" in rat["Source"]:
                        ratings["imdb"] = rat["Value"]
                    elif "Rotten Tomatoes" in rat["Source"]:
                        ratings["rt"] = rat["Value"]
                    elif "Metacritic" in rat["Source"]:
                        ratings["metascore"] = rat["Value"]
                return {
                    "imdb_rating": data.get("imdbRating", "N/A"),
                    "metascore": data.get("Metascore", "N/A"),
                    "rt_score": ratings.get("rt", "N/A"),
                    "rated": data.get("Rated", "NR"),
                    "imdb_id": data.get("imdbID", ""),
                    "awards": data.get("Awards", ""),
                    "plot": data.get("Plot", ""),
                    "director": data.get("Director", ""),
                    "actors": data.get("Actors", ""),
                    "runtime_str": data.get("Runtime", ""),
                }
        return None
    except Exception:
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSV PARSING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_letterboxd_csv(file_content):
    """Parse Letterboxd CSV export into list of {name, year, date, uri}."""
    text = file_content
    if text[0] == '\ufeff':
        text = text[1:]
    lines = text.strip().split('\n')
    if len(lines) < 2:
        return []
    movies = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        # Handle quoted fields
        fields = []
        cur, in_q = "", False
        for ch in line:
            if ch == '"':
                in_q = not in_q
            elif ch == ',' and not in_q:
                fields.append(cur.strip())
                cur = ""
            else:
                cur += ch
        fields.append(cur.strip())
        if len(fields) >= 2:
            date = fields[0] if len(fields) > 0 else ""
            name = fields[1] if len(fields) > 1 else ""
            year = int(fields[2]) if len(fields) > 2 and fields[2].isdigit() else 0
            uri = fields[3] if len(fields) > 3 else ""
            if name:
                movies.append({"name": name, "year": year, "date_added": date, "uri": uri})
    return movies


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENRICHMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def enrich_light(movies, progress_bar, status_text):
    """Light enrichment: TMDB search for all movies."""
    enriched = []
    total = len(movies)
    batch_count = 0

    for i, m in enumerate(movies):
        result = tmdb_search(m["name"], m["year"])
        movie = {**m}
        if result:
            movie.update(result)
        else:
            movie.update({"tmdb_id": None, "genre_ids": [], "overview": "",
                          "poster_path": "", "vote_average": 0, "vote_count": 0,
                          "popularity": 0, "original_language": "en"})
        enriched.append(movie)

        batch_count += 1
        if batch_count >= 38:
            time.sleep(0.5)
            batch_count = 0

        progress_bar.progress((i + 1) / total)
        status_text.text(f"Loading movie data... {i+1}/{total} — {m['name']}")

    return enriched


def enrich_full_movie(movie):
    """Full enrichment for a single finalist movie."""
    data = {"streaming_flat": [], "streaming_rent": [], "streaming_buy": [],
            "runtime": 0, "certification": "NR", "jw_link": "", "imdb_id": "",
            "imdb_rating": "N/A", "metascore": "N/A", "rt_score": "N/A",
            "rated": "NR", "plot": "", "director": "", "actors": "",
            "awards": "", "genres_full": []}

    # TMDB full
    if movie.get("tmdb_id"):
        full = tmdb_full(movie["tmdb_id"])
        if full:
            data["runtime"] = full.get("runtime", 0)
            data["certification"] = full.get("certification", "NR") or "NR"
            data["streaming_flat"] = full.get("flatrate_providers", [])
            data["streaming_rent"] = full.get("rent_providers", [])
            data["streaming_buy"] = full.get("buy_providers", [])
            data["jw_link"] = full.get("jw_link", "")
            data["imdb_id"] = full.get("imdb_id", "")
            data["genres_full"] = full.get("genres_full", [])

    # OMDB
    omdb = omdb_lookup(movie["name"], movie["year"])
    if omdb:
        data["imdb_rating"] = omdb.get("imdb_rating", "N/A")
        data["metascore"] = omdb.get("metascore", "N/A")
        data["rt_score"] = omdb.get("rt_score", "N/A")
        data["rated"] = omdb.get("rated", data["certification"]) or data["certification"]
        data["plot"] = omdb.get("plot", "")
        data["director"] = omdb.get("director", "")
        data["actors"] = omdb.get("actors", "")
        data["awards"] = omdb.get("awards", "")
        if not data["imdb_id"]:
            data["imdb_id"] = omdb.get("imdb_id", "")

    movie.update(data)
    return movie


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCORING ALGORITHM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def score_movie(movie, answers):
    """Score a movie against quiz answers. Higher = better match."""
    score = 0.0
    genres = set(movie.get("genre_ids", []))
    year = movie.get("year", 2000)
    vote = movie.get("vote_average", 0)
    popularity = movie.get("popularity", 0)
    runtime = movie.get("runtime", 0)
    cert = movie.get("certification", movie.get("rated", "NR")) or "NR"
    lang = movie.get("original_language", "en")

    # ── Base quality (0-12 pts)
    score += min(vote * 1.3, 12)

    # ── Primary genre match (0-30 pts)
    primary_genres = set(GENRE_MAP.get(answers.get("genre1", ""), []))
    if primary_genres & genres:
        score += 30
    elif primary_genres:
        # Check for genre-family adjacency
        ACTION_FAMILY = {28, 12, 53, 10752}
        DRAMA_FAMILY = {18, 36, 10749}
        THRILLER_FAMILY = {53, 9648, 80, 27}
        for fam in [ACTION_FAMILY, DRAMA_FAMILY, THRILLER_FAMILY]:
            if primary_genres & fam and genres & fam:
                score += 12
                break

    # ── Secondary genre match (0-15 pts)
    sec = answers.get("genre2", "skip")
    if sec != "skip":
        sec_genres = set(GENRE_MAP.get(sec, []))
        if sec_genres & genres:
            score += 15

    # ── Mood alignment (0-25 pts)
    mood = answers.get("my_mood", "surprise")
    if mood == "laugh" and 35 in genres:
        score += 25
    elif mood == "think" and genres & {18, 878, 9648, 36}:
        score += 25
    elif mood == "feel" and genres & {18, 10749}:
        score += 25
    elif mood == "intense" and genres & {28, 53, 27, 10752, 80}:
        score += 25
    elif mood == "surprise":
        score += 8  # slight bonus for all

    # ── Era match (0-20 pts)
    era = answers.get("decade", "any")
    era_match = {
        "pre1950": year < 1950,
        "50s60s": 1950 <= year <= 1969,
        "70s80s": 1970 <= year <= 1989,
        "90s00s": 1990 <= year <= 2009,
        "2010plus": year >= 2010,
        "any": True,
    }
    if era_match.get(era, False):
        score += 20 if era != "any" else 3

    # ── Runtime match (0-18 pts, with penalties)
    rt = answers.get("time", "any")
    if runtime > 0:
        if rt == "short":
            if runtime <= 100: score += 18
            elif runtime <= 120: score += 8
            elif runtime > 140: score -= 12
        elif rt == "medium":
            if 95 <= runtime <= 140: score += 15
            elif runtime > 160: score -= 8
        elif rt == "long":
            if runtime >= 140: score += 18
            elif runtime < 90: score -= 8

    # ── Content tone (0-15 pts)
    tone = answers.get("content_tone", "dramatic")
    if tone == "light" and genres & {35, 10751, 16, 12}:
        score += 15
    elif tone == "light" and genres & {27, 80, 10752}:
        score -= 10
    elif tone == "dramatic" and 18 in genres:
        score += 15
    elif tone == "gritty" and genres & {80, 53, 10752, 28}:
        score += 15
    elif tone == "dark" and genres & {27, 53, 9648}:
        score += 15

    # ── Violence comfort (penalties)
    viol = answers.get("violence", "moderate")
    if viol == "mild":
        if genres & {10752, 27, 28}: score -= 15
        if cert in ["R", "NC-17"]: score -= 10
    elif viol == "moderate":
        if cert == "NC-17": score -= 10

    # ── Scary comfort
    scary = answers.get("scary", "mild")
    if scary == "none":
        if 27 in genres: score -= 30
        if genres & {53, 9648}: score -= 5
    elif scary == "mild":
        if 27 in genres: score -= 15
    elif scary == "creepy":
        if 27 in genres: score += 8
    elif scary == "horror":
        if 27 in genres: score += 12

    # ── Language
    lang_pref = answers.get("language", "some")
    if lang_pref == "clean" and cert in ["R", "NC-17"]:
        score -= 8
    elif lang_pref == "clean" and cert in ["G", "PG"]:
        score += 6

    # ── Emotional weight
    emo = answers.get("emotional", "moderate")
    if emo == "light":
        if genres & {35, 12, 10751}: score += 8
        if 18 in genres and vote >= 7.5: score -= 5  # acclaimed dramas tend heavy
    elif emo == "heavy" and 18 in genres:
        score += 10
    elif emo == "devastate" and 18 in genres and vote >= 7.5:
        score += 15

    # ── After feeling
    after = answers.get("after", "any")
    if after == "uplifted" and genres & {35, 12, 10751}:
        score += 10
    elif after == "uplifted" and genres & {27, 80}:
        score -= 8
    elif after == "reflective" and genres & {18, 878, 9648}:
        score += 10
    elif after == "energized" and genres & {28, 12, 35}:
        score += 10
    elif after == "moved" and 18 in genres:
        score += 10

    # ── Film type (0-18 pts)
    ft = answers.get("filmtype", "acclaimed")
    if ft == "acclaimed" and vote >= 7.5:
        score += 18
    elif ft == "acclaimed" and vote >= 7.0:
        score += 8
    elif ft == "hidden" and popularity < 25 and vote >= 6.5:
        score += 18
    elif ft == "hidden" and popularity < 50 and vote >= 6.5:
        score += 10
    elif ft == "crowd" and popularity > 40 and vote >= 6.5:
        score += 14
    elif ft == "cult" and popularity < 40 and 5.5 <= vote < 8:
        score += 14

    # ── Pacing (0-8 pts)
    pace = answers.get("pacing", "any")
    if pace == "slow" and genres & {18, 36}:
        score += 8
    elif pace == "fast" and genres & {28, 53, 35}:
        score += 8
    elif pace == "steady":
        score += 4

    # ── True story preference
    ts = answers.get("true_story", "either")
    if ts == "true" and genres & {36, 99}:
        score += 12
    elif ts == "fiction" and genres & {878, 14}:
        score += 8

    # ── B&W preference
    bw = answers.get("bw", "open")
    if bw == "color" and year < 1965:
        score -= 15
    elif bw == "love" and year < 1965:
        score += 10

    # ── Subtitles
    sub = answers.get("foreign", "any")
    if sub == "english" and lang != "en":
        score -= 25

    # ── Wildcard
    wc = answers.get("wildcard", "best")
    if wc == "surprise":
        if popularity < 20: score += 12
    elif wc == "safe":
        if vote >= 7.5 and popularity > 30: score += 12
    elif wc == "overdue":
        # Boost movies added to watchlist earliest
        date_added = movie.get("date_added", "2025-01-01")
        try:
            from datetime import datetime
            d = datetime.strptime(date_added, "%Y-%m-%d")
            years_on_list = (datetime.now() - d).days / 365
            score += min(years_on_list * 4, 15)
        except Exception:
            pass
    elif wc == "best":
        score += vote * 1.5

    # ── Wife compatibility (only if watching with wife)
    who = answers.get("who", "solo")
    if who == "wife":
        wife_likes = answers.get("wife_likes", "open")
        wife_avoids = answers.get("wife_avoids", "none")

        # Boost for her preferences
        wife_genre_map = {
            "romance_drama": {18, 10749}, "comedy": {35},
            "thriller": {53, 9648, 80}, "adventure": {28, 12},
        }
        if wife_likes != "open" and genres & wife_genre_map.get(wife_likes, set()):
            score += 20

        # Penalty for her dealbreakers
        avoid_map = {
            "violent": {28, 10752, 27}, "scary": {27},
            "weird": set(), "slow": set(),
        }
        if wife_avoids in avoid_map and genres & avoid_map[wife_avoids]:
            score -= 20
        if wife_avoids == "sad" and 18 in genres and vote >= 7.5:
            score -= 10

    # ── Family mode = strict content
    if who == "family":
        if cert in ["R", "NC-17"]: score -= 40
        if 27 in genres: score -= 20
        if cert in ["G", "PG"]: score += 20

    # ── PERMANENT: No explicit content
    if cert == "NC-17":
        score -= 80

    # ── Streaming availability (post full-enrichment)
    user_services = set(answers.get("streaming", []))
    if "rent" not in user_services and user_services:
        flat_ids = {p["id"] for p in movie.get("streaming_flat", [])}
        has_match = False
        for svc in user_services:
            if set(PROVIDER_MAP.get(svc, [])) & flat_ids:
                has_match = True
                break
        if has_match:
            score += 22
        elif movie.get("streaming_flat") is not None and len(movie.get("streaming_flat", [])) == 0:
            if movie.get("streaming_rent") or movie.get("streaming_buy"):
                score += 2  # available to rent
            else:
                score -= 3

    return round(score, 1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEXT GENERATION (Template-based, no AI needed)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_runtime(minutes):
    if not minutes:
        return ""
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if h else f"{m}m"


def get_streaming_text(movie, user_services):
    """Build streaming availability text from TMDB watch provider data."""
    flat = movie.get("streaming_flat", [])
    rent = movie.get("streaming_rent", [])

    # Check user's services first
    on_user = []
    all_svc = set()
    for svc_key in (user_services if isinstance(user_services, list) else []):
        prov_ids = PROVIDER_MAP.get(svc_key, [])
        for p in flat:
            if p["id"] in prov_ids and p["name"] not in all_svc:
                on_user.append(p["name"])
                all_svc.add(p["name"])

    if on_user:
        return f"Streaming on {' · '.join(on_user)}", "available"

    # Not on user's services but streaming somewhere
    other_flat = [p["name"] for p in flat[:3]]
    if other_flat:
        return f"Streaming on {' · '.join(other_flat)} (not on your services)", "rent"

    # Rent only
    rent_names = list(dict.fromkeys([p["name"] for p in rent[:3]]))
    if rent_names:
        return f"Rent on {' · '.join(rent_names)}", "rent"

    return "Check JustWatch for availability", "unavailable"


def generate_pick_reason(movie, answers):
    """Generate a conversational reason this movie was picked."""
    mood_phrases = {
        "laugh": "you wanted to laugh tonight",
        "think": "you wanted something to chew on mentally",
        "feel": "you're looking to feel something deep",
        "intense": "you're chasing that white-knuckle energy",
        "surprise": "you said surprise me",
    }
    genre_names = movie.get("genres_full", []) or [TMDB_GENRES.get(g, "") for g in movie.get("genre_ids", []) if g in TMDB_GENRES]
    genre_str = " / ".join(genre_names[:2]).lower() if genre_names else "film"
    parts = []

    mood = answers.get("my_mood", "surprise")
    parts.append(f"You said {mood_phrases.get(mood, 'you wanted a great film')}, and this {genre_str} delivers.")

    vote = movie.get("vote_average", 0)
    imdb = movie.get("imdb_rating", "N/A")
    if imdb not in ["N/A", ""] and float(imdb) >= 8.0:
        parts.append(f"At {imdb}/10 on IMDb, it's one of the highest-rated films on your watchlist.")
    elif vote >= 7.8:
        parts.append(f"Highly rated at {vote}/10 on TMDB — this one's well-loved.")

    runtime = movie.get("runtime", 0)
    time_pref = answers.get("time", "any")
    if runtime:
        if time_pref == "short" and runtime <= 105:
            parts.append(f"At {format_runtime(runtime)}, it respects your time.")
        elif time_pref == "long" and runtime >= 140:
            parts.append(f"At {format_runtime(runtime)}, it's the epic you wanted.")

    director = movie.get("director", "")
    if director and director != "N/A":
        parts.append(f"Directed by {director}.")

    return " ".join(parts)


def generate_wife_note(movie, answers):
    """Generate wife-watch compatibility note."""
    who = answers.get("who", "solo")
    if who == "solo":
        return "Solo pick — save this one for your alone time."
    if who == "friends":
        return "Guys' night pick."

    genres = set(movie.get("genre_ids", []))
    wife_likes = answers.get("wife_likes", "open")
    wife_avoids = answers.get("wife_avoids", "none")
    genre_names = movie.get("genres_full", [])

    like_map = {"romance_drama": {18, 10749}, "comedy": {35}, "thriller": {53, 9648, 80}, "adventure": {28, 12}}
    avoid_map = {"violent": {28, 10752, 27}, "scary": {27}, "sad": {18}, "weird": set(), "slow": set()}

    hit_avoid = False
    if wife_avoids in avoid_map and avoid_map[wife_avoids] and genres & avoid_map[wife_avoids]:
        hit_avoid = True
    elif wife_avoids == "slow" and not genres & {28, 53, 35}:
        hit_avoid = True

    hit_like = wife_likes == "open" or (wife_likes in like_map and genres & like_map[wife_likes])

    if hit_avoid and not hit_like:
        g = ", ".join(genre_names[:2]) if genre_names else "this genre"
        return f"Heads up — {g.lower()} might hit her dealbreaker. Consider it a solo watch or ask first."
    elif hit_like and not hit_avoid:
        return "Right in her wheelhouse — great couples movie."
    elif hit_like and hit_avoid:
        return "She might like the story but parts could push her limits. Worth a conversation first."
    else:
        return "Not her usual pick, but could work if she's feeling open."


def generate_content_note(movie):
    """Generate IMDB Parents Guide-style content advisory."""
    cert = movie.get("rated", movie.get("certification", "NR")) or "NR"
    if cert in ["Not Rated", "Unrated", ""]:
        cert = "NR"
    genres = set(movie.get("genre_ids", []))
    base = CONTENT_BY_RATING.get(cert, CONTENT_BY_RATING["NR"])

    # Refine by genre
    violence = base["violence"]
    if genres & {10752}:
        violence = "Strong — war film, expect combat and casualties"
    elif genres & {27} and cert in ["R", "NC-17"]:
        violence = "Strong — horror violence, possibly graphic"
    elif genres & {28} and cert == "PG-13":
        violence = "Moderate — action violence, limited blood"

    language = base["language"]

    sexual = base["sexual"]
    if cert in ["G", "PG", "PG-13"]:
        sexual = "None to mild"
    elif cert == "R":
        if genres & {10749}:
            sexual = "⚠️ R-rated romance — check IMDB Parents Guide before watching"
        elif genres & {18} and not genres & {28, 10752, 27}:
            sexual = "⚠️ R-rated drama — check Parents Guide for sexual content"
        else:
            sexual = "Possibly mild/moderate — check Parents Guide to be safe"

    intense = base["intense"]
    if 27 in genres:
        intense = "Strong — horror film, expect scares and tension"
    elif genres & {53, 9648}:
        intense = "Moderate to strong — suspense and tension"

    return {"violence": violence, "language": language, "sexual": sexual, "intense": intense}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUIZ DEFINITION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUIZ = [
    {"id": "who", "label": "WHO'S WATCHING", "q": "Who's on the couch tonight?",
     "options": {"🎧 Just me — solo time": "solo", "💑 Me and my wife": "wife",
                 "👨‍👩‍👧 Family movie night": "family", "🍕 Friends are over": "friends"}},
    {"id": "wife_likes", "label": "WIFE'S TASTE", "q": "What kind of movies does your wife usually enjoy?",
     "options": {"🌹 Romance, drama, emotional stories": "romance_drama", "😂 Comedy — she wants to laugh": "comedy",
                 "🔍 Thriller, suspense, mystery": "thriller", "🗺️ Adventure, action, spectacle": "adventure",
                 "🤙 She's open to anything good": "open"}},
    {"id": "wife_avoids", "label": "WIFE'S DEALBREAKER", "q": "What makes your wife grab her phone?",
     "options": {"😴 Too slow or boring": "slow", "🩸 Too violent or gory": "violent",
                 "😰 Too scary or disturbing": "scary", "😢 Too depressing": "sad",
                 "🎭 Too weird or artsy": "weird", "💪 Nothing — she's a trooper": "none"}},
    {"id": "my_mood", "label": "YOUR MOOD", "q": "What are YOU in the mood for?",
     "options": {"🤣 Make me laugh": "laugh", "🧠 Something that'll stick with me": "think",
                 "💔 Hit me in the feelings": "feel", "⚡ Edge-of-my-seat tension": "intense",
                 "🎲 No idea — surprise me": "surprise"}},
    {"id": "time", "label": "RUNTIME", "q": "How much time before you fall asleep?",
     "options": {"⏱️ Under 100 min — keep it tight": "short", "🕐 About 2 hours": "medium",
                 "🎬 Going epic — 2.5+ hours": "long", "♾️ Doesn't matter if it's good": "any"}},
    {"id": "streaming", "label": "STREAMING", "q": "What streaming services do you have?",
     "multi": True,
     "options": {"🟥 Netflix": "netflix", "📦 Amazon Prime": "prime", "🍎 Apple TV+": "apple",
                 "🟩 Hulu": "hulu", "🟪 Max (HBO)": "max", "🏰 Disney+": "disney",
                 "🦚 Peacock": "peacock", "⛰️ Paramount+": "paramount",
                 "💳 I'll rent — doesn't matter": "rent"}},
    {"id": "decade", "label": "ERA", "q": "Pick your era:",
     "options": {"📽️ Silent & Golden Age (pre-1950)": "pre1950", "🎞️ 1950s – 1960s": "50s60s",
                 "📀 1970s – 1980s": "70s80s", "💿 1990s – 2000s": "90s00s",
                 "✨ 2010s and newer": "2010plus", "🔀 Any era": "any"}},
    {"id": "genre1", "label": "MAIN GENRE", "q": "Pick your lane:",
     "options": {"💥 Action / Adventure": "action", "🎭 Drama / Character study": "drama",
                 "😄 Comedy": "comedy", "🕵️ Thriller / Mystery / Noir": "thriller",
                 "🚀 Sci-Fi / Fantasy": "scifi"}},
    {"id": "genre2", "label": "BONUS GENRE", "q": "Got a second genre itch?",
     "options": {"⚔️ War / History / Epic": "war_history", "👻 Horror / Creepy": "horror",
                 "💕 Romance / Love story": "romance", "📖 Biography / True story": "bio",
                 "🤠 Western": "western", "👍 Nah, first pick is fine": "skip"}},
    {"id": "filmtype", "label": "FILM TYPE", "q": "What kind of movie are you after?",
     "options": {"🏆 Top-shelf — critically acclaimed": "acclaimed", "💎 Hidden gem most people missed": "hidden",
                 "👏 Total crowd-pleaser": "crowd", "🔮 Weird, artsy, or cult": "cult"}},
    {"id": "pacing", "label": "PACING", "q": "How should the story move?",
     "options": {"🕯️ Slow burn — let it build": "slow", "🎵 Steady rhythm": "steady",
                 "🏃 Fast — hit the ground running": "fast", "🤷 No preference": "any"}},
    {"id": "content_tone", "label": "CONTENT VIBE", "q": "Overall content vibe?",
     "options": {"☀️ Happy-go-lucky — fun, upbeat": "light", "📚 Smart & dramatic — mature themes": "dramatic",
                 "🌆 Gritty & intense — crime, conflict": "gritty", "🌑 Dark & haunting — psychological, eerie": "dark"}},
    {"id": "violence", "label": "VIOLENCE", "q": "Violence comfort level?",
     "options": {"🟢 Minimal — slapstick or implied": "mild", "🟡 Moderate — action-movie level": "moderate",
                 "🟠 Strong — war scenes, real fights": "strong", "🔴 Severe — graphic is OK": "severe"}},
    {"id": "scary", "label": "SCARES", "q": "How scary can it get?",
     "options": {"😇 Not at all": "none", "😬 Mild tension and suspense": "mild",
                 "👻 Legitimately creepy": "creepy", "💀 Full horror — nightmares welcome": "horror"}},
    {"id": "language", "label": "PROFANITY", "q": "Profanity?",
     "options": {"🧼 Keep it clean": "clean", "🤷 Some is fine": "some", "🗣️ Doesn't bother me": "any"}},
    {"id": "emotional", "label": "EMOTIONAL WEIGHT", "q": "How heavy can we go?",
     "options": {"🧊 Keep it light": "light", "💭 Some depth — make me care": "moderate",
                 "🥺 Go deep — wreck me": "heavy", "😭 Devastate me, I dare you": "devastate"}},
    {"id": "after", "label": "AFTER FEELING", "q": "How to feel when credits roll?",
     "options": {"😊 Happy and uplifted": "uplifted", "🌙 Thinking about life at 2am": "reflective",
                 "🔥 Buzzing with energy": "energized", "🥹 Deeply moved": "moved",
                 "🎬 Don't care, just make it good": "any"}},
    {"id": "true_story", "label": "TRUE STORY", "q": "True story or fiction?",
     "options": {"📰 True stories hit different": "true", "📝 Pure fiction": "fiction",
                 "🤝 Either — just make it good": "either"}},
    {"id": "bw", "label": "BLACK & WHITE", "q": "Black & white movies?",
     "options": {"🎩 Love 'em — classic cinema": "love", "👍 Sure, if it's great": "open",
                 "🌈 Color only tonight": "color"}},
    {"id": "foreign", "label": "SUBTITLES", "q": "Subtitles OK tonight?",
     "options": {"🌍 Totally fine": "yes", "🇺🇸 English only tonight": "english", "🤷 No preference": "any"}},
    {"id": "wildcard", "label": "WILDCARD", "q": "Last one — dealer's choice:",
     "options": {"🎲 Something I'd NEVER normally pick": "surprise", "🎯 Safe bet I'll love": "safe",
                 "⏳ A film I've been putting off": "overdue", "👑 Just pick the best one": "best"}},
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESULT CARD RENDERER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_movie_card(movie, rank, answers):
    medals = ["🥇", "🥈", "🥉"]
    classes = ["gold", "silver", "bronze"]
    tag_classes = ["green", "orange", "blue"]

    # Streaming info
    user_svc = answers.get("streaming", [])
    stream_text, stream_class = get_streaming_text(movie, user_svc)
    jw_link = movie.get("jw_link", "")

    # Ratings
    imdb = movie.get("imdb_rating", "N/A")
    rt = movie.get("rt_score", "N/A")
    meta = movie.get("metascore", "N/A")
    tmdb_score = movie.get("vote_average", 0)

    # Content
    cert = movie.get("rated", movie.get("certification", "NR")) or "NR"
    runtime = format_runtime(movie.get("runtime", 0))
    genre_names = movie.get("genres_full", []) or [TMDB_GENRES.get(g, "") for g in movie.get("genre_ids", []) if g in TMDB_GENRES]
    poster = f"{TMDB_IMG}/w342{movie['poster_path']}" if movie.get("poster_path") else ""

    # Generated text
    reason = generate_pick_reason(movie, answers)
    content_note = generate_content_note(movie)
    wife_note = generate_wife_note(movie, answers)

    # Links
    imdb_id = movie.get("imdb_id", "")
    uri = movie.get("uri", "")
    imdb_link = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else ""
    parents_link = f"https://www.imdb.com/title/{imdb_id}/parentalguide" if imdb_id else ""
    lb_link = uri if uri.startswith("http") else f"https://letterboxd.com{uri}" if uri else ""

    # Build card HTML
    poster_html = f'<img src="{poster}" style="width:100%;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,0.1);" />' if poster else '<div style="width:100%;aspect-ratio:2/3;background:#F5EFE0;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:2rem;">🎬</div>'

    genres_html = "".join([f'<span class="genre-tag {tag_classes[rank]}">{g}</span>' for g in genre_names[:5]])

    ratings_html = ""
    if imdb not in ["N/A", ""]:
        ratings_html += f'<span class="rating-badge rating-imdb">⭐ {imdb} IMDb</span>'
    if rt not in ["N/A", ""]:
        ratings_html += f'<span class="rating-badge rating-rt">🍅 {rt} RT</span>'
    if meta not in ["N/A", ""]:
        ratings_html += f'<span class="rating-badge rating-meta">📊 {meta} Metascore</span>'
    if tmdb_score:
        ratings_html += f'<span class="rating-badge rating-tmdb">🎬 {tmdb_score}/10 TMDB</span>'

    streaming_html = f'<div class="streaming-badge {stream_class}">📺 {stream_text}</div>'
    if jw_link:
        streaming_html += f' <a href="{jw_link}" target="_blank" style="font-size:0.75rem;color:#9E9890;">JustWatch ↗</a>'

    links_html = '<div class="links-row">'
    if parents_link:
        links_html += f'<a href="{parents_link}" target="_blank">🛡️ IMDB Parents Guide</a>'
    if imdb_link:
        links_html += f'<a href="{imdb_link}" target="_blank">⭐ IMDb</a>'
    if lb_link:
        links_html += f'<a href="{lb_link}" target="_blank">📗 Letterboxd</a>'
    if rt not in ["N/A", ""] and imdb_id:
        links_html += f'<a href="https://www.rottentomatoes.com/search?search={movie["name"]}" target="_blank">🍅 Rotten Tomatoes</a>'
    links_html += '</div>'

    content_html = f"""
    <div class="content-box advisory">
        <div class="section-label">Content Heads-Up ({cert})</div>
        <strong>Violence:</strong> {content_note['violence']}<br>
        <strong>Language:</strong> {content_note['language']}<br>
        <strong>Sexual Content:</strong> {content_note['sexual']}<br>
        <strong>Frightening/Intense:</strong> {content_note['intense']}
    </div>
    """

    wife_html = f"""
    <div class="content-box wife">
        <div class="section-label">Wife-Watch Factor</div>
        {wife_note}
    </div>
    """

    return poster_html, f"""
    <div class="movie-card {classes[rank]}">
        <div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:8px;">
            <span class="medal">{medals[rank]}</span>
            <div>
                <div class="movie-title">{movie['name']} ({movie['year']})</div>
                <div class="movie-meta">{runtime} {'· ' + cert if cert != 'NR' else ''}{' · ' + movie.get('director', '') if movie.get('director') and movie.get('director') != 'N/A' else ''}</div>
            </div>
        </div>
        <div style="margin:8px 0;">{genres_html}</div>
        <div class="rating-row">{ratings_html}</div>
        {streaming_html}
        <div class="pick-reason">{reason}</div>
        {content_html}
        {wife_html}
        {links_html}
    </div>
    """


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SESSION STATE INIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if "movies" not in st.session_state:
    st.session_state.movies = []
if "enriched" not in st.session_state:
    st.session_state.enriched = False
if "results" not in st.session_state:
    st.session_state.results = None
if "show_quiz" not in st.session_state:
    st.session_state.show_quiz = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Header
st.markdown("""
<div class="main-header">
    <h1>🎬🍿 The Lindell Movie Picker</h1>
    <p class="subtitle">Your Letterboxd watchlist, minus the decision paralysis.</p>
    <span class="brand-badge">Powered by TMDB + OMDB + JustWatch</span>
</div>
""", unsafe_allow_html=True)

st.write("")

# ── STEP 1: Upload ──
if not st.session_state.enriched:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 📁 Upload Your Watchlist")
        uploaded = st.file_uploader(
            "Drop your Letterboxd CSV here",
            type=["csv"],
            help="Letterboxd → Settings → Import & Export → Export Your Data → watchlist.csv",
        )

        if uploaded:
            content = uploaded.getvalue().decode("utf-8")
            movies = parse_letterboxd_csv(content)
            if movies:
                st.success(f"**{len(movies)} movies loaded!** Ready to enrich with TMDB data.")
                st.session_state.movies = movies

                if st.button("🚀 Load Movie Data", use_container_width=True, type="primary"):
                    progress = st.progress(0)
                    status = st.empty()
                    enriched = enrich_light(movies, progress, status)
                    st.session_state.movies = enriched
                    st.session_state.enriched = True
                    progress.empty()
                    status.empty()
                    st.rerun()
            else:
                st.error("Couldn't parse that CSV. Is it a Letterboxd watchlist export?")

# ── STEP 2: Quiz + Pick ──
elif st.session_state.results is None:
    movies = st.session_state.movies
    found = sum(1 for m in movies if m.get("tmdb_id"))
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:1rem;">
        <span class="brand-badge">{len(movies)} movies loaded · {found} matched on TMDB</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎯 Answer 21 Quick Questions")
    st.caption("Then hit the big green button at the bottom. The algorithm does the rest — no AI credits used.")
    st.write("")

    answers = {}

    # Group questions into sections of 3
    sections = [
        ("🎬 Who & Context", QUIZ[0:3]),
        ("🎭 Mood & Time", QUIZ[3:6]),
        ("📡 Streaming & Era", QUIZ[6:8]),
        ("🎪 Genre", QUIZ[8:10]),
        ("🎬 Film Type & Pacing", QUIZ[10:12]),
        ("🛡️ Content Controls", QUIZ[12:15]),
        ("💔 Emotional Weight", QUIZ[15:17]),
        ("📐 Format Preferences", QUIZ[17:20]),
        ("🎲 Wildcard", QUIZ[20:21]),
    ]

    for section_name, questions in sections:
        st.markdown(f"#### {section_name}")
        cols = st.columns(min(len(questions), 3))
        for i, q in enumerate(questions):
            with cols[i % len(cols)]:
                if q.get("multi"):
                    selected = st.multiselect(
                        q["q"],
                        options=list(q["options"].keys()),
                        default=["🟩 Hulu"],
                        key=f"quiz_{q['id']}",
                    )
                    answers[q["id"]] = [q["options"][s] for s in selected]
                else:
                    choice = st.radio(
                        q["q"],
                        options=list(q["options"].keys()),
                        key=f"quiz_{q['id']}",
                    )
                    answers[q["id"]] = q["options"][choice]
        st.write("")

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎬 PICK MY MOVIE!", use_container_width=True, type="primary"):
            with st.spinner("Scoring your watchlist and enriching top picks..."):
                # Score all movies with light data
                scored = []
                for m in movies:
                    s = score_movie(m, answers)
                    scored.append((s, m))
                scored.sort(key=lambda x: x[0], reverse=True)

                # Full enrich top 12
                top_candidates = []
                for score_val, movie in scored[:12]:
                    enriched_movie = enrich_full_movie(movie)
                    top_candidates.append((score_val, enriched_movie))
                    time.sleep(0.15)

                # Re-score with full data
                final_scored = []
                for _, movie in top_candidates:
                    new_score = score_movie(movie, answers)
                    final_scored.append((new_score, movie))
                final_scored.sort(key=lambda x: x[0], reverse=True)

                st.session_state.results = {
                    "picks": [m for _, m in final_scored[:3]],
                    "answers": answers,
                    "runner_ups": [m for _, m in final_scored[3:6]],
                }
            st.rerun()

# ── STEP 3: Results ──
else:
    results = st.session_state.results
    picks = results["picks"]
    answers = results["answers"]

    st.markdown("""
    <div style="text-align:center;margin-bottom:1.5rem;">
        <div style="font-size:2.5rem;">🎉</div>
        <span class="brand-badge" style="font-size:0.9rem;">TONIGHT'S PICKS</span>
        <p style="color:#9E9890;margin-top:6px;">From your watchlist — here's what to watch:</p>
    </div>
    """, unsafe_allow_html=True)

    for i, movie in enumerate(picks):
        poster_html, card_html = render_movie_card(movie, i, answers)
        col_poster, col_card = st.columns([1, 3])
        with col_poster:
            st.markdown(poster_html, unsafe_allow_html=True)
        with col_card:
            st.markdown(card_html, unsafe_allow_html=True)

    # Runner-ups
    runner_ups = results.get("runner_ups", [])
    if runner_ups:
        with st.expander("👀 Honorable Mentions"):
            for m in runner_ups:
                genre_names = m.get("genres_full", []) or [TMDB_GENRES.get(g, "") for g in m.get("genre_ids", []) if g in TMDB_GENRES]
                rt = format_runtime(m.get("runtime", 0))
                st.markdown(f"**{m['name']}** ({m['year']}) — {', '.join(genre_names[:3])} {'· ' + rt if rt else ''}")

    st.write("")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔄 Different Mood — Try Again", use_container_width=True):
            st.session_state.results = None
            st.rerun()
    with col2:
        if st.button("📁 Upload New List", use_container_width=True):
            st.session_state.movies = []
            st.session_state.enriched = False
            st.session_state.results = None
            st.rerun()

# Footer
st.markdown("""
<div class="footer">
    The Lindell Movie Picker · Data from TMDB, OMDB & JustWatch · You know that's right ☝️🍍
    <br><small>This product uses the TMDB API but is not endorsed or certified by TMDB.</small>
</div>
""", unsafe_allow_html=True)
