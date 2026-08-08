import json

from datetime import datetime

from modules.ai import generate_daily_news


def update_news():

    print("update_news開始")

    news = generate_daily_news()

    print(news)

    with open(
        "database/daily_news.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            news,
            f,
            ensure_ascii=False,
            indent=4
        )