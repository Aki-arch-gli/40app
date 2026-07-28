import re


def parse_ai_menu(text):

    if not text:
        return {}

    # HTMLタグ削除
    text = re.sub(
        r"<.*?>",
        "",
        text,
        flags=re.DOTALL
    )


    menu = {
        "朝食": "",
        "昼食": "",
        "夕食": ""
    }

    current = None


    for line in text.splitlines():

        line = line.strip()


        if not line:
            continue


        # 朝
        if "朝食" in line or "朝ごはん" in line:
            current = "朝食"
            continue


        # 昼
        if "昼食" in line or "昼ごはん" in line:
            current = "昼食"
            continue


        # 夜
        if (
            "夕食" in line
            or "夜ごはん" in line
            or "夕ご飯" in line
        ):
            current = "夕食"
            continue



        if (
            "理由" in line
            or "選んだ理由" in line
            or "この献立" in line
        ):
            break



        if current is None:
            continue



        # 不要文章削除
        if (
            "栄養" in line
            or "特徴" in line
            or "ポイント" in line
            or "タンパク質" in line
            or "たんぱく質" in line
            or "脂質" in line
            or "炭水化物" in line
        ):
            continue



        # kcal除外
        if re.search(
            r"\d+\s*kcal",
            line
        ):
            continue



        # 記号削除
        line = re.sub(
            r"^[\-\*\•◆]+",
            "",
            line
        ).strip()


        if line:

            if menu[current]:

                menu[current] += "\n" + line

            else:

                menu[current] = line



    return menu