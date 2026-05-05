"""Very small Streamlit UI: description + blurb input."""

import os
import sys

# Ensure the project root is on sys.path so `import recommender` works when
# running `streamlit run web/app.py` from the repo root (or elsewhere).
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st

from recommender.model import recommend


def main():
    st.set_page_config(page_title="Recco.", page_icon="🎬")
    st.title("Recco.")

    st.markdown("""
    Recco. — quick movie recommender proof-of-concept.

    Enter a short blurb describing what you want from the recommender
    (e.g., "light comedy for a date night", "sci-fi with strong female lead").
    """)

    blurb = st.text_area("Describe your need / blurb", height=150)

    if st.button("Submit"):
        st.subheader("Your blurb")
        st.write(blurb or "(no blurb entered)")

        st.subheader("Sample recommendations")
        # Use the trivial recommend() function for POC results
        recs = recommend("guest", 5)
        for r in recs:
            st.write(f"- **{r['title']}** ({r['year']})")


if __name__ == "__main__":
    main()
