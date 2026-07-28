from modules.database import add_recommended_menu


# 疾患なし
add_recommended_menu(
    65,
    100,
    "なし",
    1400,

    """
ご飯
豆腐とわかめの味噌汁
納豆
ほうれん草のおひたし
""",

    """
麦ご飯
鮭の塩焼き
ひじき煮
野菜スープ
""",

    """
ご飯
鶏肉の蒸し料理
かぼちゃ煮
豆腐味噌汁
"""
)


print("献立データ登録完了")