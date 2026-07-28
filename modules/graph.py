import plotly.express as px
import pandas as pd

def nutrition_pie(menu):

    df = pd.DataFrame({

        "栄養素":[
            "たんぱく質",
            "脂質",
            "炭水化物"
        ],

        "量":[
            menu["protein"],
            menu["fat"],
            menu["carb"]
        ]

    })

    fig = px.pie(
        df,
        names="栄養素",
        values="量",
        title="栄養バランス"
    )

    return fig


def nutrition_bar(menu):

    df = pd.DataFrame({

        "項目":[
            "カロリー",
            "たんぱく質",
            "脂質",
            "炭水化物",
            "塩分"
        ],

        "値":[

            menu["calorie"],
            menu["protein"],
            menu["fat"],
            menu["carb"],
            menu["salt"]

        ]

    })

    fig = px.bar(
        df,
        x="項目",
        y="値",
        title="栄養情報"
    )

    return fig