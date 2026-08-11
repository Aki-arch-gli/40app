import os
import re
from PIL import Image
import streamlit as st

# ==========================================
# 画像マッピングと処理（循環参照を防ぐためこちらに配置）
# ==========================================
IMAGE_MAPPING = [
    (r"パン|トースト|サンドイッチ|ロールパン", "assets/breakfast_western.jpg"),
    (
        r"雑穀|ご飯|ごはん|おにぎり|のり|梅干し|納豆|粥|かゆ",
        "assets/breakfast_japanese.jpg",
    ),
    (r"親子丼|牛丼|豚丼|カツ丼|天丼|丼", "assets/rice_grain.jpg"),
    (r"鶏|チキン|鳥|から揚げ|唐揚げ|照り焼き", "assets/chicken_dish.jpg"),
    (r"豚|ポーク|しゃぶしゃぶ|豚汁|生姜焼き|カツ", "assets/pork_dish.jpg"),
    (r"鍋|水炊き|すき焼き|煮込み", "assets/pot_dish.jpg"),
    (
        r"ホイル焼き|煮魚|照り煮|さばのみそ煮|カレイ|煮付け",
        "assets/fish_simmered.jpg",
    ),
    (
        r"魚|鮭|サケ|塩焼き|ムニエル|フライ|刺身|ツナ",
        "assets/fish_grilled.jpg",
    ),
    (r"みそ汁|味噌汁|スープ|お吸い物|汁", "assets/soup_miso.jpg"),
    (
        r"サラダ|あえもの|和え物|おひたし|ひじき|きんぴら|野菜",
        "assets/salad_vegetable.jpg",
    ),
    (r"冷奴|豆腐|高野豆腐|湯豆腐|厚揚げ|おから", "assets/tofu_dish.jpg"),
]

DEFAULT_IMAGE_PATH = "assets/default.jpg"


def get_menu_image_path(menu_text: str) -> str:
    """献立テキストから対応する画像パスを判定"""
    if not menu_text:
        return DEFAULT_IMAGE_PATH
    for pattern, img_path in IMAGE_MAPPING:
        if re.search(pattern, menu_text):
            if os.path.exists(img_path):
                return img_path
    return DEFAULT_IMAGE_PATH if os.path.exists(DEFAULT_IMAGE_PATH) else None


def display_resized_menu_image(
    img_path: str, caption: str = "", max_width: int = 260
):
    """画像をリサイズして表示"""
    if img_path and os.path.exists(img_path):
        try:
            image = Image.open(img_path)
            image.thumbnail((max_width, max_width))
            st.image(image, caption=caption, use_container_width=False)
        except Exception:
            st.write("🖼️")
    else:
        st.write("🍽️")


# ==========================================
# メインのカード表示関数
# ==========================================
def weekly_card(day, menu):
    """1日分の献立を画像付きで表示するカスタムカード"""

    if not isinstance(menu, dict):
        return

    # 1. カード上部（タイトル ＆ カロリー）
    st.markdown(
        f"""<div style="background:#FFFDF5; border-radius:20px 20px 0 0; padding:25px 30px 10px 30px; color:#333333; border-top: 1px solid #FFE4A0; border-left: 1px solid #FFE4A0; border-right: 1px solid #FFE4A0;">
<h2 style="font-size:32px; margin:0 0 10px 0; color:#333333 !important;">📅 {day}</h2>
<p style="font-size:22px; font-weight:bold; color:#E65100 !important; margin:0;">
🔥 カロリー：{menu.get("カロリー","")} kcal
</p>
</div>""",
        unsafe_allow_html=True,
    )

    # 2. 食事エリア（朝・昼・夕の3列レイアウト＋画像）
    with st.container():
        st.markdown(
            """<style>
div[data-testid="stHorizontalBlock"] {
    background: #FFFDF5;
    padding: 0px 20px;
    border-left: 1px solid #FFE4A0;
    border-right: 1px solid #FFE4A0;
}
</style>""",
            unsafe_allow_html=True,
        )

        col_bf, col_ln, col_dn = st.columns(3)

        # 朝食
        with col_bf:
            st.markdown(
                '<p style="font-size:24px; font-weight:bold; margin-bottom:5px; color:#333333 !important;">🌅 朝食</p>',
                unsafe_allow_html=True,
            )
            bf_text = menu.get("朝食", "")
            bf_img = get_menu_image_path(bf_text)
            display_resized_menu_image(
                bf_img, caption="【朝食】", max_width=260
            )
            st.markdown(
                f'<p style="font-size:20px; line-height:1.5; color:#333333 !important;">{bf_text}</p>',
                unsafe_allow_html=True,
            )

        # 昼食
        with col_ln:
            st.markdown(
                '<p style="font-size:24px; font-weight:bold; margin-bottom:5px; color:#333333 !important;">🌞 昼食</p>',
                unsafe_allow_html=True,
            )
            ln_text = menu.get("昼食", "")
            ln_img = get_menu_image_path(ln_text)
            display_resized_menu_image(
                ln_img, caption="【昼食】", max_width=260
            )
            st.markdown(
                f'<p style="font-size:20px; line-height:1.5; color:#333333 !important;">{ln_text}</p>',
                unsafe_allow_html=True,
            )

        # 夕食
        with col_dn:
            st.markdown(
                '<p style="font-size:24px; font-weight:bold; margin-bottom:5px; color:#333333 !important;">🌙 夕食</p>',
                unsafe_allow_html=True,
            )
            dn_text = menu.get("夕食", "")
            dn_img = get_menu_image_path(dn_text)
            display_resized_menu_image(
                dn_img, caption="【夕食】", max_width=260
            )
            st.markdown(
                f'<p style="font-size:20px; line-height:1.5; color:#333333 !important;">{dn_text}</p>',
                unsafe_allow_html=True,
            )

    # 3. カード下部（理由・バランス・アドバイス）
    st.markdown(
        f"""<div style="background:#FFFDF5; border-radius:0 0 20px 20px; padding:15px 30px 25px 30px; color:#333333 !important; margin-bottom:25px; border-bottom: 1px solid #FFE4A0; border-left: 1px solid #FFE4A0; border-right: 1px solid #FFE4A0; font-size:20px; line-height:1.8;">
<hr style="border:none; border-top:1px solid #FFE0B2; margin:15px 0;">
<b>💡 理由</b><br>
{menu.get("理由","")}<br><br>
<b>🥗 栄養バランス</b><br>
{menu.get("バランス","")}<br><br>
<b>🤖 アドバイス</b><br>
{menu.get("アドバイス","")}
</div>""",
        unsafe_allow_html=True,
    )