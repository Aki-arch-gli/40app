import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

AI_MODEL = "gemini-3.5-flash"
AI_BACKUP_MODEL = "gemini-3.1-flash-lite"

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")