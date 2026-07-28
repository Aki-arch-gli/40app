from database import connect

def save_water(date, amount):

    conn = connect()

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO water(date,amount)

        VALUES(?,?)
        """,

        (date, amount)

    )

    conn.commit()

    conn.close()


def total_water():

    conn = connect()

    cur = conn.cursor()

    cur.execute("""

    SELECT SUM(amount)

    FROM water

    WHERE date=date('now')

    """)

    result = cur.fetchone()[0]

    conn.close()

    if result is None:
        result = 0

    return result