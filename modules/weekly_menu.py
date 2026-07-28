from modules.menu_generator import generate_menu

def generate_weekly_menu(
    age,
    disease,
    calorie
):

    days = [
        "月曜日",
        "火曜日",
        "水曜日",
        "木曜日",
        "金曜日",
        "土曜日",
        "日曜日"
    ]

    week = {}

    history = []

    for day in days:

        menu = generate_menu(
            age=age,
            disease=disease,
            calorie=calorie,
            history=history
        )

        if menu:

            week[day] = menu

            history.append(menu["id"])

    return week