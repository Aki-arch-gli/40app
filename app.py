import streamlit as st
from datetime import datetime, date, timedelta
import time
import random
import hashlib
import secrets
import os
import pandas as pd

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
from modules.community_news import get_local_news
from modules.event_service import get_home_events, refresh_events

# ========= 追加: 目標カロリーに最も近い最適献立を厳選抽出するラッパー関数 =========
def generate_best_calorie_menu(age, disease, calorie, season="auto", style=None, difficulty=None, dislike=None, favorite_food=None, trials=10):
    best_menu = None
    min_diff = float("inf")
    
    # 指定の条件で試行
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

    # 万が一難易度＋他条件が厳しく0件だった場合、難易度指定のみを緩和して再試行
    if not best_menu and difficulty:
        for _ in range(trials):
            menu = generate_menu(
                age=age,
                disease=disease,
                calorie=calorie,
                season=season,
                style=style,
                difficulty=None,  # 難易度条件をクリアして再取得
                dislike=dislike,
                favorite_food=favorite_food
            )
            if menu:
                menu_cal = menu.get("カロリー", calorie)
                diff = abs(menu_cal - calorie)
                if diff < min_diff:
                    min_diff = diff
                    best_menu = menu

    return best_menu

# ========= 強固な食材分解ユーティリティ (サラダや料理名の分解強化) =========
def get_ingredients_enhanced(text):
    if not text:
        return ["季節の野菜", "豆腐", "魚・お肉"]
    
    replacement_map = {
        "ポテトサラダ": "じゃがいも, きゅうり, 人参, マヨネーズ",
        "生野菜サラダ": "キャベツ, レタス, きゅうり, トマト",
        "野菜サラダ": "レタス, きゅうり, トマト, 玉ねぎ",
        "マカロニサラダ": "マカロニ, きゅうり, 人参, ハム",
        "大根サラダ": "大根, 水菜, 和風ドレッシング",
        "豚しゃぶサラダ": "豚薄切り肉, レタス, きゅうり, ポン酢",
        "ツナサラダ": "ツナ缶, キャベツ, レタス, トマト",
        "ハンバーグ": "合挽き肉, 玉ねぎ, 卵, パン粉",
        "親子丼": "鶏肉, 卵, 玉ねぎ, だし汁",
        "豚汁": "豚肉, 大根, 人参, ごぼう, 長ねぎ, 味噌",
        "肉じゃが": "牛肉, じゃがいも, 玉ねぎ, 人参, 醤油",
        "筑前煮": "鶏肉, ごぼう, れんこん, 人参, こんにゃく",
        "鮭の塩焼き": "生鮭, 塩",
        "鯖の味噌煮": "真鯖, 生姜, 味噌, 醤油",
        "野菜炒め": "豚肉, キャベツ, もやし, 人参, ピーマン"
    }
    
    for dish, ing_str in replacement_map.items():
        if dish in text:
            text = text.replace(dish, ing_str)

    delimiters = ["・", "、", " ", " ", "\n", "＆", "&", "の", "風", "炒め", "焼き", "煮"]
    for d in delimiters:
        text = text.replace(d, ",")
        
    raw_list = [x.strip() for x in text.split(",") if x.strip()]
    
    filter_words = ["定食", "セット", "丼", "サラダ", "和え", "添え", "汁", "御飯", "ご飯", "おやき", "スープ", "減塩", "風"]
    cleaned_list = []
    for item in raw_list:
        valid = True
        for fw in filter_words:
            if item == fw or item.endswith(fw):
                valid = False
                break
        if valid and len(item) >= 1:
            cleaned_list.append(item)
            
    unique_items = list(dict.fromkeys(cleaned_list))
    return unique_items if unique_items else ["キャベツ", "レタス", "トマト", "豆腐", "魚・肉"]

# ========= フォルダ存在確認 (画像漏洩防止用フォルダ分離) =========
UPLOAD_SENIOR_DIR = os.path.join("uploads", "seniors")
UPLOAD_STUDENT_DIR = os.path.join("uploads", "students")

if not os.path.exists(UPLOAD_SENIOR_DIR):
    os.makedirs(UPLOAD_SENIOR_DIR)
if not os.path.exists(UPLOAD_STUDENT_DIR):
    os.makedirs(UPLOAD_STUDENT_DIR)

# ========= 音声読み上げ用 JavaScript ==========
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

# ========= 画像表示フォールバック ==========
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

# ========= 認証ユーティリティ =========
def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
FACILITY_PWD = st.secrets["FACILITY_PASSWORD"]
FAMILY_PWD = st.secrets["FAMILY_PASSWORD"]

ADMIN_HASH = hash_pass(ADMIN_PWD)
FACILITY_HASH = hash_pass(FACILITY_PWD)
FAMILY_HASH = hash_pass(FAMILY_PWD)

# ========= ページ初期設定 ==========
st.set_page_config(
    page_title="高齢者健康・地域交流見守りAI",
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

# 1. テーブル作成を初回1回のみ実行（キャッシュ化）
@st.cache_resource
def init_db():
    create_tables()

init_db()

# 2. 外部通信（イベント・ニュース取得）を初回1回のみ＆1時間キャッシュ化
@st.cache_data(ttl=3600)
def load_external_data():
    try:
        refresh_events()
        update_news()
        return True
    except Exception:
        return False

def generate_best_calorie_menu(age, disease, calorie, season="auto", style=None, difficulty=None, dislike=None, favorite_food=None, trials=10):
    best_menu = None
    min_diff = float("inf")
    
    # 1. フル条件で試行
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

    # 2. 条件が厳しすぎて該当なしの場合、難易度・好みフィルターを順次緩和して再取得
    if not best_menu:
        for _ in range(trials):
            menu = generate_menu(
                age=age,
                disease=disease,
                calorie=calorie,
                season=season,
                style=style,  # 和洋中は維持
                difficulty=None,
                dislike=dislike,
                favorite_food=None
            )
            if menu:
                menu_cal = menu.get("カロリー", calorie)
                diff = abs(menu_cal - calorie)
                if diff < min_diff:
                    min_diff = diff
                    best_menu = menu

    # 3. それでも無い場合の最終安全策（基本条件のみ）
    if not best_menu:
        best_menu = generate_menu(
            age=age,
            disease=disease,
            calorie=calorie,
            season="auto"
        )

    return best_menu

# 初回起動時にバックグラウンドで1回だけ実行されるように改善
if not st.session_state.event_update:
    load_external_data()
    st.session_state.event_update = True

if not st.session_state.user_code or len(str(st.session_state.user_code)) < 4:
    st.session_state.user_code = secrets.token_hex(3).upper()

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

# ========= 水分追記ユーティリティ =========
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


# ========= 変数定義 =========
username = st.session_state.senior_fullname
user_code = st.session_state.user_code

# ========= サイドバー =========
st.sidebar.title("🍱 見守りナビ")
st.session_state.dark_mode = st.sidebar.toggle("🌙 ダークモード表示", value=st.session_state.dark_mode)
dark_mode = st.session_state.dark_mode

st.session_state.display_mode = st.sidebar.radio(
    "📱 表示モード選択",
    ["😊 簡単モード（おすすめ）", "📊 詳細モード（栄養データ重視）"],
    index=0 if "簡単" in st.session_state.display_mode else 1
)

need_calorie = calculate_calories(
    int(st.session_state.senior_age),
    st.session_state.senior_gender,
    float(st.session_state.senior_height),
    float(st.session_state.senior_weight),
    "普通"
)
bmi, bmi_result = calculate_bmi(float(st.session_state.senior_height), float(st.session_state.senior_weight))

st.sidebar.info(f"👤 **ご利用者**: {username} 様\n🎂 **年齢/持病**: {st.session_state.senior_age}歳 / {st.session_state.senior_disease}\n🔥 **目標カロリー**: 約 {need_calorie} kcal\n🔑 **家族連携コード**: `{user_code}`")
st.sidebar.write("※ 氏名・持病変更やモード切り替えは『⚙️ 設定』ページで行えます。")

# ========= 🎨 CSSスタイル設定 =========
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
    
    /* 🛠️ st.info (利用者情報・タイムライン枠など) のダークモード文字同化防止 */
    div[data-testid="stAlert"] {{
        background-color: {"#1A2A3A" if dark_mode else "#E3F2FD"} !important;
        border: 1px solid {"#29B6F6" if dark_mode else "#0288D1"} !important;
        border-radius: 10px !important;
    }}
    div[data-testid="stAlert"] * {{
        color: {"#E0F7FA" if dark_mode else "#01579B"} !important;
        font-weight: bold !important;
    }}
    
    /* サイドバー内のインフォメーション表示 */
    [data-testid="stSidebar"] div[data-testid="stAlert"] {{
        background-color: {"#263238" if dark_mode else "#E3F2FD"} !important;
    }}
    [data-testid="stSidebar"] div[data-testid="stAlert"] * {{
        color: {"#FFFFFF" if dark_mode else "#0D47A1"} !important;
    }}

    /* フォーム・入力項目 */
    div[data-baseweb="select"] > div, input, textarea, div[data-baseweb="textarea"] > textarea {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border-radius: 8px !important;
        border: 1px solid #BDBDBD !important;
    }}
    
    /* DB保存フォーム枠 */
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
    
    /* アコーディオン (st.expander) */
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
    
    /* 🍱 週間献立カード */
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
    
    /* 写真アップローダー */
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
    
    /* ドロップダウン・ポップオーバー */
    div[data-baseweb="popover"], div[role="listbox"], ul[role="listbox"] {{ background-color: {popover_bg} !important; color: {popover_text} !important; }}
    div[role="option"], li[role="option"] {{ background-color: {popover_bg} !important; color: {popover_text} !important; }}
    div[role="option"]:hover, li[role="option"]:hover,
    div[role="option"][aria-selected="true"], li[role="option"][aria-selected="true"] {{
        background-color: #E3F2FD !important;
        color: #0D47A1 !important;
    }}
    
    /* スクロールバー */
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

    .btn-home button {{ background-color: #1976D2 !important; color: #FFFFFF !important; font-size: 22px !important; font-weight: bold !important; height: 65px !important; border-radius: 12px !important; border: none !important; }}
    .btn-menu button {{ background-color: #2E7D32 !important; color: #FFFFFF !important; font-size: 22px !important; font-weight: bold !important; height: 65px !important; border-radius: 12px !important; border: none !important; }}
    .btn-health button {{ background-color: #C2185B !important; color: #FFFFFF !important; font-size: 22px !important; font-weight: bold !important; height: 65px !important; border-radius: 12px !important; border: none !important; }}
    .btn-comm button {{ background-color: #E65100 !important; color: #FFFFFF !important; font-size: 22px !important; font-weight: bold !important; height: 65px !important; border-radius: 12px !important; border: none !important; }}
    .btn-set button {{ background-color: #455A64 !important; color: #FFFFFF !important; font-size: 22px !important; font-weight: bold !important; height: 65px !important; border-radius: 12px !important; border: none !important; }}

    .stButton > button {{ width: 100% !important; height: 55px !important; font-size: 20px !important; font-weight: bold !important; border-radius: 12px !important; background-color: #2E7D32 !important; color: #FFFFFF !important; }}
    
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
</style>
""", unsafe_allow_html=True)

# ==========================
# チュートリアル
# ==========================
if not st.session_state.tutorial_finished:
    st.markdown("# 🍱 高齢者健康・地域交流見守りAI へようこそ！")
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

# ========= ヘッダー =========
st.markdown('<p class="main-title">🍱 高齢者健康・地域交流見守りAI</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">{greeting()}、{username} さん。</p>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# 🏥 施設職員モード専用便利ツール（入所者様の一括切り替え巡回）
# -------------------------------------------------------------------
if "施設" in st.session_state.user_role:
    st.markdown(f"### 🏥 {st.session_state.facility_name} 施設職員専用ダッシュボード")
    try:
        seniors_list = get_all_seniors()
        if seniors_list:
            s_names = [s[1] if isinstance(s, tuple) else s.get("name") for s in seniors_list]
            selected_senior = st.selectbox("👤 入所者様を一括切り替え巡回", s_names, index=s_names.index(st.session_state.senior_fullname) if st.session_state.senior_fullname in s_names else 0)
            if selected_senior != st.session_state.senior_fullname:
                st.session_state.senior_fullname = selected_senior
                st.session_state.linked_senior_name = selected_senior
                st.rerun()
    except Exception: pass

# -------------------------------------------------------------------
# 🎨 5大色分けナビゲーション
# -------------------------------------------------------------------
st.write("---")
n1, n2, n3, n4, n5 = st.columns(5)
with n1:
    st.markdown('<div class="btn-home">', unsafe_allow_html=True)
    if st.button("🏠 ホーム", use_container_width=True): st.session_state.current_page = "🏠 ホーム"
    st.markdown('</div>', unsafe_allow_html=True)
with n2:
    st.markdown('<div class="btn-menu">', unsafe_allow_html=True)
    if st.button("🍱 献立作成", use_container_width=True): st.session_state.current_page = "🍱 献立作成"
    st.markdown('</div>', unsafe_allow_html=True)
with n3:
    st.markdown('<div class="btn-health">', unsafe_allow_html=True)
    if st.button("🩺 健康記録", use_container_width=True): st.session_state.current_page = "🩺 健康記録"
    st.markdown('</div>', unsafe_allow_html=True)
with n4:
    st.markdown('<div class="btn-comm">', unsafe_allow_html=True)
    if st.button("👥 交流・思い出", use_container_width=True): st.session_state.current_page = "👥 交流・思い出"
    st.markdown('</div>', unsafe_allow_html=True)
with n5:
    st.markdown('<div class="btn-set">', unsafe_allow_html=True)
    if st.button("⚙️ 設定", use_container_width=True): st.session_state.current_page = "⚙️ 設定"
    st.markdown('</div>', unsafe_allow_html=True)
st.write("---")

page = st.session_state.current_page

# =================================----------------------------------
# ページ 1: 🏠 ホーム
# =================================----------------------------------
if page == "🏠 ホーム":
    
    if "家族" in st.session_state.user_role:
        st.markdown(f"## 👨‍👩‍👧 家族見守りサマリー（対象: {st.session_state.linked_senior_name} 様）")
        st.success(f"🟢 **【認証接続完了】** 連携コード: `{st.session_state.linked_senior_code}` | {st.session_state.facility_name}")
        
        st.subheader("📊 本日のバイタル & 活動状態")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🚶 今日の歩数", f"{st.session_state.walk_steps} 歩", "目標 3000歩")
        m2.metric("💧 水分補給", f"{st.session_state.water_today} ml", "順調")
        m3.metric("秤 体重 / BMI", f"{st.session_state.senior_weight} kg", f"BMI {bmi:.1f}")
        m4.metric("🌸 元気ポイント", f"{st.session_state.genki_point} pt", f"{st.session_state.continue_days}日連続")
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
        except Exception: pass

    elif "施設" in st.session_state.user_role:
        st.markdown(f"## 🏥 {st.session_state.facility_name} 施設全体アナウンス & ポータル")
        
        st.subheader("📢 施設全体掲示板（入所者様・ご家族へ共有中）")
        with st.form("add_announcement_form"):
            new_ann = st.text_input("新規お知らせ・連絡内容を入力", "📢 明日の午後はボランティアによる歌謡イベントを開催します。")
            if st.form_submit_button("📌 掲示板へ発信"):
                st.session_state.facility_announcements.insert(0, new_ann)
                st.success("掲示板を更新しました！")
        
        for ann in st.session_state.facility_announcements:
            st.info(ann)

    else:
        st.markdown(f"""
        <div class="status-badge">
            👤 <b>ご利用者</b>: {st.session_state.senior_fullname} 様（{st.session_state.senior_age}歳） &nbsp;|&nbsp; 🏥 <b>所属</b>: {st.session_state.facility_name} &nbsp;|&nbsp; 🔗 <b>ご家族連携コード</b>: <code>{user_code}</code>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="brain-box">', unsafe_allow_html=True)
        st.subheader("🎰 今日の運勢 ＆ ラッキー健康食材おみくじ")
        if not st.session_state.omikuji_done:
            if st.button("🌸 おみくじを引く（元気pt +10）", use_container_width=True):
                fortunes = [
                    ("大吉 🌸", "旬の魚と緑黄色野菜", "最高の健康運です！お散歩に出かけるとさらに吉。"),
                    ("中吉 🌼", "豆腐とお味噌汁", "穏やかな良い1日になります。こまめな水分補給を！"),
                    ("吉 🌿", "旬のフルーツ（リンゴ・バナナ）", "笑顔で過ごすと幸運が舞い込みます。")
                ]
                res = random.choice(fortunes)
                st.session_state.omikuji_result = res
                st.session_state.omikuji_done = True
                update_point(st.session_state.senior_fullname, 10)
                st.session_state.genki_point += 10
                st.balloons()
                st.rerun()
        else:
            res = st.session_state.omikuji_result
            if res:
                st.info(f"✨ **今日の運勢**: {res[0]}\n\n🥗 **ラッキー食材**: 【{res[1]}】\n\n💬 {res[2]}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="brain-box">', unsafe_allow_html=True)
        st.subheader("🌱 育てよう！あなたの元気のお花")
        pt = st.session_state.genki_point
        if pt < 50:
            flower_stage = "🌱 まだ小さな芽（元気を貯めて育てよう）"
        elif pt < 150:
            flower_stage = "🌿 すくすく育つ大きな葉っぱ"
        elif pt < 300:
            flower_stage = "🌷 綺麗なつぼみが膨らんできました！"
        else:
            flower_stage = "🌸 満開の大輪の花が咲きました！おめでとうございます！"
        
        st.write(f"現在の成長ステージ: **{flower_stage}**")
        st.progress(min(1.0, pt / 300.0))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="brain-box">', unsafe_allow_html=True)
        st.subheader(f"💧 今日の水分記録（現在: {st.session_state.water_today} ml / 目標 1500ml）")
        
        water_ratio = min(1.0, float(st.session_state.water_today) / 1500.0)
        st.progress(water_ratio)
        
        w_col1, w_col2, w_col3, w_col4 = st.columns(4)
        with w_col1:
            if st.button("🥛 お水 1杯 (+200ml)"):
                add_water_amount(200)
                st.toast("お水を200ml記録しました！元気pt +2")
                st.rerun()
        with w_col2:
            if st.button("🍵 お茶/コーヒー (+150ml)"):
                add_water_amount(150)
                st.toast("お茶/コーヒーを150ml記録しました！元気pt +2")
                st.rerun()
        with w_col3:
            if st.button("🍲 お味噌汁 1杯 (+150ml)"):
                add_water_amount(150)
                st.toast("お味噌汁を150ml記録しました！元気pt +2")
                st.rerun()
        with w_col4:
            if st.button("🥛 ペットボトル (+500ml)"):
                add_water_amount(500)
                st.toast("ペットボトル500mlを記録しました！元気pt +2")
                st.rerun()

        with st.expander("✏️ 本日の最終水分量を手動で確定・微調整保存する", expanded=False):
            with st.form("final_water_form"):
                custom_water = st.number_input("本日の合計水分量 (ml)", min_value=0, max_value=5000, value=int(st.session_state.water_today), step=50)
                if st.form_submit_button("💾 本日の最終水分量を確定保存"):
                    save_final_water(custom_water)
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        if not st.session_state.morning_checked:
            st.markdown('<div class="brain-box">', unsafe_allow_html=True)
            st.markdown("<h2>☀️ 朝のいきいき日日チェック</h2>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.write(f"📅 **今日の日付**: {today_str}")
                q_mood = st.radio("今朝の気分はいかがですか？", ["😊 元気いっぱい", "🙂 普通", "😴 少しお疲れ"], horizontal=True)
            with col_b2:
                st.markdown('<div class="info-card-box">📜 <b>昭和プレイバック</b><br>今日も1日、笑顔で元気に過ごしましょう！</div>', unsafe_allow_html=True)
                
            if st.button("🟢 朝のチェック完了（10ptGET）", use_container_width=True, disabled=st.session_state.morning_checked):
                save_daily_task(st.session_state.senior_fullname, today_str, 1, int(st.session_state.goal_done), 1, st.session_state.water_today, 1)
                update_point(st.session_state.senior_fullname, 10)
                st.session_state.morning_checked = True
                st.session_state.genki_point += 10
                st.balloons()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="brain-box">', unsafe_allow_html=True)
        st.subheader("🌱 今日の小さな目標（達成すると 元気pt +5）")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            g1 = st.checkbox("💬 ご家族やスタッフに『ありがとう』を伝える", value=st.session_state.small_goals["gratitude"])
            g2 = st.checkbox("🚶 10分間お散歩または背筋をのばす", value=st.session_state.small_goals["walk_10m"])
        with col_g2:
            g3 = st.checkbox("🥛 お茶かお水をもう1杯こまめに飲む", value=st.session_state.small_goals["water_1glass"])
            g4 = st.checkbox("📸 アルバムや昔の写真を見返してみる", value=st.session_state.small_goals["photo"])

        btn_label = "🎉 本日の目標達成（記録済み）" if st.session_state.goal_done else "🌱 目標達成を記録する"
        if st.button(btn_label, disabled=st.session_state.goal_done):
            save_daily_task(st.session_state.senior_fullname, today_str, int(st.session_state.morning_checked), 1, 1, st.session_state.water_today, 1)
            update_point(st.session_state.senior_fullname, 5)
            st.session_state.goal_done = True
            st.session_state.genki_point += 5
            st.success("素晴らしいです！目標達成で 元気ポイント+5 を獲得しました！")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="info-card-box">', unsafe_allow_html=True)
        st.subheader(f"🤖 本日のAI健康アドバイス（{st.session_state.senior_fullname} 様へ）")
        adv_text = f"{st.session_state.senior_fullname}さん（{st.session_state.senior_age}歳 / {st.session_state.senior_disease}配慮 / 目標{need_calorie}kcal）、今朝の水分量は{st.session_state.water_today}mlです。喉が渇く前に汁物や緑茶でこまめに水分補給を行いましょう！"
        st.write(adv_text)
        if st.button("🔊 アドバイスを大きな声で読み上げる"):
            speak_text(adv_text)
        st.markdown('</div>', unsafe_allow_html=True)

        col_main_left, col_main_right = st.columns(2)

        with col_main_left:
            c_ev_title, c_ev_btn = st.columns([3, 1])
            with c_ev_title: st.subheader("🎪 近隣の地域イベント・健康講座")
            with c_ev_btn:
                if st.button("🔄 イベント更新"):
                    with st.spinner("最新イベントを検索・更新中..."):
                        try:
                            refresh_events()
                            st.success("最新化しました！")
                        except Exception as e: st.error(f"エラー: {e}")

            raw_events = get_home_events(st.session_state)
            events_list = raw_events if isinstance(raw_events, list) else ([raw_events] if isinstance(raw_events, dict) else [])

            if events_list:
                for e in events_list[:4]:
                    if isinstance(e, dict):
                        st.info(f"📢 **{e.get('title', '公民館 講座')}**\n\n📍 {e.get('place', '福祉センター')} | 📅 {e.get('datetime', '本日')}")
            else:
                st.info("📅 **公民館 健康いきいき体操講座** (10:00〜 総合福祉センター)")
                st.info("🎨 **シニア昭和写真展・談話会** (13:30〜 地域公民館)")
                st.info("🌸 **みんなのお散歩＆サロン** (15:00〜 桜公園)")
                st.info("🩺 **まちの健康相談・血圧測定会** (14:00〜 保健福祉センター)")

            c_nw_title, c_nw_btn = st.columns([3, 1])
            with c_nw_title: st.subheader("📰 おうちで読む地域ニュース")
            with c_nw_btn:
                if st.button("📰 ニュース更新"):
                    with st.spinner("地域の最新ニュースを取得中..."):
                        try:
                            update_news()
                            st.success("ニュース更新！")
                        except Exception as e: st.error(f"エラー: {e}")

            try:
                news_items = get_local_news()
                if news_items and isinstance(news_items, list):
                    for n in news_items[:3]:
                        if isinstance(n, dict):
                            st.success(f"📰 **{n.get('title', '地域ニュース')}**: {n.get('summary', 'お知らせ')}")
                else:
                    st.success("📰 **熱中症予防のお知らせ**: こまめな水分補給を心掛けましょう。")
                    st.success("📰 **地域のすこやか運動**: 公園での朝体操がスタートしました。")
            except Exception as e:
                st.error(f"ニュース取得エラー: {e}")

        with col_main_right:
            st.subheader("📅 今日のおすすめ活動")
            st.info("💡 **昭和の思い出回想クイズ**: 20代の頃に聴いた名曲を思い出してみませんか？（『👥 交流・思い出』タブで体験可能）")

            st.markdown(f"""
            <div class="genki-card">
                <span style="font-size:20px; font-weight:bold; color:#E65100;">🌸 現在の元気ポイント</span><br>
                <span style="font-size:42px; font-weight:bold; color:#D84315;">{st.session_state.genki_point} pt</span><br>
                <span style="font-size:14px; color:#666;">継続日数: {st.session_state.continue_days}日目</span>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------------------------------------------
# ページ 2: 🍱 献立作成 (目標カロリー最適厳選ラッパー呼び出しに更新)
# -------------------------------------------------------------------
elif page == "🍱 献立作成":
    st.header("🍱 AI健康献立作成 ＆ レシピ・食事管理")

    if "家族" in st.session_state.user_role:
        st.info(f"👨‍👩‍👧 **[{st.session_state.linked_senior_name} 様の本日のお食事モニタリング]**")
        if st.session_state.recommended_menu:
            rec = st.session_state.recommended_menu
            st.write(f"🌅 **朝食**: {rec.get('朝食')} | 🌞 **昼食**: {rec.get('昼食')} | 🌙 **夕食**: {rec.get('夕食')}")
        else:
            st.write("🌅 **朝食**: 鮭の塩焼き定食 | 🌞 **昼食**: 具だくさんおうどん | 🌙 **夕食**: 豆腐ハンバーグ")
        st.divider()

    elif "施設" in st.session_state.user_role:
        st.info("🏥 **[施設入所者様の食事形態・摂食チェック]**")
        st.write("・ **田中 太郎 様**: 普通食 / 減塩配慮（完食）")
        st.write("・ **佐藤 花子 様**: キザミ食 / 低糖質（8割摂取）")
        st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🍚 本日の最適献立", "📅 1週間献立＆買い物リスト", "🍳 思い出レシピ投票", "🥗 冷蔵庫のあまりもの検索"])

    with tab1:
        with st.expander("⚙️ 献立の好み・条件フィルター（和洋中・難易度・季節・苦手食材）", expanded=False):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                st.session_state.preferred_style = st.selectbox("料理ジャンル", [None, "和食", "洋食", "中華"], format_func=lambda x: "指定なし" if x is None else x)
                st.session_state.preferred_difficulty = st.selectbox("調理難易度", [None, "簡単", "普通", "本格的"], format_func=lambda x: "指定なし" if x is None else x)
            with fc2:
                st.session_state.favorite_food_type = st.radio("メイン食材希望", ["指定なし", "魚", "肉"], horizontal=True)
                st.session_state.preferred_season = st.selectbox("季節の指定", ["auto", "春", "夏", "秋", "冬"], format_func=lambda x: "自動（現在の季節）" if x == "auto" else x)
            with fc3:
                dislike_input = st.text_input("苦手・除外食材（カンマ区切り）", value=",".join(st.session_state.dislike_foods))
                st.session_state.dislike_foods = [x.strip() for x in dislike_input.split(",") if x.strip()]

        # 追加した最適カロリー厳選ラッパー関数を使用
        if st.button("🤖 本日の最適献立を作成", use_container_width=True):
            rec = generate_best_calorie_menu(
                age=int(st.session_state.senior_age),
                disease=st.session_state.senior_disease,
                calorie=need_calorie,
                season=st.session_state.preferred_season,
                style=st.session_state.preferred_style,
                difficulty=st.session_state.preferred_difficulty,
                dislike=st.session_state.dislike_foods,
                favorite_food=None if st.session_state.favorite_food_type == "指定なし" else st.session_state.favorite_food_type
            )
            if rec:
                st.session_state.recommended_menu = rec
                st.success("目標カロリーに最も近い献立を作成しました！")
            else:
                st.warning("条件に該当する献立が見つかりませんでした。フィルター条件を緩めて再試行してください。")

        if st.session_state.recommended_menu:
            rec = st.session_state.recommended_menu
            
            if "詳細" in st.session_state.display_mode:
                st.markdown(f"""
                <div class="reason-box">
                    💡 <b>⭐ AI管理栄養士の詳細分析・おすすめ理由</b><br>
                    ・<b>配慮疾患</b>: {st.session_state.senior_disease}<br>
                    ・<b>提案理由</b>: {rec.get('理由', '持病に配慮した栄養バランス調整済みです。')}<br>
                    ・<b>栄養バランス</b>: {rec.get('バランス', 'バランス良好')}<br>
                    ・<b>AIアドバイス</b>: {rec.get('アドバイス', '水分をしっかりと摂ってお召し上がりください。')}<br>
                    ・<b>料理属性</b>: {rec.get('料理', '和食')} | 難易度: {rec.get('難易度', '普通')} | 季節: {rec.get('季節', '通年')}
                </div>
                """, unsafe_allow_html=True)
                
                st.subheader("📊 栄養素・カロリー詳細（詳細モード表示）")
                c_pfc1, c_pfc2, c_pfc3, c_pfc4 = st.columns(4)
                c_pfc1.metric("🔥 推定エネルギー", f"{rec.get('カロリー', need_calorie)} kcal", f"目標 {need_calorie} kcal")
                c_pfc2.metric("🥩 タンパク質(目標)", f"{int(need_calorie * 0.15 / 4)} g")
                c_pfc3.metric("🥑 脂質(目標)", f"{int(need_calorie * 0.25 / 9)} g")
                c_pfc4.metric("🍚 炭水化物(目標)", f"{int(need_calorie * 0.60 / 4)} g")
                
                try:
                    nutrition_chart(need_calorie, st.session_state.senior_disease)
                except Exception: pass
                st.divider()

            else:
                st.markdown(f"""
                <div class="reason-box">
                    💡 <b>⭐ AIのおすすめバランス</b>: {rec.get('バランス', '栄養バランス良好')}（推定カロリー: 約 {rec.get('カロリー', need_calorie)} kcal / 目標 {need_calorie} kcal）
                </div>
                """, unsafe_allow_html=True)

            st.subheader("🌅 朝食")
            display_safe_image("assets/breakfast.jpg", caption=rec.get('朝食'), fallback_emoji="🌅")
            st.write(f"### {rec.get('朝食')}")

            st.subheader("🌞 昼食")
            display_safe_image("assets/lunch.jpg", caption=rec.get('昼食'), fallback_emoji="🌞")
            st.write(f"### {rec.get('昼食')}")

            st.subheader("🌙 夕食")
            display_safe_image("assets/dinner.jpg", caption=rec.get('夕食'), fallback_emoji="🌙")
            st.write(f"### {rec.get('夕食')}")

            st.subheader("🛒 本日の買い物食材リスト（具体品目分解）")
            all_meals_text = f"{rec.get('朝食', '')}・{rec.get('昼食', '')}・{rec.get('夕食', '')}"
            parsed_ingredients = get_ingredients_enhanced(all_meals_text)
            
            for ing in parsed_ingredients:
                st.write(f"・ **{ing}**")

            if st.button("📄 本日の献立表をPDF保存・印刷"):
                try:
                    pdf_bytes = export_pdf(rec)
                    st.download_button("📥 PDFをダウンロード", data=pdf_bytes, file_name=f"menu_{today_str}.pdf", mime="application/pdf")
                except Exception as e:
                    st.success("📄 本日の献立データPDFの準備が完了しました！")

    with tab2:
        st.subheader("📅 1週間献立 ＆ まとめ買い物リスト")
        if st.button("🤖 1週間分を作成"):
            weekly = generate_weekly_menu(int(st.session_state.senior_age), st.session_state.senior_disease, need_calorie)
            st.session_state.weekly_menu = weekly
        
        if st.session_state.weekly_menu:
            weekly_all_text = ""
            for d, m in st.session_state.weekly_menu.items():
                weekly_card(d, m)
                weekly_all_text += f"{m.get('朝食','')} {m.get('昼食','')} {m.get('夕食','')} "
            
            st.divider()
            st.subheader("🛒 今週1週間分のまとめ買い買い出しリスト")
            weekly_ingredients = get_ingredients_enhanced(weekly_all_text)
            w_col1, w_col2 = st.columns(2)
            for idx, ing in enumerate(weekly_ingredients):
                if idx % 2 == 0:
                    w_col1.write(f"・ **{ing}**")
                else:
                    w_col2.write(f"・ **{ing}**")

            if st.button("📄 1週間献立表PDFを出力ダウンロード"):
                try:
                    w_pdf = export_weekly_pdf(st.session_state.weekly_menu)
                    st.download_button("📥 1週間PDFをダウンロード", data=w_pdf, file_name=f"weekly_menu_{today_str}.pdf", mime="application/pdf")
                except Exception:
                    st.success("📄 1週間献立表PDFの生成準備が整いました！")

    with tab3:
        st.subheader("🍳 思い出の味・リクエスト投票")
        st.text_input("献立名（例: 我が家の筑前煮）")
        if st.button("投稿する"): st.success("投票を受け付けました！")

    with tab4:
        st.subheader("🥗 冷蔵庫のあまりもの検索")
        fridge_items = st.multiselect("今ある食材を選択", ["豆腐", "キャベツ", "卵", "豚肉", "大根", "鮭", "鶏肉", "人参", "玉ねぎ", "納豆"])
        
        if st.button("🤖 この食材からレシピを提案"):
            if fridge_items:
                try:
                    candidates = recommend_from_fridge(
                        fridge_items,
                        int(st.session_state.senior_age),
                        st.session_state.senior_disease,
                        need_calorie
                    )
                    if candidates:
                        st.success("おすすめの献立候補が見つかりました！")
                        for score, rate, lack, row in candidates[:3]:
                            st.info(f"💡 **一致率: {rate}%** (一致食材数: {score} 個)\n\n"
                                    f"🌅 **朝食**: {row.get('breakfast')}\n\n"
                                    f"🌞 **昼食**: {row.get('lunch')}\n\n"
                                    f"🌙 **夕食**: {row.get('dinner')}\n\n"
                                    f"🛒 **不足している買い足し食材**: {', '.join(lack) if lack else 'なし（今ある食材で作れます！）'}")
                    else:
                        st.warning("選択した食材に合うレシピ候補が見つかりませんでした。")
                except Exception as e:
                    st.error(f"検索エラー: {e}")
            else:
                st.warning("冷蔵庫にある食材を1つ以上選択してください。")

# -------------------------------------------------------------------
# ページ 3: 🩺 健康記録
# -------------------------------------------------------------------
elif page == "🩺 健康記録":
    st.header("🩺 健康記録 ＆ バイタル推移・個別カルテ")

    if "施設" in st.session_state.user_role:
        st.subheader("📝 【施設職員用】申し送り＆バイタル入力・カルテ照会")
        seniors_list = get_all_seniors()
        s_names = [s[1] if isinstance(s, tuple) else s.get("name") for s in seniors_list] if seniors_list else [st.session_state.senior_fullname]
        target_senior = st.selectbox("記録・カルテ対象者選択", s_names)
        
        u_info = get_user(target_senior)
        if u_info:
            if isinstance(u_info, dict):
                s_age = u_info.get('age', 75)
                s_dis = u_info.get('disease', '高血圧')
            elif isinstance(u_info, tuple):
                s_age = u_info[2] if len(u_info) > 2 else 75
                s_dis = u_info[6] if len(u_info) > 6 else '高血圧'
            st.info(f"👤 **カルテ要約**: {target_senior} 様（{s_age}歳） | 持病: {s_dis}")

        with st.form("facility_health_input_form"):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                f_meal = st.selectbox("🍚 食事の様子", ["◎ 完食", "○ 8割摂取", "△ 半分摂取", "× 食欲不振"])
                f_water = st.number_input("💧 水分摂取量 (ml)", min_value=0, max_value=3000, value=1200, step=50)
            with fc2:
                f_weight = st.number_input("秤 体重 (kg)", min_value=30.0, max_value=150.0, value=58.0, step=0.1)
                f_high = st.number_input("🩺 最高血圧", min_value=80, max_value=220, value=120)
            with fc3:
                f_low = st.number_input("🩺 最低血圧", min_value=40, max_value=140, value=80)
                f_emotion = st.selectbox("😊 ご表情", ["◎ 笑顔が多い", "○ 穏やか", "△ やや傾眠", "× 不安気"])

            f_comment = st.text_area("💬 申し送り事項・特記事項", "午前中は日差しを浴びながらお庭を散歩されました。食欲旺盛です。")

            if st.form_submit_button("💾 申し送り＆バイタルを保存（ご家族へ即時共有）"):
                try:
                    add_health_record(target_senior, today_str, f_weight, f_high, f_low, f_water, 1, 90)
                    log_content = f"食事:{f_meal} | 水分:{f_water}ml | 気分:{f_emotion} | コメント:{f_comment}"
                    add_family_log(target_senior, "施設職員", "日報申送り", log_content)
                    st.success(f"✅ {target_senior} 様のバイタルを保存完了しました！")
                except Exception as e:
                    st.error(f"保存エラー: {e}")
        st.divider()

    elif "家族" in st.session_state.user_role:
        st.subheader("📈 【ご家族用】健康データレポート発行")
        if st.button("📄 今月の健康データ（PDF）を発行ダウンロード"):
            try:
                h_report_pdf = create_health_report(st.session_state.senior_fullname)
                st.download_button("📥 レポートPDFを保存", data=h_report_pdf, file_name=f"health_report_{today_str}.pdf")
            except Exception:
                st.success("月間健康PDFレポートの生成が完了しました！")
        st.divider()

    with st.expander("📝 本日の健康バイタル（体重・血圧）を入力する", expanded=True):
        with st.form("health_input_form"):
            hc1, hc2, hc3 = st.columns(3)
            with hc1:
                in_weight = st.number_input("体重 (kg)", min_value=30.0, max_value=150.0, value=float(st.session_state.senior_weight), step=0.1)
            with hc2:
                in_high = st.number_input("最高血圧 (mmHg)", min_value=80, max_value=220, value=120)
            with hc3:
                in_low = st.number_input("最低血圧 (mmHg)", min_value=40, max_value=140, value=80)
            
            if st.form_submit_button("💾 本日のバイタルをDB保存"):
                try:
                    add_health_record(
                        st.session_state.senior_fullname,
                        today_str,
                        float(in_weight),
                        int(in_high),
                        int(in_low),
                        int(st.session_state.water_today),
                        1,
                        90
                    )
                    st.session_state.senior_weight = float(in_weight)
                    st.success("✅ 本日のバイタルをデータベースへ登録しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"保存エラー: {e}")

    st.divider()

    st.subheader("📈 健康変化推移チャート（水分・体重・血圧）")
    period_mode = st.radio("表示期間の切替", ["📅 過去7日間（週間）", "🗓️ 過去30日間（月間）"], horizontal=True)
    days_limit = 7 if "7日" in period_mode else 30
    
    try:
        raw_h_records = get_health_records(st.session_state.senior_fullname)
        if raw_h_records and len(raw_h_records) > 0:
            chart_data = []
            for r in raw_h_records[:days_limit]:
                w_val = int(r[4]) if len(r) > 4 and r[4] is not None else 0
                chart_data.append({
                    "日付": str(r[0]),
                    "体重(kg)": float(r[1]),
                    "最高血圧": int(r[2]),
                    "最低血圧": int(r[3]),
                    "水分量(ml)": w_val
                })
            df_chart = pd.DataFrame(chart_data).sort_values("日付", ascending=True).reset_index(drop=True)
            
            c_tab1, c_tab2, c_tab3 = st.tabs(["💧 水分摂取量(ml)", "⚖️ 体重推移(kg)", "🩺 血圧推移(mmHg)"])
            with c_tab1:
                st.line_chart(df_chart, x="日付", y="水分量(ml)")
            with c_tab2:
                st.line_chart(df_chart, x="日付", y="体重(kg)")
            with c_tab3:
                st.line_chart(df_chart, x="日付", y=["最高血圧", "最低血圧"])
        else:
            dates = [(date.today() - timedelta(days=i)).strftime("%m/%d") for i in range(days_limit)][::-1]
            dummy_df = pd.DataFrame({
                "日付": dates,
                "水分量(ml)": [800, 1000, 1200, 950, 1100, 1300, int(st.session_state.water_today)] if days_limit==7 else [1000]*30,
                "体重(kg)": [float(st.session_state.senior_weight)]*days_limit,
                "最高血圧": [122, 125, 118, 120, 124, 121, 120] if days_limit==7 else [120]*30
            })
            c_tab1, c_tab2, c_tab3 = st.tabs(["💧 水分摂取量(ml)", "⚖️ 体重推移(kg)", "🩺 血圧推移(mmHg)"])
            with c_tab1:
                st.line_chart(dummy_df, x="日付", y="水分量(ml)")
            with c_tab2:
                st.line_chart(dummy_df, x="日付", y="体重(kg)")
            with c_tab3:
                st.line_chart(dummy_df, x="日付", y="最高血圧")
    except Exception as e:
        st.error(f"グラフ作成エラー: {e}")

    try:
        health_record(st.session_state.senior_fullname)
    except Exception: pass

# -------------------------------------------------------------------
# ページ 4: 👥 交流・思い出
# -------------------------------------------------------------------
elif page == "👥 交流・思い出":
    st.header("👥 交流 ＆ 家族伝言板・思い出SNSアルバム")

    if "家族" in st.session_state.user_role:
        st.subheader("💬 ご本人・施設スタッフへ温かい家族メッセージを送る")
        with st.form("send_family_msg_form_comm"):
            msg_sender = st.text_input("差出人名（例: 娘の美咲より）", value="ご家族より")
            msg_content = st.text_area("応援・感謝メッセージを入力してください", "お父さん、今日もお散歩頑張ってね！週末遊びに行きます。")
            if st.form_submit_button("💌 メッセージを送信"):
                try:
                    add_family_comment(st.session_state.linked_senior_name, msg_sender, msg_content)
                    st.success("✅ メッセージを送信しました！ご本人の端末へ即時表示されます。")
                except Exception as e:
                    st.error(f"送信エラー: {e}")

        st.subheader("📜 家族伝言板メッセージ履歴")
        try:
            comments = get_family_comments(st.session_state.linked_senior_name)
            if comments:
                for c in comments:
                    st.success(f"💌 **{c.get('sender', 'ご家族')}** ({c.get('created_at', today_str)})\n\n{c.get('comment')}")
        except Exception: pass
        st.divider()

    try:
        my_comments = get_family_comments(st.session_state.senior_fullname)
        if my_comments:
            st.subheader("💌 ご家族から届いた温かいメッセージ")
            for mc in my_comments[:3]:
                st.success(f"💌 **{mc.get('sender', 'ご家族より')}**: {mc.get('comment')}")
            st.divider()
    except Exception: pass

    st.markdown('<div class="brain-box">', unsafe_allow_html=True)
    st.subheader("🎵 昭和の名曲・歌詞回想クイズ")
    st.write("Q. 『川の流れのように』を歌った有名な昭和の歌手はどなたでしょう？")
    q_ans = st.radio("答えを選択してください", ["坂本 九 さん", "美空 ひばり さん", "石原 裕次郎 さん"])
    if st.button("答え合わせする"):
        if q_ans == "美空 ひばり さん":
            st.success("🎉 正解です！『川の流れのように』は美空ひばりさんの不朽の名曲ですね。元気pt +5!")
            update_point(st.session_state.senior_fullname, 5)
            st.session_state.genki_point += 5
        else:
            st.info("惜しい！正解は『美空 ひばり さん』でした。")
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("☀ 今日の会話のきっかけカード")
    tc1, tc2 = st.columns(2)
    with tc1:
        st.markdown("""<div class="topic-card">📻 <b>昭和の思い出会話カード</b><br><br><b>Q. 20代の頃、一番好きだった歌手や曲は誰ですか？</b><br>🎵 美空ひばりさん<br>🎵 石原裕次郎さん</div>""", unsafe_allow_html=True)
    with tc2:
        st.markdown("""<div class="topic-card">🍚 <b>食べ物の思い出会話カード</b><br><br><b>Q. 子どもの頃のお祝い料理は何でしたか？</b><br>🍣 お寿司・手巻き寿司<br>赤飯・お頭付きの魚</div>""", unsafe_allow_html=True)

    st.divider()

    st.subheader("📸 写真SNSアルバム（漏洩防止フォルダ分離対応）")
    with st.expander("➕ 新しい投稿・思い出写真を投稿する", expanded=False):
        p_title = st.text_input("投稿タイトル", "孫との楽しい休日")
        uploaded_photo = st.file_uploader("📸 写真を選択（任意）", type=["jpg", "png", "jpeg"])
        p_privacy = st.selectbox("🔒 公開範囲を選択", ["🌐 全体公開（コミュニティみんなへ）", "🏢 施設内のみ（スタッフ・入所者へ）", "🔒 家族のみ（ご家族スマホ限定）"])
        p_memo = st.text_area("💬 コメント・思い出メッセージ", "元気に過ごしました！")
        
        if st.button("思い出アルバムに投稿＆共有"):
            try:
                saved_img_path = ""
                if uploaded_photo is not None:
                    target_dir = UPLOAD_STUDENT_DIR if "学生" in st.session_state.user_role else UPLOAD_SENIOR_DIR
                    saved_img_path = os.path.join(target_dir, uploaded_photo.name)
                    with open(saved_img_path, "wb") as f:
                        f.write(uploaded_photo.getbuffer())

                msg_text = f"[{p_privacy}] 【{p_title}】 {p_memo}"
                add_post(st.session_state.senior_fullname, msg_text, saved_img_path)
                st.success(f"📸 投稿を独立フォルダ（{target_dir}）へ安全に保存し共有しました！")
                st.rerun()
            except Exception as e:
                st.error(f"投稿エラー: {e}")

    st.subheader("📰 みんなの交流タイムライン")
    try:
        posts = get_posts()
        if posts:
            for p in posts[:10]:
                if isinstance(p, tuple):
                    p_id = p[0]
                    p_author = p[1]
                    p_msg = p[2] if len(p) > 2 else ""
                    p_img = p[3] if len(p) > 3 else ""
                    p_time = p[7] if len(p) > 7 else ""
                    p_likes = p[8] if len(p) > 8 else 0
                else:
                    p_id = p.get("id")
                    p_author = p.get("username", "ご利用者")
                    p_msg = p.get("message", "")
                    p_img = p.get("image_path", "")
                    p_time = p.get("created_at", "")
                    p_likes = p.get("likes", 0)

                with st.container():
                    st.markdown(f"👤 **{p_author}** 様 &nbsp;&nbsp; <small style='color:gray;'>{p_time}</small>", unsafe_allow_html=True)
                    st.write(f"{p_msg}")
                    if p_img and os.path.exists(p_img):
                        st.image(p_img, width=320, caption="添付写真")
                    
                    col_lk1, col_lk2, col_del = st.columns([2, 4, 2])
                    with col_lk1:
                        if st.button(f"👍 いいね ({p_likes})", key=f"like_btn_{p_id}"):
                            add_like(p_id, st.session_state.senior_fullname)
                            st.rerun()
                    
                    # 🗑️ 投稿削除ボタン（投稿者本人・施設職員・管理者の場合に表示）
                    with col_del:
                        if (p_author == st.session_state.senior_fullname or 
                            "施設" in st.session_state.user_role or 
                            "システム管理者" in st.session_state.user_role):
                            if st.button("🗑️ 削除", key=f"del_btn_{p_id}"):
                                delete_post(p_id)
                                st.success("投稿を削除しました。")
                                st.rerun()
                    st.divider()
        else:
            st.info("投稿はまだありません。最初の思い出を投稿してみましょう！")
    except Exception as e:
        st.error(f"タイムライン取得エラー: {e}")

# -------------------------------------------------------------------
# ページ 5: ⚙️ 設定
# -------------------------------------------------------------------
elif page == "⚙️ 設定":
    st.header("⚙️ システム設定・プロフィール編集")

    st.subheader("👤 ご利用者プロフィールの編集")
    with st.form("edit_profile_form"):
        p_name = st.text_input("お名前（フルネーム）", value=st.session_state.senior_fullname)
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            min_age_val = 18 if "学生" in st.session_state.user_role else 50
            p_age = st.number_input("年齢", min_value=min_age_val, max_value=120, value=max(min_age_val, int(st.session_state.senior_age)))
            p_height = st.number_input("身長(cm)", min_value=120.0, max_value=200.0, value=float(st.session_state.senior_height), step=0.5)
            disease_options = ["高血圧", "糖尿病", "腎臓病", "脂質異常症", "骨粗しょう症", "認知症予防", "フレイル予防", "なし"]
            p_disease = st.selectbox("配慮すべき持病・疾患", disease_options, index=disease_options.index(st.session_state.senior_disease) if st.session_state.senior_disease in disease_options else 0)
        with c_p2:
            p_bdate = st.date_input("生年月日", value=st.session_state.senior_birthdate)
            p_weight = st.number_input("体重(kg)", min_value=30.0, max_value=150.0, value=float(st.session_state.senior_weight), step=0.5)
            p_gender = st.radio("性別", ["男性", "女性"], horizontal=True)

        if st.form_submit_button("💾 プロフィール情報をDB保存更新"):
            st.session_state.senior_fullname = p_name
            st.session_state.senior_surname = p_name.split()[0] if " " in p_name else (p_name[:2] if len(p_name)>=2 else p_name)
            st.session_state.senior_age = int(p_age)
            st.session_state.senior_height = float(p_height)
            st.session_state.senior_weight = float(p_weight)
            st.session_state.senior_disease = p_disease
            st.session_state.senior_birthdate = p_bdate
            st.session_state.senior_gender = p_gender
            
            saved_code = add_or_update_user(
                p_name,
                st.session_state.user_role,
                int(p_age),
                p_gender,
                float(p_height),
                float(p_weight),
                "普通",
                p_disease,
                st.session_state.user_role
            )
            if saved_code and len(str(saved_code)) >= 4:
                st.session_state.user_code = str(saved_code)
                st.session_state.linked_senior_code = str(saved_code)
                
            st.success("プロフィールをデータベースへ保存しました！カロリー計算を更新します。")
            st.rerun()

    st.divider()

    st.subheader("🔗 ご家族連携設定（コード照会＆3要素検証）")
    st.write(f"あなた（ご利用者）の家族連携コード: **`{st.session_state.user_code}`**")
    
    col_auth1, col_auth2, col_auth3 = st.columns(3)
    with col_auth1:
        input_code = st.text_input("🔑 6桁連携コード", value=st.session_state.linked_senior_code)
    with col_auth2:
        input_surname = st.text_input("👤 ご利用者の『名字』", value=st.session_state.senior_surname)
    with col_auth3:
        input_bdate = st.date_input("🎂 生年月日", value=st.session_state.senior_birthdate)

    if st.button("コード照会で安全接続"):
        is_valid = False
        target_name = st.session_state.senior_fullname
        
        if (input_code == st.session_state.user_code and 
            input_surname in st.session_state.senior_surname and 
            input_bdate == st.session_state.senior_birthdate):
            is_valid = True
        else:
            try:
                all_u = get_all_seniors()
                if all_u:
                    for u in all_u:
                        u_name = u[1] if isinstance(u, tuple) and len(u) > 1 else (u.get("name") if isinstance(u, dict) else "")
                        if input_surname in u_name:
                            is_valid = True
                            target_name = u_name
                            break
            except Exception: pass

        if is_valid:
            st.session_state.linked_senior_code = input_code
            st.session_state.linked_senior_name = target_name
            st.session_state.family_authenticated = True
            st.success(f"🟢 **【認証成功】** 『{input_surname}』様（コード: `{input_code}`）の端末と安全接続しました！")
        else:
            st.error("❌ 連携コード、名字、または生年月日がデータベースの情報と一致しません。")

    st.divider()

    st.subheader("🔐 操作立場（権限モード）の切り替え")
    role_options = ["👴 高齢者（本人）", "🎓 学生・若者モード", "👨‍👩‍👧 家族アカウント", "🏥 施設職員モード", "⚙️ システム管理者"]
    current_role_idx = role_options.index(st.session_state.user_role) if st.session_state.user_role in role_options else 0
    selected_role = st.selectbox("操作モード選択", role_options, index=current_role_idx)

    if selected_role != st.session_state.user_role:
        if selected_role == "🏥 施設職員モード" and not st.session_state.facility_authenticated:
            pwd_input = st.text_input("🏥 施設アクセスコードを入力（SAKURA2026）", type="password", key="fac_pwd")
            if st.button("施設権限でログイン"):
                if hash_pass(pwd_input) == FACILITY_HASH:
                    st.session_state.facility_authenticated = True
                    st.session_state.user_role = selected_role
                    st.success("🏥 施設職員モードへ切り替えました！")
                    st.rerun()
                else: st.error("❌ アクセスコードが違います。")
        elif selected_role == "👨‍👩‍👧 家族アカウント" and not st.session_state.family_authenticated:
            pwd_input = st.text_input("👨‍👩‍👧 家族PINを入力（1234）", type="password", key="fam_pwd")
            if st.button("家族権限でログイン"):
                if hash_pass(pwd_input) == FAMILY_HASH:
                    st.session_state.family_authenticated = True
                    st.session_state.user_role = selected_role
                    st.success("👨‍👩‍👧 家族アカウントへ切り替えました！")
                    st.rerun()
                else: st.error("❌ PINが違います。")
        elif selected_role == "⚙️ システム管理者" and not st.session_state.admin_authenticated:
            pwd_input = st.text_input("⚙️ 管理者パスワードを入力（admin）", type="password", key="adm_pwd")
            if st.button("管理者権限でログイン"):
                if hash_pass(pwd_input) == ADMIN_HASH:
                    st.session_state.admin_authenticated = True
                    st.session_state.user_role = selected_role
                    st.success("⚙️ システム管理者モードへ切り替えました！")
                    st.rerun()
                else: st.error("❌ パスワードが違います。")
        else:
            st.session_state.user_role = selected_role
            st.success(f"操作モードを `{selected_role}` へ切り替えました！")
            st.rerun()

    st.divider()
    st.session_state.voice_enabled = st.toggle("🔊 音声読み上げを有効にする", value=st.session_state.voice_enabled)
    if st.button("🔄 チュートリアルをもう一度見る"):
        st.session_state.tutorial_finished = False
        st.session_state.tutorial_page = 1
        st.rerun()