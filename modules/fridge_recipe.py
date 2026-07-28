import pandas as pd

from modules.ingredient_parser import get_ingredients


def recommend_from_fridge(
        foods,
        age,
        disease,
        calorie
):

    import os


    BASE_DIR = os.path.dirname(
        os.path.dirname(__file__)
    )


    MENU_FILE = os.path.join(
        BASE_DIR,
        "data",
        "menu_data.csv"
    )


    df = pd.read_csv(MENU_FILE)


    # 年齢
    df = df[
        (df["min_age"] <= age)
        &
        (df["max_age"] >= age)
    ]



    # 疾患
    if disease == "なし":
        df = df[
            df["disease"].isin(["なし", "疾患なし"])
        ]
    else:
        df = df[
            df["disease"] == disease
        ]

    # カロリー
    df = df[
        abs(df["calorie"] - calorie) <= 700
    ]


    candidates=[]


    for _,row in df.iterrows():


        ingredients = []


        for meal in [
            row["breakfast"],
            row["lunch"],
            row["dinner"]
        ]:

            ingredients += get_ingredients(
                str(meal)
            )


        need=list(set(ingredients))


        matched = []

        for f in foods:

            for n in need:

               if f == n or f in n or n in f:

                    matched.append(n)
                    break

        matched = list(set(matched))
 
        score = len(matched)

        lack = [
            n
            for n in need
            if n not in matched
        ]


        if len(need)>0:

            rate = round(
                score / len(need) *100
            )

        else:

            rate=0



        candidates.append(

            (
                score,
                rate,
                lack,
                row

            )

        )



    candidates.sort(
        key=lambda x:x[1],
        reverse=True
    )

    return candidates[:5]

