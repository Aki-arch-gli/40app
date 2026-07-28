from datetime import datetime


def greeting():

    hour = datetime.now().hour

    if hour < 12:
        return "おはようございます"

    elif hour < 18:
        return "こんにちは"

    else:
        return "こんばんは"