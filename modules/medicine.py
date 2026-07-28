from database import connect

def add_medicine(name,time):

    conn=connect()

    cur=conn.cursor()

    cur.execute("""

    INSERT INTO medicine

    VALUES(

    NULL,

    ?,?

    )

    """,(name,time))

    conn.commit()

    conn.close()