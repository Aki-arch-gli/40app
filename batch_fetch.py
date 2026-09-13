import json
import os
from datetime import datetime

CACHE_FILE = "events_cache.json"

def fetch_external_events():
    """外部APIやWebからイベント情報を取得する処理"""
    print(f"[{datetime.now()}] イベント情報を更新中...")
    
    # 実際のAPIリクエストやスクレイピング処理をここに記述
    # 例:
    # response = requests.get("https://api.example.com/events")
    # data = response.json()
    
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": [
            {"title": "地域夏祭り", "time": "18:00", "location": "中央公園"},
            {"title": "防災セミナー", "time": "14:00", "location": "市民会館"}
        ]
    }
    
    # JSONファイルに保存（アトミックに書き込むため一時ファイルを使用）
    temp_file = CACHE_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_file, CACHE_FILE)
    
    print(f"[{datetime.now()}] 更新完了")

if __name__ == "__main__":
    fetch_external_events()