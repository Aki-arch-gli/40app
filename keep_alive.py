import os
from supabase import create_client

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL or SUPABASE_KEY is missing.")
    exit(1)

try:
    # 公式ライブラリで接続初期化
    supabase = create_client(supabase_url, supabase_key)
    
    # 認証エンドポイントへアクセスしてアクティブ状態を維持
    response = supabase.auth.get_session()
    print("Success! Supabase connection active.")
except Exception as e:
    print(f"Failed to keep alive: {e}")
    exit(1)