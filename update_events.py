import pandas as pd
import streamlit as st

from modules.community_scraper import scrape_events


def update_events():

    events = scrape_events()

    if not events:
        return False

    df = pd.DataFrame(events)

    df.to_csv(
        "data/local_events.csv",
        index=False,
        encoding="utf-8-sig"
    )

    return True


if __name__ == "__main__":

    if update_events():
        print("更新完了")
    else:
        print("イベント取得失敗")