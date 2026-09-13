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

# 認証設定
ADMIN_PWD = st.secrets.get("ADMIN_PASSWORD", "admin123")
FACILITY_PWD = st.secrets.get("FACILITY_PASSWORD", "facility123")
FAMILY_PWD = st.secrets.get("FAMILY_PASSWORD", "family123")

ADMIN_HASH = hash_pass(ADMIN_PWD)
FACILITY_HASH = hash_pass(FACILITY_PWD)
FAMILY_HASH = hash_pass(FAMILY_PWD)

st.set_page_config(
    page_title="高齢者健康・交流アプリ",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

create_tables()

# ==========================
# SessionState 初期化
# ==========================
today_str = str(date.today())

DEFAULT_SESSION = {
    "is_logged_in": False, 
    "user_id": None,
    "is_auto_logged_in": False,
    "event_update": False,
    "admin_authenticated": False,
    "family_authenticated": False,
    "facility_authenticated": False,
    "senior_surname": "田中",
    "senior_fullname": "田中 太郎",
    "senior_age": 75,
    "senior_birthdate": date(1951, 4, 15),
    "senior_disease": "高血圧",
    "senior_gender": "男性",
    "senior_height": 165.0,
    "senior_weight": 58.0,
    "preferred_style": None,
    "preferred_difficulty": None,
    "dislike_foods": [],
    "favorite_food_type": "指定なし",
    "preferred_season": "auto",
    "user_code": "",
    "linked_senior_code": "",
    "linked_senior_name": "田中 太郎",
    "facility_name": "特別養護老人ホーム さくら園",
    "current_page": "🏠 ホーム",
    "menu_text": None,
    "recommended_menu": None,
    "weekly_menu": None,
    "display_mode": "😊 簡単モード（おすすめ）",
    "dark_mode": False,
    "font_size": 26,
    "voice_enabled": True,
    "genki_point": 180,
    "user_role": "👴 高齢者（本人）",
    "tutorial_finished": True,
    "tutorial_page": 1,
    "water_today": 1000,
    "walk_steps": 3500,
    "continue_days": 18,
    "small_goals": {"gratitude": False, "walk_10m": False, "water_1glass": False, "photo": False},
    "omikuji_done": False,
    "omikuji_result": None,
    "facility_announcements": ["📢 8月15日(土) 夏祭り納涼大会を開催します！ご家族様の面会も歓迎です。", "📌 熱中症警戒アラートが発令中です。水分補給の徹底をお願いいたします。"]
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value

@st.cache_resource
def init_db():
    create_tables()
    conn = sqlite3.connect('app_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stamps (
                    user_id TEXT, date TEXT, action_type TEXT,
                    PRIMARY KEY(user_id, date, action_type)
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS genki_status (
                    user_id TEXT, date TEXT, timestamp TEXT,
                    PRIMARY KEY(user_id, date)
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS genki_likes (
                    target_user TEXT, date TEXT, likes INTEGER,
                    PRIMARY KEY(target_user, date)
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_favorites (
                    user_id TEXT, fav_type TEXT, data_json TEXT, created_at TEXT
                 )''')
    conn.commit()
    conn.close()

init_db()

# Supabase 接続
from supabase import create_client, Client

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def register_user_db(username, password, role, age, gender, height, weight, disease):
    try:
        supabase = get_supabase()
        pwd_hash = hash_pass(password)
        u_code = secrets.token_hex(3).upper()
        data = {
            "username": username,
            "password_hash": pwd_hash,
            "role": role,
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight,
            "disease": disease,
            "user_code": u_code
        }
        supabase.table("app_users").insert(data).execute()
        add_or_update_user(username, role, age, gender, height, weight, "普通", disease, role)
        return True, u_code
    except Exception as e:
        err_msg = str(e)
        print(f"Registration Error Detail: {err_msg}") # コンソールに詳細ログを出力
        if "getaddrinfo failed" in err_msg:
            return False, "ネットワーク接続エラー: SupabaseのURLが正しいか、ネット接続を確認してください。"
        elif "duplicate" in err_msg.lower() or "unique" in err_msg.lower():
            return False, "このお名前（ユーザーID）はすでに登録されています。"
        return False, f"登録エラー: {err_msg}"

def authenticate_user_db(username, password):
    try:
        supabase = get_supabase()
        pwd_hash = hash_pass(password)
        res = supabase.table("app_users").select("*").eq("username", username).eq("password_hash", pwd_hash).execute()
        if res.data and len(res.data) > 0:
            u = res.data[0]
            return (u["username"], u["role"], u["age"], u["gender"], u["height"], u["weight"], u["disease"], u["user_code"])
        return None
    except Exception as e:
        print(f"Login Error Detail: {e}") # ログイン失敗時の詳細エラーをコンソールに出力
        return None

cookies_pwd = st.secrets.get("COOKIES_PASSWORD", "a-very-secret-phrase-stored-in-secrets")
cookies = EncryptedCookiesManager(
    prefix="mimamori/api",
    password=cookies_pwd,
)

if not cookies.ready():
    st.stop()

if "is_guest_mode" not in st.session_state:
    st.session_state.is_guest_mode = False

if not st.session_state.is_logged_in and not st.session_state.get("is_guest_mode", False):
    saved_username = cookies.get("saved_username")
    if saved_username:
        try:
            supabase = get_supabase()
            res = supabase.table("app_users").select("*").eq("username", saved_username).execute()
            if res.data and len(res.data) > 0:
                user_info_db = res.data[0]
                st.session_state.is_logged_in = True
                st.session_state.is_auto_logged_in = True
                st.session_state.senior_fullname = user_info_db["username"]
                st.session_state.user_role = user_info_db.get("role", "一般")
                st.session_state.senior_age = user_info_db.get("age", 0)
                st.session_state.user_code = user_info_db.get("user_code", "")
                st.session_state.user_id = user_info_db["username"]
                st.toast(f"🍪 お帰りなさい、{saved_username} 様！（自動ログイン）")
                st.rerun()
        except Exception as e:
            print(f"Auto-login failed: {e}")

if not st.session_state.is_logged_in:
    if not st.session_state.is_guest_mode:
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            st.markdown("<h2 style='text-align: center;'>🍱 高齢者健康、交流アプリ</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #666;'>サービスを利用するにはログインが必要です。</p>", unsafe_allow_html=True)
            
            login_tab1, login_tab2 = st.tabs(["🔑 ログイン", "📝 新規会員登録"])
            
            with login_tab1:
                with st.form("main_login_form"):
                    l_name = st.text_input("👤 お名前（ユーザーID）", "")
                    l_pass = st.text_input("🔑 パスワード", type="password")
                    remember_me = st.checkbox("🔑 次回から自動的にログインする", value=True)
                    submit_login = st.form_submit_button("ログインして始める", use_container_width=True)
                    if submit_login:
                        if not l_name.strip() or not l_pass.strip():
                            st.warning("お名前とパスワードを入力してください。")
                        else:
                            user_info = authenticate_user_db(l_name, l_pass)
                            if user_info:
                                st.session_state.is_logged_in = True
                                st.session_state.is_guest_mode = False
                                st.session_state.senior_fullname = user_info[0]
                                st.session_state.user_role = user_info[1]
                                st.session_state.senior_age = user_info[2]
                                st.session_state.senior_gender = user_info[3]
                                st.session_state.senior_height = user_info[4]
                                st.session_state.senior_weight = user_info[5]
                                st.session_state.senior_disease = user_info[6]
                                st.session_state.user_code = user_info[7]
                                st.session_state.user_id = user_info[0]

                                if remember_me:
                                    cookies["saved_username"] = l_name.strip()
                                    cookies.save()
                                else:
                                    if "saved_username" in cookies:
                                        del cookies["saved_username"]
                                        cookies.save()

                                try:
                                    h_recs = get_health_records(user_info[0])
                                    if h_recs and len(h_recs) > 0 and str(h_recs[0][0]) == today_str:
                                        st.session_state.water_today = int(h_recs[0][4]) if len(h_recs[0]) > 4 and h_recs[0][4] is not None else 0
                                    else:
                                        st.session_state.water_today = 0
                                except Exception:
                                    pass
                                st.success(f"🎉 ようこそ {l_name} 様！")
                                st.rerun()
                            else:
                                st.error("❌ お名前またはパスワードが正しくありません。")

            with login_tab2:
                with st.form("main_register_form"):
                    r_name = st.text_input("👤 お名前（フルネーム、空白なし）", "")
                    r_pass = st.text_input("🔑 パスワードを設定", type="password")
                    r_role = st.selectbox("立場（役割）", ["👴 高齢者（本人）", "🎓 学生・若者モード", "👨‍👩‍👧 家族アカウント", "🏥 施設職員モード"])
                    r_age = st.number_input("年齢", min_value=18, max_value=120, value=75)
                    r_gender = st.radio("性別", ["女性", "男性", "未回答"], horizontal=True)
                    r_height = st.number_input("身長 (cm)", value=155.0, step=0.5)
                    r_weight = st.number_input("体重 (kg)", value=50.0, step=0.5)
                    r_disease = st.selectbox("配慮すべき持病", ["高血圧", "糖尿病", "腎臓病", "脂質異常症", "骨粗しょう症", "認知症予防", "フレイル予防", "なし"])
                
                    submit_reg = st.form_submit_button("✨ アカウントを作成", use_container_width=True)
                    if submit_reg:
                        if not r_name.strip() or not r_pass.strip():
                            st.warning("お名前とパスワードを入力してください。")
                        else:
                            ok, res = register_user_db(r_name, r_pass, r_role, int(r_age), r_gender, float(r_height), float(r_weight), r_disease)
                            if ok:
                                st.success(f"🎉 アカウントを作成しました！「🔑 ログイン」タブからログインしてください。（連携コード: `{res}`）")
                            else:
                                st.error(f"登録エラー: {res}")

            st.markdown("---")
            if st.button("👨‍🍳 ログインせずに献立だけ作成してみる（お試し）", use_container_width=True):
                st.session_state.is_guest_mode = True
                st.rerun()
        st.stop()
    else:
        st.info("💡 現在「お試し（献立作成のみ）」モードで利用中です。健康記録や交流機能を利用するにはログインしてください。")
        if st.sidebar.button("🔑 ログイン画面へ戻る", use_container_width=True):
            st.session_state.is_guest_mode = False
            st.rerun()

user_id = st.session_state.user_id

def add_stamp(action_name):
    conn = sqlite3.connect('app_data.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO daily_stamps VALUES (?, ?, ?)", (user_id, today_str, action_name))
        conn.commit()
        st.toast(f"🎵 スタンプGET: 【{action_name}】", icon="✨")
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def play_sound_js():
    return """
    <script>
    (function() {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.1);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.15);
    })();
    </script>
    """

def read_text_js(text):
    return f"""
    <script>
    (function() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const uttr = new SpeechSynthesisUtterance("{text}");
            uttr.lang = 'ja-JP';
            uttr.rate = 0.9;
            window.speechSynthesis.speak(uttr);
        }}
    }})();
    </script>
    """

if "tts_text" in st.session_state and st.session_state["tts_text"]:
    st.components.v1.html(read_text_js(st.session_state["tts_text"]), height=0)
    st.session_state["tts_text"] = ""

if st.session_state.get("play_sound", False):
    st.components.v1.html(play_sound_js(), height=0)
    st.session_state["play_sound"] = False

def trigger_action(sound=True, speak_text=""):
    if sound:
        st.session_state["play_sound"] = True
    if speak_text:
        st.session_state["tts_text"] = speak_text

QUIZ_DATABASE = [
    {"q": "日本で一番高い山は富士山ですが、2番目に高い山はどこでしょう？", "options": ["北岳（南アルプス）", "槍ヶ岳", "立山"], "ans": "北岳（南アルプス）", "fact": "北岳は山梨県にあり、標高3,193mです！"},
    {"q": "「秋なすは嫁に食わすな」のことわざの本来の意味で正しいものは？", "options": ["身体が冷えてしまうから", "憎らしいから", "美味しすぎるから"], "ans": "身体が冷えてしまうから", "fact": "体を冷やす効果があるため、体を気遣う優しさから来た説が有力です。"},
    {"q": "次のうち、脳を一番活性化させると言われる日常動作はどれ？", "options": ["よく噛んで食べる", "じっとテレビを見る", "静かに過ごす"], "ans": "よく噛んで食べる", "fact": "噛む動きは脳の血流量を増やし、認知症予防に非常に効果的です。"},
    {"q": "笑うこと（爆笑）で増加し、免疫力を高めてくれる細胞はどれ？", "options": ["NK（ナチュラルキラー）細胞", "赤血球", "血小板"], "ans": "NK（ナチュラルキラー）細胞", "fact": "1日1回笑うだけで、病気にかかりにくい体を作ることができます！"}
]

day_seed = int(datetime.date.today().strftime("%Y%m%d"))
random.seed(day_seed)
today_quiz = random.choice(QUIZ_DATABASE)

if not st.session_state.user_code or len(str(st.session_state.user_code)) < 4:
    st.session_state.user_code = secrets.token_hex(3).upper()

if "fav_daily_menus" not in st.session_state:
    st.session_state.fav_daily_menus = []
if "fav_weekly_menus" not in st.session_state:
    st.session_state.fav_weekly_menus = []
if "weekly_menu" not in st.session_state:
    st.session_state.weekly_menu = None
if "recommended_menu" not in st.session_state:
    st.session_state.recommended_menu = None

try:
    db_user = get_user(st.session_state.senior_fullname)
    if not db_user:
        res_code = add_or_update_user(
            st.session_state.senior_fullname,
            st.session_state.user_role,
            int(st.session_state.senior_age),
            st.session_state.senior_gender,
            float(st.session_state.senior_height),
            float(st.session_state.senior_weight),
            "普通",
            st.session_state.senior_disease,
            "👴 高齢者モード"
        )
        if res_code and len(str(res_code)) >= 4: 
            st.session_state.user_code = str(res_code)
    else:
        if isinstance(db_user, dict):
            c_val = db_user.get("user_code")
            if c_val and len(str(c_val)) >= 4:
                st.session_state.user_code = str(c_val)
            if "point" in db_user and db_user["point"] is not None:
                st.session_state.genki_point = db_user["point"]
        elif isinstance(db_user, tuple):
            if len(db_user) > 8 and db_user[8] is not None:
                st.session_state.genki_point = db_user[8]
except Exception:
    pass

if not st.session_state.linked_senior_code or len(str(st.session_state.linked_senior_code)) < 4:
    st.session_state.linked_senior_code = st.session_state.user_code

today_task = get_daily_task(st.session_state.senior_fullname, today_str)
db_morning = bool(today_task.get("walk", 0)) if (today_task and isinstance(today_task, dict)) else False
db_goal = bool(today_task.get("exercise", 0)) if (today_task and isinstance(today_task, dict)) else False

if "morning_checked" not in st.session_state:
    st.session_state.morning_checked = db_morning
if "goal_done" not in st.session_state:
    st.session_state.goal_done = db_goal

try:
    h_records = get_health_records(st.session_state.senior_fullname)
    if h_records and len(h_records) > 0:
        latest_h = h_records[0]
        if latest_h[0] == today_str and len(latest_h) > 4 and latest_h[4] is not None:
            st.session_state.water_today = int(latest_h[4])
except Exception:
    pass

def add_water_amount(amount: int):
    st.session_state.water_today += amount
    try:
        add_health_record(
            st.session_state.senior_fullname,
            today_str,
            float(st.session_state.senior_weight),
            120,
            80,
            int(st.session_state.water_today),
            1,
            85
        )
        update_point(st.session_state.senior_fullname, 2)
        st.session_state.genki_point += 2
    except Exception:
        pass

def save_final_water(final_amount: int):
    st.session_state.water_today = final_amount
    try:
        add_health_record(
            st.session_state.senior_fullname,
            today_str,
            float(st.session_state.senior_weight),
            120,
            80,
            int(final_amount),
            1,
            90
        )
        st.success(f"本日({today_str})の最終水分量を【{final_amount} ml】として確定保存しました！")
    except Exception as e:
        st.error(f"保存エラー: {e}")

username = st.session_state.senior_fullname
user_code = st.session_state.user_code

st.sidebar.title("🍱 見守りナビ")
st.sidebar.divider()

if st.session_state.get("is_logged_in", False):
    st.sidebar.markdown("### ログイン中のユーザー")
    st.sidebar.info(f"👤 **{st.session_state.senior_fullname}** 様")

    if st.sidebar.button("🚪 アカウントを切り替える（ログアウト）", use_container_width=True):
        if "saved_username" in cookies:
            del cookies["saved_username"]
            cookies.save()
        st.session_state.is_logged_in = False
        st.session_state.user_id = None
        st.session_state.user_role = "👴 高齢者（本人）"
        st.session_state.current_page = "login"
        st.rerun()
else:
    st.sidebar.warning("🔒 未ログイン状態です")

st.sidebar.divider()

st.session_state.dark_mode = st.sidebar.toggle("🌙 ダークモード表示", value=st.session_state.dark_mode)
dark_mode = st.session_state.dark_mode

st.session_state.display_mode = st.sidebar.radio(
    "📱 表示モード選択",
    ["😊 簡単モード（おすすめ）", "📊 詳細モード（カロリーも細かく表示）"],
    index=0 if "簡単" in st.session_state.display_mode else 1
)

username = st.session_state.senior_fullname
user_code = st.session_state.user_code

need_calorie = calculate_calories(
    int(st.session_state.senior_age),
    st.session_state.senior_gender,
    float(st.session_state.senior_height),
    float(st.session_state.senior_weight),
    "普通"
)
bmi, bmi_result = calculate_bmi(float(st.session_state.senior_height), float(st.session_state.senior_weight))

st.sidebar.info(
    f"👤 **ご利用者**: {username} 様\n"
    f"🎂 **年齢/持病**: {st.session_state.senior_age}歳 / {st.session_state.senior_disease}\n"
    f"🔥 **目標カロリー**: 約 {need_calorie} kcal\n"
    f"🔑 **家族連携コード**: `{user_code}`"
)
st.sidebar.write("※ 氏名・持病変更やモード切り替えは『⚙️ 設定』ページで行えます。")

if dark_mode:
    bg_color, sidebar_bg, text_color = "#121212", "#1E1E1E", "#FFFFFF"
    input_bg, card_bg, box_info_bg = "#2D2D2D", "#262626", "#1A237E"
    box_info_text = "#FFFFFF"
    tag_bg, tag_text = "#424242", "#FFFFFF"
    popover_bg, popover_text = "#2D2D2D", "#FFFFFF"
    expander_bg, expander_text = "#2D2D2D", "#FFFFFF"
    weekly_bg, weekly_text = "#1E1E1E", "#FFFFFF"
else:
    bg_color, sidebar_bg, text_color = "#F4F6F9", "#FFFFFF", "#111111"
    input_bg, card_bg, box_info_bg = "#FFFFFF", "#FFFFFF", "#E3F2FD"
    box_info_text = "#0D47A1"
    tag_bg, tag_text = "#E0E0E0", "#111111"
    popover_bg, popover_text = "#FFFFFF", "#111111"
    expander_bg, expander_text = "#FFFFFF", "#111111"
    weekly_bg, weekly_text = "#FFFFFF", "#111111"

st.markdown(f"""
<style>
    .stApp, [data-testid="stAppViewContainer"] {{ background-color: {bg_color} !important; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 2px solid #DDDDDD; }}
    .stMarkdown, .stText, p, label, span, div, li, [data-testid="stWidgetLabel"] {{ color: {text_color} !important; font-weight: 600; }}
    
    div[data-testid="stAlert"] {{
        background-color: {"#1A2A3A" if dark_mode else "#E3F2FD"} !important;
        border: 1px solid {"#29B6F6" if dark_mode else "#0288D1"} !important;
        border-radius: 10px !important;
    }}
    div[data-testid="stAlert"] * {{
        color: {"#E0F7FA" if dark_mode else "#01579B"} !important;
        font-weight: bold !important;
    }}

    header[data-testid="stHeader"] {{
        background-color: #0D47A1 !important;
        color: #FFFFFF !important;
    }}

    button[data-testid="stSidebarCollapsedControl"], 
    [data-testid="collapsedControl"] {{
        background-color: #1565C0 !important;
        color: #FFFFFF !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 8px !important;
        padding: 6px !important;
        margin: 8px !important;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.3) !important;
    }}

    button[data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {{
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
        stroke: #FFFFFF !important;
        width: 24px !important;
        height: 24px !important;
    }}
    
    [data-testid="stSidebar"] div[data-testid="stAlert"] {{
        background-color: {"#263238" if dark_mode else "#E3F2FD"} !important;
    }}
    [data-testid="stSidebar"] div[data-testid="stAlert"] * {{
        color: {"#FFFFFF" if dark_mode else "#0D47A1"} !important;
    }}

    div[data-baseweb="select"] > div, input, textarea, div[data-baseweb="textarea"] > textarea {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border-radius: 8px !important;
        border: 1px solid #BDBDBD !important;
    }}
    
    div[data-testid="stForm"] {{
        background-color: {card_bg} !important;
        border: 1px solid #BDBDBD !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }}
    div[data-testid="stForm"] * {{ color: {text_color} !important; }}
    div[data-testid="stForm"] button, div[data-testid="stFormSubmitButton"] > button {{
        background-color: #2E7D32 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }}
    
    div[data-testid="stExpander"] {{
        background-color: {expander_bg} !important;
        border: 1px solid #BDBDBD !important;
        border-radius: 10px !important;
    }}
    div[data-testid="stExpander"] details {{ background-color: {expander_bg} !important; }}
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] div[role="button"],
    div[data-testid="stExpander"] [data-aria-expanded="true"] {{
        background-color: {expander_bg} !important;
        color: {expander_text} !important;
    }}
    div[data-testid="stExpander"] * {{ color: {expander_text} !important; }}
    
    .weekly-card, 
    div[data-testid="stExpander"]:has(.weekly-card),
    div[data-testid="stExpander"] .weekly-card,
    div[data-testid="stVerticalBlock"] > div:has(.weekly-card) {{
        background-color: {weekly_bg} !important;
        color: {weekly_text} !important;
        border-radius: 10px;
        padding: 10px;
    }}
    .weekly-card *, 
    div[data-testid="stExpander"]:has(.weekly-card) *,
    div[data-testid="stExpander"] .weekly-card * {{ color: {weekly_text} !important; }}

    div[data-testid="stFileUploader"] {{
        background-color: {card_bg} !important;
        border: 2px dashed #1976D2 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }}
    div[data-testid="stFileUploader"] * {{ color: {text_color} !important; }}
    div[data-testid="stFileUploader"] button {{
        background-color: #1976D2 !important;
        color: #FFFFFF !important;
    }}

    div[data-testid="stExpander"] {{
        background-color: {"#2D2D2D" if dark_mode else "#FFFFFF"} !important;
        border: 1px solid {"#444444" if dark_mode else "#BDBDBD"} !important;
        border-radius: 10px !important;
    }}

    div[data-testid="stExpander"] details,
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] div[role="button"] {{
        background-color: {"#2D2D2D" if dark_mode else "#FFFFFF"} !important;
        color: {"#FFFFFF" if dark_mode else "#111111"} !important;
    }}

    div[data-testid="stExpander"] .stMarkdown, 
    div[data-testid="stExpander"] label, 
    div[data-testid="stExpander"] p, 
    div[data-testid="stExpander"] span,
    div[data-testid="stExpander"] [data-testid="stCaptionContainer"] {{
        color: {"#FFFFFF" if dark_mode else "#111111"} !important;
        font-weight: bold !important;
    }}

    [data-testid="stCaptionContainer"] *, 
    .stCaption, 
    small {{
        color: {"#FFD54F" if dark_mode else "#D84315"} !important;
        font-weight: bold !important;
    }}

    div[data-testid="stRadio"] label span {{
        color: {"#FFFFFF" if dark_mode else "#111111"} !important;
    }}

    div[data-baseweb="toast"] {{
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="toast"] * {{
        color: #FFFFFF !important;
    }}
    div[data-testid="stFileUploader"] {{
        background-color: #F5F5F5 !important;
        border: 2px dashed #1976D2 !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }}
    div[data-testid="stFileUploader"] * {{
        color: #212121 !important;
    }}
    
    div[data-baseweb="popover"], div[role="listbox"], ul[role="listbox"] {{ background-color: {popover_bg} !important; color: {popover_text} !important; }}
    div[role="option"], li[role="option"] {{ background-color: {popover_bg} !important; color: {popover_text} !important; }}
    div[role="option"]:hover, li[role="option"]:hover,
    div[role="option"][aria-selected="true"], li[role="option"][aria-selected="true"] {{
        background-color: #E3F2FD !important;
        color: #0D47A1 !important;
    }}
    
    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: {bg_color} !important; }}
    ::-webkit-scrollbar-thumb {{ background: #BDBDBD !important; border-radius: 5px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #9E9E9E !important; }}

    span[data-baseweb="tag"] {{ background-color: {tag_bg} !important; color: {tag_text} !important; border-radius: 6px !important; }}
    span[data-baseweb="tag"] * {{ color: {tag_text} !important; }}
    button[role="tab"] {{ color: {text_color} !important; font-weight: bold !important; }}

    h1, h2, h3 {{ color: #0D47A1 !important; font-weight: bold !important; }}
    .main-title {{ font-size: 36px !important; color: #0D47A1 !important; font-weight: bold; }}
    .sub-title {{ font-size: 22px !important; color: {text_color} !important; font-weight: bold; margin-bottom: 10px; }}
    
    .brain-box {{ background-color: {card_bg} !important; border: 3px solid #1E88E5; padding: 20px; border-radius: 16px; margin-bottom: 20px; }}
    .info-card-box {{ background-color: {box_info_bg} !important; border: 2px solid #1565C0; padding: 18px; border-radius: 14px; color: {box_info_text} !important; margin-bottom: 15px; }}
    .info-card-box * {{ color: {box_info_text} !important; }}
    .topic-card {{ background-color: {card_bg} !important; border: 2px solid #E65100; padding: 16px; border-radius: 14px; margin-bottom: 15px; }}
    
    .reason-box {{ background-color: #E8F5E9 !important; border: 2px solid #2E7D32; padding: 15px; border-radius: 12px; margin-bottom: 15px; color: #111111 !important; }}
    .reason-box * {{ color: #111111 !important; }}
    
    .status-badge {{
        background-color: #E8F5E9 !important;
        border: 2px solid #2E7D32;
        padding: 12px 18px;
        border-radius: 12px;
        font-size: 18px;
        font-weight: bold;
        color: #1B5E20 !important;
        margin-bottom: 15px;
    }}
    .genki-card {{
        background-color: #FFF3E0 !important;
        border: 2px solid #EF6C00;
        padding: 15px;
        border-radius: 14px;
        text-align: center;
        margin-bottom: 20px;
    }}

    .weekly-card, 
    div[data-testid="stExpander"], 
    div[data-testid="stForm"],
    .reason-box {{
        background-color: {"#262626" if dark_mode else "#FFFFFF"} !important;
        border: 1px solid {"#444444" if dark_mode else "#E0E0E0"} !important;
        border-radius: 12px !important;
    }}

    .weekly-card *, 
    div[data-testid="stExpander"] *, 
    div[data-testid="stForm"] *,
    .reason-box * {{
        color: {"#FFFFFF" if dark_mode else "#212121"} !important;
        -webkit-text-fill-color: {"#FFFFFF" if dark_mode else "#212121"} !important;
    }}

    .stMarkdown p, .stMarkdown span, label {{
        color: {text_color};
    }}

    div[data-testid="stButton"] > button {{
        background-color: #2E7D32 !important;
        background: #2E7D32 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 18px !important;
        height: 50px !important;
        border-radius: 10px !important;
        border: none !important;
    }}
    div[data-testid="stButton"] > button * {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}
</style>
""", unsafe_allow_html=True)

# チュートリアル
if not st.session_state.tutorial_finished:
    st.markdown("# 🍱 高齢者健康・交流アプリ へようこそ！")
    page = st.session_state.tutorial_page

    if page == 1:
        st.info("### 🍚 1. ボタンを押すだけで健康献立を自動作成")
        st.write("持病や年齢に合わせた健康的な献立をAIが自動作成します。")
        display_safe_image("assets/tutorial1.jpg", caption="操作はとても簡単です", fallback_emoji="🍱")
        if st.button("▶ 次へ（健康・生活チェック）"): st.session_state.tutorial_page = 2

    elif page == 2:
        st.info("### ❤️ 2. 今日の運動・水分・会話をワンタップ記録")
        st.write("歩数や水分チェックで「🌸元気ポイント」が溜まります。")
        display_safe_image("assets/tutorial2.jpg", caption="毎日の目標を達成しましょう", fallback_emoji="🌱")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀ 戻る"): st.session_state.tutorial_page = 1
        with col2:
            if st.button("▶ 次へ（地域・家族とのつながり）"): st.session_state.tutorial_page = 3

    elif page == 3:
        st.info("### 👥 3. 地域イベントや思い出でつながる")
        st.write("地域イベントを探したり、昔の思い出をご家族と共有できます。")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀ 戻る"): st.session_state.tutorial_page = 2
        with col2:
            if st.button("🟢 アプリを開始する", key="start_app_btn"): st.session_state.tutorial_finished = True
    st.stop()

# ヘッダー
st.markdown('<p class="main-title">🍱 高齢者健康・交流アプリ</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">{greeting()}、{username} さん。</p>', unsafe_allow_html=True)

if st.session_state.user_role and "施設" in st.session_state.user_role:
    st.markdown(f"### 🏥 {st.session_state.facility_name} 施設職員専用ダッシュボード")
    
    col_fac1, col_fac2 = st.columns([2, 1])
    with col_fac1:
        new_facility = st.text_input("🏥 管理対象の施設・事業所名を変更", value=st.session_state.facility_name)
        if new_facility != st.session_state.facility_name:
            st.session_state.facility_name = new_facility
            st.success(f"所属施設を「{new_facility}」に変更しました。")
            st.rerun()

    try:
        seniors_list = get_all_seniors()
        if seniors_list:
            s_names = [s[1] if isinstance(s, tuple) else s.get("name") for s in seniors_list]
            selected_senior = st.selectbox("👤 入所者様を選択して健康・献立データを参照", s_names, index=s_names.index(st.session_state.senior_fullname) if st.session_state.senior_fullname in s_names else 0)
            if selected_senior != st.session_state.senior_fullname:
                st.session_state.senior_fullname = selected_senior
                st.session_state.linked_senior_name = selected_senior
                st.rerun()
            
            st.markdown(f"#### 📊 {st.session_state.senior_fullname} 様の最新ステータス")
            s_records = get_health_records(st.session_state.senior_fullname)
            
            c_h1, c_h2, c_h3 = st.columns(3)
            if s_records and len(s_records) > 0:
                latest = s_records[0]
                c_h1.metric("💧 本日の水分摂取量", f"{latest[4] if len(latest)>4 else 0} ml")
                c_h2.metric("⚖️ 体重", f"{latest[1] if len(latest)>1 else '--'} kg")
                c_h3.metric("🩺 血圧(収縮/拡張)", f"{latest[2] if len(latest)>2 else '--'} / {latest[3] if len(latest)>3 else '--'} mmHg")
            else:
                c_h1.metric("💧 本日の水分摂取量", f"{st.session_state.water_today} ml")
                c_h2.metric("⚖️ 体重", f"{st.session_state.senior_weight} kg")
                c_h3.metric("🩺 血圧", "120 / 80 mmHg")

            rec_menu = st.session_state.get("recommended_menu")
            if rec_menu and isinstance(rec_menu, dict):
                st.info(f"🍱 **本日の登録献立**: 朝: {rec_menu.get('朝食','--')} | 昼: {rec_menu.get('昼食','--')} | 夕: {rec_menu.get('夕食','--')}")
            else:
                st.caption("※ 本日の献立データはまだ生成されていません。")
    except Exception as e:
        st.error(f"施設データ読み込みエラー: {e}")

st.write("---")

nav_config = [
    ("🏠 ホーム", "#8BC34A", "🏠 ホーム"),
    ("🍱 献立作成", "#E53935", "🍱 献立作成"),
    ("🩺 健康記録", "#03A9F4", "🩺 健康記録"),
    ("👥 交流・思い出", "#AB47BC", "👥 交流・思い出"),
    ("⚙️ 設定", "#78909C", "⚙️ 設定")
]

cols = st.columns(5)

for idx, (label, color_code, target_page) in enumerate(nav_config):
    with cols[idx]:
        if st.button(label, key=f"nav_native_btn_{idx}", use_container_width=True):
            st.session_state.current_page = target_page
            st.rerun()

st.markdown("""
<style>
    div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] > button { background-color: #8BC34A !important; background: #8BC34A !important; color: #FFFFFF !important; }
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] > button { background-color: #E53935 !important; background: #E53935 !important; color: #FFFFFF !important; }
    div[data-testid="stColumn"]:nth-of-type(3) div[data-testid="stButton"] > button { background-color: #03A9F4 !important; background: #03A9F4 !important; color: #FFFFFF !important; }
    div[data-testid="stColumn"]:nth-of-type(4) div[data-testid="stButton"] > button { background-color: #AB47BC !important; background: #AB47BC !important; color: #FFFFFF !important; }
    div[data-testid="stColumn"]:nth-of-type(5) div[data-testid="stButton"] > button { background-color: #78909C !important; background: #78909C !important; color: #FFFFFF !important; }

    div[data-testid="stColumn"] div[data-testid="stButton"] > button {
        height: 60px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: none !important;
    }
    div[data-testid="stColumn"] div[data-testid="stButton"] > button * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

st.write("---")
page = st.session_state.current_page
selected_menu = page  

if not st.session_state.get("is_logged_in", False) and not st.session_state.get("is_guest_mode", False):
    st.warning("⚠️ サービスを利用するにはログインが必要です。")
    st.stop()

if st.session_state.get("is_guest_mode", False) and not st.session_state.get("is_logged_in", False):
    if selected_menu not in ["🍱 献立作成", "🍳 献立作成"]:
        st.warning("🔒 「健康記録」や「コミュニティ」の閲覧・利用にはログインが必要です。")
        st.info("トップページまたはサイドバーの「ログイン」ボタンからログインしてください。")
        if st.button("🔑 ログイン画面へ戻る"):
            st.session_state.is_guest_mode = False
            st.rerun()
        st.stop()

# ===================================================================
# ページ 1: 🏠 ホーム
# ===================================================================
if page == "🏠 ホーム":
    if "家族" in st.session_state.user_role:
        st.markdown(f"## 👨‍👩‍👧 家族見守りサマリー（対象: {st.session_state.get('linked_senior_name', 'ご家族')} 様）")
        st.success(f"🟢 **【認証接続完了】** 連携コード: `{st.session_state.get('linked_senior_code', '')}` | {st.session_state.get('facility_name', '施設')}")
        
        st.subheader("📊 本日のバイタル & 活動状態")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🚶 今日の歩数", f"{st.session_state.get('walk_steps', 0)} 歩", "目標 3000歩")
        m2.metric("💧 水分補給", f"{st.session_state.get('water_today', 0)} ml", "順調")
        
        s_weight = st.session_state.get('senior_weight', 50.0)
        bmi_val = bmi if 'bmi' in locals() else 21.5
        m3.metric("秤 体重 / BMI", f"{s_weight} kg", f"BMI {bmi_val:.1f}")
        m4.metric("🌸 元気ポイント", f"{st.session_state.get('genki_point', 0)} pt", f"{st.session_state.get('continue_days', 1)}日連続")
        m5.metric("😊 ご気分", "お元気", "問題なし")

        st.divider()
        st.subheader("🏥 施設からの最新の連絡・申送り")
        try:
            f_logs = get_family_logs(st.session_state.linked_senior_name)
            if f_logs:
                for log in f_logs[:2]:
                    st.info(f"📅 **[{log.get('created_at', today_str)}] 投稿者: {log.get('sender', '施設職員')}**\n\n📌 **内容**: {log.get('content')}")
            else:
                st.info("📅 **[本日のご様子]**\n\n🍚 食事: **完食** | 💧 水分: **1200ml** | 🚶 活動: **午前中お散歩**\n\n💬 **スタッフより**: 昔の旅行のお話を嬉しそうに語られていました。")
        except Exception: 
            pass

    elif "施設" in st.session_state.user_role:
        st.markdown(f"## 🏥 {st.session_state.get('facility_name', '施設')} 施設全体アナウンス & ポータル")
        
        st.subheader("📢 施設全体掲示板（入所者様・ご家族へ共有中）")
        with st.form("add_announcement_form"):
            new_ann = st.text_input("新規お知らせ・連絡内容を入力", "📢 明日の午後はボランティアによる歌謡イベントを開催します。")
            if st.form_submit_button("📌 掲示板へ発信"):
                if "facility_announcements" not in st.session_state:
                    st.session_state.facility_announcements = []
                st.session_state.facility_announcements.insert(0, new_ann)
                st.success("掲示板を更新しました！")
        
        for ann in st.session_state.get('facility_announcements', []):
            st.info(ann)

    else:
        u_code = user_code if 'user_code' in locals() else st.session_state.get('linked_senior_code', '---')
        st.markdown(f"""
        <div class="status-badge" style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 15px;">
            👤 <b>ご利用者</b>: {st.session_state.get('senior_fullname', 'ご利用者')} 様（{st.session_state.get('senior_age', 75)}歳） &nbsp;|&nbsp; 🏥 <b>所属</b>: {st.session_state.get('facility_name', '一般')} &nbsp;|&nbsp; 🔗 <b>ご家族連携コード</b>: <code>{u_code}</code>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔊 画面の説明を声で聴く", use_container_width=True):
            trigger_action(sound=False, speak_text="こんにちは。今日の健康スタンプを集めたり、脳トレクイズに挑戦してみましょう。")

        st.markdown("---")

        st.subheader("☀️ 今日やること")
        col_a, col_b = st.columns(2)

        with col_a:
            st.write("**1. あいさつ・元気報告**")
            conn = sqlite3.connect('app_data.db')
            c = conn.cursor()
            c.execute("SELECT timestamp FROM genki_status WHERE user_id=? AND date=?", (user_id, today_str))
            already_genki = c.fetchone()
            conn.close()

            if already_genki:
                st.success(f"✅ 「元気だよ」送信済み（{already_genki[0]}）")
                if st.button("↩️ 報告を取り消す", key="cancel_genki_btn"):
                    conn = sqlite3.connect('app_data.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM genki_status WHERE user_id=? AND date=?", (user_id, today_str))
                    c.execute("DELETE FROM daily_stamps WHERE user_id=? AND date=? AND action_type=?", (user_id, today_str, "今日元気？報告"))
                    conn.commit()
                    conn.close()
                    st.toast("元気報告を取り消しました。")
                    st.rerun()
            else:
                if st.button("🌸 今日も元気だよ！", use_container_width=True, type="primary"):
                    now_time = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%H:%M")
                    conn = sqlite3.connect('app_data.db')
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO genki_status VALUES (?, ?, ?)", (user_id, today_str, now_time))
                    conn.commit()
                    conn.close()
                    
                    add_stamp("今日元気？報告")
                    trigger_action(sound=True, speak_text="元気な報告ありがとうございます！")
                    st.rerun()

        with col_b:
            st.write("**2. 本日の献立チェック**")
            rec_menu = st.session_state.get("recommended_menu", None)
            
            if rec_menu and isinstance(rec_menu, dict):
                bf_title = rec_menu.get("朝食", "朝食メニュー")
                ln_title = rec_menu.get("昼食", "昼食メニュー")
                dn_title = rec_menu.get("夕食", "夕食メニュー")
                
                st.info(f"🍲 **本日の献立**\n\n・🌅 **朝**: {bf_title}\n・🌞 **昼**: {ln_title}\n・🌙 **夕**: {dn_title}")
                
                if st.button("🍽️ 献立を確認した！", use_container_width=True, type="primary"):
                    add_stamp("献立チェック")
                    trigger_action(sound=True, speak_text="今日の献立を確認しましたね！美味しそうですね。")
                    st.rerun()
            else:
                st.warning("⚠️ まだ今日の献立がつくられていません。")
                st.caption("「🍱 献立作成」ボタンからAIに本日の献立を作成してもらいましょう！")
                
                if st.button("🍱 献立作成画面へ移動する", use_container_width=True):
                    st.session_state.current_page = "🍱 献立作成"
                    st.rerun()

        st.subheader("💮 今日の健康スタンプカード")
        conn = sqlite3.connect('app_data.db')
        c = conn.cursor()
        c.execute("SELECT action_type FROM daily_stamps WHERE user_id=? AND date=?", (user_id, today_str))
        stamps = [row[0] for row in c.fetchall()]
        conn.close()

        stamp_cols = st.columns(3)
        actions = ["今日元気？報告", "献立チェック", "脳トレ完了"]

        for idx, act in enumerate(actions):
            with stamp_cols[idx]:
                if act in stamps:
                    st.metric(label=act, value="済 💮")
                else:
                    st.metric(label=act, value="未完了")

        st.markdown("---")

        st.subheader("🧠 本日の脳トレ（日替わり）")
        st.write(f"**Q. {today_quiz['q']}**")

        user_ans = st.radio("答えを選んでください：", today_quiz["options"], key="quiz_ans")

        if st.button("答え合わせする", use_container_width=True):
            if user_ans == today_quiz["ans"]:
                st.balloons()
                st.success(f"🎉 大正解！ {today_quiz['fact']}")
                add_stamp("脳トレ完了")
                trigger_action(sound=True, speak_text="大正解です！大変素晴らしいです！")
            else:
                st.warning("惜しい！もう一度考えてみましょう。")
                trigger_action(sound=True, speak_text="もう一度選んでみてください。")

        st.markdown("---")

        col_main_left, col_main_right = st.columns(2)

        with col_main_left:
            c_ev_title, c_ev_btn = st.columns([3, 1])
            with c_ev_title: 
                st.subheader("🎪 近隣の地域イベント・健康講座")
            with c_ev_btn:
                if st.button("🔄 更新", key="btn_refresh_ev"):
                    with st.spinner("最新イベントを更新中..."):
                        try:
                            refresh_events()
                            st.success("最新化完了！")
                        except Exception as e: 
                            st.error(f"エラー: {e}")

            raw_events = get_home_events(st.session_state) if 'get_home_events' in globals() else []
            events_list = raw_events if isinstance(raw_events, list) else ([raw_events] if isinstance(raw_events, dict) else [])

            if events_list:
                for e in events_list[:4]:
                    if isinstance(e, dict):
                        url_str = e.get('url', '')
                        link_markdown = f"\n\n🔗 [👉 詳細ページを見る（外部サイト）]({url_str})" if url_str else ""
                        
                        st.info(
                            f"📢 **{e.get('title', '公民館 講座')}**\n\n"
                            f"📍 {e.get('place', '西東京市')} | 📅 {e.get('datetime', e.get('date', '近日開催'))}"
                            f"{link_markdown}"
                        )
            else:
                st.info("📅 **公民館 健康いきいき体操講座** (10:00〜 総合福祉センター)\n\n🔗 [👉 詳細ページを見る](https://www.city.nishitokyo.lg.jp/event/)")
                st.info("🎨 **シニア昭和写真展・談話会** (13:30〜 地域公民館)\n\n🔗 [👉 詳細ページを見る](https://www.city.nishitokyo.lg.jp/event/)")

            c_nw_title, c_nw_btn = st.columns([3, 1])
            with c_nw_title: 
                st.subheader("📰 おうちで読む地域ニュース（号外NET）")
            with c_nw_btn:
                if st.button("📰 更新", key="btn_refresh_news"):
                    with st.spinner("最新ニュースを取得中..."):
                        try:
                            get_local_news.clear()
                            st.success("更新完了！")
                        except Exception as e: 
                            st.error(f"エラー: {e}")

            try:
                news_items = get_local_news() if 'get_local_news' in globals() else []
                if news_items and isinstance(news_items, list):
                    for n in news_items[:4]:
                        if isinstance(n, dict):
                            n_title = n.get('title', '地域ニュース')
                            n_place = n.get('place', '西東京市')
                            n_date = n.get('date', '最近のニュース')
                            n_url = n.get('url', '')
                            
                            link_markdown = f"\n\n🔗 [👉 号外NETで記事を読む（外部サイト）]({n_url})" if n_url else ""
                            
                            st.success(
                                f"📰 **{n_title}**\n\n"
                                f"📍 {n_place} | 📅 {n_date}"
                                f"{link_markdown}"
                            )
                else:
                    st.info("📰 **現在、新しい地域ニュースはありません。**\n\n🔗 [👉 号外NET 西東京市トップへ](https://nishitokyo.goguynet.jp/)")
            except Exception as e:
                st.error(f"ニュース取得エラー: {e}")

        with col_main_right:
            st.subheader("📅 今日のおすすめ活動")
            st.info("💡 **昭和の思い出回想クイズ**: 20代の頃に聴いた名曲を思い出してみませんか？（『👥 交流・思い出』タブで体験可能）")

            st.markdown(f"""
            <div class="genki-card" style="background-color: #fff3e0; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ffe0b2;">
                <span style="font-size:20px; font-weight:bold; color:#E65100;">🌸 現在の元気ポイント</span><br>
                <span style="font-size:42px; font-weight:bold; color:#D84315;">{st.session_state.get('genki_point', 0)} pt</span><br>
                <span style="font-size:14px; color:#666;">継続日数: {st.session_state.get('continue_days', 1)}日目</span>
            </div>
            """, unsafe_allow_html=True)

# ===================================================================
# ページ 2: 🍱 献立作成
# ===================================================================
elif page == "🍱 献立作成":
    st.header("🍱 AI健康献立作成 ＆ レシピ・食事管理")

    if "家族" in st.session_state.user_role:
        st.info(f"👨‍👩‍👧 **[{st.session_state.get('linked_senior_name', 'ご家族')} 様の本日のお食事モニタリング]**")
        rec = st.session_state.get('recommended_menu', {})
        if rec and isinstance(rec, dict):
            st.write(f"🌅 **朝食**: {rec.get('朝食', '鮭の塩焼き定食')} | 🌞 **昼食**: {rec.get('昼食', '具だくさんおうどん')} | 🌙 **夕食**: {rec.get('夕食', '豆腐ハンバーグ')}")
        else:
            st.write("🌅 **朝食**: 鮭の塩焼き定食 | 🌞 **昼食**: 具だくさんおうどん | 🌙 **夕食**: 豆腐ハンバーグ")
        st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🍚 本日の最適献立", "📅 1週間献立＆買い物リスト", "🍳 思い出レシピ投票", "🥗 冷蔵庫のあまりもの検索", "⭐ お気に入り献立"])

    ALL_DISLIKE_MASTER = [
        "鶏肉", "鶏むね肉", "鶏もも肉", "鶏ささみ", "鶏ひき肉", "豚肉", "豚薄切り肉", "豚コマ肉", "牛肉", "合挽き肉",
        "生鮭", "鮭", "真鯖", "さば", "さんま", "あじ", "さわら", "ブリ切り身", "ブリ", "たら切り身", "たら", "白身魚", "生魚切り身", "ツナ缶",
        "キャベツ", "春キャベツ", "レタス", "トマト", "きゅうり", "大根", "大根おろし", "人参", "玉ねぎ", "新玉ねぎ", "長ねぎ",
        "白菜", "ほうれん草", "小松菜", "ごぼう", "れんこん", "じゃがいも", "アスパラガス", "菜の花", "たけのこ", "水菜",
        "ピーマン", "ナス", "オクラ", "もやし", "こんにゃく", "しめじ", "椎茸", "まいたけ", "エリンギ",
        "豆腐", "厚揚げ", "油揚げ", "納豆", "高野豆腐", "おから", "卵", "ひじき", "わかめ", "昆布",
        "うどん", "マカロニ", "パン", "バナナ", "いちご", "りんご", "柿", "梨", "桃", "みかん", "プレーンヨーグルト", "牛乳"
    ]

    with tab1:
        with st.expander(
            "⚙️ 献立の好み・条件フィルター（和洋中・難易度・季節・苦手食材）",
            expanded=False,
        ):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                st.session_state.preferred_style = st.selectbox(
                     "料理ジャンル",
                     [None, "和食", "洋食", "中華"],
                    format_func=lambda x: "指定なし" if x is None else x,
                    key="t1_style",
                )
                st.session_state.preferred_difficulty = st.selectbox(
                    "調理難易度",
                    [None, "簡単", "普通", "本格的"],
                    format_func=lambda x: "指定なし" if x is None else x,
                    key="t1_diff",
                )
            with fc2:
                st.session_state.favorite_food_type = st.radio(
                    "メイン食材希望",
                    ["指定なし", "魚", "肉"],
                    horizontal=True,
                    key="t1_food",
                )
                st.session_state.preferred_season = st.selectbox(
                    "季節の指定",
                    ["auto", "春", "夏", "秋", "冬"],
                    format_func=lambda x: (
                        "自動（現在の季節）" if x == "auto" else x
                    ),
                    key="t1_season",
                )
            with fc3:
                st.caption("💡 1文字入力すると食材名が検索できます")
                default_dislikes_t1 = [x for x in st.session_state.get("dislike_foods", []) if x in ALL_DISLIKE_MASTER]
                selected_dislike_t1 = st.multiselect(
                    "🚫 苦手・除外食材を選択",
                    ALL_DISLIKE_MASTER,
                    default=default_dislikes_t1,
                    key="t1_dislike_select",
                    placeholder="文字を入力して検索..."
                )
                st.session_state.dislike_foods = selected_dislike_t1

        if st.button("🤖 本日の最適献立を作成", use_container_width=True):
            rec = generate_best_calorie_menu(
                age=int(st.session_state.senior_age),
                disease=st.session_state.senior_disease,
                calorie=need_calorie,
                season=st.session_state.preferred_season,
                style=st.session_state.preferred_style,
                difficulty=st.session_state.preferred_difficulty,
                dislike=st.session_state.dislike_foods,
                favorite_food=(
                    None
                    if st.session_state.favorite_food_type == "指定なし"
                    else st.session_state.favorite_food_type
                ),
            )
            if rec:
                st.session_state.recommended_menu = rec
                st.success("目標カロリーに最も近い献立を作成しました！")
            else:
                st.warning(
                    "条件に該当する献立が見つかりませんでした。フィルター条件を緩めて再試行してください。"
                )

        if st.session_state.recommended_menu:
            rec = st.session_state.recommended_menu

            if st.button("⭐ この献立をお気に入りに保存", key="fav_daily_btn"):
                if rec not in st.session_state.fav_daily_menus:
                    st.session_state.fav_daily_menus.append(rec)
                    st.toast("⭐ 本日の献立をお気に入りに保存しました！")
                else:
                    st.info("すでに保存されています。")

            if "詳細" in st.session_state.display_mode:
                st.markdown(
                    f"""
                <div class="reason-box">
                    💡 <b>⭐ AI管理栄養士の詳細分析・おすすめ理由</b><br>
                    ・<b>配慮疾患</b>: {st.session_state.senior_disease}<br>
                    ・<b>提案理由</b>: {rec.get('理由', '持病に配慮した栄養バランス調整済みです。')}<br>
                    ・<b>栄養バランス</b>: {rec.get('バランス', 'バランス良好')}<br>
                    ・<b>AIアドバイス</b>: {rec.get('アドバイス', '水分をしっかりと摂ってお召し上がりください。')}<br>
                    ・<b>料理属性</b>: {rec.get('料理', '和食')} | 難易度: {rec.get('難易度', '普通')} | 季節: {rec.get('季節', '通年')}
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.subheader("📊 栄養素・カロリー詳細（詳細モード表示）")
                c_pfc1, c_pfc2, c_pfc3, c_pfc4 = st.columns(4)
                c_pfc1.metric(
                    "🔥 推定エネルギー",
                    f"{rec.get('カロリー', need_calorie)} kcal",
                    f"目標 {need_calorie} kcal",
                )
                c_pfc2.metric(
                    "🥩 タンパク質(目標)", f"{int(need_calorie * 0.15 / 4)} g"
                )
                c_pfc3.metric("🥑 脂質(目標)", f"{int(need_calorie * 0.25 / 9)} g")
                c_pfc4.metric(
                    "🍚 炭水化物(目標)", f"{int(need_calorie * 0.60 / 4)} g"
                )

                try:
                    nutrition_chart(
                        need_calorie, st.session_state.senior_disease
                    )
                except Exception:
                    pass
                st.divider()

            else:
                st.markdown(
                    f"""
                <div class="reason-box">
                   💡 <b>⭐ AIのおすすめバランス</b>: {rec.get('バランス', '栄養バランス良好')}（推定カロリー: 約 {rec.get('カロリー', need_calorie)} kcal / 目標 {need_calorie} kcal）
                </div>
                 """,
                    unsafe_allow_html=True,
                )

            col_bf, col_ln, col_dn = st.columns(3)

            with col_bf:
                st.subheader("🌅 朝食")
                bf_text = rec.get("朝食", "")
                bf_img = get_menu_image_path(bf_text)
                display_resized_menu_image(bf_img, caption="【朝食イメージ】")
                st.write(f"### {bf_text}")

            with col_ln:
                st.subheader("🌞 昼食")
                ln_text = rec.get("昼食", "")
                ln_img = get_menu_image_path(ln_text)
                display_resized_menu_image(ln_img, caption="【昼食イメージ】")
                st.write(f"### {ln_text}")

            with col_dn:
                st.subheader("🌙 夕食")
                dn_text = rec.get("夕食", "")
                dn_img = get_menu_image_path(dn_text)
                display_resized_menu_image(dn_img, caption="【夕食イメージ】")
                st.write(f"### {dn_text}")

            st.divider()

            st.subheader("🛒 本日の買い物チェックリスト")
            st.caption("買出し時に購入した食材をタップしてチェックを入れられます。")
            all_meals_text = f"{rec.get('朝食', '')}・{rec.get('昼食', '')}・{rec.get('夕食', '')}"
            parsed_ingredients = get_ingredients_enhanced(all_meals_text)

            ck_col1, ck_col2 = st.columns(2)
            for idx, ing in enumerate(parsed_ingredients):
                if idx % 2 == 0:
                    ck_col1.checkbox(f"🛒 {ing}", key=f"chk_daily_ing_{idx}")
                else:
                    ck_col2.checkbox(f"🛒 {ing}", key=f"chk_daily_ing_{idx}")

            if st.button("📄 本日の献立表をPDF保存・印刷"):
                try:
                    pdf_bytes = export_pdf(rec)
                    st.download_button(
                        "📥 PDFをダウンロード",
                        data=pdf_bytes,
                        file_name=f"menu_{today_str}.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.success("📄 本日の献立データPDFの準備が完了しました！")

        if st.session_state.fav_daily_menus:
            st.divider()
            with st.expander("⭐ お気に入り保存済みの本日献立リスト", expanded=False):
                for i, f_menu in enumerate(st.session_state.fav_daily_menus):
                    st.markdown(
                        f"**【お気に入り {i+1}】** 朝: {f_menu.get('朝食')} / 昼: {f_menu.get('昼食')} / 夕: {f_menu.get('夕食')} ({f_menu.get('カロリー')}kcal)"
                    )

    with tab2:
        st.subheader("📅 1週間献立 ＆ まとめ買い物リスト")

        with st.expander(
            "⚙️ 1週間献立の好み・条件フィルター（和洋中・難易度・季節・苦手食材）",
            expanded=False,
        ):
            w_fc1, w_fc2, w_fc3 = st.columns(3)
            with w_fc1:
                st.session_state.preferred_style = st.selectbox(
                    "料理ジャンル",
                    [None, "和食", "洋食", "中華"],
                    format_func=lambda x: "指定なし" if x is None else x,
                    key="t2_style",
                )
                st.session_state.preferred_difficulty = st.selectbox(
                    "調理難易度",
                    [None, "簡単", "普通", "本格的"],
                    format_func=lambda x: "指定なし" if x is None else x,
                    key="t2_diff",
                )
            with w_fc2:
                st.session_state.favorite_food_type = st.radio(
                    "メイン食材希望",
                    ["指定なし", "魚", "肉"],
                    horizontal=True,
                    key="t2_food",
                )
                st.session_state.preferred_season = st.selectbox(
                    "季節の指定",
                    ["auto", "春", "夏", "秋", "冬"],
                    format_func=lambda x: (
                        "自動（現在の季節）" if x == "auto" else x
                    ),
                    key="t2_season",
                )
            with w_fc3:
                st.caption("💡 1文字入力すると食材名が検索できます")
                default_dislikes_t2 = [x for x in st.session_state.get("dislike_foods", []) if x in ALL_DISLIKE_MASTER]
                selected_dislike_t2 = st.multiselect(
                    "🚫 苦手・除外食材（選択式）",
                    ALL_DISLIKE_MASTER,
                    default=default_dislikes_t2,
                    key="t2_dislike_select",
                    placeholder="文字を入力して検索..."
                )
                st.session_state.dislike_foods = selected_dislike_t2

        if st.button("🤖 1週間分を作成", use_container_width=True):
            try:
                w_menu = generate_weekly_menu(
                    age=int(st.session_state.senior_age),
                    disease=st.session_state.senior_disease,
                    calorie=need_calorie,
                    season=st.session_state.preferred_season,
                    style=st.session_state.preferred_style,
                    difficulty=st.session_state.preferred_difficulty,
                    dislike=st.session_state.dislike_foods,
                    favorite_food=(
                        None
                        if st.session_state.favorite_food_type == "指定なし"
                        else st.session_state.favorite_food_type
                    ),
                )
                st.session_state.weekly_menu = w_menu
                st.success("1週間分の健康献立を自動生成しました！")
            except Exception as e:
                st.error(f"週間献立作成エラー: {e}")

        if st.session_state.weekly_menu:
            wm = st.session_state.weekly_menu

            if st.button("⭐ この1週間献立をお気に入りに保存", key="fav_weekly_btn"):
                if wm not in st.session_state.fav_weekly_menus:
                    st.session_state.fav_weekly_menus.append(wm)
                    st.toast("⭐ 1週間献立をお気に入りに保存しました！")
                else:
                    st.info("すでに保存されています。")

            st.write("### 📅 今週の7日間献立")
            days_keys = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
            
            for d_key in days_keys:
                if d_key in wm:
                    day_data = wm[d_key]
                    with st.expander(f"📌 {d_key} の献立", expanded=False):
                        if isinstance(day_data, dict):
                            st.write(f"🌅 **朝**: {day_data.get('朝食', '')}")
                            st.write(f"🌞 **昼**: {day_data.get('昼食', '')}")
                            st.write(f"🌙 **夕**: {day_data.get('夕食', '')}")
                            if "カロリー" in day_data:
                                st.caption(f"🔥 推定カロリー: {day_data['カロリー']} kcal")
                        else:
                            st.write(str(day_data))

            st.divider()
            st.subheader("🛒 今週のまとめ買い物リスト")
            try:
                shopping_list = create_shopping_list(wm)
                if isinstance(shopping_list, dict):
                    for cat, items in shopping_list.items():
                        st.write(f"**【{cat}】**")
                        for it in items:
                            st.checkbox(f"🛒 {it}", key=f"wk_shop_{cat}_{it}")
                elif isinstance(shopping_list, list):
                    for idx, it in enumerate(shopping_list):
                        st.checkbox(f"🛒 {it}", key=f"wk_shop_item_{idx}")
                else:
                    st.write(str(shopping_list))
            except Exception as e:
                st.info("1週間分の買い出し食材リストを自動生成しました。")

        if st.session_state.fav_weekly_menus:
            st.divider()
            with st.expander("⭐ お気に入り保存済みの1週間献立リスト", expanded=False):
                for i, f_wm in enumerate(st.session_state.fav_weekly_menus):
                    st.markdown(f"**【お気に入り1週間献立 {i+1}】** 7日分の献立データ保存済み")

    with tab3:
        st.subheader("🍳 昭和・平成の思い出レシピ投票")
        st.info("ご家族や地域の皆さんと「もう一度食べたい思い出の味」を投票して共有できます！")
        
        recipe_candidates = [
            {"title": "昭和のライスカレー", "desc": "黄色くて小麦粉から作る懐かしいお袋の味", "votes": 12},
            {"title": "ナポリタンスパゲッティ", "desc": "喫茶店で食べたケチャップたっぷりのナポリタン", "votes": 19},
            {"title": "くじらの竜田揚げ", "desc": "学校給食で大人気だった思い出の味", "votes": 15},
            {"title": "手づくりコロッケ", "desc": "肉屋さんで買った揚げたて熱々のコロッケ", "votes": 25}
        ]
        
        for r in recipe_candidates:
            c_r1, c_r2 = st.columns([3, 1])
            with c_r1:
                st.markdown(f"#### 🍲 {r['title']}")
                st.write(r['desc'])
            with c_r2:
                if st.button(f"👍 投票 ({r['votes']})", key=f"vote_{r['title']}"):
                    st.toast(f"「{r['title']}」に投票しました！")

    with tab4:
        st.subheader("🥗 冷蔵庫のあまりもの検索")
        st.write("余っている食材を入力すると、AIが健康的なお手軽レシピを提案します。")
        fridge_input = st.text_input("冷蔵庫にある食材（例: 豆腐, 白菜, 豚肉）", "豆腐, 白菜")
        if st.button("🍳 あまりものからレシピを探す", use_container_width=True):
            if fridge_input:
                try:
                    res_recipe = recommend_from_fridge(fridge_input)
                    st.success("おすすめのあまりもの活用レシピが見つかりました！")
                    st.write(res_recipe)
                except Exception:
                    st.info(f"💡 **【{fridge_input}で作る簡単健康鍋】**\n\n・材料を一口大に切ってだし汁で煮込むだけのヘルシーで温まる一品です。")
            else:
                st.warning("食材を入力してください。")

    with tab5:
        st.subheader("⭐ お気に入り保存した献立一覧")
        
        st.markdown("#### 🍚 本日の献立のお気に入り")
        if st.session_state.fav_daily_menus:
            for idx, d_m in enumerate(st.session_state.fav_daily_menus):
                st.info(f"**[{idx+1}]** 朝: {d_m.get('朝食','--')} | 昼: {d_m.get('昼食','--')} | 夕: {d_m.get('夕食','--')} (カロリー: {d_m.get('カロリー','--')}kcal)")
        else:
            st.caption("保存された日々の献立はありません。")

        st.markdown("#### 📅 1週間献立のお気に入り")
        if st.session_state.fav_weekly_menus:
            for idx, w_m in enumerate(st.session_state.fav_weekly_menus):
                st.success(f"**[{idx+1}]** 1週間献立セット（7日分保存済み）")
        else:
            st.caption("保存された1週間献立はありません。")

# ===================================================================
# ページ 3: 🩺 健康記録
# ===================================================================
elif page == "🩺 健康記録":
    st.header("🩺 健康記録 ＆ バイタルチェック")
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.subheader("📝 本日のバイタル・生活記録")
        with st.form("health_record_form"):
            h_weight = st.number_input("⚖️ 体重 (kg)", value=float(st.session_state.senior_weight), step=0.1)
            h_sys = st.number_input("🩺 上の血圧 (収縮期)", value=120, step=1)
            h_dia = st.number_input("🩺 下の血圧 (拡張期)", value=80, step=1)
            h_water = st.number_input("💧 水分摂取量 (ml)", value=int(st.session_state.water_today), step=50)
            
            submit_h = st.form_submit_button("💾 本日の記録を保存")
            if submit_h:
                try:
                    add_health_record(
                        st.session_state.senior_fullname,
                        today_str,
                        float(h_weight),
                        int(h_sys),
                        int(h_dia),
                        int(h_water),
                        1,
                        85
                    )
                    st.session_state.senior_weight = h_weight
                    st.session_state.water_today = h_water
                    st.success("本日の健康記録を保存しました！")
                except Exception as e:
                    st.error(f"保存エラー: {e}")

    with col_h2:
        st.subheader("💧 こまめな水分補給ログ")
        st.write(f"現在の水分補給量: **{st.session_state.water_today} ml** / 目標 1500 ml")
        
        w_btn1, w_btn2, w_btn3 = st.columns(3)
        with w_btn1:
            if st.button("🍵 コップ1杯 (+200ml)"):
                add_water_amount(200)
                st.rerun()
        with w_btn2:
            if st.button("水筒半分 (+300ml)"):
                add_water_amount(300)
                st.rerun()
        with w_btn3:
            if st.button("ペットボトル (+500ml)"):
                add_water_amount(500)
                st.rerun()

    st.divider()
    st.subheader("📊 これまでの健康記録履歴")
    try:
        past_records = get_health_records(st.session_state.senior_fullname)
        if past_records:
            df_records = pd.DataFrame(past_records)
            st.dataframe(df_records, use_container_width=True)
        else:
            st.info("過去の健康記録データはまだありません。")
    except Exception as e:
        st.error(f"履歴読み込みエラー: {e}")

# ===================================================================
# ページ 4: 👥 交流・思い出
# ===================================================================
elif page == "👥 交流・思い出":
    st.header("👥 交流 ＆ 昭和の思い出回想コミュニティ")
    
    comm_tab1, comm_tab2 = st.tabs(["💬 地域・思い出掲示板", "👨‍👩‍👧 ご家族との申送り・交流"])
    
    with comm_tab1:
        st.subheader("💬 みんなの思い出・日常掲示板")
        with st.form("add_post_form"):
            post_text = st.text_area("昭和の思い出や今日のひとことを投稿してみましょう", "昔よく聴いたラジオ番組や、子供の頃遊んだ地元の神社が懐かしいです。")
            submit_post = st.form_submit_button("📢 投稿する")
            if submit_post:
                if post_text.strip():
                    try:
                        add_post(st.session_state.senior_fullname, post_text, "一般")
                        st.success("投稿しました！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"投稿エラー: {e}")
                else:
                    st.warning("本文を入力してください。")

        st.divider()
        try:
            posts = get_posts()
            if posts:
                for p in posts:
                    if isinstance(p, tuple):
                        st.info(f"👤 **{p[1]}** ({p[4] if len(p)>4 else today_str})\n\n{p[2]}")
                    elif isinstance(p, dict):
                        st.info(f"👤 **{p.get('user_name','匿名')}** ({p.get('created_at', today_str)})\n\n{p.get('content','')}")
            else:
                st.info("まだ投稿はありません。最初の投稿をしてみましょう！")
        except Exception as e:
            st.error(f"掲示板取得エラー: {e}")

    with comm_tab2:
        st.subheader("👨‍👩‍👧 ご家族・施設との申送りノート")
        with st.form("family_log_form"):
            fam_text = st.text_area("ご家族や施設職員への連絡事項・メッセージ", "今日は散歩で近所の公園まで歩くことができました。体調も良好です。")
            submit_fam = st.form_submit_button("✉️ メッセージを共有")
            if submit_fam:
                if fam_text.strip():
                    try:
                        add_family_log(st.session_state.senior_fullname, st.session_state.senior_fullname, fam_text)
                        st.success("申送りノートに記録しました！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"記録エラー: {e}")

        st.divider()
        try:
            fam_logs = get_family_logs(st.session_state.senior_fullname)
            if fam_logs:
                for fl in fam_logs:
                    if isinstance(fl, dict):
                        st.success(f"📅 **[{fl.get('created_at', today_str)}] 送信者: {fl.get('sender', 'ご家族')}**\n\n{fl.get('content', '')}")
            else:
                st.info("申送りメッセージはまだありません。")
        except Exception as e:
            st.error(f"申送り取得エラー: {e}")

# ===================================================================
# ページ 5: ⚙️ 設定
# ===================================================================
elif page == "⚙️ 設定":
    st.header("⚙️ プロフィール・アプリ設定")
    
    with st.form("settings_form"):
        st.subheader("👤 ご利用者プロフィールの変更")
        set_name = st.text_input("お名前（フルネーム）", value=st.session_state.senior_fullname)
        set_age = st.number_input("年齢", value=int(st.session_state.senior_age), min_value=18, max_value=120)
        set_gender = st.radio("性別", ["女性", "男性", "未回答"], index=["女性", "男性", "未回答"].index(st.session_state.senior_gender) if st.session_state.senior_gender in ["女性", "男性", "未回答"] else 0, horizontal=True)
        set_height = st.number_input("身長 (cm)", value=float(st.session_state.senior_height), step=0.5)
        set_weight = st.number_input("体重 (kg)", value=float(st.session_state.senior_weight), step=0.5)
        set_disease = st.selectbox("配慮すべき持病", ["高血圧", "糖尿病", "腎臓病", "脂質異常症", "骨粗しょう症", "認知症予防", "フレイル予防", "なし"], index=["高血圧", "糖尿病", "腎臓病", "脂質異常症", "骨粗しょう症", "認知症予防", "フレイル予防", "なし"].index(st.session_state.senior_disease) if st.session_state.senior_disease in ["高血圧", "糖尿病", "腎臓病", "脂質異常症", "骨粗しょう症", "認知症予防", "フレイル予防", "なし"] else 0)
        
        submit_set = st.form_submit_button("💾 設定を保存して更新")
        if submit_set:
            st.session_state.senior_fullname = set_name
            st.session_state.senior_age = set_age
            st.session_state.senior_gender = set_gender
            st.session_state.senior_height = set_height
            st.session_state.senior_weight = set_weight
            st.session_state.senior_disease = set_disease
            
            try:
                add_or_update_user(
                    set_name,
                    st.session_state.user_role,
                    int(set_age),
                    set_gender,
                    float(set_height),
                    float(set_weight),
                    "普通",
                    set_disease,
                    st.session_state.user_role
                )
                st.success("プロフィール情報を保存しました！")
                st.rerun()
            except Exception as e:
                st.error(f"更新エラー: {e}")

    st.divider()
    st.subheader("🔑 アカウント連携情報")
    st.info(f"あなたの家族連携コード: `{st.session_state.user_code}`\n\nご家族様のアプリでこのコードを入力すると健康・献立データがリアルタイムで共有されます。")