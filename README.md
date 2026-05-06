# Recco.
A proof-of-concept system that gives individual movie recommendations and helps friends quickly decide what movie to watch together.

Getting started (local)

- Install dependencies:

```bash
python -m pip install -r requirements.txt
```

- Run the Streamlit UI:

```bash
streamlit run web/app.py
```

This repository currently contains a tiny Python backend (`recommender/`) and a minimal Streamlit UI (`web/app.py`) to demonstrate integration. The backend is intentionally lightweight for proof-of-concept.

Movie data and metadata provided by [The Movie Database (TMDB)](https://www.themoviedb.org/).
