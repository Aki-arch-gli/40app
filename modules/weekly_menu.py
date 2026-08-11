from modules.menu_generator import generate_menu

def generate_weekly_menu(
    age,
    disease,
    calorie,
    season="auto",
    style=None,
    difficulty=None,
    dislike=None,
    favorite_food=None
):
    days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    week = {}
    history = []
    used_meals = set() # 昼食・夕食の被り判定用

    for day in days:
        best_menu = None
        
        # 被りを防ぐため、最大5回まで再生成を試みる
        for _ in range(5):
            menu = generate_menu(
                age=age,
                disease=disease,
                calorie=calorie,
                history=history,
                season=season,
                style=style,
                difficulty=difficulty,
                dislike=dislike,
                favorite_food=favorite_food
            )
            
            if menu:
                lunch = menu.get("昼食", "")
                dinner = menu.get("夕食", "")
                
                # 既に採用済みのメニュー名が含まれていなければ即採用
                if lunch not in used_meals and dinner not in used_meals:
                    best_menu = menu
                    break
                
                # 被っていても一旦キープ（リトライ上限に達した時のため）
                best_menu = menu
                
        if best_menu:
            week[day] = best_menu
            
            if "id" in best_menu:
                history.append(best_menu["id"])
                
            # 採用した昼食・夕食を記録し、次回以降の被りを防ぐ
            used_meals.add(best_menu.get("昼食", ""))
            used_meals.add(best_menu.get("夕食", ""))

    return week