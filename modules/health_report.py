from modules.database import get_health_records


def create_health_report(username):
    records = get_health_records(username)

    if not records:
        return None

    count = len(records)

    weights = []
    waters = []
    highs = []
    lows = []
    scores = []

    for r in records:

        weights.append(r[1])
        highs.append(r[2])
        lows.append(r[3])
        waters.append(r[4])
        scores.append(r[5])

    report = {
        "記録日数": count,
        "平均体重": round(sum(weights) / count, 1),
        "平均最高血圧": int(sum(highs) / count),
        "平均最低血圧": int(sum(lows) / count),
        "平均水分": int(sum(waters) / count),
        "平均健康スコア": int(sum(scores) / count)
    }

    return report