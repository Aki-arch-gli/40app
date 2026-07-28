def shopping_list(text):

    if "買い物リスト" not in text:

        return []

    part = text.split("買い物リスト")[-1]

    foods = []

    for line in part.splitlines():

        line = line.strip()

        if line:

            foods.append(line)

    return foods