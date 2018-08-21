import  psycopg2





def add_question(question,user_id):
    try:

        sql="""INSERT INTO questions(question,user_id) VALUES (%s,%s) RETURNING question_id"""
        cur=conn.cursor()

        cur.execute(sql,(question,user_id))

        question_id= cur.fetchone()[0]

        conn.commit()

        cur.close()
    except(Exception,psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()

    return question_id

def add_answer(answer,question_id):
    try:

        sql="""INSERT INTO answers(answer,question_id) VALUES (%s,%s) RETURNING answer_id"""
        cur=conn.cursor()

        cur.execute(sql,(answer,question_id))

        answer_id= cur.fetchone()[0]

        conn.commit()

        cur.close()
    except(Exception,psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()

    return answer_id


def get_all_questions():
    try:

        sql = """SELECT question_id,question,user_id FROM questions ORDER BY question_id"""
        cur = conn.cursor()

        cur.execute(sql)

        rows=cur.fetchall()

        print("The number of questions: ", cur.rowcount)
        for row in rows:
            print(row)

        conn.commit()

        cur.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()


def delete_question(question_id):
    try:

        sql = """UPDATE questions SET deleted=%i WHERE question_id=%s"""
        cur = conn.cursor()

        cur.execute(sql,(1,question_id))

        rows=cur.rowcount()

        conn.commit()

        cur.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()

    return rows

def preferred_answer(answer_id):
    try:

        sql = """UPDATE questions SET preffered=%i WHERE answer_id=%s"""
        cur = conn.cursor()

        cur.execute(sql,(1,answer_id))

        rows=cur.rowcount()

        conn.commit()

        cur.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()

    return rows

def create_tables():

    commands = (
        """
        CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            user_name VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            user_email VARCHAR(255),
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
        )
        """,
        """ CREATE TABLE questions (
                question_id SERIAL PRIMARY KEY,
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
                answer_id SERIAL PRIMARY KEY,
                answer VARCHAR(255) NOT NULL,
                question_id INTEGER NOT NULL,
                preffered INTEGER,
                FOREIGN KEY (question_id)
                REFERENCES questions (question_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        """)

    try:
        # read the connection parameters
        # connect to the PostgreSQL server
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
    conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
    create_tables()