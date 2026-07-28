import streamlit as st


def weekly_card(day, menu):

    st.markdown(f"""
<div style="
background:#FFFDF5;
border-radius:20px;
padding:30px;
color:#333333;
margin-bottom:20px;
">

<h2 style="
font-size:32px;
">
📅 {day}
</h2>


<p style="
font-size:26px;
line-height:2.2;
">

🌅 朝食<br>
{menu.get("朝食","")}<br><br>

🌞 昼食<br>
{menu.get("昼食","")}<br><br>

🌙 夕食<br>
{menu.get("夕食","")}<br><br>

🔥 カロリー<br>
{menu.get("カロリー","")} kcal<br><br>


💡 理由<br>
{menu.get("理由","")}<br><br>


🥗 栄養バランス<br>
{menu.get("バランス","")}<br><br>


🤖 アドバイス<br>
{menu.get("アドバイス","")}

</p>

</div>

""",
unsafe_allow_html=True)