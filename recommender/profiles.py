import re

profiles = {}

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

def save_sample_profile():
    """Save the sample profile to the in-memory store."""
    profile = get_sample_profile()
    profiles[profile["username"]] = profile
    return profile

def save_profile(profile: dict):
    """Save a user profile to the in-memory store."""
    profiles[profile["username"]] = profile

def is_valid_username(username: str) -> bool:
    """Check if the username is unique."""
    username_regex = r"^[a-zA-Z0-9_]+$"
    if username not in profiles and re.match(username_regex, username):
        return True
    return False


