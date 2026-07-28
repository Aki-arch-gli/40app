import pandas as pd
from modules.database import get_health_records


def create_dashboard_data(username):

    records = get_health_records(username)

    if not records:
        return None

    df = pd.DataFrame(
        records,
        columns=[
            "日付",
            "体重",
            "最高血圧",
            "最低血圧",
            "水分",
            "スコア"
        ]
    )

    df = df.sort_values("日付")

    df["日付"] = pd.to_datetime(df["日付"])

    df = df.sort_values("日付")

    today = pd.Timestamp.today()

# 最新データ
    latest = df.iloc[-1]

# ===== 先週 =====
    week_df = df[df["日付"] >= today - pd.Timedelta(days=7)]

# ===== 先月 =====
    month_df = df[df["日付"] >= today - pd.Timedelta(days=30)]

    summary = {

        "最新体重": latest["体重"],
        "先週体重": week_df["体重"].mean(),
        "先月体重": month_df["体重"].mean(),

        "最新最高血圧": latest["最高血圧"],
        "先週最高血圧": week_df["最高血圧"].mean(),
        "先月最高血圧": month_df["最高血圧"].mean(),

        "最新水分": latest["水分"],
        "先週水分": week_df["水分"].mean(),
        "先月水分": month_df["水分"].mean(),

        "最新スコア": latest["スコア"],
        "先週スコア": week_df["スコア"].mean(),
        "先月スコア": month_df["スコア"].mean(),

    }

    return df, summary