from google import genai
from dotenv import load_dotenv
import os
import time


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_weekly_ai(
    age,
    disease,
    calorie
):

    prompt = f"""

あなたは高齢者専門の管理栄養士です。

対象者：
年齢 {age}歳

疾患：
{disease}

必要カロリー：
約{calorie}kcal


月曜日から日曜日まで
朝食・昼食・夕食を作成してください。


形式：

月曜日

🌅 朝食
料理名

🌞 昼食
料理名

🌙 夕食
料理名


火曜日
...


最後に

【買い物リスト】

【1週間の健康アドバイス】

を書いてください。


高齢者が読みやすい文章にしてください。

"""


    models = [

        "gemini-flash-latest",

        "gemini-1.5-flash"

    ]


    error = ""


    for model in models:

        try:

            response = client.models.generate_content(

                model=model,

                contents=prompt

            )


            return response.text


        except Exception as e:

            error = str(e)

            time.sleep(2)



    return f"""
現在AIサービスが利用できません。

しばらく時間を置いて再度お試しください。

{error}
"""