"""SQLite operations for Recco profile storage."""

import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "recco.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn

def init_db():
    """Create tables if they don't exist. Call once on app startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE NOT NULL,
                liked_genres    TEXT DEFAULT '[]',
                disliked_genres TEXT DEFAULT '[]',
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ratings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id  INTEGER NOT NULL REFERENCES profiles(id),
                tmdb_id     INTEGER NOT NULL,
                title       TEXT NOT NULL,
                rating      REAL,
                sentiment   TEXT CHECK(sentiment IN ('liked', 'disliked', 'neutral')),
                rated_at    TEXT NOT NULL
            );
        """)

# --- profile operations ---

def create_profile(username: str, liked_genres: list, disliked_genres: list) -> dict:
    """Create and return a new profile. Raises ValueError if username is taken."""
    with get_connection() as conn:
        try:
            conn.execute(
                """INSERT INTO profiles (username, liked_genres, disliked_genres, created_at)
                   VALUES (?, ?, ?, ?)""",
                (username, json.dumps(liked_genres), json.dumps(disliked_genres), datetime.now(timezone.utc).isoformat())
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"Username '{username}' is already taken.")
    return get_profile(username)

def get_profile(username: str) -> dict | None:
    """Return a profile dict or None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM profiles WHERE username = ?", (username,)
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "liked_genres": json.loads(row["liked_genres"]),
        "disliked_genres": json.loads(row["disliked_genres"]),
        "created_at": row["created_at"]
    }

def delete_profile(username: str) -> bool:
    """Delete a profile and all its ratings. Returns True if deleted."""
    with get_connection() as conn:
        profile = get_profile(username)
        if not profile:
            return False
        conn.execute("DELETE FROM ratings WHERE profile_id = ?", (profile["id"],))
        conn.execute("DELETE FROM profiles WHERE username = ?", (username,))
    return True

# --- ratings operations ---

def add_rating(username: str, tmdb_id: int, title: str, rating: float, sentiment: str) -> dict:
    """Add or update a rating for a profile."""
    profile = get_profile(username)
    if not profile:
        raise ValueError(f"Profile '{username}' not found.")

    with get_connection() as conn:
        # update if already rated, insert if not
        existing = conn.execute(
            "SELECT id FROM ratings WHERE profile_id = ? AND tmdb_id = ?",
            (profile["id"], tmdb_id)
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE ratings SET rating = ?, sentiment = ?, rated_at = ?
                   WHERE profile_id = ? AND tmdb_id = ?""",
                (rating, sentiment, datetime.now(timezone.utc).isoformat(), profile["id"], tmdb_id)
            )
        else:
            conn.execute(
                """INSERT INTO ratings (profile_id, tmdb_id, title, rating, sentiment, rated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (profile["id"], tmdb_id, title, rating, sentiment, datetime.utcnow().isoformat())
            )
    return get_ratings(username)

def update_genres_db(username: str, liked_genres: list, disliked_genres: list) -> None:
     with get_connection() as conn:
        conn.execute(
            "UPDATE profiles SET liked_genres = ?, disliked_genres = ? WHERE username = ?",
            (json.dumps(liked_genres), json.dumps(disliked_genres), username)
        )

def get_ratings(username: str) -> list[dict]:
    """Return all ratings for a profile."""
    profile = get_profile(username)
    if not profile:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ratings WHERE profile_id = ? ORDER BY rated_at DESC",
            (profile["id"],)
        ).fetchall()
    return [
        {
            "tmdb_id": r["tmdb_id"],
            "title": r["title"],
            "rating": r["rating"],
            "sentiment": r["sentiment"],
            "rated_at": r["rated_at"]
        }
        for r in rows
    ]

def get_usernames() -> list[str]:
    """Return a list of all usernames."""
    with get_connection() as conn:
        rows = conn.execute("SELECT username FROM profiles").fetchall()
    return [r["username"] for r in rows]