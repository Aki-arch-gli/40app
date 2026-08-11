import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin
import requests
import streamlit as st
from bs4 import BeautifulSoup

# =============================================================================
# 1. 地域イベント取得（西東京市公式HP）
# =============================================================================
NISHITOKYO_BASE = "https://www.city.nishitokyo.lg.jp"
EVENT_URL = NISHITOKYO_BASE + "/event/"

KEYWORDS = [
    "健康",
    "介護",
    "認知",
    "栄養",
    "糖尿病",
    "体操",
    "リハビリ",
    "運動",
    "フレイル",
    "ケア",
]


@st.cache_data(ttl=3600)
def get_local_events():
    """西東京市公式HPから健康・運動系イベント情報を取得"""
    events = []
    try:
        r = requests.get(EVENT_URL, timeout=8)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        links = soup.find_all("a")
        used = set()

        for a in links:
            title = a.get_text(" ", strip=True)
            if len(title) < 5 or not any(k in title for k in KEYWORDS):
                continue

            href = a.get("href")
            if not href:
                continue

            url = urljoin(NISHITOKYO_BASE, href)
            if title in used:
                continue
            used.add(title)

            events.append(
                {
                    "title": title,
                    "date": "近日開催",
                    "place": "西東京市（公民館・福祉センター等）",
                    "url": url,
                    "label": "🏃",
                    "comment": "健康・介護・運動に関する地域イベント",
                }
            )
    except Exception as e:
        print(f"イベント取得エラー: {e}")
        return []

    return events[:4]


# =============================================================================
# 2. 地域ニュース取得（号外NET RSSフィード完全対応）
# =============================================================================
GOGUYNET_FEED = "https://nishitokyo.goguynet.jp/feed/"


@st.cache_data(ttl=3600)
def get_local_news():
    """号外NET 西東京市のRSSフィードから確実にニュースを取得"""
    news_list = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(GOGUYNET_FEED, headers=headers, timeout=8)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall(".//item")

            for item in items:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pubDate_elem = item.find("pubDate")

                if title_elem is None or link_elem is None:
                    continue

                title = title_elem.text.strip() if title_elem.text else ""
                url = link_elem.text.strip() if link_elem.text else ""

                if not title or len(title) < 5:
                    continue

                # 日付のパース
                pub_date_str = "最近のニュース"
                if pubDate_elem is not None and pubDate_elem.text:
                    try:
                        # RFC 822 形式のパース (例: Mon, 10 Aug 2026 07:02:59 +0000)
                        raw_date = pubDate_elem.text
                        d_match = re.search(
                            r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", raw_date
                        )
                        if d_match:
                            day = d_match.group(1)
                            month_map = {
                                "Jan": "01",
                                "Feb": "02",
                                "Mar": "03",
                                "Apr": "04",
                                "May": "05",
                                "Jun": "06",
                                "Jul": "07",
                                "Aug": "08",
                                "Sep": "09",
                                "Oct": "10",
                                "Nov": "11",
                                "Dec": "12",
                            }
                            month = month_map.get(d_match.group(2), "01")
                            year = d_match.group(3)
                            pub_date_str = f"{year}年{month}月{day}日"
                    except Exception:
                        pass

                # エリアの判定
                place = "西東京市全域"
                if "保谷" in title or "東町" in title:
                    place = "保谷・東町エリア"
                elif "田無" in title:
                    place = "田無エリア"
                elif "ひばり" in title:
                    place = "ひばりヶ丘エリア"
                elif "東伏見" in title:
                    place = "東伏見エリア"
                elif "谷戸" in title:
                    place = "谷戸町エリア"

                news_list.append(
                    {
                        "title": title,
                        "date": pub_date_str,
                        "place": place,
                        "url": url,
                        "comment": "号外NET 西東京市",
                    }
                )

                if len(news_list) >= 4:
                    break
    except Exception as e:
        print(f"号外NET RSS取得エラー: {e}")

    return news_list