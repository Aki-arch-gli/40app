import pandas as pd
import datetime
from modules.shopping import create_shopping_list

# CSVのロードユーティリティ
def load_menu():
    return pd.read_csv("data/menu_data.csv")

def current_season():
    month = datetime.datetime.now().month
    if month in [3, 4, 5]:
        return "春"
    elif month in [6, 7, 8]:
        return "夏"
    elif month in [9, 10, 11]:
        return "秋"
    else:
        return "冬"

def contains_food(row, food):
    text = f"{row.get('breakfast', '')} {row.get('lunch', '')} {row.get('dinner', '')}"
    return food in text

def generate_menu(
    age,
    disease,
    calorie,
    season="auto",
    style=None,
    difficulty=None,
    dislike=None,
    favorite_food=None,
    history=None
):
    age = int(age)
    calorie = int(calorie)
    disease = str(disease).strip()

    df = load_menu()

    # 年齢フィルター
    if "min_age" in df.columns and "max_age" in df.columns:
        df = df[(df["min_age"] <= age) & (df["max_age"] >= age)]

    # 疾患フィルター
    if "disease" in df.columns:
        df["disease"] = df["disease"].astype(str).str.strip()
        if disease in ["なし", "疾患なし"]:
            df = df[df["disease"].isin(["なし", "疾患なし"])]
        else:
            df = df[df["disease"] == disease]

    # 季節フィルター
    if season == "auto":
        season = current_season()
    if "season" in df.columns:
        df = df[(df["season"] == season) | (df["season"] == "通年")]

    # 料理スタイル（和洋中）
    if style and "japanese_style" in df.columns:
        df = df[df["japanese_style"] == style]

    # 難易度フィルター (difficulty または level カラムの両方に対応)
    if difficulty:
        diff_col = "difficulty" if "difficulty" in df.columns else ("level" if "level" in df.columns else None)
        if diff_col:
            df = df[df[diff_col].astype(str).str.contains(str(difficulty), na=False)]

    # 苦手食材フィルター
    if dislike:
        for food in dislike:
            if food:
                df = df[
                    ~(
                        df["breakfast"].astype(str).str.contains(food, na=False) |
                        df["lunch"].astype(str).str.contains(food, na=False) |
                        df["dinner"].astype(str).str.contains(food, na=False)
                    )
                ]

    # 魚料理希望
    if favorite_food == "魚":
        fish = ["鮭", "さば", "ぶり", "たら", "あじ", "白身魚", "さんま", "魚", "さわら", "赤魚"]
        df = df[df.apply(lambda x: any(contains_food(x, f) for f in fish), axis=1)]

    # 肉料理希望
    elif favorite_food == "肉":
        meat = ["鶏", "豚", "牛", "ハンバーグ"]
        df = df[df.apply(lambda x: any(contains_food(x, f) for f in meat), axis=1)]

    # 過去履歴除外
    if history and "id" in df.columns:
        df = df[~df["id"].isin(history)]

    if len(df) == 0:
        return None

    # カロリー差でソート
    if "calorie" in df.columns:
        df["diff"] = abs(df["calorie"] - calorie)
        df = df.sort_values("diff")

    candidates = df.head(15)
    menu = candidates.sample(1).iloc[0]

    # レスポンス形式はそのまま保持
    return {
        "id": int(menu["id"]) if "id" in menu else 1,
        "朝食": menu.get("breakfast", ""),
        "昼食": menu.get("lunch", ""),
        "夕食": menu.get("dinner", ""),
        "理由": menu.get("reason", "持病に配慮した栄養バランス調整済みです。"),
        "バランス": menu.get("balance", "バランス良好"),
        "アドバイス": menu.get("advice", "水分をしっかりと摂ってお召し上がりください。"),
        "カロリー": int(menu.get("calorie", calorie)),
        "季節": menu.get("season", "通年"),
        "料理": menu.get("japanese_style", "和食"),
        "難易度": menu.get("difficulty", menu.get("level", "普通")),
        "買い物リスト": create_shopping_list({
            "朝食": menu.get("breakfast", ""),
            "昼食": menu.get("lunch", ""),
            "夕食": menu.get("dinner", "")
        })
    }