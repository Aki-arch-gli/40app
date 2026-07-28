import re


def create_simple_menu(menu_text):

    if menu_text is None:
        return ""

    simple = menu_text

    # あいさつ部分を削除
    remove_words = [
        "こんにちは。管理栄養士です。",
        "ご相談ありがとうございます。日本の管理栄養士です。"
    ]

    for word in remove_words:
        simple = simple.replace(word, "")

    # 「この献立の理由」以降を全部削除
    if "この献立の理由" in simple:
        simple = simple.split("この献立の理由")[0]

    if "【この献立の理由" in simple:
        simple = simple.split("【この献立の理由")[0]

    # 栄養バランス説明を削除
    simple = re.sub(
        r"【栄養バランス】.*?ポイント：.*?(?=■|🍽|$)",
        "",
        simple,
        flags=re.S
    )

    # 空行整理
    while "\n\n\n" in simple:
        simple = simple.replace("\n\n\n", "\n\n")

    simple = simple.replace("■ 朝食", "🌅 朝食")
    simple = simple.replace("■ 昼食", "🌞 昼食")
    simple = simple.replace("■ 夕食", "🌙 夕食")

    return simple.strip()