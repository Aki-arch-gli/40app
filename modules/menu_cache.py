import random


menus = [

"""
🌅 朝食

ご飯
味噌汁
鮭
納豆


🌞 昼食

うどん
野菜のお浸し


🌙 夕食

豚肉の煮物
かぼちゃ
ご飯
""",

"""
🌅 朝食

食パン
牛乳
卵料理


🌞 昼食

親子丼


🌙 夕食

魚の煮付け
野菜料理
ご飯
"""

]


def get_cached_menu():

    return random.choice(menus)
