"""Simple data utilities for the Recco POC."""

from turtle import st

from dotenv import load_dotenv
import os
import requests
from .util import get_api_key


API_KEY = get_api_key("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

GENRE_IDS = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
    "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751,
    "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
    "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
    "Thriller": 53, "War": 10752, "Western": 37
}

# Streamlit Cloud - switch to this during deployment, and ensure the API key is set in the Streamlit secrets:
# API_KEY = st.secrets["TMDB_API_KEY"]

def get_movie(movie_id: int) -> dict:
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY, "language": "en-US"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def search_movies(query: str) -> list[dict]:
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": query}
    return requests.get(url, params=params).json().get("results", [])

def get_similar(movie_id: int) -> list[dict]:
    url = f"{BASE_URL}/movie/{movie_id}/similar"
    params = {"api_key": API_KEY}
    return requests.get(url, params=params).json().get("results", [])

def get_sample_movies():
    """Return a small, hard-coded list of movies for the POC."""
    sample_movies = []
    for movie in get_sample_movies_from_tmdb():
        sample_movies.append({"title": movie["title"], "year": movie["release_date"][:4]}) 
    return sample_movies

def get_sample_movies_from_tmdb():
    """Fetch a small list of popular movies from TMDB for the POC."""
    url = f"{BASE_URL}/movie/popular"
    params = {"api_key": API_KEY, "language": "en-US", "page": 1}
    response = requests.get(url, params=params)
    return response.json().get("results", []) # using get() is cleaner and avoids KeyError if "results" is missing

def enrich_movie(movie_id: int) -> dict:
    """Fetch full movie details by ID."""
    return requests.get(
        f"{BASE_URL}/movie/{movie_id}",
        params={"api_key": API_KEY}
    ).json()

def discover_movies(genre_names: list[str], page: int = 1) -> list[dict]:
    """Use TMDB discover endpoint — filters by genre, popularity, rating."""
    genre_ids = [str(GENRE_IDS[g]) for g in genre_names if g in GENRE_IDS]
    if not genre_ids:
        return []

    url = f"{BASE_URL}/discover/movie"
    params = {
        "api_key": API_KEY,
        "with_genres": ",".join(genre_ids),
        "sort_by": "popularity.desc",
        "vote_count.gte": 500,
        "vote_average.gte": 6.5,
        "language": "en-US",
        "page": page
    }
    results = requests.get(url, params=params).json().get("results", [])

    enriched = []
    for r in results[:20]:
        enriched.append(enrich_movie(r["id"]))
    return enriched

def filter_candidates(movies: list[dict]) -> list[dict]:
    """Filter out obscure and low quality movies."""
    return [
        m for m in movies
        if m.get("vote_count", 0) >= 500
        and m.get("vote_average", 0) >= 6.5
        and m.get("popularity", 0) >= 10
    ]


# def get_movies_blurb(query: str) -> list[dict]:
#     """Fetch candidate movies from TMDB using keyword search."""
#     url = f"{BASE_URL}/search/movie"
#     params = {"api_key": API_KEY, "query": query, "page": 1}
#     results = requests.get(url, params=params).json().get("results", [])
    
#     # enrich with full details so we get genres
#     enriched = []
#     for r in results[:20]:  # limit to avoid too many API calls
#         detail = requests.get(
#             f"{BASE_URL}/movie/{r['id']}",
#             params={"api_key": API_KEY}
#         ).json()
#         enriched.append(detail)
    
#     return enriched
