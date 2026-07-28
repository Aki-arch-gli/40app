def create_shopping_list(weekly_menu):

    foods = []

    for day, menu in weekly_menu.items():

        if "買い物リスト" in menu:

            foods.extend(
                menu["買い物リスト"]
            )

        else:

            foods.extend([
                menu.get("朝食",""),
                menu.get("昼食",""),
                menu.get("夕食","")
            ])


    # 重複削除
    result=[]

    for food in foods:

        if food not in result:
            result.append(food)


    return result