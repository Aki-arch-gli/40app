import os
import urllib.request

# 環境変数からURLとAPIキーを取得
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL or SUPABASE_KEY is missing.")
    exit(1)

# SupabaseのREST API（ヘルスチェック用エンドポイント等）へアクセス
url = f"{supabase_url}/rest/v1/"
headers = {
    "apikey": supabase_key,
    "Authorization": f"Bearer {supabase_key}"
}

req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        print(f"Success! Status code: {response.getcode()}")
except Exception as e:
    print(f"Failed to keep alive: {e}")
    exit(1)