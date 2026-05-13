"""Simple data utilities for the Recco POC."""

from turtle import st

from dotenv import load_dotenv
import os
import requests
from .util import get_api_key


API_KEY = get_api_key("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

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

# def get_sample_movies_():
#     """Return a small, hard-coded list of movies for the POC."""
#     return [
#         {"title": "The Shawshank Redemption", "year": 1994},
#         {"title": "The Godfather", "year": 1972},
#         {"title": "The Dark Knight", "year": 2008},
#         {"title": "Pulp Fiction", "year": 1994},
#         {"title": "Forrest Gump", "year": 1994},
#         {"title": "Inception", "year": 2010},
#         {"title": "The Matrix", "year": 1999},
#         {"title": "Interstellar", "year": 2014},
#         {"title": "Parasite", "year": 2019},
#         {"title": "Spirited Away", "year": 2001},
#     ]

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




def get_movies_blurb(query: str) -> list[dict]:
    """Fetch candidate movies from TMDB using keyword search."""
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": query, "page": 1}
    results = requests.get(url, params=params).json().get("results", [])
    
    # enrich with full details so we get genres
    enriched = []
    for r in results[:10]:  # limit to avoid too many API calls
        detail = requests.get(
            f"{BASE_URL}/movie/{r['id']}",
            params={"api_key": API_KEY}
        ).json()
        enriched.append(detail)
    
    return enriched
    
    # embed each candidate's text
    # candidate_texts = [movie_to_text(m) for m in enriched]
    # return candidate_texts