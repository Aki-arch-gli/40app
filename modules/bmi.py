def calculate_bmi(height, weight):
    """
    BMIを計算する
    
    height : cm
    weight : kg
    """

    height_m = height / 100

    bmi = weight / (height_m ** 2)

    bmi = round(bmi, 1)


    if bmi < 18.5:
        result = "低体重"

    elif bmi < 25:
        result = "普通体重"

    elif bmi < 30:
        result = "肥満（1度）"

    else:
        result = "肥満"


    return bmi, result