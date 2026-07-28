import pandas as pd
import random
from datetime import datetime

MENU_FILE = "data/menu_data.csv"


# -----------------------------
# CSV読み込み
# -----------------------------
def load_menu():

    df = pd.read_csv(
        MENU_FILE,
        encoding="utf-8"
    )

    # 数値列を強制的に数値化
    numeric_columns = [
        "id",
        "min_age",
        "max_age",
        "calorie"
    ]

    for col in numeric_columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


    # 欠損行を削除
    df = df.dropna(
        subset=[
            "min_age",
            "max_age",
            "calorie"
        ]
    )


    return df


# -----------------------------
# 現在の季節取得
# -----------------------------
def current_season():

    month = datetime.now().month

    if month in [3, 4, 5]:
        return "春"

    elif month in [6, 7, 8]:
        return "夏"

    elif month in [9, 10, 11]:
        return "秋"

    else:
        return "冬"


# -----------------------------
# 食材検索
# -----------------------------
def contains_food(row, keyword):

    text = (
        str(row["breakfast"])
        + str(row["lunch"])
        + str(row["dinner"])
    )

    return keyword in text


# -----------------------------
# 買い物リスト生成
# -----------------------------
def create_shopping_list(menu):

    foods = []

    for key in ["朝食", "昼食", "夕食"]:

        foods.extend(
            str(menu[key]).split("・")
        )

    foods = list(dict.fromkeys(foods))

    return foods


# -----------------------------
# 献立生成
# -----------------------------
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
    # 型を修正
    age = int(age)
    calorie = int(calorie)

    disease = str(disease)

    df = load_menu()

    # 年齢
    df = df[
        (df["min_age"] <= age)
        &
        (df["max_age"] >= age)
    ]

    # 疾患
    # 「なし」と「疾患なし」を同じ扱いにする

    # 疾患
    df["disease"] = (
        df["disease"]
        .astype(str)
        .str.strip()
    )

    disease = disease.strip()


    if disease in ["なし", "疾患なし"]:

        disease_df = df[
            df["disease"].isin(
                [
                    "なし",
                    "疾患なし"
                ]
            )
        ]

    else:

        disease_df = df[
             df["disease"] == disease
        ]


    df = disease_df.copy()

    # 季節
    if season == "auto":

        season = current_season()

    df = df[
        (df["season"] == season)
        |
        (df["season"] == "通年")
    ]

    # 和洋中
    if style:

        df = df[
            df["japanese_style"] == style
        ]

    # 難易度
    if difficulty:

        df = df[
            df["difficulty"] == difficulty
        ]

    # 苦手食材
    if dislike:

        for food in dislike:

            df = df[
                ~(
                    df["breakfast"].str.contains(food, na=False)
                    |
                    df["lunch"].str.contains(food, na=False)
                    |
                    df["dinner"].str.contains(food, na=False)
                )
            ]

    # 魚料理希望
    if favorite_food == "魚":

        fish = [
            "鮭",
            "さば",
            "ぶり",
            "たら",
            "あじ",
            "白身魚",
            "さんま",
            "魚",
            "さわら",
            "赤魚"
        ]

        df = df[
            df.apply(
                lambda x: any(
                    contains_food(x, f)
                    for f in fish
                ),
                axis=1
            )
        ]

    # 肉料理希望
    elif favorite_food == "肉":

        meat = [
            "鶏",
            "豚",
            "牛",
            "ハンバーグ"
        ]

        df = df[
            df.apply(
                lambda x: any(
                    contains_food(x, f)
                    for f in meat
                ),
                axis=1
            )
        ]

    # 過去7件除外
    if history:

        df = df[
            ~df["id"].isin(history)
        ]

    # カロリー差
    df["diff"] = abs(
        df["calorie"] - calorie
    )

    df = df.sort_values("diff")

    if len(df) == 0:


        return None

    candidates = df.head(15)

    menu = candidates.sample(1).iloc[0]


    return {

        "id": int(menu["id"]),

        "朝食": menu["breakfast"],

        "昼食": menu["lunch"],

        "夕食": menu["dinner"],

        "理由": menu["reason"],

        "バランス": menu["balance"],

        "アドバイス": menu["advice"],

        "カロリー": int(menu["calorie"]),

        "季節": menu["season"],

        "料理": menu["japanese_style"],

        "難易度": menu["difficulty"],

        "買い物リスト": create_shopping_list(
            {
                "朝食": menu["breakfast"],
                "昼食": menu["lunch"],
                "夕食": menu["dinner"]
            }
        )

    }
