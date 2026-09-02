"""Very small Streamlit UI: description + blurb input."""
import warnings
import os
import sys
import logging
# Suppress warnings globally
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)


# Ensure the project root is on sys.path so `import recommender` works when
# running `streamlit run web/app.py` from the repo root (or elsewhere).
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from recommender.model import recommend_from_blurb, QuotaExceededError
from recommender.db import init_db
from recommender.profiles import (
    register_profile, load_profile, rate_movie, get_full_profile, update_genres
)

init_db()  # ensure DB tables are created before handling any requests

def profile_section():
    st.sidebar.title("👤 Profile")

    if "username" not in st.session_state:
        st.session_state.username = None

    if st.session_state.username:
        st.sidebar.success(f"Logged in as **{st.session_state.username}**")

        st.sidebar.markdown("**Liked genres**")
        liked = st.sidebar.text_input("e.g. drama, thriller", key="liked_genres")

        st.sidebar.markdown("**Disliked genres**")
        disliked = st.sidebar.text_input("e.g. horror, musical", key="disliked_genres")

        if st.sidebar.button("Save preferences"):
            profile = load_profile(st.session_state.username)
            liked_list = [g.strip() for g in liked.split(",") if g.strip()]
            disliked_list = [g.strip() for g in disliked.split(",") if g.strip()]
            update_genres(st.session_state.username, liked_list, disliked_list)
            st.sidebar.success("Preferences saved!")

        if st.sidebar.button("Log out"):
            st.session_state.username = None
            st.rerun()

    else:
        username_input = st.sidebar.text_input("Username")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.sidebar.button("Log in"):
                profile = load_profile(username_input)
                if profile:
                    st.session_state.username = username_input
                    st.rerun()
                else:
                    st.sidebar.error("Profile not found.")
        with col2:
            if st.sidebar.button("Register"):
                try:
                    register_profile(username_input)
                    st.session_state.username = username_input
                    st.rerun()
                except ValueError as e:
                    st.sidebar.error(str(e))

def main():
    st.set_page_config(page_title="Recco.", page_icon="🎬")
    st.title("Recco.")

    profile_section()

    st.markdown("""
    Recco. — quick movie recommender proof-of-concept.
    Enter a short blurb describing what you want to watch
    (e.g., "light comedy for a date night", "sci-fi with strong female lead").
    """)

    blurb = st.text_area("Describe what you want to watch", height=150)

    if st.button("Submit"):
        if not blurb:
            st.warning("Please enter a blurb first.")
            return
        
        # grab profile if logged in
        profile = None
        if st.session_state.get("username"):
            profile = get_full_profile(st.session_state.username)

        with st.spinner("Finding movies..."):
            try:
                results = recommend_from_blurb(blurb, profile=profile)
            except QuotaExceededError:
                results = None
                
        if results is None:
            st.warning("⚠️ Too many requests - try again tomorrow! (This is what happens when you use free stuff 😅)")
            st.stop()

        st.subheader("Recommendations")
        st.write(f"We have {len(results)} recommendations for you based on your likes and dislikes:")
        for movie in results:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if movie.get("poster_path"):
                    st.image(f"https://image.tmdb.org/t/p/w200{movie['poster_path']}")
                else:
                    st.write("🎬")  # fallback if no poster
            
            with col2:
                st.subheader(movie["title"])
                
                # year + rating on one line
                year = movie.get("release_date", "")[:4]
                rating = movie.get("vote_average", 0)
                genres = ", ".join(g["name"] for g in movie.get("genres", []))
                st.caption(f"{year}  ·  ⭐ {rating:.1f}  ·  {genres}")
                
                st.write(movie.get("overview", ""))
                st.write(f"Reason: {movie.get("reason", "")}")
            
            st.divider()  # clean separator between movies


if __name__ == "__main__":
    main()
