import streamlit as st
import requests
import time
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="Lindell Movie Picker",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# API keys
TMDB_KEY = st.secrets.get("TMDB_API_KEY", "a20688a723e8c7dd1bef2c2cf21ea3eb")
OMDB_KEY = st.secrets.get("OMDB_API_KEY", "5d2291bb")
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS & PROVIDERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
}

# Map quiz genre answers → TMDB genre IDs
GENRE_MAP = {
    "Action": [28, 12], "Adventure": [12, 28], "Animation": [16],
    "Comedy": [35], "Crime": [80], "Documentary": [99],
    "Drama": [18], "Family": [10751], "Fantasy": [14],
    "History": [36], "Horror": [27], "Music": [10402],
    "Mystery": [9648], "Romance": [10749], "Sci-Fi": [878],
    "Thriller": [53], "War": [10752], "Western": [37],
}

# Streaming provider IDs (TMDB uses JustWatch data)
PROVIDER_MAP = {
    "Netflix": [8], "Prime Video": [9, 119], "Apple TV+": [2, 350],
    "Hulu": [15], "Max": [384, 1899], "Disney+": [337],
    "Peacock": [386, 387], "Paramount+": [531],
    "Kanopy": [191], "Watch TCM": [361],
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
p, li, span, div, label { font-family: 'Nunito', sans-serif !important; }

/* Header */
.main-header { text-align: center; padding: 1rem 0 0.5rem; }
.main-header h1 { font-size: 2.5rem; color: #2D2A26; margin: 0; }
.brand-badge {
    display: inline-block; padding: 4px 16px; margin-top: 8px;
    background: #E8F5E9; border-radius: 99px;
    color: #3BA55D; font-weight: 700; font-size: 0.8rem;
    letter-spacing: 1.5px; text-transform: uppercase;
}

/* Movie cards */
.movie-card {
    background: #FFFFFF; border-radius: 18px; padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06); margin-bottom: 12px;
    border: 2px solid transparent;
}
.movie-card.gold { border-color: #3BA55D; box-shadow: 0 6px 30px rgba(59,165,93,0.12); }
.movie-card.silver { border-color: #F4A236; }
.movie-card.bronze { border-color: #4A90D9; }

.movie-title { font-size: 1.4rem; font-weight: 700; color: #2D2A26; line-height: 1.3; }
.movie-meta { color: #9E9890; font-size: 0.85rem; margin-top: 4px; }

.genre-tag {
    display: inline-block; padding: 3px 12px; margin: 2px 4px 2px 0;
    border-radius: 99px; font-size: 0.75rem; font-weight: 700; background: #E8F5E9; color: #3BA55D;
}

.rating-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; margin-right: 8px;
}
.rating-imdb { background: #FFF8E1; color: #F5C518; }
.rating-rt { background: #FFF0F0; color: #FA320A; }

/* Buttons */
.stButton > button {
    font-family: 'Fredoka', sans-serif !important;
    border-radius: 99px !important;
    font-weight: 600 !important;
    padding: 0.6rem 2rem !important;
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_data(ttl=86400, show_spinner=False)
def tmdb_search(title, year=None):
    try:
        params = {"api_key": TMDB_KEY, "query": title}
        if year: params["year"] = year
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
                    "title": m.get("title", title),
                    "year": int(m.get("release_date", "0000")[:4]) if m.get("release_date") else 0
                }
        return None
    except Exception:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def tmdb_get_recommendations(tmdb_id):
    try:
        params = {"api_key": TMDB_KEY, "language": "en-US", "page": 1}
        r = requests.get(f"{TMDB_BASE}/movie/{tmdb_id}/recommendations", params=params, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
            movies = []
            for m in results[:20]:
                movies.append({
                    "name": m["title"],
                    "year": int(m["release_date"][:4]) if m.get("release_date") else 0,
                    "tmdb_id": m["id"],
                    "genre_ids": m.get("genre_ids", []),
                    "overview": m.get("overview", ""),
                    "poster_path": m.get("poster_path", ""),
                    "vote_average": m.get("vote_average", 0),
                    "popularity": m.get("popularity", 0),
                    "original_language": m.get("original_language", "en"),
                    "date_added": datetime.today().strftime('%Y-%m-%d')
                })
            return movies
        return []
    except Exception:
        return []

@st.cache_data(ttl=86400, show_spinner=False)
def tmdb_full(tmdb_id):
    try:
        params = {"api_key": TMDB_KEY, "append_to_response": "watch/providers,release_dates"}
        r = requests.get(f"{TMDB_BASE}/movie/{tmdb_id}", params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            cert = "NR"
            for country in data.get("release_dates", {}).get("results", []):
                if country.get("iso_3166_1") == "US":
                    for rd in country.get("release_dates", []):
                        if rd.get("certification"):
                            cert = rd["certification"]
                            break
                    break
            
            us_providers = data.get("watch/providers", {}).get("results", {}).get("US", {})
            flatrate = us_providers.get("flatrate", [])
            
            return {
                "runtime": data.get("runtime", 0),
                "certification": cert,
                "imdb_id": data.get("imdb_id", ""),
                "flatrate_providers": [{"id": p["provider_id"], "name": p["provider_name"]} for p in flatrate],
                "jw_link": us_providers.get("link", ""),
                "genres_full": [g["name"] for g in data.get("genres", [])],
                "director": "",
            }
        return None
    except Exception:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def omdb_lookup(title, year):
    try:
        params = {"t": title, "y": year, "apikey": OMDB_KEY}
        r = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("Response") == "True":
                return {
                    "imdb_rating": data.get("imdbRating", "N/A"),
                    "rt_score": next((r["Value"] for r in data.get("Ratings", []) if "Rotten Tomatoes" in r["Source"]), "N/A"),
                    "director": data.get("Director", ""),
                    "rated": data.get("Rated", "NR"),
                    "imdb_id": data.get("imdbID", "")
                }
        return None
    except Exception:
        return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_letterboxd_csv(file_content):
    text = file_content
    if text[0] == '\ufeff': text = text[1:]
    lines = text.strip().split('\n')
    movies = []
    import csv
    reader = csv.reader(lines)
    try:
        next(reader) 
        for row in reader:
            if len(row) >= 2:
                name = row[1]
                year = int(row[2]) if row[2].isdigit() else 0
                uri = row[3] if len(row) > 3 else ""
                movies.append({"name": name, "year": year, "uri": uri, "date_added": row[0]})
    except:
        pass
    return movies

def enrich_light(movies, progress_bar, status_text):
    enriched = []
    total = len(movies)
    for i, m in enumerate(movies):
        if "tmdb_id" in m and m["tmdb_id"]:
            enriched.append(m)
        else:
            result = tmdb_search(m["name"], m["year"])
            movie = {**m}
            if result: movie.update(result)
            enriched.append(movie)
        
        if i % 5 == 0:
            progress_bar.progress((i + 1) / total)
            status_text.text(f"Scanning... {i+1}/{total} — {m['name']}")
    return enriched

def enrich_full_movie(movie):
    data = {"streaming_flat": [], "runtime": 0, "certification": "NR", 
            "imdb_rating": "N/A", "rt_score": "N/A", "director": "", "genres_full": []}
    
    if movie.get("tmdb_id"):
        full = tmdb_full(movie["tmdb_id"])
        if full:
            data.update({
                "runtime": full.get("runtime", 0),
                "certification": full.get("certification", "NR"),
                "streaming_flat": full.get("flatrate_providers", []),
                "jw_link": full.get("jw_link", ""),
                "imdb_id": full.get("imdb_id", ""),
                "genres_full": full.get("genres_full", [])
            })
    
    omdb = omdb_lookup(movie["name"], movie["year"])
    if omdb:
        data.update({
            "imdb_rating": omdb.get("imdb_rating", "N/A"),
            "rt_score": omdb.get("rt_score", "N/A"),
            "director": omdb.get("director", ""),
            "rated": omdb.get("rated", "NR")
        })
        if not data["imdb_id"]: data["imdb_id"] = omdb.get("imdb_id", "")
    
    movie.update(data)
    return movie

def score_movie(movie, answers):
    score = 0.0
    genres = set(movie.get("genre_ids", []))
    year = movie.get("year", 2000)
    vote = movie.get("vote_average", 0)
    
    # 1. GENRES
    user_genres = answers.get("genres", [])
    if user_genres:
        matches = 0
        for g_name in user_genres:
            g_ids = GENRE_MAP.get(g_name, [])
            if set(g_ids) & genres:
                matches += 1
        if matches > 0: score += 30 + (matches * 5)
    
    # 2. MOOD
    moods = answers.get("mood", [])
    if "Laugh" in moods and 35 in genres: score += 15
    if "Think/Drama" in moods and genres & {18, 99, 36}: score += 15
    if "Adrenaline" in moods and genres & {28, 53, 27}: score += 15
    if "Feel/Cry" in moods and genres & {18, 10749}: score += 15
    
    # 3. ERAS
    eras = answers.get("eras", [])
    if eras:
        movie_decade = (year // 10) * 10
        decade_str = f"{movie_decade}s"
        if decade_str in eras:
            score += 25
        elif "Pre-1950s" in eras and year < 1950:
            score += 25

    # 4. STREAMING
    user_providers = answers.get("providers", [])
    movie_providers = {p["id"] for p in movie.get("streaming_flat", [])}
    
    provider_match = False
    if user_providers:
        for p_name in user_providers:
            p_ids = PROVIDER_MAP.get(p_name, [])
            if set(p_ids) & movie_providers:
                provider_match = True
                break
        
        if provider_match:
            score += 40
        elif "Rent/Buy" not in user_providers:
            score -= 10
            
    score += (vote * 2)
    who = answers.get("who", "Solo")
    if who == "Wife/Partner":
        if genres & {27}: score -= 20 
        
    return score

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DISPLAY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_runtime(minutes):
    if not minutes: return ""
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m"

def render_movie_card_html(movie, rank, answers):
    # Prepare Data
    medals = ["🥇", "🥈", "🥉"]
    classes = ["gold", "silver", "bronze"]
    
    title = movie.get("name")
    year = movie.get("year")
    poster = f"{TMDB_IMG}/w342{movie['poster_path']}" if movie.get("poster_path") else ""
    runtime = format_runtime(movie.get("runtime", 0))
    rating = movie.get("certification", "NR") or "NR"
    director = movie.get("director", "")
    
    # Genres
    g_list = movie.get("genres_full", [])[:3]
    genre_html = "".join([f'<span class="genre-tag">{g}</span>' for g in g_list])

    # Ratings
    imdb = movie.get("imdb_rating", "N/A")
    rt = movie.get("rt_score", "N/A")
    ratings_html = ""
    if imdb != "N/A": ratings_html += f'<span class="rating-badge rating-imdb">⭐ {imdb}</span>'
    if rt != "N/A": ratings_html += f'<span class="rating-badge rating-rt">🍅 {rt}</span>'

    # Wife Note
    wife_note = ""
    if answers.get("who") == "Wife/Partner":
        wife_note = f"""
        <div style="background:#FFF8F0; padding:10px; border-radius:8px; margin-top:10px; border-left:3px solid #F4A236; font-size:0.85rem; color:#6B6560;">
            <strong>Couple's Note:</strong> {'Good pick.' if movie.get('vote_average',0) > 7 else 'Might be risky.'}
        </div>
        """

    # Card HTML - NO LINKS HERE to avoid "raw code" errors
    card_html = f"""
    <div class="movie-card {classes[rank] if rank < 3 else ''}">
        <div style="display:flex; gap:10px; margin-bottom:10px;">
            <div style="font-size:2rem;">{medals[rank]}</div>
            <div>
                <div class="movie-title">{title} ({year})</div>
                <div class="movie-meta">{runtime} · {rating} · {director}</div>
            </div>
        </div>
        <div style="margin-bottom:10px;">{genre_html}</div>
        <div style="margin-bottom:10px;">{ratings_html}</div>
        <div style="font-size:0.95rem; color:#444; line-height:1.5;">{movie.get('overview', '')[:250]}...</div>
        {wife_note}
    </div>
    """
    
    poster_html = f'<img src="{poster}" style="width:100%; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1);">' if poster else ""
    
    return poster_html, card_html

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if "movies" not in st.session_state: st.session_state.movies = []
if "enriched" not in st.session_state: st.session_state.enriched = False
if "results" not in st.session_state: st.session_state.results = None

# Header
st.markdown("""
<div class="main-header">
    <h1>🎬🍿 Lindell Movie Picker</h1>
    <span class="brand-badge">Updated with Kanopy & TCM</span>
</div>
""", unsafe_allow_html=True)

# ── STEP 1: SOURCE ──
if not st.session_state.enriched:
    st.markdown("### 1️⃣ Get Your Movies")
    source = st.radio("Choose source:", ["📁 Upload Letterboxd CSV", "🔍 Search for a Seed Movie"], horizontal=True)
    
    if source == "📁 Upload Letterboxd CSV":
        uploaded = st.file_uploader("Upload watchlist.csv", type=["csv"])
        if uploaded:
            movies = parse_letterboxd_csv(uploaded.getvalue().decode("utf-8"))
            if st.button(f"Load {len(movies)} Movies"):
                progress = st.progress(0)
                status = st.empty()
                st.session_state.movies = enrich_light(movies, progress, status)
                st.session_state.enriched = True
                st.rerun()

    else:
        seed_query = st.text_input("Enter a movie you love (e.g., 'Inception'):")
        if seed_query and st.button("Generate Recommendations"):
            with st.spinner("Searching TMDB..."):
                seed_result = tmdb_search(seed_query)
                if seed_result:
                    st.info(f"Found: **{seed_result['title']}** ({seed_result['year']}). Finding similar movies...")
                    recs = tmdb_get_recommendations(seed_result['tmdb_id'])
                    if recs:
                        st.session_state.movies = recs 
                        st.session_state.enriched = True
                        st.rerun()
                    else:
                        st.error("No recommendations found.")
                else:
                    st.error("Movie not found.")

# ── STEP 2: QUIZ ──
elif st.session_state.results is None:
    st.markdown("### 2️⃣ Filter & Rank")
    
    with st.form("quiz_form"):
        c1, c2 = st.columns(2)
        with c1:
            q_who = st.radio("Who is watching?", ["Solo", "Wife/Partner", "Family", "Friends"])
            q_genres = st.multiselect("Genres (All that apply):", list(GENRE_MAP.keys()))
            q_mood = st.multiselect("Mood (All that apply):", ["Laugh", "Think/Drama", "Adrenaline", "Feel/Cry", "Surprise Me"])
        
        with c2:
            q_eras = st.multiselect("Decades (All that apply):", 
                                    ["Pre-1950s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"])
            q_providers = st.multiselect("Streaming Services (All that apply):", list(PROVIDER_MAP.keys()))

        submitted = st.form_submit_button("🎬 Find Best Matches", type="primary", use_container_width=True)
        
        if submitted:
            answers = {"who": q_who, "genres": q_genres, "mood": q_mood, "eras": q_eras, "providers": q_providers}
            
            with st.spinner("Analyzing..."):
                scored = []
                for m in st.session_state.movies:
                    s = score_movie(m, answers)
                    scored.append((s, m))
                scored.sort(key=lambda x: x[0], reverse=True)
                
                final_picks = []
                for score, m in scored[:5]:
                    final_picks.append(enrich_full_movie(m))
                    time.sleep(0.1)
                
                st.session_state.results = {
                    "picks": final_picks[:3],
                    "runner_ups": [m for _, m in scored[3:8]],
                    "answers": answers
                }
            st.rerun()

# ── STEP 3: RESULTS ──
else:
    results = st.session_state.results
    
    if st.button("⬅ Start Over"):
        st.session_state.results = None
        st.session_state.enriched = False
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    for i, movie in enumerate(results["picks"]):
        poster_html, card_html = render_movie_card_html(movie, i, results["answers"])
        c1, c2 = st.columns([1, 3])
        with c1: 
            st.markdown(poster_html, unsafe_allow_html=True)
        with c2: 
            st.markdown(card_html, unsafe_allow_html=True)
            # Render Links here as Markdown to avoid Raw HTML issues
            imdb_id = movie.get("imdb_id", "")
            jw_link = movie.get("jw_link", "")
            links = []
            if imdb_id:
                links.append(f"[⭐ IMDb](https://www.imdb.com/title/{imdb_id}/)")
                links.append(f"[🛡️ Parents Guide](https://www.imdb.com/title/{imdb_id}/parentalguide)")
            if jw_link:
                links.append(f"[📺 Watch on JustWatch]({jw_link})")
            
            st.markdown(" **·** ".join(links))
        
        st.markdown("---")

    # Honorable Mentions - Simple List (No HTML Box)
    if results.get("runner_ups"):
        st.markdown("### 👀 Honorable Mentions")
        for m in results["runner_ups"]:
            st.markdown(f"**{m['name']}** ({m['year']})")
