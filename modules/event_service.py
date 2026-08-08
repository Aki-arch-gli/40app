
"""
event_service.py

地域イベント取得サービス

役割
-------------------------
・DBからイベント取得
・必要に応じてスクレイピング更新
・おすすめイベント取得
・app.pyを軽量化
"""

from modules.database import (
    get_events,
    get_recommended_events
)

from modules.event_scraper import scrape_events


# ==================================================
# イベント一覧取得
# ==================================================

def load_events(limit=10):
    """
    DBからイベント取得
    """

    events = get_events(limit)

    if events is None:
        return []

    return events


# ==================================================
# おすすめイベント取得
# ==================================================

def load_recommended_events(limit=5):
    """
    おすすめイベント取得
    """

    events = get_recommended_events(limit)

    if events is None:
        return []

    return events


# ==================================================
# イベント更新
# ==================================================

def refresh_events():
    """
    イベント情報更新
    """

    try:

        events = scrape_events()

        return events

    except Exception as e:

        print(e)

        return []


# ==================================================
# 初回のみ更新
# ==================================================

def auto_refresh(session_state):
    """
    起動時に一度だけイベント更新
    """

    if not session_state.event_update:

        refresh_events()

        session_state.event_update = True


# ==================================================
# イベント取得（ホーム画面用）
# ==================================================

def get_home_events(session_state, limit=5):
    """
    ホーム画面表示用
    """

    auto_refresh(session_state)

    return load_recommended_events(limit)


# ==================================================
# 全イベント取得
# ==================================================

def get_all_events(session_state, limit=30):
    """
    一覧表示用
    """

    auto_refresh(session_state)

    return load_events(limit)