import  psycopg2

conn = None

def add_user(user_name,user_email):
    try:
        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
        sql="""INSERT INTO users(user_name,_user_email) VALUES (%s,%s) RETURNING user_id"""
        cur=conn.cursor()

        cur.execute(sql,(user_name,user_email))

        user_id= cur.fetchone()[0]

        conn.commit()

        cur.close()
    except(Exception,psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()

    return user_id

def add_question(question,user_id):
    try:
        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
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
        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
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
        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
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
        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
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
        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
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
