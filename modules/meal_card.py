import streamlit as st


def meal_card(title,icon,text):


    st.markdown(
    f"""
    <div style="
        background:#f8fff8;
        padding:20px;
        border-radius:15px;
        border:1px solid #cce8cc;
        margin-bottom:15px;
        color:#333333;
    ">

    <h2 style="
    color:#2E8B57;
    ">
    {icon} {title}
    </h2>


    <p style="
    font-size:18px;
    color:#333333;
    ">
    {text}
    </p>


    </div>

    """,
    unsafe_allow_html=True
    )