import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.city.nishitokyo.lg.jp"

PAGES = [

    "/event/kenko_anzen/index.html",
    "/event/manabu_kangaeru/index.html",
    "/event/index.html"

]

KEYWORDS = {

    "認知症":50,
    "介護":45,
    "高齢":45,
    "フレイル":45,
    "包括":40,
    "栄養":35,
    "体操":35,
    "糖尿病":35,
    "高血圧":35,
    "リハビリ":35,
    "相談":30,
    "講座":25,
    "教室":20,
    "あるこ":50,
    "あるチャレ":60

}


def score_text(text):

    score = 0

    for k,v in KEYWORDS.items():

        score += text.count(k) * v

    return score


session = requests.Session()

urls = []

for page in PAGES:

    try:

        r = session.get(BASE+page)

        r.encoding="utf-8"

        soup = BeautifulSoup(r.text,"html.parser")

        for a in soup.select("a[href]"):

            href=a["href"]

            if ".html" not in href:
                continue

            if "index.html" in href:
                continue

            urls.append(urljoin(BASE,href))

    except:
        pass


urls=list(dict.fromkeys(urls))

events=[]

for url in urls[:30]:

    try:

        r=session.get(url)

        r.encoding="utf-8"

        soup=BeautifulSoup(r.text,"html.parser")

        title=soup.title.text.strip()

        text=soup.get_text("\n",strip=True)

        score=score_text(text)

        if score<40:
            continue

        m=re.search(r"\d{4}年\d+月\d+日",text)

        date=m.group() if m else ""

        place=""

        for line in text.split("\n"):

            if "場所" in line or "会場" in line:

                place=line[:40]

                break

        comment=text[:120]

        events.append({

            "title":title,
            "date":date,
            "place":place,
            "comment":comment,
            "score":score,
            "url":url

        })

    except:
        pass

events.sort(

    key=lambda x:x["score"],

    reverse=True

)

events=events[:5]

with open(

    "data/community_news.json",

    "w",

    encoding="utf-8"

) as f:

    json.dump(

        events,

        f,

        ensure_ascii=False,

        indent=4

)

print("保存完了")