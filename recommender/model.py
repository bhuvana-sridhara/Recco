"""Minimal recommender logic for the Recco POC.

This module intentionally contains a trivial recommendation function so
the Streamlit UI can demonstrate integration with the backend.
"""
from turtle import st
import warnings
import logging
import json
import re

# Suppress warnings globally
warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)

from typing import List, Dict
import numpy as np
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .data import get_sample_movies, get_movies_blurb
from .util import get_api_key
from .profiles import get_sample_profile

# Configure Gemini API key
genai.configure(api_key=get_api_key("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.5-flash")
encoder = SentenceTransformer("all-MiniLM-L6-v2")

class QuotaExceededError(Exception):
    """Custom exception for when Gemini API quota is exceeded."""
    pass

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

def get_profile_details_prompt():
    sample_profile = get_sample_profile()
    return f"""
    - Liked movies: {', '.join(sample_profile['liked_movies'])}
    - Disliked movies: {', '.join(sample_profile['disliked_movies'])}
    """

def process_blurb(blurb: str) -> dict:
    """Use Gemini to extract search terms + expand blurb for better embedding."""
    prompt = f"""A user wants to watch a movie and described it as: "{blurb}"

    Here are some of the user's preferences:
    {get_profile_details_prompt()}

    Return a JSON object with exactly these two fields:
    - "search_terms": a list of 3 short TMDB-friendly search queries (1-3 words each)
    - "expanded": a 2-3 sentence description covering tone, themes, pacing, and emotional feel

    Only return the raw JSON object. no markdown, no backticks, nothing else."""

    try:
        response = gemini.generate_content(prompt)
    except ResourceExhausted:
        # fall back to returning the raw blurb as-is
        raise QuotaExceededError()

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"search_terms": [blurb], "expanded": blurb}
    
def get_candidate_summaries(candidates: List[dict], blurb: str, n: int):    
    # build candidate list for Gemini to reason over
    candidate_summaries = [
        f"{i}. {m['title']} ({m.get('release_date', '')[:4]}): {m.get('overview', '')}"
        for i, m in enumerate(candidates)
    ]

    prompt = f"""A user wants to watch a movie and described it as: "{blurb}"
    From the following list, pick the top {n} that best match. For each, return the index number and a one-sentence reason why it fits.
    {chr(10).join(candidate_summaries)}

    Return only a JSON array like this, nothing else:
    [{{"index": 0, "reason": "..."}}, ...]"""

    response = gemini.generate_content(prompt)
    return response

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
    
    try:
        # build candidate list for Gemini to reason over
        response = get_candidate_summaries(unique, blurb, n)
        raw = re.sub(r"```json|```", "", response.text).strip()
        ranked = json.loads(raw)
    except ResourceExhausted:
        raise QuotaExceededError()
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            ranked = json.loads(match.group())
        else:
            print("Gemini ranking failed, falling back to cosine similarity")
            expanded_vector = encoder.encode([processed["expanded"]])
            candidate_texts = [movie_to_text(m) for m in unique]
            candidate_vectors = encoder.encode(candidate_texts)
            scores = cosine_similarity(expanded_vector, candidate_vectors)[0]
            ranked_fallback = sorted(zip(scores, unique), reverse=True)
            return [movie for _, movie in ranked_fallback[:n]]

    results = []
    for item in ranked[:n]:
        idx = item.get("index")
        if idx is not None and idx < len(unique):
            movie = unique[idx]
            movie["reason"] = item.get("reason", "")
            results.append(movie)
    
    print("Gemini ranked results:")
    for m in results:
        print(m['title'])

    return results