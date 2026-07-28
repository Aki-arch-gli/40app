from database import connect

def save_menu(menu,date):

    conn=connect()

    cur=conn.cursor()

    cur.execute("""

    INSERT INTO meal_history

    VALUES(

    NULL,

    ?,?,?,?,?

    )

    """,(

    date,

    menu["朝"],

    menu["昼"],

    menu["夜"],

    menu["calorie"]

    ))

    conn.commit()

    conn.close()