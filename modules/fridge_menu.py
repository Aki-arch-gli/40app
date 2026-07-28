import pandas as pd

from modules.ingredient_parser import (
    get_ingredients,
    normalize_food
)


def recommend_from_fridge(

        foods,
        age,
        disease,
        calorie

):


    df=pd.read_csv(
        "data/menu_data.csv"
    )


    # 年齢

    df=df[
        (df["min_age"]<=age)
        &
        (df["max_age"]>=age)
    ]


    # 疾患

    df=df[
        (df["disease"]==disease)
        |
        (df["disease"]=="なし")
    ]


    # カロリー

    df=df[
        abs(df["calorie"]-calorie)<=200
    ]



    # ★冷蔵庫食材を正規化

    normalized_foods=[

        normalize_food(food)

        for food in foods

    ]



    candidates=[]


    for _,row in df.iterrows():


        breakfast=get_ingredients(
            row["breakfast"]
        )


        lunch=get_ingredients(
            row["lunch"]
        )


        dinner=get_ingredients(
            row["dinner"]
        )


        need=list(

            set(

                breakfast
                +
                lunch
                +
                dinner

            )

        )



        # 一致数

        score = 0


        for food in foods:

            food = normalize_food(food)


            for item in need:

                item = normalize_food(item)


                if food == item:

                    score += 1
                    break



        # 足りない食材

        lack=list(

            set(need)

            -
            set(normalized_foods)

        )



        # 一致率

        if len(need)>0:


            rate=round(

                score
                /
                len(need)
                *
                100

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



    # 一致数が多い順

    candidates.sort(

        key=lambda x:x[0],

        reverse=True

    )


    return candidates[:10]