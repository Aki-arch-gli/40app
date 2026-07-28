def calculate_calories(age, gender, height, weight, activity):
    """
    必要カロリーを計算
    """

    if gender == "男性":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_dict = {
        "低い": 1.2,
        "普通": 1.375,
        "高い": 1.55
    }

    return round(bmr * activity_dict[activity])