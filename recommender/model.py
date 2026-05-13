"""Minimal recommender logic for the Recco POC.

This module intentionally contains a trivial recommendation function so
the Streamlit UI can demonstrate integration with the backend.
"""
import warnings
import logging
import os
import json
import re

# Suppress warnings globally
warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)

from typing import List, Dict
import numpy as np
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .data import get_sample_movies, get_movies_blurb
from .util import get_api_key

# Configure Gemini API key
genai.configure(api_key=get_api_key("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.5-flash")
encoder = SentenceTransformer("all-MiniLM-L6-v2")

# sanity check that we can connect to Gemini and list models
def get_models():
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(m.name)

def recommend_sample(user: str, n: int = 10) -> List[Dict]:
    """Return the top-n sample movies.

    Args:
        user: username (not used in POC)
        n: number of recommendations

    Returns:
        List of movie dicts with `title` and `year`.
    """
    movies = get_sample_movies()
    return movies[: max(1, min(n, len(movies)))]


def movie_to_text(movie: dict) -> str:
    genres = " ".join(g["name"] for g in movie.get("genres", []))
    overview = movie.get("overview", "")
    title = movie.get("title", "")
    return f"{title}. {overview} Genres: {genres}"

def process_blurb(blurb: str) -> dict:
    """Use Gemini to extract search terms + expand blurb for better embedding."""
    prompt = f"""A user wants to watch a movie and described it as: "{blurb}"

    Return a JSON object with exactly these two fields:
    - "search_terms": a list of 3 short TMDB-friendly search queries (1-3 words each)
    - "expanded": a 2-3 sentence description covering tone, themes, pacing, and emotional feel

    Only return the raw JSON object. no markdown, no backticks, nothing else."""

    response = gemini.generate_content(prompt)

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"search_terms": [blurb], "expanded": blurb}


def recommend_from_blurb(blurb: str, n: int = 5) -> list[dict]:
    # get expanded processed blurb with search terms
    processed = process_blurb(blurb)
    print(f"Search terms: {processed['search_terms']}")
    print(f"Expanded: {processed['expanded']}")

    # cast a wider net using all search terms
    candidates = []
    for term in processed["search_terms"]:
        candidates += get_movies_blurb(term)

    # deduplicate by movie id - some movies may match multiple search terms
    seen = set()
    unique = []
    for m in candidates:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)

    if not unique:
        return []

    # embed expanded blurb + rank candidates
    expanded_vector = encoder.encode([processed["expanded"]])
    candidate_texts = [movie_to_text(m) for m in unique]
    candidate_vectors = encoder.encode(candidate_texts)

    # compute cosine similarity and rank
    scores = cosine_similarity(expanded_vector, candidate_vectors)[0]
    ranked = sorted(zip(scores, unique), reverse=True)

    print(f"Ranking {len(unique)} unique candidates")
    for score, movie in ranked[:n]:
        print(f"  {score:.4f} - {movie['title']}")

    return [movie for _, movie in ranked[:n]]