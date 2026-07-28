import google.generativeai as genai

from config import GEMINI_API_KEY


# Gemini設定
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def create_prompt(age, disease, calorie, simple=False):

    if simple:

        return f"""
あなたは高齢者専門の管理栄養士です。

対象
・年齢：{age}歳
・疾患：{disease}
・必要カロリー：約{calorie}kcal

必ず以下の形式だけで回答してください。

🌅 朝食
料理名だけを書く

🌞 昼食
料理名だけを書く

🌙 夕食
料理名だけを書く

🔥 カロリー
数字だけを書く

理由
短く書く

バランス
短く書く

アドバイス
短く書く

料理名以外の説明文を朝食・昼食・夕食欄には入れないでください。
"""


    return f"""
あなたは日本の管理栄養士です。

年齢：{age}歳
疾患：{disease}
必要カロリー：約{calorie}kcal

朝食・昼食・夕食について

・料理名
・カロリー
・栄養バランス

を書いてください。

最後に

【この献立の理由】

も説明してください。
"""


def generate_ai_menu(
    age,
    disease,
    calorie,
    simple=False
):

    prompt = create_prompt(
        age,
        disease,
        calorie,
        simple
    )

    models = [
        "gemini-flash-latest",
        "gemini-2.0-flash"
    ]


    last_error = ""


    for model in models:

        try:

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            return response.text


        except Exception as e:

            last_error = str(e)


    return f"""
現在AIサーバーが混雑しています。

時間をおいて再度お試しください。

{last_error}
"""


def generate_weekly_ai_menu(
    age,
    disease,
    calorie
):

    prompt = f"""
あなたは高齢者専門の管理栄養士です。

年齢：{age}歳
疾患：{disease}
必要カロリー：約{calorie}kcal

高齢者が1週間続けやすい献立を作成してください。

必ず以下の形式で回答してください。

【月曜日】
朝
・料理
・料理
・料理

昼
・料理
・料理
・料理

夜
・料理
・料理
・料理


【火曜日】
...

【水曜日】
...

【木曜日】
...

【金曜日】
...

【土曜日】
...

【日曜日】
...


【ルール】

・料理名だけ

・説明不要

・カロリー不要

・栄養説明不要

・やわらかい料理を中心

・日本食中心

・毎日違う献立
"""


    models = [
        "gemini-flash-latest",
        "gemini-2.0-flash"
    ]


    for model in models:

        try:

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            return response.text


        except Exception:

            pass


    return "週間献立を作成できませんでした。"