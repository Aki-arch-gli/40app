import os
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SupabaseのURLまたはKEYが設定されていません。")
    return create_client(url, key)