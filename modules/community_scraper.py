import requests
import streamlit as st

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from modules.event_parser import parse_event


BASE = "https://www.city.nishitokyo.lg.jp"
EVENT_PAGE = "/event/"


KEYWORDS = [

    "健康",
    "介護",
    "認知症",
    "フレイル",
    "栄養",
    "体操",
    "運動",
    "相談",
    "講座",
    "糖尿病",
    "高血圧",
    "リハビリ",
    "ウォーキング",
    "あるチャレ",
    "しゃきしゃき"

]


@st.cache_data(ttl=3600)
def scrape_events():

    session = requests.Session()

    try:

        r = session.get(
            BASE + EVENT_PAGE,
            timeout=8
        )

        r.encoding = "utf-8"

    except:
        return []

    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )

    candidates = []

    for a in soup.select("a"):

        title = a.get_text(" ", strip=True)

        href = a.get("href")

        print(title)

        if not href:
            continue

        if ".html" not in href:
            continue

        if "index.html" in href:
            continue

        if not any(k in title for k in KEYWORDS):
            continue

        url = urljoin(BASE, href)

        candidates.append(
            {
                "title": title,
                "url": url
            }
        )

    # 重複削除
    seen = set()

    unique = []

    for c in candidates:

        if c["url"] in seen:
            continue

        seen.add(c["url"])

        unique.append(c)

    # 最大5件だけ詳細取得
    events = []

    for c in unique[:5]:

        event = parse_event(c["url"])

        if event:

            events.append(event)

    events.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return events