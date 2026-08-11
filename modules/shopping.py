# modules/shopping.py

def create_shopping_list(menu):
    # 引数が辞書の場合と文字列の場合の両方に対応
    if isinstance(menu, dict):
        breakfast = menu.get("朝食", menu.get("breakfast", ""))
        lunch = menu.get("昼食", menu.get("lunch", ""))
        dinner = menu.get("夕食", menu.get("dinner", ""))
        text = f"{breakfast} {lunch} {dinner}"
    else:
        text = str(menu)

    # 食材キーワードの簡易抽出（例）
    ingredients = []
    keywords = ["鮭", "さば", "鶏肉", "豚肉", "牛肉", "豆腐", "卵", "キャベツ", "玉ねぎ", "人参", "ほうれん草", "大根", "トマト", "味噌", "納豆", "うどん", "白身魚", "じゃがいも"]
    
    for kw in keywords:
        if kw in text:
            ingredients.append(kw)
            
    return "、".join(ingredients) if ingredients else "旬の野菜、お好みのお肉・お魚"