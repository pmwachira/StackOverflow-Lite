from flask import(
    Flask,
    render_template
)
from data import Questions
import connexion
import psycopg2

app= Flask(__name__,template_folder="templates")
#app= connexion.App(__name__,specification_dir='./')
conn = None

Questions=Questions()

@app.route('/')

def home():
    conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
    return render_template('home.html')

@app.route('/auth/signup')

def add_user(user_name,user_email):
    try:

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

#@app.route('/auth/login')

@app.route('/questions')
def questions():
    return render_template('questions.html',questions=Questions)

@app.route('/question/<string:id>/')
def question(id):
    return render_template('question.html', id=id)

# @app.route('/questions')
# @app.route('/questions/<questionId>')
# @app.route('/questions/<questionId>/answers')
# @app.route('/questions/<questionId>/answers/<answerId>')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
