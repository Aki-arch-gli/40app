import streamlit as st
from datetime import datetime, date, timedelta
import datetime
import time
import random
import hashlib
import secrets
import os
import re
import json
import sqlite3
import threading
import pandas as pd
from zoneinfo import ZoneInfo
from PIL import Image
from cookies_manager import EncryptedCookiesManager

# ========= モジュール ==========
from modules.calorie import calculate_calories
from modules.bmi import calculate_bmi
from modules.database import (
    create_tables,
    add_user,
    update_point,
    get_ranking,
    get_user,
    add_post,
    get_posts,
    add_like,
    delete_post,
    add_health_record,
    get_health_records,
    add_favorite_menu,
    get_favorite_menus,
    add_favorite_weekly_menu,
    get_favorite_weekly_menus,
    get_menu_ranking,
    add_recommended_menu,
    add_food,
    get_foods,
    delete_food,
    get_menu_by_id,
    add_or_update_user,
    get_all_seniors,
    get_daily_task,
    save_daily_task,
    add_family_log,
    get_family_logs,
    add_family_comment,
    get_family_comments,
    get_posts_filtered
)
from modules.weekly_comment import weekly_comment
from modules.utils import greeting
from modules.weekly_pdf_export import export_weekly_pdf
from modules.menu_generator import generate_menu
from modules.weekly_menu import generate_weekly_menu
from modules.shopping import create_shopping_list
from modules.ai_comment import create_comment
from modules.nutrition_chart import nutrition_chart
from modules.pdf_export import export_pdf
from modules.voice import create_voice
from modules.recommended_card import recommended_card
from modules.health import health_record
from modules.ai import generate_ai_menu
from modules.weekly_card import weekly_card
from modules.ai_parser import parse_ai_menu
from modules.meal_card import meal_card
from modules.health_report import create_health_report
from modules.health_dashboard import create_dashboard_data
from modules.fridge_recipe import recommend_from_fridge
from modules.news import load_news
from modules.news_update import update_news
from modules.community_news import get_local_events, get_local_news
from modules.event_service import get_home_events, refresh_events

from supabase import create_client

# Secretsから接続情報を取得
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

# Supabaseクライアントの作成
supabase = create_client(url, key)

# ========= 補助関数 =========
def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def background_data_update():
    """バックグラウンドスレッドで外部更新処理を非同期実行"""
    try:
        refresh_events()
        update_news()
    except Exception:
        pass

def run_background_update_if_needed():
    """12時間に1回、バックグラウンドで更新処理を呼び出す"""
    last_update = st.session_state.get("last_background_update")
    now = datetime.datetime.now()
    
    if last_update is None or (now - last_update).total_seconds() > 3600 * 12:
        st.session_state.last_background_update = now
        thread = threading.Thread(target=background_data_update, daemon=True)
        thread.start()

run_background_update_if_needed()

@st.cache_data(ttl=3600*12, show_spinner=False)
def get_daily_events():
    json_path = os.path.join("data", "daily_events.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# 初回読み込み完了フラグの初期化
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    daily_events = get_daily_events()
    st.session_state.daily_events = daily_events
    st.session_state.data_loaded = True
else:
    daily_events = st.session_state.get("daily_events", [])

def generate_best_calorie_menu(age, disease, calorie, season="auto", style=None, difficulty=None, dislike=None, favorite_food=None, trials=10):
    best_menu = None
    min_diff = float("inf")
    
    for _ in range(trials):
        menu = generate_menu(
            age=age,
            disease=disease,
            calorie=calorie,
            season=season,
            style=style,
            difficulty=difficulty,
            dislike=dislike,
            favorite_food=favorite_food
        )
        if menu:
            menu_cal = menu.get("カロリー", calorie)
            diff = abs(menu_cal - calorie)
            if diff < min_diff:
                min_diff = diff
                best_menu = menu
            if min_diff <= 10:
                break

    if not best_menu and difficulty:
        for _ in range(trials):
            menu = generate_menu(
                age=age,
                disease=disease,
                calorie=calorie,
                season=season,
                style=style,
                difficulty=None,
                dislike=dislike,
                favorite_food=favorite_food
            )
            if menu:
                menu_cal = menu.get("カロリー", calorie)
                diff = abs(menu_cal - calorie)
                if diff < min_diff:
                    min_diff = diff
                    best_menu = menu

    if not best_menu:
        best_menu = generate_menu(
            age=age,
            disease=disease,
            calorie=calorie,
            season="auto"
        )

    return best_menu

# ========= 🛒 menu_txt完全準拠：強固な食材分解ユーティリティ =========
DISH_INGREDIENTS_MAP = {
    "ご飯": "米", "白ご飯": "米", "雑穀ご飯": "雑穀米", "玄米ご飯": "玄米", "全粒パン": "全粒粉パン",
    "納豆": "納豆, 長ねぎ", "納豆少量": "納豆", "冷奴": "豆腐, 生姜, 醤油", 
    "卵": "卵", "卵焼き": "卵, だし汁", "ヨーグルト": "プレーンヨーグルト", "牛乳": "牛乳",
    "味噌汁": "豆腐, わかめ, だし汁, 味味噌", "減塩味噌汁": "豆腐, 長ねぎ, 減塩味噌, だし汁", "野菜味噌汁": "キャベツ, 人参, 味噌",
    "野菜スープ": "キャベツ, 玉ねぎ, 人参, コンソメ",
    "果物": "季節の果物", "バナナ": "バナナ", "いちご": "いちご", "りんご": "りんご", 
    "柿": "柿", "梨": "梨", "桃": "桃", "みかん": "みかん",
    "鶏むね肉の照り焼き": "鶏むね肉, 醤油, みりん", "鶏肉の照り焼き": "鶏もも肉, 醤油, みりん",
    "鶏むね肉の冷しゃぶ": "鶏むね肉, レタス, きゅうり, ポン酢", "鶏むね肉の蒸し料理": "鶏むね肉, 酒, 塩",
    "鶏むね肉の蒸し焼き": "鶏むね肉, キャベツ, 醤油", "鶏むね肉料理": "鶏むね肉, 玉ねぎ",
    "鶏むね肉と野菜の煮物": "鶏むね肉, 人参, 大根, 醤油",
    "鶏ささみサラダ": "鶏ささみ, レタス, きゅうり, トマト", "鶏ささみ丼": "鶏ささみ, 卵, 玉ねぎ, 米",
    "鶏ささみ料理": "鶏ささみ, 大葉, ポン酢",
    "鶏肉ときのこの炒め物": "鶏肉, しめじ, エリンギ, 醤油", "鶏肉ときのこの煮物": "鶏肉, 椎茸, しめじ, だし汁",
    "鶏肉ときのこの料理": "鶏肉, まいたけ, 醤油",
    "鶏肉と白菜の煮物": "鶏肉, 白菜, 人参, だし汁", "鶏肉と白菜料理": "鶏肉, 白菜, 長ねぎ", "鶏肉と白菜の煮込み": "鶏肉, 白菜, 生姜",
    "鶏肉と根菜の煮物": "鶏肉, ごぼう, れんこん, 人参", "鶏肉と根菜料理": "鶏肉, ごぼう, 人参",
    "鶏肉と根菜の煮込み": "鶏肉, れんこん, 大根",
    "鶏肉と春野菜の煮物": "鶏肉, たけのこ, 菜の花, だし汁", "鶏肉と春野菜の炒め物": "鶏肉, アスパラガス, キャベツ",
    "鶏肉と春野菜の蒸し料理": "鶏肉, 春キャベツ, 新玉ねぎ", "鶏肉と春野菜料理": "鶏肉, 菜の花, 春キャベツ",
    "鶏肉と野菜の煮物": "鶏肉, 人参, だし汁, 醤油", "鶏肉と野菜炒め": "鶏肉, キャベツ, ピーマン, 醤油",
    "鶏肉と野菜の炒め物": "鶏肉, もやし, 人参, 醤油", "鶏肉と野菜鍋": "鶏肉, 白菜, 長ねぎ, だし汁",
    "鶏肉の煮物": "鶏肉, 大根, 人参, 醤油", "鶏肉のグリル": "鶏肉, 塩, 胡椒", "鶏肉グリル": "鶏肉, 塩, 胡椒",
    "鶏肉のトマト煮": "鶏肉, トマト缶, 玉ねぎ, ニンニク", "鶏肉トマト煮": "鶏肉, トマト缶, 玉ねぎ",
    "鶏肉の南蛮風": "鶏肉, 玉ねぎ, 酢, 醤油, 砂糖", "鶏肉の蒸し料理": "鶏肉, 長ねぎ, 生姜",
    "鶏肉少量と野菜の煮物": "鶏肉, 人参, 椎茸, だし汁", "鶏肉少量料理": "鶏肉, 大根", "鶏肉料理": "鶏肉, 玉ねぎ, 醤油",
    "チキンソテー": "鶏むね肉, オリーブオイル, 塩",
    "豚しゃぶサラダ": "豚薄切り肉, レタス, きゅうり, ポン酢", "豚しゃぶ": "豚薄切り肉, もやし, ポン酢",
    "豚しゃぶおろしサラダ": "豚薄切り肉, 大根おろし, レタス, ポン酢", "豚しゃぶ野菜サラダ": "豚薄切り肉, トマト, 水菜",
    "豚肉と白菜の煮物": "豚コマ肉, 白菜, 長ねぎ, だし汁", "豚肉と白菜の煮込み": "豚コマ肉, 白菜, 生姜",
    "豚肉と白菜料理": "豚肉, 白菜, だし汁", "豚肉と白菜の鍋料理": "豚薄切り肉, 白菜, 豆腐, だし汁",
    "豚肉と夏野菜炒め": "豚肉, ナス, ピーマン, トマト, 醤油", "豚肉と野菜の炒め物": "豚肉, キャベツ, もやし, 人参, 醤油",
    "豚肉と野菜炒め": "豚肉, ピーマン, 玉ねぎ, 醤油", "豚肉と野菜の煮物": "豚肉, じゃがいも, 人参, 醤油",
    "豚肉と野菜料理": "豚肉, 玉ねぎ, 人参", "豚肉と根菜の煮物": "豚肉, ごぼう, れんこん, 人参",
    "豚肉と根菜料理": "豚肉, 大根, ごぼう", "豚肉と春野菜の炒め物": "豚肉, 春キャベツ, 新玉ねぎ",
    "豚肉と春野菜炒め": "豚肉, アスパラガス, 醤油",
    "豚汁": "豚肉, 大根, 人参, ごぼう, 長ねぎ, 味噌", "豚汁（薄味）": "豚肉, 大根, 人参, 長ねぎ, 減塩味噌",
    "豚肉少量の野菜炒め": "豚肉, キャベツ, もやし", "豚肉少量の白菜煮": "豚肉, 白菜, だし汁",
    "豚肉少量の白菜料理": "豚肉, 白菜", "豚肉少量の煮物": "豚肉, 大根, 人参",
    "豚肉少量の冷しゃぶ": "豚肉, きゅうり, ポン酢", "豚肉少量料理": "豚肉, 玉ねぎ",
    "豚しゃぶ野菜料理": "豚薄切り肉, キャベツ, ポン酢", "豚肉料理": "豚肉, 玉ねぎ, 醤油",
    "鮭の塩焼き": "生鮭, 塩", "鮭の焼き物": "生鮭, 塩", "鮭のホイル焼き": "生鮭, しめじ, 玉ねぎ, バター",
    "鮭鍋": "鮭切り身, 白菜, 長ねぎ, 豆腐, だし汁", "鮭料理": "鮭, 醤油",
    "さばの塩焼き": "真鯖, 塩", "さばの味噌煮": "真鯖, 生姜, 味噌, 醤油", "さばの焼き物": "真鯖, 塩",
    "さんまの塩焼き": "さんま, 塩, 大根おろし", "さんまの焼き物": "さんま, 塩", "さんま料理": "さんま, 醤油",
    "あじの焼き物": "あじ, 塩", "あじの南蛮焼き": "あじ, 玉ねぎ, 酢, 醤油", "あじの南蛮漬け": "あじ, 人参, 玉ねぎ, 酢",
    "さわらの焼き物": "さわら, 塩", "ぶり大根": "ブリ切り身, 大根, 生姜, 醤油",
    "たら鍋": "たら切り身, 白菜, 長ねぎ, 豆腐, 昆布", "たら鍋風料理": "たら切り身, 豆腐, 白菜",
    "たらの湯豆腐": "たら切り身, 豆腐, 昆布, ポン酢", "たらの煮付け": "たら切り身, 生姜, 醤油, みりん",
    "たらの焼き物": "たら切り身, 塩", "たらの蒸し料理": "たら切り身, 長ねぎ, ポン酢", "たら料理": "たら切り身, 塩",
    "白身魚の塩焼き": "たら切り身, 塩", "白身魚の煮付け": "たら切り身, 生姜, 醤油", "白身魚の焼き物": "鯛切り身, 塩",
    "白身魚の蒸し料理": "白身魚, 長ねぎ, ポン酢", "白身魚グリル": "白身魚, オリーブオイル, 塩",
    "白身魚料理": "白身魚, 醤油", "魚料理": "旬の魚切り身, 塩",
    "親子丼": "鶏肉, 卵, 玉ねぎ, だし汁, 米", "豆腐ハンバーグ": "豆腐, 鶏ひき肉, 玉ねぎ, パン粉",
    "野菜サラダ": "レタス, きゅうり, トマト", "春野菜サラダ": "春キャベツ, アスパラガス, 新玉ねぎ",
    "夏野菜サラダ": "トマト, きゅうり, ナス", "きのことサラダ": "しめじ, レタス, トマト", "サラダ": "レタス, きゅうり",
    "ほうれん草のおひたし": "ほうれん草, 醤油, かつお節", "小松菜のおひたし": "小松菜, だし汁, 醤油",
    "小松菜のお浸し": "小松菜, だし汁", "オクラのおひたし": "オクラ, だし汁, 醤油", "小松菜料理": "小松菜, 油揚げ",
    "ひじき煮": "ひじき, 人参, 油揚げ, だし汁, 醤油", "野菜煮物": "大根, 人参, ごぼう, だし汁",
    "夏野菜料理": "ナス, ピーマン, トマト", "根菜料理": "ごぼう, れんこん, 人参", "根菜サラダ": "ごぼう, 人参, マヨネーズ",
    "温野菜": "ブロッコリー, 人参, じゃがいも", "豆腐料理": "豆腐, 長ねぎ, 醤油", "豆類料理": "大豆, ひじき, 人参",
    "海藻料理": "わかめ, ひじき, 酢", "わかめ煮": "わかめ, 出汁, 醤油", "わかめ料理": "わかめ, きゅうり"
}

def get_ingredients_enhanced(text):
    if not text:
        return ["季節の野菜", "豆腐", "魚・お肉"]

    matched_ingredients = []
    sorted_dishes = sorted(DISH_INGREDIENTS_MAP.keys(), key=len, reverse=True)
    
    for dish in sorted_dishes:
        if dish in text:
            ings = DISH_INGREDIENTS_MAP[dish].split(",")
            for ing in ings:
                cleaned_ing = ing.strip()
                if cleaned_ing and cleaned_ing not in matched_ingredients:
                    matched_ingredients.append(cleaned_ing)

    if not matched_ingredients:
        delimiters = ["・", "、", " ", " ", "\n", "＆", "&", "の", "風", "炒め", "焼き", "煮", "和え", "添え"]
        for d in delimiters:
            text = text.replace(d, ",")
            
        raw_list = [x.strip() for x in text.split(",") if x.strip()]
        
        exclude_keywords = [
            "定食", "セット", "丼", "サラダ", "汁", "御飯", "ご飯", "おやき", "スープ", 
            "減塩", "風", "メニュー", "朝食", "昼食", "夕食", "本日の", "最適", "料理", "グリル"
        ]
        
        for item in raw_list:
            if not any(item.endswith(kw) or item == kw for kw in exclude_keywords) and len(item) >= 1:
                matched_ingredients.append(item)

    unique_items = list(dict.fromkeys(matched_ingredients))
    return unique_items if unique_items else ["キャベツ", "レタス", "トマト", "豆腐", "魚・肉"]

IMAGE_MAPPING = [
    (r"パン|トースト|サンドイッチ|ロールパン", "assets/breakfast_western.jpg"),
    (r"雑穀|ご飯|ごはん|おにぎり|のり|梅干し|納豆|粥|かゆ", "assets/breakfast_japanese.jpg"),
    (r"親子丼|牛丼|豚丼|カツ丼|天丼|丼", "assets/rice_grain.jpg"),
    (r"鶏|チキン|鳥|から揚げ|唐揚げ|照り焼き", "assets/chicken_dish.jpg"),
    (r"豚|ポーク|しゃぶしゃぶ|豚汁|生姜焼き|カツ", "assets/pork_dish.jpg"),
    (r"鍋|水炊き|すき焼き|煮込み", "assets/pot_dish.jpg"),
    (r"ホイル焼き|煮魚|照り煮|さばのみそ煮|カレイ|煮付け", "assets/fish_simmered.jpg"),
    (r"魚|鮭|サケ|塩焼き|ムニエル|フライ|刺身|ツナ", "assets/fish_grilled.jpg"),
    (r"みそ汁|味噌汁|スープ|お吸い物|汁", "assets/soup_miso.jpg"),
    (r"サラダ|あえもの|和え物|おひたし|ひじき|きんぴら|野菜", "assets/salad_vegetable.jpg"),
    (r"冷奴|豆腐|高野豆腐|湯豆腐|厚揚げ|おから", "assets/tofu_dish.jpg"),
]

DEFAULT_IMAGE_PATH = "assets/default.jpg"

def get_menu_image_path(menu_text: str) -> str:
    if not menu_text:
        return DEFAULT_IMAGE_PATH

    for pattern, img_path in IMAGE_MAPPING:
        if re.search(pattern, menu_text):
            if os.path.exists(img_path):
                return img_path

    return (
        DEFAULT_IMAGE_PATH
        if os.path.exists(DEFAULT_IMAGE_PATH)
        else None
    )

def display_resized_menu_image(img_path: str, caption: str = "", max_width: int = 300):
    if img_path and os.path.exists(img_path):
        try:
            image = Image.open(img_path)
            image.thumbnail((max_width, max_width))
            st.image(image, caption=caption, use_container_width=False)
        except Exception:
            st.write("🖼️ (画像読み込みエラー)")
    else:
        st.write("🍽️")

UPLOAD_SENIOR_DIR = os.path.join("uploads", "seniors")
UPLOAD_STUDENT_DIR = os.path.join("uploads", "students")

os.makedirs(UPLOAD_SENIOR_DIR, exist_ok=True)
os.makedirs(UPLOAD_STUDENT_DIR, exist_ok=True)

def speak_text(text: str):
    if not text: return
    clean_text = text.replace("\n", " ").replace("'", "\\'").replace('"', '\\"')
    js_code = f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{clean_text}');
            msg.lang = 'ja-JP';
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        }}
    </script>
    """
    st.components.v1.html(js_code, height=0)

def display_safe_image(img_path: str, caption: str = "", fallback_emoji: str = "🍲"):
    if img_path and os.path.exists(img_path):
        st.image(img_path, caption=caption, use_container_width=True)
    else:
        st.markdown(f"""
        <div style="background-color:#E8F5E9; border:2px dashed #2E7D32; padding:25px; border-radius:12px; text-align:center;">
            <span style="font-size:42px;">{fallback_emoji}</span><br>
            <b style="color:#1B5E20; font-size:16px;">{caption if caption else '料理イメージ'}</b>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 🌱 40〜60代向け「未来の健康をつくる」アプリ
# 旧「高齢者・施設・家族」向け機能を整理し、年齢による画面分岐を廃止。
# 年齢はカロリー/BMI等の健康計算にのみ利用します。
# ============================================================

st.set_page_config(
    page_title="未来の健康習慣AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

create_tables()

@st.cache_resource
def init_local_db():
    conn = sqlite3.connect("app_data.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS daily_stamps (
        user_id TEXT, date TEXT, action_type TEXT,
        PRIMARY KEY(user_id, date, action_type)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS genki_status (
        user_id TEXT, date TEXT, timestamp TEXT,
        PRIMARY KEY(user_id, date)
    )""")
    conn.commit()
    conn.close()

init_local_db()

# -----------------------------
# セッション初期値
# -----------------------------
DEFAULT_SESSION = {
    "is_logged_in": False,
    "is_auto_logged_in": False,
    "is_guest_mode": False,
    "user_id": None,
    "user_code": "",
    "current_page": "🏠 ホーム",
    "senior_fullname": "ゲスト",
    "senior_age": 50,
    "senior_gender": "未回答",
    "senior_height": 165.0,
    "senior_weight": 60.0,
    "senior_disease": "なし",
    "user_role": "一般",
    "recommended_menu": None,
    "weekly_menu": None,
    "fav_daily_menus": [],
    "fav_weekly_menus": [],
    "water_today": 0,
    "walk_steps": 0,
    "sleep_hours": 7.0,
    "mood_today": "普通",
    "genki_point": 0,
    "continue_days": 0,
    "dislike_foods": [],
    "favorite_food_type": "指定なし",
    "preferred_style": None,
    "preferred_difficulty": None,
    "preferred_season": "auto",
    "tutorial_finished": True,
    "dark_mode": False,
    "voice_enabled": True,
    "show_detail": False,
    "last_background_update": st.session_state.get("last_background_update"),
}
for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 旧データ/旧アカウントでログインしても「役割」による画面分岐はしない
st.session_state.user_role = "一般"

# -----------------------------
# 認証
# -----------------------------
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def register_user_db(username, password, age, gender, height, weight, disease):
    try:
        sb = get_supabase()
        pwd_hash = hash_pass(password)
        u_code = secrets.token_hex(3).upper()
        data = {
            "username": username.strip(),
            "password_hash": pwd_hash,
            "role": "一般",
            "age": int(age),
            "gender": gender,
            "height": float(height),
            "weight": float(weight),
            "disease": disease,
            "user_code": u_code,
        }
        sb.table("app_users").insert(data).execute()
        add_or_update_user(
            username.strip(), "一般", int(age), gender,
            float(height), float(weight), "普通", disease, "一般"
        )
        return True, u_code
    except Exception as e:
        msg = str(e)
        if "duplicate" in msg.lower() or "unique" in msg.lower():
            return False, "このユーザーIDはすでに使われています。"
        if "getaddrinfo" in msg.lower():
            return False, "ネットワーク接続を確認してください。"
        return False, f"登録エラー: {msg}"

def authenticate_user_db(username, password):
    try:
        sb = get_supabase()
        pwd_hash = hash_pass(password)
        res = (
            sb.table("app_users")
            .select("*")
            .eq("username", username.strip())
            .eq("password_hash", pwd_hash)
            .execute()
        )
        if res.data:
            u = res.data[0]
            return (
                u.get("username", username.strip()),
                u.get("age", 50),
                u.get("gender", "未回答"),
                u.get("height", 165.0),
                u.get("weight", 60.0),
                u.get("disease", "なし"),
                u.get("user_code", ""),
            )
    except Exception as e:
        print(f"Login Error: {e}")
    return None

cookies_pwd = st.secrets.get("COOKIES_PASSWORD", "change-this-in-streamlit-secrets")
cookies = EncryptedCookiesManager(prefix="health-habit-app", password=cookies_pwd)

if not cookies.ready():
    st.stop()

# 自動ログイン
if not st.session_state.is_logged_in and not st.session_state.is_guest_mode:
    saved_username = cookies.get("saved_username")
    if saved_username:
        try:
            sb = get_supabase()
            res = sb.table("app_users").select("*").eq("username", saved_username).execute()
            if res.data:
                u = res.data[0]
                st.session_state.is_logged_in = True
                st.session_state.senior_fullname = u.get("username", saved_username)
                st.session_state.senior_age = int(u.get("age", 50) or 50)
                st.session_state.senior_gender = u.get("gender", "未回答")
                st.session_state.senior_height = float(u.get("height", 165) or 165)
                st.session_state.senior_weight = float(u.get("weight", 60) or 60)
                st.session_state.senior_disease = u.get("disease", "なし")
                st.session_state.user_code = u.get("user_code", "")
                st.session_state.user_id = u.get("username", saved_username)
                st.session_state.user_role = "一般"
                st.session_state.is_auto_logged_in = True
                st.rerun()
        except Exception:
            pass

if not st.session_state.is_logged_in and not st.session_state.is_guest_mode:
    st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
    st.markdown("<h1>🌱 未来の健康習慣AI</h1>", unsafe_allow_html=True)
    st.markdown("### 今の小さな習慣が、未来の自分をつくる。")
    st.write("40〜60代の毎日に寄り添い、食事・運動・睡眠などの健康習慣を無理なく続けるためのアプリです。")
    st.markdown("</div>", unsafe_allow_html=True)

    login_tab, register_tab = st.tabs(["🔑 ログイン", "✨ はじめて使う"])
    with login_tab:
        with st.form("login_form"):
            l_name = st.text_input("ユーザーID")
            l_pass = st.text_input("パスワード", type="password")
            remember = st.checkbox("次回から自動ログイン", value=True)
            submit = st.form_submit_button("ログイン", use_container_width=True, type="primary")
            if submit:
                if not l_name.strip() or not l_pass.strip():
                    st.warning("ユーザーIDとパスワードを入力してください。")
                else:
                    info = authenticate_user_db(l_name, l_pass)
                    if info:
                        (
                            name, age, gender, height, weight, disease, code
                        ) = info
                        st.session_state.is_logged_in = True
                        st.session_state.is_guest_mode = False
                        st.session_state.user_id = name
                        st.session_state.senior_fullname = name
                        st.session_state.senior_age = int(age or 50)
                        st.session_state.senior_gender = gender or "未回答"
                        st.session_state.senior_height = float(height or 165)
                        st.session_state.senior_weight = float(weight or 60)
                        st.session_state.senior_disease = disease or "なし"
                        st.session_state.user_code = code or ""
                        st.session_state.user_role = "一般"
                        if remember:
                            cookies["saved_username"] = name
                            cookies.save()
                        st.success("ログインしました。")
                        st.rerun()
                    else:
                        st.error("ユーザーIDまたはパスワードが正しくありません。")

    with register_tab:
        with st.form("register_form"):
            r_name = st.text_input("ユーザーID / お名前")
            r_pass = st.text_input("パスワード", type="password")
            r_age = st.number_input("年齢", min_value=40, max_value=69, value=50, step=1)
            r_gender = st.radio("性別", ["女性", "男性", "未回答"], horizontal=True)
            r_height = st.number_input("身長 (cm)", min_value=120.0, max_value=220.0, value=165.0, step=0.5)
            r_weight = st.number_input("体重 (kg)", min_value=30.0, max_value=150.0, value=60.0, step=0.5)
            disease_options = ["なし", "高血圧", "糖尿病", "腎臓病", "脂質異常症", "骨粗しょう症", "心疾患"]
            r_disease = st.selectbox("健康上、食事で配慮したいこと", disease_options)
            agree = st.checkbox("健康管理の補助を目的としたサービスであることを理解しました。")
            submit_reg = st.form_submit_button("アカウントを作成", use_container_width=True, type="primary")
            if submit_reg:
                if not r_name.strip() or not r_pass.strip():
                    st.warning("ユーザーIDとパスワードを入力してください。")
                elif not agree:
                    st.warning("確認欄にチェックを入れてください。")
                else:
                    ok, result = register_user_db(
                        r_name, r_pass, r_age, r_gender, r_height, r_weight, r_disease
                    )
                    if ok:
                        st.success("アカウントを作成しました。ログインしてください。")
                        st.info(f"ユーザーコード: `{result}`")
                    else:
                        st.error(result)

    st.divider()
    if st.button("👀 ログインせずにアプリを見てみる", use_container_width=True):
        st.session_state.is_guest_mode = True
        st.session_state.senior_fullname = "ゲスト"
        st.session_state.user_id = "guest"
        st.rerun()
    st.stop()

# -----------------------------
# ゲスト/ユーザー情報の読み込み
# -----------------------------
user_id = st.session_state.user_id or "guest"
username = st.session_state.senior_fullname

if st.session_state.is_logged_in:
    try:
        db_user = get_user(username)
        if db_user:
            if isinstance(db_user, dict):
                if db_user.get("user_code"):
                    st.session_state.user_code = str(db_user["user_code"])
                if db_user.get("point") is not None:
                    st.session_state.genki_point = int(db_user["point"])
            elif isinstance(db_user, tuple):
                if len(db_user) > 8 and db_user[8] is not None:
                    st.session_state.genki_point = int(db_user[8])
    except Exception:
        pass

# -----------------------------
# 共通ユーティリティ
# -----------------------------
today_str = str(date.today())

def get_today_stamps():
    try:
        conn = sqlite3.connect("app_data.db")
        rows = conn.execute(
            "SELECT action_type FROM daily_stamps WHERE user_id=? AND date=?",
            (user_id, today_str)
        ).fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:
        return []

def add_stamp(action_name, points=0):
    try:
        conn = sqlite3.connect("app_data.db")
        conn.execute(
            "INSERT OR IGNORE INTO daily_stamps VALUES (?, ?, ?)",
            (user_id, today_str, action_name)
        )
        conn.commit()
        conn.close()
        if points:
            try:
                update_point(username, points)
            except Exception:
                pass
            st.session_state.genki_point += points
        st.toast(f"✨ {action_name}" + (f" +{points}pt" if points else ""))
    except Exception:
        pass

def calculate_health_score():
    """診断ではなく、今日の習慣を可視化する0〜100点の目安。"""
    score = 50
    steps = int(st.session_state.get("walk_steps", 0))
    water = int(st.session_state.get("water_today", 0))
    sleep = float(st.session_state.get("sleep_hours", 7))
    mood = st.session_state.get("mood_today", "普通")
    if steps >= 6000:
        score += 15
    elif steps >= 3000:
        score += 8
    if water >= 1500:
        score += 15
    elif water >= 1000:
        score += 8
    if 6.5 <= sleep <= 8.5:
        score += 12
    elif 5.5 <= sleep < 6.5 or 8.5 < sleep <= 9.5:
        score += 5
    if mood == "良い":
        score += 8
    elif mood == "普通":
        score += 4
    return max(0, min(100, score))

def coach_message():
    score = calculate_health_score()
    steps = int(st.session_state.get("walk_steps", 0))
    water = int(st.session_state.get("water_today", 0))
    sleep = float(st.session_state.get("sleep_hours", 7))
    if water < 1000:
        return "今日はまず水分を1杯。小さな行動から始めましょう。"
    if steps < 3000:
        return "あと少し歩くだけでも十分です。10分だけ外に出てみませんか？"
    if sleep < 6.5:
        return "今日は睡眠を少し優先してみましょう。寝る前は画面を早めに切り上げるのがおすすめです。"
    if score >= 80:
        return "いい流れです。完璧を目指さず、この習慣を明日も続けていきましょう。"
    return "今日できたことを1つ見つければ十分。無理なく続けることが健康づくりのコツです。"

def save_health_today(weight, systolic, diastolic, water, sleep, steps):
    try:
        # 既存DBのadd_health_record仕様に合わせる
        add_health_record(
            username, today_str, float(weight), int(systolic), int(diastolic),
            int(water), 1, int(round(float(sleep) * 10))
        )
        st.session_state.senior_weight = float(weight)
        st.session_state.water_today = int(water)
        st.session_state.sleep_hours = float(sleep)
        st.session_state.walk_steps = int(steps)
        return True, ""
    except Exception as e:
        return False, str(e)

def current_season():
    m = date.today().month
    if m in (3, 4, 5): return "春"
    if m in (6, 7, 8): return "夏"
    if m in (9, 10, 11): return "秋"
    return "冬"

def safe_event_link(url, label="詳細を見る"):
    if url:
        st.markdown(f"[🔗 {label}]({url})")

def display_health_record_table(records):
    if not records:
        st.info("まだ記録がありません。今日から少しずつ残してみましょう。")
        return
    rows = []
    for r in records:
        if isinstance(r, dict):
            rows.append(r)
        else:
            rows.append({
                "日付": r[0] if len(r)>0 else "",
                "体重(kg)": r[1] if len(r)>1 else "",
                "収縮期": r[2] if len(r)>2 else "",
                "拡張期": r[3] if len(r)>3 else "",
                "水分(ml)": r[4] if len(r)>4 else "",
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# -----------------------------
# CSS
# -----------------------------
dark_mode = st.session_state.dark_mode
if dark_mode:
    bg = "#111827"; card = "#1F2937"; text = "#F9FAFB"; muted = "#D1D5DB"
else:
    bg = "#F7FAF7"; card = "#FFFFFF"; text = "#17221A"; muted = "#526158"

st.markdown(f"""
<style>
.stApp {{ background:{bg}; }}
.stMarkdown, .stText, p, label, span, li {{ color:{text}; }}
h1,h2,h3 {{ color:#176B3A !important; font-weight:800 !important; }}
.hero {{
    background:linear-gradient(135deg,#E8F5E9,#F1F8E9);
    border-radius:20px; padding:26px; margin-bottom:20px;
    border:1px solid #C8E6C9;
}}
.card {{
    background:{card}; border:1px solid #D9E4DB; border-radius:16px;
    padding:20px; margin-bottom:14px;
}}
.small-muted {{ color:{muted} !important; font-size:0.92rem; }}
.score {{
    font-size:46px; font-weight:900; color:#2E7D32;
}}
div[data-testid="stButton"] > button {{
    border-radius:12px; min-height:48px; font-weight:700;
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# サイドバー
# -----------------------------
st.sidebar.title("🌱 未来の健康習慣AI")
if st.session_state.is_logged_in:
    st.sidebar.success(f"👤 {username} さん")
else:
    st.sidebar.info("👀 お試しモード")

st.sidebar.markdown("### 今日の健康")
st.sidebar.metric("健康習慣スコア", f"{calculate_health_score()} / 100")
st.sidebar.metric("ポイント", f"{st.session_state.genki_point} pt")

st.sidebar.divider()
st.session_state.dark_mode = st.sidebar.toggle("🌙 ダークモード", value=st.session_state.dark_mode)
st.session_state.voice_enabled = st.sidebar.toggle("🔊 音声案内", value=st.session_state.voice_enabled)

if st.session_state.is_logged_in:
    if st.sidebar.button("🚪 ログアウト", use_container_width=True):
        try:
            if "saved_username" in cookies:
                del cookies["saved_username"]
                cookies.save()
        except Exception:
            pass
        st.session_state.is_logged_in = False
        st.session_state.is_auto_logged_in = False
        st.session_state.user_id = None
        st.session_state.current_page = "🏠 ホーム"
        st.rerun()

# -----------------------------
# ナビゲーション
# -----------------------------
nav_config = [
    ("🏠 ホーム", "今日の健康"),
    ("🌱 健康チェック", "記録・振り返り"),
    ("🍳 食事アイデア", "食べ方・レシピ"),
    ("🧠 楽しむ・つながる", "脳トレ・地域"),
    ("⚙️ 設定", "プロフィール"),
]
cols = st.columns(5)
for i, (target, sub) in enumerate(nav_config):
    with cols[i]:
        if st.button(target, key=f"nav_{i}", use_container_width=True):
            st.session_state.current_page = target
            st.rerun()

page = st.session_state.current_page

if st.session_state.is_guest_mode and page not in ("🏠 ホーム", "🍳 食事アイデア"):
    st.info("👀 お試しモードではホームと食事アイデアを体験できます。健康記録・交流を保存するにはログインしてください。")
    if st.button("🔑 ログインする"):
        st.session_state.is_guest_mode = False
        st.rerun()
    st.stop()

# ============================================================
# 🏠 ホーム
# ============================================================

# ============================================================
# 🧠 1分脳トレ / 共通アクション
# ============================================================
QUIZ_DATABASE = [
    {
        "q": "日本で一番高い山は富士山ですが、2番目に高い山はどこでしょう？",
        "options": ["北岳（南アルプス）", "槍ヶ岳", "立山"],
        "ans": "北岳（南アルプス）",
        "fact": "北岳は山梨県にあり、標高3,193mです。"
    },
    {
        "q": "「秋なすは嫁に食わすな」ということわざについて、代表的な由来はどれでしょう？",
        "options": ["身体が冷えてしまうから", "美味しすぎるから", "収穫が少ないから"],
        "ans": "身体が冷えてしまうから",
        "fact": "秋なすには体を冷やす性質があると考えられたことが、由来の一説です。"
    },
    {
        "q": "食事のときによく噛むことについて、期待されることはどれでしょう？",
        "options": ["食べ過ぎを防ぎやすい", "必ず血圧が下がる", "必ず睡眠時間が増える"],
        "ans": "食べ過ぎを防ぎやすい",
        "fact": "よく噛むと食事に時間がかかり、満腹感を得やすくなるとされています。"
    },
    {
        "q": "笑うことと健康について、一般的に知られているものはどれでしょう？",
        "options": ["気分転換につながる", "必ず病気を治す", "必ず血圧を正常にする"],
        "ans": "気分転換につながる",
        "fact": "笑うことは気分転換やストレス軽減のきっかけになります。"
    },
]

day_seed = int(date.today().strftime("%Y%m%d"))
quiz_rng = random.Random(day_seed)
today_quiz = quiz_rng.choice(QUIZ_DATABASE)

def trigger_action(sound=True, speak_text=""):
    """ボタン操作後の効果音・音声読み上げを予約する。"""
    if sound:
        st.session_state["play_sound"] = True
    if speak_text:
        st.session_state["tts_text"] = str(speak_text)

if page == "🏠 ホーム":
    score = calculate_health_score()
    st.markdown(f"""
    <div class="hero">
      <h1>🌱 {greeting()}、{username}さん</h1>
      <p>今の小さな習慣が、未来の自分をつくります。</p>
      <div class="score">{score}<span style="font-size:20px;"> / 100</span></div>
      <p>今日の健康習慣スコア</p>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🚶 歩数", f"{st.session_state.walk_steps:,} 歩", "目標 6,000")
    c2.metric("💧 水分", f"{st.session_state.water_today:,} ml", "目安 1,500")
    c3.metric("😴 睡眠", f"{st.session_state.sleep_hours:.1f} h")
    c4.metric("😊 気分", st.session_state.mood_today)

    st.subheader("🤖 今日のAI健康コーチ")
    st.info(coach_message())
    st.caption("※健康習慣を考えるための一般的なアドバイスです。診断・治療の代替ではありません。")

    st.subheader("✅ 今日の3つの小さなチャレンジ")
    stamps = get_today_stamps()
    ch1,ch2,ch3 = st.columns(3)

    with ch1:
        done = "水分チェック" in stamps
        st.write("💧 **水分を1回記録**")
        if done: st.success("達成済み")
        elif st.button("記録する", key="home_water"):
            add_stamp("水分チェック", 5)
            st.rerun()

    with ch2:
        done = "歩数チェック" in stamps
        st.write("🚶 **少しでも歩く**")
        if done: st.success("達成済み")
        elif st.button("歩いた！", key="home_walk"):
            add_stamp("歩数チェック", 5)
            st.rerun()

    with ch3:
        done = "脳トレ完了" in stamps
        st.write("🧠 **1分脳トレ**")
        if done: st.success("達成済み")
        else:
            if st.button("挑戦する", key="home_quiz"):
                st.session_state.current_page = "🧠 楽しむ・つながる"
                st.rerun()

    st.divider()
    st.subheader("⚡ すぐ使える機能")
    q1,q2,q3 = st.columns(3)
    with q1:
        if st.button("🥗 今日の食事アイデア", use_container_width=True):
            st.session_state.current_page = "🍳 食事アイデア"; st.rerun()
    with q2:
        if st.button("📊 健康を記録する", use_container_width=True):
            st.session_state.current_page = "🌱 健康チェック"; st.rerun()
    with q3:
        if st.button("🧠 1分脳トレ", use_container_width=True):
            st.session_state.current_page = "🧠 楽しむ・つながる"; st.rerun()

    st.subheader("💡 今日の健康ミニ知識")
    st.info(today_quiz["q"])
    st.caption("毎日ひとつ、新しい知識を。答えは「楽しむ・つながる」で確認できます。")


# ============================================================
# 🌱 健康チェック
# ============================================================
elif page == "🌱 健康チェック":
    st.header("🌱 健康チェック")
    st.write("毎日の数字を完璧にするためではなく、自分の変化に気づくためのページです。")

    with st.form("health_form"):
        a,b = st.columns(2)
        with a:
            h_weight = st.number_input("⚖️ 体重 (kg)", min_value=30.0, max_value=200.0,
                                       value=float(st.session_state.senior_weight), step=0.1)
            h_sys = st.number_input("🩺 血圧・上 (mmHg)", min_value=70, max_value=250, value=120)
            h_dia = st.number_input("🩺 血圧・下 (mmHg)", min_value=40, max_value=150, value=80)
        with b:
            h_water = st.number_input("💧 水分摂取量 (ml)", min_value=0, max_value=5000,
                                      value=int(st.session_state.water_today), step=100)
            h_sleep = st.number_input("😴 睡眠時間", min_value=0.0, max_value=14.0,
                                      value=float(st.session_state.sleep_hours), step=0.5)
            h_steps = st.number_input("🚶 今日の歩数", min_value=0, max_value=50000,
                                      value=int(st.session_state.walk_steps), step=500)
        h_mood = st.select_slider("😊 今日の調子", options=["いまいち","普通","良い"],
                                   value="普通")
        save = st.form_submit_button("💾 今日の記録を保存", use_container_width=True, type="primary")
        if save:
            ok, msg = save_health_today(h_weight, h_sys, h_dia, h_water, h_sleep, h_steps)
            st.session_state.mood_today = "良い" if h_mood == "良い" else ("普通" if h_mood == "普通" else "いまいち")
            if ok:
                add_stamp("健康記録", 5)
                st.success("今日の記録を保存しました。")
            else:
                st.error(f"保存できませんでした: {msg}")

    st.subheader("💧 水分をワンタップ記録")
    wc1,wc2,wc3,wc4 = st.columns(4)
    for col, amount, label in [
        (wc1,150,"コップ1杯 +150ml"),
        (wc2,250,"マグカップ +250ml"),
        (wc3,350,"水筒 +350ml"),
        (wc4,500,"ペットボトル +500ml"),
    ]:
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.water_today += amount
                add_stamp("水分チェック", 2)
                st.rerun()

    st.divider()
    height = float(st.session_state.senior_height)
    weight = float(st.session_state.senior_weight)
    try:
        bmi_value, bmi_result = calculate_bmi(height, weight)
        st.subheader("📊 今の自分を知る")
        x1,x2,x3 = st.columns(3)
        x1.metric("BMI", f"{bmi_value:.1f}")
        x2.metric("体重", f"{weight:.1f} kg")
        x3.metric("健康習慣スコア", f"{calculate_health_score()} / 100")
        st.caption(f"BMIの目安: {bmi_result}。BMIだけで健康状態を判断するものではありません。")
    except Exception:
        pass

    st.divider()
    st.subheader("📈 これまでの記録")
    try:
        records = get_health_records(username)
        display_health_record_table(records)
    except Exception as e:
        st.warning(f"履歴を読み込めませんでした: {e}")

# ============================================================
# 🍳 食事アイデア
# ============================================================
elif page == "🍳 食事アイデア":
    st.header("🍳 食事アイデア")
    st.write("「毎日きっちり献立を決める」より、今日の食事を少し良くするアイデアを見つけるためのページです。")

    food_tab1, food_tab2, food_tab3 = st.tabs(["✨ 今日のおすすめ", "🥗 冷蔵庫から探す", "⭐ 保存したアイデア"])

    ALL_DISLIKE_MASTER = [
        "鶏肉","豚肉","牛肉","魚","鮭","さば","卵","豆腐","納豆",
        "牛乳","ヨーグルト","キャベツ","レタス","トマト","きゅうり",
        "大根","人参","玉ねぎ","白菜","ほうれん草","小松菜",
        "きのこ","海藻","ナッツ"
    ]

    with food_tab1:
        st.subheader("✨ 今日の食事アイデアをつくる")
        f1,f2,f3 = st.columns(3)
        with f1:
            style = st.selectbox("料理の方向", ["指定なし","和食","洋食","中華"], key="food_style")
            difficulty = st.selectbox("手間", ["指定なし","簡単","普通","本格的"], key="food_diff")
        with f2:
            main_food = st.radio("主役", ["指定なし","魚","肉"], horizontal=True, key="food_main")
            season = st.selectbox("季節", ["auto","春","夏","秋","冬"],
                                  format_func=lambda x: "今の季節" if x=="auto" else x,
                                  key="food_season")
        with f3:
            dislikes = st.multiselect("避けたい食材", ALL_DISLIKE_MASTER, key="food_dislike")
        st.caption("年齢による画面分岐は行わず、登録した健康情報は必要な範囲で食事提案に利用します。")

        if st.button("🤖 食事アイデアを提案してもらう", use_container_width=True, type="primary"):
            try:
                calorie = calculate_calories(
                    int(st.session_state.senior_age),
                    st.session_state.senior_gender,
                    float(st.session_state.senior_height),
                    float(st.session_state.senior_weight),
                    "普通"
                )
                rec = generate_best_calorie_menu(
                    age=int(st.session_state.senior_age),
                    disease=st.session_state.senior_disease,
                    calorie=calorie,
                    season=season,
                    style=None if style=="指定なし" else style,
                    difficulty=None if difficulty=="指定なし" else difficulty,
                    dislike=dislikes,
                    favorite_food=None if main_food=="指定なし" else main_food,
                )
                st.session_state.recommended_menu = rec
                st.session_state.preferred_style = None if style=="指定なし" else style
                st.session_state.preferred_difficulty = None if difficulty=="指定なし" else difficulty
                st.session_state.dislike_foods = dislikes
                st.success("あなた向けの食事アイデアを作りました。")
            except Exception as e:
                st.error(f"食事アイデアの作成に失敗しました: {e}")

        rec = st.session_state.get("recommended_menu")
        if rec:
            calorie = calculate_calories(
                int(st.session_state.senior_age), st.session_state.senior_gender,
                float(st.session_state.senior_height), float(st.session_state.senior_weight), "普通"
            )
            st.divider()
            st.subheader("🍽️ 今日の提案")
            c1,c2,c3 = st.columns(3)
            for col, meal, emoji in [(c1,"朝食","🌅"),(c2,"昼食","🌞"),(c3,"夕食","🌙")]:
                with col:
                    title = rec.get(meal, "おすすめ料理")
                    display_safe_image(get_menu_image_path(title), caption=meal, fallback_emoji="🍳")
                    st.markdown(f"### {emoji} {title}")

            st.info(f"💡 {rec.get('バランス','主食・主菜・副菜を意識したバランスです。')}")
            if rec.get("アドバイス"):
                st.write(f"**今日のポイント:** {rec.get('アドバイス')}")

            with st.expander("📊 栄養情報を詳しく見る"):
                st.metric("推定エネルギー", f"{rec.get('カロリー', calorie)} kcal")
                st.write(f"提案理由: {rec.get('理由','健康状態や設定条件を考慮して提案しています。')}")
                st.caption("栄養情報は目安です。治療中の方は医療者・管理栄養士の指示を優先してください。")

            if st.button("⭐ この提案を保存", key="save_food_idea"):
                if rec not in st.session_state.fav_daily_menus:
                    st.session_state.fav_daily_menus.append(rec)
                    add_stamp("食事アイデア保存", 3)
                    st.success("保存しました。")

            try:
                pdf_bytes = export_pdf(rec)
                st.download_button(
                    "📄 今日の食事アイデアをPDF保存",
                    data=pdf_bytes,
                    file_name=f"food_idea_{today_str}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception:
                pass

            with st.expander("🛒 材料を確認する"):
                ingredients = get_ingredients_enhanced(
                    f"{rec.get('朝食','')}・{rec.get('昼食','')}・{rec.get('夕食','')}"
                )
                for idx, ing in enumerate(ingredients):
                    st.checkbox(ing, key=f"food_ing_{idx}")

        st.divider()
        st.subheader("📅 もっと計画したい人向け")
        if st.button("1週間の食事プランを作る", use_container_width=True):
            try:
                calorie = calculate_calories(
                    int(st.session_state.senior_age), st.session_state.senior_gender,
                    float(st.session_state.senior_height), float(st.session_state.senior_weight), "普通"
                )
                wm = generate_weekly_menu(
                    age=int(st.session_state.senior_age),
                    disease=st.session_state.senior_disease,
                    calorie=calorie,
                    season=st.session_state.get("preferred_season","auto"),
                    style=st.session_state.get("preferred_style"),
                    difficulty=st.session_state.get("preferred_difficulty"),
                    dislike=st.session_state.get("dislike_foods",[]),
                    favorite_food=None,
                )
                st.session_state.weekly_menu = wm
            except Exception as e:
                st.error(f"週間プラン作成エラー: {e}")
        if st.session_state.get("weekly_menu"):
            wm = st.session_state.weekly_menu
            for d in ["月曜日","火曜日","水曜日","木曜日","金曜日","土曜日","日曜日"]:
                if d in wm:
                    dd = wm[d]
                    with st.expander(f"📌 {d}"):
                        if isinstance(dd, dict):
                            st.write(f"🌅 {dd.get('朝食','')}")
                            st.write(f"🌞 {dd.get('昼食','')}")
                            st.write(f"🌙 {dd.get('夕食','')}")
                            if dd.get("カロリー"):
                                st.caption(f"約 {dd.get('カロリー')} kcal")
                        else:
                            st.write(str(dd))
            try:
                shop = create_shopping_list(wm)
                with st.expander("🛒 まとめ買いリスト"):
                    if isinstance(shop, dict):
                        for cat, items in shop.items():
                            st.write(f"**{cat}**")
                            for it in items:
                                st.checkbox(str(it), key=f"shop_{cat}_{it}")
                    elif isinstance(shop, list):
                        for i,it in enumerate(shop):
                            st.checkbox(str(it), key=f"shop_list_{i}")
            except Exception:
                pass

    with food_tab2:
        st.subheader("🥗 冷蔵庫のあまりものから")
        fridge = st.text_input("ある食材を入力（例：豆腐、白菜、きのこ）", key="fridge_input")
        if st.button("🍳 レシピを探す", use_container_width=True):
            if not fridge.strip():
                st.warning("食材を入力してください。")
            else:
                try:
                    result = recommend_from_fridge(fridge)
                    st.success("こんな使い方があります。")
                    st.write(result)
                    add_stamp("冷蔵庫レシピ", 3)
                except Exception as e:
                    st.info(f"💡 {fridge}なら、野菜と一緒にだしで煮る・炒めるなど、調味料を控えめにした料理がおすすめです。")
        st.info("余りものを無駄にしないことも、無理なく続く健康習慣のひとつです。")

    with food_tab3:
        st.subheader("⭐ 保存した食事アイデア")
        if not st.session_state.fav_daily_menus:
            st.info("まだ保存したアイデアはありません。")
        else:
            for i,m in enumerate(st.session_state.fav_daily_menus):
                st.info(
                    f"**{i+1}.** 朝：{m.get('朝食','-')} / 昼：{m.get('昼食','-')} / 夕：{m.get('夕食','-')}"
                )

# ============================================================
# 🧠 楽しむ・つながる
# ============================================================
elif page == "🧠 楽しむ・つながる":
    st.header("🧠 楽しむ・つながる")
    st.write("健康は、記録だけでは続きません。知る・遊ぶ・人とつながる時間も大切にします。")

    tab_quiz, tab_post, tab_event, tab_news = st.tabs(
        ["🧠 1分脳トレ", "💬 みんなの投稿", "📍 地域イベント", "📰 地域ニュース"]
    )

    with tab_quiz:
        st.subheader("🧠 今日の1分脳トレ")
        st.write(f"**Q. {today_quiz['q']}**")
        ans = st.radio("答えを選んでください", today_quiz["options"], key="main_quiz")
        if st.button("答え合わせ", use_container_width=True):
            if ans == today_quiz["ans"]:
                st.success(f"🎉 正解！ {today_quiz['fact']}")
                if "脳トレ完了" not in get_today_stamps():
                    add_stamp("脳トレ完了", 5)
                if st.session_state.voice_enabled:
                    trigger_action(sound=True, speak_text="正解です。今日の脳トレを完了しました。")
            else:
                st.warning("惜しい！答えを見ながら、もう一度覚えてみましょう。")
        st.divider()
        st.subheader("🏆 続ける楽しみ")
        st.metric("現在のポイント", f"{st.session_state.genki_point} pt")
        st.caption("ポイントは順位を競うためだけでなく、健康習慣を続けた記録として使います。")

    with tab_post:
        st.subheader("💬 みんなの健康習慣")
        if st.session_state.is_logged_in:
            with st.form("community_post"):
                post = st.text_area(
                    "今日やってみたこと・おすすめの習慣",
                    placeholder="例：夕食後に10分歩いたら気分がよかったです。"
                )
                if st.form_submit_button("📢 投稿する"):
                    if post.strip():
                        try:
                            add_post(username, post.strip(), "一般")
                            add_stamp("コミュニティ投稿", 5)
                            st.success("投稿しました。")
                            st.rerun()
                        except Exception as e:
                            st.error(f"投稿エラー: {e}")
                    else:
                        st.warning("内容を入力してください。")
        try:
            posts = get_posts()
            if posts:
                for p in posts[:20]:
                    if isinstance(p, dict):
                        name = p.get("user_name","匿名")
                        content = p.get("content","")
                        created = p.get("created_at","")
                    else:
                        name = p[1] if len(p)>1 else "匿名"
                        content = p[2] if len(p)>2 else ""
                        created = p[4] if len(p)>4 else ""
                    st.info(f"👤 **{name}**　{created}\n\n{content}")
            else:
                st.info("まだ投稿はありません。最初のひとことをどうぞ。")
        except Exception as e:
            st.warning(f"投稿を読み込めませんでした: {e}")

    with tab_event:
        st.subheader("📍 地域のイベント・健康講座")
        st.caption("地域とのつながりは、健康習慣を続けるきっかけにもなります。")
        if st.button("🔄 最新情報に更新", key="events_refresh"):
            try:
                refresh_events()
                st.success("更新しました。")
            except Exception as e:
                st.warning(f"更新できませんでした: {e}")
        try:
            events = get_home_events(st.session_state)
            if not isinstance(events, list):
                events = [events] if events else []
            if events:
                for e in events[:8]:
                    if isinstance(e, dict):
                        st.info(
                            f"📅 **{e.get('title','地域イベント')}**\n\n"
                            f"📍 {e.get('place','地域')}　|　{e.get('datetime',e.get('date','開催予定'))}"
                        )
                        safe_event_link(e.get("url",""))
            else:
                st.info("現在表示できるイベントがありません。")
        except Exception as e:
            st.warning(f"イベント情報を読み込めませんでした: {e}")

    with tab_news:
        st.subheader("📰 地域ニュース")
        try:
            news_items = get_local_news()
            if news_items:
                for n in news_items[:8]:
                    if isinstance(n, dict):
                        st.success(
                            f"📰 **{n.get('title','地域ニュース')}**\n\n"
                            f"📍 {n.get('place','地域')}　|　{n.get('date','最近')}"
                        )
                        safe_event_link(n.get("url",""), "記事を読む")
            else:
                st.info("現在表示できるニュースがありません。")
        except Exception as e:
            st.warning(f"ニュースを読み込めませんでした: {e}")

# ============================================================
# ⚙️ 設定
# ============================================================
elif page == "⚙️ 設定":
    st.header("⚙️ 設定")
    st.write("必要な情報だけを登録しておけば、健康チェックや食事アイデアをあなた向けに調整できます。")

    with st.form("profile_form"):
        p1,p2 = st.columns(2)
        with p1:
            p_name = st.text_input("お名前 / ユーザーID", value=username)
            p_age = st.number_input("年齢", min_value=18, max_value=120,
                                    value=int(st.session_state.senior_age), step=1)
            gender_options = ["女性","男性","未回答"]
            current_gender = st.session_state.senior_gender if st.session_state.senior_gender in gender_options else "未回答"
            p_gender = st.radio("性別", gender_options,
                                index=gender_options.index(current_gender), horizontal=True)
        with p2:
            p_height = st.number_input("身長 (cm)", min_value=120.0, max_value=220.0,
                                       value=float(st.session_state.senior_height), step=0.5)
            p_weight = st.number_input("体重 (kg)", min_value=30.0, max_value=200.0,
                                       value=float(st.session_state.senior_weight), step=0.5)
            disease_options = ["なし","高血圧","糖尿病","腎臓病","脂質異常症","骨粗しょう症","心疾患"]
            cur = st.session_state.senior_disease if st.session_state.senior_disease in disease_options else "なし"
            p_disease = st.selectbox("健康上、食事で配慮したいこと",
                                     disease_options, index=disease_options.index(cur))
        save_profile = st.form_submit_button("💾 プロフィールを保存", use_container_width=True, type="primary")
        if save_profile:
            try:
                old_name = username
                st.session_state.senior_fullname = p_name.strip() or old_name
                st.session_state.senior_age = int(p_age)
                st.session_state.senior_gender = p_gender
                st.session_state.senior_height = float(p_height)
                st.session_state.senior_weight = float(p_weight)
                st.session_state.senior_disease = p_disease
                add_or_update_user(
                    st.session_state.senior_fullname, "一般", int(p_age), p_gender,
                    float(p_height), float(p_weight), "普通", p_disease, "一般"
                )
                st.success("プロフィールを更新しました。")
                st.rerun()
            except Exception as e:
                st.error(f"保存エラー: {e}")

    st.divider()
    st.subheader("🎯 アプリの使い方")
    st.markdown("""
    - **ホーム**：今日やることを3つだけ確認
    - **健康チェック**：体重・血圧・水分・睡眠・歩数を記録
    - **食事アイデア**：毎日の食事や冷蔵庫の食材からヒントを取得
    - **楽しむ・つながる**：1分脳トレ、投稿、地域イベント、ニュース
    - **設定**：健康計算に使うプロフィールを変更
    """)
    st.info("💡 年齢によって画面や機能を切り替えることはありません。登録した年齢は健康計算など必要な処理にのみ使用します。")

    st.divider()
    st.subheader("🔊 音声案内")
    if st.button("画面のポイントを読み上げる"):
        trigger_action(
            sound=False,
            speak_text="未来の健康習慣AIです。ホームでは今日の健康習慣を確認し、健康チェックでは記録、食事アイデアでは料理のヒント、楽しむつながるでは脳トレや地域情報を利用できます。"
        )

    if st.session_state.is_logged_in:
        st.divider()
        st.subheader("🔐 アカウント情報")
        st.code(f"ユーザーコード: {st.session_state.user_code or '未設定'}")
        st.caption("ユーザーコードは本人確認やデータ管理に使用するため、必要以上に他人へ共有しないでください。")
else:
    st.warning("ページを選択してください。")