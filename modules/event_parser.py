from bs4 import BeautifulSoup
from urllib.parse import urljoin

def clean_text(text):
    if not text:
        return ""
    return (
        text.replace("\u3000", " ")
            .replace("\xa0", " ")
            .strip()
    )

def parse_event(html, url=""):
    soup = BeautifulSoup(html, "html.parser")

    event = {
        "title": "",
        "description": "",
        "datetime": "",
        "date": "",
        "time": "",
        "place": "",
        "target": "",
        "capacity": "",
        "fee": "",
        "teacher": "",
        "application": "",
        "contact": "",
        "images": [],
        "pdfs": [],
    }

    # -------------------------
    # タイトル
    # -------------------------
    h1 = soup.select_one("div.h1bg h1") or soup.select_one("h1")
    if h1:
        event["title"] = clean_text(h1.get_text())

    # イベントではないページ（施設名のみ、講座情報一覧、トップページなど）を弾く
    invalid_keywords = ["一覧", "トップページ", "公民館案内"]
    if any(kw in event["title"] for kw in invalid_keywords):
        event["title"] = ""
        return event

    # 単なる施設名（例: 「谷戸公民館」「芝久保公民館」）のみのタイトルを除外
    if event["title"].endswith("公民館") and len(event["title"]) <= 10:
        event["title"] = ""
        return event

    # -------------------------
    # h3bg の解析（とき、ところ、費用など）
    # -------------------------
    info = {}
    for h3bg in soup.select("div.h3bg"):
        h3 = h3bg.find("h3")
        if not h3:
            continue
        key = clean_text(h3.get_text())

        value_texts = []
        curr = h3bg.next_sibling
        while curr:
            if getattr(curr, "name", None) is None:
                curr = curr.next_sibling
                continue
            if curr.name in ["h2", "h3", "h4"] or "h3bg" in curr.get("class", []) or "h2bg" in curr.get("class", []):
                break
            t = clean_text(curr.get_text("\n", strip=True))
            if t:
                value_texts.append(t)
            curr = curr.next_sibling

        if value_texts:
            info[key] = "\n".join(value_texts)

    event["date"] = info.get("とき", info.get("日時", ""))
    event["time"] = info.get("時間", "")
    event["datetime"] = f"{event['date']} {event['time']}".strip()
    event["place"] = info.get("ところ", info.get("場所", ""))
    event["target"] = info.get("対象", "")
    event["capacity"] = info.get("定員", "")
    event["teacher"] = info.get("講師", "")
    event["fee"] = info.get("費用", info.get("材料費", ""))

    # 概要
    descriptions = []
    for wysi in soup.select("div.wysiwyg_wp"):
        if not wysi.find(["h2", "h3", "h4"]):
            t = clean_text(wysi.get_text(" ", strip=True))
            if t:
                descriptions.append(t)
    if descriptions:
        event["description"] = "\n".join(descriptions[:2])

    # 画像・PDF
    for img in soup.select("div.img-area img, div.img-area-l img"):
        src = img.get("src")
        if src and not src.startswith("/images/"):
            event["images"].append(urljoin(url, src))
    event["images"] = list(dict.fromkeys(event["images"]))

    for a in soup.select("a.pdf"):
        href = a.get("href")
        if href:
            event["pdfs"].append(urljoin(url, href))
    event["pdfs"] = list(dict.fromkeys(event["pdfs"]))

    return event