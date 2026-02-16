import requests
import pandas as pd
import os
import streamlit as st

API_KEY = "YOUR_TMDB_API_KEY" # Get one at themoviedb.org
BASE_URL = "https://api.themoviedb.org/3"
DB_FILE = "data/votes.csv"

def init_db():
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=['session_id', 'user_name', 'movie_id', 'title', 'vote'])
        df.to_csv(DB_FILE, index=False)

def fetch_trending_movies(page=1):
    url = f"{BASE_URL}/trending/movie/week?api_key={API_KEY}&page={page}"
    try:
        response = requests.get(url).json()
        return response.get('results', [])
    except:
        return []

def record_vote(session_id, user_name, movie_id, title, vote):
    df = pd.read_csv(DB_FILE)
    new_vote = pd.DataFrame([[session_id, user_name, movie_id, title, vote]], 
                            columns=['session_id', 'user_name', 'movie_id', 'title', 'vote'])
    df = pd.concat([df, new_vote], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

def get_matches(session_id):
    df = pd.read_csv(DB_FILE)
    session_df = df[(df['session_id'] == session_id) & (df['vote'] == 'Like')]
    # Group by movie_id and count unique users who liked it
    match_counts = session_df.groupby(['movie_id', 'title']).user_name.nunique()
    matches = match_counts[match_counts > 1].index.get_level_values('title').tolist()
    return matches
