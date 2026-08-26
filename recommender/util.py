from dotenv import load_dotenv
import os
import streamlit as st

def get_api_key(key: str) -> str:
    # try .env first, fall back to st.secrets
    return os.getenv(key) or st.secrets.get(key)