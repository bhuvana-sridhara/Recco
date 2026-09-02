"""Minimal recommender logic for the Recco POC.

This module intentionally contains a trivial recommendation function so
the Streamlit UI can demonstrate integration with the backend.
"""
from time import time, sleep
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
from .data import get_sample_movies, discover_movies, filter_candidates
from .util import get_api_key
from .profiles import get_full_profile

FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

EXCLUDE_PATTERNS = ["omni", "tts", "image", "preview", "lite", "latest"]


# Configure Gemini API key
genai.configure(api_key=get_api_key("GEMINI_API_KEY"))
# gemini = genai.GenerativeModel("gemini-2.5-flash")
encoder = SentenceTransformer("all-MiniLM-L6-v2")

_gemini = None

class QuotaExceededError(Exception):
    """Custom exception for when Gemini API quota is exceeded."""
    pass

def get_best_model() -> str:
    """Fetch available models and return the newest flash model."""
    try:
        available = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
            and "flash" in m.name
            and not any(pattern in m.name for pattern in EXCLUDE_PATTERNS)
        ]
        print(f"Filtered stable models: {available}")

        if not available:
            return "models/gemini-2.5-flash"  # last resort hardcode

        # extract version number and sort — picks highest
        def version_key(name):
            match = re.search(r'(\d+\.\d+|\d+)', name)
            return float(match.group()) if match else 0

        available.sort(key=version_key, reverse=True)
        print(f"Selected model: {available[0]}")
        return available[0]

    except Exception:
        return "models/gemini-2.5-flash"

def get_gemini():
    global _gemini
    if _gemini is None:
        model_name = get_best_model()
        for name in [model_name] + FALLBACK_MODELS:
            try:
                _gemini = genai.GenerativeModel(name)
                print(f"Using Gemini model: {name}")
                break
            except Exception as e:
                print(f"{name} failed: {e}, trying next...")
        if _gemini is None:
            raise RuntimeError("No Gemini model available.")
    return _gemini

def generate_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Call Gemini with exponential backoff on quota errors."""
    for attempt in range(max_retries):
        try:
            response = get_gemini().generate_content(prompt)
            return response.text
        except ResourceExhausted:
            if attempt == max_retries - 1:
                raise QuotaExceededError()
            wait = 2 ** attempt
            print(f"Quota hit, retrying in {wait}s...")
            sleep(wait)


# sanity check that we can connect to Gemini and list models
def get_models():
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods and "flash" in m.name:
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

def get_profile_details_prompt(profile: dict):
    profile = get_full_profile(profile["username"])
    profile_prompt = ""
    if profile:
        for key, value in profile.items():
            if isinstance(value, list):
                value = ", ".join(value)
            profile_prompt += f"{key}: {value}\n"
    return profile_prompt

def process_blurb(blurb: str, profile: dict = None) -> dict:
    """Use Gemini to extract structured filters from the blurb."""
    prompt = f"""A user wants to watch a movie and described it as: "{blurb}"

    {get_profile_details_prompt(profile) if profile else ""}

    Return a JSON object with exactly these three fields:
    - "genres": list of 1-3 genre names from this list only:
      [Action, Adventure, Animation, Comedy, Crime, Documentary, Drama,
      Family, Fantasy, History, Horror, Music, Mystery, Romance,
      Science Fiction, Thriller, War, Western]. Do not combine or invent genres. 
      If the mood spans multiple genres, list them separately.
    - "tone": a 2-3 sentence description of mood, pacing, and emotional feel
    - "keywords": list of 2-3 thematic keywords — think themes like
      "redemption", "friendship", "coming of age". NOT literal title words.

    Only return the raw JSON object, no markdown, no backticks, nothing else."""

    try:
        response_text = generate_with_retry(prompt)
    except QuotaExceededError:
        raise

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"genres": ["Drama"], "tone": blurb, "keywords": []}


def get_candidate_summaries(candidates: list[dict], blurb: str, tone: str, keywords: list, n: int) -> str:
    candidate_summaries = [
        f"{i}. {m['title']} ({m.get('release_date', '')[:4]}): {m.get('overview', '')}"
        for i, m in enumerate(candidates)
    ]

    prompt = f"""A user wants to watch a movie and described it as: "{blurb}"
            Mood/tone they're looking for: {tone}
            Themes: {", ".join(keywords)}

            From the list below pick the top {n} best matches. Prioritize well-known
            mainstream movies over obscure ones. For each return the index and a
            one-sentence reason why it fits the mood.

            {chr(10).join(candidate_summaries)}

            Return only a JSON array, nothing else:
            [{{"index": 0, "reason": "..."}}]"""

    return generate_with_retry(prompt)

def recommend_from_blurb(blurb: str, profile: dict | None = None, n: int = 5) -> list[dict]:
    processed = process_blurb(blurb, profile)
    print(f"Genres: {processed['genres']}")
    print(f"Tone: {processed['tone']}")
    print(f"Keywords: {processed['keywords']}")

    # use discover instead of keyword search
    candidates = discover_movies(processed["genres"], page=1)
    candidates += discover_movies(processed["genres"], page=2)

    # deduplicate
    seen = set()
    unique = []
    for m in candidates:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)

    # filter for quality + mainstream
    unique = filter_candidates(unique)

    if not unique:
        return []

    try:
        response_text = get_candidate_summaries(unique, blurb, processed["tone"], processed["keywords"], n)
        raw = re.sub(r"```json|```", "", response_text).strip()
        ranked = json.loads(raw)
    except QuotaExceededError:
        raise
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if match:
            ranked = json.loads(match.group())
        else:
            print("Gemini ranking failed, falling back to cosine similarity")
            expanded_vector = encoder.encode([processed["tone"]])
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
        print(m["title"])

    return results