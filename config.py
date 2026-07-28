# config.py

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")

# 使用するAI
AI_MODEL = "gemini"