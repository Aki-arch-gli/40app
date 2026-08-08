def calculate_calories(age, gender, height, weight, activity):
    """
    必要カロリーを計算
    """

    male_bmr = 10 * weight + 6.25 * height - 5 * age + 5
    female_bmr = 10 * weight + 6.25 * height - 5 * age - 161

    bmr_dict = {
        "男性": male_bmr,
        "女性": female_bmr,
        "回答しない": (male_bmr + female_bmr) / 2
    }

    bmr = bmr_dict.get(gender, (male_bmr + female_bmr) / 2)

    activity_dict = {
        "低い": 1.2,
        "普通": 1.375,
        "高い": 1.55
    }

    return round(bmr * activity_dict[activity])