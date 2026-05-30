import re
from recommender.db import (
    create_profile,
    get_profile,
    delete_profile,
    add_rating,
    get_ratings,
    get_usernames,
    update_genres_db
)

USERNAME_REGEX = r"^[a-zA-Z0-9_]+$"

def is_valid_username(username: str) -> bool:
    """Check if the username is unique."""
    if username not in set(get_usernames()) and re.match(USERNAME_REGEX, username) and len(username) >= 3:
        return True
    return False


def get_sample_profile():
    """Return a sample user profile with a blurb and liked movies."""
    profile = {
        "username": "cinephile_007",
        "liked_movies": ["The Godfather","GoodFellas", "The Devil Wears Prada", "Meet The Parents"],
        "disliked_movies": ["2001: A Space Odyssey", "The Tree of Life"],
        "liked_genres": ["crime", "comedy"],
        "disliked_genres": ["science fiction"],
    }
    return profile

def register_profile(username: str, liked_genres: list = [], disliked_genres: list = []) -> dict:
    """Create a new profile. Raises ValueError if username is taken or invalid."""
    if not is_valid_username(username):
        raise ValueError("Username must be at least 3 characters, alphanumeric and underscores only.")
    return create_profile(username, liked_genres, disliked_genres)

def load_profile(username: str) -> dict | None:
    """Load a profile by username. Returns None if not found."""
    return get_profile(username)

def rate_movie(username: str, tmdb_id: int, title: str, rating: float) -> dict:
    """Rate a movie and derive sentiment from the rating automatically."""
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5.")
    sentiment = "liked" if rating >= 4 else "disliked" if rating <= 2 else "neutral"
    return add_rating(username, tmdb_id, title, rating, sentiment)

def get_liked_movies(username: str) -> list[dict]:
    """Return movies the user liked (rating >= 4)."""
    return [r for r in get_ratings(username) if r["sentiment"] == "liked"]

def get_disliked_movies(username: str) -> list[dict]:
    """Return movies the user disliked (rating <= 2)."""
    return [r for r in get_ratings(username) if r["sentiment"] == "disliked"]

def get_full_profile(username: str) -> dict | None:
    """Return profile info + full ratings list combined."""
    profile = get_profile(username)
    if not profile:
        return None
    profile["ratings"] = get_ratings(username)
    profile["liked_movies"] = [r["title"] for r in profile["ratings"] if r["sentiment"] == "liked"]
    profile["disliked_movies"] = [r["title"] for r in profile["ratings"] if r["sentiment"] == "disliked"]
    return profile

def update_genres(username: str, liked_genres: list, disliked_genres: list) -> None:
    """Update the liked and disliked genres for a user."""
    profile = get_profile(username)
    if profile:
        update_genres_db(username, liked_genres, disliked_genres)

def remove_profile(username: str) -> bool:
    """Delete a profile and all its ratings."""
    return delete_profile(username)




