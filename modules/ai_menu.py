import re
import google.generativeai as genai
import openai

from config import *

if GEMINI_API_KEY:

    genai.configure(api_key=GEMINI_API_KEY)

if OPENAI_API_KEY:

    openai.api_key = OPENAI_API_KEY


def create_prompt(
    age,
    disease,
    calorie,
    simple
):

 if simple:

    return f"""
あなたは高齢者専門の管理栄養士です。

対象は{age}歳です。
疾患は「{disease}」です。
目標カロリーは約{calorie}kcalです。

80歳前後の方でも読みやすい文章にしてください。

以下の形式を必ず守ってください。

🌅 朝ごはん
・料理名
・料理名
・料理名

🌞 昼ごはん
・料理名
・料理名
・料理名

🌙 夜ごはん
・料理名
・料理名
・料理名

💡 今日のポイント
・水分を飲みましょう
・野菜を食べましょう
・お肉か魚を食べましょう

【ルール】
・料理だけを書いてください
・専門用語は禁止
・栄養素は書かない
・カロリー計算は書かない
・200文字以内
"""

 return f"""
あなたは日本の管理栄養士です。

対象
・年齢：{age}歳
・疾患：{disease}
・必要カロリー：約{calorie}kcal

必ず以下の形式だけで回答してください。

🌅 朝食
例：
ご飯
納豆
味噌汁

🌞 昼食
例：
鮭の塩焼き
ご飯
野菜サラダ

🌙 夕食
例：
鶏肉料理
野菜のおかず
味噌汁

🔥 カロリー
約1800kcal

💡 理由
1文

🥗 バランス
1文

🤖 アドバイス
1文


禁止事項：
・HTMLタグは禁止
・<h1>や<p>は禁止
・表形式は禁止
・料理説明は禁止
"""


def gemini_menu(
    age,
    disease,
    calorie,
    simple=False
):

    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(

        create_prompt(
           age,
           disease,
           calorie,
           simple
        )

    )


    text = response.text


    # HTMLタグ削除
    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )


    # Markdown装飾削除
    text = text.replace(
        "**",
        ""
    )


    return text.strip()


def openai_menu(
    age,
    disease,
    calorie,
    simple=False
):

    client = openai.OpenAI()

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[

            {
                "role": "user",
                "content":
                create_prompt(
                    age,
                    disease,
                    calorie,
                    simple
                )

            }

        ]

    )

    return response.choices[0].message.content


def generate_ai_menu(
    age,
    disease,
    calorie,
    simple=False
):

    if AI_MODEL == "gemini":

        return gemini_menu(
            age,
            disease,
            calorie,
            simple
        )

    return openai_menu(
        age,
        disease,
        calorie,
        simple
    )