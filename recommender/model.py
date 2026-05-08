"""Minimal recommender logic for the Recco POC.

This module intentionally contains a trivial recommendation function so
the Streamlit UI can demonstrate integration with the backend.
"""

from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .data import get_sample_movies, get_movies_blurb

model = SentenceTransformer("all-MiniLM-L6-v2")

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

def recommend_from_blurb(blurb: str, n: int = 5) -> list[dict]:
    # embed the user's blurb
    blurb_vector = model.encode([blurb])

    # fetch candidates from TMDB
    candidates = get_movies_blurb(blurb)
    if not candidates:
        return []

    # embed each candidate's text
    # candidate_texts = [movie_to_text(m) for m in candidates]
    candidate_vectors = model.encode(candidates)

    # rank by cosine similarity
    scores = cosine_similarity(blurb_vector, candidate_vectors)[0]
    ranked = sorted(zip(scores, candidates), reverse=True)

    return [movie for _, movie in ranked[:n]]