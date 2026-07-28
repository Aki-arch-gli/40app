def health_score(
    water,
    medicine,
    high,
    low
):

    score = 100

    advice = []

    if water < 1200:

        score -= 15

        advice.append(
            "水分摂取量が不足しています。"
        )

    if not medicine:

        score -= 20

        advice.append(
            "服薬を忘れていませんか？"
        )

    if high > 140:

        score -= 10

        advice.append(
            "血圧が高めです。"
        )

    if low > 90:

        score -= 5

        advice.append(
            "最低血圧が高めです。"
        )

    if score >= 90:

        star = "★★★★★"

    elif score >= 80:

        star = "★★★★☆"

    elif score >= 70:

        star = "★★★☆☆"

    elif score >= 60:

        star = "★★☆☆☆"

    else:

        star = "★☆☆☆☆"

    return score, star, advice