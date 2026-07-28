from datetime import datetime

# --------------------------
# 残り日数計算
# --------------------------
def calc_remaining(expiry):

    today = datetime.today().date()
    expiry = datetime.strptime(expiry,"%Y-%m-%d").date()

    diff = (expiry-today).days

    return diff


# --------------------------
# 色判定
# --------------------------
def expiry_color(diff):

    if diff < 0:
        return "red"

    elif diff <=2:
        return "orange"

    else:
        return "green"


# --------------------------
# 表示用文字
# --------------------------
def expiry_text(diff):

    if diff < 0:
        return "❌期限切れ"

    elif diff==0:
        return "⚠今日まで"

    elif diff==1:
        return "⚠残り1日"

    else:
        return f"あと{diff}日"