import streamlit as st
from datetime import datetime
import time
import random

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
    get_menu_by_id
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
from modules.ai import (
    generate_ai_menu,
    generate_weekly_ai_menu
)
from modules.weekly_ai import generate_weekly_ai
from modules.weekly_parser import parse_week
from modules.weekly_card import weekly_card
from modules.shopping_ai import shopping_list
from modules.ai_parser import parse_ai_menu
from modules.simple_menu import create_simple_menu
from modules.meal_card import meal_card
from modules.health_report import create_health_report
from modules.health_dashboard import create_dashboard_data
from modules.fridge import (
    calc_remaining,
    expiry_color,
    expiry_text
)
from modules.fridge_recipe import recommend_from_fridge
from modules.ingredient_parser import (
    get_ingredients,
    normalize_food
)

st.markdown("""
<style>

.meal-card{
font-size:24px;
line-height:2;
}

.post-card{

font-size:22px;

line-height:1.9;

padding:18px;

border-radius:12px;

background:#F8FFF7;

}


.big-title{
font-size:32px;
font-weight:bold;
}


</style>
""",
unsafe_allow_html=True)

# ========= 初期設定 ==========
st.set_page_config(
    page_title="高齢者健康献立AI",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

create_tables()

# ==========================
# 初回案内
# ==========================

if "tutorial_page" not in st.session_state:
    st.session_state.tutorial_page = 1

if "tutorial_finished" not in st.session_state:
    st.session_state.tutorial_finished = False


# ========= CSS ==========
st.markdown("""
<style>

.main-title{
    font-size:42px;
    color:#2E8B57;
    font-weight:bold;
}

.sub-title{
    font-size:24px;
    color:#666666;
}

.big-font{
    font-size:22px;
}

.stButton>button{
    width:100%;
    height:55px;
    font-size:20px;
}

</style>
""",unsafe_allow_html=True)


if not st.session_state.tutorial_finished:

    page = st.session_state.tutorial_page

    st.markdown("# 🍱 高齢者健康献立AI")

    st.write("")

    if page == 1:

        st.markdown("""
# 🍚 AIが献立を考えます

毎日の献立を

AIが自動で作成します😊

🥗 栄養バランスも安心です。
""")

        if st.button("▶ 次へ"):

            st.session_state.tutorial_page = 2
            st.rerun()

    elif page == 2:

        st.markdown("""
# ❤️ 健康を記録できます

毎日

⚖️体重

❤️血圧

💧水分量

を簡単に保存できます。
""")

        col1, col2 = st.columns(2)

        with col1:

            if st.button("◀ 戻る"):

                st.session_state.tutorial_page = 1
                st.rerun()

        with col2:

            if st.button("▶ 次へ"):

                st.session_state.tutorial_page = 3
                st.rerun()

    elif page == 3:

        st.markdown("""
# 🌸 毎日続けましょう

🏆 健康ポイント

📈 健康記録

🍱 AI献立

で健康生活を応援します😊
""")

        col1, col2 = st.columns(2)

        with col1:

            if st.button("◀ 戻る"):

                st.session_state.tutorial_page = 2
                st.rerun()

        with col2:

            if st.button("🟢 はじめる"):

                st.session_state.tutorial_finished = True
                st.rerun()

    st.stop()

# ========= タイトル ==========
st.markdown(
    '<p class="main-title">🍱 高齢者健康献立AI</p>',
    unsafe_allow_html=True
)

st.markdown(
    f'<p class="sub-title">{greeting()}。</p>',
    unsafe_allow_html=True
)

st.write("---")


# ========= サイドバー ==========
st.sidebar.title("利用者情報")

# ========= 利用モード =========

mode = st.sidebar.radio(
    "利用目的",
    [
        "👴 高齢者モード",
        "🎓 体験モード"
    ]
)

username = st.sidebar.text_input(
    "ニックネーム",
    "匿名ユーザー"
)

display_mode = st.sidebar.radio(
    "表示方法",
    [
        "📖 詳細モード",
        "😊 簡単モード"
    ]
)

st.sidebar.divider()

show_help = st.sidebar.checkbox(
    "❓ はじめての方へ"
)

if mode == "👴 高齢者モード":

    age = st.sidebar.slider(
        "年齢",
        65,
        100,
        75
    )


    gender = st.sidebar.radio(
        "性別",
        [
            "男性",
            "女性"
        ]
    )


    height = st.sidebar.slider(
        "身長(cm)",
        130,
        190,
        160
    )


    weight = st.sidebar.slider(
        "体重(kg)",
        30,
        120,
        55
    )


    activity = st.sidebar.selectbox(
        "活動量",
        [
            "低い",
            "普通",
            "高い"
        ]
    )


    disease = st.sidebar.selectbox(
        "疾患",
        [
            "なし",
            "高血圧",
            "糖尿病",
            "腎臓病",
            "脂質異常症",
            "骨粗しょう症",
            "認知症予防",
            "フレイル予防",
            "心疾患予防",
            "便秘予防"
        ]
    )


else:

    age = st.sidebar.slider(
        "年齢",
        18,
        100,
        20
    )



    gender = st.sidebar.radio(
        "性別",
      [
        "男性",
        "女性"
      ]
    )


    height = st.sidebar.slider(
       "身長(cm)",
       130,
       190,
       160
    )


    weight = st.sidebar.slider(
       "体重(kg)",
       30,
       120,
       55
    )


    activity = st.sidebar.selectbox(
       "活動量",
      [
        "低い",
        "普通",
        "高い"
      ]
    )


    disease = st.sidebar.selectbox(
       "疾患",
      [
        "なし",
        "高血圧",
        "糖尿病",
        "腎臓病",
        "脂質異常症",
        "骨粗しょう症",
        "認知症予防",
        "フレイル予防",
        "心疾患予防",
        "便秘予防"
      ]
    )

# ==========================
# ヘルプ
# ==========================

if show_help:

    st.info("""
👋 ようこそ！

このアプリは毎日の食事と健康をサポートします。

画面を上から順番に使えば大丈夫です😊
""")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.success("""
① 利用者情報

年齢や病気を入力します。
""")

    with col2:

        st.success("""
② AI献立

ボタンを押すだけで献立完成！
""")

    with col3:

        st.success("""
③ 健康記録

体重・血圧を保存できます。
""")

    with col4:

        st.success("""
④ 継続

毎日続けて健康維持😊
""")

    st.divider()

# ========= 計算 ==========
need_calorie = calculate_calories(
    age,
    gender,
    height,
    weight,
    activity
)

bmi,bmi_result = calculate_bmi(
    height,
    weight
)

# ==========================
# セッション初期化
# ==========================

if "menu" not in st.session_state:
    st.session_state.menu = None

if "menu_text" not in st.session_state:
    st.session_state.menu_text = None

if "recommended_menu" not in st.session_state:
    st.session_state.recommended_menu = None

if "ai_comment" not in st.session_state:
    st.session_state.ai_comment = None

if "audio" not in st.session_state:
    st.session_state.audio = None

if "weekly_ai_menu" not in st.session_state:
         st.session_state.weekly_ai_menu = None

if "weekly_menu" not in st.session_state:
    st.session_state.weekly_menu = None

if "shopping" not in st.session_state:
    st.session_state.shopping = None

if "history" not in st.session_state:
    st.session_state.history = []

# 健康ポイント（高齢者モード）
if "health_point" not in st.session_state:
    st.session_state.health_point = 0


# 食事ポイント（体験モード）
if "food_point" not in st.session_state:
    st.session_state.food_point = 0


# 健康活動履歴
if "health_action" not in st.session_state:
    st.session_state.health_action = []

if "registered" not in st.session_state:

    user = get_user(username)


    if user is None:

        add_user(
            username,
            age,
            gender,
            height,
            weight,
            disease,
            mode
        )


    st.session_state.registered = True

# 継続日数
if "continue_days" not in st.session_state:
    st.session_state.continue_days = 1

if "fridge" not in st.session_state:

    st.session_state.fridge=[]

# ==========================
# ダッシュボード
# ==========================

st.write("## 📊 ダッシュボード")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "必要カロリー",
        f"{need_calorie} kcal"
    )

with col2:
    st.metric(
        "BMI",
        bmi
    )

with col3:
    st.metric(
        "判定",
        bmi_result
    )

with col4:

    if mode == "👴 高齢者モード":

        st.metric(
            "継続日数",
            f"{st.session_state.continue_days}日"
        )

    else:

        st.metric(
            "食事ポイント",
            f"{st.session_state.food_point}pt"
        )

st.write("---")

today = datetime.now().strftime("%Y年%m月%d日")

st.info(f"📅 今日の日付：{today}")

if mode == "👴 高齢者モード":

    st.info(
        "👴 高齢者モード：健康習慣の継続をサポートします"
    )

else:

    st.info(
        "🎓 体験モード：食生活を振り返り健康意識を高めます"
    )

st.write("---")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(

[
    "🍱 今日の献立",
    "📅 週間献立",
    "📈 健康管理",
    "🏆 健康ランキング",
    "💬 みんなの健康記録",
    "⚙ 設定",
    "❓ 使い方",
    "⭐ お気に入り"
]

)

with tab1:

    st.header("🍱 今日の献立")
    st.write("AIまたは登録済み献立から献立を生成します。")

    ai_button = st.button(
        "🤖 AI献立を作成",
        use_container_width=True
    )

    random_button = st.button(
        "🍳 ランダム献立",
        use_container_width=True
    )

    if ai_button:

       status_area = st.empty()

       progress_area = st.empty()


       status_area.info(
         "🍱 健康献立を検索しています..."
       )

       progress = progress_area.progress(10)


       try:

            time.sleep(0.5)


            status_area.info(
                "🔍 健康状態に合わせた献立を探しています..."
            )
            
            progress.progress(30)

            time.sleep(0.7)


            status_area.info(
                "🥗 栄養バランスを調整しています..."
            )

            progress.progress(60)

            recommended_menu = generate_menu(
              age,
              disease,
              need_calorie
            )

            time.sleep(0.5)
            
            progress.progress(90)

            status_area.info(
                "✨ 献立を完成しています..."
            )

            time.sleep(0.5)

            progress.progress(100)

            st.session_state.recommended_menu = recommended_menu

            time.sleep(0.5)

            status_area.empty()

            progress_area.empty()


            menu_text = f"""
🌅 朝食
{recommended_menu["朝食"]}


🌞 昼食
{recommended_menu["昼食"]}


🌙 夕食
{recommended_menu["夕食"]}


🔥 約{recommended_menu["カロリー"]} kcal


💡 この献立を選んだ理由

{recommended_menu["理由"]}


🥗 栄養バランス

{recommended_menu["バランス"]}


🤖 アドバイス

{recommended_menu["アドバイス"]}
"""

            st.session_state.menu_text = menu_text
            st.session_state.audio = create_voice(menu_text)
            st.session_state.ai_comment = recommended_menu["アドバイス"]

            status_area.empty()
            progress_area.empty()

            st.success(
              "📚 健康献立データから作成しました😊"
            )


       except Exception as e:


            st.error(
                f"登録献立エラー:{e}"
            )

            st.write(e)

            st.session_state.recommended_menu = None


            menu_text = generate_ai_menu(
                age,
                disease,
                need_calorie,
                simple=(
                    display_mode=="😊 簡単モード"
                )
            )

            progress.progress(100)

            st.success("✅ AI献立が完成しました！")

        # 保存
            st.session_state.menu_text = menu_text

            st.session_state.recommended_menu = {

               "id":0,

               "朝食":"",
               "昼食":"",
               "夕食":"",

               "理由":
               "AIが栄養バランスを考えて作成した献立です。",

               "バランス":
               "主食・主菜・副菜を意識しています。",

               "難易度":
               "★★",

               "アドバイス":
               "毎日の食事を楽しみながら続けましょう。",

               "カロリー":
               need_calorie
            }

            st.session_state.audio = create_voice(menu_text)

        # AIコメント
            if mode == "👴 高齢者モード":
              st.session_state.ai_comment = create_comment(
                disease,
                need_calorie
              )
            else:
              st.session_state.ai_comment = (
                "🎓 主食・主菜・副菜を意識した食生活を続けましょう。"
              )

        # ポイント加算
            if mode == "👴 高齢者モード":

              st.session_state.health_point += 10

              update_point(
                username,
                st.session_state.health_point
              )

            else:

              st.session_state.food_point += 20

              update_point(
                username,
                st.session_state.food_point
              )

    # -----------------------
    # 献立表示
    # -----------------------
    if st.session_state.menu_text:

        menu = parse_ai_menu(
            st.session_state.menu_text
        )

        st.subheader("🍱 おすすめ健康献立")

        meal_card(
            "朝ごはん",
            "🌅",
            menu.get("朝食","")
        )

        meal_card(
            "昼ごはん",
            "🌞",
            menu.get("昼食","")
        )

        meal_card(
            "夜ごはん",
            "🌙",
            menu.get("夕食","")
        )


        # 詳細情報表示
        if display_mode == "📖 詳細モード":

            st.divider()

            st.subheader("💡 この献立について")

            detail = st.session_state.recommended_menu or {}


            st.info(
            f"""
           💡 **この献立を選んだ理由**

            {detail.get("理由","")}
            """
            )


            st.success(
            f"""
            🥗 **栄養バランス**

            {detail.get("バランス","")}
            """
            )


            st.warning(
            f"""
            ⭐ **調理の難しさ**

            {detail.get("難易度","")}
            """
            )


            st.info(
            f"""
            🤖 **健康アドバイス**

            {detail.get("アドバイス","")}
            """
            )

        if st.session_state.audio:

            st.subheader("🔊 音声読み上げ")

            st.audio(
                st.session_state.audio
            )

        if st.session_state.ai_comment:

            st.subheader("🤖 AIアドバイス")

            st.info(
                st.session_state.ai_comment
            )

        col1, col2, col3, col4= st.columns(4)

        with col1:

          if st.button("💾 おすすめ登録"):


            saved_menu = st.session_state.recommended_menu


            if saved_menu:

              reason = saved_menu["理由"]

              nutrition = saved_menu["バランス"]

              advice = saved_menu["アドバイス"]


            else:

              reason = "AIが個別生成した献立"

              nutrition = "バランスを考慮"

              advice = "健康的な食生活を続けましょう"



            add_recommended_menu(

              max(18, age - 5),

              min(100, age + 5),

              disease,

              need_calorie,


              menu.get("朝食",""),

              menu.get("昼食",""),

              menu.get("夕食",""),


              reason,

              nutrition,

              advice

            )


            st.success("登録しました😊")

        with col2:

            if st.button("⭐ お気に入り"):

                if st.session_state.recommended_menu:

                    menu_id = (
                       st.session_state.recommended_menu["id"]
                       if st.session_state.recommended_menu
                       else 0
                    )

                    add_favorite_menu(
                       username,
                       menu_id,
                       menu.get("朝食", ""),
                       menu.get("昼食", ""),
                       menu.get("夕食", ""),
                       need_calorie,
                       "AI献立"
                    )

                    st.success("お気に入り登録しました😊")


        with col3:

            if st.button("📄 PDF保存"):

                pdf = export_pdf(
                    st.session_state.menu_text
                )

                with open(pdf, "rb") as f:

                    st.download_button(
                        "📥 ダウンロード",
                        f,
                        file_name="AI献立.pdf"
                    )

        with col4:

            if st.button("🗑 非表示"):

                st.session_state.menu_text = None
                st.session_state.ai_comment = None
                st.session_state.audio = None

                st.rerun()

with tab2:

    st.header("📅 AI週間献立")

    if st.button(
        "🤖 1週間献立を作成",
        use_container_width=True
    ):

        try:

            weekly = generate_weekly_menu(
              age,
              disease,
              need_calorie
            )

            st.session_state.weekly_menu = weekly

            st.success("📚 健康献立データから作成しました😊")

        except:

            weekly = generate_weekly_ai(
              age,
              disease,
              need_calorie
            )

            st.session_state.weekly_menu = weekly

            st.warning("登録献立が見つからないためAIで作成しました")

        st.session_state.weekly_menu = weekly

    if st.session_state.weekly_menu:


        for day, menu in st.session_state.weekly_menu.items():

            weekly_card(
               day,
               menu
            )

        st.subheader("🛒 買い物リスト")

        foods = create_shopping_list(
            st.session_state.weekly_menu
        )

        for food in foods:

            st.checkbox(food)

        st.divider()


        if st.button(
            "📄 週間献立をPDF保存",
            use_container_width=True
        ):


            pdf = export_weekly_pdf(
                st.session_state.weekly_menu
            )


            with open(pdf,"rb") as f:

                st.download_button(

                    "📥 PDFダウンロード",

                    f,

                    file_name="AI週間献立表.pdf"

                )

                st.divider()

        if st.button(
           "⭐ この週間献立をお気に入り",
           use_container_width=True
        ):

           add_favorite_weekly_menu(

              username,

              st.session_state.weekly_menu

           )

           st.success("週間献立を保存しました😊")


        st.subheader(
            "🤖 AI週間健康アドバイス"
        )


        if st.button(
            "健康評価を見る"
        ):


            comment = weekly_comment(
                age,
                disease,
                need_calorie
            )


            st.session_state.weekly_comment = comment



        if "weekly_comment" in st.session_state:

            st.info(
                st.session_state.weekly_comment
            )

with tab3:

    st.header("📈 健康管理")

    health_record(
        username
    )

    st.divider()

    st.header("📈 健康レポート")

    report = create_health_report(username)

    if report is None:

        st.info("まだ健康記録がありません")
   
    else:

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
               "記録日数",
               report["記録日数"]
            )

            st.metric(
               "平均体重",
               f'{report["平均体重"]}kg'
            )

        with col2:

            st.metric(
               "平均最高血圧",
               report["平均最高血圧"]
            )

            st.metric(
               "平均最低血圧",
               report["平均最低血圧"]
            )

        with col3:

            st.metric(
               "平均水分",
               f'{report["平均水分"]}ml'
            )

            st.metric(
               "平均健康スコア",
               report["平均健康スコア"]
            )

        st.divider()

        score = report["平均健康スコア"]

        if score >= 90:

            st.success("🌸 とても健康的です！この調子で続けましょう！")

        elif score >= 75:

            st.info("😊 良好です。もう少し水分を意識するとさらに良くなります。")

        elif score >= 60:

            st.warning("⚠ 少し生活習慣を見直しましょう。")

        else:

            st.error("🚨 健康管理を優先しましょう。") 

    st.divider()

    st.header("📊 健康ダッシュボード")

    result = create_dashboard_data(username)

    if result is None:

        st.info("まだ健康記録がありません")

    else:

        df, summary = result

        if df is None:

            st.info("まだ健康記録がありません")

        else:

            st.subheader("⚖ 体重推移")

            st.line_chart(
                df.set_index("日付")["体重"]
            )

            st.subheader("❤️ 血圧推移")

            blood = df.set_index("日付")[["最高血圧","最低血圧"]]

            st.line_chart(blood)

            st.subheader("💧 水分量")

            st.bar_chart(
                df.set_index("日付")["水分"]
            )
  
            st.subheader("🏆 健康スコア")

            st.line_chart(
                df.set_index("日付")["スコア"]
            ) 

            st.divider()

            st.subheader("📅 先週との比較")

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "⚖️体重",
                    f"{summary['最新体重']:.1f} kg",
                    delta=f"{summary['最新体重']-summary['先週体重']:+.1f} kg"
                )

                st.metric(
                    "❤️最高血圧",
                    f"{int(summary['最新最高血圧'])}",
                    delta=f"{summary['最新最高血圧']-summary['先週最高血圧']:+.0f}"
                )

            with col2:

                st.metric(
                    "💧水分",
                    f"{summary['最新水分']} ml",
                    delta=f"{summary['最新水分']-summary['先週水分']:+.0f} ml"
                )

                st.metric(
                    "🏆健康スコア",
                    f"{summary['最新スコア']} 点",
                    delta=f"{summary['最新スコア']-summary['先週スコア']:+.0f}"
                )

            st.divider()

            st.subheader("🗓️ 先月との比較")

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "⚖️体重",
                    f"{summary['最新体重']:.1f} kg",
                    delta=f"{summary['最新体重']-summary['先月体重']:+.1f} kg"
                ) 
   
                st.metric(
                    "❤️最高血圧",
                    f"{int(summary['最新最高血圧'])}",
                    delta=f"{summary['最新最高血圧']-summary['先月最高血圧']:+.0f}"
                )

            with col2:

                st.metric(
                    "💧水分",
                   f"{summary['最新水分']} ml",
                   delta=f"{summary['最新水分']-summary['先月水分']:+.0f} ml"
                )
 
                st.metric(
                    "🏆健康スコア",
                    f"{summary['最新スコア']} 点",
                    delta=f"{summary['最新スコア']-summary['先月スコア']:+.0f}"
                )

    st.divider()

    st.header("🥕 冷蔵庫管理")

    col1, col2, col3 = st.columns(3)

    with col1:
        food = st.text_input("食材名")

    with col2:
        amount = st.text_input("数量")

    with col3:
        expire = st.date_input("賞味期限")

    if st.button("➕ 食材を追加"):


        if food:

            add_food(
                username,
                food,
                amount,
                str(expire)
            )


            st.success(
                f"🥕 {food} を追加しました😊"
            )


            st.session_state.fridge_refresh=True


        else:

            st.warning(
                "食材名を入力してください"
            )


    # --------------------------
    # 登録済み食材取得
    # --------------------------

    foods = get_foods(username)

    if foods:

        st.subheader("🥬 現在の食材")

        from datetime import datetime

        today = datetime.today().date()

        for row in foods:

            food_id = row[0]
            food_name = row[1]
            amount = row[2]
            expire = row[3]

            expire_date = datetime.strptime(
                expire,
                "%Y-%m-%d"
            ).date()

            remain = (expire_date - today).days

            if remain < 0:
                color = "🔴"
                status = "期限切れ"

            elif remain == 0:
                color = "🟠"
                status = "今日まで"

            elif remain <= 2:
                color = "🟡"
                status = f"残り{remain}日"

            else:
                color = "🟢"
                status = f"残り{remain}日"

            col1, col2 = st.columns([6,1])

            with col1:

                st.markdown(f"""
    ### {color} {food_name}

    **数量：** {amount}

    **賞味期限：** {expire}

    **状態：** {status}
    """)

            with col2:

                if st.button(
                    "🗑",
                    key=f"food_{food_id}"
                ):

                    delete_food(food_id)

                    st.rerun()

    else:

        st.info("まだ食材が登録されていません")

    st.divider()

    st.subheader("🚨 期限が近い食材")

    danger_foods = []

    for row in foods:

        expire_date = datetime.strptime(
            row[3],
            "%Y-%m-%d"
        ).date()
 
        remain = (expire_date - today).days
 
        if remain <= 2:
            danger_foods.append(row)

    if danger_foods:

        for row in danger_foods:

            st.warning(
                f"⚠ {row[1]} は賞味期限が近づいています！"
            )

    else:

        st.success("期限が近い食材はありません😊")

    st.divider()

    st.header("🍱 冷蔵庫だけで作れる献立")

    foods=get_foods(username)

    food_names=[

        f[1]

        for f in foods

    ]

    menus=recommend_from_fridge(

        food_names,

        age,

        disease,

        need_calorie

    )

    st.subheader("🍱 冷蔵庫で作れる献立候補")

    if menus:

        for score,rate,lack,row in menus:


            st.success(f"""
                🍱 一致率：{rate}%


                🌅 朝食

                {row["breakfast"]}

  
                🌞 昼食

                {row["lunch"]}


                🌙 夕食

                {row["dinner"]}


                🔥 {row["calorie"]} kcal

            """)

            if lack:

                st.info(
                    "あとこれだけ😊\n\n"
                    + "、".join(lack)
                )

            else:

                st.success("🎉 冷蔵庫だけで全部作れます！")

            col1,col2 = st.columns(2)

            with col1:
 
                st.button(
                    "🍳 今日の献立にする",
                    key=f"use_{row['id']}"
                )

            with col2:

                st.button(
                    "⭐ お気に入り",
                    key=f"favorite_{row['id']}"
                )

    else:

        st.info(
            "冷蔵庫の食材だけで作れる登録献立が見つかりませんでした😊"
        )

with tab4:


    if mode == "👴 高齢者モード":

        st.header(
            "🌱 健康継続チャレンジ"
        )


        st.metric(
            "健康継続日数",
            f"{st.session_state.continue_days}日"
        )


        st.info(
            "毎日の食事確認や健康記録を続けることで、健康習慣を育てます😊"
        )


        st.divider()


        st.subheader(
            "今日の健康活動"
        )


        for action in st.session_state.health_action:

            st.write(
                "✅ " + action
            )


    else:


        st.header(
            "🏆 1週間食事バランスチャレンジ"
        )


        st.write(
            "1週間の食生活を振り返り、健康ポイントを競います"
        )


        breakfast = st.checkbox(
            "🍚 朝食を入力"
        )

        lunch = st.checkbox(
            "🍱 昼食を入力"
        )

        dinner = st.checkbox(
            "🍽 夕食を入力"
        )

        vegetable = st.checkbox(
            "🥬 野菜を食べた"
        )

        protein = st.checkbox(
            "🥩 タンパク質を摂取"
        )


        point = 0


        if breakfast:
            point += 10

        if lunch:
            point += 10

        if dinner:
            point += 10

        if vegetable:
            point += 20

        if protein:
            point += 20


        st.metric(
            "あなたの食事ポイント",
            f"{point} pt"
        )


        ranking = get_ranking(
           mode
        )


        ranking = sorted(
            ranking,
            key=lambda x:x[1],
            reverse=True
        )


        st.subheader(
            "🎓 体験ランキング"
        )


        for i,(name,point) in enumerate(ranking):


            st.success(
                f"{i+1}位 {name} {point}pt"
            )

with tab5:


    st.header(
        "💬 みんなの健康記録"
    )


    st.write(
        "今日の健康活動を共有して、地域のみんなとつながりましょう😊"
    )


    message = st.text_input(
        "今日の一言"
    )

    uploaded = st.file_uploader(

        "📷 写真を追加（任意）",

        type=["png","jpg","jpeg"]

    )

    share_today = st.checkbox(
        "🍱 今日の献立も一緒に投稿"
    )


    if st.button(
        "投稿する"
    ):


        if message:

            image_path = ""

            if uploaded:

                import os

                os.makedirs(
                    "uploads",
                    exist_ok=True
                )

                image_path = (
                    f"uploads/{uploaded.name}"
                )

                with open(
                    image_path,
                    "wb"
                ) as f:
                    
                    f.write(uploaded.getbuffer())

            breakfast = ""
            lunch = ""
            dinner = ""

            if share_today and st.session_state.menu_text:

                menu = parse_ai_menu(
                    st.session_state.menu_text
                )

                breakfast = menu.get("朝食","")
                lunch = menu.get("昼食","")
                dinner = menu.get("夕食","")

            add_post(

                username,
                message,
                image_path,
                breakfast,
                lunch,
                dinner

            )

            st.success("投稿しました！")


    st.divider()


    posts = get_posts()


    for post in posts:


     post_id = post[0]

     name = post[1]

     text = post[2]

     image = post[3]

     breakfast = post[4]

     lunch = post[5]

     dinner = post[6]

     date = post[7]

     likes = post[8]


     st.markdown(f"""
<div style="
background:#f8f9fa;
padding:20px;
border-radius:15px;
margin-bottom:20px;
color:#222;
border:2px solid #d9d9d9;
">

<h3 style="font-size:28px; margin-bottom:15px;">
👤 {username}
</h3>

<p style="font-size:24px; line-height:1.6;">
💬 {message}
</p>

<p style="font-size:20px; color:#555;">
📅 {date}
</p>

<p style="font-size:22px; font-weight:bold; color:#e63946;">
❤️ 応援数：{likes}
</p>

</div>
""", unsafe_allow_html=True)

     if image:

        st.image(
            image,
            use_container_width=True
        )

     if breakfast:

        st.success(f"""
     🍱 今日の献立

     🌅 朝食
     {breakfast}

     🌞 昼食
     {lunch}

     🌙 夕食
     {dinner}
     """)


     if st.button(
        "❤️ 応援する",
        key=f"like_{post_id}"
     ):

        add_like(
            post_id,
            username
        )

        st.success(
            "応援しました😊"
        )

     if st.button(
        "🗑 投稿を削除",
        key=f"delete_{post_id}"
     ):

        delete_post(post_id)

        st.success(
          "投稿を削除しました"
        )

        st.rerun()

with tab6:

    st.header("⚙ 設定")

    dark = st.toggle("ダークモード")

    font = st.slider(

        "文字サイズ",

        18,

        40,

        24

    )

    sound = st.checkbox(

        "音声読み上げを有効"

    )

    family = st.checkbox(

        "家族共有を有効"

    )

    st.success("設定は自動保存されます。")

with tab7:

    st.header("❓ このアプリの使い方")

    st.markdown("""
## ① 利用者情報を入力
サイドバーから年齢・性別・病気を入力します。

---

## ② AI献立を作成
「🤖 AI献立を作成」を押します。

---

## ③ 今日の食事を確認
朝・昼・夜の献立を確認します。

---

## ④ 健康記録を保存
体重・血圧・水分量を入力します。

---

## ⑤ 毎日続ける
健康記録は毎日続けることが大切です😊
""")

with tab8:

    st.header("⭐ お気に入り献立")

    favorites = get_favorite_menus(username)

    if not favorites:

        st.info("まだ登録されていません")

    else:

        for menu in favorites:

            st.success(f"""
🌅 朝食
{menu[0]}

🌞 昼食
{menu[1]}

🌙 夕食
{menu[2]}

🔥 {menu[3]} kcal

💡 {menu[4]}
""")

st.divider()

st.subheader("📅 お気に入り週間献立")

weeks = get_favorite_weekly_menus(username)

days = [

"月曜日",

"火曜日",

"水曜日",

"木曜日",

"金曜日",

"土曜日",

"日曜日"

]

for week in weeks:

    st.success(f"📅 保存日：{week[0]}")

    for i,day in enumerate(days):

        menu = get_menu_by_id(week[i+1])

        if menu:

            st.markdown(f"""
### {day}

🌅 {menu[0]}

🌞 {menu[1]}

🌙 {menu[2]}

🔥 {menu[3]} kcal

---
""")

st.divider()

st.subheader("🏆 人気献立ランキング")

ranking = get_menu_ranking()

for i,row in enumerate(ranking):

    st.success(f"""
🥇 第{i+1}位

🌅 朝食
{row[0]}

🌞 昼食
{row[1]}

🌙 夕食
{row[2]}

⭐ お気に入り
{row[3]}件
""")
