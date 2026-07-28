import matplotlib.pyplot as plt

def nutrition_chart(menu):

    protein = 0
    fat = 0
    salt = 0

    for meal in menu.values():

        protein += float(meal.get("タンパク質", 0))
        fat += float(meal.get("脂質", 0))
        salt += float(meal.get("塩分", 0))

    labels = [
        "Protein (g)",
        "Fat (g)",
        "Salt (g)"
    ]

    values = [
        protein,
        fat,
        salt
    ]

    fig, ax = plt.subplots(figsize=(6,4))

    ax.bar(labels, values)

    ax.set_title("Nutrition Balance")

    return fig