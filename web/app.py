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


def main():
    st.set_page_config(page_title="Recco.", page_icon="🎬")
    st.title("Recco.")

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

        with st.spinner("Finding movies..."):
            try:
                results = recommend_from_blurb(blurb)
            except QuotaExceededError:
                st.warning("⚠️ Too many requests - try again tomorrow! (This is what happens when you use free stuff 😅)")
                st.stop()

        st.subheader("Recommendations")
        st.write(f"We have {len(results)} recommendations for you:")
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
