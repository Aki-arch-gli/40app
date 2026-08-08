import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from modules.event_parser import parse_event
from modules.database import save_event

BASE_URL = "https://www.city.nishitokyo.lg.jp"
START_URL = "https://www.city.nishitokyo.lg.jp/enjoy/kouminkan/kouza_johou/index.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def get_html(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.encoding = r.apparent_encoding
    return r.text

def collect_links():
    event_links = set()
    sub_pages = set([START_URL])

    # 1. 各公民館のトップページ等を中間リンクとして収集
    try:
        html = get_html(START_URL)
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(START_URL, href)
            if "/kouza_johou/" in full_url and full_url.endswith(".html"):
                sub_pages.add(full_url)
    except Exception as e:
        print(f"Error reading START_URL: {e}")

    # 2. 中間ページから個別イベントページを抽出
    for page_url in sub_pages:
        try:
            html = get_html(page_url)
            soup = BeautifulSoup(html, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(page_url, href)

                if "/kouza_johou/" not in full_url:
                    continue

                # どんな階層であれ "index.html" で終わるリンクは施設一覧・目次ページなので除外する
                if full_url.endswith("/index.html") or full_url.endswith("index.html"):
                    continue

                event_links.add(full_url)

        except Exception as e:
            print(f"Error reading sub_page {page_url}: {e}")

    return sorted(list(event_links))


def scrape_events():
    events = []
    links = collect_links()

    for url in links:
        try:
            html = get_html(url)
            event = parse_event(html, url)
            event["url"] = url

            # タイトルと日時の両方が入っている正当なイベントのみDB保存対象にする
            if event.get("title") and event.get("datetime"):
                save_event(event)
                events.append(event)
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    return events