import requests
import streamlit as st

from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE="https://www.city.nishitokyo.lg.jp"

URL=BASE+"/event/"

KEYWORDS=[

"健康",

"介護",

"認知",

"栄養",

"糖尿病",

"体操",

"リハビリ",

"運動",

"フレイル",

"ケア"

]

@st.cache_data(ttl=21600)

def get_local_news():

    events=[]

    try:

        r=requests.get(

            URL,

            timeout=8

        )

        r.encoding="utf-8"

        soup=BeautifulSoup(

            r.text,

            "html.parser"

        )

        links=soup.find_all("a")

        used=set()

        for a in links:

            title=a.get_text(

                " ",

                strip=True

            )

            if len(title)<5:

                continue

            if not any(

                k in title

                for k in KEYWORDS

            ):

                continue

            href=a.get("href")

            if not href:

                continue

            url=urljoin(

                BASE,

                href

            )

            if title in used:

                continue

            used.add(title)

            events.append({

                "title":title,

                "date":"近日開催",

                "place":"西東京市",

                "url":url,

                "label":"🏃",

                "comment":"健康・介護・運動に関するイベント"

            })

    except Exception:

        return []

    return events[:3]