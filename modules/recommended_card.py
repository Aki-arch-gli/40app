import streamlit as st


def recommended_card(
    breakfast,
    lunch,
    dinner,
    calorie,
    reason="",
    nutrition="",
    advice=""
):

    st.markdown(
        f"""
<div style="
background:#f8fff8;
padding:20px;
border-radius:18px;
border:2px solid #4CAF50;
box-shadow:0px 4px 12px rgba(0,0,0,0.15);
">

<h2>⭐ おすすめ健康献立</h2>

<hr>

<h3>🌅 朝食</h3>

<div style="
background:white;
padding:15px;
border-radius:12px;
">

{breakfast}

</div>

<br>

<h3>🌞 昼食</h3>

<div style="
background:white;
padding:15px;
border-radius:12px;
">

{lunch}

</div>

<br>

<h3>🌙 夕食</h3>

<div style="
background:white;
padding:15px;
border-radius:12px;
">

{dinner}

</div>

<br>

<h3>🔥 目安カロリー</h3>

<b>{calorie} kcal</b>

<hr>

<h3>💡 この献立を選んだ理由</h3>

{reason}

<hr>

<h3>🥗 栄養バランス</h3>

{nutrition}

<hr>

<h3>🤖 AIアドバイス</h3>

{advice}

</div>
""",
        unsafe_allow_html=True,
    )