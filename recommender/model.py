"""Minimal recommender logic for the Recco POC.

This module intentionally contains a trivial recommendation function so
the Streamlit UI can demonstrate integration with the backend.
"""

from typing import List, Dict
from .data import get_sample_movies


def recommend(user: str, n: int = 5) -> List[Dict]:
    """Return the top-n sample movies.

    Args:
        user: username (not used in POC)
        n: number of recommendations

    Returns:
        List of movie dicts with `title` and `year`.
    """
    movies = get_sample_movies()
    return movies[: max(1, min(n, len(movies)))]
