import streamlit as st
import movie_logic as ml

st.set_page_config(page_title="Movie Matcher", layout="centered")
ml.init_db()

# --- STEP 1: JOIN SESSION ---
if 'user_name' not in st.session_state:
    st.title("🍿 Movie Match Maker")
    with st.form("join_form"):
        user = st.text_input("Your Name")
        room = st.text_input("Room ID (Share this with your friend)", value="MovieNight123")
        submit = st.form_submit_button("Start Matching")
        if submit and user and room:
            st.session_state.user_name = user
            st.session_state.room_id = room
            st.session_state.movie_idx = 0
            st.session_state.movies = ml.fetch_trending_movies()
            st.rerun()
    st.stop()

# --- STEP 2: THE MATCHING UI ---
st.title(f"Room: {st.session_state.room_id}")
st.write(f"Logged in as: **{st.session_state.user_name}**")

# Sidebar for matches
matches = ml.get_matches(st.session_state.room_id)
with st.sidebar:
    st.header("✨ It's a Match!")
    if matches:
        for m in matches:
            st.success(f"🔥 {m}")
    else:
        st.info("No mutual matches yet. Keep swiping!")

# Main Card Logic
if st.session_state.movie_idx < len(st.session_state.movies):
    movie = st.session_state.movies[st.session_state.movie_idx]
    
    # Movie Card Container
    with st.container(border=True):
        col1, col2 = st.columns([1, 1.5])
        with col1:
            poster_path = movie.get('poster_path')
            url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            st.image(url)
        
        with col2:
            st.subheader(movie['title'])
            st.write(movie['overview'][:250] + "...")
            st.write(f"⭐ {movie['vote_average']}")
            
            c1, c2 = st.columns(2)
            if c1.button("👎 Dislike", use_container_width=True):
                ml.record_vote(st.session_state.room_id, st.session_state.user_name, movie['id'], movie['title'], 'Dislike')
                st.session_state.movie_idx += 1
                st.rerun()
            
            if c2.button("👍 Like", type="primary", use_container_width=True):
                ml.record_vote(st.session_state.room_id, st.session_state.user_name, movie['id'], movie['title'], 'Like')
                st.session_state.movie_idx += 1
                st.rerun()
else:
    st.balloons()
    st.write("You've seen all the movies for today!")
    if st.button("Load More"):
        st.session_state.movie_idx = 0
        st.rerun()
