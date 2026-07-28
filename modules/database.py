import sqlite3
import csv
import os
import random
from datetime import datetime


DB_NAME = "health.db"



def connect():

    return sqlite3.connect(DB_NAME)



def create_tables():

    conn = connect()

    cur = conn.cursor()



    # =====================
    # 利用者情報
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        age INTEGER,

        gender TEXT,

        height REAL,

        weight REAL,

        disease TEXT,

        mode TEXT,

        point INTEGER DEFAULT 0,

        continue_days INTEGER DEFAULT 1

    )
    """)



    # =====================
    # 食事履歴
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS meal_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        date TEXT,

        breakfast TEXT,

        lunch TEXT,

        dinner TEXT,

        calorie INTEGER

    )
    """)



    # =====================
    # 水分管理
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS water(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        date TEXT,

        amount INTEGER

    )
    """)



    # =====================
    # 服薬管理
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicine(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        medicine TEXT,

        time TEXT

    )
    """)



    # =====================
    # 投稿
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        message TEXT,

        image TEXT,

        breakfast TEXT,

        lunch TEXT,

        dinner TEXT,

        created_at TEXT,

        likes INTEGER DEFAULT 0
    )
    """)

    # =====================
    # お気に入り週間献立
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorite_weekly_menus(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        save_date TEXT,

        monday INTEGER,
        tuesday INTEGER,
        wednesday INTEGER,
        thursday INTEGER,
        friday INTEGER,
        saturday INTEGER,
        sunday INTEGER
 
    )
    """)



    # =====================
    # いいね履歴
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        post_id INTEGER,

        username TEXT

    )
    """)



    # =====================
    # 健康コミュニティ
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS community(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        name TEXT,

        message TEXT,

        date TEXT,

        good INTEGER DEFAULT 0

    )
    """)



    # =====================
    # 健康記録
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS health_records(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        date TEXT,

        weight REAL,

        high INTEGER,

        low INTEGER,

        water INTEGER,

        medicine INTEGER,

        score INTEGER

    )
    """)

    # =====================
    # AI推薦献立データ
    # =====================

    cur.execute("""
     CREATE TABLE IF NOT EXISTS recommended_menus(

       id INTEGER PRIMARY KEY AUTOINCREMENT,

       age_min INTEGER,

       age_max INTEGER,

       disease TEXT,

       calorie INTEGER,

       breakfast TEXT,

       lunch TEXT,

       dinner TEXT,

       reason TEXT,

       nutrition TEXT,

       advice TEXT

     )
    """)

    # =====================
    # お気に入り献立
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorite_menus(

       id INTEGER PRIMARY KEY AUTOINCREMENT,

       username TEXT,

       menu_id INTEGER,

       breakfast TEXT,

       lunch TEXT,

       dinner TEXT,

       calorie INTEGER,

       reason TEXT,

       favorite_date TEXT

    )
    """)


    # =====================
    # 冷蔵庫管理
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS refrigerator(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        food TEXT,

        amount TEXT,

        expire TEXT

    )
    """)

    conn.commit()

    conn.close()

    

# ==========================
# 利用者登録
# ==========================

def add_user(

    name,
    age,
    gender,
    height,
    weight,
    disease,
    mode

):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        INSERT INTO users

        (
        name,
        age,
        gender,
        height,
        weight,
        disease,
        mode
        )

        VALUES(?,?,?,?,?,?,?)

        """,

        (

            name,

            age,

            gender,

            height,

            weight,

            disease,

            mode

        )

    )


    conn.commit()

    conn.close()





# ==========================
# ポイント更新
# ==========================

def update_point(

    name,

    point

):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        UPDATE users

        SET point=?

        WHERE name=?

        """,

        (

            point,

            name

        )

    )


    conn.commit()

    conn.close()





# ==========================
# ランキング取得
# ==========================

def get_ranking(mode):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT name, point

        FROM users

        WHERE mode=?

        ORDER BY point DESC

        LIMIT 10

        """,

        (

            mode,

        )

    )


    data = cur.fetchall()


    conn.close()


    return data





# ==========================
# ユーザー取得
# ==========================

def get_user(name):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT *

        FROM users

        WHERE name=?

        """,

        (

            name,

        )

    )


    user = cur.fetchone()


    conn.close()


    return user





# ==========================
# 投稿追加
# ==========================

def add_post(
    username,
    message,
    image="",
    breakfast="",
    lunch="",
    dinner=""
):

    conn = sqlite3.connect(DB_NAME)

    cur = conn.cursor()

    cur.execute("""
    INSERT INTO posts(

        username,
        message,
        image,
        breakfast,
        lunch,
        dinner,
        created_at

    )

    VALUES(?,?,?,?,?,?,?)
    """,(

        username,
        message,
        image,
        breakfast,
        lunch,
        dinner,
        datetime.now().strftime("%Y-%m-%d %H:%M")

    ))

    conn.commit()

    conn.close()





# ==========================
# 投稿取得
# ==========================

def get_posts():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT

        id,
        username,
        message,
        image,
        breakfast,
        lunch,
        dinner,
        created_at,
        likes

        FROM posts

        ORDER BY id DESC

        LIMIT 20
    """)

    posts = cur.fetchall()

    conn.close()

    return posts





# ==========================
# いいね追加
# ==========================

def add_like(

    post_id,

    username

):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT *

        FROM likes

        WHERE post_id=?

        AND username=?

        """,

        (

            post_id,

            username

        )

    )



    result = cur.fetchone()



    if result is None:


        cur.execute(
            """
            INSERT INTO likes

            (

            post_id,

            username

            )

            VALUES(?,?)

            """,

            (

                post_id,

                username

            )

        )



        cur.execute(
            """
            UPDATE posts

            SET likes = likes + 1

            WHERE id=?

            """,

            (

                post_id,

            )

        )



    conn.commit()

    conn.close()





# ==========================
# 投稿削除
# ==========================

def delete_post(post_id):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        DELETE FROM posts

        WHERE id=?

        """,

        (

            post_id,

        )

    )


    conn.commit()

    conn.close()





# ==========================
# 健康記録追加
# ==========================

def add_health_record(

    username,

    date,

    weight,

    high,

    low,

    water,

    medicine,

    score

):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        INSERT INTO health_records

        (

        username,

        date,

        weight,

        high,

        low,

        water,

        medicine,

        score

        )

        VALUES(?,?,?,?,?,?,?,?)

        """,

        (

            username,

            date,

            weight,

            high,

            low,

            water,

            int(medicine),

            score

        )

    )


    conn.commit()

    conn.close()





# ==========================
# 健康記録取得
# ==========================

def get_health_records(username):


    conn = connect()

    cur = conn.cursor()



    cur.execute(
        """
        SELECT

        date,

        weight,

        high,

        low,

        water,

        score


        FROM health_records


        WHERE username=?


        ORDER BY id DESC

        """,

        (

            username,

        )

    )


    records = cur.fetchall()


    conn.close()


    return records


# ==========================
# 推薦献立追加
# ==========================

def add_recommended_menu(
    age_min,
    age_max,
    disease,
    calorie,
    breakfast,
    lunch,
    dinner,
    reason="",
    nutrition="",
    advice=""
):


    conn = connect()

    cur = conn.cursor()


    cur.execute(
        """
        INSERT INTO recommended_menus

        (
        age_min,
        age_max,
        disease,
        calorie,
        breakfast,
        lunch,
        dinner,
        reason,
        nutrition,
        advice
        )

        VALUES(?,?,?,?,?,?,?,?,?,?)

        """,

        (
            age_min,
            age_max,
            disease,
            calorie,
            breakfast,
            lunch,
            dinner,
            reason,
            nutrition,
            advice
        )

    )


    conn.commit()

    conn.close()


def add_favorite_menu(

    username,

    menu_id,

    breakfast,

    lunch,

    dinner,

    calorie,

    reason

):
    conn = connect()
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
    INSERT INTO favorite_menus(

    username,
    menu_id,
    breakfast,
    lunch,
    dinner,
    calorie,
    reason,
    favorite_date

    )

    VALUES(?,?,?,?,?,?,?,?)
    """,
    (
       username,
       menu_id,
       breakfast,
       lunch,
       dinner,
       calorie,
       reason,
       today
    ))

    conn.commit()
    conn.close()

def get_favorite_menus(username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT

    breakfast,

    lunch,

    dinner,

    calorie,

    reason

    FROM favorite_menus

    WHERE username=?
    """,(username,))

    data = cur.fetchall()

    conn.close()

    return data

# ==========================
# 推薦献立取得
# ==========================

def get_recommended_menu(age, disease, calorie):

    menus = []

    with open(
        "data/menus.csv",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            if (
                int(row["min_age"]) <= age <= int(row["max_age"])
                and row["disease"] == disease
            ):

                menus.append(row)

    if not menus:

        return None

    menu = random.choice(menus)

    return (
        menu["breakfast"],
        menu["lunch"],
        menu["dinner"],
        menu["calorie"],
        menu["reason"],
        menu["balance"],
        menu["advice"]
    )

def get_menu_ranking():

    conn=connect()
    cur=conn.cursor()

    cur.execute("""

SELECT

    r.breakfast,
    r.lunch,
    r.dinner,
    COUNT(*) AS total

FROM favorite_menus f

JOIN recommended_menus r

ON f.menu_id = r.id

GROUP BY f.menu_id

ORDER BY total DESC

LIMIT 10

""")

    data=cur.fetchall()

    conn.close()

    return data

def add_favorite_weekly_menu(username, week):

    conn = connect()
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
    INSERT INTO favorite_weekly_menus(

        username,
        save_date,
        monday,
        tuesday,
        wednesday,
        thursday,
        friday,
        saturday,
        sunday

    )

    VALUES(?,?,?,?,?,?,?,?,?)

    """,(

        username,
        today,

        week["月曜日"]["id"],
        week["火曜日"]["id"],
        week["水曜日"]["id"],
        week["木曜日"]["id"],
        week["金曜日"]["id"],
        week["土曜日"]["id"],
        week["日曜日"]["id"]

    ))

    conn.commit()
    conn.close()

def get_favorite_weekly_menus(username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""

    SELECT

    save_date,

    monday,

    tuesday,

    wednesday,

    thursday,

    friday,

    saturday,

    sunday

    FROM favorite_weekly_menus

    WHERE username=?

    ORDER BY id DESC

    """,(username,))

    data = cur.fetchall()

    conn.close()

    return data

# ==========================
# 食材追加
# ==========================

def add_food(
    username,
    food,
    amount,
    expire
):

    conn=connect()
    cur=conn.cursor()


    cur.execute(
    """
    SELECT id
    FROM refrigerator
    WHERE username=?
    AND food=?
    """,
    (
        username,
        food
    ))

    exists=cur.fetchone()


    if exists:

        cur.execute(
        """
        UPDATE refrigerator

        SET amount=?,
        expire=?

        WHERE id=?

        """,
        (
            amount,
            expire,
            exists[0]
        ))

    else:

        cur.execute(
        """
        INSERT INTO refrigerator

        (
        username,
        food,
        amount,
        expire
        )

        VALUES(?,?,?,?)

        """,
        (
            username,
            food,
            amount,
            expire
        ))


    conn.commit()
    conn.close()

# ==========================
# 食材取得
# ==========================

def get_foods(username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""

    SELECT

    id,

    food,

    amount,

    expire

    FROM refrigerator

    WHERE username=?

    ORDER BY expire

    """,(username,))

    data=cur.fetchall()

    conn.close()

    return data

def delete_food(food_id):

    conn=connect()
    cur=conn.cursor()

    cur.execute("""

    DELETE FROM refrigerator

    WHERE id=?

    """,(food_id,))

    conn.commit()
    conn.close()

def get_menu_by_id(menu_id):

    with open("data/menu_data.csv", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if int(row["id"]) == int(menu_id):

                return (
                    row["breakfast"],
                    row["lunch"],
                    row["dinner"],
                    row["calorie"],
                    row["reason"]
                )

    return None