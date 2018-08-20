import psycopg2





def create_tables():
    """ create tables in the PostgreSQL database"""
    commands = (
        """
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            user_name VARCHAR(255) NOT NULL,
            user_email VARCHAR(255) 
        )
        """,
        """ CREATE TABLE questions (
                question_id INTEGER PRIMARY KEY,
                question VARCHAR(255) NOT NULL,
                user_id INTEGER NOT NULL,
                deleted INTEGER,
                FOREIGN KEY (user_id)
                REFERENCES users (user_id)
                ON UPDATE CASCADE ON DELETE CASCADE
                )
        """,
        """
        CREATE TABLE answers (
                answer_id INTEGER PRIMARY KEY,
                answer VARCHAR(255) NOT NULL,
                question_id INTEGER NOT NULL,
                preffered INTEGER,
                FOREIGN KEY (question_id)
                REFERENCES questions (question_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        """)
    conn = None
    try:
        # read the connection parameters

        # connect to the PostgreSQL server
        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
        cur = conn.cursor()
        # create table one by one
        for command in commands:
            cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    create_tables()